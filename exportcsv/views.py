from django.shortcuts import render
from django.http import HttpResponse
import csv
from django.conf import settings
from xhtml2pdf import pisa
import os
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
import logging
from retailsettings.models import (RetailSettings)
from rest_framework.response import Response
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee, isSuperuser
from django.db import DatabaseError, OperationalError, connection,IntegrityError
from django.db import transaction
from datetime import datetime, timedelta, date
from rest_framework.exceptions import ValidationError
from customers.models import (Customers)
from customers.serializers import (CustomerSerializer)
from accounts.models import User
from retailmasters.models import (Size,Branch, Supplier, Uom,FinancialYear,ErpStockStatusMaster)
from retailcataloguemasters.models import (Purity,Section,Metal, Product, Category, Design, SubDesign, ProductMapping, SubDesignMapping,Stone,ProductSection)
from itertools import islice  # Import islice for batch processing
from .models import (RawCustomerData,RawTagData,RawTagStoneData, RawSchemeAccountData)
from .serializers import (RawTagDataSerializer, RawTagStoneDataSerializer, RawSchemeAccountDataSerializer)
from inventory.views import ErpTagCreateAPIView
from retailmasters.views import BranchEntryDate
from employees.models import (Employee,EmployeeType,EmployeeSettings)
from reports.constants import (SCHEME_ABSTRACT_COLUMN_LIST)
from inventory.models import ErpTagging,ErpTaggingLogDetails,ErpTaggingStone
from schememaster.models import (Scheme)
from managescheme.models import (SchemeAccount)
from managescheme.serializers import (SchemeAccountSerializer)
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
import random
import uuid
import copy
logger = logging.getLogger(__name__)
from employees.serializers import EmployeeSerializer,EmployeeSettingsSerializer
from retailmasters.models import (Branch, Profile, Country, State, City, Area, Department)
from dateutil.relativedelta import relativedelta
from random import randint
from rest_framework import serializers



