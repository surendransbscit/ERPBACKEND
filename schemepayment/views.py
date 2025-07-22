from django.shortcuts import render
from django.http import HttpResponse, request, Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from datetime import datetime, timedelta, date
from django.db import transaction,IntegrityError
from django.db.models import Sum,Max
from django.core.exceptions import ObjectDoesNotExist,ValidationError
from django.db.models import Q
from django.conf import settings
import os
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from random import randint
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from threading import Thread
import time
from decimal import Decimal

import logging
#Import Models
from core.renderers import CustomJSONRenderer, DecimalWithPrecision
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee,isSuperuser,IsEmployeeOrCustomer
from managescheme.models import (SchemeAccount)
from customers.models import (Customers, CustomerAddress)
from employees.models import (Employee, EmployeeSettings)
from .models import (Payment,PaymentStatus,PaymentModeDetail)
from schememaster.models import (PaymentSettings,Scheme, SchemeDigiGoldInterestSettings)
from retailmasters.models import (MetalRates, Branch,metalRatePurityMaster, PaymentMode,PaymentGateway, Profile)
from retailcataloguemasters.models import (Purity)
from crmsettings.models import (ChitSettings)
from accounts.models import (User)
from core.models import (EmployeeOTP)
from managescheme.views import (RateMasterClass)
from utilities.constants import FILTERS
from core.views  import get_reports_columns_template
from notifications.views import (send_notification_for_scheme_payment)

#Import Views
from retailmasters.views import BranchEntryDate
from managescheme.views import SchemeAccountPaidDetails,SchemePaymentSettings
#Import Serializers
from managescheme.serializers import (SchemeAccountSerializer)
from schememaster.serializers import (SchemeSerializer,PaymentSettingsSerializer)
from customers.serializers import (CustomerSerializer)
from retailmasters.serializers import (MetalRatePurityMasterSerializer,PaymentGatewaySerializer,PaymentModeSerializer)
from retailcataloguemasters.serializers import (PuritySerializer)
from crmsettings.serializers import (ChitSettingsSerializer)
from .serializers import (PaymentSerializer,PaymentModeDetailSerializer,PaymentStatusSerializer)

#Import Services
from services import cashfree_service
from services.cc_avenue_service import encrypt,decrypt

#Import constants
from utilities.pagination_mixin import PaginationMixin
from utilities.utils import format_date,format_number_with_decimal,format_currency_with_symbol, date_format_with_time
from .constants import PAYMENT_COLUMN_LIST,ACTION_LIST

pagination = PaginationMixin()  # Apply pagination

from cryptography.fernet import Fernet
from retailsettings.models import (RetailSettings)
fernet = Fernet(os.getenv('crypt_key'))

class AutoGenerate:
    
    def generate_payment_receipt_no(self, id_payment,id_scheme, id_branch):
        queryset = ChitSettings.objects.latest('id')
        setting = queryset.receipt_no_setting
        if (setting == 1):
           last_payment = Payment.objects.filter(~Q(receipt_no=None),id_scheme=id_scheme).aggregate(Max('receipt_no'))
        elif(setting == 2):
            last_payment = Payment.objects.filter(~Q(receipt_no=None),id_branch=id_branch).aggregate(Max('receipt_no'))
        else:
            last_payment = Payment.objects.filter(~Q(receipt_no=None),id_scheme=id_scheme, id_branch=id_branch).aggregate(Max('receipt_no'))
        if last_payment['receipt_no__max']!='' and last_payment['receipt_no__max'] is not None:
            print(last_payment['receipt_no__max'])
            receipt_no = f"{int(last_payment['receipt_no__max']) + 1:05d}"
        else:
            receipt_no = '00001'
        Payment.objects.filter(id_payment=id_payment).update(receipt_no=receipt_no)
    
    
    def generate_scheme_acc_no(self, id_scheme_account,id_scheme, id_branch):
        queryset = ChitSettings.objects.latest('id')
        setting = queryset.receipt_no_setting
        if (setting == 1):
            last_account = SchemeAccount.objects.filter(~Q(scheme_acc_number=None), acc_scheme_id=id_scheme).aggregate(Max('scheme_acc_number'))
        elif(setting == 2):
            last_account=SchemeAccount.objects.filter(~Q(scheme_acc_number=None), id_branch=id_branch).aggregate(Max('scheme_acc_number'))
        else:
            last_account=SchemeAccount.objects.filter(~Q(scheme_acc_number=None), acc_scheme_id=id_scheme, id_branch=id_branch).aggregate(Max('scheme_acc_number'))
        if last_account['scheme_acc_number__max'] is not None:
            scheme_acc_number = f"{int(last_account['scheme_acc_number__max']) + 1:05d}"
        else:
            scheme_acc_number = '00001'
        SchemeAccount.objects.filter(id_scheme_account = id_scheme_account).update(scheme_acc_number=scheme_acc_number)
 
    
