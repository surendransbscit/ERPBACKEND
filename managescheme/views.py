from django.shortcuts import render
from django.http import HttpResponse, request, Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from datetime import datetime, timedelta, date
from django.db import transaction
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError
from random import randint
from django.utils import timezone
import os
from datetime import datetime, timedelta, date, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


#Import models
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee,isSuperuser,IsEmployeeOrCustomer
from .models import (SchemeAccount)
from core.models import (EmployeeOTP)
from retailmasters.models import (Profile)
from accounts.models import (User)
from customers.models import (Customers)
from employees.models import (Employee, EmployeeSettings)
from schemepayment.models import (Payment)
from schememaster.models import (PaymentSettings,Scheme,Denomination,SchemeWeight, SchemeDigiGoldInterestSettings)
from retailmasters.models import (MetalRates, Branch,metalRatePurityMaster, PaymentMode, Taxmaster)
from retailcataloguemasters.models import (Purity,Metal)
from crmsettings.models import (ChitSettings)
from retailmasters.views import BranchEntryDate

#Import Serializers
from .serializers import (SchemeAccountSerializer)
from schememaster.serializers import (SchemeSerializer,PaymentSettingsSerializer,SchemeAmountDenomSerializer,SchemeWeightDenomSerializer,
                                      SchemeDigiGoldInterestSettingsSerializer)
from customers.serializers import (CustomerSerializer)
from retailmasters.serializers import (MetalRatePurityMasterSerializer)
from retailcataloguemasters.serializers import (PuritySerializer)
from crmsettings.serializers import (ChitSettingsSerializer)
from schemepayment.serializers import (PaymentSerializer)
from schemepayment.models import (PaymentModeDetail)
from schemepayment.serializers import (PaymentModeDetailSerializer)

#Import constants
from .constants import (SCHEME_ACCOUNT_COLUMN_LIST, SCHEME_CLOSED_ACCOUNT_COLUMN_LIST,
                        ACTION_LIST)
from utilities.utils import format_date,date_format_with_time  # Adjust import path
from utilities.pagination_mixin import PaginationMixin
from utilities.constants import FILTERS
pagination = PaginationMixin()  # Apply pagination

from cryptography.fernet import Fernet
from retailsettings.models import (RetailSettings)
fernet = Fernet(os.getenv('crypt_key'))

class RateMasterClass :

    def get_metal_rates(self,id_purity,id_metal):
        metal_rate = 0
        if(metalRatePurityMaster.objects.filter(id_metal=id_metal,id_purity=id_purity).exists()):
            queryset = metalRatePurityMaster.objects.get(id_metal=id_metal,id_purity=id_purity)
            serializer = MetalRatePurityMasterSerializer(queryset)
            if (serializer.data['id_purity']==id_purity and serializer.data['id_metal'] == id_metal):
                try: 
                    metal_rate = MetalRates.objects.latest('rate_id')
                    field_name = MetalRates._meta.get_field(queryset.rate_field)
                    rate_value = field_name.value_from_object(metal_rate)
                    metal_rate = rate_value
                except MetalRates.DoesNotExist:
                    metal_rate = 0
        return metal_rate

