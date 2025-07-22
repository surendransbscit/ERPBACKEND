from django.shortcuts import render
from rest_framework import generics, permissions, status , serializers
from rest_framework.response import Response
from django.db import IntegrityError, transaction
from django.utils import timezone
from random import randint
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee, IsEmployeeOrCustomer
from rest_framework.permissions import AllowAny
from datetime import datetime, timedelta, date
from rest_framework.views import APIView
import base64
from PIL import Image
from django.core.files.images import ImageFile
import io
from rest_framework.decorators import api_view
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist,ValidationError
import logging
from cryptography.fernet import Fernet
import os
logger = logging.getLogger(__name__)
from django.db.models import Q, ProtectedError
from re import sub



from knox.models import AuthToken
from accounts.serializers import UserSerializer
from retailsettings.models import (RetailSettings)
from .serializers import (CustomerSerializer, CustomerLoginSerializer, CustomerLoginPinSerializer, CustomerAddressSerializer,
                          CustomerFamilyDetailsSerializer, CustomerDeviceIdMasterSerializer, CustomerNomineeSerializer,
                          TempCustomersSerializer, CustomerEnquirySerializer)
from .models import(Customers, CustomerLoginPin, CustomerAddress, CustomerFamilyDetails, CustomerDeviceIdMaster,
                    CustomerNominee, TempCustomers, CustomerEnquiry)
from accounts.models import User
from employees.models import (Employee, EmployeeSettings)
from managescheme.models import (SchemeAccount)
from managescheme.serializers import SchemeAccountSerializer
from retailmasters.serializers import (CompanySerializer, CustomerNotificationMasterSerializer, CustomerNotificationsSerializer)
from retailmasters.models import (Company, Area, RelationType, Profession,ErpService, CustomerNotifications, CustomerNotificationMaster, Product, WeightRange, Design, Size)
from retailmasters.views import (CompanyAPI)
from schemepayment.models import Payment
from utilities.pagination_mixin import PaginationMixin
from utilities.utils import format_date,date_format_with_time
from utilities.constants import FILTERS
from utilities.notifications import send_push_notification
from core.views  import get_reports_columns_template
from core.models import (TempCustomerOtp)
from services.send_sms_message import send_customer_reg_sms

from .constants import (CUSTOMER_COLUMN_LIST,CUSTOMER_ACTION_LIST, APPROVAL_CUSTOMER_COLUMN_LIST)
# Create your views here.

pagination = PaginationMixin()  # Apply pagination

fernet = Fernet(os.getenv('crypt_key'))
class LogoutView(APIView):

    def get(self, request, format=None):
        request.auth.delete()
        return Response({"Message": "Account Logged out successfully"},status=status.HTTP_204_NO_CONTENT)
    
class CustomerApprovalListView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    queryset = Customers.objects.all()
    serializer_class = CustomerSerializer
    
    def get(self, request, *args, **kwargs):
        filter_type = request.query_params.get('type', 1)
        added_through = request.query_params.get('added_through', 1)
        employee = Employee.objects.filter(user = request.user.pk).get()
        show_full_number = EmployeeSettings.objects.get(id_employee=employee.pk).is_show_full_mobile
        queryset = Customers.objects.filter(catalogue_req_status=1).order_by('-pk')
        if int(filter_type) == 2:
            queryset = Customers.objects.filter(approved_status=2).order_by('-pk')
        elif int(filter_type) == 3:
            queryset = Customers.objects.filter(approved_status=3).order_by('-pk')
        serializer = CustomerSerializer(queryset, many=True, context={"request":request})
        output = []
        preview_images =[]
        for index,data in enumerate(serializer.data):
            instance = {}
            if (data['gender'] == 1):
                instance.update({"gender":"Male"})
            elif (data['gender'] == 2):
                instance.update({"gender":"Female"})
            else:
                instance.update({"gender":"Other"})
            if(CustomerAddress.objects.filter(customer=data['id_customer']).exists()):
                cus_address = CustomerAddress.objects.filter(customer=data['id_customer']).get()
                area       = Area.objects.filter(id_area=cus_address.area.pk).get()
                instance.update({"area_name":area.area_name})
            if (data['cus_img'] == None):
                instance.update({"image":None, "image_text":data['firstname'][0]})
            if (data['cus_img'] != None):
                preview_images.append({"image":data['cus_img'], "name":data['firstname']})
                instance.update({"image":data['cus_img'], "image_text":data['firstname'][0]})
            instance.update({
                "sno":index+1,
                "pk_id":data['id_customer'],
                "id_customer":data['id_customer'],
                "email":data['email'],
                "reference_no":data['reference_no'], 
                "name": data['firstname'],
                "date_add":format_date(data['created_on']),
                "show_catalogue_date":date_format_with_time(data['show_catalogue_date']),
                "title":data['title'], 
                "date_of_birth":data['date_of_birth'],
                "firstname":data['firstname'],
                "lastname":data['lastname'], 
                "emp_ref_code":data['emp_ref_code'], 
                "mob_code":data['mob_code'],
                "preview_images":preview_images,
                "isChecked":False,
                "company_name":data['company_name'],
                "gst_number":data['gst_number'],
                "show_catalogue":"Life Time" if data['catalogue_visible_type']==0 else "Limited",
                "catalogue_visible_type":data['catalogue_visible_type'],
            })
            if show_full_number:
                instance.update({"mobile":data['mob_code']+"-"+data['mobile'],
                             "mobile_woc":data['mobile']})
            else:
                # Mask the mobile number (e.g., show first 2 and last 2 digits)
                masked_mobile = data['mobile'][:2] + "X" * (len(data['mobile']) - 4) + data['mobile'][-2:]
                instance.update({"mobile":data['mob_code']+"-"+masked_mobile,
                        "mobile_woc":masked_mobile})
            if instance not in output:
                output.append(instance)
        if added_through==1:
            response_data = {
                'columns':APPROVAL_CUSTOMER_COLUMN_LIST,
                'rows':output}
            return Response(response_data,status=status.HTTP_200_OK)
        else:
            return Response({"data":output,"message":"No Records Found" if len(output)==0 else "Data Retrieved Successfully"},status=status.HTTP_200_OK)
        
    
    def post(self, request, *args, **kwargs):
        approve_ids = request.data['approve_ids']
        
        
        service = ErpService.objects.filter(short_code='login_approval').first()
        for data in approve_ids:
            show_catalogue = 0
            show_catalogue_date = None
            if "show_catalogue" in data:
                show_catalogue = data['show_catalogue']
            if "show_catalogue_date" in data:
                show_catalogue_date = data['show_catalogue_date']
                show_catalogue_date = datetime.strptime(show_catalogue_date, "%d-%m-%Y %H:%M:%S")
                show_catalogue_date = timezone.make_aware(show_catalogue_date)
            customer = Customers.objects.filter(id_customer=data['pk_id']).update(
                catalogue_req_status=request.data['approved_status'],
                approved_through=request.data['approved_through'],
                show_catalogue_date = show_catalogue_date,
                catalogue_visible_type = show_catalogue
                )
            if service.send_notification:
                customer = CustomerDeviceIdMaster.objects.filter(customer=data['pk_id'])
                device_serializers = CustomerDeviceIdMasterSerializer(customer, many=True)
                for device in device_serializers.data:
                    if device['subscription_id'] != None and device['subscription_id']!='':
                        send_push_notification(device['subscription_id'], "Customer Approval", service.content)
        
        return Response({"message":"Customers Approved Successfully."},status=status.HTTP_200_OK)
        
class CustomerListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = Customers.objects.all()
    serializer_class = CustomerSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Customers.objects.filter(active=1)
            serializer = CustomerSerializer(queryset, many=True)
            for data in serializer.data:
                data.update({'isChecked':False})
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.query_params['branch']!='undefined':
            branch_ids_list = list(map(int, request.query_params['branch'].split(',')))
            queryset = Customers.objects.filter(id_branch__in=branch_ids_list)
        else:
            queryset = Customers.objects.filter(active=True)
        queryset = queryset.order_by('-pk')
        paginator, page = pagination.paginate_queryset(queryset, request,None,CUSTOMER_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,CUSTOMER_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True, context={"request":request})
        output = []
        preview_images =[]
        employee = Employee.objects.filter(user = request.user.pk).get()
        show_full_number = EmployeeSettings.objects.get(id_employee=employee.pk).is_show_full_mobile
        for index,data in enumerate(serializer.data):
            instance = {}
            if (data['gender'] == 1):
                instance.update({"gender":"Male"})
            elif (data['gender'] == 2):
                instance.update({"gender":"Female"})
            else:
                instance.update({"gender":"Other"})
            if(CustomerAddress.objects.filter(customer=data['id_customer']).exists()):
                cus_address = CustomerAddress.objects.filter(customer=data['id_customer']).get()
                area       = Area.objects.filter(id_area=cus_address.area.pk).get()
                instance.update({"area_name":area.area_name})
            # decrypted_gst = fernet.decrypt(data['gst_number'])
            # decrypted_pan = fernet.decrypt(data['pan_number'])
            if (data['cus_img'] == None):
                instance.update({"image":None, "image_text":data['firstname'][0]})
            if (data['cus_img'] != None):
                preview_images.append({"image":data['cus_img'], "name":data['firstname']})
                instance.update({"image":data['cus_img'], "image_text":data['firstname'][0]})
            instance.update({"sno":index+1,"pk_id":data['id_customer'],"id_customer":data['id_customer'],"email":data['email'],"reference_no":data['reference_no'], 
                             "name": data['firstname'],"date_add":format_date(data['created_on']),
                             "title":data['title'], "date_of_birth":data['date_of_birth'],"firstname":data['firstname'],
                             "lastname":data['lastname'], "emp_ref_code":data['emp_ref_code'], "mob_code":data['mob_code'], 
                             "for_search": (data['firstname'] + " " +data['mobile']),
                            #  "gst_number":decrypted_gst,"is_active":data['active'],"pan":decrypted_pan,
                             "gst_number":data['gst_number'],"is_active":data['active'],"pan":data['pan_number'],
                             "preview_images":preview_images,
                             "total_accounts":SchemeAccount.objects.filter(id_customer=data['id_customer']).count()})
            # if data['mobile'] != None and len(data['mobile'])>15:
            #     try:
            #         decrypted_mobile = fernet.decrypt(str(data['mobile']).encode()).decode()

            #         if show_full_number:
            #             # Show full mobile number
            #             instance.update({"mobile":data['mob_code']+"-"+decrypted_mobile,
            #                  "mobile_woc":decrypted_mobile})
            #         else:
            #             # Mask the mobile number (e.g., show first 2 and last 2 digits)
            #             masked_mobile = decrypted_mobile[:2] + "X" * (len(decrypted_mobile) - 4) + decrypted_mobile[-2:]
            #             instance.update({"mobile":data['mob_code']+"-"+masked_mobile,
            #                  "mobile_woc":masked_mobile})
            #     except Exception as e:
            #         print("Decryption failed:", str(e))
          
            if show_full_number:
                instance.update({"mobile":data['mob_code']+"-"+data['mobile'],
                             "mobile_woc":data['mobile']})
            else:
                # Mask the mobile number (e.g., show first 2 and last 2 digits)
                masked_mobile = data['mobile'][:2] + "X" * (len(data['mobile']) - 4) + data['mobile'][-2:]
                instance.update({"mobile":data['mob_code']+"-"+masked_mobile,
                        "mobile_woc":masked_mobile})

            if instance not in output:
                output.append(instance)
                
        FILTERS['isDateFilterReq'] = True
        context={
            'columns':columns,
            'actions':CUSTOMER_ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(output,context)
    
    def post(self,request,*args, **kwargs):
        if request.data['email']!=None and request.data['email'] != '' and User.objects.filter(email=request.data['email']).exists():
            return Response({"message": "Email id already in use"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=request.data['mobile']).exists():
            return Response({"message": "Username already in use"}, status=status.HTTP_400_BAD_REQUEST)
        if Customers.objects.filter(mobile=request.data['mobile']).exists():
            return Response({"message": "Mobile number already in use"}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            try:
                customer_address = request.data['customer_address']
                relation_details = request.data['relation_details']
                del request.data['customer_address']
                del request.data['relation_details']
                if(request.data['img'] != None):
                    b = ((base64.b64decode(request.data['img']
                    [request.data['img'].find(",") + 1:])))
                    img = Image.open(io.BytesIO(b))
                    filename = 'cus_img.jpeg'
                    img_object = ImageFile(io.BytesIO(
                    img.fp.getvalue()), name=filename)
                    request.data.update({"cus_img":img_object})
                else:
                    request.data.update({"cus_img":None})
                today = date.today()
                expiry = today.replace(today.year + 1)
                password = request.data['mobile']
                user = User.objects.create(is_customer=True,email=request.data['email'], 
                                       username = request.data['mobile'], first_name=request.data['firstname'],
                                       last_name=request.data['lastname'] if request.data['lastname']!=None else 'null', account_expiry=expiry)
                user.set_password(password)
                user.save()
                encrypted_pan=None
                encrypted_gst=None
                encrypted_aadhar=None
                encrypted_mobile=None
                if(request.data['pan_number']!= None):
                    encrypted_pan = (fernet.encrypt(str(request.data['pan_number']).encode())).decode()
                if(request.data['gst_number']!= None):
                    encrypted_gst = (fernet.encrypt(str(request.data['gst_number']).encode())).decode()
                if(request.data['aadhar_number']!= None):
                    encrypted_aadhar = (fernet.encrypt(str(request.data['aadhar_number']).encode())).decode()
                # if(request.data['mobile']!= None):
                #     encrypted_mobile = (fernet.encrypt(str(request.data['mobile']).encode())).decode()
                del request.data['pan_number']
                del request.data['gst_number']
                del request.data['aadhar_number']
                #del request.data['mobile']
                request.data.update({
                    # "created_by": request.user.pk, 
                    "user": user.pk,
                    "pan_number":encrypted_pan, 
                    "gst_number":encrypted_gst,
                    "aadhar_number":encrypted_aadhar, 
                    "mobile":request.data['mobile']
                })

                request.data.update({"created_by": request.user.pk, "user": user.pk,
                                     "pan_number":encrypted_pan, "gst_number":encrypted_gst,
                                     "aadhar_number":encrypted_aadhar, "mobile":request.data['mobile'],
                                     "approved_status":2})

                serializer = CustomerSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                # print(serializer.data)
                customer_address.update({"customer": serializer.data['id_customer']})
                address_serializer = CustomerAddressSerializer(data=customer_address)
                address_serializer.is_valid(raise_exception=True)
                address_serializer.save()
                for relation_data in relation_details:
                    relation_data.update({"customer": serializer.data['id_customer']})
                    relation_serializer = CustomerFamilyDetailsSerializer(data=relation_data)
                    relation_serializer.is_valid(raise_exception=True)
                    relation_serializer.save()
                return Response(serializer.data,status=status.HTTP_201_CREATED)   
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
                return Response({"message": F"A database error occurred.  {e}"}, status=status.HTTP_400_BAD_REQUEST)
                
            
        

class CustomerDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = Customers.objects.all()
    serializer_class = CustomerSerializer
    
    def get(self, request, *args, **kwargs):
        customer = self.get_object()
        if ('changestatus' in request.query_params):
            if(customer.active == True):
                customer.active = False
            else:
                customer.active = True
            customer.updated_by = self.request.user
            customer.updated_on = datetime.now(tz=timezone.utc)
            customer.save()
            return Response({"Message": "Customer status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = CustomerSerializer(customer, context={"request":request})
        output = serializer.data
        if customer.mobile != None and len(customer.mobile)>15:
            try:
                decrypted_mobile = fernet.decrypt(str(customer.mobile).encode()).decode()
                
                output.update({"mobile":decrypted_mobile})
            except Exception as e:
                    print("Decryption failed:", str(e))
        else:
            output.update({"mobile":customer.mobile})
        if customer.gst_number != None and len(customer.gst_number)>15:
            try:
                
                decrypted_gst = fernet.decrypt(str(customer.gst_number).encode()).decode()
                output.update({"gst_number": decrypted_gst,})
            except Exception as e:
                    print("Decryption failed:", str(e))
        else:
            output.update({"gst_number": customer.gst_number,})
        if customer.pan_number != None and len(customer.pan_number)>15:
            try:
                decrypted_pan = fernet.decrypt(str(customer.pan_number).encode()).decode()
                output.update({"pan_number":decrypted_pan})
            except Exception as e:
                    print("Decryption failed:", str(e))
        else:
            output.update({"pan_number":customer.pan_number})
        if customer.aadhar_number != None and len(customer.aadhar_number)>15:
            try:
                decrypted_aadhar = fernet.decrypt(str(customer.aadhar_number).encode()).decode()
                output.update({"aadhar_number":decrypted_aadhar})
            except Exception as e:
                    print("Decryption failed:", str(e))
        else:
            output.update({"aadhar_number":customer.aadhar_number})
        relations_details = []
        address_details = {}
        if(CustomerFamilyDetails.objects.filter(customer=customer.id_customer).exists()):
            relation_queryset = CustomerFamilyDetails.objects.filter(customer=customer.id_customer)
            relation_serializer = CustomerFamilyDetailsSerializer(relation_queryset, many=True)
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
                    }
                })
                if relation_data not in relations_details:
                    relations_details.append(relation_data)
        if(CustomerAddress.objects.filter(customer=customer.id_customer).exists()):
            address = CustomerAddress.objects.filter(customer=customer.id_customer).get()
            address_serializer = CustomerAddressSerializer(address)
            address_details = address_serializer.data
        output.update({
            "customer_address":address_details,
            "relations_details":relations_details,
            #"created_by": customer.created_by.username,
            "updated_by": customer.updated_by.username if customer.updated_by != None else None
        })
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        customer_address = request.data['customer_address']
        relation_details = request.data['relation_details']
        del request.data['customer_address']
        del request.data['relation_details']
        # request.data.update({"created_by": obj.created_by.id})
        with transaction.atomic():
            new_email = (request.data.get('email') or '').strip()
            if new_email and new_email != obj.email:
                if User.objects.filter(email=new_email).exists():
                    return Response({"message": "Email id already in use"}, status=status.HTTP_400_BAD_REQUEST)
                User.objects.filter(id=obj.user.pk).update(email=new_email)


            customer_address.update({"customer":obj.id_customer})
            print(customer_address)
            if(CustomerAddress.objects.filter(customer=obj.id_customer).exists()):
                address_query =CustomerAddress.objects.filter(customer=obj.id_customer).get()
                address_serializer = CustomerAddressSerializer(address_query, data=customer_address)
                address_serializer.is_valid(raise_exception=True)
                address_serializer.save()
            else:
                address_serializer = CustomerAddressSerializer(data=customer_address)
                address_serializer.is_valid(raise_exception=True)
                address_serializer.save()
            if(CustomerFamilyDetails.objects.filter(customer=obj.id_customer).exists()):
                CustomerFamilyDetails.objects.filter(customer=obj.id_customer).delete()
                
            for relation_data in relation_details:
                relation_data.update({"customer": obj.id_customer})
                relation_serializer = CustomerFamilyDetailsSerializer(data=relation_data)
                relation_serializer.is_valid(raise_exception=True)
                relation_serializer.save()
                
            if (request.data['img'] != None):
                if 'data:image/' in request.data['img'][:30]:
                    # update items  for which image is changed
                    obj.cus_img.delete()
                    b = ((base64.b64decode( request.data['img'][ request.data['img'].find(",") + 1:])))
                    img = Image.open(io.BytesIO(b))
                    filename = 'emphoto.jpeg'
                    img_object = ImageFile(io.BytesIO(
                        img.fp.getvalue()), name=filename)
                    request.data.update({"cus_img": img_object})
                    encrypted_pan=None
                    encrypted_gst=None
                    encrypted_aadhar=None
                    encrypted_mobile=None
                    if(request.data['pan_number']!= None):
                        encrypted_pan = (fernet.encrypt(str(request.data['pan_number']).encode())).decode()
                    if(request.data['gst_number']!= None):
                        encrypted_gst = (fernet.encrypt(str(request.data['gst_number']).encode())).decode()
                    if(request.data['aadhar_number']!= None):
                        encrypted_aadhar = (fernet.encrypt(str(request.data['aadhar_number']).encode())).decode()
                    # if(request.data['mobile']!= None):
                    #     encrypted_mobile = (fernet.encrypt(str(request.data['mobile']).encode())).decode()
                    del request.data['pan_number']
                    del request.data['gst_number']
                    del request.data['aadhar_number']
                    request.data.update({"pan_number":encrypted_pan, "gst_number":encrypted_gst,
                                     "aadhar_number":encrypted_aadhar, "mobile":request.data['mobile']})
                    
                    serializer = self.get_serializer(obj, data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                encrypted_pan=None
                encrypted_gst=None
                encrypted_aadhar=None
                encrypted_mobile=None
                if(request.data['pan_number']!= None):
                    encrypted_pan = (fernet.encrypt(str(request.data['pan_number']).encode())).decode()
                if(request.data['gst_number']!= None):
                    encrypted_gst = (fernet.encrypt(str(request.data['gst_number']).encode())).decode()
                if(request.data['aadhar_number']!= None):
                    encrypted_aadhar = (fernet.encrypt(str(request.data['aadhar_number']).encode())).decode()
                # if(request.data['mobile']!= None):
                #     encrypted_mobile = (fernet.encrypt(str(request.data['mobile']).encode())).decode()
                del request.data['pan_number']
                del request.data['gst_number']
                del request.data['aadhar_number']
                #del request.data['mobile']
                request.data.update({"pan_number":encrypted_pan, "gst_number":encrypted_gst,
                                 "aadhar_number":encrypted_aadhar, "mobile":request.data['mobile']})
                serializer = self.get_serializer(obj, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            else:
                encrypted_pan=None
                encrypted_gst=None
                encrypted_aadhar=None
                encrypted_mobile=None
                if(request.data['pan_number']!= None):
                    encrypted_pan = (fernet.encrypt(str(request.data['pan_number']).encode())).decode()
                if(request.data['gst_number']!= None):
                    encrypted_gst = (fernet.encrypt(str(request.data['gst_number']).encode())).decode()
                if(request.data['aadhar_number']!= None):
                    encrypted_aadhar = (fernet.encrypt(str(request.data['aadhar_number']).encode())).decode()
                if(request.data['mobile']!= None):
                    encrypted_mobile = (fernet.encrypt(str(request.data['mobile']).encode())).decode()
                del request.data['pan_number']
                del request.data['gst_number']
                del request.data['aadhar_number']
                request.data.update({"pan_number":encrypted_pan, "gst_number":encrypted_gst,
                                 "aadhar_number":encrypted_aadhar, "mobile":request.data['mobile'],
                                 "cus_img":None})
                serializer = self.get_serializer(obj, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Customer instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
     
class CustomerTokenRefreshView(generics.GenericAPIView):
    serializer_class = CustomerLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        # header_token = request.META.get('HTTP_AUTHORIZATION', None)
        # header_token = request.data.get('token', None)
        # print(header_token)
        if not Customers.objects.filter(id_customer=request.data['id_customer']).exists():
            return Response({"status": False, "message": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        customer = Customers.objects.get(id_customer=request.data['id_customer'])
        serializers = CustomerSerializer(customer, context=self.get_serializer_context())
        if not User.objects.filter(id=serializers.data['user']).exists():
            return Response({"status": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user = User.objects.get(id=customer.user.pk)
        if user.is_anonymous is False:
            if user.is_customer:
                token = AuthToken.objects.create(user)
                expiry = timezone.localtime(token[0].expiry)
                User.objects.filter(id=user.id).update(last_login=datetime.now(tz=timezone.utc))
                return Response({"status": True,"token": token[1],"login_expiry": expiry})
        # if header_token is not None:
        #     try:
        #         token = sub('Token ', '',
        #                     request.data.get('token', None))
        #         token_obj = AuthToken.objects.get(token_key=token[:8])
        #         customer = Customers.objects.get(id_customer=request.data.get['id_customer'])
        #         print(request.data)
        #         user = User.objects.get(id=token_obj.user_id)
        #         # request.user = token_obj.user
        #         current_user = user
        #         if current_user.is_anonymous is False:
        #             if current_user.is_customer:
        #                 token = AuthToken.objects.create(current_user)
        #                 token_obj.delete()
        #                 return Response({"status": True,"token": token[1]})
        #     except AuthToken.DoesNotExist:
        #         return Response({"status": False, "message": "Invalid Token"}, status=status.HTTP_404_NOT_FOUND)
        # return Response({"status": True},status=status.HTTP_200_OK)


class EmployeeTokenRefreshView(generics.GenericAPIView):
    serializer_class = CustomerLoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        # header_token = request.META.get('HTTP_AUTHORIZATION', None)
        header_token = request.data.get('token', None)
        print(header_token)
        if header_token is not None:
            try:
                token = sub('Token ', '',
                            request.data.get('token', None))
                token_obj = AuthToken.objects.get(token_key=token[:8])
                user = User.objects.get(id=token_obj.user_id)
                # request.user = token_obj.user
                current_user = user
                if current_user.is_anonymous is False:
                    if current_user.is_adminuser:
                        token = AuthToken.objects.create(current_user)
                        token_obj.delete()
                        return Response({"status": True,"token": token[1]})
            except AuthToken.DoesNotExist:
                return Response({"status": False, "message": "Invalid Token"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"status": True},status=status.HTTP_200_OK)

class CustomerSignInAPI(generics.GenericAPIView):
    serializer_class = CustomerLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        if 'login_pin' in request.data:
            try:
                user = User.objects.get(username=request.data['username'], is_customer=True)
                customer = Customers.objects.get(user=user.pk)
                pin = CustomerLoginPin.objects.get(user=user.pk, customer=customer.pk)
                
                comp = Company.objects.latest("id_company")

                country = CompanyAPI.get_country(self, comp.country.pk)

                
                if request.data['login_pin'] == pin.pin:
                    user_data = UserSerializer(user, context=self.get_serializer_context()).data
                    cus = Customers.objects.get(user_id=user_data['id'])
                    sign_serializer = CustomerSerializer(cus,context={"request":request})
                    preferences = {}

                    token = AuthToken.objects.create(user)
                    expiry = timezone.localtime(token[0].expiry)
                    User.objects.filter(id=user.id).update(last_login=datetime.now(tz=timezone.utc))
                    
                    return Response({
                        "status": True,
                        "token": token[1],
                        "login_expiry": expiry,
                        "redirect": True,
                        "customer": sign_serializer.data,
                        "preferences": preferences,
                        "currency_sybmol":(country['currency_code'])
                    })
                else:
                    return Response({"status": False, "message": "Invalid PIN"}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"status": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except Customers.DoesNotExist:
                return Response({"status": False, "message": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
            except CustomerLoginPin.DoesNotExist:
                return Response({"status": False, "message": "PIN not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.validated_data
                user_data = UserSerializer(user, context=self.get_serializer_context()).data
                cus = Customers.objects.get(user_id=user_data['id'])
                sign_serializer = CustomerSerializer(cus, context={"request":request})
                serialized_data = sign_serializer.data
                customer_need_to_approved = RetailSettings.objects.get(name='is_customer_need_to_be_approved').value
                is_amount_show_in_catalog_app = RetailSettings.objects.get(name='is_amount_show_in_catalog_app').value
                if int(customer_need_to_approved) == 1:
                        if serialized_data['approved_status']==1:
                            return Response({"status": False, "message": "Please Wait for The Admin Approval to Login"}, status=status.HTTP_200_OK)
                        if serialized_data['approved_status']==3:
                            return Response({"status": False, "message": "Your request has beed rejected by Admin. Contact support."}, status=status.HTTP_200_OK)
                        
                preferences = {}

                token = AuthToken.objects.create(user)
                expiry = timezone.localtime(token[0].expiry)
                User.objects.filter(id=user.id).update(last_login=datetime.now(tz=timezone.utc))
                company = Company.objects.latest("id_company")
                serializer = CompanySerializer(company)
                company_api = CompanyAPI()
                country = company_api.get_country(serializer.data['country'])

                if "subscription_id" in request.data:
                    update_customer_device_id = UpdateCustomerDeviceId()
                    update_customer_device_id.update_customer_device_id(request.data['device_id'],request.data['subscription_id'],serialized_data['id_customer'])
                
                cus_accounts = SchemeAccount.objects.filter(id_customer=sign_serializer.data['id_customer'])
                if  cus_accounts.exists():
                    result = SchemeAccountSerializer(cus_accounts, many=True)
                    total_weight = 0
                    account_paid_weight = 0
                    for data in result.data:
                        account_paid_weight = Payment.objects.filter(id_scheme_account=data['id_scheme_account'], payment_status=1).aggregate(total=Sum('metal_weight'))['total'] or 0
                        total_weight += account_paid_weight
                
                    serialized_data.update({"total_weight": f"{round(total_weight, 3)} Grams"})
                
                return Response({
                    "status": True,
                    "token": token[1],
                    "login_expiry": expiry,
                    "redirect": True,
                    "customer": serialized_data,
                    "preferences": preferences,
                    "is_amount_show_in_catalog_app":is_amount_show_in_catalog_app,
                    "allow_delete_view":True,
                    "currency_sybmol":(country['currency_code'])
                })
            except IntegrityError as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except KeyError as e:
                return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
            except ValidationError as e:
                return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response({"status": False, "message": "Invalid credentials"}, status=status.HTTP_200_OK)


class UpdateCustomerDeviceId(generics.GenericAPIView):
    
    def update_customer_device_id(self,device_id,subscription_id, customer_id):
        if not CustomerDeviceIdMaster.objects.filter(deviceID=subscription_id).exists():
            deviceid_master_instance = {
                "customer":customer_id,
                "deviceID":device_id,
                "subscription_id":subscription_id,
                "is_active":True
            }
            device_id_serializer = CustomerDeviceIdMasterSerializer(data=deviceid_master_instance)
            device_id_serializer.is_valid(raise_exception=True)
            device_id_serializer.save()
            return Response({"message":"Device ID updated successfully."}, status=status.HTTP_200_OK)

class CustomerSignupAPI(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    
    def create_customer(self, request_data, customer_need_to_approved, show_catalogue_restriction):
        email = request_data.get('email', '').strip() or None
        mobile = request_data.get('mobile', '').strip()

        if email:
            if User.objects.filter(email=email).exists():
                raise ValidationError("Email id already in use")
            if Customers.objects.filter(email=email).exists():
                raise ValidationError("Email ID already in use")

        if User.objects.filter(username=mobile).exists():
            raise ValidationError("Username already in use")

        if Customers.objects.filter(mobile=mobile).exists():
            raise ValidationError("Mobile number already in use")

        today = date.today()
        expiry = today.replace(today.year + 1)
        password = request_data['confirm_password']
        email = request_data['email'] if request_data['email']!="" else None
        request_data.update({"email":email})
        user = User.objects.create(
            is_customer=True,
            email=email, 
            username = request_data['mobile'], 
            first_name=request_data['firstname'],
            last_name=request_data['lastname'] if(request_data['lastname']!= None) else "",
            account_expiry = expiry
        )
        user.set_password(password)
        user.save()
        request_data.update({"user": user.pk})
        request_data.update({"registered_through": 2})
        if(int(customer_need_to_approved) == 1):
            request_data.update({"approved_status": 1})
        else:
            request_data.update({"approved_status": 2})
        if int(show_catalogue_restriction) == 1:
            request_data.update({"catalogue_req_status": 0})
        else:
            request_data.update({"catalogue_req_status": 2})
        serializer = CustomerSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if "subscription_id" in request_data:
            update_customer_device_id = UpdateCustomerDeviceId()
            update_customer_device_id.update_customer_device_id(request_data['device_id'],request_data['subscription_id'], serializer.data['id_customer'])
        return serializer.data
    
    
    def post(self, request, *args, **kwargs):
        if request.data['email'] != '' and request.data['email'] is not None:
            if User.objects.filter(email=request.data['email']).exists():
                return Response({"message": "Email id already in use"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=request.data['mobile']).exists():
            return Response({"message": "Username already in use"}, status=status.HTTP_400_BAD_REQUEST)
        if Customers.objects.filter(mobile=request.data['mobile']).exists():
            return Response({"message": "Mobile number already in use"}, status=status.HTTP_400_BAD_REQUEST)
        if request.data['email'] != '' and request.data['email'] is not None:
            if Customers.objects.filter(email=request.data['email']).exists():
                return Response({"message": "Email ID already in use"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                is_otp_verify_req_for_reg = False  # Typically from settings
                customer_need_to_approved = RetailSettings.objects.get(name='is_customer_need_to_be_approved').value
                show_catalogue_restriction = RetailSettings.objects.get(name='show_catalogue_restriction').value
                comp = Company.objects.latest("id_company")

                if is_otp_verify_req_for_reg:
                    try:
                        # Check if the customer already exists
                        if not TempCustomers.objects.filter(mobile=request.data['mobile']).exists():
                            temp_cus_serializer = TempCustomersSerializer(data=request.data)
                            if temp_cus_serializer.is_valid(raise_exception=True):
                                temp_cus_serializer.save()
                                id_customer = temp_cus_serializer.data['id_customer']

                        
                        temp_cus_obj = TempCustomers.objects.get(mobile = request.data.get('mobile'))
                        email = request.data.get('email') or None
                        name = request.data.get('firstname', 'User')
                        otp_code = randint(100000, 999999)
                        TempCustomerOtp.objects.create(
                            customer=temp_cus_obj,
                            otp_for=1,
                            email_id=email,
                            otp_code=otp_code,
                            expiry=timezone.now() + timedelta(minutes=5)
                        )
                        template_id = "1707175065621417140"
                        message = f"Dear {name}, Your OTP is {str(otp_code)} for registration. Thank you for registering with TN Jewellers."
                        # Send SMS with proper arguments

                        send_customer_reg_sms(
                            request.data['mobile'], 
                            str(otp_code), 
                            name,
                            [name, str(otp_code)],
                            template_id,
                            message)


                        return Response({
                            "status": True,
                            "title": "OTP Sent",
                            "message": f"An OTP has been sent to {request.data['mobile']}. Please verify to continue. OTP is valid for 5 minutes."
                        }, status=status.HTTP_200_OK)
                    except Exception as e:
                        return Response({"message": f"OTP registration failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                
                # If OTP is not required
                try:
                    self.create_customer(request.data, customer_need_to_approved, show_catalogue_restriction)
                except ValidationError as e:
                    return Response({"message": e.detail}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({"message": f"Customer creation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

                if int(customer_need_to_approved) == 0:
                    return Response({
                        "status": True,
                        "title": "Successfully Registered",
                        "message": f"Congratulations! Your registration with {comp.company_name} is completed successfully",
                        "is_approval_req": False
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "status": True,
                        "title": "Successfully Registered",
                        "message": "Thanks for Registering with us. Please wait for admin approval to log in.",
                        "is_approval_req": True
                    }, status=status.HTTP_200_OK)

            except IntegrityError as e:
                if "Invalid username" in str(e):
                    return Response({"message": "Invalid username"}, status=status.HTTP_400_BAD_REQUEST)
                if "users.username" in str(e):
                    return Response({"message": "Username already allocated"}, status=status.HTTP_400_BAD_REQUEST)
                if "users.users_email" in str(e):
                    return Response({"message": "Email already allocated"}, status=status.HTTP_400_BAD_REQUEST)
            except KeyError as e:
                return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

class CustomerRegOTPVerify(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Delete Expired OTPs of all users.  || Later:  Need to check case of Valid OTPs of this User other than email in request
        TempCustomerOtp.objects.filter(expiry__lt=timezone.now()).delete()
        with transaction.atomic():
            try:
                temp_cus_obj = TempCustomers.objects.filter(mobile=request.data['mobile']).first()
                latest_otp = TempCustomerOtp.objects.filter(otp_for=1, customer=temp_cus_obj.pk, expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['otp']):
                    comp = Company.objects.latest("id_company")
                    customer_need_to_approved = RetailSettings.objects.get(name='is_customer_need_to_be_approved').value
                    show_catalogue_restriction = RetailSettings.objects.get(name='show_catalogue_restriction').value
                    request_data = {
                        "firstname": temp_cus_obj.firstname,
                        "lastname":temp_cus_obj.lastname,
                        "company_name":temp_cus_obj.company_name,
                        "mobile": temp_cus_obj.mobile,
                        "email": temp_cus_obj.email,
                        "confirm_password":temp_cus_obj.confirm_password,
                        "gst_number":temp_cus_obj.gst_number,
                        "pan_number":temp_cus_obj.pan_number,
                        "cus_type":temp_cus_obj.cus_type,
                        "registered_through":temp_cus_obj.registered_through
                    }
                    latest_otp.delete()
                    customer_create_master_class = CustomerSignupAPI()
                    customer_create_master_class.create_customer(request_data, customer_need_to_approved, show_catalogue_restriction)
                    TempCustomerOtp.objects.filter(otp_for=1, customer=temp_cus_obj.pk).delete()  # / mutli request scenario
                    
                    name = temp_cus_obj.firstname
                    template_id = "1707175049969306590"
                    message = f"Dear {name}, you have successfully register with us. Thanks for registration with TN Jewellers."
                    # Send SMS with proper arguments
                    # send_customer_reg_sms(
                    #     temp_cus_obj.mobile, 
                    #     "", 
                    #     name,
                    #     [name],
                    #     template_id,
                    #     message)
                    temp_cus_obj.delete()
                    return Response({
                        "status": True,
                        "title": "OTP verified successfully.",
                        "message": f"Congratulations! Your registration with {comp.company_name} is completed successfully",
                        "is_approval_req": False
                    }, status=status.HTTP_200_OK)
                else:
                    raise TempCustomerOtp.DoesNotExist
            except TempCustomerOtp.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)

class CustomerRegResendVerify(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Delete expired OTPs globally
        TempCustomerOtp.objects.filter(expiry__lt=timezone.now()).delete()

        try:
            with transaction.atomic():
                # First, validate existence of TempCustomer by mobile
                mobile = request.data.get('mobile')
                temp_cus_obj = TempCustomers.objects.filter(mobile=mobile).first()
                if not temp_cus_obj:
                    return Response({
                        "status": False,
                        "message": "Temporary customer not found for the given mobile. Please register again."
                    }, status=status.HTTP_404_NOT_FOUND)

                name = temp_cus_obj.firstname or "Customer"
                mobile = temp_cus_obj.mobile  

                TempCustomerOtp.objects.filter(otp_for=1, customer=temp_cus_obj.pk).delete()

                otp_code = randint(100000, 999999)
                TempCustomerOtp.objects.create(
                    customer=temp_cus_obj,
                    otp_for=1,
                    email_id=None,
                    otp_code=otp_code,
                    expiry=timezone.now() + timedelta(minutes=5)
                )

                # Send SMS
                template_id = "1707175065621417140"
                message = f"Dear {name}, Your OTP is {str(otp_code)} for registration. Thank you for registering with TN Jewellers."

                send_customer_reg_sms(
                    mobile=mobile,
                    otp=str(otp_code),
                    name=name,
                    params=[name, str(otp_code)],
                    template_id=template_id,
                    message=message
                )

                return Response({
                    "status": True,
                    "title": "OTP resent",
                    "message": f"An OTP has been resent to {mobile}. Please verify to continue. OTP is valid for 5 minutes."
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Failed to resend OTP. {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
                
        
class CustomerLoginpinCreateView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def post(self, request, *args, **kwargs):
        cus = Customers.objects.filter(user = request.user.pk).get()
        if(CustomerLoginPin.objects.filter(user=request.user).exists()):
            return Response({"message": "PIN already exists for this user."}, status=status.HTTP_400_BAD_REQUEST)
        request.data.update({"user":request.user.pk, "customer":cus.pk, "updated_on":datetime.now()})
        serializer = CustomerLoginPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CustomerSearchView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        mob_num = request.data.get("mob_num", None)
        name = request.data.get("name", None)

        if mob_num:
            queryset = Customers.objects.filter(mobile__icontains=mob_num)
        elif name:
            queryset = Customers.objects.filter(firstname__icontains=name)
        else:
            return Response({"message": "Please provide either mob_num or name."}, status=status.HTTP_400_BAD_REQUEST)
        is_cus_search_status_chk = RetailSettings.objects.get(name='is_cus_search_status_chk').value
        if int(is_cus_search_status_chk) == 1:
            queryset = queryset.filter(approved_status=2)
        if queryset.exists():
            serializer = CustomerSerializer(queryset, many=True)
            output = []
            for data in serializer.data:
                instance = {
                    **data,
                    "label": f"{data['firstname']}-{data['mobile']}",
                    "value": data["id_customer"]
                }
                if CustomerAddress.objects.filter(customer=data["id_customer"]).exists():
                    address_queryset = CustomerAddress.objects.filter(customer=data["id_customer"]).get()
                    address_serializer = CustomerAddressSerializer(address_queryset)
                    instance.update({"address_details": address_serializer.data})
                if instance not in output:
                    output.append(instance)
            return Response(output, status=status.HTTP_200_OK)
        return Response({"message": "No customer found."}, status=status.HTTP_400_BAD_REQUEST)



class CustomerSearchAutoCompleteView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        mob_num = request.data.get("mob_num", None)
        name = request.data.get("name", None)

        if mob_num:
            queryset = Customers.objects.filter(mobile__icontains=mob_num)
        elif name:
            queryset = Customers.objects.filter(firstname__icontains=name)
        else:
            return Response({"message": "Please provide either mob_num or name."}, status=status.HTTP_400_BAD_REQUEST)
        is_cus_search_status_chk = RetailSettings.objects.get(name='is_cus_search_status_chk').value
        if int(is_cus_search_status_chk) == 1:
            queryset = queryset.filter(approved_status=2)
        if queryset.exists():
            serializer = CustomerSerializer(queryset, many=True)
            output = []
            for data in serializer.data:
                instance = {
                    "label": f"{data['firstname']}-{data['mobile']}",
                    "value": data["id_customer"],
                    "mobile": data["mobile"],
                    "firstname": data["firstname"],
                }
                if instance not in output:
                    output.append(instance)
            return Response({"data":output}, status=status.HTTP_200_OK)
        return Response({"message": "No customer found."}, status=status.HTTP_400_BAD_REQUEST)

    
class CustomerAccountEditView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def post(self, request, *args, **kwargs):
        if User.objects.filter(email=request.data['email']).exists():
            return Response({"message": "Email id already in use"}, status=status.HTTP_400_BAD_REQUEST)
        if Customers.objects.filter(email=request.data['email']).exists():
            return Response({"message": "Email id already in use"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            user = User.objects.filter(id=request.user.id).first()
            customer = Customers.objects.filter(user=user.pk).first()
            if 'mobile' in request.data:
                del request.data['mobile']
            # if 'email' in request.data:
            #     del request.data['email']
            if(request.data['email'] != customer.email):
                user.email = request.data['email']
                user.save()
            request.data.update({"mobile":customer.mobile})
            customer_serializer = CustomerSerializer(customer, data=request.data)
            customer_serializer.is_valid(raise_exception=True)
            customer_serializer.save()
            if(request.data['address1'] != '' and request.data['address1'] != None):
                if(CustomerAddress.objects.filter(customer=customer.pk).exists()):
                    customer_address_data = {
                        "customer":customer.pk,
                        "line1":request.data['address1'],
                        # "line2":request.data['address2']
                    }
                    customer_address = CustomerAddress.objects.filter(customer=customer.pk).first()
                    customer_address_serializer = CustomerAddressSerializer(customer_address, data=customer_address_data)
                    customer_address_serializer.is_valid(raise_exception=True)
                    customer_address_serializer.save()
                elif(CustomerAddress.objects.filter(customer=customer.pk).exists()==False):
                    customer_address_data = {
                        "customer":customer.pk,
                        "line1":request.data['address1'],
                        "line2":None,
                        "line3":None,
                        "pincode":None,
                        "country":None,
                        "state":None,
                        "city":None,
                        "area":None,
                    }
                    customer_address_serializer = CustomerAddressSerializer(data=customer_address_data)
                    customer_address_serializer.is_valid(raise_exception=True)
                    customer_address_serializer.save()
            if(request.data['nominee_name'] != '' and request.data['nominee_name'] != None):
                if(CustomerNominee.objects.filter(id_nominee_cusid=customer.pk).exists()):
                    customer_nominee_data = {
                        "id_nominee_cusid":customer.pk,
                        "nominee_name":request.data['nominee_name'],
                        "nominee_mobile":request.data['nominee_mobile'],
                    }
                    customer_nominee = CustomerNominee.objects.filter(id_nominee_cusid=customer.pk).first()
                    customer_nominee_serializer = CustomerNomineeSerializer(customer_nominee, data=customer_address_data)
                    customer_nominee_serializer.is_valid(raise_exception=True)
                    customer_nominee_serializer.save()
                elif(CustomerNominee.objects.filter(id_nominee_cusid=customer.pk).exists()==False):
                    customer_nominee_data = {
                        "id_nominee_cusid":customer.pk,
                        "nominee_name":request.data['nominee_name'],
                        "nominee_mobile":request.data['nominee_mobile'],
                        "nominee_relationship":None,
                        "nominee_date_of_birth":None,
                        "nominee_date_of_wed":None,
                    }
                    customer_nominee_serializer = CustomerNomineeSerializer(data=customer_nominee_data)
                    customer_nominee_serializer.is_valid(raise_exception=True)
                    customer_nominee_serializer.save()
            return Response({"message":"Profile edited successfully.","data":customer_serializer.data}, status=status.HTTP_200_OK)


class CustomerProfileImageEditView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            user = User.objects.filter(id=request.user.id).first()
            customer = Customers.objects.filter(user=user.pk).first()
            b = ((base64.b64decode(request.data['cus_img']
                                               [request.data['cus_img'].find(",") + 1:])))
            img = Image.open(io.BytesIO(b))
            filename = 'customer_image.jpeg'
            img_object = ImageFile(io.BytesIO(
                img.fp.getvalue()), name=filename)
            customer.cus_img = img_object
            customer.save()
            customer_serializer = CustomerSerializer(customer, context={'request':request})
            return Response({"message":"Image edited successfully.","data":customer_serializer.data}, status=status.HTTP_200_OK)


class CustomerCatalogueRequestView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    queryset = Customers.objects.all()
    serializer_class = CustomerSerializer

    def get(self, request, *args, **kwargs):
        try:
            customer = self.queryset.get(user=request.user.pk)
        except Customers.DoesNotExist:
            return Response({"status":False,"message": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        if customer.catalogue_req_status == 1:
            return Response({"status":False,"message": "You have already sent a request.Please Wait for Admin Approval."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CustomerSerializer(customer, data={"catalogue_req_status": 1}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "request sent successfully."}, status=status.HTTP_200_OK)
    

class CustomerNotificationsListView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def get(self, request, *args, **kwargs):
        customer_obj = Customers.objects.get(user=request.user.pk)
        notifications_query = CustomerNotifications.objects.filter(customers=customer_obj.pk)
        notifications_serializer = CustomerNotificationsSerializer(notifications_query, many=True)
        output = []
        for data in notifications_serializer.data:
            instance = {}
            notification_master = CustomerNotificationMaster.objects.filter(id=data['notification']).first()
            notification_master_serializer = CustomerNotificationMasterSerializer(notification_master, context={'request':request})
            instance.update({
                'notification_id':data['id'],
                'content': notification_master.content,
                'title': notification_master.title,
                'image' : notification_master_serializer.data['image'],
                'status' : 'Seen' if(data['status']==2) else 'Not yet seen'
            })
            if instance not in output:
                output.append(instance)
        return Response({"data": output}, status=status.HTTP_200_OK)
            
class CustomerNotificationsDetailView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def post(self, request, *args, **kwargs):
        customer_obj = Customers.objects.get(user=request.user.pk)
        notifications_query = CustomerNotifications.objects.filter(customers=customer_obj.pk, id=request.data['notification_id']).first()
        instance = {}
        if notifications_query:
            notification_master = CustomerNotificationMaster.objects.filter(id=notifications_query.notification.pk).first()
            notification_master_serializer = CustomerNotificationMasterSerializer(notification_master, context={'request':request})
            instance.update({
                'content': notification_master.content,
                'title': notification_master.title,
                'image' : notification_master_serializer.data['image'],
            })
            notifications_query.status = 2
            notifications_query.save()
            return Response({"message": "Notification seen successfully.", "data":instance}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Notification not found.", "data":{}}, status=status.HTTP_400_BAD_REQUEST)



class CustomerRejectView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]

    def get(self, request, *args, **kwargs):
        customer_obj = Customers.objects.get(user=request.user.pk)
        if customer_obj.approved_status == 3:
            return Response({"status":False,"message": "You have already rejected the request."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CustomerSerializer(customer_obj, data={"approved_status": 3}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Request rejected successfully."}, status=status.HTTP_200_OK)
    
class ActiveCatalogueVisibleCustomers(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]

    def get(self, request, *args, **kwargs):
        current_time = datetime.now()

        approved_customers = Customers.objects.filter(catalogue_req_status=2)

        lifetime_customers = approved_customers.filter(catalogue_visible_type=0)

        date_limited_customers = approved_customers.filter(
            catalogue_visible_type=1,
            show_catalogue_date__gte=current_time
        )

        final_customers = lifetime_customers.union(date_limited_customers)

        data = [
            {
                "id": customer.id_customer,
                "name": f"{customer.firstname} {customer.lastname}",
                "mobile": customer.mobile,
                "catalogue_visible_type": customer.catalogue_visible_type,
                "show_catalogue_date": customer.show_catalogue_date,
            }
            for customer in final_customers
        ]

        return Response({
            "status": True,
            "data": {
                "count":len(data),
                "list":data
            }
        }, status=status.HTTP_200_OK)

class CustomerEnquiryCreateView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def post(self, request, *args, **kwargs):
        customer_obj = Customers.objects.filter(user=request.user).first()
        request.data.update({
            "enquiry_date":date.today(),
            "customer":customer_obj.pk
        })
        serializer = CustomerEnquirySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message":"Details sent successfully", "data":serializer.data}, status=status.HTTP_201_CREATED)
    
class CustomerEnquiryListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        GENDER_OPTIONS = {
            1: "Male",
            2: "Female",
            3: "Transgender"
        }
        METAL_OPTIONS = {
            1: "Gold",
            2: "Silver",
        }
        STATUS_OPTIONS = {
            1: "Open",
            2: "Replied",
        }    
        queryset = CustomerEnquiry.objects.all()
        if('status' in request.data):
            queryset = queryset.filter(status=request.data['status'])
        serializer = CustomerEnquirySerializer(queryset, many=True)
        for data in serializer.data:
            cus_obj = Customers.objects.filter(id_customer=data['customer']).first()
            prod_obj = Product.objects.filter(pro_id=data['product']).first()
            design_obj = Design.objects.filter(id_design=data['design']).first()
            size_obj = Size.objects.filter(id_size=data['size']).first()
            weight_range_obj = WeightRange.objects.filter(id_weight_range=data['weight_range']).first()
            description = data.get('description', '')
            data.update({
                "gender_name":GENDER_OPTIONS.get(data['gender']),
                "status_name":STATUS_OPTIONS.get(data['status']),
                "customer_name":cus_obj.firstname,
                "colour":'warning' if(data['status']==1) else 'success',
                "mobile":cus_obj.mobile,
                "product_name":prod_obj.product_name,
                "design_name":design_obj.design_name,
                "size_name":size_obj.name,
                "metal":METAL_OPTIONS.get(data['metal']),
                # "weight_range": {f"{weight_range_obj.from_weight} to {weight_range_obj.to_weight}"},
                "weight_range": weight_range_obj.weight_range_name,
                "description":description,
                "can_reply":True if(data['status']==1) else False,
            })
        return Response({"data":serializer.data})