class SchemePaymentView(generics.ListCreateAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    queryset =  Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get(self, request, *args, **kwargs):
        customer_id = request.query_params['customer']
        scheme_id = request.query_params['scheme']
        branch_ids_list = list(map(int, request.query_params['branch'].split(',')))
        # queryset = Payment.objects.filter(id_branch__in=branch_ids_list, date_payment__lte=request.query_params['to'],
        #                                   date_payment__gte=request.query_params['from'])
        queryset = Payment.objects.all()
        if(customer_id != 'undefined' and customer_id != 'null'):
            queryset = queryset.filter(id_scheme_account__id_customer=customer_id)
        else:
            queryset = Payment.objects.filter(id_branch__in=branch_ids_list, date_payment__lte=request.query_params['to'],
                                          date_payment__gte=request.query_params['from'])
            if(scheme_id != 'undefined' and scheme_id != 'null' and scheme_id != ''):
                queryset = queryset.filter(id_scheme=scheme_id)
        paginator, page = pagination.paginate_queryset(queryset, request,None,PAYMENT_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,PAYMENT_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)

        output=[]
        for index,data in enumerate(serializer.data):
            result = {}
            acc_result      = SchemeAccount.objects.filter(id_scheme_account=data['id_scheme_account']).get()
            pay_status      = PaymentStatus.objects.filter(id=data['payment_status']).get()
            branch_name     = ''
            employee_name   = ''
            if (data['id_branch']):
                branch          = Branch.objects.get(id_branch=data['id_branch'])
                branch_name     = branch.name
            if(data['created_by']):
                try :
                    employee      = Employee.objects.get(user=data['created_by'])
                    print(employee.emp_code)
                    employee_name = f"{employee.firstname}-{employee.emp_code}"
                except Employee.DoesNotExist:
                    employee_name = ''
            result.update({
                'sno'               :index+1,
                'pk_id'             :data['id_payment'],
                'id_payment'        :data['id_payment'],
                'acc_name'          :acc_result.account_name, 
                'id_scheme_account' :data['id_scheme_account'],
                'installment'       :data['installment'],
                'scheme_account'    :acc_result.scheme_acc_number if acc_result.scheme_acc_number !='' else 'Not Allocated',
                'metal_weight'      :data['metal_weight'],
                'payment_amount'    :data['payment_amount'],
                'metal_rate'        :data['metal_rate'],
                'date_payment'      :format_date(data['entry_date']),
                'receipt_no'        :data['receipt_no'] if data['receipt_no'] != None else '',
                "scheme_code"       :acc_result.acc_scheme_id.scheme_code,
                "scheme_name"       :acc_result.acc_scheme_id.scheme_name,
                # "mobile"            :acc_result.id_customer.mobile,
                "cus_name"          :acc_result.id_customer.firstname,
                "payment_status"    :pay_status.name,
                "status_color"      :pay_status.color,
                "branch_name"       :branch_name,
                "employee_name"     :employee_name,
                "paid_through"      :data['paid_through_display']
            })
            if(acc_result.scheme_acc_number !='' and acc_result.scheme_acc_number is not None):
                result.update({'account_no':acc_result.scheme_acc_number,
                               'sch_pk_id' : acc_result.id_scheme_account})
                
            employee = Employee.objects.filter(user = request.user.pk).get()
            show_full_number = EmployeeSettings.objects.get(id_employee=employee.pk).is_show_full_mobile
            if acc_result.id_customer.mobile != None and len(acc_result.id_customer.mobile)>15:
                try:
                    decrypted_mobile = fernet.decrypt(str(acc_result.id_customer.mobile).encode()).decode()

                    if show_full_number:
                        # Show full mobile number
                        result.update({"mobile":acc_result.id_customer.mob_code+"-"+decrypted_mobile,
                             "mobile_woc":decrypted_mobile})
                    else:
                        # Mask the mobile number (e.g., show first 2 and last 2 digits)
                        masked_mobile = decrypted_mobile[:2] + "X" * (len(decrypted_mobile) - 4) + decrypted_mobile[-2:]
                        result.update({"mobile":acc_result.id_customer.mob_code+"-"+masked_mobile,
                             "mobile_woc":masked_mobile})
                except Exception as e:
                    print("Decryption failed:", str(e))
            else:
                result.update({"mobile":acc_result.id_customer.mob_code+"-"+acc_result.id_customer.mobile,
                             "mobile_woc":acc_result.id_customer.mobile})
            if result not in output:
                output.append(result)
        filters_copy = FILTERS.copy()
        filters_copy['isSchemeFilterReq']=True
        filters_copy['isCustomerFilterReq']=True
        context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'filters':filters_copy,
                'is_filter_req':True
            }
        return pagination.paginated_response(output,context) 
    
    
    def post(self, request, *args, **kwargs):
        try:
            pay_validation      = ValidatePayment()
            payment_validation  = pay_validation.validate_payment(request.data)
            id_payment = ''
            if(payment_validation['status']!=True):
                return Response({"message": payment_validation['message']}, status=status.HTTP_400_BAD_REQUEST)
            total_payment_amount = payment_validation["order_amount"]
            payment_status       = 1 #Success
            paid_through         = request.data[0]['paid_through']
            id_pay_gateway       = request.data[0]['id_payGateway'] 
            payment_session_id   = None
            order_id             = None
            customer = Customers.objects.filter(user=request.user.pk).first()
            if((paid_through==2 or paid_through==3) and (id_pay_gateway!='' and id_pay_gateway!=None)): # For Mobile App and Collection App
                query_set = PaymentGateway.objects.get(id_pg=id_pay_gateway)
                payment_status = 3 ## Pending
                gateway_serializer = PaymentGatewaySerializer(query_set,many=False)
                
                if(gateway_serializer.data['pg_code']=='cashfree'):
                        order_details = generate_order_details(customer.pk,payment_validation["order_amount"])
                        order_id = order_details["order_id"]
                        order_details.update({"client_id":gateway_serializer.data["param_1"],"secret_key":gateway_serializer.data["param_2"],"api_url":gateway_serializer.data["api_url"]})
                if(gateway_serializer.data['pg_code']=='cc_avenue'):
                        order_details = generate_cc_avenue_order_details(customer.pk,payment_validation["order_amount"],gateway_serializer.data["param_1"],gateway_serializer.data["param_3"])
                        order_id = order_details["order_id"]
            with transaction.atomic():
                for data in request.data:
                    autogenerate = AutoGenerate()
                    if(paid_through!=2):
                        pay_det      = data['payment_mode_details']
                        del data['payment_mode_details']
                    if data['id_scheme_account']!=None and data['id_scheme_account']!='':
                        scheme_account = SchemeAccount.objects.filter(id_scheme_account = data['id_scheme_account']).get()
                        scheme_id      = scheme_account.acc_scheme_id.pk
                    else:
                        scheme_id = data['scheme_id']
                    scheme          = Scheme.objects.filter(scheme_id = scheme_id).get()
                    branch_date = BranchEntryDate()
                    if data['id_branch']!='' and data['id_branch']!=0 and data['id_branch']!=None:
                        entry_date = branch_date.get_entry_date(data['id_branch'])
                    else:
                        data.update({"id_branch" : None })
                        entry_date = date.today()
                    #Update Payment Details
                    data.update({
                        "receipt_no"    :'',
                        "order_id"      :order_id,
                        "entry_date"    :entry_date,
                        "id_scheme"     :scheme_id,
                        "created_by"    :request.user.pk,
                        "payment_status":payment_status,
                    })

                    if (scheme.scheme_type == 2):

                        # For Digi Gold Scheme
                        if data['id_scheme_account']=='':
                            if paid_through == 2:
                                data.update({
                                    "account_name":data['acc_name'],
                                    "acc_scheme_id":data['scheme_id'],
                                    "id_customer":customer.pk,
                                })

                        rate_master  = RateMasterClass()
                        metal_rate  = rate_master.get_metal_rates(scheme.sch_id_purity.pk, scheme.sch_id_metal.pk)
                        if data['id_scheme_account']!=None and data['id_scheme_account']!='':
                            joined_date = scheme_account.start_date
                        else:
                            joined_date = date.today()
                        today = date.today()

                        days_elapsed = (today - joined_date).days
                        interest_setting = SchemeDigiGoldInterestSettings.objects.filter(
                            scheme=scheme.pk,
                            from_day__lte=days_elapsed,
                            to_day__gte=days_elapsed
                        ).first()
                        
                        interest_percentage = 0
                        if interest_setting:
                            interest_percentage = interest_setting.interest_percentage
                        # else:
                        #     interest_percentage = 0
                        
                        # metal_weight = float(data.get("metal_weight", 0))
                        metal_weight = (float(data['payment_amount']) / float(metal_rate))
                        digi_interest_value = (metal_weight * float(interest_percentage)) / 100
                        digi_interest_amount_value = (float(data['payment_amount']) * float(interest_percentage)) / 100
                        digi_interest_value = float(f"{digi_interest_value:.3f}")
                        digi_interest_amount_value = float(f"{digi_interest_amount_value:.2f}")
                        data.update({'bonus_metal_weight':digi_interest_value,
                                     'bonus_metal_amount':digi_interest_amount_value})
                    advance = int(data['advance']) + 1
                    
                    for x in range(1, advance):
                        if (x > 1):
                            data.update({"due_type":"AD"})
                        else:
                            data.update({"due_type":"ND"})
                        data.update({"installment":int(data['installment'] + 1)})
                        data.update({"date_payment":date.today()})
                        
                        pay_serializer = PaymentSerializer(data=data)
                        pay_serializer.is_valid(raise_exception=True)
                        if pay_serializer.save():
                            id_payment = pay_serializer.data['id_payment']
                            
                            if(paid_through!=2): # paid_through - Mobile app
                                for mode_each in pay_det:
                                    mode_each.update({"id_pay":pay_serializer.data['id_payment']})
                                    mode_serializer = PaymentModeDetailSerializer(data=mode_each)
                                    mode_serializer.is_valid(raise_exception=True)
                                    mode_serializer.save()
                            
                            #Receipt and Account Number Update
                            if data['id_scheme_account']!=None and data['id_scheme_account']!='':
                                if(scheme_account.scheme_acc_number == None):
                                    autogenerate.generate_scheme_acc_no(data['id_scheme_account'],scheme.scheme_id, data['id_branch'])

                            if(id_pay_gateway=='' or id_pay_gateway==None):
                                autogenerate.generate_payment_receipt_no(pay_serializer.data['id_payment'],scheme.scheme_id, data['id_branch'])
                                
                        # Free Installment Condition
                        if scheme.has_free_installment and (data['installment'] + 1) == scheme.free_installment:
                            free_installment_data = {
                                "id_scheme_account": data["id_scheme_account"],
                                "id_scheme": scheme.scheme_id,
                                "date_payment": date.today(),
                                "installment": data["installment"] + 1,
                                "id_branch": data["id_branch"],
                                "payment_amount": 0,  # Free installment, so amount is 0
                                "net_amount": 0,
                                "payment_status": 1,
                                "is_free_installment": True,
                                "created_by": request.user.pk,
                                "entry_date": entry_date,
                            }
                            free_payment_serializer = PaymentSerializer(data=free_installment_data)
                            free_payment_serializer.is_valid(raise_exception=True)
                            free_payment_serializer.save()
                    if data['id_scheme_account']!=None and data['id_scheme_account']!='':
                        SchemeAccount.objects.filter(id_scheme_account = data['id_scheme_account']).update(total_paid_ins=scheme_account.total_paid_ins + int(data['advance']))
                                
                if((paid_through==2 or paid_through==3) and (id_pay_gateway!='' or id_pay_gateway!=None)):
                    if(gateway_serializer.data["pg_code"]=='cashfree'):
                        gateway_response = cashfree_service.create_order(order_details)
                        print(gateway_response)
                        if(gateway_response['status']):
                            gateway_result = gateway_response["result"]
                            payment_session_id = gateway_result['payment_session_id']
                            Payment.objects.filter(order_id = order_id).update(payment_session_id=payment_session_id)
                        else:
                            return Response({"message": gateway_response['message']}, status=status.HTTP_400_BAD_REQUEST)  
            notify_data = {
                "payment_id": id_payment,
            }
            # send_notification_for_scheme_payment(customer.pk, notify_data)          
            return Response({
                "message":"Payment Created successfully.",
                "payment_session_id":payment_session_id,
                "order_id":order_id,"order_amount":total_payment_amount,
                "id_payment":id_payment,
                "pdf_path":"payment/receipt",
                "encRequest" : order_details["enc_request"] if order_details else None,
                "access_code" : gateway_serializer.data["param_2"],
                "payment_url" : gateway_serializer.data["api_url"],
                },status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)