class SchemeAccountDrop(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    queryset = SchemeAccount.objects.all()
    serializer_class = SchemeAccountSerializer
    
    def post(self, request, *args, **kwargs):
        if 'customer' in request.data:
            if(SchemeAccount.objects.filter(id_customer = request.data['customer']).exists()):
                queryset        = SchemeAccount.objects.filter(id_customer = request.data['customer'])
                serializer      = SchemeAccountSerializer(queryset, many=True)
                
                result_data     = []
                for data in serializer.data:
                    scheme_acc_obj = SchemeAccount.objects.filter(id_scheme_account=data['id_scheme_account']).first()
                    acc_details         = {}
                    customer            = Customers.objects.get(id_customer=data['id_customer'])
                    branch              = Branch.objects.get(id_branch=data['id_branch'])
                    scheme              = Scheme.objects.filter(scheme_id=data['acc_scheme_id']).get()
                    sch_serializer      = SchemeSerializer(scheme)
                    rate_master         = RateMasterClass()  ## getting metal rate Based on purity and metal
                    metal_rate          = rate_master.get_metal_rates(sch_serializer.data['sch_id_purity'],sch_serializer.data['sch_id_metal'])
                    scheme_paid_class   = SchemeAccountPaidDetails()
                    paid_details        = scheme_paid_class.get_scheme_account_paid_details(data['id_scheme_account'])
                    paid_installment    = paid_details['tot_paid_installment']
                    payment_settings    = SchemePaymentSettings()
                    scheme_payment_data = payment_settings.scheme_payment_settings(data['acc_scheme_id'],paid_installment,metal_rate,data['id_scheme_account'],sch_serializer.data)
                    scheme_amount_denom = []
                    scheme_weight_denom = []
                    if Denomination.objects.filter(id_scheme=data['acc_scheme_id']).exists():
                        scheme_amount_queryset = Denomination.objects.filter(id_scheme=data['acc_scheme_id'])
                        scheme_amount_serializer = SchemeAmountDenomSerializer(scheme_amount_queryset, many=True)
                        scheme_amount_denom = scheme_amount_serializer.data
                        # print(scheme_amount_denom)
                    if SchemeWeight.objects.filter(id_scheme = data['acc_scheme_id']).exists():
                        scheme_weight_queryset = SchemeWeight.objects.filter(id_scheme = data['acc_scheme_id'])
                        scheme_weight_serializer = SchemeWeightDenomSerializer(scheme_weight_queryset,many=True)
                        scheme_weight_denom = scheme_weight_serializer.data
                    if(scheme.tax_id != None):
                        acc_details.update({"tax_percentage":Taxmaster.objects.get(tax_id=scheme.tax_id.pk).tax_percentage})
                    
                    total_installments = int(scheme.total_instalment if scheme.total_instalment!=None else 0)
                    acc_details.update({
                    'id_scheme'          :data['acc_scheme_id'],
                    'id_scheme_account'  :data['id_scheme_account'],
                    'account_name'       :data['account_name'],
                    'id_branch'          :data['id_branch'],
                    'start_date'         :format_date(data['start_date']),
                    'scheme_acc_number'  :data['scheme_acc_number'] if (data['scheme_acc_number'] != None) else "",
                    'branch_name'        :branch.name,
                    'scheme_name'        :scheme.scheme_name,
                    'convert_to_weight'  :scheme.convert_to_weight,
                    'scheme_code'        :scheme.scheme_code,
                    'tax_type'           :scheme.tax_type,
                    'tax_id'             :scheme.tax_id.pk if scheme.tax_id != None else None, 
                    'customer_name'      :customer.firstname,
                    'mobile'             :customer.mobile,
                    'paid_installments'  :int(paid_installment) + int(scheme_acc_obj.total_paid_ins),
                    'allow_advance'      :scheme.allow_advance if scheme.allow_advance !=None else 0,
                    'advance_months'     :int(scheme.number_of_advance if scheme.number_of_advance!=None else 0),
                    'total_installments' :total_installments,
                    'paid_amount'        :(Decimal(paid_details['total_paid_amount']) + Decimal(scheme_acc_obj.opening_balance_amount)),
                    'paid_weight'        :(Decimal(paid_details['total_paid_weight']) + Decimal(scheme_acc_obj.opening_balance_weight)),
                    'last_paid_date'     :paid_details['last_paid_date'],
                    'todays_rate'        :float(metal_rate),
                    'limit_type'         :int(scheme_payment_data['limit_type']),
                    'payment_chance_type':scheme_payment_data['payment_chance_type'],
                    'payment_chance_value':scheme_payment_data['payment_chance_value'],
                    'discount_type'      :int(scheme_payment_data['discount_type']),
                    'discount_value'     :int(scheme_payment_data['discount_value']),
                    'denom_type'         :int(scheme_payment_data['denom_type']),
                    'denom_value'        :int(scheme_payment_data['denom_value']),
                    'minimum_payable'    :scheme_payment_data['minimum_payable_details'],
                    'maximum_payable'    :scheme_payment_data['maximum_payable_details'],
                    'allow_pay'          :scheme_payment_data['allow_pay'],
                    'amount_denom'       :scheme_amount_denom,
                    'weight_denom'       :scheme_weight_denom,
                    "for_search"         :data['account_name'] + " " + (data['scheme_acc_number'] if (data['scheme_acc_number'] != None) else ""),
                    'scheme_type'        :scheme.scheme_type,
                    'unpaid_dues'        : total_installments - int(paid_installment),
                    'digi_scheme'        : True if(scheme.scheme_type==2) else False
                        })
                    if(paid_installment > 0 ):
                        acc_details.update({
                            'last_paid_date': format_date(paid_details['last_paid_date']),
                            'last_paid_amount': paid_details['last_paid_amount'],
                        })
                    if(scheme.scheme_type==2):
                        maturity_days = scheme.digi_maturity_days
                        maturity_date = ""
                        if scheme_acc_obj.start_date and maturity_days:
                            maturity_date = scheme_acc_obj.start_date + timedelta(days=maturity_days)
                        joined_date = scheme_acc_obj.start_date
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
                        acc_details.update({
                            'payment_chance_type':1,
                            'maturity_date': format_date(maturity_date),
                            'digi_interest_percent':interest_percentage,
                            'payment_chance_value':scheme.digi_payment_chances,
                            'minimum_payable':{"min_weight":0.00,"min_amount":float(scheme.digi_min_amount)},
                            'maximum_payable':{"min_weight":0.00,"min_amount":float(scheme.digi_min_amount)}
                        })
                    if(acc_details not in result_data):
                        result_data.append(acc_details)
                if(len(serializer.data) != 0):
                    return Response({"message":"Account Fetched Successfully","data":result_data},status=status.HTTP_200_OK)
            else:
                return Response({"message":"No Scheme account for this customer."},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message":"Customer Id Required"},status=status.HTTP_400_BAD_REQUEST)
        
    
    def get(self, request, *args, **kwargs):
        if 'id' in request.query_params:
            queryset = SchemeAccount.objects.filter(id_scheme_account=request.query_params['id']).get()
            
            purity = str(queryset.acc_scheme_id.sch_id_purity.purity).split('.')[0]
            metal = str(queryset.acc_scheme_id.sch_id_metal.metal_name).lower()
            fld_name = ""
            for l in MetalRates._meta.get_fields():
                if(metal in l.name and purity in l.name): 
                        fld_name=l.name
            obj = MetalRates.objects.latest('rate_id')
            field_object = MetalRates._meta.get_field(fld_name)
            field_value = field_object.value_from_object(obj)
            # print(field_value)
            output = {}
            output.update({
                "start_date":queryset.start_date,
                "account_name":queryset.account_name,
                "scheme_code":queryset.acc_scheme_id.scheme_code,
                "scheme_name":queryset.acc_scheme_id.scheme_name,
                "payable":queryset.avg_payable,
                "amount":queryset.firstPayment_amt,
                "rate_name":fld_name,
                "today_rate":field_value
            })
            return Response(output, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_200_OK)

class SchemeAccountPaidDetails :

    def get_scheme_account_paid_details(self,id_scheme_account):
        return_data = {}
        tot_paid_installment = 0
        total_paid_amount = 0.00
        total_paid_weight = 0.000
        last_paid_date = ''
        last_paid_amount = 0
        if (Payment.objects.filter(id_scheme_account=id_scheme_account,payment_status=1).exists()):
            last_paid_details           = Payment.objects.filter(id_scheme_account=id_scheme_account,payment_status=1).latest('id_payment') 
            tot_paid_installment        = last_paid_details.installment
            last_paid_date              = last_paid_details.date_payment
            last_paid_amount              = last_paid_details.payment_amount
            total_paid_amount           = Payment.objects.filter(id_scheme_account=id_scheme_account, payment_status=1).aggregate(total=Sum('payment_amount'))['total']
            total_paid_weight           = Payment.objects.filter(id_scheme_account=id_scheme_account, payment_status=1).aggregate(total=Sum('metal_weight'))['total']
        return_data.update({
            'tot_paid_installment':tot_paid_installment,
            'last_paid_date':last_paid_date,
            'last_paid_amount':last_paid_amount,
            'total_paid_amount':round(total_paid_amount,2),
            'total_paid_weight':float(total_paid_weight)
        })  
        return return_data        


class SchemeAccountView(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    
    def get(self, request, *args, **kwargs):
        customer_id = request.query_params['customer']
        scheme_id = request.query_params['scheme']
        # print(customer_id)
        branch_ids_list = list(map(int, request.query_params['branch'].split(',')))
        queryset = SchemeAccount.objects.filter(is_closed=0).order_by('-id_scheme_account')
        if(customer_id != 'undefined' and customer_id != 'null'):
            queryset = queryset.filter(id_customer=customer_id)
        else:
            queryset = queryset.filter(id_branch__in=branch_ids_list, start_date__lte=request.query_params['to'],
                                          start_date__gte=request.query_params['from']).order_by('-id_scheme_account')
            if(scheme_id != 'undefined' and scheme_id != 'null' and scheme_id != ''):
                queryset = queryset.filter(acc_scheme_id=scheme_id)

        paginator, page = pagination.paginate_queryset(queryset, request,None,SCHEME_ACCOUNT_COLUMN_LIST)
        serializer = SchemeAccountSerializer(page, many=True,context={'request': request})
        result_data = []
        for data in serializer.data:
            accDetails = {}
            customer = Customers.objects.get(id_customer=data['id_customer'])
            branch = Branch.objects.get(id_branch=data['id_branch'])
            scheme = Scheme.objects.get(scheme_id=data['acc_scheme_id'])
            scheme_payment_details   = SchemeAccountPaidDetails()
            payment_details        = scheme_payment_details.get_scheme_account_paid_details(data['id_scheme_account'])
            accDetails.update({
            'pk_id'             :data['id_scheme_account'],
            'id_scheme_account'  :data['id_scheme_account'],
            'account_name'       :data['account_name'],
            'start_date'         :data['start_date'],
            'scheme_acc_number'  :data['scheme_acc_number'] if (data['scheme_acc_number'] != None) else None,
            'branch_name'        :branch.name,
            'scheme_name'        :scheme.scheme_name,
            'customer_name'      :customer.firstname,
            # 'mobile'             :customer.mobile,
            # 'paid_installments'  :payment_details['tot_paid_installment'],
            'paid_installments'  :data['total_paid_ins'],
            'total_paid_amount'  :Decimal(payment_details['total_paid_amount']) + Decimal(data['opening_balance_amount']),
            'total_paid_weight'  :Decimal(payment_details['total_paid_weight']) + Decimal(data['opening_balance_weight']),
            })
            # if(data['is_closed']==True):
            #     accDetails.update({'is_revertable':True})
            employee = Employee.objects.filter(user = request.user.pk).get()
            show_full_number = EmployeeSettings.objects.get(id_employee=employee.pk).is_show_full_mobile
            if customer.mobile != None and len(customer.mobile)>15:
                try:
                    decrypted_mobile = fernet.decrypt(str(customer.mobile).encode()).decode()

                    if show_full_number:
                        # Show full mobile number
                        accDetails.update({"mobile":customer.mob_code+"-"+decrypted_mobile,
                             "mobile_woc":decrypted_mobile})
                    else:
                        # Mask the mobile number (e.g., show first 2 and last 2 digits)
                        masked_mobile = decrypted_mobile[:2] + "X" * (len(decrypted_mobile) - 4) + decrypted_mobile[-2:]
                        accDetails.update({"mobile":customer.mob_code+"-"+masked_mobile,
                             "mobile_woc":masked_mobile})
                except Exception as e:
                    print("Decryption failed:", str(e))
            else:
                accDetails.update({"mobile":customer.mob_code+"-"+customer.mobile,
                             "mobile_woc":customer.mobile})
            if(accDetails not in result_data):
                result_data.append(accDetails)
        filters_copy = FILTERS.copy()        
        filters_copy['isBranchFilterReq']=True
        filters_copy['isDateFilterReq']=True
        filters_copy['isSchemeFilterReq']=True
        filters_copy['isCustomerFilterReq']=True
        SCHEME_ACCOUNT_ACTION_LIST = ACTION_LIST.copy()
        context={
            'columns':SCHEME_ACCOUNT_COLUMN_LIST,
            'actions':SCHEME_ACCOUNT_ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'filters':filters_copy,
            'is_filter_req':True
        }
        # print(result_data)
        return pagination.paginated_response(result_data,context) 
            
        
    def post(self, request, *args, **kwargs):
        serializer = SchemeAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch_date = BranchEntryDate()
        entry_date = branch_date.get_entry_date(request.data['id_branch'])
        if serializer.save():
            scheme = Scheme.objects.get(scheme_id=request.data['acc_scheme_id'])
            if scheme.has_free_installment and (scheme.free_installment) == 1:
                free_installment_data = {
                    "id_scheme_account": serializer.data["id_scheme_account"],
                    "id_scheme": scheme.scheme_id,
                    "date_payment": date.today(),
                    "installment": 1,
                    "id_branch": request.data['id_branch'],
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
                SchemeAccount.objects.filter(id_scheme_account = serializer.data["id_scheme_account"]).update(total_paid_ins=1)
            return Response({"message":scheme.scheme_name+" "+"Activated Successfully","data":serializer.data}, status=status.HTTP_201_CREATED)
    
class SchemeAccountDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    queryset = SchemeAccount.objects.all()
    serializer_class = SchemeAccountSerializer
    
    def get(self, request, *args, **kwargs):
        sch_account = self.get_object()
        sch_seri = SchemeAccountSerializer(sch_account)
        scheme_obj = Scheme.objects.filter(scheme_id=sch_account.acc_scheme_id.pk).first()
        output = sch_seri.data
        
        total_paid_amount    = 0
        total_paid_weight    = 0
        paid_installment     = 0
                    
        if (Payment.objects.filter(id_scheme_account=sch_account.id_scheme_account,payment_status=1).exists()):
            last_paid_details           = Payment.objects.filter(id_scheme_account=sch_account.id_scheme_account,payment_status=1).latest('id_payment') 
            paid_installment            = last_paid_details.installment
            last_paid_date              = last_paid_details.date_payment
            total_paid_amount           = Payment.objects.filter(id_scheme_account=sch_account.id_scheme_account, payment_status=1).aggregate(total=Sum('payment_amount'))['total']
            total_paid_weight           = Payment.objects.filter(id_scheme_account=sch_account.id_scheme_account, payment_status=1).aggregate(total=Sum('metal_weight'))['total']
        
        output.update({"total_paid_amount":Decimal(total_paid_amount) + Decimal(sch_account.opening_balance_amount), "total_paid_weight":Decimal(total_paid_weight) + Decimal(sch_account.opening_balance_weight),
                       "paid_installment":sch_account.total_paid_ins, 'scheme_type':scheme_obj.scheme_type})
        instance = {}
        customer = Customers.objects.filter(id_customer=sch_account.id_customer.pk).get()
        cus_seri = CustomerSerializer(customer, context={"request":request})
        instance.update(cus_seri.data)
        for_srch = []
        for_srch.append(customer.firstname + " " +customer.mobile)
        instance.update({"for_search":for_srch})
        # output.update({"acc_scheme_name":sch_account.acc_scheme_id.scheme_name,
        #                "branch":sch_account.id_branch.name,
        #                "customer":sch_account.id_customer.firstname})
        output.update({"id_customer":instance})
        if(scheme_obj.scheme_type==2):
            maturity_days = scheme_obj.digi_maturity_days
            maturity_date = ""
            if sch_account.start_date and maturity_days:
                maturity_date = sch_account.start_date + timedelta(days=maturity_days)
            output.update({"maturity_date":format_date(maturity_date)})
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        sch_account = self.get_object()
        sch_seri = SchemeAccountSerializer(sch_account, data=request.data)
        sch_seri.is_valid(raise_exception = True)
        sch_seri.save()
        return Response(sch_seri.data,status = status.HTTP_200_OK)
    
    
    def delete(self, request, *args, **kwargs):
        sch_account = self.get_object()
        try:
            sch_account.delete()
        except ProtectedError:
            return Response({"error_detail": ["Scheme Account can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SchemeAccountClosedList(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    queryset = SchemeAccount.objects.all()
    serializer_class = SchemeAccountSerializer
    
    def get(self, request, *args, **kwargs):
        if "id_customer" in request.query_params:
            queryset = SchemeAccount.objects.filter(is_closed=True,id_customer=request.query_params["id_customer"]).order_by('-id_scheme_account')
            serializer = SchemeAccountSerializer(queryset, many=True)

        else :
            branch_ids_list = list(map(int, request.query_params['branch'].split(',')))
            queryset = SchemeAccount.objects.filter(is_closed=True, id_branch__in=branch_ids_list, closing_date__lte=request.query_params['to'],
                                            closing_date__gte=request.query_params['from']).order_by('-id_scheme_account')
            paginator, page = pagination.paginate_queryset(queryset, request,None,SCHEME_CLOSED_ACCOUNT_COLUMN_LIST)
            serializer = SchemeAccountSerializer(page, many=True,context={'request': request})
        result_data = []
        for data in serializer.data:
            accDetails = {}
            closed_by = Employee.objects.filter(id_employee=data['closed_employee']).first()
            customer = Customers.objects.get(id_customer=data['id_customer'])
            branch = Branch.objects.get(id_branch=data['id_branch'])
            scheme = Scheme.objects.get(scheme_id=data['acc_scheme_id'])
            accDetails.update({
            'pk_id'             :data['id_scheme_account'],
            'id_scheme_account'  :data['id_scheme_account'],
            'account_name'       :data['account_name'],
            'start_date'         :data['start_date'],
            'closing_date'         :data['closing_date'],
            'closing_balance'    :data['closing_balance'],
            'closing_amount'     :data['closing_amount'],
            'closing_weight'     :data['closing_weight'] if data['closing_weight'] != None else 0,
            'additional_benefits':data['additional_benefits'],
            'scheme_acc_number'  :data['scheme_acc_number'] if (data['scheme_acc_number'] != None) else None,
            'branch_name'        :branch.name,
            'scheme_name'        :scheme.scheme_name,
            'customer_name'      :customer.firstname,
            'closed_by'      :closed_by.firstname,
            'is_revertable':True
            # 'mobile'             :customer.mobile
            })

            accDetails.update({"mobile":customer.mob_code+"-"+customer.mobile,
                             "mobile_woc":customer.mobile})
            maturity_days = scheme.digi_maturity_days
            total_weight = 0
            if (scheme.scheme_type == 2):
                payment_query = Payment.objects.filter(id_scheme_account=data['id_scheme_account'])
                payment_serializer = PaymentSerializer(payment_query, many=True)
                for payment_data in payment_serializer.data:
                    total_weight += Decimal(data['bonus_metal_weight'])
            accDetails.update({"bonus_weight":total_weight})
            if(accDetails not in result_data):
                result_data.append(accDetails)
        if "id_customer" in request.query_params:
            return Response({"data":result_data,"status":True,"message":"No record Found" if len(result_data)==0 else "Accounts Retrieved successfully"} ,status.HTTP_200_OK)
        else:
            filters_copy = FILTERS.copy()        
            filters_copy['isBranchFilterReq']=True
            # filters_copy['isDateFilterReq']=True
            # filters_copy['isSchemeFilterReq']=True
            # filters_copy['isCustomerFilterReq']=True
            SCHEME_CLOSED_ACCOUNT_ACTION_LIST = {"is_add_req":False,"is_edit_req":False,"is_delete_req":False,
                                                 "is_print_req":False,"is_cancel_req":False, 'is_revert_close_req':True, "is_total_req":True}
            context={
                'columns':SCHEME_CLOSED_ACCOUNT_COLUMN_LIST,
                'actions':SCHEME_CLOSED_ACCOUNT_ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'filters':filters_copy,
                'is_filter_req':True
                }
            return pagination.paginated_response(result_data,context) 

class SchemeAccountClosingView(generics.UpdateAPIView):
    permission_classes = [IsEmployee]
    queryset = SchemeAccount.objects.all()
    serializer_class = SchemeAccountSerializer
    
    def put(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.user.pk).get()
        emp = Employee.objects.filter(user_id = request.user.pk).get()
        emp_profile = Profile.objects.filter(id_profile=emp.id_profile.pk).get()
        
        sch_account = self.get_object()
        scheme = Scheme.objects.filter(scheme_id = sch_account.acc_scheme_id.scheme_id).first()
        # emp = Employee.objects.filter(user=request.user).get()
        branch = Branch.objects.filter(id_branch=request.data['closing_id_branch']).get()
        if(emp_profile.isOTP_req_for_account_closing == True):
            OTP_code = randint(100000, 999999)
            expiry_time = timezone.now() + timedelta(minutes=5)
            if (EmployeeOTP.objects.filter(employee=emp.pk, otp_for="7", expiry__gt=timezone.now()).exists()):
                return Response({"message": "A account closing OTP already exists. Please use it / wait till its expire"}, status=status.HTTP_400_BAD_REQUEST)
            EmployeeOTP.objects.create(employee=emp, otp_for="7", email_id=user.email,
                                    otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
            return Response({"message": "Enter OTP sent to your mobile number to proceed further."})
        else:
            if scheme.scheme_type == 2:
                joined_date = sch_account.start_date
                today = date.today()
                days_elapsed = (today - joined_date).days
                if(int(scheme.digi_maturity_days) > int(days_elapsed)):
                    payment_datas = Payment.objects.filter(id_scheme=scheme.pk, 
                                                           id_scheme_account=sch_account.id_scheme_account)
                    total_bonus_weight = payment_datas.aggregate(
                        total=Sum('bonus_metal_weight'))['total'] or Decimal('0.000')
                    try:
                        closing_weight = Decimal(str(request.data.get('closing_weight', '0')))
                    except (InvalidOperation, TypeError):
                        closing_weight = Decimal('0')
                    bonus_weight = Decimal(str(total_bonus_weight))
                    total_weight = closing_weight + bonus_weight
                    total_weight_with_bonus = float(f"{total_weight:.3f}")
                    sch_account.closing_weight = total_weight_with_bonus
                else:
                    sch_account.closing_weight = request.data['closing_weight']
                    
            sch_account.closed_employee = emp
            sch_account.closing_id_branch = branch
            sch_account.is_closed = True
            sch_account.closing_date = date.today()
            sch_account.total_paid_ins = request.data['total_paid_ins']
            sch_account.closing_balance = request.data['closing_balance']
            sch_account.closing_amount = request.data['closing_amount']
            # sch_account.closing_weight = request.data['closing_weight']
            # sch_account.closed_remarks = request.data['closed_remarks']
            sch_account.closing_deductions = request.data['closing_deductions']
            sch_account.additional_benefits = request.data['additional_benefits']
            sch_account.closing_benefits = request.data['closing_benefits']
            sch_account.save()

            sch_seri = SchemeAccountSerializer(sch_account)

            return Response(sch_seri.data,status = status.HTTP_200_OK)

class SchemeAccountCloseRevertView(generics.UpdateAPIView):
    permission_classes = [IsEmployee]
    queryset = SchemeAccount.objects.all()
    serializer_class = SchemeAccountSerializer
    
    def put(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.user.pk).get()
        emp = Employee.objects.filter(user_id = request.user.pk).get()
    
        sch_account = self.get_object()
        sch_account.is_closed = False
        sch_account.closing_weight = None
        sch_account.closing_amount = None
        sch_account.closing_balance = None
        sch_account.closed_employee = None
        sch_account.close_reverted_by = emp
        sch_account.save()
        sch_seri = SchemeAccountSerializer(sch_account)
        return Response(sch_seri.data,status = status.HTTP_200_OK)
    
class PayableFormula :
    
    def any_formula(self,data,min,metal_rate):
        
        try:
            formula_data={}
            if(min):
                if(data['limit_by'] == 1):
                    formula_data.update({"min_amount":float(data['min_parameter']),"min_weight":0.000})
                    
                if(data['limit_by'] == 2):
                    min_weight = int(data['min_parameter'])/int(metal_rate)
                    formula_data.update({"min_weight":float(data['min_parameter']),"min_amount":0.00})
            else:
                if(data['limit_by'] == 1):
                    formula_data.update({"max_weight":0.000, "max_amount":float(data['max_parameter'])})
                    
                if(data['limit_by'] == 2):
                    max_weight = int(data['max_parameter'])/int(metal_rate)
                    formula_data.update({"max_weight":float(data['max_parameter']), "max_amount":0.00})            
            return formula_data
        except ObjectDoesNotExist:
            return None

    def multiples_of_paid_as_payable(self, min, data, sch_id, x1, x2, metal_rate):
        try:
            formula_data={}
            x1_pay_details = Payment.objects.filter(id_scheme_account=sch_id, payment_status=True,
                                                 installment=x1).get()
            amount = (float(x1_pay_details.payment_amount))*(int(x2))
            
            if(min):
                if(data['limit_by'] == 1):
                    formula_data.update({"min_weight":0.000, "min_amount":float(amount)})
                    
                if(data['limit_by'] == 2):
                    min_weight = float(amount) / float(metal_rate)
                    formula_data.update({"min_weight":float(min_weight), "min_amount":0.00})
            else:
                if(data['limit_by'] == 1):
                    formula_data.update({"max_weight":0.000, "max_amount":float(amount)})
                    
                if(data['limit_by'] == 2):
                    max_weight = float(amount) / float(metal_rate)
                    formula_data.update({"max_weight":float(max_weight), "max_amount":0.00})
            return formula_data
        except ObjectDoesNotExist:
            return None

    
    def average_paid_amount_as_payable(self, min, data, sch_id, from_installment, to_installment, metal_rate):
        try:
            formula_data={}
            pay_details = Payment.objects.filter(id_scheme_account=sch_id, payment_status=True,installment__lte=to_installment, installment__gte=from_installment)
            pay_detail_seri = PaymentSerializer(pay_details, many=True)
            
            amount = 0
            for each in pay_detail_seri.data:
                amount += float(each['payment_amount'])
                
                
            formula_amount = amount/len(pay_detail_seri.data)
            
            if(min):
                if(data['limit_by'] == 1):
                    formula_data.update({"min_weight":0.000, "min_amount":float(formula_amount)})
                    
                if(data['limit_by'] == 2):
                    min_weight = float(formula_amount)/float(metal_rate)
                    formula_data.update({"min_weight":float(min_weight), "min_amount":0.00})
            else:
                if(data['limit_by'] == 1):
                    formula_data.update({"max_weight":0.000, "max_amount":float(formula_amount)})
                    
                if(data['limit_by'] == 2):
                    max_weight = float(formula_amount)/float(metal_rate)
                    formula_data.update({"max_weight":float(max_weight), "max_amount":0.00})
            
            return formula_data
        
        except ObjectDoesNotExist:
            return None

    def previous_paid_as_payable(self, min, sch_id, metal_rate, data):
        try:
            formula_data={}
            pay_details = Payment.objects.filter(id_scheme_account=sch_id, payment_status=True,installment=data['min_parameter']).get()
            amount = (float(pay_details.payment_amount))
            
            if(min):
                if(data['limit_by'] == 1):
                    formula_data.update({"min_weight":0.000, "min_amount":float(amount)})
                    
                if(data['limit_by'] == 2):
                    min_weight = float(amount) / float(metal_rate)
                    formula_data.update({"min_weight":float(min_weight), "min_amount":0.00})
            else:
                if(data['limit_by'] == 1):
                    formula_data.update({"max_weight":0.000, "max_amount":float(amount)})
                    
                if(data['limit_by'] == 2):
                    max_weight = float(amount) / float(metal_rate)
                    formula_data.update({"max_weight":float(max_weight), "max_amount":0.00})

            return formula_data
        except ObjectDoesNotExist:
            return None

    
class check_payment_chance_type :
    
    def monthly_check_payment_chance_type(self,data,sch_id):
        if sch_id!='' and sch_id!=None:
            allow_pay       = True
            if Payment.objects.filter(id_scheme_account=sch_id,payment_status=True).exists():
                current_month   = date.today().month
                current_year    = date.today().year
                scheme_payments = Payment.objects.filter(id_scheme_account=sch_id,payment_status=True)
                scheme_payments_seri = PaymentSerializer(scheme_payments, many=True)
                arr =[]
                
                if(len(scheme_payments_seri.data)>0):
                    for pay_data in scheme_payments_seri.data:
                        payment_date_month = (datetime.strptime(pay_data['entry_date'], '%Y-%m-%d').date()).month
                        payment_date_year = (datetime.strptime(pay_data['entry_date'], '%Y-%m-%d').date()).year
                        if (current_year == payment_date_year and current_month == payment_date_month):
                            arr.append(pay_data)
                    # print(data)
                    if(data['payment_chance_value'] <=len(arr)):
                        allow_pay = False
                    else:
                        allow_pay = True
                else:
                    allow_pay = True
            return allow_pay
        else:
            return True
     
    def daily_check_payment_chance_type(self,data,sch_id):
        current_date    = date.today()
        if sch_id!='' and sch_id!=None:
            if Payment.objects.filter(id_scheme_account = sch_id, payment_status = True, entry_date = current_date).exists():
                scheme_payments = Payment.objects.filter(id_scheme_account=sch_id,payment_status=True, entry_date=current_date)
                scheme_payments_seri = PaymentSerializer(scheme_payments, many=True)
                if(int(data['payment_chance_value']) > int(len(scheme_payments_seri.data))):
                    allow_pay = True
                else:
                    allow_pay = False
                return allow_pay
        else:
            return True

class SchemePaymentSettings:

    def scheme_payment_settings(self,id_scheme,paid_installment,metal_rate,id_scheme_account,scheme):
        pay_settings                    = PaymentSettings.objects.filter(scheme=id_scheme)
        pay_settings_serializer         = PaymentSettingsSerializer(pay_settings, many=True)
        scheme_type = scheme['scheme_type'] 
        acc_details = {}
        if(pay_settings_serializer.data and scheme_type != 2):
            for pay_data in pay_settings_serializer.data:
                pay_data['metal_rate'] = metal_rate
                pay_data['paid_installment'] = paid_installment
                pay_data['id_scheme_account'] = id_scheme_account
                # print(pay_data)
                if (pay_data['installment_from'])<= (paid_installment+1) <= (pay_data['installment_to']):
                    
                    min_max_payable_class = MinimumMaximumPayableValue()
                    minimum_payable_details = min_max_payable_class.minimum_payable_details(pay_data)
                    maximum_payable_details = min_max_payable_class.maximum_payable_details(pay_data)
                    ##checking Allow Payment
                    if(pay_data['payment_chance_type']==2):   # Monthly Payment
                        payment_chance = check_payment_chance_type()
                        allow_pay = payment_chance.monthly_check_payment_chance_type(pay_data,pay_data['id_scheme_account'])
                    elif(pay_data['payment_chance_type']==1):
                        payment_chance = check_payment_chance_type() # Daily Payment
                        allow_pay = payment_chance.daily_check_payment_chance_type(pay_data,pay_data['id_scheme_account'])
                    acc_details.update({
                        'limit_type'            :pay_data['limit_by'],
                        'payment_chance_type'   :pay_data['payment_chance_type'],
                        'payment_chance_value'  :pay_data['payment_chance_value'],
                        'discount_type'         :pay_data['discount_type'],
                        'discount_value'        :pay_data['discount_value'],
                        'denom_type'            :pay_data['denom_type'],
                        'denom_value'           :pay_data['denom_value'],
                        'minimum_payable_details':minimum_payable_details,
                        'maximum_payable_details':maximum_payable_details,
                        'allow_pay'             :allow_pay
                        })
                    break
                else:
                    acc_details.update({
                        'limit_type'            :1,
                        'payment_chance_type'   :1,
                        'payment_chance_value'  :0,
                        'discount_type'         :1,
                        'discount_value'        :0,
                        'denom_type'            :1,
                        'denom_value'           :0,
                        'minimum_payable_details':{"min_amount":0.00,"min_weight":0.000},
                        'maximum_payable_details':{"max_weight":0.000,"max_amount":0.00},
                        'allow_pay'             :False
                        })
        elif(scheme_type == 2):
            scheme_obj = Scheme.objects.filter(scheme_id=id_scheme).first()
            # scheme_acnt_obj = SchemeAccount.objects.filter(id_scheme_account=id_scheme_account).first()
            payment_chance = check_payment_chance_type()
            scheme_payment_chance = {'payment_chance_value':scheme_obj.digi_payment_chances}
            acc_details.update({
                        'limit_type'            :1,
                        'payment_chance_type'   :1,
                        'payment_chance_value'  :scheme_obj.digi_payment_chances,
                        'discount_type'         :1,
                        'discount_value'        :0,
                        'denom_type'            :3,
                        'denom_value'           :0,
                        'minimum_payable_details':{"min_amount":0.00,"min_weight":0.00},
                        'maximum_payable_details':{"max_weight":0.000,"max_amount":0.00},
                        'allow_pay'             : payment_chance.daily_check_payment_chance_type(scheme_payment_chance,id_scheme_account)
                        })
        
        else:
            acc_details.update({
                        'limit_type'            :1,
                        'payment_chance_type'   :1,
                        'payment_chance_value'  :0,
                        'discount_type'         :1,
                        'discount_value'        :0,
                        'denom_type'            :1,
                        'denom_value'           :0,
                        'minimum_payable_details':{"min_amount":0.00,"min_weight":0.000},
                        'maximum_payable_details':{"max_weight":0.000,"max_amount":0.00},
                        'allow_pay'             :False
                        })
        return acc_details
class MinimumMaximumPayableValue:
    
    def minimum_payable_details(self,pay_data):
        #Minimum Payable
        payable_formula = PayableFormula()
        if(pay_data['min_formula']==1):
            minimum_payable = payable_formula.any_formula(pay_data,True,pay_data['metal_rate'])
        elif(pay_data['min_formula'] == 2):
            params = pay_data['min_parameter'].split(",")
            minimum_payable = payable_formula.multiples_of_paid_as_payable(True, pay_data, pay_data['id_scheme_account'], params[0], params[1],pay_data['metal_rate'])
        elif(pay_data['min_formula'] == 3):
            installments = pay_data['min_parameter'].split(",")
            minimum_payable = payable_formula.average_paid_amount_as_payable(True, pay_data, pay_data['id_scheme_account'], installments[0], installments[1], pay_data['metal_rate'])
        elif(pay_data['min_formula'] == 4):
            minimum_payable = payable_formula.previous_paid_as_payable(True, pay_data['id_scheme_account'], pay_data['metal_rate'], pay_data)
        return minimum_payable

        #Maximum Payable
    def maximum_payable_details(self,pay_data):
        minimum = False
        pay_formula = PayableFormula()
        if(pay_data['max_formula']==1):
            maximum_payable = pay_formula.any_formula(pay_data,minimum,pay_data['metal_rate'])
        elif(pay_data['max_formula'] == 2):
            params = pay_data['max_parameter'].split(",")
            maximum_payable = pay_formula.multiples_of_paid_as_payable(minimum, pay_data, pay_data['id_scheme_account'], params[0], params[1], pay_data['metal_rate'])
        elif(pay_data['max_formula'] == 3):
            installments = pay_data['max_parameter'].split(",")
            maximum_payable = pay_formula.average_paid_amount_as_payable(minimum, pay_data, pay_data['id_scheme_account'], installments[0], installments[1], pay_data['metal_rate'])
        elif(pay_data['max_formula'] == 4):
            maximum_payable = pay_formula.previous_paid_as_payable(minimum, pay_data['id_scheme_account'], pay_data['metal_rate'], pay_data)
        return maximum_payable


    def payable_settings(self,pay_data,acc_details):
        payable_settings = {}
        if pay_data['installment_from']<= (pay_data['paid_installment']+1) <= pay_data['installment_to']:
            minimum_payable           = {},
            maximum_payable           = {}
            limit_type                = pay_data['limit_by']
            payment_chance_type       = pay_data['payment_chance_type']
            max_chance                = pay_data['payment_chance_value']
            discount_type             = pay_data['discount_type']
            discount_value            = pay_data['discount_value']  

            payable_settings.update({
                'limit_type'            :limit_type,
                'payment_chance_type'   :payment_chance_type,
                'max_chance'            :max_chance,
                'discount_type'         :discount_type,
                'discount_value'        :discount_value,
                'denom_type'            :pay_data['denom_type'],
                'denom_value'           :pay_data['denom_value'],
                })
            
            
            ##checking Payment Settings
            pay_formula = PayableFormula()
            #Minimum Payable
            minimum = True
            if(pay_data['min_formula']==1):
                minimum_payable = pay_formula.any_formula(pay_data,minimum,pay_data['metal_rate'])
            elif(pay_data['min_formula'] == 2):
                params = pay_data['min_parameter'].split(",")
                minimum_payable = pay_formula.multiples_of_paid_as_payable(minimum, pay_data, pay_data['id_scheme_account'], params[0], params[1], pay_data['metal_rate'])
            elif(pay_data['min_formula'] == 3):
                installments = pay_data['min_parameter'].split(",")
                minimum_payable = pay_formula.average_paid_amount_as_payable(minimum, pay_data, pay_data['id_scheme_account'], installments[0], installments[1], pay_data['metal_rate'])
            elif(pay_data['min_formula'] == 4):
                minimum_payable = pay_formula.previous_paid_as_payable(minimum, pay_data['id_scheme_account'], pay_data['metal_rate'], pay_data)
            payable_settings.update({'minimum_payable':minimum_payable})
            #Maximum Payable
            minimum = False
            if(pay_data['max_formula']==1):
                maximum_payable = pay_formula.any_formula(pay_data,minimum,pay_data['metal_rate'])
            elif(pay_data['max_formula'] == 2):
                params = pay_data['min_parameter'].split(",")
                maximum_payable = pay_formula.multiples_of_paid_as_payable(minimum, pay_data, pay_data['id_scheme_account'], params[0], params[1], pay_data['metal_rate'])
            elif(pay_data['max_formula'] == 3):
                installments = pay_data['min_parameter'].split(",")
                maximum_payable = pay_formula.average_paid_amount_as_payable(minimum, pay_data, pay_data['id_scheme_account'], installments[0], installments[1], pay_data['metal_rate'])
            elif(pay_data['max_formula'] == 4):
                maximum_payable = pay_formula.previous_paid_as_payable(minimum, pay_data['id_scheme_account'], pay_data['metal_rate'], pay_data)
            payable_settings.update({'maximum_payable':maximum_payable})
            #Maximum Payable

            return acc_details
    
class SetDigiSchemeTargetWeight(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def post(self, request, *args, **kwargs):
        if not request.data['customerId']:
            return Response({'error': 'Customer ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.data['accountId']:
            return Response({'error': 'Account ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        scheme_acc_obj = SchemeAccount.objects.filter(id_customer=request.data['customerId'], id_scheme_account=request.data['accountId']).first()
        scheme_obj = Scheme.objects.filter(scheme_id=scheme_acc_obj.acc_scheme_id.pk).first()
        if scheme_obj:
            scheme_acc_obj.target_weight = Decimal(request.data['targetWeight'])
            scheme_acc_obj.save()
        return Response({'message':'Target weight updated for scheme account.'}, status = status.HTTP_200_OK)
        
class CustomerDigiSchemesMobileAppView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        customer = Customers.objects.get(user=user)
        scheme_query = Scheme.objects.filter(scheme_type=2)
        scheme_serializer = SchemeSerializer(scheme_query, many=True)
        output = []
        for data in scheme_serializer.data:
            scheme_obj = Scheme.objects.filter(scheme_id=data['scheme_id']).first()
            rate_master         = RateMasterClass()  ## getting metal rate Based on purity and metal
            metal_rate          = rate_master.get_metal_rates(scheme_obj.sch_id_purity.pk, scheme_obj.sch_id_metal.pk)
            instance = {}
            if(SchemeAccount.objects.filter(acc_scheme_id=data['scheme_id'], id_customer=customer.pk, is_closed=0).exists()):
                scheme_acc_query = SchemeAccount.objects.filter(acc_scheme_id=data['scheme_id'], id_customer=customer.pk)
                scheme_acc_serializer = SchemeAccountSerializer(scheme_acc_query, many=True)
                for sch_acc_data in scheme_acc_serializer.data:
                    
                    goalTracking_instance = {}
                    interest_output_data = []
                    
                    scheme_acc_obj = SchemeAccount.objects.filter(id_scheme_account=sch_acc_data['id_scheme_account']).first()
                    
                    
                    interest_setting_query = SchemeDigiGoldInterestSettings.objects.filter(scheme=scheme_obj.pk,)
                    interest_setting_serializer = SchemeDigiGoldInterestSettingsSerializer(interest_setting_query, many=True)
                    
                    today = date.today()
                    days_elapsed = (today - scheme_acc_obj.start_date).days
                    interest_setting = SchemeDigiGoldInterestSettings.objects.filter(
                        scheme=scheme_obj.pk,
                        from_day__lte=days_elapsed,
                        to_day__gte=days_elapsed
                    ).first()
                    interest_percentage = 0
                    if interest_setting:
                        interest_percentage = interest_setting.interest_percentage
                    
                    maturity_days = scheme_obj.digi_maturity_days
                    maturity_date = ""
                    if scheme_acc_obj.start_date and maturity_days:
                        maturity_date = scheme_acc_obj.start_date + timedelta(days=maturity_days)
                    
                    for intrst_data in interest_setting_serializer.data:
                        interest_instance = {}
                        if(intrst_data['from_day'] <= days_elapsed and intrst_data['to_day'] >= days_elapsed):
                            interest_instance.update({
                                'fromDays' : intrst_data['from_day'],
                                'toDays' : intrst_data['to_day'],
                                'interestRate' : intrst_data['interest_percentage'],
                                'isCurrentSlab' : True,
                                'slabCrossed' : False
                            })
                        elif intrst_data['to_day'] < days_elapsed:
                            interest_instance.update({
                                'fromDays' : intrst_data['from_day'],
                                'toDays' : intrst_data['to_day'],
                                'interestRate' : intrst_data['interest_percentage'],
                                'isCurrentSlab' : False,
                                'slabCrossed' : True
                            })
                        else:
                            interest_instance.update({
                                'fromDays' : intrst_data['from_day'],
                                'toDays' : intrst_data['to_day'],
                                'interestRate' : intrst_data['interest_percentage'],
                                'isCurrentSlab' : False,
                                'slabCrossed' : False
                            })
                        if interest_instance not in interest_output_data:
                            interest_output_data.append(interest_instance)
                    
                    total_paid_weight = Payment.objects.filter(id_scheme_account=scheme_acc_obj.id_scheme_account, payment_status=1).aggregate(total=Sum('metal_weight'))['total']
                    total_bonus_weight = Payment.objects.filter(id_scheme_account=scheme_acc_obj.id_scheme_account, payment_status=1).aggregate(total=Sum('bonus_metal_weight'))['total']
                    print(scheme_obj.show_target)
                    print(scheme_acc_obj.target_weight)
                    if(scheme_obj.show_target == True and scheme_acc_obj.target_weight != None and scheme_acc_obj.target_weight > 0):
                        total_weeks = 0
                        target_grams = Decimal(scheme_acc_obj.target_weight)
                        weekly_target = Decimal('0.000')
                        total_weeks = maturity_days // 7
                        
                        
                        if maturity_days % 7 != 0:
                            total_weeks += 1
                        
                        if total_weeks > 0:
                            weekly_target = (Decimal(scheme_acc_obj.target_weight) / Decimal(total_weeks)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                        
                        print(scheme_obj.show_target)
                        print(scheme_acc_obj.target_weight)
                        print(total_weeks)
                        print(target_grams)
                        print(weekly_target)
                        
                        days_left = max((maturity_date - today).days, 0)
                        weekly_savings_tip = f"Save {weekly_target}g per week to achieve your {target_grams}g goal by {format_date(maturity_date)}."
                        goalTracking_instance.update({
                            'targetGrams' : scheme_acc_obj.target_weight,
                            'totalDays' : scheme_obj.digi_maturity_days,
                            'weeklyTarget' : weekly_target,
                            'currentSaved' : Decimal(total_paid_weight) + Decimal(total_bonus_weight),
                            'daysLeft' : days_left,
                            'weeklySavingsTip' : weekly_savings_tip,
                            'showAutoSaveOption' : True,
                            'showProgressCard' : True
                        })
                        
                        achieve_percent = (Decimal(total_paid_weight) + Decimal(total_bonus_weight)) / Decimal(target_grams) * 100
                        achieve_percent = round(achieve_percent, 2)
                        instance.update({
                            'targetAchievedPercent':str(achieve_percent)
                        })
                    else:
                        instance.update({
                            'targetAchievedPercent':''
                        })
                    instance.update({
                        'schemeName': scheme_obj.scheme_name,
                        'schemeDescription': scheme_obj.scheme_description,
                        'metalType' : scheme_obj.sch_id_metal.metal_name,
                        'maturityDays' : scheme_obj.digi_maturity_days,
                        'metalId' : scheme_obj.sch_id_metal.pk,
                        'metalRate' : float(metal_rate),
                        'schemeId': scheme_obj.pk,
                        'accountId':str(sch_acc_data['id_scheme_account']),
                        'joined':True,
                        'actionType': 1,
                        'status':'JOINED',
                        'accountNumber':sch_acc_data['scheme_acc_number'],
                        'accountName':sch_acc_data['account_name'],
                        'weightSavedGrams': total_paid_weight,
                        'maturityBenefitGrams': total_bonus_weight,
                        'totalGoldSavedGrams': Decimal(total_paid_weight) + Decimal(total_bonus_weight),
                        'jointDate' : format_date(scheme_acc_obj.start_date),
                        'maturityDate' : format_date(maturity_date),
                        'isTargetSet': True if scheme_acc_obj.target_weight != None else False,
                        'currentInterestSlab' : f"{interest_setting.from_day}-{interest_setting.to_day}" if interest_setting else "",
                        'currentInterestSlabRate' : float(interest_percentage),
                        'currentDaysFromJointDate' : (days_elapsed),
                        'showTarget' : scheme_obj.show_target,
                        'interestSlabs':interest_output_data,
                        'goalTracking' : goalTracking_instance
                    })
            else:
                interest_setting = SchemeDigiGoldInterestSettings.objects.filter(
                    scheme=scheme_obj.pk).order_by('from_day').first()
                interest_percentage = 0
                if interest_setting:
                    interest_percentage = interest_setting.interest_percentage
                interest_output_data = []
                interest_setting_query = SchemeDigiGoldInterestSettings.objects.filter(scheme=scheme_obj.pk,)
                interest_setting_serializer = SchemeDigiGoldInterestSettingsSerializer(interest_setting_query, many=True)
                for intrst_data in interest_setting_serializer.data:
                    interest_instance = {}
                    # if(intrst_data['from_day'] <= days_elapsed and intrst_data['to_day'] >= days_elapsed):
                    #     interest_instance.update({
                    #         'fromDays' : intrst_data['from_day'],
                    #         'toDays' : intrst_data['to_day'],
                    #         'interestRate' : intrst_data['interest_percentage'],
                    #         'isCurrentSlab' : True,
                    #         'slabCrossed' : False
                    #     })
                    # elif intrst_data['to_day'] < days_elapsed:
                    #     interest_instance.update({
                    #         'fromDays' : intrst_data['from_day'],
                    #         'toDays' : intrst_data['to_day'],
                    #         'interestRate' : intrst_data['interest_percentage'],
                    #         'isCurrentSlab' : False,
                    #         'slabCrossed' : True
                    #     })
                    # else:
                    interest_instance.update({
                        'fromDays' : intrst_data['from_day'],
                        'toDays' : intrst_data['to_day'],
                        'interestRate' : intrst_data['interest_percentage'],
                        'isCurrentSlab' : False,
                        'slabCrossed' : False
                    })
                    if interest_instance not in interest_output_data:
                        interest_output_data.append(interest_instance)
                
                instance.update({
                        'targetAchievedPercent':'',
                        'schemeName': scheme_obj.scheme_name,
                        'schemeDescription': scheme_obj.scheme_description,
                        'metalType' : scheme_obj.sch_id_metal.metal_name,
                        'metalId' : scheme_obj.sch_id_metal.pk,
                        'metalRate' : float(metal_rate),
                        'schemeId': scheme_obj.pk,
                        'accountId':'',
                        'joined':False,
                        'actionType':0,
                        'status':'NOT_JOINED',
                        'accountNumber':'',
                        'accountName':'',
                        'weightSavedGrams': Decimal('0.000'),
                        'maturityBenefitGrams': Decimal('0.000'),
                        'totalGoldSavedGrams': Decimal('0.000'),
                        'jointDate' : '',
                        'maturityDate' : '',
                        'isTargetSet': False,
                        'currentInterestSlab' : f"{interest_setting.from_day}-{interest_setting.to_day}" if interest_setting else "",
                        'currentInterestSlabRate' : float(interest_percentage),
                        'currentDaysFromJointDate' : 0,
                        'showTarget' : scheme_obj.show_target,
                        'interestSlabs':interest_output_data,
                        'goalTracking' : {}
                    })
            if instance not in output:
                output.append(instance)
        return Response({"data":output,"message":"Data retrieved successfully"}, status = status.HTTP_200_OK)