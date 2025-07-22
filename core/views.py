from datetime import datetime, timedelta
from random import randint
from django.conf import settings
from django.forms import model_to_dict
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from knox.models import AuthToken
import subprocess
from django.utils.module_loading import import_string
from rest_framework import generics, status
from django.db import IntegrityError
from django.utils import timezone
from django.db.models import Q, ProtectedError
from models_logging.models import Change
from django.utils.timezone import utc
from pathlib import Path

from django.http import Http404
from django.core.mail import send_mail
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet, InvalidToken
from django.template.loader import render_to_string
import dotenv
import os
from django.contrib.auth.hashers import make_password
from common.permissions import IsEmployee
from django.db import transaction
import re
from django.utils.timezone import localtime, now
from django.shortcuts import get_object_or_404
import json
# local imports
from common.permissions import isAdmin, isSuperuser
from accounts.models import User
from .serializers import (MenuSerializer, EmployeeSerializer, EmployeeSignInSerializer, ChangesLogAPISerializer, LoginDetailSerializer,ReportColumnsTemplatesSerializer)
from .models import (Employee, Menu, EmpMenuAccess, EmployeeOTP, CustomerOTP, LoginDetails,ReportColumnsTemplates)
from customers.models import (Customers)
from retailmasters.models import (Branch, Profile, RegisteredDevices, ErpService)
from retailmasters.serializers import (BranchSerializer, ErpServiceSerializer)
from schememaster.models import (Scheme)
from schemepayment.models import (Payment)

from utilities.pagination_mixin import PaginationMixin
from .constants import (MENU_COLUMN_LIST,MENU_ACTION_LIST)
from services.send_sms_message import send_customer_reg_sms


#
dotenv.load_dotenv()
#
fernet = Fernet(os.getenv('crypt_key'))
#
pagination = PaginationMixin()  # Apply pagination


# Check Token Valid:
class EmployeeCheckTokenAPI(generics.GenericAPIView):
    def post(self, request):
        # if request.user.erpemployee.email_verified == False:
        #     return Response({"success": False, "message": "Verify Email Address"})
        emp = (Employee.objects.get(user_id=request.user.pk))
        emp_profile = Profile.objects.get(id_profile=emp.id_profile.pk)
        # if(EmployeeOTP.objects.filter(employee=emp.pk, otp_for="3", expiry__gt=timezone.now()).exists()):
        #     return Response({"success": False, "message": "Verify OTP to login"})
        if emp_profile.device_wise_login:
            if 'deviceID' not in request.data:
                return Response({"error_detail": ["Device ID is required."]}, status=status.HTTP_400_BAD_REQUEST)
            try:
                registered_device = RegisteredDevices.objects.get(ref_no=request.data['deviceID'], is_active=True)
            except RegisteredDevices.DoesNotExist:
                request.auth.delete()
                return Response({"error_detail": ["Invalid or unregistered device"]}, status=status.HTTP_400_BAD_REQUEST)
            counter_name = registered_device.id_counter.name if registered_device.id_counter else None
        return Response({"success": True, "message": "User already logged in"})