class SchemePaymentStatusUpdateView(generics.ListCreateAPIView):
    permission_classes = [IsEmployeeOrCustomer]


    def update_cash_free_payment_mode(self,order_id,id_payment,payment_amount):
        try:
            cash_free_response = cashfree_service.get_gateway_order_details(order_id)
            if len(cash_free_response['result']) > 0:
                for cash_free_data in cash_free_response['result']:
                    mode_details = {}
                    id_payment_mode = ''
                    id_payment_status = ''
                    
                    if not PaymentMode.objects.filter(mode_name = cash_free_data['payment_group']).exists():
                        gateway_payment_mode = {"mode_name": cash_free_data['payment_group'],"short_code":cash_free_data['payment_group'], "show_to_pay": False}
                        mode = PaymentMode.objects.create(**gateway_payment_mode)
                        serializer = PaymentModeSerializer(data=mode)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        id_payment_mode = serializer.data['id_mode']
                    else:
                        id_payment_mode = PaymentMode.objects.get(mode_name = cash_free_data['payment_group']).pk
                    
                    if not PaymentStatus.objects.filter(name = cash_free_data['payment_status']).exists():
                        gateway_payment_status = {"name": cash_free_data['payment_status'], "color": "#000000"}
                        status = PaymentStatus.objects.create(**gateway_payment_status)
                        serializer = PaymentStatusSerializer(data=status)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        id_payment_status = serializer.data['id']
                    else:
                        id_payment_status = PaymentStatus.objects.get(name = cash_free_data['payment_status']).pk
    
                    mode_details.update({
                        "id_pay" : id_payment,
                        "payment_mode" : id_payment_mode,
                        "payment_amount" :payment_amount,
                        "payment_status":id_payment_status,
                        "payment_type":1
                    })
                    mode_serializer = PaymentModeDetailSerializer(data = mode_details)
                    mode_serializer.is_valid(raise_exception=True)
                    mode_serializer.save()
        except ValidationError as e:
            return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)  


    def update_cc_avenue_payment_mode(self,enc_resp,id_payment,payment_amount,working_key):
        try:
            cash_free_response = decrypt(enc_resp,working_key)
            print(cash_free_response)
            if len(cash_free_response['result']) > 0:
                for cash_free_data in cash_free_response['result']:
                    mode_details = {}
                    id_payment_mode = ''
                    id_payment_status = ''
                    
                    if not PaymentMode.objects.filter(mode_name = cash_free_data['payment_group']).exists():
                        gateway_payment_mode = {"mode_name": cash_free_data['payment_group'],"short_code":cash_free_data['payment_group'], "show_to_pay": False}
                        mode = PaymentMode.objects.create(**gateway_payment_mode)
                        serializer = PaymentModeSerializer(data=mode)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        id_payment_mode = serializer.data['id_mode']
                    else:
                        id_payment_mode = PaymentMode.objects.get(mode_name = cash_free_data['payment_group']).pk
                    
                    if not PaymentStatus.objects.filter(name = cash_free_data['payment_status']).exists():
                        gateway_payment_status = {"name": cash_free_data['payment_status'], "color": "#000000"}
                        status = PaymentStatus.objects.create(**gateway_payment_status)
                        serializer = PaymentStatusSerializer(data=status)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        id_payment_status = serializer.data['id']
                    else:
                        id_payment_status = PaymentStatus.objects.get(name = cash_free_data['payment_status']).pk
    
                    mode_details.update({
                        "id_pay" : id_payment,
                        "payment_mode" : id_payment_mode,
                        "payment_amount" :payment_amount,
                        "payment_status":id_payment_status,
                        "payment_type":1
                    })
                    mode_serializer = PaymentModeDetailSerializer(data = mode_details)
                    mode_serializer.is_valid(raise_exception=True)
                    mode_serializer.save()
        except ValidationError as e:
            return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)    
                
    
    def post(self, request, *args, **kwargs):
        try:
            if 'type' not in request.data:
                return Response({"message": "type missing"}, status=status.HTTP_400_BAD_REQUEST)
            if 'order_id' not in request.data or 'encResp' not in request.data:
                return Response({"message": "Order id is missing"}, status=status.HTTP_400_BAD_REQUEST)
           
            else:
                order_id = request.data['order_id']
                enc_resp = request.data['encResp']
                
                        
                queryset = Payment.objects.filter(order_id=order_id)
                payment_serializer = PaymentSerializer(queryset, many=True)
                if len(payment_serializer.data)==0:
                    return Response({"message": "No record found for given order id"}, status=status.HTTP_400_BAD_REQUEST)
                else: 
                    if request.data['type'] =='Success':
                        for data in payment_serializer.data:
                            if data['id_payGateway']:
                                payment_gateway = PaymentGateway.objects.get(id_pg=data['id_payGateway'])
                                payment_gateway_serializer = PaymentGatewaySerializer(payment_gateway)
                                if payment_gateway_serializer.data['pg_code']=='cashfree':
                                    self.update_cash_free_payment_mode(data['order_id'],data['id_payment'],data['payment_amount'])
                                if payment_gateway_serializer.data['pg_code']=='cc_avenue':
                                    self.update_cc_avenue_payment_mode(enc_resp,data['id_payment'],data['payment_amount'],payment_gateway_serializer['param_3'])
                                    
                                        
                            autogenerate = AutoGenerate()
                            if data['id_scheme_account']!=None and data['id_scheme_account']!='':
                                id_scheme_account = data['id_scheme_account']
                                scheme_account_query = SchemeAccount.objects.get(id_scheme_account = id_scheme_account)
                                scheme_account_serializer = SchemeAccountSerializer(scheme_account_query)
                                if scheme_account_serializer.data['scheme_acc_number']==None:
                                    autogenerate.generate_scheme_acc_no(id_scheme_account,data['id_scheme'], data['id_branch'])
                            else:
                                branch = Branch.objects.filter(is_ho = 1).first()
                                scheme_account_data = {
                                    "scheme_acc_number":None,
                                    "acc_scheme_id" : data['id_scheme'],
                                    "id_customer" : data['id_customer'],
                                    "id_branch" : branch.id_branch,
                                    "account_name" : data['account_name'],
                                    "start_date" : date.today(),
                                }
                                scheme_account_serializer = SchemeAccountSerializer(data=scheme_account_data)
                                scheme_account_serializer.is_valid(raise_exception=True)
                                scheme_account_serializer.save()
                                autogenerate.generate_scheme_acc_no(scheme_account_serializer.data['id_scheme_account'],data['id_scheme'], data['id_branch'])
                                Payment.objects.filter(id_payment = data['id_payment']).update(payment_status=1,id_scheme_account = scheme_account_serializer.data['id_scheme_account'])
                            
                            Payment.objects.filter(id_payment = data['id_payment']).update(payment_status=1)
                            autogenerate.generate_payment_receipt_no(data['id_payment'],data['id_scheme'], data['id_branch'])
                        return Response({"status":True,"message":"Payment Created successfully."},status=status.HTTP_201_CREATED)
                    if request.data['type'] =='Cancelled':
                        for data in payment_serializer.data:
                            Payment.objects.filter(id_payment = data['id_payment']).update(payment_status=4)
                        return Response({"status":True,"message":"Your payment was cancelled."},status=status.HTTP_201_CREATED)
                    if request.data['type'] =='Failure':
                        for data in payment_serializer.data:
                            Payment.objects.filter(id_payment = data['id_payment']).update(payment_status=5)
                        return Response({"status":True,"message":"Your payment was Failed."},status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)
