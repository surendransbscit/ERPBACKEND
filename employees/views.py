from django.shortcuts import render
from django.db import IntegrityError
from django.utils.timezone import utc
from django.utils import timezone
from django.http import HttpResponse, request, Http404
from rest_framework.permissions import AllowAny
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.permissions import (IsAdminUser, IsCustomerUser, IsEmployee, isAdmin, isSuperuser, AllowAnyOrIsEmployee,
                                IsSuperuserOrEmployee)
from django.utils.dateparse import parse_datetime, parse_date
from random import randint
from django.conf import settings
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Q, ProtectedError
from django.db import transaction
import base64
from PIL import Image
from django.core.files.images import ImageFile
import io
import subprocess
import traceback
import uuid
from core.views  import get_reports_columns_template

from utilities.pagination_mixin import PaginationMixin
from datetime import datetime, timedelta, date, time
from dateutil.relativedelta import relativedelta
from knox.models import AuthToken
from models_logging.models import Change
from .models import (Employee, EmployeeType, EmployeeSettings,EmployeeFamilyDetails)
from retailsettings.models import (RetailSettings)
from .serializers import (EmployeeSerializer, CreateEmployeeSerializer, EmployeeSignupSerializer, 
                          EmployeeTypeSerializer, EmployeeLoginSerializer, EmployeeSettingsSerializer,
                          BranchSerializer, ChangesLogAPISerializer, EmployeeFamilyDetailsSerializer)
from billing.views import(cancel_bill)
from inventory.views import (generate_bulk_tag_print)
from managescheme.models import (SchemeAccount)
from schemepayment.views import (cancel_payment)
from accounts.models import User
from accounts.serializers import UserSerializer
from core.models import (EmpMenuAccess, Menu, LoginDetails, EmployeeOTP)
from core.serializers import EmpMenuAccessSerializer
from retailmasters.models import (Branch, Profile, Country, State, City, Area, RegisteredDevices, Company,
                                  Profession, RelationType)
from estimations.models import (ErpEstimation)
from cryptography.fernet import Fernet, InvalidToken
import os
from retailmasters.views import BranchEntryDate

from core.models import EmployeeOTP
from retailmasters.models import Department, Designation

from .constants import (EMPLOYEE_COLUMN_LIST,EMPLOYEE_ACTION_LIST,FILTERS)
from retailcataloguemasters.models import Section


pagination = PaginationMixin()

# Create your views here.
fernet = Fernet(os.getenv('crypt_key'))

pagination = PaginationMixin()  # Apply pagination
class LogoutView(APIView):

    def get(self, request, format=None):
        request.auth.delete()
        return Response({"Message": "Account Logged out sucessfully"},
                        status=status.HTTP_204_NO_CONTENT)