class BackupCurrentDB(generics.GenericAPIView):
    permission_classes = [IsEmployee]  # replace with IsEmployee if needed

    def get(self, request, *args, **kwargs):
        timestamp = localtime(now()).strftime("%Y-%m-%d_%H-%M-%S")
        
        # Load Django settings
        settings_module = os.getenv('DJANGO_SETTINGS_MODULE', 'jewelry_retail_api.settings.development')
        settings = import_string(settings_module)

        # Database credentials
        db_config = settings.DATABASES.get('default', {})
        db_name = db_config.get('NAME', '')
        db_user = db_config.get('USER', '')
        db_password = db_config.get('PASSWORD', '')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '3306')

        if not db_name or not db_user:
            return Response({"error": "Database configuration is missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Set the USB drive path (Windows: example E:\db_backups)
        usb_drive_path = r"F:\db_backups"  # Change this to your USB drive path
        if not os.path.exists(usb_drive_path):
            return Response({"error": "USB drive not found at E:\\db_backups"}, status=status.HTTP_400_BAD_REQUEST)

        os.makedirs(usb_drive_path, exist_ok=True)

        # Set filename and full path
        sql_filename = f"{timestamp}_backup.sql"
        sql_file_path = os.path.join(usb_drive_path, sql_filename)

        # Full path to mysqldump (change if different on your system)
        mysqldump_path = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
        if not os.path.exists(mysqldump_path):
            return Response({"error": "mysqldump not found. Please check the path."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Build the dump command
        dump_command = [
            mysqldump_path, "--single-transaction", "--quick", "--verbose",
            "-u", db_user, "-h", db_host, "-P", str(db_port), db_name
        ]

        # Set password via environment variable
        env = os.environ.copy()
        env["MYSQL_PWD"] = db_password

        try:
            with open(sql_file_path, 'w', encoding='utf-8') as output_file:
                process = subprocess.Popen(dump_command, stdout=output_file, stderr=subprocess.PIPE, text=True, env=env)
                for line in process.stderr:
                    print(f" Dump Error: {line.strip()}")
                process.wait(timeout=120)

            if process.returncode == 0:
                return Response({
                    "message": "Database backup successful",
                    "saved_to": sql_file_path
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Database export failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except subprocess.TimeoutExpired:
            return Response({"error": "Database export timed out"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": "Failed to export database", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComposeMessage(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def post(self, request, *args, **kwargs):
        cus_id = request.data['cus_id']
        service_id = request.data['service_id']
        customer = Customers.objects.filter(id_customer=cus_id).get()
        service = ErpService.objects.filter(id_service = service_id).get()
        branch = Branch.objects.filter(id_branch = customer.id_branch).get()
        
        replacements = {
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
        }
        
        if(service_id == 1):
            OTP_code = randint(100000, 999999)
            expiry_time = timezone.now() + timedelta(minutes=5)
            replacements = {
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            "otp": OTP_code,
            "validate_sec": (expiry_time - timezone.now()).seconds,
            }
            if (CustomerOTP.objects.filter(customer=customer.pk, otp_for=2, expiry__gt=timezone.now()).exists()):
                return Response({"error_detail": ["A valid reset OTP already exists. Please use it / wait till its expire"]}, status=status.HTTP_400_BAD_REQUEST)
            # CustomerOTP.objects.create(customer=customer, otp_for=0, email_id=user.email,
            #                         otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
            content = service.content
            # Use regex to find and replace placeholders
            def replace_placeholder(match):
                key = match.group(1)
                return str(replacements.get(key, f"@@{key}@@"))

            updated_content = re.sub(r"@@(.*?)@@", replace_placeholder, content)
            print(updated_content)
            return Response(status=status.HTTP_200_OK)
        
        if(service_id == 2):
            replacements = {
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            "company_name":branch.id_company.company_name
            }
            content = service.content
            # Use regex to find and replace placeholders
            def replace_placeholder(match):
                key = match.group(1)
                return str(replacements.get(key, f"@@{key}@@"))

            updated_content = re.sub(r"@@(.*?)@@", replace_placeholder, content)
            print(updated_content)
            return Response(status=status.HTTP_200_OK)
        
        if(service_id == 3):
            scheme_id = request.data['scheme_id']
            scheme = Scheme.objects.filter(scheme_id=scheme_id).get()
            replacements = {
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            "scheme_name":scheme.scheme_name
            }
            content = service.content
            # Use regex to find and replace placeholders
            def replace_placeholder(match):
                key = match.group(1)
                return str(replacements.get(key, f"@@{key}@@"))

            updated_content = re.sub(r"@@(.*?)@@", replace_placeholder, content)
            print(updated_content)
            return Response(status=status.HTTP_200_OK)
        
        if(service_id == 4):
            payment_id = request.data['payment_id']
            payment = Payment.objects.filter(id_payment = payment_id).get()
            replacements = {
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            "scheme_name":payment.id_scheme.scheme_name,
            "payment_amount":payment.payment_amount,
            "receipt_no":payment.receipt_no,
            "company_name":branch.id_company.company_name
            }
            content = service.content
            # Use regex to find and replace placeholders
            def replace_placeholder(match):
                key = match.group(1)
                return str(replacements.get(key, f"@@{key}@@"))

            updated_content = re.sub(r"@@(.*?)@@", replace_placeholder, content)
            print(updated_content)
            return Response(status=status.HTTP_200_OK)
        
class BranchDropdownView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def post(self, request, *args, **kwargs):
        output = []
        print(request.data)
        for data in request.data['login_branches']:
            branch = Branch.objects.filter(id_branch=data).get()
            branch_serializer = BranchSerializer(branch)
            if branch_serializer.data not in output:
                output.append(branch_serializer.data)
        return Response(output, status=status.HTTP_200_OK)

# List create api for  AdminMenus in Admin panel


class MenuList(PaginationMixin,generics.ListCreateAPIView):
    permission_classes = [isAdmin]
    serializer_class = MenuSerializer
    queryset = Menu.objects.all()

    def get(self, request, *args, **kwargs):
        if 'options' in request.query_params:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            output = []
            output.append({"value": 0, "label": "Home"})
            for data in serializer.data:
                # if (data['sub'] == True):
                if (data['parent'] == None or '#' in data['link']):
                    instance = {}
                    instance.update(
                        {"value": data['id'], "label": data['text']})
                    if instance not in output:
                        output.append(instance)
            
            return Response(output, status=status.HTTP_200_OK)
        
        if 'search' in request.query_params:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            output = []
            for data in serializer.data:
                data.update({"submenus": 0})
                if data['parent'] == None or data['parent'] == data['id']:
                    data.update({"parent_page": "Home"})
                else:
                    try:
                        parent_page = Menu.objects.get(id=data['parent']).text
                        data.update({"parent_page": parent_page})
                    except Menu.DoesNotExist:
                        data.update({"parent_page": None})
                for each in serializer.data:
                    # print(each != data)
                    if (each != data):
                        # print(each['parent']==data["id"])
                        if (each['parent'] == data["id"]):
                            data['submenus'] += 1
                # data.pop("ownership")
                # data.pop("icon")
                instance = {}
                instance.update({"id":data['id'], "name":data['text'], "url":data['link'],
                                 "icon":data['icon'], "section":data['parent_page']})
                if instance not in output:
                    output.append(instance)
            return Response(
                sorted(output, key=lambda k: k['id'], reverse=True))
            
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request,None,MENU_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for data in serializer.data:
            if 'active' in data:
                data['is_active'] = data.pop('active')
            # data.update({"submenus": 0})
            if data['parent'] == None or data['parent'] == data['id']:
                data.update({"parent_page": "Home"})
            else:
                try:
                    parent_page = Menu.objects.get(id=data['parent']).text
                    data.update({"parent_page": parent_page})
                except Menu.DoesNotExist:
                    data.update({"parent_page": None})
            # for each in serializer.data:
            #     # print(each != data)
            #     if (each != data):
            #         # print(each['parent']==data["id"])
            #         if (each['parent'] == data["id"]):
            #             data['submenus'] += 1
            # data.pop("ownership")
            data.pop("icon")
        menu_data = sorted(serializer.data, key=lambda k: k['id'], reverse=True)
        menu_details = []
        for index,menu in enumerate(menu_data):
            menu_object = {}
            menu_object.update({"pk_id":menu['id'],"sno":index+1})
            menu_object.update(menu)
            if menu_object not in menu_details:
                menu_details.append(menu_object)
        context={'columns':MENU_COLUMN_LIST,'actions':MENU_ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number}
        return pagination.paginated_response(menu_details,context)

    def post(self, request, *args, **kwargs):
        menu_links = [each.link for each in Menu.objects.all()]
        if 'link' in request.data:
            if '#' in request.data['link']:
                request.data.update({"sub":True})
            elif '*' in request.data['link']:
                request.data.update({"sub":True})
            else:
                request.data.update({"sub":False})  
            if request.data['link'] != '#' or request.data['link'] != '*':
                if (len(request.data['link']) > 1):
                    request.data['link'] = request.data['link'].rstrip("/")
                if request.data['link'] in menu_links:
                    return Response(
                        {"error_detail": [
                            'Menu with this link already exist']},
                        status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # for each in Employee.objects.all():
        #     EmpMenuAccess.objects.create(
        #         emp=each, menu_id=serializer.data['id'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, format=None):
        obj = self.get_object()
        try:
            obj.delete()
        except ProtectedError:
            return Response({"error_detail": ["Menu can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


# RetrieveUpdateDestroy  api for  AdminMenu entries in Admin panel
class MenuDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [isAdmin]
    serializer_class = MenuSerializer
    queryset = Menu.objects.all()

    def get(self, request, *args, **kwargs):
        admin_menu = self.get_object()
        serializer = self.get_serializer(admin_menu)
        instance = serializer.data
        if instance['parent'] != None:
            menu_id = admin_menu.parent.id
            menu_name = admin_menu.parent.text
            # print("menu_id", menu_id, "menu_name", menu_name)
            instance.update(
                {'parent':  menu_id})
        else:
            instance.update({'parent': 0})

        return Response(instance)

    def put(self, request, *args, **kwargs):
        menu_links = [
            each.link for each in Menu.objects.filter(~Q(
                id=kwargs['pk']))
        ]
        if 'link' in request.data:
            if request.data['link'] != '#':
                if (len(request.data['link']) > 1):
                    request.data['link'] = request.data['link'].rstrip(
                        "/")
                    if request.data['link'] in menu_links:
                        return Response(
                            {"error_detail": [
                                "Menu with this link already exist"]},
                            status=status.HTTP_400_BAD_REQUEST)
            if '#' in request.data['link']:
                request.data.update({"sub":True})
            elif '*' in request.data['link']:
                request.data.update({"sub":True})
            else:
                request.data.update({"sub":False})
        admin_menu = self.get_object()
        serializer = self.get_serializer(admin_menu, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class MenuFetch(generics.GenericAPIView):
    permission_classes = [isAdmin]
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(active=True)
        if 'options' in request.query_params:
            menu_access = queryset.values()
            # Sort Order by a combo of Order and Primary
            # sortbyorder = sorted(menu_access,
            #                      key=lambda k:
            #                      (k['order'], k['id']))
            new_order = []
            # To get the count of sub menus of parent
            for each in menu_access:
                each.update({"submenus": 0, "view": 0,
                            "add": 0, "edit": 0, "delete": 0})
                # delete unused properties
                del each['link']
                del each['icon']
                del each['active']
                del each['title']
                del each['order']
                new_order.append(each)

            #     # print('Pk', each['id'])
            #     for each1 in sortbyorder:
            #         if (each1 != each):
            #             # print('Parent', each1['parent_id'])
            #             if (each1['parent_id'] == each["id"]):
            #                 each['submenus'] += 1
            #     # Create a new list with parent menu then its child menu  in order
            
            # for each in sortbyorder:
            #     #  if no child and {condition checked whether parent is Root / home  or Parent is item itself} add the item to list
            #     if (each['submenus'] == 0) and (each['parent_id'] == None or each['parent_id'] == each['id']):
            #         # if each not in new_order:
            #         new_order.append(each)
            #         continue
            #     # if the Item  has children Menu items
            #     if (each['submenus'] > 0):
            #         # first add the item to new list
            #         new_order.append(each)
            #         # Search the children of the item by looping again
            #         for submen in sortbyorder:
            #             if each['id'] == submen['parent_id']:
            #                 # append the child to the new list
            #                 new_order.append(submen)
            return Response({"menu_access": new_order, "dasboard_access": []}, status=status.HTTP_200_OK)
        try:
            admin = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(queryset, many=True)
        admin_menu_data = serializer.data
        sub_menu_data = []
        for data in serializer.data:
            # Filter Out Menu If the user does not have view permission/ is not superuser
            try:
                emp = Employee.objects.get(id_employee=request.user.employee.pk)
                admin_menu_access = EmpMenuAccess.objects.get(
                    menu_id=data['id'], profile = emp.id_profile.pk)

                if (admin_menu_access.view or request.user.is_superuser) == False:
                    admin_menu_data.remove(data)
                    continue
            except EmpMenuAccess.DoesNotExist:
                admin_menu_data.remove(data)
                continue

            # if parent is assigned and not self parent -> create a sub menu list; and sub menu item is removed from the main menu list
            if data['parent'] != None and data['parent'] != data['id']:
                admin_menu_data.remove(data)
                sub_menu_data.append(data)
        # Sub menu are appended to their corresponding Parents:
        for menu in (serializer.data):
            if menu['parent'] == None or menu['parent'] == menu['id']:
                menu.update({"subMenu": []})
                for each in sub_menu_data:
                    if each['sub'] == True:
                        each.update({"subMenu": []})
                        for eac in sub_menu_data:
                            if (each['id'] == eac['parent']):
                                each['subMenu'].append(eac)
                # if submenu empty : remove it from the menu item
                        if (each['subMenu'] == []):
                            each.pop("subMenu")
                        else:
                            each['subMenu'] = sorted(each['subMenu'],
                                             key=lambda k:
                                             (k['order'], k['id']))
                    
                    if (menu['id'] == each['parent']):
                        menu['subMenu'].append(each)
                # if submenu empty : remove it from the menu item
                if (len(menu['subMenu'])==0):
                    admin_menu_data = [m for m in admin_menu_data if m['id'] != menu['id']]
                    # admin_menu_data.remove(menu)
                    #serializer.data.remove(menu)
                    # menu.pop("subMenu")
                else:
                    menu['subMenu'] = sorted(menu['subMenu'],
                                             key=lambda k:
                                             (k['order'], k['id']))
        return Response(sorted(admin_menu_data, key=lambda k: (k['order'], k['id'])))


# Admin List/Create API
class AdminCRUDAPI(generics.GenericAPIView):
    permission_classes = [isSuperuser]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()

    def get(self, request, *args, **kwargs):
        if ('pk' in kwargs):
            admin = (self.get_object())
            # hide Super User admin
            if (admin.user.is_superuser):
                raise Http404
            accessdata = []
            for each in (EmpMenuAccess.objects.filter(
                    admin=admin)):
                menu_item = {}
                menu_item.update({'id': each.menu.pk,
                                  'text': each.menu.text,
                                  "order": each.menu.order,
                                  'parent_id': each.menu.parent.pk if each.menu.parent != None else None,
                                  'view': each.view,
                                  "add": each.add,
                                  "edit": each.edit,
                                  "delete": each.delete})
                accessdata.append(menu_item)
            sortbyorder = sorted(accessdata,
                                 key=lambda k:
                                 (k['order'], k['id']))
            # To get the count of sub menus of parent
            for each in sortbyorder:
                each.update({"submenus": 0})
                for each1 in sortbyorder:
                    if (each1 != each):
                        # print('Parent', each1['parent_id'])
                        if (each1['parent_id'] == each["id"]):
                            each['submenus'] += 1
                # Create a new list with parent menu then its child menu  in order
            new_order = []
            for each in sortbyorder:
                #  if no child and {condition checked whether parent is Root / home  or Parent is item itself} add the item to list
                if (each['submenus']
                        == 0) and (each['parent_id'] == None
                                   or each['parent_id'] == each['id']):
                    # if each not in new_order:
                    new_order.append(each)
                    continue
                # if the Item  has children Menu items
                if (each['submenus'] > 0):
                    # first add the item to new list
                    new_order.append(each)
                    # Search the children of the item by looping again
                    for submen in sortbyorder:
                        if each['id'] == submen['parent_id']:
                            # append the child to the new list
                            new_order.append(submen)
            output = {"employee": {"name": admin.firstname, "username": admin.user.username,
                                "email": admin.user.email, "is_active": admin.user.is_active, "firstname": admin.user.first_name, "lastname": admin.user.last_name},
                      "accessdata": new_order}
            return Response(output)
        output = []
        # Non Super User Admins
        queryset = self.get_queryset().filter(user__is_superuser=0)
        for each in queryset:
            admin = {"adminid": each.id_employee, "name": each.firstname,
                     "username": each.user.username, "email": each.user.email, "is_active": each.user.is_active}
            if admin not in output:
                output.append(admin)

        return Response(output, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if ('pk' in kwargs):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # > CREATE ADMIN
        admin_name = request.data['admin'].pop('name')
        password = request.data['admin'].pop('password')
        # create a user
        request.data['admin'].update({'is_adminuser': True})
        try:
            user = User.objects.create(**request.data['admin'])
            user.set_password(password)
            user.save()
            # create admin using user
            emp = Employee.objects.create(firstname=admin_name, user=user)
            # create Admin menu access for created Admin
            for each in request.data['accessdata']:
                each.update({"emp": emp})
                EmpMenuAccess.objects.create(**each)
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

    def put(self, request, *args, **kwargs):
        if ('pk' in kwargs):
            admin = self.get_object()
            # super user Admin is not editable
            if (admin.user.is_superuser):
                return Response({"error_detail": ["You are not allowed to perform this action"]}, status=status.HTTP_403_FORBIDDEN)
            admin.firstname = request.data['admin']['name']
            user = admin.user
            try:
                user.username = request.data['admin']['username']
                # If a new mail ID is used set email verified status as False
                if user.email != request.data['admin']['email']:
                    user.email = request.data['admin']['email']
                    admin.email_verified = False
                    user.is_active = True
                # user.is_active = request.data['admin']['is_active']
                if (request.data['admin']['changepass']):
                    user.set_password(request.data['admin']['password'])
                user.save()
            except IntegrityError as e:
                if "Invalid username" in str(e):
                    return Response({"error_detail": ["Invalid username"]}, status=status.HTTP_400_BAD_REQUEST)
                if ("users.username" in str(e)):
                    return Response({"error_detail": ['Username already in use.']}, status=status.HTTP_400_BAD_REQUEST)
                if ("users.email" in str(e)):
                    return Response({"error_detail": ['Email already allocated for another user']}, status=status.HTTP_400_BAD_REQUEST)
            admin.save()
            for access in request.data['accessdata']:
                EmpMenuAccess.objects.filter(
                    menu_id=access['id'],
                    emp=admin.pk).update(
                    view=access['view'],
                    add=access['add'],
                    edit=access['edit'],
                    delete=access['delete'])

            # delete tokens of edited user:
            AuthToken.objects.filter(user=user).delete()
            return Response({"success": True,
                             "message": "Admin user updated successfully"}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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

class GetProfileMenuAccess(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, *args, **kwargs):
        profile_id = request.data['profileID']
        if not profile_id:
            return Response({"error": "profileID is required"}, status=status.HTTP_400_BAD_REQUEST)

        emp_menu_access = EmpMenuAccess.objects.filter(profile_id=profile_id)
        if not emp_menu_access.exists():
            return Response({"expanded": [], "checked": []}, status=status.HTTP_200_OK)

        expanded_set = set()
        checked_set = set()
        permission_checked = []
        for access in emp_menu_access:
            menu = access.menu
            if access.view:
                permission_checked.append(f"{menu.id}_view")
            if access.add:
                permission_checked.append(f"{menu.id}_add")
            if access.edit:
                permission_checked.append(f"{menu.id}_edit")
            if access.delete:
                permission_checked.append(f"{menu.id}_delete")
            if access.print:
                permission_checked.append(f"{menu.id}_print")
            if access.export:
                permission_checked.append(f"{menu.id}_export")
            if any([access.view, access.add, access.edit, access.delete]):
                checked_set.add(menu.id)
            current_menu = menu
            while current_menu.parent:
                expanded_set.add(current_menu.parent.id)
                current_menu = current_menu.parent
        expanded = list(expanded_set)
        checked = list(checked_set)
        return Response({"expanded": expanded, "checked": checked + permission_checked}, status=status.HTTP_200_OK)

class ProfileMenuAccess(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, *args, **kwargs):
        if len(request.data['combinedMenuIds']) == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        combined_menu_ids = request.data['combinedMenuIds']
        vertical_icon_tab = request.data['selectedProfile']
        
        # Step 1: Extract base menu ids and their corresponding permissions from combinedMenuIds
        menu_permissions = {}
        for item in combined_menu_ids:
            parts = item.split('_')
            menu_id = int(parts[0])
            if menu_id not in menu_permissions:
                menu_permissions[menu_id] = {
                    'add': False, 'edit': False, 'view': False, 
                    'delete': False, 'print': False, 'export': False
                }
            if len(parts) > 1:
                permission = parts[1]
                menu_permissions[menu_id][permission] = True

        # Step 2: Add parent menus and set their permissions to True (full access)
        all_menu_ids = set(menu_permissions.keys())
        for menu_id in list(menu_permissions.keys()):
            current_menu = Menu.objects.get(id=int(menu_id))
            if current_menu.parent_id is None:
                menu_permissions[menu_id] = {
                        'add': True, 'edit': True, 'view': True,
                        'delete': True, 'print': True, 'export': True
                    }
            while current_menu.parent_id is not None:
                parent_id = current_menu.parent_id
                if parent_id not in menu_permissions:
                    menu_permissions[parent_id] = {
                        'add': True, 'edit': True, 'view': True,
                        'delete': True, 'print': True, 'export': True
                    }
                else:
                    for key in ['add', 'edit', 'view', 'delete', 'print', 'export']:
                        menu_permissions[parent_id][key] = True

                all_menu_ids.add(parent_id)
                current_menu = Menu.objects.get(id=parent_id)
        with transaction.atomic():
            if EmpMenuAccess.objects.filter(profile=vertical_icon_tab).exists():
                EmpMenuAccess.objects.filter(profile=vertical_icon_tab).delete()
            for menu_id, permissions in menu_permissions.items():
                profile = Profile.objects.get(id_profile=vertical_icon_tab)
                menu = Menu.objects.get(id=menu_id)
                EmpMenuAccess.objects.create(
                    menu=menu, profile=profile, 
                    add=permissions['add'], view=permissions['view'], 
                    edit=permissions['edit'], delete=permissions['delete'],
                    print=permissions['print'], export=permissions['export']
                )
        return Response({"message": "Access created successfully"}, status=status.HTTP_201_CREATED)

def get_ordered_menus_with_permissions():
        def add_permissions(menu):
            return {
                "id": menu.id,
                "text": menu.text,
                "link": menu.link,
                "icon": menu.icon,
                "title": menu.title,
                "order": menu.order,
                "parent_id": menu.parent_id,
                "add": False,
                "edit": False,
                "delete": False,
                "view": False,
                "print": False,
                "export": False,
                "is_parent_menu": Menu.objects.filter(parent=menu, active=True).exists()
            }
    
        def build_menu_tree(menu, result):
            children = Menu.objects.filter(parent=menu, active=True).order_by("order")
            for child in children:
                result.append(add_permissions(child))
                build_menu_tree(child, result)
    
        result = []
        root_menus = Menu.objects.filter(parent__isnull=True, active=True).order_by("order")
    
        for menu in root_menus:
            result.append(add_permissions(menu))
            build_menu_tree(menu, result)
    
        return result
    

def get_access_menus_with_permissions(profile_id):
    access_map = {
        access.menu_id: {
            "add": access.add,
            "edit": access.edit,
            "delete": access.delete,
            "view": access.view,
            "print": access.print,
            "export": access.export
        }
        for access in EmpMenuAccess.objects.filter(profile_id=profile_id)
    }

    def add_permissions(menu):
        access = access_map.get(menu.id, {})
        return {
            "id": menu.id,
            "text": menu.text,
            "link": menu.link,
            "icon": menu.icon,
            "title": menu.title,
            "order": menu.order,
            "parent_id": menu.parent_id,
            "add": access.get("add", False),
            "edit": access.get("edit", False),
            "delete": access.get("delete", False),
            "view": access.get("view", False),
            "print": access.get("print", False),
            "export": access.get("export", False),
            "is_parent_menu": Menu.objects.filter(parent=menu, active=True).exists()
        }

    def build_menu_tree(menu, result):
        children = Menu.objects.filter(parent=menu, active=True).order_by("order")
        for child in children:
            result.append(add_permissions(child))
            build_menu_tree(child, result)

    result = []
    root_menus = Menu.objects.filter(parent__isnull=True, active=True).order_by("order")

    for menu in root_menus:
        result.append(add_permissions(menu))
        build_menu_tree(menu, result)

    return result

class ProfileMenuAccessOptionsForCheckboxForm(generics.GenericAPIView):
    permission_classes = [isAdmin]
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    
    def get(self, request, *args, **kwargs):
        menu_list = get_ordered_menus_with_permissions()
        return Response(menu_list, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        if(Profile.objects.filter(id_profile=request.data['profile']).exists()):
            profile = Profile.objects.get(id_profile=request.data['profile'])
            # if EmpMenuAccess.objects.filter(profile=request.data['profile']).exists():
            #     EmpMenuAccess.objects.filter(profile=request.data['profile']).delete()
            for access in request.data['accessData']:
                if EmpMenuAccess.objects.filter(profile=request.data['profile'], menu=access['id']).exists():
                    EmpMenuAccess.objects.filter(
                        menu=access['id'],
                        profile=profile.pk).update(
                        view=access['view'],
                        add=access['add'],
                        edit=access['edit'],
                        delete=access['delete'],
                        print=access['print'],
                        export=access['export'],
                        )
                else:
                    menu = Menu.objects.get(id=access['id'])
                    EmpMenuAccess.objects.create(
                        menu=menu, profile=profile, 
                        add=access['add'], view=access['view'], 
                        edit=access['edit'], delete=access['delete'],
                        print=access['print'], export=access['export']
                    ) 
            return Response({"message": "Access created successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message':'Invalid profile ID'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileMenuAccessForCheckboxForm(generics.GenericAPIView):
    permission_classes = [isAdmin]
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    
    def post(self, request, *args, **kwargs):
        menu_list = get_access_menus_with_permissions(request.data['profileID'])
        return Response(menu_list, status=status.HTTP_200_OK)


# Admin Menu List/Create API
class EmployeeMenuFetch(generics.GenericAPIView):
    permission_classes = [isAdmin]
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(active=True)
        # if 'options' in request.query_params:
        #     # Get menu access values and sort them by 'order' and 'id'
        #     menu_access = queryset.values()
        #     sortbyorder = sorted(menu_access, key=lambda k: (k['order'], k['id']))
    
        #     # Update each menu access with default permissions and clean up unnecessary fields
        #     for each in sortbyorder:
        #         each.update({
        #             "view": 0, 
        #             "add": 0, 
        #             "edit": 0, 
        #             "delete": 0,
        #             "print": 0,
        #             "export": 0
        #         })
        #         del each['link']
        #         del each['icon']
        #         del each['active']
        #         del each['title']
        #         del each['order']
    
        #     # Initialize an empty dictionary to hold the hierarchical menu structure
        #     menu_dict = {}
    
        #     # First pass: Add parent-level items
        #     for each in sortbyorder:
        #         if each['parent_id'] is None:
        #             menu_dict[each['id']] = {
        #                 "value": each['id'],
        #                 "label": each['text']
        #             }
    
        #     # Second pass: Add child items to their respective parents
        #     for each in sortbyorder:
        #         if each['parent_id'] is not None:
        #             parent_id = each['parent_id']
        #             if parent_id in menu_dict:
        #                 # Add permissions as children of each menu item
        #                 children = [
        #                     {"value": f"{each['id']}_add", "label": "ADD"},
        #                     {"value": f"{each['id']}_edit", "label": "EDIT"},
        #                     {"value": f"{each['id']}_view", "label": "VIEW"},
        #                     {"value": f"{each['id']}_delete", "label": "DELETE"},
        #                     {"value": f"{each['id']}_print", "label": "PRINT"},
        #                     {"value": f"{each['id']}_export", "label": "EXPORT"}
        #                 ]
                        
        #                 # If the parent already has children, add more; if not, initialize the children array
        #                 if "children" not in menu_dict[parent_id]:
        #                     menu_dict[parent_id]["children"] = []
        #                 menu_dict[parent_id]["children"].append({
        #                     "value": each['id'],
        #                     "label": each['text'],
        #                     "children": children
        #                 })
    
        #     # Remove empty children arrays from parent items that do not have submenus
        #     for each in menu_dict.values():
        #         if "children" in each and len(each["children"]) == 0:
        #             del each["children"]
    
        #     # Convert the dictionary to a list of values, as required by the output structure
        #     new_order = list(menu_dict.values())
    
        #     # Return the response with the hierarchical structure
        #     return Response({"menu_access": new_order, "dashboard_access": []}, status=status.HTTP_200_OK)
        if 'options' in request.query_params:
            serializer = self.get_serializer(queryset, many=True)
            admin_menu_data = serializer.data
            sub_menu_data = []

            for data in serializer.data:
                if data['parent'] is not None and data['parent'] != data['id']:
                    admin_menu_data.remove(data)
                    sub_menu_data.append(data)

            def format_menu_item(item):
                formatted_item = {
                    "value": item['id'],
                    "label": item['text'],
                }
                if item.get('children'): 
                    formatted_item["children"] = item['children']
                return formatted_item

            def safe_int(value, default=0):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            permissions_template = [
                {"value": "_add", "label": "ADD"},
                {"value": "_edit", "label": "EDIT"},
                {"value": "_view", "label": "VIEW"},
                {"value": "_delete", "label": "DELETE"},
                {"value": "_print", "label": "PRINT"},
                {"value": "_export", "label": "EXPORT"},
            ]

            for menu in admin_menu_data:
                if menu['parent'] is None or menu['parent'] == menu['id']:
                    menu['children'] = []
                    for each in sub_menu_data:
                        each['value'] = each['id']
                        each['label'] = each['text']

                        if each['sub']:
                            each['children'] = []
                            for eac in sub_menu_data:
                                if each['id'] == eac['parent']:
                                    eac['children'] = [
                                        {"value": f"{eac['id']}{perm['value']}", "label": perm['label']}
                                        for perm in permissions_template
                                    ]
                                    each['children'].append(format_menu_item(eac))

                            if not each['children']:
                                each.pop('children', None)
                            else:
                                each['children'] = each['children']

                        if 'children' not in each or not each['children']:
                            each['children'] = [
                                {"value": f"{each['id']}{perm['value']}", "label": perm['label']}
                                for perm in permissions_template
                            ]

                        if menu['id'] == each['parent']:
                            menu['children'].append(format_menu_item(each))

                    if not menu['children']:
                        menu.pop('children', None)
                    else:
                        menu['children'] = sorted(
                            menu['children'], key=lambda k: (safe_int(k.get('order')), k['value'])
                        )

                menu['value'] = menu['id']
                menu['label'] = menu['text']
            formatted_menu_data = [format_menu_item(menu) for menu in admin_menu_data]
            sorted_menu_data = sorted(formatted_menu_data, key=lambda k: (safe_int(k.get('order')), k['value']))
            return Response(sorted_menu_data, status=status.HTTP_200_OK)
        try:
            admin = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(queryset, many=True)
        admin_menu_data = serializer.data
        sub_menu_data = []
        for data in serializer.data:
            # Filter Out Menu If the user does not have view permission/ is not superuser
            try:
                admin_menu_access = EmpMenuAccess.objects.get(
                    menu_id=data['id'], admin=admin)

                if (admin_menu_access.view or request.user.is_superuser) == False:
                    admin_menu_data.remove(data)
                    continue
            except EmpMenuAccess.DoesNotExist:
                admin_menu_data.remove(data)
                continue

            # if parent is assigned and not self parent -> create a sub menu list; and sub menu item is removed from the main menu list
            if data['parent'] != None and data['parent'] != data['id']:
                admin_menu_data.remove(data)
                sub_menu_data.append(data)
        # Sub menu are appended to their corresponding Parents:
        for menu in (serializer.data):
            if menu['parent'] == None or menu['parent'] == menu['id']:
                menu.update({"subMenu": []})
                for each in sub_menu_data:
                    if each['sub'] == True:
                        each.update({"subMenu": []})
                        for eac in sub_menu_data:
                            if (each['id'] == eac['parent']):
                                each['subMenu'].append(eac)
                # if submenu empty : remove it from the menu item
                        if (each['subMenu'] == []):
                            each.pop("subMenu")
                        else:
                            each['subMenu'] = sorted(each['subMenu'],
                                             key=lambda k:
                                             (k['order'], k['id']))
                    
                    
                    
                    if (menu['id'] == each['parent']):
                        menu['subMenu'].append(each)
                # if submenu empty : remove it from the menu item
                if (menu['subMenu'] == []):
                    menu.pop("subMenu")
                else:

                    menu['subMenu'] = sorted(menu['subMenu'],
                                             key=lambda k:
                                             (k['order'], k['id']))

        return Response(sorted(admin_menu_data, key=lambda k: (k['order'], k['id'])), 
                        status=status.HTTP_200_OK)


# check Access
class CheckAcess(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, format=None):
        try:
            emp = Employee.objects.filter(user = request.user).get()
            menu_access = EmpMenuAccess.objects.get(
                profile=emp.id_profile.pk, menu__link=request.data['path'])
            title = Menu.objects.get(link=request.data['path']).title
            out = model_to_dict(menu_access)
            out.update(
                {"title": title, "is_superuser": False})
            # if super user.. give all permission irrespective of permissions set
            if request.user.is_superuser:
                out.update(
                    {"is_superuser": True, "view": True,
                     "add": True,
                     "edit": True,
                     "delete": True})
            return Response(out, status=status.HTTP_201_CREATED)
        except EmpMenuAccess.DoesNotExist:
            # if access not set / menu not created  / admin created manually in db ...
            # if super user.. give all permission
            if request.user.is_superuser:
                out = {
                    "is_superuser": True,
                    "view": True,
                    "add": True,
                    "edit": True,
                    "delete": True
                }
                return Response(out)
            # if not super user.. reject all permission
            out = {
                "is_superuser": False,
                "view": False,
                "add": False,
                "edit": False,
                "delete": False
            }
            return Response(out, status=status.HTTP_201_CREATED)


# Logs List API
class ChangesLogAPI(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def get(self, request, format=None):
        queryset = Change.objects.all()
        format = '%Y-%m-%d %H:%M:%S.%f'
        if 'from' in request.query_params and 'to' in request.query_params and 'offset' in request.query_params:
            if request.query_params['from'] != None and request.query_params[
                    'from'] != 'null' and request.query_params[
                        'to'] != None and request.query_params['to'] != 'null' and request.query_params[
                        'offset'] != None and request.query_params['offset'] != 'null':
                offset = (request.query_params['offset'])
                offset_hrs = int(offset.lstrip(
                    '-'))//60
                offset_mins = int(offset.lstrip(
                    '-')) % 60
                #
                from_date = (datetime.strptime(
                    request.query_params['from'] + ' 0:0:0.0',
                    format)).replace(tzinfo=utc) + timedelta(hours=offset_hrs, minutes=offset_mins) if '-' in offset else (datetime.strptime(
                        request.query_params['from'] + ' 0:0:0.0',
                        format)).replace(tzinfo=utc) - timedelta(hours=offset_hrs, minutes=offset_mins)
                #
                to_date = (datetime.strptime(
                    request.query_params['to'] + ' 23:59:59.999999',
                    format)).replace(tzinfo=utc) + timedelta(hours=offset_hrs, minutes=offset_mins) if '-' in offset else (datetime.strptime(
                        request.query_params['to'] + ' 23:59:59.999999',
                        format)).replace(tzinfo=utc) - timedelta(hours=offset_hrs, minutes=offset_mins)
                #
                queryset = queryset.filter(date_created__lte=to_date,
                                           date_created__gte=from_date)
        serializer = ChangesLogAPISerializer(queryset, many=True)

        return Response(sorted(serializer.data, key=lambda i: i['id']),
                        status=status.HTTP_200_OK)


class EditAdmin(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, *args, **kwargs):
        user = (request.user)
        data = request.data.copy()
        if 'edit_profile' in request.query_params:
            user.admin.name = request.data['name']
            user.admin.save()
            return Response({"success": True, "message": "Profile Updated"}, status=status.HTTP_200_OK)


# class loginsessionView(generics.GenericAPIView):
#     permission_classes = [AllowAny]

#     def post(self, request, *args, **kwargs):
#         def get_ip_address(request):
#             user_ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
#             if user_ip_address:
#                 ip = user_ip_address.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#             return ip
#         user_ip = get_ip_address(request)
#         print(user_ip)
#         print(request.user)
#     # Let's assume that the visitor uses an iPhone...
#         print(request.user_agent.is_mobile)  # returns True
#         print(request.user_agent.is_tablet)  # returns False
#         print(request.user_agent.is_touch_capable)  # returns True
#         print(request.user_agent.is_pc)  # returns False
#         print(request.user_agent.is_bot)  # returns False

#     # Accessing user agent's browser attributes
#         # returns Browser(family=u'Mobile Safari', version=(5, 1), version_string='5.1')
#         print(request.user_agent.browser)
#         print(request.user_agent.browser.family)  # returns 'Mobile Safari'
#         print(request.user_agent.browser.version)  # returns (5, 1)
#         print(request.user_agent.browser.version_string)   # returns '5.1'

#     # Operating System properties
#         # returns OperatingSystem(family=u'iOS', version=(5, 1), version_string='5.1')
#         print(request.user_agent.os)
#         print(request.user_agent.os.family)  # returns 'iOS'
#         print(request.user_agent.os.version)  # returns (5, 1)
#         print(request.user_agent.os.version_string)  # returns '5.1'

#     # Device properties
#         print(request.user_agent.device)  # returns Device(family='iPhone')
#         print(request.user_agent.device.family)  # returns 'iPhone'
#         print(request.user_agent.device.brand)  # returns 'iPhone'

#         return Response(status=status.HTTP_200_OK)

#     def get(self, request):
#         login_det = LoginDetails.objects.filter(
#             user=request.user).order_by('-pk')
#         serializer = LoginDetailSerializer(login_det, many=True)
#         return Response(serializer.data)


class CustomerAccountVerify(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        if "email" in request.data:
            # try:
            #     EmailValidator()(request.data['email'])
            # except ValidationError:
            #     return Response({"error_detail": ['Invalid email format']}, status=status.HTTP_400_BAD_REQUEST)
            
            # if(User.objects.filter(is_customer=True).get(
            #         username=request.data['email']))
            try:
                try:
                    EmailValidator()(request.data['email'])
                    user = User.objects.filter(is_customer=True).get(
                    email=request.data['email'])
                except:
                    user = User.objects.filter(is_customer=True).get(
                    username=request.data['email'])
                customer = Customers.objects.filter(user=user).get()
                #
                # check if already a reset link/otp request exists with expiry time still left
                if (CustomerOTP.objects.filter(customer=customer.pk, otp_for=2, email_id=user.email, expiry__gt=timezone.now()).exists()):
                    return Response({"error_detail": ["A valid reset OTP already exists. Please use it / wait till its expire"]}, status=status.HTTP_400_BAD_REQUEST)
                
                # origin = request.data['origin']
                OTP_code = randint(100000, 999999)
                encOTP = fernet.encrypt(str(OTP_code).encode())
                # MODE - ADMIN PASSWORD RESET / FORGOT
                CustomerOTP.objects.create(customer=customer, otp_for=2, email_id=user.email,
                                    otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
                message = f'\n{customer.firstname}, \n Please use this OTP {OTP_code} to verify your account and complete the process.OTP is valid for 5 minutes only.'
                html_message = render_to_string('verify_email_otp.html', {
                                            "name": customer.firstname, "code": OTP_code})
                subject = "One Time Password to Verify your Email Address"
                send_mail(html_message=html_message, subject=subject, message=message,
                      from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[user.email])
                CustomerOTP.objects.filter(customer=customer.pk,  otp_for=2, expiry__lt=timezone.now()).delete()
                return Response({"success": True, "message": "Email with OTP for account verification has been sent"})
            except User.DoesNotExist:
                return Response({"message": "No User Found with provided details"}, status=status.HTTP_400_BAD_REQUEST)

class CustomerForgotPassword(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            # try:
            #     EmailValidator()(request.data['user'])
            #     user = User.objects.filter(is_customer=True).get(
            #         email=request.data['user'])
            # except:
            user = User.objects.filter(is_customer=True).get(
                    username=request.data['username'])
            customer = Customers.objects.filter(user=user).get()
            # if (CustomerOTP.objects.filter(customer=customer.pk, otp_for=1, email_id=user.email, expiry__gt=timezone.now()).exists()):
            #     return Response({"error_detail": ["A valid reset OTP already exists. Please use it / wait till its expire"]}, status=status.HTTP_400_BAD_REQUEST)
            # subject = "OTP to reset your Password"
            # OTP_code = randint(100000, 999999)
            # encOTP = fernet.encrypt(str(OTP_code).encode())
            # CustomerOTP.objects.create(customer=customer, otp_for=1, email_id=user.email,
            #                         otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
            # message = f"Use this OTP to reset your password and to enter new password. \n This OTP is only valid for 5 minutes."
            # html_message = render_to_string(
            #     'reset_email_template.html', { "encOTP": OTP_code, "name": customer.firstname, "account_type": "Customer", "path": "auth-reset/confirm_reset"})
            # send_mail(subject=subject, message=message,
            #           from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[user.email], html_message=html_message)
            # CustomerOTP.objects.filter(
            #     customer=customer.pk,  otp_for=1, expiry__lt=timezone.now()).delete()

            email = None
            otp_code = randint(100000, 999999)
            CustomerOTP.objects.create(
                customer=customer,
                otp_for=1,
                email_id=email,
                otp_code=otp_code,
                expiry=timezone.now() + timedelta(minutes=5)
            )
            
            template_id = "1707175065621417140"
            message = f"Dear {customer.firstname}, Your OTP is {str(otp_code)} for registration. Thank you for registering with TN Jewellers."
            # Send SMS with proper arguments

            send_customer_reg_sms(
                request.data['mobile'], 
                str(otp_code), 
                customer.firstname,
                [customer.firstname, str(otp_code)],
                template_id,
                message)
            
            return Response({"success": True, "message": "Email with OTP for reset password has been sent"})
        except User.DoesNotExist:
            return Response({"message": "No User Found with provided details"}, status=status.HTTP_400_BAD_REQUEST)

class CustomerOTPVerify(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        if 'email_otp' in request.data:
            # Delete Expired OTPs of all users.  || Later:  Need to check case of Valid OTPs of this User other than email in request
            CustomerOTP.objects.filter(expiry__lt=timezone.now()).delete()
            try:
                # otp  for  -- "2", "Email Verify OTP" - change if any other scenario uses this API view
                latest_otp = CustomerOTP.objects.filter( otp_for=2, email_id=request.data['email'], expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['email_otp']):
                    user = User.objects.filter(email=request.data['email']).get()
                    customer = Customers.objects.filter(user=user.pk).update(is_email_verified=True)
                    # customer.is_email_verified = True
                    # customer.save()
                    # Delete this OTP because its usage is over.
                    latest_otp.delete()
                    # Delete OTP related with user & email
                    CustomerOTP.objects.filter( email_id=request.data['email']).delete()  # / mutli request scenario
                    return Response({'message': "OTP verified"})
                else:
                    raise CustomerOTP.DoesNotExist
            except CustomerOTP.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)
            
        if 'forgotpass_otp' in request.data:
            CustomerOTP.objects.filter(expiry__lt=timezone.now()).delete()
            try:
                # otp  for  -- "0", "Forgot Password OTP" - change if any other scenario uses this API view
                latest_otp = CustomerOTP.objects.filter(otp_for=1, email_id=request.data['email'], expiry__gte=timezone.now()).latest('creation_time')
                if (latest_otp.otp_code == request.data['otp']):
                    # Delete this OTP because its usage is over.
                    latest_otp.delete()
                    # Delete OTP related with user & email
                    CustomerOTP.objects.filter(email_id=request.data['email']).delete()  # / mutli request scenario
                    return Response({'message': "OTP verified"})
                else:
                    raise CustomerOTP.DoesNotExist
            except CustomerOTP.DoesNotExist:
                return Response({"error_detail": ['OTP entered is incorrect']}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error_detail": ['Invalid Request']}, status=status.HTTP_400_BAD_REQUEST)
    

class CustomerResetPassword(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        user = User.objects.filter(email=request.data['email'], is_customer=True).get()
        if user:
            if (bool(user.check_password(request.data['confrm_pass']))):
                return Response({"error_detail": ["New Password and Old password can't be same"]}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(request.data['confrm_pass'])
            user.save()
            tokens = AuthToken.objects.filter(user=user).delete()
            return Response({"message": "Password changed successfully"})
        else:
            return Response({"message": "User Not Found"})

class CustomerChangePassword(generics.GenericAPIView):
    permission_classes = [isAdmin]

    def post(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.user.id, is_customer=True).first()
    
        if not user:
            return Response({"message": "User Not Found"}, status=status.HTTP_404_NOT_FOUND)

        old_password = request.data.get('old_pass')
        new_password = request.data.get('confirm_pass')

        if not user.check_password(old_password):
            return Response({"error_detail": ["Old password is incorrect"]}, status=status.HTTP_400_BAD_REQUEST)

        if old_password == new_password:
            return Response({"error_detail": ["New password and old password can't be the same"]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        AuthToken.objects.filter(user=user).delete()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)   
    

class loginsessionView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        def get_ip_address(request):
            user_ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
            if user_ip_address:
                ip = user_ip_address.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip
        user_ip = get_ip_address(request)
        print(user_ip)
        print(request.user)
    # Let's assume that the visitor uses an iPhone...
        print(request.user_agent.is_mobile)  # returns True
        print(request.user_agent.is_tablet)  # returns False
        print(request.user_agent.is_touch_capable)  # returns True
        print(request.user_agent.is_pc)  # returns False
        print(request.user_agent.is_bot)  # returns False

    # Accessing user agent's browser attributes
        # returns Browser(family=u'Mobile Safari', version=(5, 1), version_string='5.1')
        print(request.user_agent.browser)
        print(request.user_agent.browser.family)  # returns 'Mobile Safari'
        print(request.user_agent.browser.version)  # returns (5, 1)
        print(request.user_agent.browser.version_string)   # returns '5.1'

    # Operating System properties
        # returns OperatingSystem(family=u'iOS', version=(5, 1), version_string='5.1')
        print(request.user_agent.os)
        print(request.user_agent.os.family)  # returns 'iOS'
        print(request.user_agent.os.version)  # returns (5, 1)
        print(request.user_agent.os.version_string)  # returns '5.1'

    # Device properties
        print(request.user_agent.device)  # returns Device(family='iPhone')
        print(request.user_agent.device.family)  # returns 'iPhone'
        print(request.user_agent.device.brand)  # returns 'iPhone'

        return Response(status=status.HTTP_200_OK)

    def get(self, request):
        login_det = LoginDetails.objects.filter(
            user=request.user).order_by('-pk')[:10]
        serializer = LoginDetailSerializer(login_det, many=True)
        return Response(serializer.data)       

# Admin Change Password API:
class AdminChangePassword(generics.GenericAPIView):
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
    
class EncodeAndDecodeView(generics.GenericAPIView):
    permission_classes=[isAdmin]
    
    def post(self, request, *args, **kwargs):
        encrypted = fernet.encrypt(str(request.data['name']).encode())
        decrypted = fernet.decrypt(encrypted)
        
        print(encrypted)
        print(decrypted)
        return Response(status=status.HTTP_200_OK)
    
    
class TokenRefreshApi(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Extract the Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith("Token "):
            return Response({"detail": "Invalid or missing token."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract the token key
        token_key = auth_header.split(" ")[1]
        print(token_key[:8])
        try:
            # Fetch the token from the database
            token = AuthToken.objects.get(token_key=token_key[:8])  # Knox tokens store the first 8 chars as a key
            print(token)
        except AuthToken.DoesNotExist:
            return Response({"detail": "Token not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the token has expired
        print(now())
        print(token.expiry < now())
        if token.expiry < now():
            print(token)
            # Update the expiry to a new time (e.g., add 10 hours)
            new_expiry = now() + timedelta(hours=10)
            token.expiry = new_expiry
            token.save()

            return Response({
                "detail": "Token expiry updated.",
                "new_expiry": new_expiry
            }, status=status.HTTP_200_OK)
        
        return Response({"detail": "Token is still valid."}, status=status.HTTP_200_OK)


class MenuSearchView(generics.GenericAPIView):
    permission_classes = [isAdmin]
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    
    def post(self, request, *args, **kwargs):
        user = request.user
        employee = Employee.objects.filter(user=user).first()
        profile = get_object_or_404(Profile, id_profile=employee.id_profile.pk)
        
        # Get menus based on user's access
        menu_access = EmpMenuAccess.objects.filter(profile=profile, view=True).values_list('menu_id', flat=True)
        
        # Filter menus based on the search criteria
        search_query = request.data.get('search', '').strip()
        menus = Menu.objects.filter(id__in=menu_access, text__icontains=search_query).exclude(link__contains='#').exclude(link__contains='*')
        serializer = MenuSerializer(menus, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ReportColumnsTemplatesList(PaginationMixin,generics.ListCreateAPIView):
    permission_classes = [isAdmin]
    serializer_class = ReportColumnsTemplatesSerializer
    queryset = ReportColumnsTemplates.objects.all()

    def post(self, request, *args, **kwargs):
        request.data['menu'] = Menu.objects.get(link=request.data['path']).pk
        request.data['user'] = request.user.pk
        queryset = ReportColumnsTemplates.objects.filter(user = request.data['user'],menu = request.data['menu'])
        if queryset:
            queryset = queryset.get().delete()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
def get_reports_columns_template(user,report_columns,report_name):
    queryset = ReportColumnsTemplates.objects.filter(user = user,menu__link = report_name)
    if queryset:
        queryset = queryset.get()
        columns = json.loads(queryset.columns)
        for row in report_columns:
            template_row = [item for item in columns if item.get("accessor") == row.get("accessor")]
            if template_row:
                template_row = template_row[0]
                row['showCol'] = template_row.get("showCol",True)
    return report_columns