class SchemePaymentDetailView(generics.GenericAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get(self, request, *args, **kwargs):
        payment             = self.get_object()
        payment_serializer  = PaymentSerializer(payment)
        output              = payment_serializer.data
        output.update({
                       "created_by"          : payment.created_by.username,
                       "updated_by"          : payment.updated_by.username if payment.updated_by != None else None,
                       "account_name"        : payment.id_scheme_account.account_name,
                       "scheme_name"         : payment.id_scheme_account.acc_scheme_id.scheme_name,
                       "account_number"      : payment.id_scheme_account.scheme_acc_number,
                       "customer_name"       : payment.id_scheme_account.id_customer.firstname,
                       "mobile"              : payment.id_scheme_account.id_customer.mobile,
                       "total_paid_weight"   : Payment.objects.filter(id_scheme_account=payment.id_scheme_account, payment_status=1).aggregate(total=Sum('metal_weight'))['total'],
                       "total_paid_amount"   : Payment.objects.filter(id_scheme_account=payment.id_scheme_account, payment_status=1).aggregate(total=Sum('payment_amount'))['total']
                       })
        pay_detail              = PaymentModeDetail.objects.filter(id_pay=payment.id_payment)
        pay_detail_serializer   = PaymentModeDetailSerializer(pay_detail, many=True)
        payment_mode_detail     = []
        for data in pay_detail_serializer.data:
            instance = {}
            pay_mode = PaymentMode.objects.get(id_mode=data['payment_mode'])
            instance.update({
                            "id_pay_mode_details"   :data['id_pay_mode_details'],
                            "payment_mode"          :pay_mode.mode_name,
                            "payment_amount"        :data['payment_amount']
                             })
            if instance not in payment_mode_detail:
                payment_mode_detail.append(instance)
        output.update({"payment_mode_detail":payment_mode_detail})
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        pay_det = request.data['payment_mode_details']
        del request.data['payment_mode_details']
        payment = self.get_object()
        payment_serializer = PaymentSerializer(payment, data = request.data)
        payment_serializer.is_valid(raise_exception=True)
        for each in pay_det:
            each.update({"id_pay":payment_serializer.data['id_payment']})
            if(PaymentModeDetail.objects.filter(id_pay_mode_details=each['id_pay_mode_details']).exists()):
                pay_detail = PaymentModeDetail.objects.filter(id_pay_mode_details=each['id_pay_mode_details']).get()
                pay_detail_serializer = PaymentModeDetailSerializer(pay_detail, data=each)
                pay_detail_serializer.is_valid(raise_exception=True)
                pay_detail_serializer.save()
            else:
                pay_detail_serializer = PaymentModeDetailSerializer(data=each)
                pay_detail_serializer.is_valid(raise_exception=True)
                pay_detail_serializer.save()
        payment_serializer.save()
        output = payment_serializer.data
        return Response(output, status=status.HTTP_202_ACCEPTED)

    
class GenerateReceiptView(generics.GenericAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get(self, request, *args, **kwargs):
        payment             = self.get_object()
        payment_serializer  = PaymentSerializer(payment)
        output              = payment_serializer.data
        output.update({
                       "created_by"          : payment.created_by.username,
                       "updated_by"          : payment.updated_by.username if payment.updated_by != None else None,
                       "account_name"        : payment.id_scheme_account.account_name,
                       "scheme_name"         : payment.id_scheme_account.acc_scheme_id.scheme_name,
                       "scheme_type"         : payment.id_scheme_account.acc_scheme_id.scheme_type,
                       "account_number"      : payment.id_scheme_account.scheme_acc_number,
                       "customer_name"       : payment.id_scheme_account.id_customer.firstname,
                       "mobile"              : payment.id_scheme_account.id_customer.mobile,
                       "bonus_metal_weight"  : payment.bonus_metal_weight,
                       "bonus_metal_amount"  : payment.bonus_metal_amount,
                       "total_paid_amount"   : Payment.objects.filter(id_scheme_account=payment.id_scheme_account, payment_status=1, date_payment__lte = payment.date_payment).aggregate(total=Sum('payment_amount'))['total']
                       })
        if(payment.id_scheme_account.acc_scheme_id.scheme_type != 0):
            output.update({
                'metal_rate':Decimal(payment.metal_rate)
            })
        if(payment.id_scheme_account.acc_scheme_id.scheme_type==2):
            total_weight = Payment.objects.filter(id_scheme_account=payment.id_scheme_account, payment_status=1, date_payment__lte = payment.date_payment).aggregate(total=Sum('metal_weight'))['total']
            total_amount = Payment.objects.filter(id_scheme_account=payment.id_scheme_account, payment_status=1, date_payment__lte = payment.date_payment).aggregate(total=Sum('payment_amount'))['total']
            total_bonus_metal_amount = Payment.objects.filter(id_scheme_account=payment.id_scheme_account, payment_status=1, date_payment__lte = payment.date_payment).aggregate(total=Sum('bonus_metal_amount'))['total']
            total_bonus_weight = Payment.objects.filter(id_scheme_account=payment.id_scheme_account, payment_status=1, date_payment__lte = payment.date_payment).aggregate(total=Sum('bonus_metal_weight'))['total']
            output.update({
                "total_bonus_metal_weight"   : total_bonus_weight,
                "total_bonus_metal_amount"   : total_bonus_metal_amount,
                "total_wallet_weight"   : Decimal(total_weight) + Decimal(total_bonus_weight),
                "total_wallet_amount"   : Decimal(total_amount) + Decimal(total_bonus_metal_amount),
                "total_receipt_weight"   : Decimal(payment.bonus_metal_weight) + Decimal(payment.metal_weight),
            })
        else:
            output.update({
                "total_paid_weight"   : Payment.objects.filter(id_scheme_account=payment.id_scheme_account, payment_status=1, date_payment__lte = payment.date_payment).aggregate(total=Sum('metal_weight'))['total'],
            })
        pay_detail              = PaymentModeDetail.objects.filter(id_pay=payment.id_payment)
        pay_detail_serializer   = PaymentModeDetailSerializer(pay_detail, many=True)
        payment_mode_detail     = []
        for data in pay_detail_serializer.data:
            instance = {}
            pay_mode = PaymentMode.objects.get(id_mode=data['payment_mode'])
            instance.update({
                            "id_pay_mode_details"   :data['id_pay_mode_details'],
                            "payment_mode"          :pay_mode.mode_name,
                            "payment_amount"        :data['payment_amount']
                             })
            if instance not in payment_mode_detail:
                payment_mode_detail.append(instance)
        output.update({"payment_mode_detail":payment_mode_detail})
        content = output
        template_path = 'receipt.html'
        rendered_content = render_to_string(template_path, {"content":content})
        # Define the path to save the PDF
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
        pdf_file_path = os.path.join(pdf_dir, f'invoice_{payment.id_payment}.pdf')

        # Create the directory if it doesn't exist
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)

        # Generate the PDF if it doesn't exist
        if not os.path.exists(pdf_file_path):
            with open(pdf_file_path, 'wb') as pdf_file:
                pisa.CreatePDF(rendered_content, dest=pdf_file)

        # Build the absolute URI for the PDF file
        pdf_url = request.build_absolute_uri(settings.MEDIA_URL + f'invoices/invoice_{payment.id_payment}.pdf')
        
        self.delete_file_after_delay(pdf_file_path, delay=5)
        response = Response({"pdf_url": pdf_url}, status=status.HTTP_202_ACCEPTED)

        # Optionally, delete the PDF after the response is sent (if you don't need to keep it)
        # Schedule deletion after 5 seconds
        
        
        return response

    def delete_file_after_delay(self,file_path, delay=5):
        def delete_file():
            time.sleep(delay)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"File deleted successfully: {file_path}")
                except Exception as e:
                    logging.error(f"Error deleting file {file_path}: {e}")
            else:
                logging.warning(f"File does not exist: {file_path}")

        # Run the deletion in a separate thread
        thread = Thread(target=delete_file)
        thread.start()