def call_stored_procedure(proc_name, *args):
    try:
        with connection.cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(args))
            proc_call = f"CALL {proc_name}({placeholders})"
            cursor.execute(proc_call, args)
            print(connection.queries[-1])
            response_data = ({"report_field":[],"report_data":[]})
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.append(field_value)
                response_data = { "report_field":field_names,"report_data":report_data}
            else:
                result = None
            return response_data
    except OperationalError as e:
        if 'does not exist' in str(e):
            return Response({"error": f"Error: Stored Procedure '{proc_name}' does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise e
    except DatabaseError as e:
        return Response({"error": f"Database error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment, filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(['employee', 'morning', 'afternoon', 'date'])

    users = Employee.objects.all().values_list('firstname')
    for user in users:
        writer.writerow(user)

    return response

class EmployeeExport(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        # filename = f'data_{now().strftime("%Y%m%d%H%M%S")}.csv'
        csv_dir = os.path.join(settings.MEDIA_ROOT, 'export_csv')
        csv_file_path = os.path.join(csv_dir, f'employee.csv')
        # csv_file_path = os.path.join(csv_dir, f'invoice_{payment.id_payment}.csv')

        # Create the directory if it doesn't exist
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)

        # Generate the CSV if it doesn't exist
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(['FirstName', 'LastName', 'Mobile'])
                for obj in Employee.objects.all():
                    csvwriter.writerow([obj.firstname, obj.lastname, obj.mobile])
        file_url = request.build_absolute_uri(settings.MEDIA_URL + f'export_csv/employee.csv')
        return Response({'csv_file_path': file_url}, status=status.HTTP_200_OK)


class SchemeAbstractExport(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        # filename = f'data_{now().strftime("%Y%m%d%H%M%S")}.csv'
        csv_dir = os.path.join(settings.MEDIA_ROOT, 'export_csv')
        csv_file_path = os.path.join(csv_dir, f'scheme_abstract.csv')
        # csv_file_path = os.path.join(csv_dir, f'invoice_{payment.id_payment}.csv')

        # Create the directory if it doesn't exist
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
            
        from_date = request.data['from_date']
        to_date = request.data['to_date']
        id_scheme = request.data['id_scheme']
        id_branch = request.data['id_branch']
        # Convert id_scheme and id_branch to integers if provided, else set to None
        id_scheme = (id_scheme) if id_scheme != '' else 0   
        id_branch = (id_branch) if id_branch != '' else 0
        #Execute the stored procedure
        collection_report = call_stored_procedure('GetCollectionReport',from_date,to_date,id_branch,id_scheme)
        print(collection_report['report_data'])

        # Generate the CSV if it doesn't exist
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                instance = []
                for header in SCHEME_ABSTRACT_COLUMN_LIST:
                    instance.append(header['Header'])
                    # print(header['Header'])
                csvwriter.writerow(instance)
                for obj in collection_report['report_data']:
                    csvwriter.writerow([
                        obj['receipt_no'], obj['entry_date'], obj['cus_name'], obj['mobile'],
                        obj['scheme_name'], obj['scheme_acc_number'], obj['payment_amount'], obj['discountAmt'],
                        obj['net_amount'], obj['metal_weight'], obj['metal_rate'], obj['paid_through'],
                        obj['emp_name']
                                        ])
        file_url = request.build_absolute_uri(settings.MEDIA_URL + f'export_csv/scheme_abstract.csv')
        return Response({'csv_file_path': file_url}, status=status.HTTP_200_OK)


class UploadCustomerDataView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = csv_file.read().decode("utf-8").splitlines()
            csv_reader = csv.DictReader(data)
        except Exception:
            return Response({"error": "Invalid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        raw_data = []
        user_objects = []
        customer_objects = []
        with transaction.atomic():
            for row in csv_reader:
                if User.objects.filter(username=row.get("mobile")).exists():
                                is_imported = False
                                error_message = "User with this username already exists."
                else:
                    user = {}
                
                    user.update({
                       "username":row.get("mobile"),
                       "first_name":row.get("firstname"),
                       "last_name":row.get("lastname"),
                       "email":row.get("email",None),
                       "isCustomer":True
                    })
                    user.set_password(row.get("mobile"))
                    user_objects.append(user)
                    created_users = User.objects.create(user)
                    user.save()
                                    
                    
                    # Add the Customer object
                    customer_objects.append(Customers(
                        mobile=row.get("mobile"),
                        firstname=row.get("firstname"),
                        lastname=row.get("lastname", ""),
                        email=row.get("email", None),
                        user=user.pk,
                        created_by=request.user,
                    ))
                    
                    

                    # Associate Customers with the created Users
                    for customer, user in zip(customer_objects, created_users):
                        customer.user = user

                    # Bulk create Customers and update raw data
                    Customers.objects.bulk_create(customer_objects, ignore_conflicts=True)
                    
                    
                raw_data.append(
                    RawCustomerData(
                        mobile=row.get("mobile"),
                        firstname=row.get("firstname"),
                        lastname=row.get("lastname", ""),
                        email=row.get("email", None),
                        address1=row.get("address1", None),
                        address2=row.get("address2", None),
                        pincode=row.get("pincode", None),
                        is_imported = is_imported,
                        error_message = error_message,
                    )
                )

            RawCustomerData.objects.bulk_create(raw_data)
            # customer_import_class = ImportCustomerRawData()
            # customer_import_class.import_cus_data(request)

        return Response(
                            {
                                "message": f"Imported {len(raw_data)} customers with some errors."
                            },
                        status=status.HTTP_200_OK,
                        )






class ImportCustomerRawData(APIView):
    
    def post(self, request):
        task = import_customer_data.delay()

        return Response(
            {
                "message": "Customer import started.",
                "task_id": task.id,
            },
            status=status.HTTP_200_OK
        )

    def import_cus_data(self, request, *args, **kwargs):
        raw_data = RawCustomerData.objects.filter(is_imported=False)
        batch_size = 500  # Process records in batches
        imported_count = 0
        errors = []

        for batch_start in range(0, len(raw_data), batch_size):
            batch = raw_data[batch_start:batch_start + batch_size]
            user_objects = []
            customer_objects = []
            raw_updates = []

            with transaction.atomic():
                for raw in batch:
                    try:
                        # Check if User already exists
                        if User.objects.filter(username=raw.mobile).exists():
                            raw.is_imported = False
                            raw.error_message = "User with this username already exists."
                        else:
                            # Create the User object
                            user = User(
                                username=raw.mobile,
                                first_name=raw.firstname,
                                last_name=raw.lastname,
                                email=raw.email,
                                is_customer=True,
                            )
                            user.set_password(raw.mobile)
                            user_objects.append(user)

                            # Fetch branch for the customer
                            branch = Branch.objects.filter(id_branch=raw.branch_id).first()
                            if not branch:
                                raise ValueError(f"Branch with ID {raw.branch_id} not found.")

                            # Add the Customer object
                            customer_objects.append(Customers(
                                user=user,
                                mobile=raw.mobile,
                                firstname=raw.firstname,
                                lastname=raw.lastname,
                                email=raw.email,
                                id_branch=branch,
                                created_by=request.user,
                            ))

                            raw.is_imported = True
                            raw.error_message = None

                        raw_updates.append(raw)

                    except Exception as e:
                        raw.is_imported = False
                        raw.error_message = f"Error creating user/customer: {str(e)}"
                        raw_updates.append(raw)
                        errors.append({"row": raw.id, "error": raw.error_message})

                # Bulk create Users
                created_users = User.objects.bulk_create(user_objects, ignore_conflicts=True)

                # Associate Customers with the created Users
                for customer, user in zip(customer_objects, created_users):
                    customer.user = user

                # Bulk create Customers and update raw data
                Customers.objects.bulk_create(customer_objects, ignore_conflicts=True)
                RawCustomerData.objects.bulk_update(
                    raw_updates, fields=["is_imported", "error_message"]
                )

                imported_count += len(created_users)

        # Return the response
        response_message = {
            "message": f"Imported {imported_count} customers successfully.",
            "errors": errors,
        }
        return Response(response_message, status=status.HTTP_200_OK)

                        

class ImportCustomerDataCSVView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        # Step 1: Validate file input
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = csv_file.read().decode("utf-8").splitlines()
            csv_reader = csv.DictReader(data)
        except Exception:
            return Response({"error": "Invalid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        required_fields = ["mobile", "firstname"]  # 'email' is optional
        errors = []
        created_customers = []
        batch_size = 100  # Process 100 rows at a time

        try:
            with transaction.atomic():
                # Step 2: Load existing users for duplicate checks
                existing_usernames = set(User.objects.values_list("username", flat=True))

                while True:
                    # Step 3: Read a batch of rows
                    batch = list(islice(csv_reader, batch_size))
                    if not batch:
                        break

                    customers_to_create = []
                    users_to_create = []

                    for row_number, row in enumerate(batch, start=1):
                        try:
                            # Validate required fields
                            missing_fields = [field for field in required_fields if not row.get(field)]
                            if missing_fields:
                                errors.append({"row": row_number, "error": f"Missing fields: {', '.join(missing_fields)}"})
                                continue

                            mobile = row.get("mobile").strip()
                            firstname = row.get("firstname").strip()
                            lastname = row.get("lastname", "").strip()
                            email = row.get("email", None)

                            # Check for duplicate username
                            if mobile in existing_usernames:
                                errors.append({"row": row_number, "error": f"User with mobile {mobile} already exists."})
                                continue

                            # Create User instance
                            user = User(
                                username=mobile,
                                email=email,
                                first_name=firstname,
                                last_name=lastname,
                                account_expiry=date.today().replace(year=date.today().year + 1),
                                is_customer=True,
                            )
                            user.set_password(mobile)
                            users_to_create.append(user)

                            # Add username to local set for duplicate prevention
                            existing_usernames.add(mobile)

                            # Fetch Branch instance
                            branch = Branch.objects.get(id_branch=request.data["branch"])

                            # Create Customer instance
                            customer = Customers(
                                mobile=mobile,
                                firstname=firstname,
                                lastname=lastname,
                                created_by=request.user,
                                id_branch=branch.pk,
                            )
                            customers_to_create.append(customer)

                        except Branch.DoesNotExist:
                            errors.append({"row": row_number, "error": "Branch does not exist."})
                        except Exception as e:
                            errors.append({"row": row_number, "error": str(e)})

                    # Step 4: Save users individually, then save customers with foreign key reference to users
                    # First, save User instances
                    for user in users_to_create:
                        user.save()  # Save each user one at a time
                    
                    # After users are saved, link them to customers and save customers
                    for customer, user in zip(customers_to_create, users_to_create):
                        customer.user = user  # Assign the saved user to the customer
                        customer.save()

                    # Track created customers for the response
                    created_customers.extend(customers_to_create)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 5: Return response
        return Response(
            {
                "message": f"Imported {len(created_customers)} customers with some errors.",
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )
        
class ImportMetalCategoryProductCSV(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = csv_file.read().decode("utf-8").splitlines()
            csv_reader = csv.DictReader(data)
        except Exception as e:
            return Response({"error": f"Invalid CSV file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        required_fields = ["Metal", "Category", "Product",] 
        with transaction.atomic():
            try:
                
                for row_number, row in enumerate(csv_reader, start=1):
                    missing_fields = [field for field in required_fields if not row.get(field)]
                    if missing_fields:
                        return Response({"error": f"Row {row_number}: Missing fields: {', '.join(missing_fields)}"}, 
                                        status=status.HTTP_400_BAD_REQUEST)
                    metal_name = row.get("Metal").strip()
                    category_name = row.get("Category").strip()
                    product_name = row.get("Product").strip()
                    design_name = row.get("Design").strip()
                    sub_design_name = row.get("SubDesign").strip()

                    if not metal_name or not category_name or not product_name:
                        raise ValueError(f"Missing data at row {row_number}: Metal, Category, and Product Name are required.")

                    # --- Step 1: Check or create Metal ---
                    metal, _ = Metal.objects.get_or_create(
                        metal_name=metal_name,
                        defaults={"created_by": request.user}
                    )

                    # --- Step 2: Check or create Category ---
                    category, _ = Category.objects.get_or_create(
                        cat_name=category_name,
                        id_metal=metal,
                        defaults={"created_by": request.user, "cat_type": "1"}
                    )

                    # --- Step 3: Check or create Product ---
                    product, _ = Product.objects.get_or_create(
                        product_name=product_name,
                        id_metal=metal,
                        cat_id=category,
                        defaults={"created_by": request.user, "stock_type": "0", "sales_mode": "0"}
                    )

                    # --- Step 4: Check or create Design ---
                    if design_name:
                        design, _ = Design.objects.get_or_create(
                            design_name=design_name,
                            defaults={"created_by": request.user}
                        )

                        # --- Step 5: Map Product to Design (ProductMapping) ---
                        ProductMapping.objects.get_or_create(
                            id_product=product,
                            id_design=design,
                            defaults={"created_by": request.user}
                        )
                    
                        # --- Step 6: Check or create SubDesign ---
                        if sub_design_name:
                            sub_design, _ = SubDesign.objects.get_or_create(
                                sub_design_name=sub_design_name,
                                defaults={"created_by": request.user}
                            )

                            # --- Step 7: Map Product, Design, and SubDesign (SubDesignMapping) ---
                            SubDesignMapping.objects.get_or_create(
                                id_product=product,
                                id_design=design,
                                id_sub_design=sub_design,
                                defaults={"created_by": request.user}
                            )

                return Response({"message": "CSV file imported successfully."}, status=status.HTTP_200_OK)

            except Exception as e:
                transaction.set_rollback(True)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            

class UploadTagDetailsDataView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        csv_file2 = request.FILES.get("file2")
        import_id = random.randint(1000000, 9999999)
        tag_stone = []
        if not csv_file:
            return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = csv_file.read().decode("utf-8").splitlines()
            csv_reader = csv.DictReader(data)
        except Exception:
            return Response({"error": "Invalid CSV file."}, status=status.HTTP_400_BAD_REQUEST)
        
        if csv_file2:
            try:
                stone_data = csv_file2.read().decode("utf-8").splitlines()
                tag_stone = list(csv.DictReader(stone_data))
            except Exception:
                return Response({"error": "Invalid CSV file."}, status=status.HTTP_400_BAD_REQUEST)
    
        is_sub_design_req = int(RetailSettings.objects.get(name='is_sub_design_req').value)
        raw_data = []
        with transaction.atomic():
            for row in csv_reader:
                filtered_stone =  []
                is_imported = True
                error_message = ""
                branch = None
                product = None
                design = None
                purity = None
                sub_design = None
                uom = None
                section = None
                karigar = None
                formatted_date = None
                tag = {}
                branch_name = row.get("Branch")
                product_name = row.get("Product")
                product_code = row.get("ProductCode")
                design_name = row.get("Design").strip()
                sub_design_name = row.get("SubDesign")
                section_name = row.get("Section")
                size_name = row.get("Size")
                uom_name = row.get("Uom")
                purity_name = row.get("Purity")
                karigar_name = row.get("KARIGAR")
                short_code = row.get("KARIGARCODE")
                date = row.get("TagDate")
                if(date):
                    date_obj = datetime.strptime(date, "%d/%m/%Y")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                else:
                    formatted_date = datetime.now().strftime('%Y-%m-%d')


                if ErpTagging.objects.filter(old_tag_code=row.get("TagNumber")).exists():
                                is_imported = False
                                error_message = "Tag Code already exists."
                                print(error_message)
                                print(ErpTagging.objects.filter(old_tag_code=row.get("TagNumber")).get().pk)
                else:
                   
                    try :
                        branch = Branch.objects.filter(name=branch_name).get().pk
                        if product_name!='':
                            product = Product.objects.filter(product_name=product_name).get().pk
                        elif product_code!='':
                            product = Product.objects.filter(short_code=product_code).get().pk
                        # product_instance = Product.objects.get(product_name=product_name)
                        if not (Design.objects.filter(design_name=design_name)).exists():
                            
                            design = Design.objects.create(design_name=design_name, created_by=request.user)
                            ProductMapping.objects.create(
                                id_product=Product.objects.get(pro_id=product),
                                id_design=design,
                                created_by=request.user
                            )
                        design = Design.objects.filter(design_name=design_name).get().pk
                        if section_name!='':
                            if not (Section.objects.filter(section_name=section_name)).exists():
                                section = Section.objects.create(section_name=section_name, created_by=request.user)
                                ProductSection.objects.create(
                                    id_product=Product.objects.get(pro_id=product),
                                    id_section=section,
                                    created_by=request.user
                                )
                            section = Section.objects.filter(section_name=section_name).get().pk

                            if not (ProductSection.objects.filter(id_section=section,id_product = product).exists()):
                                ProductSection.objects.create(
                                    id_product=Product.objects.get(pro_id=product),
                                    id_section=Section.objects.get(id_section=section),
                                    created_by=request.user
                                )

                        if karigar_name!='':
                            if not (Supplier.objects.filter(supplier_name=karigar_name)).exists():
                                karigar = Supplier.objects.create(
                                    supplier_name=karigar_name, 
                                    short_code = randint(400, 999),
                                    created_by=request.user)
                            karigar = Supplier.objects.filter(supplier_name=karigar_name).get().pk

                        #print(date_obj,formatted_date,date)
                        if(is_sub_design_req == 1):
                            sub_design = SubDesign.objects.filter(sub_design_name=sub_design_name).get().pk
                        else:
                            sub_design = None
                     
                        if(uom_name):
                            uom = Uom.objects.filter(uom_name=uom_name).get().pk
                        else:
                            uom = 1
                            
                        if(purity_name):
                            purity = Purity.objects.filter(purity=purity_name).get().pk
                        else:
                            purity = None

                        if(size_name and Size.objects.filter(id_product = product,name=size_name).exists()):
                            size = Size.objects.filter(id_product = product,name=size_name).get().pk
                        else:
                            error_message = f"Invalid Size : {size_name}"
                            size = None

                    except Supplier.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Supplier : {karigar_name}"
                    except Product.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Product : {product_name}"
                    except Design.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Design : {design_name}"
                    except SubDesign.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Sub Design : {sub_design_name}"
                    except Section.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Section : {section_name}"
                    except Purity.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Purity : {purity_name}"
                    except Uom.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Uom : {uom_name}"

                tag ={
                    "error_msg": error_message,
                    "import_status": 2 if is_imported == True else 1 ,
                    "tag_date": formatted_date,
                    "tag_current_branch": branch,
                    "tag_product_id": product,
                    "tag_design_id": design,
                    "tag_sub_design_id": sub_design,
                    "tag_section_id": section,
                    "tag_purity_id": purity,
                    "tag_supplier_id": karigar,
                    "size_id": size,
                    "tag_uom_id": uom,
                    "tag_pcs": row.get("Pieces").strip(),
                    "tag_gwt": row.get("GrossWt",'0.00').strip() if row.get("GrossWt")!='' else 0,
                    "tag_lwt": float(row.get("LessWt")) if row.get("LessWt") and row.get("LessWt").strip() else 0.0,
                    "tag_nwt": row.get("NetWt",'0.00').strip() if row.get("NetWt")!='' else 0,
                    "tag_stn_wt": row.get("StnWt",'0.00').strip() if row.get("StnWt")!='' else 0,
                    "tag_dia_wt": row.get("DiaWt",'0.00').strip() if row.get("DiaWt")!='' else 0,
                    "tag_wastage_percentage": row.get("WastagePer","0").strip() if row.get("WastagePer")!='' else 0,
                    "tag_wastage_wt": row.get("WastageWt",'0.000').strip() if row.get("WastageWt")!='' else 0,
                    "tag_mc_value": row.get("MCValue",'0.00').strip(),
                    "tag_mc_type": row.get("MCType") if  row.get("MCType") and row.get("MCType").strip() else '1',
                    "flat_mc_value": row.get("FlatMc",'0.00').strip() if row.get("FlatMc")!='' else 0,
                    "tag_sell_rate": row.get("SalesValue").strip() if row.get("SalesValue",'0.00').strip() != '' else 0,    
                    "tag_buy_rate": row.get("PurchaseCost",'0.00').strip() if row.get("PurchaseCost")!='' else 0,
                    "tag_huid2": row.get("HUID2").strip()  if row.get("HUID2",'').strip() != '' else None,
                    "tag_huid":row.get("HUID1").strip() if row.get("HUID1",'').strip() != '' else None,
                    "old_tag_id": row.get("TagNumber").strip(),
                    "old_tag_code": row.get("TagNumber").strip(),
                    "tag_tax_amount":0,
                    "tag_item_cost":0,
                    "import_id": import_id,
                }
                tag_import_id= insert_data_return_id('tag_import',tag)
                tag.update({'id':tag_import_id})
                                
                raw_instance = RawTagData.objects.get(id = tag_import_id)
                raw_instance.error_msg = error_message
                raw_instance.import_status = 2 if is_imported == True else 1
                raw_instance.save()

            for stn in tag_stone:
                    import_tag = None
                    cal_type = 1
                    show_in_lwt = 1
                    stone = None
                    uom = None
                    quality_code = None
                    stn_error_message = ''
                    stn_is_imported = True
                    try :
                        
                        stone_name = stn.get("StoneName").strip()
                        uom_name = stn.get("Unit").strip()
                        #quality_code_name = stn.get("Unit").strip()
                        cal_type_name = stn.get("CAL TYPE").strip()
                        show_in_lwt_name = stn.get("Less Wt").strip()
                        stone_type = stn.get("stone_type").strip()
                        cal_type = 1 if cal_type_name == "PER PIECE" else 2
                        show_in_lwt = 1 if show_in_lwt_name == "YES" else 0
                        raw_tag_instance = RawTagData.objects.filter(import_id = import_id,old_tag_code = stn.get("Tag Number").strip()).get()
                        import_tag = raw_tag_instance.pk
                        if not (Stone.objects.filter(stone_name=stone_name)).exists():
                            uom = Uom.objects.filter(uom_name=uom_name).get()
                            stone = Stone.objects.create(
                                stone_name=stone_name, 
                                show_less_wt = show_in_lwt,
                                stone_type = stone_type,
                                uom_id = uom,
                                created_by=request.user)
                        stone = Stone.objects.filter(stone_name=stone_name).get().pk
                        uom = Uom.objects.filter(uom_name=uom_name).get().pk
                        #quality_code = QualityCode.objects.filter(code=uom_name).get().pk
                        cal_type = 1 if cal_type_name == "PER PIECE" else 2
                        show_in_lwt = 1 if show_in_lwt_name == "YES" else 0

                    except Stone.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Stone Details"
                        stn_is_imported = False
                        stn_error_message = f"Invalid Stone : {stone_name}"
                        if raw_tag_instance:
                            raw_tag_instance.error_msg = error_message
                            raw_tag_instance.import_status = 2 if is_imported == True else 1
                            raw_tag_instance.save()
                    except RawTagData.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Stone Details"
                        stn_is_imported = False
                        stn_error_message = f"Invalid Raw Tag Data : {stn.get('Tag Number').strip()}"
                    except Uom.DoesNotExist:
                        is_imported = False
                        error_message = f"Invalid Stone Details"
                        stn_is_imported = False
                        stn_error_message = f"Invalid Uom : {uom_name}"
                        if raw_tag_instance:
                            raw_tag_instance.error_msg = error_message
                            raw_tag_instance.import_status = 2 if is_imported == True else 1
                            raw_tag_instance.save()
                    insert_item = {
                            "ref_id" : import_tag,
                            "show_in_lwt": show_in_lwt,
                            "stone_calc_type" :cal_type,
                            "id_stone" : stone,
                            "uom_id" : uom,
                            "id_quality_code": quality_code,
                            "stone_pcs" : stn.get("Pieces").strip(),
                            "stone_wt" : stn.get("Weight").strip(),
                            "stone_rate" :  stn.get("Rate/Gram").strip(),
                            "stone_amount":  stn.get("Amount").strip(),
                            "import_status" :2 if stn_is_imported == True else 1 ,
                            "error_msg" :stn_error_message,
                        }
                    
                    tag_stn_import_id= insert_data_return_id('tag_import_stone',insert_item)

            raw_data_instance = RawTagData.objects.filter(import_status = 2)
            
            raw_data = RawTagDataSerializer(raw_data_instance,many=True).data

            updated_data =[]
            current_date = datetime.now().strftime('%Y-%m-%d')
            for item, instance in zip(raw_data, raw_data_instance):
                
                try:                
                    fy=FinancialYear.objects.get(fin_status=True)
                    fin_id = fy.fin_id
                    branch_date = BranchEntryDate()
                    entry_date = branch_date.get_entry_date(item['tag_current_branch'])
                    product=Product.objects.get(pro_id=item['tag_product_id'])
                    tag_code_settings = RetailSettings.objects.get(name='tag_code_settings').value
                    if tag_code_settings=='4':
                        tag_code = ErpTagCreateAPIView.generate_random_tag_code(product.short_code)
                    else:
                        tag_code = ErpTagCreateAPIView.generate_tagcode(item,product.short_code,fy)
                    filtered_stone_instance =RawTagStoneData.objects.filter(ref_id = instance.pk)
                    filtered_stone = RawTagStoneDataSerializer(filtered_stone_instance,many = True).data
                    item.update({
                        "is_imported":1,
                        "tag_code":tag_code,
                        "tag_status_id":1,
                        "fin_year_id":fin_id,
                        "created_by_id": request.user.id,
                        "tag_current_branch_id": item['tag_current_branch'],
                        "tag_product_id_id": item['tag_product_id'],
                        "tag_design_id_id": item['tag_design_id'],
                        "tag_sub_design_id_id": item['tag_sub_design_id'],
                        "tag_section_id_id": item['tag_section_id'],
                        "tag_purity_id_id": item['tag_purity_id'],
                        "tag_uom_id_id": item['tag_uom_id'],
                        "id_supplier_id": item['tag_supplier_id'],
                        "size_id": item['size_id'],
                        'tag_other_metal_wt':0,
                        'tag_purchase_cost':0,
                        'tag_purchase_calc_type':1,
                        'tag_purchase_rate_calc_type':1,
                        'tag_purchase_mc':0,
                        'tag_purchase_mc_type':1,
                        'tag_purchase_rate':0,
                        'tag_pure_wt':0,
                        'tag_purchase_touch':0,
                        'tag_purchase_va':0,
                        'is_partial_sale':0,
                        'is_issued_to_counter':1,
                        'total_mc_value':0,
                        'is_special_discount_applied':0,
                        'created_on':now()
                    })
                    del item['error_msg']
                    del item['import_status']
                    del item['tag_supplier_id']
                    del item['id']
                    del item['tag_id']
                    del item['tag_product_id']
                    del item['tag_design_id']
                    del item['tag_sub_design_id']
                    del item['tag_section_id']
                    del item['tag_purity_id']
                    del item['tag_uom_id']
                    del item['tag_current_branch']
                    del item['import_id']


                    id= insert_data_return_id('erp_tagging',item)

                
                    log = {
                            "date" : current_date,
                            "transaction_type": 1,
                            "to_branch_id": item['tag_current_branch_id'],
                            "tag_id_id":id,
                            "id_stock_status_id":1,
                            "created_by_id":request.user.id,
                            "created_on":current_date,
                    }
                    ed_id= insert_data_return_id('erp_tag_log_details',log)
                    for stn, stn_instance in zip(filtered_stone, filtered_stone_instance):
                        try:
                            insert_item = {
                                    "tag_id_id":id,
                                    "show_in_lwt": stn.get("show_in_lwt"),
                                    "stone_calc_type" :stn.get("stone_calc_type"),
                                    "id_stone_id" : stn.get("id_stone"),
                                    "id_quality_code_id": stn.get("id_quality_code"),
                                    "uom_id_id" : stn.get("uom_id"),
                                    "stone_pcs" : stn.get("stone_pcs"),
                                    "stone_wt" : stn.get("stone_wt"),
                                    "stone_rate" :  stn.get("stone_rate"),
                                    "stone_amount":  stn.get("stone_amount"),
                                }
                            tag_stn_id = insert_data_return_id('erp_tag_stone',insert_item)
                            stn_instance.import_status = 4
                            stn_instance.save()
                        except IntegrityError as e:
                            error_message = f"Database Integrity Error: {str(e)}"
                            stn_instance.import_status = 3
                            stn_instance.error_msg = error_message
                            stn_instance.save()
                            raise
                        except OperationalError as e:
                            error_message = f"Database Operational Error: {str(e)}"
                            stn_instance.import_status = 3
                            stn_instance.error_msg = error_message
                            stn_instance.save()
                            raise
                        except ObjectDoesNotExist as e:
                            error_message = f"Object not found: {str(e)}"
                            stn_instance.import_status = 3
                            stn_instance.error_msg = error_message
                            stn_instance.save()
                            raise
                        except Exception as e:
                            error_message = f"Unexpected error: {str(e)}"
                            stn_instance.import_status = 3
                            stn_instance.error_msg = error_message
                            stn_instance.save()
                            raise

                        
                    instance.tag_id = id
                    instance.import_status = 4
                    instance.save()
                    updated_data.append(item)
                        
                except FinancialYear.DoesNotExist:
                    error_message = "No active financial year found."
                    instance.import_status = 3
                    instance.error_msg = error_message
                    instance.save()

                except IntegrityError as e:
                    error_message = f"Database Integrity Error: {str(e)}"
                    instance.import_status = 3
                    instance.error_msg = error_message
                    instance.save()
                except OperationalError as e:
                    error_message = f"Database Operational Error: {str(e)}"
                    instance.import_status = 3
                    instance.error_msg = error_message
                    instance.save()
                except ObjectDoesNotExist as e:
                    error_message = f"Object not found: {str(e)}"
                    instance.import_status = 3
                    instance.error_msg = error_message
                    instance.save()
                except Exception as e:
                    error_message = f"Unexpected error: {str(e)}"
                    instance.import_status = 3
                    instance.error_msg = error_message
                    instance.save()



        return Response({"message": f"Imported {len(updated_data)} Tag"},status=status.HTTP_200_OK)



class UploadTagStatusDataView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        import_id = random.randint(1000000, 9999999)
        tag_stone = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        if not csv_file:
            return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = csv_file.read().decode("utf-8").splitlines()
            csv_reader = csv.DictReader(data)
        except Exception:
            return Response({"error": "Invalid CSV file."}, status=status.HTTP_400_BAD_REQUEST)
            
        is_sub_design_req = int(RetailSettings.objects.get(name='is_sub_design_req').value)
        raw_data = []
        with transaction.atomic():
            for row in csv_reader:
                tag_code = row.get("TagCode").strip()
                old_tag_code = row.get("oldTagNo").strip()
                tag_status = 1
                updated_tag_status = 2
                is_imported = True
                error_message = ""
                tag_id = None
                log_id = None
                try :
                    if tag_code!='':
                        tag = ErpTagging.objects.filter(tag_code=tag_code).get()
                    elif old_tag_code!='':
                        tag = ErpTagging.objects.filter(old_tag_code=old_tag_code).get()
                    tag_status = tag.tag_status.pk
                    tag_id = tag.pk
                    if tag_status == 1:
                        tag.tag_status = ErpStockStatusMaster.objects.get(id_stock_status=2)
                        tag.save()
                        log = {
                                "date" : current_date,
                                "transaction_type": 9,
                                "from_branch_id": tag.tag_current_branch.pk,
                                "tag_id_id":tag.pk,
                                "id_stock_status_id":2,
                                "created_by_id":request.user.id,
                                "created_on":current_date,
                        }
                        log_id= insert_data_return_id('erp_tag_log_details',log)
                        is_imported = True
                        error_message = ""
                        raw_data.append(log_id)
                    else:
                        is_imported = True
                        tag_status_name = tag.tag_status.name
                        error_message = f"Invalid Tag Status : {tag_status_name}"
                except ErpTagging.DoesNotExist:
                    is_imported = False
                    error_message = f"Invalid TagCode : {tag_code}"
                except IntegrityError as e:
                    error_message = f"Database Integrity Error: {str(e)}"
                    is_imported = False
                except OperationalError as e:
                    error_message = f"Database Operational Error: {str(e)}"
                    is_imported = False
                except ObjectDoesNotExist as e:
                    error_message = f"Object not found: {str(e)}"
                    is_imported = False
                except Exception as e:
                    error_message = f"Unexpected error: {str(e)}"
                    is_imported = False


                insert_data ={
                    "tag_code": tag_code,
                    "old_tag_code": old_tag_code,
                    "tag_status": tag_status,
                    "import_id": import_id,
                    "tag_id":tag_id,
                    "error_msg": error_message,
                    "import_status": 1 if is_imported == True else 0,
                    "tag_updated_status": updated_tag_status,
                    "log_id": log_id,
                    "created_by_id": request.user.pk,
                    "created_on":now()
                }
                id= insert_data_return_id('tag_status_import',insert_data)




        return Response({"message": f"Imported {len(raw_data)} Tag"},status=status.HTTP_200_OK)


def insert_data_return_id(table_name, params):
    columns = ', '.join(params.keys())
    values = ', '.join([f"%({key})s" for key in params.keys()])    
    sql = f"""
        INSERT INTO {table_name} ({columns}) 
        VALUES ({values});
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        inserted_id = cursor.lastrowid  # Get the last inserted ID
        #connection.commit()  # Commit the transaction
    return inserted_id


class ImportEmployeesAPI(generics.GenericAPIView):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        updated = []
        if not csv_file:
            return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = csv_file.read().decode("utf-8").splitlines()
            csv_reader = csv.DictReader(data)
        except Exception:
            return Response({"error": "Invalid CSV file."}, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        dept = Department.objects.first()
        emp_type = EmployeeType.objects.first()
        profile = Profile.objects.get(id_profile = 3)
        country = Country.objects.first()
        state = State.objects.first()
        city = City.objects.first()
        area = Area.objects.first()
        for data in csv_reader:
            date_of_join = data.get("date_of_join").strip()
            if(date_of_join):
                date_obj = datetime.strptime(date_of_join, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%Y-%m-%d")
            else:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
            is_imported = True
            error_message = ""
            password = data.get("firstname").strip() +"@"+ data.get("emp_code").strip()
            #username = data.get("firstname").strip()
            username = (data.get("firstname") or "").strip().replace(" ", "")
            log_branch = checkbranch(self, [1])
                
            emp_code = data.get("emp_code").strip()

            
            if User.objects.filter(username=username).exists():
                return Response({"message": "Username already in use"}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                try:

                    import_data = {"firstname":data.get("firstname",'').strip(), "lastname": '', "date_of_join":formatted_date,
                        "emp_code":emp_code, "dept" : dept.pk, "designation":None, "email_verified":True,
                        "mobile": data.get("mobile",'').strip(),
                            "id_profile":profile.pk, "address1":data.get("address1",'').strip(),
                        "address2":data.get("address2",'').strip(),"address3":data.get("address3",'').strip(),
                        "country":country.pk, "state":state.pk, "city":city.pk,
                        "area":area.pk,"login_branches":[1],"created_by":request.user.pk,'created_on':now()}
                    user = User.objects.create(is_adminuser=True,email=None, 
                                        username = username, first_name= data.get("firstname",'').strip(),
                                        last_name='', account_expiry=date.today()+relativedelta(years=20))
                    user.set_password(password)
                    user.save()

                    import_data.update({"user":user.pk})

                    
                    emp = EmployeeSerializer(data=import_data)
                    emp.is_valid(raise_exception=True)
                    emp.save()

                    emp_settings_data = {"id_employee":emp.data['id_employee'], "disc_limit_type":"1","disc_limit":1,
                                        "allow_branch_transfer":False, "allow_day_close":False,"menu_style":1,
                                        "created_by":request.user.pk}
                    emp_settings = EmployeeSettingsSerializer(data = emp_settings_data)
                    emp_settings.is_valid(raise_exception=True)
                    emp_settings.save()
                    import_data.update({"is_imported":is_imported,"error_message":error_message})
                    updated.append(import_data)
                except IntegrityError as e:
                    error_message = f"Database Integrity Error: {str(e)}"
                    is_imported = False
                    import_data.update({"is_imported":is_imported,"error_message":error_message})
            employee_import = {
                "date_of_join":formatted_date,
                "lastname": data.get("lastname",'').strip(),
                "firstname": data.get("firstname",'').strip(),
                "emp_code": emp_code,
                "mobile": data.get("mobile",'').strip(),
                "address1":data.get("address1",'').strip(),
                "address2":data.get("address2",'').strip(),
                "address3":data.get("address3",'').strip(),
                "is_imported": is_imported,
                "error_message": error_message,
                "created_on":now(),
                # "created_by":request.user.pk, 
            }
            import_id= insert_data_return_id('employee_import',employee_import)
        return Response({"success": True,
                         "message": f"Employee created successfully{len(updated)}"},
                        status=status.HTTP_201_CREATED)


# class ImportSchemeAccountDetailsView(generics.GenericAPIView):
    
#     def post(self, request, *args, **kwargs):
#         csv_file = request.FILES.get("file")
#         import_id = random.randint(1000000, 9999999)
#         if not csv_file:
#             return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             data = csv_file.read().decode("utf-8").splitlines()
#             csv_reader = csv.DictReader(data)
#         except Exception:
#             return Response({"error": "Invalid CSV file."}, status=status.HTTP_400_BAD_REQUEST)
        
#         raw_data = []
#         raw_instance_data = []
#         saving_data = []
#         print(request.data['branch'])
#         with transaction.atomic():
#             for row in csv_reader:
#                 if(row['Chit No.'] == ''):
#                     del row
#                 else:
#                     raw_data.append(row)
#                 # raw_data.append(row)
#             for raw in raw_data:
#                 raw_instance = {}
#                 if(Customers.objects.filter(mobile=raw['Mobile No']).exists()):
#                     raw_instance['cus_pk'] = Customers.objects.get(mobile=raw['Mobile No']).pk
#                 else:
#                     user = User.objects.create(
#                             is_customer=True,
#                             username=raw['Mobile No'], 
#                             first_name=raw['Name'],
#                             )
#                     user.set_password(raw['Mobile No'])
#                     user.save()
#                     cus_instance = {
#                         "user": user.pk,
#                         'firstname':raw['Name'],
#                         'mobile':raw['Mobile No'],
#                         'email':None,
#                         'id_branch': request.data['branch'],
#                         'id_area':None,
#                         'title':None,
#                         'lastname':None,
#                         'date_of_birth':None,
#                         'date_of_wed':None,
#                         'gender':None,
#                         'cus_img':None,
#                         'comments':None,
#                         'profile_complete':None,
#                         'approved_status':2,
#                         'date_add':datetime.now(),
#                         'gst_number':None,
#                         'pan_number':None,
#                         'aadhar_number':None,
#                         'cus_ref_code':None,
#                         'is_refbenefit_crt_cus':None,
#                         'religion':None,
#                         'kyc_status':None,
#                         'last_sync_time':None,
#                         'last_payment_on':None,
#                         'registered_through':1,
#                     }
#                     customer_serializer = CustomerSerializer(data=cus_instance)
#                     customer_serializer.is_valid(raise_exception=True)
#                     customer_serializer.save()
#                     raw_instance['cus_pk'] = customer_serializer.data['id_customer']
                    
#                 if(Scheme.objects.filter(scheme_id=raw['Scheme']).exists()):
#                     raw_instance['scheme_pk'] = Scheme.objects.get(scheme_id=raw['Scheme']).pk
#                 else:
#                     raw_instance['scheme_pk'] = None
#                 unique_id = uuid.uuid4()
#                 # print(unique_id)
#                 raw_instance.update({
#                     'cus_name':raw['Name'],
#                     'cus_mobile':raw['Mobile No'],
#                     'scheme_acc_no':raw['Chit No.'],
#                     'installment_paid':raw['No.of Ins Paid'],
#                     'amount':raw['Amount '],
#                     'weight':raw['Wt'],
#                     'g_name':raw['G NAME'],
#                     'import_id':str(unique_id)
#                 })
#                 raw_data_serializer = RawSchemeAccountDataSerializer(data=raw_instance)
#                 raw_data_serializer.is_valid(raise_exception=True)
#                 raw_data_serializer.save()
#                 raw_instance.update({'id':raw_data_serializer.data['id']})
#                 if raw_instance not in raw_instance_data:
#                     raw_instance_data.append(raw_instance)
#             # print(raw_instance_data[0])      
#             with transaction.atomic():
#                 for data in raw_instance_data:
#                     # if(data['cus_pk'] == None):
#                         # user = User.objects.create(
#                         #     is_customer=True,
#                         #     username=data['cus_mobile'], 
#                         #     first_name=data['cus_name'],
#                         #     )
#                         # user.set_password(data['cus_mobile'])
#                         # user.save()
#                         # cus_instance = {
#                         #     "user": user.pk,
#                         #     'firstname':data['cus_name'],
#                         #     'mobile':data['cus_mobile'],
#                         #     'email':None,
#                         #     'id_branch': request.data['branch'],
#                         #     'id_area':None,
#                         #     'title':None,
#                         #     'lastname':None,
#                         #     'date_of_birth':None,
#                         #     'date_of_wed':None,
#                         #     'gender':None,
#                         #     'cus_img':None,
#                         #     'comments':None,
#                         #     'profile_complete':None,
#                         #     'approved_status':2,
#                         #     'date_add':datetime.now(),
#                         #     'gst_number':None,
#                         #     'pan_number':None,
#                         #     'aadhar_number':None,
#                         #     'cus_ref_code':None,
#                         #     'is_refbenefit_crt_cus':None,
#                         #     'religion':None,
#                         #     'kyc_status':None,
#                         #     'last_sync_time':None,
#                         #     'last_payment_on':None,
#                         #     'registered_through':1,

#                         # }
#                         # customer_serializer = CustomerSerializer(data=cus_instance)
#                         # customer_serializer.is_valid(raise_exception=True)
#                         # customer_serializer.save()
#                         # raw_scheme_Account = RawSchemeAccountData.objects.get(id=data['id'])
#                         # raw_scheme_Account.cus_pk=customer_serializer.data['id_customer']
#                         # raw_scheme_Account.save()
#                         # data.update({'cus_pk':customer_serializer.data['id_customer']})
#                     instance = {}
#                     instance.update({
#                        'acc_scheme_id':data['scheme_pk'],
#                        'id_customer':data['cus_pk'],
#                        'id_branch' : request.data['branch'],
#                        'account_name' : data['cus_name'],
#                        'old_scheme_acc_number' : data['scheme_acc_no'],
#                        'opening_balance_amount' : data['amount'],
#                        'opening_balance_weight' : data['weight'],
#                        'added_by':0,
#                        'scheme_acc_number':None
#                     })
#                     # print(instance)
#                     scheme_account_serializer = SchemeAccountSerializer(data=instance)
#                     scheme_account_serializer.is_valid(raise_exception=True)
#                     scheme_account_serializer.save()
#                     if instance not in saving_data:
#                         saving_data.append(instance)
#             # print(saving_data)
#             return Response({'message' : 'Chit datas imported successfully.'}, status=status.HTTP_201_CREATED)


class ImportSchemeAccountDetailsView(generics.GenericAPIView):
    
    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        import_id = random.randint(1000000, 9999999)

        if not csv_file:
            return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = csv_file.read().decode("utf-8").splitlines()
            csv_reader = csv.DictReader(data)
        except Exception:
            return Response({"error": "Invalid CSV file."}, status=status.HTTP_400_BAD_REQUEST)

        raw_data = []
        raw_instance_data = []
        saving_data = []

        with transaction.atomic():
            for row in csv_reader:
                if row['Chit No.'] != '':
                    raw_data.append(row)

            for raw in raw_data:
                raw_instance = {}

                try:
                    # Check if customer exists
                    if Customers.objects.filter(mobile=raw['Mobile No']).exists():
                        raw_instance['cus_pk'] = Customers.objects.get(mobile=raw['Mobile No']).pk
                    else:
                        # Create user and customer
                        # print(str(raw['S.No.'] + ' - ' + str(raw['Chit No.'])))
                        today = date.today()
                        expiry = today.replace(today.year + 5)
                        user = User.objects.create(
                            is_customer=True,
                            username=raw['Mobile No'],
                            first_name=raw['Name'],
                            account_expiry=expiry
                        )
                        user.set_password(raw['Mobile No'])
                        user.save()

                        cus_instance = {
                            "user": user.pk,
                            'firstname': raw['Name'],
                            'mobile': raw['Mobile No'],
                            'email': None,
                            'id_branch': request.data['branch'],
                            'id_area': None,
                            'title': None,
                            'lastname': None,
                            'date_of_birth': None,
                            'date_of_wed': None,
                            'gender': None,
                            'cus_img': None,
                            'comments': None,
                            'profile_complete': None,
                            'approved_status': 2,
                            'date_add': datetime.now(),
                            'gst_number': None,
                            'pan_number': None,
                            'aadhar_number': None,
                            'cus_ref_code': None,
                            'is_refbenefit_crt_cus': None,
                            'religion': None,
                            'kyc_status': None,
                            'last_sync_time': None,
                            'last_payment_on': None,
                            'registered_through': 1,
                        }

                        customer_serializer = CustomerSerializer(data=cus_instance)
                        customer_serializer.is_valid(raise_exception=True)
                        customer_serializer.save()
                        raw_instance['cus_pk'] = customer_serializer.data['id_customer']

                except serializers.ValidationError as e:
                    return Response({
                        "error": "Validation error while creating customer.",
                        "mobile": raw.get("Mobile No", "Unknown"),
                        "details": e.detail
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Fetch scheme
                if Scheme.objects.filter(scheme_id=raw['Scheme']).exists():
                    raw_instance['scheme_pk'] = Scheme.objects.get(scheme_id=raw['Scheme']).pk
                else:
                    raw_instance['scheme_pk'] = None

                unique_id = uuid.uuid4()
                raw_instance.update({
                    'cus_name': raw['Name'],
                    'cus_mobile': raw['Mobile No'],
                    'scheme_acc_no': raw['Chit No.'],
                    'installment_paid': raw['No.of Ins Paid'],
                    'amount': raw['Amount '],
                    'weight': raw['Wt'],
                    'g_name': raw['G NAME'],
                    'import_id': str(unique_id)
                })

                try:
                    raw_data_serializer = RawSchemeAccountDataSerializer(data=raw_instance)
                    raw_data_serializer.is_valid(raise_exception=True)
                    raw_data_serializer.save()
                    raw_instance['id'] = raw_data_serializer.data['id']
                    raw_instance_data.append(raw_instance)
                except serializers.ValidationError as e:
                    return Response({
                        "error": "Validation error while saving raw scheme data.",
                        "mobile": raw.get("Mobile No", "Unknown"),
                        "details": e.detail
                    }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                for data in raw_instance_data:
                    instance = {
                        'acc_scheme_id': data['scheme_pk'],
                        'id_customer': data['cus_pk'],
                        'old_paid_ins': data['installment_paid'],
                        'total_paid_ins': data['installment_paid'],
                        'id_branch': request.data['branch'],
                        'account_name': data['cus_name'],
                        'old_scheme_acc_number': data['scheme_acc_no'],
                        'opening_balance_amount': data['amount'],
                        'opening_balance_weight': data['weight'],
                        'added_by': 0,
                        'scheme_acc_number': None
                    }

                    try:
                        scheme_account_serializer = SchemeAccountSerializer(data=instance)
                        scheme_account_serializer.is_valid(raise_exception=True)
                        scheme_account_serializer.save()
                        saving_data.append(instance)
                    except serializers.ValidationError as e:
                        return Response({
                            "error": "Validation error while creating scheme account.",
                            "mobile": data.get("cus_mobile", "Unknown"),
                            "details": e.detail
                        }, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Chit datas imported successfully.'}, status=status.HTTP_201_CREATED)
    
# class UpdateInstallmentOfImportDatas(generics.GenericAPIView):
    
#     def get(self, request, *args, **kwargs):
#         queryset = SchemeAccount.objects.all()
#         serializer = SchemeAccountSerializer(queryset, many=True)
#         raw_queryset = RawSchemeAccountData.objects.all()
#         raw_serializer = RawSchemeAccountDataSerializer(raw_queryset, many=True)
#         for data in serializer.data:
#             for raw_data in raw_serializer.data:
#                 if data['old_scheme_acc_number'] == raw_data['scheme_acc_no']:
#                     SchemeAccount.objects.filter(id_scheme_account=data['id_scheme_account']).update(
#                         total_paid_ins = raw_data['installment_paid'],
#                         old_paid_ins = raw_data['installment_paid'],
#                     )
#         return Response({'message':'Installments updated'})