class MenuStyleUpdateView(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    
    def post(self, request, *args, **kwargs):
        emp = Employee.objects.get(user=request.user)
        EmployeeSettings.objects.filter(id_employee=emp.id_employee).update(
            menu_style=request.data['menu_style']
        )
        return Response({"message":"Menu style updated successfully."},status=status.HTTP_200_OK)

class SystemUserEmployeeDropdownView(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    
    def get(self, request, *args, **kwargs):
        queryset = Employee.objects.filter(is_system_user=True)
        serializer = EmployeeSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SystemUserEmployeeList(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    
    def get(self, request, *args, **kwargs):
        req_user = Employee.objects.filter(user=request.user.id).first()
        queryset = Employee.objects.filter(is_system_user=True)
        if req_user and not req_user.id_profile.show_super_user_and_admin:
            # queryset = queryset.filter(user_is_superuser=False, user_is_adminuser=False)
            queryset = queryset.exclude(user__is_superuser=True).exclude(user__is_adminuser=True)

            # Include the requesting user even if they are a superuser or admin
            self_user_qs = Employee.objects.filter(user=request.user.id, is_system_user=True)
            queryset = (queryset | self_user_qs).distinct()
        if (request.query_params['employee'] != 'null'):
            queryset = Employee.objects.filter(is_system_user=True, id_employee=request.query_params['employee'])
        serializer = EmployeeSerializer(queryset, many=True)
        for data in serializer.data:
            profile = Profile.objects.filter(id_profile=data['id_profile']).first()
            if(data['user']==None):
                data.update({"password1":"", "password1show":True, "username":"",
                             "password2":"", "password2show":True, "profile":"",'updateType':1,
                             "showRow":False, "enableChangePass":False,"profile_name": profile.profile_name if profile else '',})
            else:
                user = User.objects.filter(id=data['user']).first()
                profile = Profile.objects.filter(id_profile=data['id_profile']).first()
                data.update({"enableChangePass":True, "profile_name": profile.profile_name if profile else '',
                             "username":user.username, "changepass":False, 'newUsername':user.username,
                             "changePassword1":"", "changePassword2":"", 'updateType':2,
                             "changePassword1show":False, "changePassword2show":False, 'showRow':False})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        for data in request.data:
            if(data['updateType']==1):
                if User.objects.filter(username=data['username']).exists():
                    return Response({"message": "Username already in use"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    user = User.objects.create(is_adminuser=True,email=data['email'], 
                                           username = data['username'], first_name=data['firstname'],
                                           last_name=data['lastname'], account_expiry=date.today()+relativedelta(years=20))
                    user.set_password(data['password2'])
                    user.save()
                    Employee.objects.filter(id_employee=data['id_employee']).update(
                        user=user
                    )
                return Response({"message":"Employee updated successfully"}, status=status.HTTP_200_OK)
            if(data['updateType']==2):
                user = User.objects.filter(is_adminuser=True,username=data['username']).first()
                if(user.username != data['newUsername']):
                    if User.objects.filter(username=data['newUsername']).exists():
                        return Response({"message": "Username already in use"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        user.username = data['newUsername']
                        user.save()
                Employee.objects.filter(id_employee=data['id_employee']).update(
                        id_profile=data['id_profile']
                    )
                if(data['changepass'] == True):
                    user = User.objects.filter(id=data['user']).first()
                    if bool(user.check_password(data['changePassword2'])) == True:
                        return Response({"error_detail": ['New Password and Old password cant be same']}, status=status.HTTP_400_BAD_REQUEST)
                    user.set_password(data['changePassword2'])
                    user.save()
                    AuthToken.objects.filter(user=user).exclude(token_key=request.auth.token_key).delete()
                return Response({"message":"Employee updated successfully"}, status=status.HTTP_200_OK)
        return Response({"message":"Employee updated successfully"}, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        for data in request.data:
            user = User.objects.filter(id=data['user']).first()
            # if (request.data['emp']['old_password'] == request.data['emp']['password']):
            #     return Response({"error_detail": ['New Password and Old password cant be same']}, status=status.HTTP_400_BAD_REQUEST)
            if bool(user.check_password(data['changePassword2'])) == True:
                return Response({"error_detail": ['New Password and Old password cant be same']}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(data['changePassword2'])
            user.save()
            # Delete all  Tokens of this user to logout from other Devices other than This Device/Browser --
            AuthToken.objects.filter(user=user).exclude(token_key=request.auth.token_key).delete()
            # return Response({"message": "Password changed successfully"})
        return Response({"message":"Password changed successfully"}, status=status.HTTP_200_OK)
    
class EmployeeInfo(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, format=None):
        # (request.auth.token_key)'
        notifications =[]
        data = {}
        comp = Company.objects.get(id_company=request.data['id_company'])
        country = Country.objects.get(id_country=comp.country.pk)
        emp = Employee.objects.get(user=request.user)
        emp_type = emp.emp_type.employee_type if emp.emp_type else 'Employee'
        expiry = AuthToken.objects.get(token_key=request.auth.token_key).expiry
        # print(EmployeeSettings.objects.get(id_employee=emp.id_employee))
        
        data.update({
                        "user": {
                            "username": request.user.username, 
                            "emp_firstname": emp.firstname, 
                            "emp_lastname": emp.lastname, 
                            "emp_email": request.user.email, 
                            "emp_mobile": emp.mobile, 
                            "emp_type": emp_type,
                            "login_expiry": expiry, 
                            "promotional_billing":emp.id_profile.promotional_billing,
                            "customer_type_show":emp.id_profile.customer_type_show,
                            "retailer_billing":emp.id_profile.retailer_billing,
                            "est_bill_convert":emp.id_profile.est_bill_convert,
                            "est_bill_approval":emp.id_profile.est_bill_approval,
                            "allow_status_update":emp.id_profile.allow_status_update,
                            "company_state":comp.state.pk, 
                            "company_name": comp.short_code.upper(),
                            "company_fullname": comp.company_name,
                            "comapny_mobile":comp.mobile,
                            "company_address":(comp.address1 if(comp.address1) else ''),
                            "company_city": comp.city.name if(comp.city) else '',
                            "company_gst": (comp.gst_number if(comp.gst_number) else ''),
                        },
                        "settings":{
                            "menu_style":EmployeeSettings.objects.get(id_employee=emp.id_employee).menu_style,
                            "allow_pur_det_add_in_pur_entry":EmployeeSettings.objects.get(id_employee=emp.id_employee).allow_pur_det_add_in_pur_entry,
                            "purchase_edit_billing":emp.id_profile.purchase_edit_billing,
                            "sales_return_limit":emp.id_profile.sales_return_limit,
                            "sales_return_limit_days":emp.id_profile.sales_return_limit_days,
                            "is_section_required":RetailSettings.objects.get(name='is_section_required').value,
                            "stock_download_type":RetailSettings.objects.get(name='stock_download_type').value,
                            "max_outward_cash_limit":RetailSettings.objects.get(name='max_outward_cash_limit').value,
                            "max_inward_cash_limit":RetailSettings.objects.get(name='max_inward_cash_limit').value,
                            "is_sub_design_req":RetailSettings.objects.get(name='is_sub_design_req').value,
                            "is_design_mapping_req":RetailSettings.objects.get(name='is_design_mapping_req').value,
                            "is_old_metal_item_req":RetailSettings.objects.get(name='is_old_metal_item_req').value,
                            "old_metal_calculation":RetailSettings.objects.get(name='old_metal_calculation').value,
                            "is_short_code_req":int(RetailSettings.objects.get(name='is_short_code_req').value),
                            "tag_print_template":int(RetailSettings.objects.get(name='tag_print_template').value),
                            "estimation_print_template":int(RetailSettings.objects.get(name='estimation_print_template').value),
                            "bill_print_template":int(RetailSettings.objects.get(name='bill_print_template').value),
                            "metal_rate_type":RetailSettings.objects.get(name='metal_rate_type').value,
                            "master_words_type":RetailSettings.objects.get(name='master_words_type').value,
                            "is_qc_required":RetailSettings.objects.get(name='is_qc_required').value,
                            "pur_entry_des_and_sub_des_req":RetailSettings.objects.get(name='pur_entry_des_and_sub_des_req').value,
                            "is_huid_required":RetailSettings.objects.get(name='is_huid_required').value,
                            "is_old_metal_cost_editable":RetailSettings.objects.get(name='is_old_metal_cost_editable').value,
                            "tax_required_in_purchase":RetailSettings.objects.get(name='tax_required_in_purchase').value,
                            "is_design_and_pur_req_in_lot":RetailSettings.objects.get(name='is_design_and_pur_req_in_lot').value,
                            "rate_cut_and_pay_type":RetailSettings.objects.get(name='rate_cut_and_pay_type').value,
                            "is_metal_wise_billing":RetailSettings.objects.get(name='is_metal_wise_billing').value,
                            "dust_wt_auto_calculate":RetailSettings.objects.get(name='dust_wt_auto_calculate').value,
                            "is_sales_emp_req":RetailSettings.objects.get(name='is_sales_emp_req').value,
                            "dust_wt_auto_calc_type":RetailSettings.objects.get(name='dust_wt_auto_calc_type').value,
                            "add_chit_adj_manually":RetailSettings.objects.get(name='add_chit_adj_manually').value,
                            "bill_print_office_copy_req":RetailSettings.objects.get(name='bill_print_office_copy_req').value,
                            "allow_bill_date_change":emp.id_profile.allow_bill_date_change,
                            "show_tagging_edit":emp.id_profile.show_tagging_edit,
                            "allow_min_sales_amount":emp.id_profile.allow_min_sales_amount,
                            "purchase_print_template":(RetailSettings.objects.get(name='purchase_print_template').value),
                            "stock_transfer_print_template":(RetailSettings.objects.get(name='stock_transfer_print_template').value),
                            "qc_issue_print_template":(RetailSettings.objects.get(name='qc_issue_print_template').value),
                            "issue_receipt_print_format":(RetailSettings.objects.get(name='issue_receipt_print_format').value),
                            "lot_issue_receipt_print":(RetailSettings.objects.get(name='lot_issue_receipt_print').value),
                            "stock_issue_receipt_print":(RetailSettings.objects.get(name='stock_issue_receipt_print').value),
                            "can_edit_account_join_date":emp.id_profile.can_edit_account_join_date,
                            "show_trans_code_search_in_billing":emp.id_profile.show_trans_code_search_in_billing,
                            "is_category_required_purchase_entry":(RetailSettings.objects.get(name='is_category_required_purchase_entry').value),
                            "purchase_entry_tax_percentage":(RetailSettings.objects.get(name='purchase_entry_tax_percentage').value),
                            "chit_gold_purity_id":(RetailSettings.objects.get(name='chit_gold_purity_id').value),
                            "chit_silver_cat_id":(RetailSettings.objects.get(name='chit_silver_cat_id').value),
                            "chit_silver_purity_id":(RetailSettings.objects.get(name='chit_silver_purity_id').value),
                            "chit_gold_cat_id":(RetailSettings.objects.get(name='chit_gold_cat_id').value),
                            "stock_audit_based_on":(RetailSettings.objects.get(name='stock_audit_based_on').value),
                            "can_show_tag_no":(RetailSettings.objects.get(name='can_show_tag_no').value),
                            "pur_entry_des_req":(RetailSettings.objects.get(name='pur_entry_des_req').value),
                            "min_sales_amt_calculate_tax_percentage":(RetailSettings.objects.get(name='min_sales_amt_calculate_tax_percentage').value),
                            "default_login_type":(RetailSettings.objects.get(name='default_login_type').value),
                            "mrp_item_discount_percentage":(RetailSettings.objects.get(name='mrp_item_discount_percentage').value),
                            "default_login_type":int(RetailSettings.objects.get(name='default_login_type').value),
                            "is_approval_required_for_minimum_discount":(RetailSettings.objects.get(name='is_approval_required_for_minimum_discount').value),
                            "silver_lot_wt_tolarance":(RetailSettings.objects.get(name='silver_lot_wt_tolarance').value),
                            "gold_lot_wt_tolarance":(RetailSettings.objects.get(name='gold_lot_wt_tolarance').value),
                            "is_confirmation_req_in_billing":(RetailSettings.objects.get(name='is_confirmation_req_in_billing').value),
                            "is_confirmation_req_in_billing_for_credit":(RetailSettings.objects.get(name='is_confirmation_req_in_billing_for_credit').value),
                            "is_wastage_and_mc_edit_in_est":(RetailSettings.objects.get(name='is_wastage_and_mc_edit_in_est').value),
                            "is_counter_req_in_billing":(RetailSettings.objects.get(name='is_counter_req_in_billing').value),
                            "tag_code_manually_tag_audit":(RetailSettings.objects.get(name='tag_code_manually_tag_audit').value),
                            "show_scale_weight_in_stock_transfer":(RetailSettings.objects.get(name='show_scale_weight_in_stock_transfer').value),
                            "can_edit_account_join_date":emp.id_profile.can_edit_account_join_date,
                            "is_show_min_sales_amount":emp.id_profile.is_show_min_sales_amount,
                            "show_unscanned_details":emp.id_profile.show_unscanned_details,
                            "is_otp_req_for_bill_delete":emp.id_profile.is_otp_req_for_bill_delete,
                        },
                        "tag_edit_settings":{
                            "can_edit_tag_va":emp.id_profile.can_edit_tag_va,
                            "can_edit_tag_mc":emp.id_profile.can_edit_tag_mc,
                            "can_edit_tag_gwt":emp.id_profile.can_edit_tag_gwt,
                            "can_edit_tag_pcs":emp.id_profile.can_edit_tag_pcs,
                            "can_edit_tag_purity":emp.id_profile.can_edit_tag_purity,
                            "can_edit_tag_mrp":emp.id_profile.can_edit_tag_mrp,
                            "can_edit_tag_huid":emp.id_profile.can_edit_tag_huid,
                            "can_edit_tag_attr":emp.id_profile.can_edit_tag_attr,
                            "can_edit_tag_pur_cost":emp.id_profile.can_edit_tag_pur_cost,
                            "can_edit_tag_dsgn_sub_desgn":emp.id_profile.can_edit_tag_dsgn_sub_desgn,
                            "can_edit_tag_img":emp.id_profile.can_edit_tag_img,
                            "can_print_tag":emp.id_profile.can_print_tag,
                            },
                        "issue_reciept_settings":{
                            "show_issue_pettycash_option":emp.id_profile.show_issue_pettycash_option,
                            "show_issue_credit_option":emp.id_profile.show_issue_credit_option,
                            "show_issue_refund_option":emp.id_profile.show_issue_refund_option,
                            "show_issue_bankdeposit_option":emp.id_profile.show_issue_bankdeposit_option,
                            "show_reciept_genadvnc_option":emp.id_profile.show_reciept_genadvnc_option,
                            "show_reciept_ordadvnc_option":emp.id_profile.show_reciept_ordadvnc_option,
                            "show_reciept_credcoll_option":emp.id_profile.show_reciept_credcoll_option,
                            "show_reciept_repord_delivery_option":emp.id_profile.show_reciept_repord_delivery_option,
                            "show_reciept_openbal_option":emp.id_profile.show_reciept_openbal_option,
                            "show_reciept_chitdepo_option":emp.id_profile.show_reciept_chitdepo_option,
                            "show_reciept_others_option":emp.id_profile.show_reciept_others_option,
                            },
                        "dashboard_settings":{
                            "show_est_details":emp.id_profile.show_est_details,
                            "show_cus_visits":emp.id_profile.show_cus_visits,
                            "show_sales":emp.id_profile.show_sales,
                            "show_karigar_order":emp.id_profile.show_karigar_order,
                            "show_cus_orders":emp.id_profile.show_cus_orders,
                            "show_sales_returns":emp.id_profile.show_sales_returns,
                            "show_credit_sales":emp.id_profile.show_credit_sales,
                            "show_old_metal_purchase":emp.id_profile.show_old_metal_purchase,
                            "show_lots":emp.id_profile.show_lots,
                            "show_cash_abstract":emp.id_profile.show_cash_abstract,
                            "show_statistics":emp.id_profile.show_statistics,
                            "show_top_products":emp.id_profile.show_top_products,
                            "show_active_chits":emp.id_profile.show_active_chits,
                            "show_matured_claimed":emp.id_profile.show_matured_claimed,
                            "show_payment":emp.id_profile.show_payment,
                            "show_users_joined_through":emp.id_profile.show_users_joined_through,
                            "show_scheme_wise":emp.id_profile.show_scheme_wise,
                            "show_branch_wise":emp.id_profile.show_branch_wise,
                            "show_collection_summary":emp.id_profile.show_collection_summary,
                            "show_inactive_chits":emp.id_profile.show_inactive_chits,
                            "show_chit_closing_details":emp.id_profile.show_chit_closing_details,
                            "show_register_through_details":emp.id_profile.show_register_through_details,
                            "show_customer_details":emp.id_profile.show_customer_details,
                            "show_customer_personal_landmark":emp.id_profile.show_customer_personal_landmark,
                            "show_branch_wise_collection_details":emp.id_profile.show_branch_wise_collection_details
                            },
                    })
        # , "other": {"branch_name": None, "company_name": comp.short_code.upper()} in above line
        # if (int(request.data['id_branch']) != 0):
        login_branch =[]
        for bid in request.data['login_branches']:
            other = {}
            branch_serializer = BranchSerializer(Branch.objects.get(
                id_branch=bid), context={"request": request})
            branch_name = branch_serializer.data['name'].upper()
            branch_logo = branch_serializer.data['logo']
            other.update({"branch_name": branch_name,"branch_logo": branch_logo,
                          "id_branch":branch_serializer.data['id_branch']})
            if other not in login_branch:
                login_branch.append(other)
        entry_date = None
        if(len(login_branch)==1):
            for log_branch in login_branch:
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(log_branch['id_branch'])
        data['user'].update({"other":login_branch,"currency_code":country.currency_code,"entry_date":entry_date})
        if(EmployeeSettings.objects.filter(id_employee=emp.id_employee).exists()):
            data['user'].update({
                "allow_day_close" : EmployeeSettings.objects.get(id_employee=emp.id_employee).allow_day_close
            })
        else:
            data['user'].update({"allow_day_close" : False})
        if request.user.is_superuser:
            data['user'].update({
                "emp_type": "Super Admin",
                "currency_code":country.currency_code
            })
        if(RetailSettings.objects.filter(name='customer_order_print_template').exists()):
            data['settings'].update({
                "customer_order_print_template":int(RetailSettings.objects.filter(name='customer_order_print_template').first().value),
            })
        else:
            data['settings'].update({
                "customer_order_print_template":1
            })
            
        return Response({"data": data}, status=status.HTTP_200_OK)
    

class EmployeeNotifications(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, format=None):
        notifications =[]
        data = {}
        emp = Employee.objects.get(user=request.user)
        emp_type = emp.emp_type.employee_type
        if(emp.id_profile.is_notify_for_est_approve == True):
            unapproved_estimation = ErpEstimation.objects.filter(is_approved=0).count()
            non_billed_estimation = ErpEstimation.objects.filter(invoice_id=None).count()
            if(unapproved_estimation > 0 and unapproved_estimation <= 20):
                notifications.append({
                    "id": uuid.uuid4(),
                    "icon": "curve-down-right",
                    "iconStyle": "bg-warning-dim",
                    "text": "You have " + str(unapproved_estimation) + " estimations to be approved.",
                    "page_url":"/estimation/approval"
                    })
            if(unapproved_estimation > 0 and unapproved_estimation > 20):
                notifications.append({
                    "id": uuid.uuid4(),
                    "icon": "curve-down-right",
                    "iconStyle": "bg-warning-dim",
                    "text": "You have 20+ estimations to be approved.",
                    "page_url":"/estimation/approval"
                    })
            if(non_billed_estimation > 0 and non_billed_estimation <= 20):
                notifications.append({
                    "id": uuid.uuid4(),
                    "icon": "curve-down-left",
                    "iconStyle": "bg-success-dim",
                    "text": "You have " + str(non_billed_estimation) + " estimations to be billed.",
                    "page_url":"/estimation/approval"
                    })
            if(non_billed_estimation > 0 and non_billed_estimation > 20):
                notifications.append({
                    "id": uuid.uuid4(),
                    "icon": "curve-down-left",
                    "iconStyle": "bg-success-dim",
                    "text": "You have 20+ estimations to be billed.",
                    "page_url":"/estimation/approval"
                    })
        
        data.update({"notifications" : notifications})
        return Response(data, status=status.HTTP_200_OK)
    
class EmpProfileView(generics.GenericAPIView):
    permission_classes = [isAdmin]
    
    def get(self, request, *args, **kwargs):
        emp = Employee.objects.get(user=request.user)
        emp_serializer = EmployeeSerializer(emp)
        data = {}
        login_branch = []
        for each in emp_serializer.data['login_branches']:
            branches = Branch.objects.filter(id_branch=each)
            branch_serializer = BranchSerializer(branches, many=True)
            for each_branch in branch_serializer.data:
                login_branch.append(each_branch['name'])
        data.update({"pk_id":emp.id_employee,"id_employee":emp.id_employee,"name": emp.firstname + " " + emp.lastname, "designation": emp.designation.name,
                     "doj":emp.date_of_join, "dob":emp.date_of_birth, "firstname":emp.firstname, "lastname":emp.lastname,
                     "address1":emp.address1, "address2":emp.address2, "address3":emp.address3, "pincode":emp.pincode,
                     "country":emp.country.pk, "state":emp.state.pk, "city":emp.city.pk,
                     "phone":emp.mobile, "email":emp.user.email, "emp_code":emp.emp_code, "emp_type":emp.emp_type.employee_type,
                     "login_branches":login_branch, })
        return Response(data, status=status.HTTP_200_OK)
    
    def put (self, request, *args, **kwargs):
        emp = Employee.objects.get(user=request.user)
        request.data.update({"user":request.user.pk, "id_profile":emp.id_profile.pk})
        emp_serializer = EmployeeSerializer(emp, data=request.data)
        emp_serializer.is_valid(raise_exception=True)
        emp_serializer.save()
        if (request.data['firstname'] != emp.firstname):
            User.objects.filter(id=emp.user.pk).update(first_name=request.data['firstname'])
        if (request.data['lastname'] != emp.lastname):
            User.objects.filter(id=emp.user.pk).update(last_name=request.data['lastname'])
        return Response(emp_serializer.data,status=status.HTTP_200_OK)


class ActiveEmployees(generics.ListAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    
    def get(self, request, *args, **kwargs):
        print(request)
        queryset = Employee.objects.all()
        serializer = EmployeeSerializer(queryset, many=True)
        output = []
        for data in serializer.data:
            instance = {}
            instance.update({"value":data['id_employee']})
            if (data['lastname'] != None):
                instance.update({"label": data['emp_code'] + " - " + data['firstname'] + " " + data['lastname']})
            else:
                instance.update({"label": data['emp_code'] + " - " +data['firstname']})
            if instance not in output:
                output.append(instance)
        return Response({"data" : output}, status=status.HTTP_200_OK)


class CreateEmployeeAPI(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()

    def get(self, request, *args, **kwargs):
        output = []
        # Non Super User Admins
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request,None, EMPLOYEE_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,EMPLOYEE_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.get_serializer(page, many=True, context={"request":request})
        for index,data in enumerate(serializer.data):
            # designation = Designation.objects.get(id_design=data['designation'])
            department = Department.objects.get(id_dept=data['dept'])
           
            if(data['user'] is not None):
                user = User.objects.get(id=data['user'])
                data.update({"is_active":user.is_active})
            if(data['user'] == None):
                data.update({"is_active":True})
            if(data['image']!=None):
                data.update({"image":data['image'], "image_text":data['firstname'][0]})
            else:
                data.update({"image":None, "image_text":data['firstname'][0]})
            data.update({"pk_id":data['id_employee'],'sno':index+1,
                         "department":department.name})
            if data not in output:
                if(data['user'] is not None):
                    user = User.objects.get(id=data['user'])
                    if(user.is_superuser != True):
                        output.append(data)
                else:
                    output.append(data) 
        context={
            'columns':columns,
            'actions':EMPLOYEE_ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':False,
            'filters':FILTERS
            }
        return pagination.paginated_response(output,context)

    def post(self, request, *args, **kwargs):

        def checkbranch(self, data):
            branches = []
            instance = {}
            for each in data:
                try:
                    branch = Branch.objects.get(id_branch=each)
                    branches.append(branch)
                except Branch.DoesNotExist:
                    pass
            instance.update({"login_branches": branches})
            return instance
        
        if ('pk' in kwargs):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
       
        # password = request.data['emp']['password']
        
        if User.objects.filter(email=request.data['emp']['email']).exists():
            return Response({"message": "Emailid already in use"}, status=status.HTTP_400_BAD_REQUEST)
        if Employee.objects.filter(email=request.data['emp']['email']).exists():
            return Response({"message": "Emailid already in use"}, status=status.HTTP_400_BAD_REQUEST)
        # if User.objects.filter(username=request.data['emp']['username']).exists():
        #     return Response({"message": "Username already in use"}, status=status.HTTP_400_BAD_REQUEST)
        if Employee.objects.filter(mobile=request.data['emp']['mobile']).exists():
            return Response({"message": "Mobile number already in use"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            try:
                # user = User.objects.create(is_adminuser=True,email=request.data['emp']['email'], 
                #                        username = request.data['emp']['username'], first_name=request.data['emp']['firstName'],
                #                        last_name=request.data['emp']['lastName'], account_expiry=date.today()+relativedelta(years=20))
                # user.set_password(password)
                # user.save()
                relation_details = request.data['emp']['relation_details']
                # del request.data['emp']['username']
                # del request.data['emp']['password']
                del request.data['emp']['relation_details']
                request.data['emp'].update({"email_verified":True})
            # create admin using user
                dept = Department.objects.get(id_dept = request.data['emp']['department'])
                # desig = Designation.objects.get(id_design = request.data['emp']['designation'])
                emp_type = EmployeeType.objects.get(id_employee_type = request.data['emp']['emp_type'])
                # profile = Profile.objects.get(id_profile = request.data['emp']['id_profile'])
                country = Country.objects.get(id_country = request.data['emp']['id_country'])
                state = State.objects.get(id_state = request.data['emp']['id_state'])
                city = City.objects.get(id_city = request.data['emp']['id_city'])
                area = Area.objects.get(id_area = request.data['emp']['id_area'])
                log_branch = checkbranch(self, request.data['emp']['login_branches'])
                
                emp_code = None
                if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
                    emp_code = None
                if(int(RetailSettings.objects.get(name='is_short_code_req').value)==0):
                    emp_code = request.data['emp']['emp_code']
                
                data = {}   
                if (request.data['emp']['image'] != None):
                    b = ((base64.b64decode(request.data['emp']['image']
                                   [request.data['emp']['image'].find(",") + 1:])))
                    img = Image.open(io.BytesIO(b))
                    filename = 'emplaoyee_image.jpeg'
                    img_object = ImageFile(io.BytesIO(
                        img.fp.getvalue()), name=filename)
                    data.update({"image": img_object})
                else:
                    data.update({"image": None})
                    
                if (request.data['emp']['signature'] != None):
                    sign_b = ((base64.b64decode(request.data['emp']['signature'][request.data['emp']['signature'].find(",") + 1:])))
                    sign_img = Image.open(io.BytesIO(sign_b))
                    sign_filename = 'employee_signature.jpeg'
                    sign_object = ImageFile(io.BytesIO(
                        sign_img.fp.getvalue()), name=sign_filename)
                    data.update({"signature": sign_object})
                else:
                    data.update({"signature": None})
                
                if 'section' in request.data['emp']:
                    data.update({
                                "section":request.data['emp']['section']})

                data.update({"firstname":request.data['emp']['firstName'], "lastname":request.data['emp']['lastName'], "date_of_birth":request.data['emp']['dob'],
                    "emp_code":emp_code, "dept" : dept.pk, "designation":None, "email_verified":True,
                    "date_of_join" :request.data['emp']['doj'], "mobile":request.data['emp']['mobile'], "comments":request.data['emp']['comments'],
                    "emp_type" : emp_type.pk, "user" :None,"id_profile":None, "address1":request.data['emp']['address1'],
                    "address2":request.data['emp']['address2'],"address3":request.data['emp']['address3'],"pincode":request.data['emp']['pincode'],
                    "pincode":request.data['emp']['pincode'],"country":country.pk, "state":state.pk, "city":city.pk,
                    "area":area.pk,"login_branches":request.data['emp']['login_branches']})
            # emp = Employee.objects.create(**data)
                emp = EmployeeSerializer(data=data)
                emp.is_valid(raise_exception=True)
                emp.save()
                for relation_data in relation_details:
                    relation_data.update({"employee": emp.data['id_employee']})
                    relation_serializer = EmployeeFamilyDetailsSerializer(data=relation_data)
                    relation_serializer.is_valid(raise_exception=True)
                    relation_serializer.save()
                if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
                    Employee.objects.filter(id_employee=emp.data['id_employee']).update(emp_code=emp.data['id_employee'])
                emp_settings_data = {"id_employee":emp.data['id_employee'], "disc_limit_type":"1","disc_limit":1,
                                     "allow_branch_transfer":False, "allow_day_close":False,"menu_style":1,
                                     "created_by":request.user.pk}
                emp_settings = EmployeeSettingsSerializer(data = emp_settings_data)
                emp_settings.is_valid(raise_exception=True)
                emp_settings.save()
                # create Admin menu access for created Admin
                # for each in request.data['accessdata']:
                #     each.update({"emp_id": emp.data['id_employee']})
                #     EmpMenuAccess.objects.create(**each)
            except IntegrityError as e:
                if "Invalid username" in str(e):
                    return Response(
                    {"error_detail": ["Invalid username"]}, status=status.HTTP_400_BAD_REQUEST)
                if ("users.username" in str(e)):
                    return Response({"error_detail": [
                                'Username already allocated']}, status=status.HTTP_400_BAD_REQUEST)
                if ("users.users_email" in str(e)):
                    return Response(
                    {"error_detail": ['Email already allocated']}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True,
                         "message": "Admin user created successfully"},
                        status=status.HTTP_201_CREATED)


class EmployeeDetailView(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()
    
    
    def get(self, request, *args, **kwargs):
        employee = self.get_object()
        serializer = EmployeeSerializer(employee, context={"request":request})
        section = []
        # # hide Super User admin
        # if (employee.user.is_superuser):
        #     raise Http404
        accessdata = []
        branches = []
        relations_details = []
        if(EmployeeFamilyDetails.objects.filter(employee=employee.id_employee).exists()):
            relation_queryset = EmployeeFamilyDetails.objects.filter(employee=employee.id_employee)
            relation_serializer = EmployeeFamilyDetailsSerializer(relation_queryset, many=True)
            for relation_data in relation_serializer.data:
                relation_data.update({
                    "fam_name":relation_data['name'],
                    "fam_dob":relation_data['date_of_birth'],
                    "fam_wed_dob":relation_data['date_of_wed'],
                    "relation_type":{
                        "value": relation_data['relation_type'], 
                        "label": RelationType.objects.get(id=relation_data['relation_type']).name if relation_data['relation_type']!=None else None
                    },
                    "profession":{
                        "value": relation_data['profession'], 
                        "label": Profession.objects.get(id_profession=relation_data['profession']).profession_name if relation_data['profession']!=None else None
                    },
                })
                if relation_data not in relations_details:
                    relations_details.append(relation_data)
        for branch in serializer.data['login_branches']:
            branches.append(
                {"value": branch, "label": Branch.objects.get(id_branch=branch).name})
        for sections in serializer.data['section']:
            section.append(
                {"value": sections, "label": Section.objects.get(id_section=sections).section_name})
        output = {"employee": serializer.data, "accessdata": accessdata}
        output['employee'].update({"email":employee.email,
                                   "login_branches": branches,"relations_details":relations_details,"section":section})
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            employee = self.get_object()
            relation_details = request.data['emp']['relation_details']
            del request.data['emp']['relation_details']
            # super user Admin is not editable
            # if (employee.user.is_superuser):
            #     return Response({"error_detail": ["You are not allowed to perform this action"]}, status=status.HTTP_403_FORBIDDEN)
            # if request.data['emp']['changepass'] == True:
            #     user = (employee.user)
            #     if (request.data['emp']['old_password'] == request.data['emp']['password']):
            #         return Response({"error_detail": ['New Password and Old password cant be same']}, status=status.HTTP_400_BAD_REQUEST)
            #     if bool(user.check_password(request.data['emp']['old_password'])) == False:
            #         return Response({"error_detail": ['Incorrect password entered as Current Password']}, status=status.HTTP_400_BAD_REQUEST)
            #     user.set_password(request.data['emp']['password'])
            #     user.save()
            #     del request.data['emp']['old_password']
            #     del request.data['emp']['password']
            #     del request.data['emp']['changepass']
            #     # Delete all  Tokens of this user to logout from other Devices other than This Device/Browser --
            #     AuthToken.objects.filter(user=user).exclude(token_key=request.auth.token_key).delete()
            #     # AuthToken.objects.filter(user=user).delete()
            #     return Response({"message": "Password changed successfully"})
            if(EmployeeFamilyDetails.objects.filter(employee=employee.id_employee).exists()):
                EmployeeFamilyDetails.objects.filter(employee=employee.id_employee).delete()
            for relation_data in relation_details:
                relation_data.update({"employee": employee.id_employee})
                relation_serializer = EmployeeFamilyDetailsSerializer(data=relation_data)
                relation_serializer.is_valid(raise_exception=True)
                relation_serializer.save()
            if (request.data['emp']['image'] != None):
                if 'data:image/' in request.data['emp']['image'][:30]:
                    # update items  for which image is changed
                    employee.image.delete()
                    b = ((base64.b64decode(request.data['emp']['image'][request.data['emp']['image'].find(",") + 1:])))
                    img = Image.open(io.BytesIO(b))
                    filename = 'employee_image.jpeg'
                    img_object = ImageFile(io.BytesIO(
                        img.fp.getvalue()), name=filename)
                    request.data['emp'].update({"image": img_object})
                    # serializer = EmployeeSerializer(employee, data=request.data['emp'])
                    # serializer.is_valid(raise_exception=True)
                    # serializer.save()
                    # return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                else:
                    del request.data['emp']['image']
                    # serializer = EmployeeSerializer(employee, data=request.data['emp'])
                    # serializer.is_valid(raise_exception=True)
                    # serializer.save()
                    # return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            else:
                # print("Image Null")
                request.data['emp'].update({"image":None})
                
            if (request.data['emp']['signature'] != None):
                if 'data:image/' in request.data['emp']['signature'][:30]:
                    # update items  for which image is changed
                    employee.signature.delete()
                    sign_b = ((base64.b64decode(request.data['emp']['signature'][request.data['emp']['signature'].find(",") + 1:])))
                    sign_img = Image.open(io.BytesIO(sign_b))
                    sign_filename = 'employee_signature.jpeg'
                    sign_object = ImageFile(io.BytesIO(
                        sign_img.fp.getvalue()), name=sign_filename)
                    request.data['emp'].update({"signature": sign_object})
                    # serializer = EmployeeSerializer(employee, data=request.data['emp'])
                    # serializer.is_valid(raise_exception=True)
                    # serializer.save()
                    # return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                else:
                    del request.data['emp']['signature']
                    # serializer = EmployeeSerializer(employee, data=request.data['emp'])
                    # serializer.is_valid(raise_exception=True)
                    # serializer.save()
                    # return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            else:
                # print("Image Null")
                request.data['emp'].update({"signature":None})
            if(employee.user == None):
                request.data['emp'].update({"user":None})
            if(employee.user is not None):
                request.data['emp'].update({"user":employee.user.pk})
            
            is_system_user = employee.is_system_user
            user_id = ""
            if(is_system_user == True and request.data['emp']['is_system_user']==False):
                user_id = employee.user.pk
            if(employee.is_system_user == True and request.data['emp']['is_system_user']==False):
                request.data['emp'].update({"user":None})
            serializer = EmployeeSerializer(employee, data=request.data['emp'])
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if(is_system_user == True and request.data['emp']['is_system_user']==False):
                User.objects.filter(id=user_id).delete()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                

    def delete(self, request, *args, **kwargs):
        if ('pk' in kwargs):
            # print(request.user)
            admin = self.get_object()
            if (admin.user.is_superuser):
                return Response({"error_detail": ["This Employee is a superuser, can't be deleted..."]}, status=status.HTTP_400_BAD_REQUEST)
            user = admin.user
            try:
                admin.delete()
                user.delete()
            except ProtectedError:
                return Response({"error_detail": ["Can't delete. Employee has items associated to him"]}, status=status.HTTP_423_LOCKED)
            return Response({"success": True, "message": "Employee user deleted"}, status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class EmpSettingsView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = EmployeeSettings.objects.all()
    serializer_class = EmployeeSettingsSerializer
    
    def post(self, request):
        output = []
        profiletype = request.data.get('profiletype')
        employee_id = request.data.get('employee')
        employee_settings_queryset = EmployeeSettings.objects.all()

        if profiletype:
            employee_settings_queryset = employee_settings_queryset.filter(id_employee__id_profile=profiletype)
        
        if employee_id:
            employee_settings_queryset = employee_settings_queryset.filter(id_employee_id=employee_id)
        serializer = EmployeeSettingsSerializer(employee_settings_queryset, many=True)
        for data in serializer.data:
            instance = {}
            employee = Employee.objects.get(id_employee=data['id_employee'])
            if(data['disc_limit_type']=="1"):
                instance.update({"disc_limit_type":{"label":"Amount", "value":"1"}})
            else:
                instance.update({"disc_limit_type":{"label":"Percent", "value":"2"}})
                
            if(data['allow_day_close']==True):
                instance.update({"allow_day_close":{"label":"Yes", "value":1}})
            else:
                instance.update({"allow_day_close":{"label":"No", "value":0}})
                
            if(data['allow_branch_transfer']==True):
                instance.update({"allow_branch_transfer":{"label":"Yes", "value":1}})
            else:
                instance.update({"allow_branch_transfer":{"label":"No", "value":0}})

            if(data['allow_pur_det_add_in_pur_entry']==True):
                instance.update({"allow_pur_det_add_in_pur_entry":{"label":"Yes", "value":1}})
            else:
                instance.update({"allow_pur_det_add_in_pur_entry":{"label":"No", "value":0}})

            access_time_from = data['access_time_from']
            access_time_to = data['access_time_to']
            if access_time_from:
                access_time_parts = access_time_from.split(':')
                access_time_from_time = time(int(access_time_parts[0]), int(access_time_parts[1]), int(access_time_parts[2]))
            else:
                access_time_from_time = None

            if access_time_to:
                access_time_parts = access_time_to.split(':')
                access_time_to_time = time(int(access_time_parts[0]), int(access_time_parts[1]), int(access_time_parts[2]))
            else:
                access_time_to_time = None
            instance.update({"id":data['id'], "disc_limit":data['disc_limit'], "access_time_from":data['access_time_from'],
                             "access_time_to":data['access_time_to'], "id_employee":data['id_employee'], "employee":employee.firstname,
                             "selected":False, "access_time_from":access_time_from_time, "access_time_to":access_time_to_time,
                             "menu_style":data['menu_style']})
            if instance not in output:
                output.append(instance)
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        if(len(request.data['employee_settings']) ==0):
            return Response({"message":"Empty list"},status= status.HTTP_400_BAD_REQUEST)
        for data in request.data['employee_settings']:
            queryset = EmployeeSettings.objects.get(id=data['id'])
            data.update({"created_by": queryset.created_by.pk})
            serializer = EmployeeSettingsSerializer(queryset, data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=self.request.user,
                            updated_on=datetime.now(tz=timezone.utc))
        return Response({"message":"Employee settings updated successfully."}, status=status.HTTP_202_ACCEPTED)



# Create Admin User[Employee User]:
# class CreateEmployeeAPI(APIView):
#     permission_classes = [IsEmployee]
#     #permission_classes = [permissions.AllowAny]

#     def get(self, request, *args, **kwargs):
#         # single employee Instance
#         if 'id' in request.query_params and request.query_params['id'] != None:
#             queryset = Employee.objects.get(
#                 id_employee=request.query_params['id'])
#             serializer = EmployeeSerializer(queryset)
#             user = (User.objects.get(id=serializer.data['user']))
#             userserializer = UserSerializer(user)
#             emp_type = {"value": serializer.data['emp_type'], "label": EmployeeType.objects.get(
#                 id_employee_type=serializer.data['emp_type']).employee_type}
#             emp_access = EmpMenuAccess.objects.filter(
#                 emp=serializer.data['id_employee']).values()

#             # To append extra details from Menu table
#             for each in emp_access:
#                 menu = Menu.objects.get(id=each['menu_id'])
#                 each.update({
#                     'label': menu.text,
#                     # "link": menu.link,
#                     # "icon": menu.icon,
#                     "parent": menu.parent,
#                     "order": menu.order
#                 })
#             sortbyorder = sorted(emp_access,
#                                  key=lambda k:
#                                  (k['order'], k['menu_id']))

#             for each in sortbyorder:
#                 each.update({"submenus": 0})
#                 # print(each)
#                 for each1 in sortbyorder:

#                     if (each1 != each):

#                         if (each1['parent'] == each["menu_id"]):
#                             each['submenus'] += 1
#             new_order = []
#             for each in sortbyorder:
#                 if (each['submenus']
#                         == 0) and (each['parent'] == None
#                                    or each['parent'] == each['menu_id']):
#                     new_order.append(each)
#                     continue
#                 if (each['submenus'] > 0):
#                     new_order.append(each)
#                     for submen in sortbyorder:
#                         if each['menu_id'] == submen['parent']:

#                             new_order.append(submen)

#             branches = []
#             for branch in serializer.data['login_branches']:
#                 branches.append(
#                     {"value": branch, "label": Branch.objects.get(id_branch=branch).name})
#             return Response({"id_employee": serializer.data['id_employee'], "firstname": serializer.data['firstname'], "lastname": serializer.data['lastname'], "mobile": serializer.data['mobile'], "emp_type": emp_type, "login_branches": branches, "user": userserializer.data, "emp_access": new_order})
#             # return Response(new_order)
#         # List of Employees
#         queryset = Employee.objects.all()
#         serializer = EmployeeSerializer(queryset, many=True)
#         output = []
#         for data in serializer.data:
#             user = (User.objects.get(id=data['user']))
#             userserializer = UserSerializer(user)
#             instance = {}
#             emp_type = EmployeeType.objects.get(
#                 id_employee_type=data['emp_type']).employee_type
#             instance.update({"user": userserializer.data,
#                              "id_employee": data['id_employee'], "firstname": data['firstname'], "lastname": data['lastname'], "emp_type": emp_type, })
#             output.append(instance)
#         return Response(output)

#     def post(self, request, *args, **kwargs):
#         # print(request.data['emp'])
#         serializer = CreateEmployeeSerializer(data=request.data['emp'])
#         serializer.is_valid(raise_exception=True)
#         data = serializer.checkbranch(serializer.data)
#         user, emp = serializer.save(data)
#         # print(model_to_dict(user), model_to_dict(emp))
#         for data in request.data['accessdata']:
#             data.update({"emp_id": emp.id_employee})
#             try:
#                 EmpMenuAccess.objects.create(**data)
#             except IntegrityError:
#                 pass

#         userializer = UserSerializer(user)
#         eserializer = EmployeeSerializer(emp)
#         return Response({"Success": "Employee Created Successfully", "user": userializer.data, "employee": eserializer.data}, status=status.HTTP_201_CREATED)

#     def put(self, request, *args, **kwargs):
#         if 'id' in request.query_params and request.query_params['id'] != None:
#             try:
#                 emp = Employee.objects.get(
#                     id_employee=request.query_params['id'])
#                 emp_user = emp.user
#                 request.data['emp'].update({"user": emp_user.id})
#                 serializer = EmployeeSerializer(emp, data=request.data['emp'])
#                 serializer.is_valid(raise_exception=True)
#                 try:
#                     emp_user.email = data = request.data['emp']['email']
#                     emp_user.save()
#                 except IntegrityError:
#                     return Response({"error_detail": ["Email already taken"]}, status=status.HTTP_400_BAD_REQUEST)
#                 if ((emp_user.account_expiry) !=
#                    parse_date(request.data['emp']['account_expiry'])):
#                     emp_user.account_expiry = (
#                         request.data['emp']['account_expiry'])
#                 if (request.data['emp']['changepass']):
#                     emp_user.set_password(request.data['emp']['password'])
#                 emp_user.is_active = request.data['emp']['is_active']

#                 for maccess in (request.data['accessdata']):
#                     EmpMenuAccess.objects.filter(
#                         emp_id=emp.id_employee, menu=maccess['menu_id']).update(view=maccess['view'], add=maccess['add'], edit=maccess['edit'], delete=maccess['delete'])
#                 serializer.save()
#                 emp_user.save()
#                 # Logout the edited User
#                 if (emp_user != request.user):
#                     AuthToken.objects.filter(user=emp_user).delete()
#             except Employee.DoesNotExist:
#                 return Response({"error_detail": ["Employee Does Not Exist"]}, status=status.HTTP_400_BAD_REQUEST)
#             return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
#         return Response(status=status.HTTP_400_BAD_REQUEST)

# Admin User Sign Up: (Web) // Emoloyee


class AdminUserSignupView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    serializer_class = EmployeeSignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = AuthToken.objects.create(user)
        return Response({
            "user":
            UserSerializer(user, context=self.get_serializer_context()).data,
            "token":
            token[1],
            "message":
            "account created successfully"
        })

class EmployeeTypeDetils(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = EmployeeType.objects.all()
    serializer_class = EmployeeTypeSerializer
    
    def get(self, request, *args, **kwargs):
        emp_type = self.get_object()
        serializer = EmployeeTypeSerializer(emp_type)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        emp_type = self.get_object()
        serializer = EmployeeTypeSerializer(emp_type, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        emp_type = self.get_object(id)
        emp_type.delete()
        return Response(status=status.HTTP_200_OK)

class EmployeeTypeList(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]

    def get_object(self, obj_id):
        try:
            return EmployeeType.objects.get(id_employee_type=obj_id) 
        except EmployeeType.DoesNotExist:
            raise Http404
    
    def get(self, request, *args, **kwargs):
        emp_type = EmployeeType.objects.all()
        serializer = EmployeeTypeSerializer(emp_type, many=True)
        if 'options' in request.query_params:
            for data in serializer.data:
                data['label'] = data.pop('employee_type')
                data['value'] = data.pop('id_employee_type')
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        serializer = EmployeeTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # for menu in Menu.objects.all():
        #     print(menu.id)
        #     EmpMenuAccess.objects.create(emp_type=EmployeeType.objects.get(
        #         id_employee_type=serializer.data['id_employee_type']),
        #         menu=menu)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class EmployeeOTPCreate(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]

    def post(self, request, *args, **kwargs):
        email = request.data['email']
        otp_for = request.data['otp_for']
        try:
            EmailValidator()(email)
        except ValidationError:
            return Response({"error_detail": ['Invalid email format']}, status=status.HTTP_400_BAD_REQUEST)
        if (User.objects.filter(Q(email=email)).exclude(id=request.user.id).exists()):
            return Response({"error_detail": ['Email already associated with another account']}, status=status.HTTP_400_BAD_REQUEST)
        otp = (randint(100000, 999999))
        # MODE - CREATE ADMIN OTP - now for Email verification for superadmin changed mail - / 1. profile change / 2.verification
        EmployeeOTP.objects.create(otp_for=otp_for, employee=request.user.erpemployee, otp_code=otp,
                                expiry=timezone.now() + timedelta(minutes=2), email_id=email)
        message = f'\n{request.user.erpemployee.firstname}, \n We received a request to update your email on the Jewellery Association Admin. Please use the OTP {otp} to verify this email and complete the process.OTP is valid for 2 minutes only.'
        html_message = render_to_string('verify_email_otp.html', {
                                        "name": request.user.erpemployee.firstname, "code": otp})
        subject = "One Time Password to Verify your Email Address"
        send_mail(html_message=html_message, subject=subject, message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[email])
        return Response({'message': "OTP created and is sent to your email"})
    
# def get_device_id():
#         try:
#             # Use WMIC to get Device ID
#             result = subprocess.check_output('wmic csproduct get UUID', shell=True)
#             result = result.decode('utf-8').split('\n')[1].strip()  # Extract the UUID
#             return result
#         except Exception as e:
#             return f"Error: {str(e)}"

class EmployeeSignInAPI(generics.GenericAPIView):
    serializer_class = EmployeeLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid() == False:
            return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)

        user = serializer.validated_data

        userdata = UserSerializer(user,context=self.get_serializer_context()).data
        emp = (Employee.objects.get(user_id=userdata['id']))
        signserializer = EmployeeSerializer(emp)
        login_branches = (signserializer.data['login_branches'])
        rid_comp = request.data['id_company']
        company = Company.objects.filter(id_company=rid_comp).get()
        preferences = {}

        # branch_ids = [each.id_branch for each in Branch.objects.filter(
        #     id_company=rid_comp)]
        # print(login_branches, branch_ids)
        # if (rid_branch in login_branches):
        #     print("kjhg")
        # # All branch in a company is selected
        # if int(rid_branch) == 0:
        #     # if not a superuser
        #     if not user.is_superuser:

        #         if set(branch_ids) <= set(login_branches):
        #             preferences.update(
        #                 {"id_company": rid_comp, "id_branch": rid_branch})
        #         else:
        #             return Response({"error_detail": ["No Permissions to view all branches"]}, status=status.HTTP_401_UNAUTHORIZED)

        #     # for superuser login allowed irrespective of permissions
        #     else:
        #         preferences.update(
        #             {"id_company": rid_comp, "id_branch": rid_branch})

        # # a branch is selected:
        # else:
        #     if not user.is_superuser:
        #         if rid_branch in login_branches:
        #             preferences.update(
        #                 {"id_company": rid_comp, "id_branch": rid_branch})
        #         else:
        #             return Response({"error_detail": ["No Permissions to view this branch "]}, status=status.HTTP_401_UNAUTHORIZED)
        #     # for super User
        #     else:
        #         preferences.update(
        #             {"id_company": rid_comp, "id_branch": rid_branch})
        
        emp_profile = Profile.objects.get(id_profile=emp.id_profile.pk)
        if(emp_profile.isOTP_req_for_login == True):
            OTP_code = randint(100000, 999999)
            expiry_time = timezone.now() + timedelta(minutes=5)
            if (EmployeeOTP.objects.filter(employee=emp.pk, otp_for="3", expiry__gt=timezone.now()).exists()):
                return Response({"error_detail": ["A valid login OTP already exists. Please use it / wait till its expire"]}, status=status.HTTP_400_BAD_REQUEST)
            EmployeeOTP.objects.create(employee=emp, otp_for="3", email_id=user.email,
                                    otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
            return Response({
            "message": "Enter OTP to login",
            })
        else:
            if emp_profile.device_wise_login:
                if 'deviceID' not in request.data:
                    return Response({"message": "Device ID is required for login"}, status=status.HTTP_401_UNAUTHORIZED)
                try:
                    registered_device = RegisteredDevices.objects.get(ref_no=request.data['deviceID'], is_active=True)
                except RegisteredDevices.DoesNotExist:
                    return Response({"error_detail": ["Invalid or unregistered device"]}, status=status.HTTP_401_UNAUTHORIZED)
                counter_name = registered_device.id_counter.counter_name if registered_device.id_counter else None
                preferences.update({"counter_name": counter_name, "id_counter" : registered_device.id_counter})
            if RegisteredDevices.objects.filter(ref_no=request.data['deviceID'], is_active=True).exists():
                registered_device = RegisteredDevices.objects.get(ref_no=request.data['deviceID'], is_active=True)
                if registered_device.id_counter:
                    preferences.update({"id_counter": registered_device.id_counter.pk, "counter_name": registered_device.id_counter.counter_name})
            if not user.is_superuser:
                if len(login_branches) != 0:
                    preferences.update({
                        "login_branches":login_branches, 
                        "id_company":rid_comp, 
                        "company_name":company.company_name,
                        "company_country":company.country.id_country,
                        "emp_id":emp.pk
                    })    
                else:
                        return Response({"error_detail": ["No Permissions to view any branch "]}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                op =[]
                all_branch =Branch.objects.all()
                all_branch_seri = BranchSerializer(all_branch, many=True)
                for data in all_branch_seri.data:
                    op.append(data['id_branch'])
                preferences.update({
                    "login_branches":op, 
                    "id_company":rid_comp, 
                    "company_name":company.company_name, 
                    "company_country":company.country.id_country,
                    "emp_id":emp.pk})
        
            token = AuthToken.objects.create(user)
            expiry = timezone.localtime(token[0].expiry)
            User.objects.filter(id=user.id).update(
                last_login=datetime.now(tz=timezone.utc))

            def get_ip_address(request):
                user_ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
                if user_ip_address:
                    ip = user_ip_address.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                return ip
            user_ip = get_ip_address(request)
            LoginDetails.objects.create(
                user=user, is_mobile=request.user_agent.is_mobile, is_tablet=request.user_agent.is_tablet,
                is_touch_capable=request.user_agent.is_touch_capable, is_pc=request.user_agent.is_pc, is_bot=request.user_agent.is_bot,
                browser_fam=request.user_agent.browser.family, browser_ver=request.user_agent.browser.version_string,
                os_fam=request.user_agent.os.family, os_ver=request.user_agent.os.version_string,
                device_fam=request.user_agent.device.family, device_brand=request.user_agent.device.brand,
                signin_time=datetime.now(), ip_address=user_ip)
            # print ("The MAC address in formatted way is : ", end="")
            # print (':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
            # for ele in range(0,8*6,8)][::-1]))
            # print(gma())
            # print(subprocess.Popen('dmidecode.exe -s system-uuid'.split()))
            # if sys.platform == 'win32' or sys.platform == 'cygwin' or sys.platform == 'msys':
            #     id = read_win_registry('HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography', 'MachineGuid')
            #     if not id:
            #         id = execute('wmic csproduct get uuid').split('\n')[2].strip()
            #         print(id)
            # device_id = get_device_id()
            # print(f"Device ID: {device_id}")
            return Response({
                "token": token[1],
                "login_expiry": expiry,
                "redirect" : True,
                "success" : True,
                "employee": signserializer.data,
                "preferences": preferences
            })


class EmployeeChangePassword(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, *args, **kwargs):
        user = (request.user)
        if (request.data['old_password'] == request.data['new_password']):
            return Response({"error_detail": ['New Password and Old password cant be same']}, status=status.HTTP_400_BAD_REQUEST)
        if bool(user.check_password(request.data['old_password'])) == False:
            return Response({"error_detail": ['Incorrect password entered as Current Password']}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(request.data['new_password'])
        user.save()
        # User.objects.filter(id=user.id).update(pass_updated=datetime.now())
        # Delete all  Tokens of this user to logout from other Devices other than This Device/Browser --
        AuthToken.objects.filter(user=user).exclude(
            token_key=request.auth.token_key).delete()
        return Response({"message": "Password changed successfully"})


# Update Admin by self
class EmployeeChange(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, *args, **kwargs):
        user = (request.user)
        data = request.data.copy()
        request.data.pop('email')

        # # Case - When OTP is entered with other data to  save email
        # if ('email_otp' in request.data):
        #     # Delete Expired OTPs of all users.  || Later:  Need to check case of Valid OTPs of this User other than email in request
        #     EmployeeOTP.objects.filter(expiry__lt=timezone.now()).delete()
        #     ##
        #     try:
        #         latest_otp = EmployeeOTP.objects.filter(
        #             employee=request.user.erpemployee, email_id=data['email'], otp_for=1, expiry__gte=timezone.now()).latest('creation_time')
        #         if (latest_otp.otp_code == request.data['email_otp']):
        #             try:
        #                 user.email = data['email']
        #                 user.save()
        #             except IntegrityError:
        #                 return Response({"error_detail": ['Email already associated with another account']}, status=status.HTTP_400_BAD_REQUEST)
        #             request.user.erpemployee.firstname = request.data['name']
        #             request.user.erpemployee.save()
        #             # Delete this OTP because its usage is over.
        #             latest_otp.delete()
        #             # Delete OTP related with user & email
        #             EmployeeOTP.objects.filter(
        #                 employee=request.user.erpemployee, email_id=data['email']).delete()  # / mutli request scenario
        #             return Response({"success": True, 'message': "Profile updated with email being successfully verified"})
        #         else:
        #             raise EmployeeOTP.DoesNotExist
        #     except EmployeeOTP.DoesNotExist:
        #         return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)

        # # Case - When Email is changed... OTP is sent to verify the email
        # if (user.email != data['email']):
        #     if User.objects.filter(
        #             email=data['email']).exclude(id=user.pk).exists():
        #         return Response({"error_detail": ['Email already associated with another account']}, status=status.HTTP_400_BAD_REQUEST)

        #     otp = (randint(100000, 999999))
        #     message = f'\n{request.user.erpemployee.firstname}, \n We received a request to update your email on the Jewellery Association Admin. Please use the OTP {otp} to verify this email and complete the process.OTP is valid for 2 minutes only.'
        #     subject = "One Time Password to Verify your Email Address"
        #     # MODE - WHEN EMAIL IS CHANGED by SELF- OTP is sent
        #     EmployeeOTP.objects.create(employee=request.user.erpemployee, otp_code=otp,
        #                             expiry=timezone.now() + timedelta(minutes=2), email_id=data['email'], otp_for=1)
        #     html_message = render_to_string('verify_email_otp.html', {
        #         "name": request.user.erpemployee.firstname, "code": otp})
        #     send_mail(subject=subject, message=message, html_message=html_message,
        #               from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[data['email']])
        #     return Response({"success": True, "message": "Email verification Required"}, status=status.HTTP_200_OK)

        # # Case - When Only Admin Name is Changed
        # request.user.erpemployee.firstname = request.data['name']
        # request.user.erpemployee.save()
        if (user.email != data['email']):
            try:
                EmailValidator()(data['email'])
            except:
                return Response({"error_detail": ['Enter valid email address']}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(
                    email=data['email']).exclude(id=user.pk).exists():
                return Response({"error_detail": ['Email already associated with another account']}, status=status.HTTP_400_BAD_REQUEST)
            else:
                User.objects.filter(id=user.pk).update(email = data['email'], first_name = data['fname'], last_name=data['lname'])
                Employee.objects.filter(user=user.pk).update(email_verified=False, firstname=data['fname'], lastname=data['lname'])
                
        User.objects.filter(id=user.pk).update(first_name = data['fname'], last_name=data['lname'])
        Employee.objects.filter(user=user.pk).update(firstname=data['fname'], lastname=data['lname'])
        return Response({"success": True, "message": "Profile Updated"}, status=status.HTTP_200_OK)

class EmployeeResendOTP(generics.GenericAPIView):
    permission_classes = [AllowAnyOrIsEmployee]
    
    def post(self, request, *args, **kwargs):
        otp_for = request.data['otp_for']
        user = User.objects.filter(id=request.user.pk).get()
        emp = Employee.objects.filter(user_id = request.user.pk).get()
        OTP_code = randint(100000, 999999)
        expiry_time = timezone.now() + timedelta(minutes=5)
        if (EmployeeOTP.objects.filter(employee=emp.pk, otp_for=otp_for).exists()):
            EmployeeOTP.objects.filter(employee=emp.pk, otp_for=otp_for).delete()
        EmployeeOTP.objects.create(employee=emp, otp_for=otp_for, email_id=user.email,
                                otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
        return Response({"message": "OTP has been resent to your mobile number."})


# Verify Admin OTP:
class EmployeeOTPVerify(generics.GenericAPIView):
    permission_classes = [AllowAnyOrIsEmployee]

    def post(self, request, *args, **kwargs):
        if 'email_otp' in request.data:
            # Delete Expired OTPs of all users.  || Later:  Need to check case of Valid OTPs of this User other than email in request
            EmployeeOTP.objects.filter(expiry__lt=timezone.now()).delete()
            try:
                # otp  for  -- "2", "Email Verify OTP" - change if any other scenario uses this API view
                latest_otp = EmployeeOTP.objects.filter(
                    employee=request.user.erpemployee, otp_for=2, email_id=request.data['email'], expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['email_otp']):
                    request.user.erpemployee.email_verified = True
                    request.user.erpemployee.save()
                    # Delete this OTP because its usage is over.
                    latest_otp.delete()
                    # Delete OTP related with user & email
                    EmployeeOTP.objects.filter(otp_for=2,
                        employee=request.user.erpemployee, email_id=request.data['email']).delete()  # / mutli request scenario
                    return Response({'message': "OTP verified"})
                else:
                    raise EmployeeOTP.DoesNotExist
            except EmployeeOTP.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)
            
        
        if 'bill_cancel_otp' in request.data:
            EmployeeOTP.objects.filter(expiry__lt=timezone.now()).delete()
            try:
                user = User.objects.filter(id = request.user.id).get()
                employee = Employee.objects.filter(user = request.user.id).get()
                latest_otp = EmployeeOTP.objects.filter(
                    employee=employee.pk, otp_for="4", email_id=user.email, expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['bill_cancel_otp']):
                    try:
                        cancel_bill(request)
                        # Delete this OTP because its usage is over.
                        latest_otp.delete()
                        # Delete OTP related with user & email
                        EmployeeOTP.objects.filter(
                            employee=employee.pk, otp_for="4", email_id=user.email).delete()  # / mutli request scenario
                        return Response({'message': "OTP verified and bill has been canceled."}, status=status.HTTP_201_CREATED)
                        # return Response({"message":"Invoice Canceled Successfully."}, status=status.HTTP_201_CREATED)
                    except IntegrityError as e:
                        tb = traceback.format_exc()
                        return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
                    except KeyError as e:
                        tb = traceback.format_exc()
                        return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)    
                else:
                    raise EmployeeOTP.DoesNotExist
            except EmployeeOTP.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)
            
        if 'account_close_otp' in request.data:
            EmployeeOTP.objects.filter(expiry__lt=timezone.now()).delete()
            try:
                user = User.objects.filter(id = request.user.id).get()
                employee = Employee.objects.filter(user = request.user.id).get()
                latest_otp = EmployeeOTP.objects.filter(
                    employee=employee.pk, otp_for="7", email_id=user.email, expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['account_close_otp']):
                    sch_account = SchemeAccount.objects.filter(id_scheme_account=request.data['sch_id']).get()
                    emp = Employee.objects.filter(user=request.user).get()
                    branch = Branch.objects.filter(id_branch=request.data['closing_id_branch']).get()
                    sch_account.closed_employee = emp
                    sch_account.closing_id_branch = branch
                    sch_account.is_closed = True
                    sch_account.closing_date = date.today()
                    sch_account.total_paid_ins = request.data['total_paid_ins']
                    sch_account.closing_balance = request.data['closing_balance']
                    sch_account.closing_amount = request.data['closing_amount']
                    sch_account.closing_weight = request.data['closing_weight']
                    # sch_account.closed_remarks = request.data['closed_remarks']
                    sch_account.closing_deductions = request.data['closing_deductions']
                    sch_account.additional_benefits = request.data['additional_benefits']
                    sch_account.closing_benefits = request.data['closing_benefits']
                    sch_account.save()

                    # sch_seri = SchemeAccountSerializer(sch_account)
                    # Delete this OTP because its usage is over.
                    latest_otp.delete()
                    # Delete OTP related with user & email
                    EmployeeOTP.objects.filter(
                        employee=employee.pk, otp_for="7", email_id=user.email).delete()  # / mutli request scenario
                    return Response({'message': "OTP verified and account has been closed successfully."}, status=status.HTTP_201_CREATED)
                else:
                    raise EmployeeOTP.DoesNotExist
            except EmployeeOTP.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'payment_cancel_otp' in request.data:
            EmployeeOTP.objects.filter(expiry__lt=timezone.now()).delete()
            try:
                user = User.objects.filter(id = request.user.id).get()
                employee = Employee.objects.filter(user = request.user.id).get()
                latest_otp = EmployeeOTP.objects.filter(
                    employee=employee.pk, otp_for="6", email_id=user.email, expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['payment_cancel_otp']):
                    with transaction.atomic():
                        for data in request.data['cancel_payments']:
                            if(data['cancel'] == True):
                                cancel_payment(data, request)
                                # Delete this OTP because its usage is over.
                                latest_otp.delete()
                                # Delete OTP related with user & email
                                EmployeeOTP.objects.filter(
                                    employee=employee.pk, otp_for="6", email_id=user.email).delete()  # / mutli request scenario
                                return Response({'message': "OTP verified and tags generated successfully."}, status=status.HTTP_201_CREATED)
                            else:
                                return Response(status=status.HTTP_200_OK)
                else:
                    raise EmployeeOTP.DoesNotExist
            except EmployeeOTP.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)
        
        
        if 'tag_print_otp' in request.data:
            EmployeeOTP.objects.filter(expiry__lt=timezone.now()).delete()
            try:
                user = User.objects.filter(id = request.user.id).get()
                employee = Employee.objects.filter(user = request.user.id).get()
                latest_otp = EmployeeOTP.objects.filter(
                    employee=employee.pk, otp_for="5", email_id=user.email, expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['tag_print_otp']):
                    tag_url = generate_bulk_tag_print(request.data['tagData'],request)
                    # Delete this OTP because its usage is over.
                    latest_otp.delete()
                    # Delete OTP related with user & email
                    EmployeeOTP.objects.filter(
                        employee=employee.pk, otp_for="5", email_id=user.email).delete() 
                    return Response({'message': "OTP verified and payments cancelled successfully.",
                        "tag_url":tag_url}, status=status.HTTP_200_OK)
                else:
                    raise EmployeeOTP.DoesNotExist
            except EmployeeOTP.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)
            
            
        if 'login_otp' in request.data:
            preferences = {}
            # user = User.objects.filter(username = request.data['username']).get()
            EmployeeOTP.objects.filter(expiry__lt=timezone.now()).delete()
            try:
                serializer = self.get_serializer(data=request.data)
                if serializer.is_valid() == False:
                    return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)
                user = serializer.validated_data
                
                userdata = UserSerializer(user,context=self.get_serializer_context()).data
                emp = (Employee.objects.get(user_id=userdata['id']))
                signserializer = EmployeeSerializer(emp)
                
                latest_otp = EmployeeOTP.objects.filter(
                    employee=emp.pk, otp_for="3", email_id=request.data['email'], expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['login_otp']):
                    
                    login_branches = (signserializer.data['login_branches'])
                    rid_comp = request.data['id_company']
                    company = Company.objects.filter(id_company=rid_comp).get()
                    preferences = {}

                    emp_profile = Profile.objects.get(id_profile=emp.id_profile.pk)
                    if emp_profile.device_wise_login:
                        if 'deviceID' not in request.data:
                            return Response({"error_detail": ["Device ID is required for login"]}, status=status.HTTP_401_UNAUTHORIZED)
                        try:
                            registered_device = RegisteredDevices.objects.get(ref_no=request.data['deviceID'], is_active=True)
                        except RegisteredDevices.DoesNotExist:
                            return Response({"error_detail": ["Invalid or unregistered device"]}, status=status.HTTP_401_UNAUTHORIZED)
                        counter_name = registered_device.id_counter.name if registered_device.id_counter else None
                        preferences.update({"counter_name": counter_name})

                    if not user.is_superuser:
                        if len(login_branches) != 0:
                            preferences.update({"login_branches":login_branches, "id_company":rid_comp, "company_name":company.company_name})    
                        else:
                                return Response({"error_detail": ["No Permissions to view any branch "]}, status=status.HTTP_401_UNAUTHORIZED)
                    else:
                        op =[]
                        all_branch =Branch.objects.all()
                        all_branch_seri = BranchSerializer(all_branch, many=True)
                        for data in all_branch_seri.data:
                            op.append(data['id_branch'])
                        preferences.update({"login_branches":op, "id_company":rid_comp, 
                                            "company_name":company.company_name, "company_country":company.country.id_country})

                    token = AuthToken.objects.create(user)
                    expiry = timezone.localtime(token[0].expiry)
                    User.objects.filter(id=user.id).update(
                        last_login=datetime.now(tz=timezone.utc))

                    def get_ip_address(request):
                        user_ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
                        if user_ip_address:
                            ip = user_ip_address.split(',')[0]
                        else:
                            ip = request.META.get('REMOTE_ADDR')
                        return ip
                    user_ip = get_ip_address(request)
                    LoginDetails.objects.create(
                        user=user, is_mobile=request.user_agent.is_mobile, is_tablet=request.user_agent.is_tablet,
                        is_touch_capable=request.user_agent.is_touch_capable, is_pc=request.user_agent.is_pc, is_bot=request.user_agent.is_bot,
                        browser_fam=request.user_agent.browser.family, browser_ver=request.user_agent.browser.version_string,
                        os_fam=request.user_agent.os.family, os_ver=request.user_agent.os.version_string,
                        device_fam=request.user_agent.device.family, device_brand=request.user_agent.device.brand,
                        signin_time=datetime.now(), ip_address=user_ip)
                    # Delete this OTP because its usage is over.
                    latest_otp.delete()
                    # Delete OTP related with user & email
                    EmployeeOTP.objects.filter(
                        employee=emp.pk, otp_for="3", email_id=request.data['email']).delete()  # / mutli request scenario
                    return Response({
                        "token": token[1],
                        "login_expiry": expiry,
                        "redirect" : True,
                        "employee": signserializer.data,
                        "preferences": preferences
                    })
                else:
                    raise EmployeeOTP.DoesNotExist
            except EmployeeOTP.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error_detail": ['Invalid Request']}, status=status.HTTP_400_BAD_REQUEST)


# Reset Admin Password:
class EmployeeResetPassword(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if 'reset_password' in request.data:
            try:
                try:
                    EmailValidator()(request.data['user'])
                    user = User.objects.filter(is_adminuser=True).get(
                        email=request.data['user'])
                except:
                    user = User.objects.filter(is_adminuser=True).get(
                        username=request.data['user'])
                employee = Employee.objects.filter(user=user).get()
                #
                # check if already a reset link/otp request exists with expiry time still left
                if (EmployeeOTP.objects.filter(employee=employee.pk, otp_for=0, email_id=user.email, expiry__gt=timezone.now()).exists()):
                    return Response({"error_detail": ["A valid reset OTP already exists. Please use it / wait till its expire"]}, status=status.HTTP_400_BAD_REQUEST)
                #
                subject = "OTP to reset your Password"
                # origin = request.data['origin']
                OTP_code = randint(100000, 999999)
                encOTP = fernet.encrypt(str(OTP_code).encode())
                # MODE - ADMIN PASSWORD RESET / FORGOT
                EmployeeOTP.objects.create(employee=employee, otp_for=0, email_id=user.email,
                                        otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
                message = f"Use this OTP to reset your password and to enter new password. \n This link is valid for next 5 minutes only"
                html_message = render_to_string(
                    'reset_email_template.html', { "encOTP": OTP_code, "name": employee.firstname, "account_type": "Admin", "path": "auth-reset/confirm_reset"})
                send_mail(subject=subject, message=message,
                          from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[user.email], html_message=html_message)
                # delete old OTPs created for passsword reset
                EmployeeOTP.objects.filter(
                    employee=employee.pk,  otp_for=0, expiry__lt=timezone.now()).delete()
                return Response({"success": True, "message": "Email with OTP for reset password has been sent"})
            except User.DoesNotExist:
                return Response({"error_detail": ["No User Found with provided details"]}, status=status.HTTP_400_BAD_REQUEST)
        if 'change_password' in request.data:
            # passing invalid OTP/encrypted code ... / if code is malfunctioned
            try:
                decOTP = fernet.decrypt(
                    request.data['reset_code'].encode('utf-8')).decode()
            except InvalidToken:
                return Response({"error_detail": ["Invalid password reset link. Please request reset link again "]}, status=status.HTTP_400_BAD_REQUEST)
            #
            if (EmployeeOTP.objects.filter(otp_code=decOTP, otp_for=0,
                                        expiry__gte=timezone.now()).exists()):
                instance = EmployeeOTP.objects.get(otp_code=decOTP)
                user = instance.erpemployee.user
                user.set_password(request.data['passwd'])
                user.save()
                # delete used OTP:
                instance.delete()
                # Delete users all tokens:
                AuthToken.objects.filter(user=user).delete()
                return Response({"success": True, 'message': "Password is reset successfully"})
            return Response({"error_detail": ["Invalid/Expired link used. Please request reset link again"]}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error_detail": []}, status=status.HTTP_400_BAD_REQUEST)
    
class ActiveEmployeeAPI(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()

    def get(self,request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={"request":request})
        return Response(serializer.data)