class ValidatePayment:

    def validate_payment(self, payment):
        total_received_amount = 0
        total_net_amount = 0
        payment_status = {"status":True}
        for data in payment:
            if data["id_scheme_account"]!='' and data["id_scheme_account"]!=None:
                scheme_account = SchemeAccount.objects.filter(id_scheme_account = data["id_scheme_account"]).get()
                scheme_id      = scheme_account.acc_scheme_id.pk
                data.update({"scheme_id" : scheme_id})
            scheme          = Scheme.objects.filter(scheme_id = data['scheme_id']).get()
            scheme_data = SchemeSerializer(scheme).data
            payment_settings    = SchemePaymentSettings()
            paid_installment = int(data["installment"])
            scheme_payment_data = payment_settings.scheme_payment_settings(scheme.scheme_id,paid_installment,data["metal_rate"],data["id_scheme_account"],scheme_data)
            min_amount = scheme_payment_data['minimum_payable_details']['min_amount']
            max_amount = scheme_payment_data['maximum_payable_details']['max_amount']
            total_net_amount = data['total_net_amount']
            if(float(data['payment_amount'])<float(min_amount)):
                payment_status = {"status":False,"message":"Payment Amount is Less than the Minimum Amount"}
            if((float(data['payment_amount'])>float(max_amount)) and (float(max_amount) > 0)):
                payment_status = {"status":False,"message":"Payment Amount greater than the Maximum Amount"}
            actual_net_amount = float(data['payment_amount'])-float(data['discountAmt'])+float(data['tax_amount'] if data['tax_type']==2 else 0)
            if(float(actual_net_amount)!=float(data['net_amount'])):
                payment_status = {"status":False,"message":"Net Amount is not matched"}
            if(float(data['net_amount'])>(float(data['payment_amount'])+float(data['tax_amount'] if data['tax_type']==2 else 0))):
                payment_status = {"status":False,"message":"Net Amount is Should not greater than the Payment Amount"}
            if data['paid_through']==1:
                received_amount = 0
                for payment_mode in data['payment_mode_details']:
                    received_amount +=float(payment_mode['payment_amount'])
                    total_received_amount +=float(payment_mode['payment_amount'])
                    payment_status.update({"order_amount":total_received_amount})
                if(float(received_amount)!=float(data['total_net_amount'])):
                    payment_status = {"status":False,"message":"Received Amount Does Not Match with Net Amount"}
            if data['paid_through']==2:
                total_received_amount+=float(data['net_amount'])
                payment_status.update({"order_amount":total_received_amount})
        return payment_status

def generate_order_details(id_customer,order_amount):
    # account_details = SchemeAccount.objects.get(id_scheme_account=id_scheme_account)
    # account_serializer = SchemeAccountSerializer(account_details,many=False)
    # id_customer = account_serializer.data['id_customer']
    customer = Customers.objects.get(id_customer=id_customer)
    now = datetime.now()
    order_id = f"{id_customer}_{now.strftime('%Y%m%d%H%M%S')}" 
    return {
        "order_id":order_id,
        "order_amount":order_amount,
        "order_currency":"INR",
        "customer_details":
        {
            "customer_id":str(id_customer),
            "customer_email":customer.email,
            "customer_phone":customer.mobile,
            "customer_name":customer.firstname
        }
    }

def generate_cc_avenue_order_details(id_customer,order_amount,merchant_id,working_key):
    # account_details = SchemeAccount.objects.get(id_scheme_account=id_scheme_account)
    # account_serializer = SchemeAccountSerializer(account_details,many=False)
    # id_customer = account_serializer.data['id_customer']
    customer = Customers.objects.get(id_customer=id_customer)
    now = datetime.now()
    order_id = f"{id_customer}_{now.strftime('%Y%m%d%H%M%S')}" 
    data = {
        "order_id":order_id,
        "merchant_id":merchant_id,
        "amount":order_amount,
        "currency":"INR",
        "language":"EN",
        "customer_id":str(id_customer),
        "billing_email":customer.email,
        "billing_tel":customer.mobile,
        "billing_name":customer.firstname
    }

    # Build the query string
    request_str = "&".join([f"{k}={v}" for k, v in data.items()])
    enc_request = encrypt(request_str, working_key)
    return {"order_id":order_id, "enc_request":enc_request}
    
    
def cancel_payment(data, request):
    # with transaction.atomic():
    #     for data in request.data['cancel_payments']:
    #         if(data['cancel'] == True):
    payment = Payment.objects.get(id_payment=data['id'])
    payment_status = PaymentStatus.objects.get(id=4)
    payment.cancelled_by = request.user
    payment.payment_status = payment_status
    payment.cancelled_date = date.today()
    payment.cancel_reason = data['cancel_reason']
    payment.save()
                
    
class CancelPaymentView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def post(self, request, *args, **kwargs):
        # print(request.data['cancel_payments'])
        user = User.objects.filter(id=request.user.pk).get()
        emp = Employee.objects.filter(user_id = request.user.pk).get()
        emp_profile = Profile.objects.get(id_profile=emp.id_profile.pk)
        if(emp_profile.isOTP_req_for_payment_cancel == True):
            OTP_code = randint(100000, 999999)
            expiry_time = timezone.now() + timedelta(minutes=5)
            if (EmployeeOTP.objects.filter(employee=emp.pk, otp_for="6", expiry__gt=timezone.now()).exists()):
                return Response({"message": "A payment cancel OTP already exists. Please use it / wait till its expire"}, status=status.HTTP_400_BAD_REQUEST)
            EmployeeOTP.objects.create(employee=emp, otp_for="6", email_id=user.email,
                                    otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
            return Response({"message": "Enter OTP sent to your mobile number to proceed further."})
        else:
            with transaction.atomic():
                for data in request.data['cancel_payments']:
                    if(data['cancel'] == True):
                        cancel_payment(data, request)
                        return Response({"message":"Payments cancelled successfully."},status=status.HTTP_202_ACCEPTED)
                    else:
                        return Response(status=status.HTTP_200_OK)
        
            
    
class AccountPaymentHistoryView(generics.GenericAPIView):
    renderer_classes = [CustomJSONRenderer]
    permission_classes = [IsEmployeeOrCustomer]
    queryset = SchemeAccount.objects.all()
    serializer_class = SchemeAccountSerializer
    
    
    def get(self, request, *args, **kwargs):
        instance = {}
        customer_obj = {}
        scheme_account = self.get_object()
        scheme_account_serializer = SchemeAccountSerializer(scheme_account)
        scheme_account_data = scheme_account_serializer.data
        
        scheme_account_data.update({"scheme_name":scheme_account.acc_scheme_id.scheme_name,
                                    # "scheme_type":scheme_account.acc_scheme_id.scheme_type,
                                    "closing_balance" : scheme_account.closing_balance if(scheme_account.closing_balance != None) else DecimalWithPrecision(Decimal("0.00"), 2),
                                    "closing_amount" : scheme_account.closing_amount if(scheme_account.closing_amount != None) else DecimalWithPrecision(Decimal("0.00"), 2),
                                    "closing_weight" : scheme_account.closing_weight if(scheme_account.closing_weight != None) else DecimalWithPrecision(Decimal("0.000"), 3),
                                    "target_weight" : scheme_account.target_weight if(scheme_account.target_weight != None) else DecimalWithPrecision(Decimal("0.000"), 3),
                                    'closing_date' : format_date(scheme_account.closing_date) if(scheme_account.closing_date != None) else '',
                                    # 'added_by' : scheme_account.added_by if(scheme_account.added_by != None) else '',
                                    'closed_employee' : scheme_account.closed_employee.pk if(scheme_account.closed_employee != None) else 0,
                                    'closing_id_branch' : scheme_account.closing_id_branch.pk if(scheme_account.closing_id_branch != None) else 0,
                                    'fin_year' : scheme_account.fin_year.pk if(scheme_account.fin_year != None) else 0,
                                    'close_reverted_by' : scheme_account.close_reverted_by if(scheme_account.close_reverted_by != None) else 0,
                                    'updated_on' : date_format_with_time(scheme_account.updated_on) if(scheme_account.updated_on != None) else '',
                                    "additional_benefits" : scheme_account.additional_benefits if(scheme_account.additional_benefits != None) else DecimalWithPrecision(Decimal("0.00"), 2),
                                    "closing_add_charges" : scheme_account.closing_add_charges if(scheme_account.closing_add_charges != None) else DecimalWithPrecision(Decimal("0.00"), 2),
                                    "closing_deductions" : scheme_account.closing_deductions if(scheme_account.closing_deductions != None) else DecimalWithPrecision(Decimal("0.00"), 2),
                                    "closing_benefits" : scheme_account.closing_benefits if(scheme_account.closing_benefits != None) else DecimalWithPrecision(Decimal("0.00"), 2),
                                    })
        if(scheme_account.utilized_type != None):
            if(scheme_account.utilized_type == 1):
                scheme_account_data.update({
                    'utilized_type' : 'Cash Refund',
                })
            elif(scheme_account.utilized_type == 2):
                scheme_account_data.update({
                    'utilized_type' : 'Against Purchase',
                })
        if(scheme_account.utilized_type == None):
            scheme_account_data.update({'utilized_type' : ''})
            
        if(scheme_account.acc_scheme_id.scheme_type==1):
            scheme_account_data.update({'scheme_type' : 'Amount Scheme'})
        if(scheme_account.acc_scheme_id.scheme_type==2):
            scheme_account_data.update({'scheme_type' : 'Weight Scheme'})
        if(scheme_account.acc_scheme_id.scheme_type==1):
            scheme_account_data.update({'scheme_type' : 'Digi Gold'})
            
        if(scheme_account.added_by==0):
            scheme_account_data.update({'added_by' : 'Admin App'})
        elif(scheme_account.added_by==1):
            scheme_account_data.update({'added_by' : 'Mobile App'})
        elif(scheme_account.added_by==2):
            scheme_account_data.update({'added_by' : 'Web App'})
        elif(scheme_account.added_by==3):
            scheme_account_data.update({'added_by' : 'Collection App'})
        elif(scheme_account.added_by==None):
            scheme_account_data.update({'added_by' : ''})
            
        customer = Customers.objects.get(id_customer=scheme_account.id_customer.id_customer)
        customer_serializer = CustomerSerializer(customer, context={'request':request})
        customer_obj = customer_serializer.data
        customer_obj.update({"date_of_birth":format_date(customer.date_of_birth)})
        if(CustomerAddress.objects.filter(customer=customer.id_customer).exists()):
            customer_address = CustomerAddress.objects.get(customer=customer.id_customer)
            address1 = customer_address.line1 if customer_address.line1 != None else ""
            address2 = customer_address.line2 if customer_address.line2 != None else ""
            address3 = customer_address.line3 if customer_address.line3 != None else ""
            address = f"{address1} {address2} {address3}".strip()
            customer_obj.update({"address":address})
            customer_obj.update({"address1":address1,
                                 "address2":address2,
                                 "address3":address3})
        else:
            customer_obj.update({"address":""})
        show_full_number = False
        user = User.objects.get(id=request.user.pk)
        if(user.is_adminuser):
            employee = Employee.objects.filter(user = request.user.pk).get()
            show_full_number = EmployeeSettings.objects.get(id_employee=employee.pk).is_show_full_mobile
        if(user.is_customer):
            show_full_number = True
        if customer.mobile != None and len(customer.mobile)>15:
            try:
                decrypted_mobile = fernet.decrypt(str(customer.mobile).encode()).decode()
                if show_full_number:
                    # Show full mobile number
                    customer_obj.update({"mobile":customer.mob_code+"-"+decrypted_mobile,
                         "mobile_woc":decrypted_mobile})
                else:
                    # Mask the mobile number (e.g., show first 2 and last 2 digits)
                    masked_mobile = decrypted_mobile[:2] + "X" * (len(decrypted_mobile) - 4) + decrypted_mobile[-2:]
                    customer_obj.update({"mobile":customer.mob_code+"-"+masked_mobile,
                         "mobile_woc":masked_mobile})
            except Exception as e:
                print("Decryption failed:", str(e))
        else:
            customer_obj.update({"mobile":customer.mob_code+"-"+customer.mobile,
                         "mobile_woc":customer.mobile})
        payments = []
        total_metal_weight = 0
        total_net_amount = 0
        total_bonus_weight = 0
        total_bonus_amount = 0
        payment = Payment.objects.filter(id_scheme_account=scheme_account.id_scheme_account, payment_status=1)
        payment_serializer = PaymentSerializer(payment, many=True)
        for data in payment_serializer.data:
            # Sum up total metal_weight and total net_amount
            total_metal_weight += Decimal(data['metal_weight'])
            total_bonus_weight += Decimal(data['bonus_metal_weight'])
            total_bonus_amount += Decimal(data['bonus_metal_amount'])
            total_net_amount += Decimal(data['net_amount'])
            pay_status      = PaymentStatus.objects.filter(id=data['payment_status']).get()
            
            if (data['paid_through'] == 1):
                data.update({"paid_through":"Admin App"})
            elif (data['paid_through'] == 2):
                data.update({"paid_through":"Mobile App"})
            else:
                data.update({"paid_through":"Collection App"})
                
            accumulate_weight = Decimal(data['metal_weight']) + Decimal(data['bonus_metal_weight'])  
            data.update({"cancel":False,
                         "bonus":data['discountAmt'],
                         "accumulate_weight":accumulate_weight,
                         "entry_date":format_date(data['entry_date']),
                         "payment_status"    :pay_status.name,
                         "status_color"      :pay_status.color,
                         "trans_id" : data['trans_id'] if(data['trans_id'] is not None) else '',
                         "ref_trans_id" : data['ref_trans_id'] if(data['ref_trans_id'] is not None) else '',
                         "order_id" : data['order_id'] if(data['order_id'] is not None) else '',
                         "cancel_reason" : data['cancel_reason'] if(data['cancel_reason'] is not None) else '',
                         "payment_session_id" : data['payment_session_id'] if(data['payment_session_id'] is not None) else '',
                         "approval_date" : format_date(data['approval_date']) if(data['approval_date'] is not None) else '',
                         "updated_on" : date_format_with_time(data['updated_on']) if(data['updated_on'] is not None) else '',
                         "cancelled_date" : format_date(data['cancelled_date']) if(data['cancelled_date'] is not None) else '',
                         "id_payGateway" : data['id_payGateway'] if(data['id_payGateway'] is not None) else 0,
                         "tax_id" : data['tax_id'] if(data['tax_id'] is not None) else 0,
                         "updated_by" : data['updated_by'] if(data['updated_by'] is not None) else 0,
                         "cancelled_by" : data['cancelled_by'] if(data['cancelled_by'] is not None) else 0,
                         })
            if data not in payments:
                payments.append(data)
        if(scheme_account.acc_scheme_id.scheme_type == 2):
            sch_acc_obj = SchemeAccount.objects.get(id_scheme_account=scheme_account.id_scheme_account)
            today = date.today()
            days_elapsed = (today - sch_acc_obj.start_date).days
            interest_setting = SchemeDigiGoldInterestSettings.objects.filter(
                scheme=sch_acc_obj.acc_scheme_id.pk,
                from_day__lte=days_elapsed,
                to_day__gte=days_elapsed
            ).first()
            interest_percentage = 0
            if interest_setting:
                interest_percentage = interest_setting.interest_percentage
                
            maturity_days = scheme_account.acc_scheme_id.digi_maturity_days
            maturity_date = ""
            if scheme_account.start_date and maturity_days:
                maturity_date = scheme_account.start_date + timedelta(days=maturity_days)
            scheme_account_data.update({
                'curr_period_and_interest': f"{interest_setting.from_day}-{interest_setting.to_day}({interest_setting.interest_percentage}%)" if interest_setting else "",
                'maturity_date' : format_date(maturity_date)
            })
        total_metal_weight += Decimal(scheme_account.opening_balance_weight)
        total_net_amount += Decimal(scheme_account.opening_balance_amount)
        scheme_account_data.update({
        # "total_metal_weight": round(total_metal_weight, 3),
        # "total_net_amount": round(total_net_amount, 2),
        "total_metal_weight": DecimalWithPrecision(Decimal(total_metal_weight), 3),
        "total_bonus_amount": DecimalWithPrecision(Decimal(total_bonus_amount), 2),
        "total_bonus_weight": DecimalWithPrecision(Decimal(total_bonus_weight), 3),
        "total_accumulate_weight": DecimalWithPrecision(Decimal(total_bonus_weight + total_metal_weight), 3),
        "total_net_amount": DecimalWithPrecision(Decimal(total_net_amount), 2),
        })
        instance.update({"scheme_account":scheme_account_data, "customer":customer_obj,
                         "payments":payments})
        return Response(instance, status=status.HTTP_200_OK)


class PaymentHistoryView (generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]

    def post(self, request, *args, **kwargs):
            
            queryset = PaymentModeDetail.objects.all()
            if 'id_customer' in request.data and request.data["id_customer"]!='':
                id_customer = request.data["id_customer"]
                queryset = PaymentModeDetail.objects.filter(id_pay__id_scheme_account__id_customer= id_customer)
            if 'id_scheme_account' in request.data and request.data["id_scheme_account"]!='':
                id_scheme_account = request.data["id_scheme_account"]
                queryset = PaymentModeDetail.objects.filter(id_pay__id_scheme_account= id_scheme_account)
            payment_details = queryset.select_related(
                'id_pay__id_scheme_account',
                 'payment_mode',
            ).values(
                'id_pay',  # Foreign key field on PaymentModeDetail
                'id_pay__id_scheme_account',
                'id_pay__id_scheme_account__id_customer',
                'id_pay__date_payment',
                'id_pay__payment_amount',
                'id_pay__receipt_no',
                'id_pay__id_scheme_account__scheme_acc_number',
                'payment_mode__mode_name',
                'id_pay__metal_rate',
                'id_pay__metal_weight',
                'id_pay__id_scheme_account__acc_scheme_id__scheme_name',
                'id_pay__payment_status__name',
                'id_pay__payment_status__color',
            )
            if payment_details:
                response_data = []
                for detail in payment_details:
                    response_data.append({
                        'payment_id': detail['id_pay'],
                        'id_scheme_account': detail['id_pay__id_scheme_account'],
                        'customer_id': detail['id_pay__id_scheme_account__id_customer'],
                        'payment_date': format_date(detail['id_pay__date_payment']),
                        'receipt_no': (detail['id_pay__receipt_no']),
                        'amount': format_currency_with_symbol(detail['id_pay__payment_amount']),
                        'account_number': detail['id_pay__id_scheme_account__scheme_acc_number'],
                        'payment_mode': detail['payment_mode__mode_name'],
                        'metal_rate': format_currency_with_symbol(detail['id_pay__metal_rate']),
                        'metal_weight': format_number_with_decimal(detail['id_pay__metal_weight'],3),
                        'scheme_name': detail['id_pay__id_scheme_account__acc_scheme_id__scheme_name'],
                        'status_name': detail['id_pay__payment_status__name'],  # Renaming status fields
                        'status_color': detail['id_pay__payment_status__color'],
                    })
                return Response({"message":"Data retrieved successfully.","response_data":response_data}, status=status.HTTP_200_OK)
            else:
                return Response({"message":"No Record found."}, status=status.HTTP_200_OK)