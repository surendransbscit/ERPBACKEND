from django.shortcuts import render
from django.http import HttpResponse, request, Http404
from rest_framework import generics, permissions, status , serializers
from django.forms.models import model_to_dict
from rest_framework.response import Response
from django.db.models import Q
from django.utils.timezone import now
import calendar
import subprocess
from django.utils.module_loading import import_string
from django.conf import settings
import os
from django.db.models.functions import ExtractMonth
from datetime import datetime, timedelta, date
from django.db import transaction , IntegrityError,DatabaseError,OperationalError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count,Value,PositiveIntegerField,IntegerField
from decimal import Decimal

from retailsettings.models import (RetailSettings)
from retailcataloguemasters.models import ErpReorderSettings,Product,MakingAndWastageSettings
from managescheme.models import (SchemeAccount)
from managescheme.serializers import (SchemeAccountSerializer)
from customerorder.models import (ERPOrder, ERPOrderDetails, ERPOrderImages, ErpJobOrderDetails, ErpJobOrder)
from managescheme.views import (SchemeAccountPaidDetails)
from customerorder.serializers import (ErpOrdersSerializer, ErpOrdersDetailSerializer, ErpOrderImagesSerializer,
                                       ErpJobOrderSerializer, ErpJobOrderDetailSerializer)
from customers.models import (CustomerAddress, Customers)
from customers.serializers import (CustomerAddressSerializer, CustomerSerializer)
from schememaster.models import Scheme,SchemeDigiGoldInterestSettings
from schemepayment.models import Payment,PaymentModeDetail
from schemepayment.serializers import PaymentSerializer
from retailmasters.models import (IncentiveTransactions,IncentiveSettings,WeightRange,Size,Supplier, Branch,Metal,
                                  PaymentMode,CashOpeningBalance,Profile,BankDeposit, ERPOrderStatus, FinancialYear)
from inventory.models import (ErpTagging,ErpTaggingLogDetails,ErpTaggingImages,ErpTagScan,ErpTagScanDetails,
                              ErpTaggingStone, ErpLotInwardDetails, ErpTaggingLogDetails , ErpLotMergeDetails , ErpLotMerge)
from inventory.serializers import (ErpTaggingSerializer,ErpTaggingImagesSerializer, ErpTagStoneSerializer,
                                   ErpTaggingLogSerializer)
from retailcataloguemasters.serializers import (MetalSerializer)
from branchtransfer.models import ErpStockTransfer,ErpTagTransfer,ErpNonTagTransfer
from branchtransfer.serializers import ErpStockTransferSerializer,ErpNonTagTransferSerializer
from billing.models import (ErpInvoice,ErpInvoiceSalesDetails,ErpInvoiceOldMetalDetails,ErpInvoiceSalesReturn,ErpItemDelivered,
                            ErpInvoicePaymentModeDetail,ErpIssueReceiptPaymentDetails,ErpIssueReceipt,ErpReceiptAdvanceAdj,
                            ErpInvoiceSchemeAdjusted,ErpReceiptCreditCollection,ErpReceiptAdvanceAdj,ErpInvoiceGiftDetails,
                            ErpInvoiceDiscountSalesDetails,ErpInvoiceDiscountOldMetalDetails,ErpInvoiceDiscount, ErpAdvanceAdj,
                            ErpLiablityEntry)
from billing.serializers import (ErpInvoiceSerializer,ErpInvoiceSalesDetailsSerializer,ErpInvoiceOldMetalDetailsSerializer,ErpItemDeliveredSerializer,
                                 ErpIssueReceiptSerializer,ErpReceiptCreditCollectionSerializer,ErpInvoicePaymentModeDetailSerializer,
                                 ErpInvoiceDiscountSerializer,ErpInvoiceDiscountOldMetalDetailsSerializer,
                                 ErpInvoiceSalesDiscountDetailsSerializer,ErpIssueReceiptPaymentDetailsSerializer, ErpAdvanceAdjSerializer)
from estimations.models import (ErpEstimation,ErpEstimationSalesDetails,ErpEstimationOldMetalDetails,ErpEstimationSalesReturnDetails)
from estimations.serializers import (ErpEstimationSalesReturnSerializer,ErpEstimationSalesDetailsSerializer,ErpEstimationOldMetalDetailsSerializer)
from .constants import *
from utilities.constants import FILTERS
from utilities.pagination_mixin import PaginationMixin
pagination = PaginationMixin()  # Apply pagination
from django.db.models import Q, OuterRef, Exists, DecimalField,ExpressionWrapper
from inventory.models import ErpTagging,ErpTaggingLogDetails,ErpTaggingImages,ErpTagScan,ErpTagScanDetails,ErpLotNonTagInwardDetails
from inventory.serializers import ErpTaggingSerializer,ErpTaggingImagesSerializer
from branchtransfer.models import ErpStockTransfer,ErpTagTransfer,ErpNonTagTransfer
from branchtransfer.serializers import ErpStockTransferSerializer,ErpNonTagTransferSerializer
from billing.models import ErpInvoice,ErpInvoiceSalesDetails,ErpInvoiceOldMetalDetails,ErpInvoiceSalesReturn,ErpInvoicePaymentModeDetail,ErpIssueReceiptPaymentDetails,ErpIssueReceipt,ErpReceiptAdvanceAdj,ErpInvoiceSchemeAdjusted,ErpReceiptCreditCollection,ErpReceiptAdvanceAdj,ErpReceiptRefund
from billing.serializers import get_bill_no,ErpInvoiceSerializer,ErpInvoiceSalesDetailsSerializer,ErpInvoiceOldMetalDetailsSerializer,ErpIssueReceiptSerializer,ErpReceiptCreditCollectionSerializer,ErpReceiptAdvanceAdjSerializer,ErpInvoiceSchemeAdjustedSerializer,ErpReceiptRefundSerializer,ErpInvoiceSalesReturnSerializer,ErpIssueReceiptSerializer
from billing.views import get_invoice_no
from retailmasters.views import BranchEntryDate
from oldmetalprocess.models import ErpMetalProcess
# from oldmetalprocess.serializer import ErpMetalProcessSerializer
from retailmasters.serializers import (BankDepositSerializer,IncentiveTransactionsSerializer, FinancialYearSerializer)
from retailmasters.constants import (FIN_YEAR_ACTION_LIST, FIN_YEAR_COLUMN_LIST)
from retailpurchase.models import (ErpPurchaseEntry, ErpAccountStockProcessDetails, ErpSupplierPaymentModeDetail,
                                   ErpSupplierMetalIssueDetails, ErpPurchaseReturnDetails, ErpPurchaseReturn, ErpPurchaseReturnStoneDetails)
from  utilities.constants import (  ITEM_TYPE_CHOICES )
import traceback
from utilities.utils import train_sales_model,predict_future_sales,dynamic_predict_future_sales,format_number_with_decimal,generate_query_result,grand_total_data
# import pandas as pd
import copy
from collections import defaultdict
from core.views  import get_reports_columns_template
from django.utils.timezone import make_aware
from core.models import ReportColumnsTemplates,Employee
from retailpurchase.serializers import (ErpSupplierPaymentModeDetailSerializer, ErpPurchaseReturnDetailsSerializer, ErpPurchaseReturnSerializer)
from django.db.models.functions import Coalesce
from billing.views import (generate_issue_receipt_billno, insert_other_details)

class GeneralDataSerializer(serializers.Serializer):
    key = serializers.CharField()
    another_key = serializers.CharField()

from django.db import connection
from django import forms
from customers.models import (Customers)
from django.db.models import  Sum, F, When, Case,Avg
from utilities.utils import format_date,format_data_with_decimal,date_format_with_time

from branchtransfer.views import get_status_color


from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee,isSuperuser
import json

# FILTERS = {}

def call_stored_procedure(proc_name, *args):
    """
    Call a stored procedure
    :param proc_name: Name of the stored procedure
    :param args: Arguments to pass to the stored procedure
    """
    try:
        with connection.cursor() as cursor:
            print(args,"args")
            placeholders = ', '.join(['%s'] * len(args))
            proc_call = f"CALL {proc_name}({placeholders})"
            print(proc_call,placeholders)

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
        print(connection.queries[-1]['sql'])

        if 'does not exist' in str(e):
            raise Exception(f"Error: Stored Procedure '{proc_name}' does not exist.")
            #return Response({"error": f"Error: Stored Procedure '{proc_name}' does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(connection.queries[-1]['sql'])
            raise e
    except DatabaseError as e:
        print(connection.queries[-1])

        raise Exception(f"Database error occurred: {connection.queries[-1]} : {str(e)}")
        #return Response({"error": f"Database error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


def get_customer_financials(customer_id):
    outstanding_amount = 0  # Initialize outstanding amount
    advance_in_hand = 0  # Initialize advance in hand

    # Get credit (Outstanding Amount)
    credit_queryset = ErpIssueReceipt.objects.filter(customer=customer_id, issue_type=1, bill_status=1)
    credit_serializer = ErpIssueReceiptSerializer(credit_queryset, many=True).data

    for credits in credit_serializer:
        received_amount = 0
        issued_amount = float(credits['amount'])
        balance_amount = 0

        col = ErpReceiptCreditCollection.objects.filter(issue=credits['id'], receipt__bill_status=1)
        col_data = ErpReceiptCreditCollectionSerializer(col, many=True).data

        for collection in col_data:
            received_amount += float(collection['received_amount']) + float(collection['discount_amount'])

        balance_amount = issued_amount - received_amount
        if balance_amount > 0:
            outstanding_amount += balance_amount

    # Get advance amount (Advance in Hand)
    adv_queryset = ErpIssueReceipt.objects.filter(customer=customer_id, receipt_type__in=[1, 2, 3, 4], bill_status=1)
    adv_serializered_data = ErpIssueReceiptSerializer(adv_queryset, many=True).data

    for adv_data in adv_serializered_data:
        refunded_amount = 0
        adjusted_amount = 0
        advance_amount = float(adv_data['amount'])
        balance_amount = 0

        refund = ErpReceiptRefund.objects.filter(receipt=adv_data['id'], issue__bill_status=1)
        refund_data = ErpReceiptRefundSerializer(refund, many=True).data
        for ref in refund_data:
            refunded_amount += float(ref['refund_amount'])

        adjusted = ErpReceiptAdvanceAdj.objects.filter(receipt=adv_data['id'], invoice_bill_id__invoice_status=1)
        adjusted_data = ErpReceiptAdvanceAdjSerializer(adjusted, many=True).data
        for adj in adjusted_data:
            adjusted_amount += float(adj['adj_amount'])

        twod_adjusted = ErpAdvanceAdj.objects.filter(receipt=adv_data['id'], invoice_bill_id__invoice_status=1)
        twod_adjusted_data = ErpAdvanceAdjSerializer(twod_adjusted, many=True).data
        for adj in twod_adjusted_data:
            adjusted_amount += float(adj['adj_amount'])

        balance_amount = advance_amount - refunded_amount - adjusted_amount
        advance_in_hand += balance_amount

    return advance_in_hand, outstanding_amount

# from retail masters views
class FinancialYearListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = FinancialYear.objects.all()
    serializer_class = FinancialYearSerializer
    
    def export_and_create_db(self, fin_year_code):
        print(f"\n===== [START] Export and Create DB for {fin_year_code} =====")

        # Load Django settings
        settings_module = os.getenv('DJANGO_SETTINGS_MODULE', 'jewelry_retail_api.settings.development')
        settings = import_string(settings_module)

        # Step 1: Get database credentials
        db_config = settings.DATABASES.get('default', {})
        db_name = db_config.get('NAME','sds')
        db_user = db_config.get('USER','root')
        db_password = db_config.get('PASSWORD','')
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '3306')

        print(f" Database Name: {db_name}")
        print(f" Database User: {db_user}")
        print(f" Database Host: {db_host}")
        print(f" Database Port: {db_port}")
        print(f" Database PWD: {db_password}")

        if not db_name or not db_user:
            print(" Database configuration missing!")
            return Response({"error": "Database configuration is missing"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 2: Define file paths
        save_dir = os.path.join(settings.MEDIA_ROOT, 'exported_sql', f'{fin_year_code}')
        os.makedirs(save_dir, exist_ok=True)  # Ensure directory exists

        sql_file = os.path.join(save_dir, f"{db_name}_{fin_year_code}.sql")
        print(f" SQL Export File: {sql_file}")

        # Step 3: Export current DB as SQL file
        dump_command = [
                "mysqldump", "--single-transaction", "--quick", "--verbose",  
                "-u", db_user, "-h", db_host, "-P", str(db_port), db_name
            ]

        env = os.environ.copy()
        env["MYSQL_PWD"] = db_password  # Securely pass the password

        try:
            print(" Exporting database (this may take time)...")
            with open(sql_file, 'w', encoding='utf-8') as output_file:
                process = subprocess.Popen(dump_command, stdout=output_file, stderr=subprocess.PIPE, text=True, env=env)
                # Debug: Print live stderr output
                for line in process.stderr:
                    print(f" Dump Error: {line.strip()}")
                process.wait(timeout=120)  # Increased timeout
                
            if process.returncode == 0:
                print(" Database export successful!")
            else:
                print(" Database export failed!")
                return Response({"error": "Database export failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except subprocess.TimeoutExpired:
            print(" Database export timed out! Try checking MySQL logs.")
            return Response({"error": "Database export timed out"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(f" Failed to export database: {e}")
            return Response({"error": "Failed to export database", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # # Step 4: Create a new database
        # new_db_name = f"{db_name}_cloned_{fin_year_code}"
        # create_db_command = ["mysql", "-u", db_user, "-h", db_host, "-P", str(db_port), "-e", f"CREATE DATABASE {new_db_name};"]

        # try:
        #     print(f" Creating new database: {new_db_name}")
        #     process = subprocess.Popen(create_db_command, stderr=subprocess.PIPE, text=True, env=env)

        #     for line in process.stderr:
        #         print(f" DB Creation Error: {line.strip()}")

        #     process.wait(timeout=30)

        #     if process.returncode == 0:
        #         print(f" Database {new_db_name} created successfully!")
        #     else:
        #         print(" Database creation failed!")
        #         return Response({"error": "Database creation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except subprocess.TimeoutExpired:
        #     print(" Database creation timed out!")
        #     return Response({"error": "Database creation timed out"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     print(f" Failed to create new database: {e}")
        #     return Response({"error": "Failed to create new database", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # # Step 5: Import the exported SQL file into the new database
        # import_command = ["mysql", "-u", db_user, "-h", db_host, "-P", str(db_port), new_db_name]

        # try:
        #     print(" Importing data into new database...")
        #     with open(sql_file, 'r') as input_file:
        #         process = subprocess.Popen(import_command, stdin=input_file, stderr=subprocess.PIPE, text=True, env=env)

        #         for line in process.stderr:
        #             print(f" Import Error: {line.strip()}")

        #         process.wait(timeout=90)

        #     if process.returncode == 0:
        #         print(" Database import successful!")
        #     else:
        #         print(" Database import failed!")
        #         return Response({"error": "Database import failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except subprocess.TimeoutExpired:
        #     print(" Database import timed out!")
        #     return Response({"error": "Database import timed out"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # except Exception as e:
        #     print(f" Failed to import data into new database: {e}")
        #     return Response({"error": "Failed to import data into new database", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # print(f" Successfully created and imported {new_db_name}")
        print("===== [END] Export =====")

        return Response({"success": f"Database exported successfully!"}, status=status.HTTP_200_OK)

    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = FinancialYear.objects.filter(fin_status=1)
            serializer = FinancialYearSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        queryset = FinancialYear.objects.all().order_by('-pk')
        paginator, page = pagination.paginate_queryset(queryset, request,None,FIN_YEAR_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,FIN_YEAR_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['fin_id'], "sno": index+1})
            data.update({"fin_year_from": format_date(data['fin_year_from']), "fin_year_to": format_date(
                data['fin_year_to']), "is_active": data['fin_status']})
        context = {'columns': columns, 'actions': FIN_YEAR_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        reset_db_on_finyear_change = int(RetailSettings.objects.get(name='reset_db_on_finyear_change').value)        
            # Ensures rollback if any step fails
        if (reset_db_on_finyear_change != 1):
            try:
                with transaction.atomic():
                    request.data.update({"created_by": request.user.id, "fin_status": True})
                    active_fin_year = FinancialYear.objects.filter(fin_status=True).first()
                    if not active_fin_year:
                        print("No active financial year found")  
                        return Response({"error": "No active financial year found"}, status=status.HTTP_400_BAD_REQUEST)
                    print("Setting all financial years to inactive")  
                    FinancialYear.objects.all().update(fin_status=False)
        
                    print("Saving new financial year")  
                    serializer = FinancialYearSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response({"error": "Database integrity error", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except DatabaseError as e:
                return Response({"error": "Database operation failed", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                print(f"Error occurred: {e}, rolling back transaction")  
                return Response({"message": "Duplicate Fin year or Fin Code ", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                with transaction.atomic():
                    print("Inside transaction block")  
                    request.data.update({"created_by": request.user.id, "fin_status": True})
        
                    customers = Customers.objects.all()
                    print(f"Total customers found: {customers.count()}")  
        
                    customer_updates = []
                    for customer in customers:
                        print(f"Processing customer: {customer.id_customer}")  
                        advance_in_hand, outstanding_amount = get_customer_financials(customer.id_customer)
                        customer.debit_balance = outstanding_amount
                        customer.credit_balance = advance_in_hand
                        customer_updates.append(customer)
        
                    # Bulk update customers
                    Customers.objects.bulk_update(customer_updates, ['debit_balance', 'credit_balance'])
                    print("Bulk update completed")  
        
                    active_fin_year = FinancialYear.objects.filter(fin_status=True).first()
                    if not active_fin_year:
                        print("No active financial year found")  
                        return Response({"error": "No active financial year found"}, status=status.HTTP_400_BAD_REQUEST)
        
                    print(f"Calling export_and_create_db with fin_year_code: {active_fin_year.fin_year_code}")  
        
                    # Call export_and_create_db and check response
                    response = self.export_and_create_db(fin_year_code=active_fin_year.fin_year_code)
                    if response.status_code != 200:
                        print("export_and_create_db failed, rolling back transaction")
                        return response  # Return error response from function
        
                    print("Setting all financial years to inactive")  
                    FinancialYear.objects.all().update(fin_status=False)
        
                    print("Saving new financial year")  
                    serializer = FinancialYearSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
        
                    # **TRUNCATE TABLES BEFORE INSERTING NEW DATA**
                    tables_to_truncate = [
                        "erp_issue_receipt_payment_details",
                        "erp_receipt_credit_collection",
                        "erp_receipt_refund",
                        "erp_advance_adj",
                        "erp_issue_receipt",
                    ]
        
                    with connection.cursor() as cursor:
                        for table in tables_to_truncate:
                            cursor.execute(f"DELETE FROM {table};")
                            print(f"Table {table} DELETED.")
        
                    # **INSERT DATA BASED ON CREDIT/DEBIT BALANCES**
                    for cus in customer_updates:
                        #print(cus)
                        fy = FinancialYear.objects.filter(fin_id=serializer.data['fin_id']).first()
                        branch = Branch.objects.filter(id_branch=cus.id_branch).first()
                        branch_date = BranchEntryDate()
                        entry_date = branch_date.get_entry_date(branch.pk)
                        # print(request.user)
                        if cus.credit_balance:
                            bill_no = generate_issue_receipt_billno({'branch': branch.pk, 'type': 1}, branch.short_name, fy, 1)
                            deposit_details = {
                                'type': 2, 'issue_type': 4, 'fin_year': serializer.data['fin_id'], 'bill_date': entry_date,
                                'branch': branch.pk, 'bill_no': bill_no, 'customer': cus.id_customer, 'deposit_bill': None,
                                'amount': cus.credit_balance, 'weight': 0, "created_by": request.user.id,
                                'remarks': "Opening Balance", 'ref_id': None
                            }#"employee": request.user.id, throw error
                            insert_other_details([deposit_details], ErpIssueReceiptSerializer, None)
        
                        if cus.debit_balance:
                            bill_no = generate_issue_receipt_billno({'branch': branch.pk, 'type': 2}, branch.short_name, fy, 2)
                            deposit_details = {
                                'type': 2, 'receipt_type': 4, 'fin_year': serializer.data['fin_id'], 'bill_date': entry_date,
                                'branch': branch.pk, 'bill_no': bill_no, 'customer': cus.id_customer, 'deposit_bill': None,
                                'amount': cus.debit_balance, 'weight': 0, "created_by": request.user.id,
                                'remarks': "Opening Balance", 'ref_id': None
                                #"employee": request.user.erpemployee,
                            }
                            insert_other_details([deposit_details], ErpIssueReceiptSerializer, None)

                    #SETIING OPENING FOR SUPPLIER 

                    metals = Metal.objects.all()
                    branch_query = Branch.objects.filter(is_ho = True).get()
                    branch_date = BranchEntryDate()
                    op_date = branch_date.get_entry_date(branch_query.id_branch)
                    branch = None
                    opening_details = []
                    for metal in metals:
                        opening = get_supplier_balance(metal.pk,op_date)
                        opening_details = opening_details + opening
                    opening_insert_detail = []
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM  erp_purchase_supplier_opening")
                    for opening in opening_details:
                        data ={
                            "id_supplier_id": opening['id_supplier'],
                            "id_metal_id": opening['id_metal'],
                            "entry_date":op_date,
                            "id_branch_id": branch,
                            "weight": opening['balance_weight'],
                            "amount": opening['balance_amount'],
                            "created_on" : now(),
                            "created_by_id" : request.user.id,
                            "updated_by_id":None,
                            "updated_on":None,
                        }
                        id= insert_data_return_id('erp_purchase_supplier_opening',data)
                        

                    
                    #DELETE BILLING DETAILS
                    
                    tables_to_truncate = [

                        "erp_purchase_return__stone_details",
                        "erp_purchase_return_details",
                        "erp_purchase_return",
                        "erp_purchase_item_charges_details",
                        "erp_account_stock_process_details",
                        "erp_account_stock_process",
                        "erp_supplier_metal_issue_details",
                        "erp_supplier_metal_issue",

                        "erp_rate_cut",
                        "erp_supplier_payment_mode",
                        "erp_supplier_payment_details",
                        "erp_supplier_payment",
                        "erp_purchase_issue_receipt_other_metal",
                        "erp_purchase_issue_receipt_stone_details",
                        "erp_purchase_item_issue_receipt_details",
                        "erp_purchase_item_issue_receipt",

                        "erp_purchase_other_metal",
                        "erp_purchase_stone_details",
                        "erp_purchase_item_details",
                        "erp_purchase_entry",


                        "erp_transfer_partly_sale_stone",
                        "erp_transfer_partly_sale_item",
                        "erp_transfer_sales_return_item",
                        "erp_transfer_old_metal_item",
                        "erp_transfer_non_tag_stn_item",
                        "erp_transfer_non_tag_item",
                        "erp_transfer_tag_item",
                        "erp_stock_transfer",
                        "erp_refining_receipt_details",
                        "erp_refining_details",
                        "erp_refining",
                        "erp_testing_details",
                        "erp_melting_receipt_details",
                        "erp_melting_issue_details",
                        "erp_metal_process",
                        "erp_pocket_stone_details",
                        "erp_pocket_other_metal",
                        "erp_pocket_details",
                        "erp_pocket",
                        "erp_customer_deposit_payment",
                        "erp_customer_deposit_items",
                        "erp_customer_deposit",
                        "erp_customer_sales_log",
                        "erp_incentive_transaction",
                        "erp_estimation_charges_details",
                        "erp_estimation_stone_details",
                        "erp_est_scheme_adjusted_details",
                        "erp_est_other_metal",                    
                        "erp_estimation_old_metal_details",
                        "erp_estimation_sales_details",
                        "erp_estimation_sales_return_details",                    
                        "erp_estimation",
                        "erp_invoice_sales_return_details",
                        "erp_invoice_payment_details",
                        "erp_invoice_stone_details",
                        "erp_invoice_charges_details",
                        "erp_invoice_other_metal",
                        "erp_item_delivered_images",
                        "erp_item_delivered",
                        "erp_invoice_sales_details",
                        "erp_invoice_old_metal_details",
                        "erp_invoice_scheme_adjusted_details",
                        "erp_invoice",
                        "erp_tag_scan_details",
                        "erp_tag_scan",
                    ]
                    
                    with connection.cursor() as cursor:
                        #SET NULL BEFORE DELETE
                        cursor.execute(f"UPDATE `erp_order_details` SET `erp_tag_id` = NULL WHERE erp_tag_id in (SELECT tag_id FROM erp_tagging WHere tag_status_id != 1);")
                        cursor.execute(f"UPDATE `erp_pocket_details` SET `invoice_sale_item_id_id` = NULL and `invoice_old_metal_item_id_id` = NULL and `invoice_return_id_id` = NULL")
                        cursor.execute(f"UPDATE `erp_account_stock_process_details` SET `invoice_sale_item_id_id` = NULL and `invoice_old_metal_item_id_id` = NULL and `invoice_return_id_id` = NULL")
                        cursor.execute(f"UPDATE `erp_lot_inward_details` SET `purchase_entry_detail_id` = NULL")
                        cursor.execute(f"UPDATE `erp_lot_inward_stone_details` SET `purchase_stn_detail_id` = NULL")

                        for table in tables_to_truncate:
                            cursor.execute(f"DELETE FROM {table};")
                            print(f"Table {table} truncated.")
                        cursor.execute(f"DELETE FROM  erp_tag_stone WHere tag_id_id in (SELECT tag_id FROM erp_tagging WHere tag_status_id != 1);")
                        cursor.execute(f"DELETE FROM  erp_tagging_images WHere erp_tag_id in (SELECT tag_id FROM erp_tagging WHere tag_status_id != 1);")
                        cursor.execute(f"DELETE FROM  erp_tag_other_metal WHere tag_id_id in (SELECT tag_id FROM erp_tagging WHere tag_status_id != 1);")
                        cursor.execute(f"DELETE FROM  erp_tag_charges_details WHere tag_id_id in (SELECT tag_id FROM erp_tagging WHere tag_status_id != 1);")
                        cursor.execute(f"DELETE FROM  erp_tag_log_details")
                        cursor.execute(f"DELETE FROM  erp_tag_container_log_details WHere tag_id in (SELECT tag_id FROM erp_tagging WHere tag_status_id != 1);")
                        cursor.execute(f"DELETE FROM  erp_attribute_details WHere tag_id_id in (SELECT tag_id FROM erp_tagging WHere tag_status_id != 1);")
                        cursor.execute(f"DELETE FROM  erp_tagging WHere tag_status_id != 1")
                        
                        cursor.execute(f"""
                            INSERT INTO erp_tag_log_details (date, transaction_type, to_branch_id,tag_id_id,id_stock_status_id,created_by_id,created_on)
                            SELECT 
                                day_close.entry_date as date,
                                1 as transaction_type,
                                tag_current_branch_id as to_branch_id,
                                tag_id as tag_id_id,
                                1 as id_stock_status_id,
                                {request.user.id} as created_by_id,
                                day_close.entry_date as created_on
                            FROM erp_tagging
                            LEFT JOIN erp_day_closing day_close ON day_close.id_branch_id = tag_current_branch_id
                            ;""")

                    

                    print("Returning response")  
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
        
            except Exception as e:
                print(f"Error occurred: {e}, rolling back transaction")  
                return Response({"error": "Internal Server Error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CollectionReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        from_date = request.data['from_date']
        to_date = request.data['to_date']
        id_scheme = request.data['id_scheme']
        id_branch = request.data['id_branch']
        id_scheme = (id_scheme) if id_scheme != '' else 0   
        id_branch = (id_branch) if id_branch != '' else 0

        payment_modes = PaymentMode.objects.filter(is_active=True).values('id_mode', 'mode_name', 'short_code')

        payment_mode_totals = {mode['short_code']: 0 for mode in payment_modes}

        collection_report = call_stored_procedure('GetCollectionReport', from_date, to_date, id_branch, id_scheme)

        scheme_data = {}
        grand_total = {"amount": 0, "rate": 0, "weight": 0}

        for result in collection_report['report_data']:
            scheme_name = result['scheme_name']
            if scheme_name not in scheme_data:
                scheme_data[scheme_name] = {
                    "data": [],
                    "sub_total": {"amount": 0, "rate": 0, "weight": 0, "discount": 0, "netamnt": 0}
                }

            formatted_result = {
                "receipt_no": result['receipt_no'],
                "entry_date": result['entry_date'],
                "cus_name": result['cus_name'],
                "scheme_name": result['scheme_name'],
                "mobile": result['mobile'],
                "paid_through": result['paid_through'],
                "emp_name": result['emp_name'],
                "scheme_acc_number": result['scheme_acc_number'],
                "amount": float(result["payment_amount"]),
                "discountAmt": float(result["discountAmt"]),
                "net_amount": float(result["net_amount"]),
                "rate": float(result["metal_rate"]),
                "weight": float(result["metal_weight"]),
            }

            scheme_data[scheme_name]["data"].append(formatted_result)
            scheme_data[scheme_name]["sub_total"]["amount"] += formatted_result["amount"]
            scheme_data[scheme_name]["sub_total"]["rate"] += formatted_result["rate"]
            scheme_data[scheme_name]["sub_total"]["weight"] += formatted_result["weight"]
            scheme_data[scheme_name]["sub_total"]["discount"] += formatted_result["discountAmt"]
            scheme_data[scheme_name]["sub_total"]["netamnt"] += formatted_result["net_amount"]

            grand_total["amount"] += formatted_result["amount"]
            grand_total["rate"] += formatted_result["rate"]
            grand_total["weight"] += formatted_result["weight"]

            payment_mode_detail = result.get("paid_through", None)
            if payment_mode_detail:
                for mode in payment_modes:
                    if payment_mode_detail == mode['id_mode']:
                        payment_mode_totals[mode['mode_name']] += formatted_result["amount"]

        response_data = {
            "schemes": [],
            "grand_total": grand_total,
            "payment_mode_totals": payment_mode_totals,
        }

        for scheme_name, data in scheme_data.items():
            scheme_entry = {
                "scheme_name": scheme_name,
                "sub_total": data["sub_total"],
                "transactions": data["data"]
            }
            response_data["schemes"].append(scheme_entry)

        return Response(response_data, status=status.HTTP_200_OK)


class ChitCustomerReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        try:
            year = request.data.get('year')
            if not year:
                return Response({'error': 'Year is required'}, status=status.HTTP_400_BAD_REQUEST)
            year = int(year)
            month_names = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            response_data = []
            schemes = Scheme.objects.all()
            for scheme in schemes:
                scheme_accounts = SchemeAccount.objects.filter(acc_scheme_id=scheme)
                month_counts = {f'{month}_count': 0 for month in month_names}

                for month in range(1, 13):
                    customers_in_month = Customers.objects.filter(
                        custom_entry_date__year=year,
                        custom_entry_date__month=month
                    )
                    scheme_customers_in_month = scheme_accounts.filter(
                        id_customer__in=customers_in_month.values_list('id_customer', flat=True)
                    )
                    month_counts[f'{month_names[month-1]}_count'] = scheme_customers_in_month.count()
                response_data.append({
                    "scheme_name": scheme.scheme_name,
                    "datas": [{
                        "year": year,
                        **month_counts
                    }]
                })
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class MonthwiseSchemeCollectionReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        try:
            year = int(request.data.get('year'))
            response_data = []
            schemes = Scheme.objects.all()
            for scheme in schemes:
                scheme_data = {}
                scheme_data['scheme_name'] = scheme.scheme_name
                scheme_data['datas'] = []
                monthly_totals = {
                    'jan_total': 0,
                    'feb_total': 0,
                    'mar_total': 0,
                    'apr_total': 0,
                    'may_total': 0,
                    'jun_total': 0,
                    'jul_total': 0,
                    'aug_total': 0,
                    'sep_total': 0,
                    'oct_total': 0,
                    'nov_total': 0,
                    'dec_total': 0,
                }
                payments = Payment.objects.filter(id_scheme=scheme, entry_date__year=year)
                for month in range(1, 13):
                    monthly_payment_total = payments.filter(entry_date__month=month).aggregate(total=Sum('payment_amount'))['total'] or 0
                    if month == 1:
                        monthly_totals['jan_total'] = monthly_payment_total
                    elif month == 2:
                        monthly_totals['feb_total'] = monthly_payment_total
                    elif month == 3:
                        monthly_totals['mar_total'] = monthly_payment_total
                    elif month == 4:
                        monthly_totals['apr_total'] = monthly_payment_total
                    elif month == 5:
                        monthly_totals['may_total'] = monthly_payment_total
                    elif month == 6:
                        monthly_totals['jun_total'] = monthly_payment_total
                    elif month == 7:
                        monthly_totals['jul_total'] = monthly_payment_total
                    elif month == 8:
                        monthly_totals['aug_total'] = monthly_payment_total
                    elif month == 9:
                        monthly_totals['sep_total'] = monthly_payment_total
                    elif month == 10:
                        monthly_totals['oct_total'] = monthly_payment_total
                    elif month == 11:
                        monthly_totals['nov_total'] = monthly_payment_total
                    elif month == 12:
                        monthly_totals['dec_total'] = monthly_payment_total
                scheme_data['datas'].append({
                    'year': year,
                    **monthly_totals
                })
                response_data.append(scheme_data)
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

     
class MonthwiseSchemeJoinReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        year = request.data.get('year')
        added_through = request.data.get('added_through', "")
        if not year:
            return Response({"error": "Year is required."}, status=400)
        try:
            year = int(year)
        except ValueError:
            return Response({"error": "Invalid year format."}, status=400)

        query_filters = {'start_date__year': year}
        if added_through != "":
            try:
                added_through = int(added_through) 
                query_filters['added_by'] = added_through
            except ValueError:
                return Response({"error": "Invalid added_by format."}, status=400)

        scheme_accounts = (
            SchemeAccount.objects
            .filter(**query_filters)
            .annotate(month=ExtractMonth('start_date'))
            .values('acc_scheme_id', 'month')
            .annotate(count=Count('id_scheme_account'))
            .order_by('acc_scheme_id', 'month')
        )
        schemes = Scheme.objects.in_bulk(field_name='scheme_id')
        all_months = {month: 0 for month in range(1, 13)}
        scheme_data = {}
        for record in scheme_accounts:
            scheme_id = record['acc_scheme_id']
            month = record['month']
            count = record['count']
            
            scheme_name = schemes[scheme_id].scheme_name if scheme_id in schemes else "Unknown"
            month_abbr = calendar.month_abbr[month].lower()

            if scheme_id not in scheme_data:
                scheme_data[scheme_id] = {
                    "scheme_name": scheme_name,
                    "datas": [{"year": year}]
                }
                for m in range(1, 13):
                    scheme_data[scheme_id]["datas"][0][f"{calendar.month_abbr[m].lower()}_count"] = 0
            scheme_data[scheme_id]["datas"][0][f"{month_abbr}_count"] = count
        response = list(scheme_data.values())
        return Response(response, status= status.HTTP_200_OK)
  
        
class UnpaidReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        result = call_stored_procedure('unpaid_report')
        columns = get_reports_columns_template(request.user.pk,CUSTOMER_UNPAID_REPORT_LIST,request.data["path_name"])           
        paginator, page = pagination.paginate_queryset(result['report_data'], request,None,CUSTOMER_UNPAID_REPORT_LIST)
        context={'columns':columns,'actions':ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':False}
        return pagination.paginated_response(result['report_data'],context)

class CustomerOutstandingReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        try:
            result = call_stored_procedure('customer_outstanding_report')
            columns = get_reports_columns_template(request.user.pk,CUSTOMER_OUTSTANDING_COLUMN_LIST,request.data["path_name"])           
            paginator, page = pagination.paginate_queryset(result['report_data'], request,None,CUSTOMER_OUTSTANDING_COLUMN_LIST)
            context={'columns':columns,'actions':ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':False}
            return pagination.paginated_response(result['report_data'],context) 
        except Exception as e:
            return Response({"error": f"Database error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class ModeWiseCollectionReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_scheme = request.data['id_scheme']
        id_branch = request.data['branch']
        # id_branch = ",".join(map(str, id_branch))
        filters_copy = FILTERS.copy()
        filters_copy['isSchemeFilterReq'] = False
        filters_copy['isBranchFilterReq'] = True
        # Convert id_scheme and id_branch to integers if provided, else set to None
        id_scheme = (id_scheme) if id_scheme != '' else 0
        id_branch = (id_branch) if id_branch != '' else 0
        #Execute the stored procedure
        result = call_stored_procedure('chit_mode_wise_collection',from_date,to_date,id_branch,0)
        columns = get_reports_columns_template(request.user.pk,MODE_COLUMN_LIST,request.data["path_name"])           
        paginator, page = pagination.paginate_queryset(result['report_data'], request,None,MODE_COLUMN_LIST)
        context={'columns':columns,'actions':ACTION_LIST,'page_count':paginator.count,
                 'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':True,
                 'filters':filters_copy}
        return pagination.paginated_response(result['report_data'],context) 


class ClosedAccountReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        try:
            from_date = request.data['from_date']
            to_date = request.data['to_date']
            id_scheme = request.data['id_scheme']
            id_branch = request.data['id_branch']
            # Convert id_scheme and id_branch to integers if provided, else set to None
            id_scheme = (id_scheme) if id_scheme != '' else 0
            id_branch = (id_branch) if id_branch != '' else 0
            #Execute the stored procedure
            filters_copy = FILTERS.copy()
            result = call_stored_procedure('closed_account_report',from_date,to_date,id_branch,id_scheme)
            columns = get_reports_columns_template(request.user.pk,CLOSED_ACC_COLUMN_LIST,request.data["path_name"])           
            paginator, page = pagination.paginate_queryset(result['report_data'], request,None,CLOSED_ACC_COLUMN_LIST)
            context={'columns':columns,'actions':ACTION_LIST,'page_count':paginator.count,
                     'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':True,
                     'filters':filters_copy}
            return pagination.paginated_response(result['report_data'],context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class SchemeWiseOpeningAndClosingView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        try:
            from_date = datetime.strptime(request.data['from_date'], '%Y-%m-%d')
            op_blc_date = from_date - timedelta(days=1)
            from_date = request.data['from_date']
            to_date = request.data['to_date']
            id_scheme = request.data['id_scheme']
            # Convert id_scheme and id_branch to integers if provided, else set to 0
            id_scheme = (id_scheme) if id_scheme != '' else 0
            #Execute the stored procedure
            print(op_blc_date)
            result = call_stored_procedure('scheme_wise_opening_and_closing',op_blc_date,from_date,to_date,id_scheme)
            for index,data in enumerate(result['report_data']):
                data.update({'sno':index+1})
            paginator, page = pagination.paginate_queryset(result['report_data'], request,None,SCHEME_OPENING_AND_CLOSING_COLUMN_LIST)
            columns = get_reports_columns_template(request.user.pk,SCHEME_OPENING_AND_CLOSING_COLUMN_LIST,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = True
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            return pagination.paginated_response(result['report_data'],context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

class StockInAndOutAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate',None)
        section = request.data.get('section',None)
        product = request.data.get('product',None)
        metal = request.data.get('id_metal',None)
        emp = Employee.objects.filter(user_id = request.user.pk).get()
        emp_profile = Profile.objects.get(id_profile=emp.id_profile.pk)
        if product == '':
            product = None
        if section == '':
            section = None
        if metal == '':
            metal = None
        # report_col = ReportColumnsAccess.objects.get(menu = 82,profile=emp_profile.pk)
        # columns = report_col.columns
      #  STOCK_IN_AND_OUT_REPORT_LIST =  json.loads(report_col.columns)
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            id_branch = ",".join(map(str, id_branch))
            print(id_branch)
            result1 = call_stored_procedure('TagStockInandOut',id_branch,from_date,to_date,metal,product,section)
            result2 = call_stored_procedure('TagStockInandOutBasedOnWeightRange',id_branch,from_date,to_date,metal,product,section)
            result3 = call_stored_procedure('NonTagStockReport',id_branch,from_date,to_date,product,metal,section)
            result4 = call_stored_procedure('TagStockInandOutProductWise',id_branch,from_date,to_date,metal,product,section)
            result = result1['report_data'] + result2['report_data'] + result3['report_data'] + result4['report_data']
            # result = result1['report_data']
            columns = get_reports_columns_template(request.user.pk,STOCK_IN_AND_OUT_REPORT_LIST,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isProductFilterReq'] = True
            filters_copy['isSectionFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True

            paginator, page = pagination.paginate_queryset(result, request,None,STOCK_IN_AND_OUT_REPORT_LIST)
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
                'groupingColumns': ["section_name","product_name"],
                }
            return pagination.paginated_response(result,context) 


            # response_data = { "stock" :response_data1,"report_data" :result2['report_data'] }
            # #paginator, page = pagination.paginate_queryset(response_data, request)
            # filters_copy = FILTERS.copy()
            # filters_copy['isDateFilterReq'] = True
            # filters_copy['isBranchFilterReq'] = True
            # filters_copy['isProductFilterReq'] = True
            # context={
            #     'columns':STOCK_IN_AND_OUT_REPORT_LIST,
            #     "result":result3,
            #     'actions':ACTION_LIST,
            #     'is_filter_req':True,
            #     'filters':filters_copy,
            #     "data":response_data,
            #     "BasedOnWeightRange":response_data2, 
            #     "grant_total" :grant_total
            #     }
            # #result['report_data'] = format_data_with_decimal(result['report_data'],STOCK_IN_AND_OUT_REPORT_LIST)
            
            # return Response(context, status=status.HTTP_200_OK)
            
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}","tb":tb}, status=status.HTTP_400_BAD_REQUEST)
        
class TaggedStockAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        product = request.data.get('product')
        design = request.data.get('design')
        sub_design = request.data.get('subDesign')
        purity = request.data.get('purity')
        supplier = request.data.get('supplier')
        metal = request.data.get('id_metal')
        from_wt = request.data.get('from_wt')
        to_wt = request.data.get('to_wt')
        tag_code = request.data.get('tag_code')
        lot = request.data.get('lot_code')
        report_type = int(request.data.get('group_by',1))



        searchText = request.query_params.get('search')
        filters = ''

        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            id_branch = ",".join(map(str, id_branch))
            if product:
                filters += f' and tag.tag_product_id_id = {product} '
            if design:
                filters += f' and tag.tag_design_id_id = {design} '
            if sub_design:
                filters += f' and tag.tag_sub_design_id_id = {sub_design} '
            if purity:
                filters += f' and tag.tag_purity_id_id = {purity} '
            if supplier:
                filters += f' and lot.id_supplier_id = {supplier} '
            if metal:
                filters += f' and product.id_metal_id = {metal} '
            if tag_code:
                filters += f' and  tag.tag_code = {tag_code} '
            if from_wt and to_wt:
                filters += f' and tag.tag_gwt BETWEEN {from_wt} AND {to_wt} '
            elif from_wt:
                filters += f' and tag.tag_gwt >= {from_wt} '
            elif to_wt:
                filters += f' and tag.tag_gwt <= {to_wt} '

            if lot:
                filters += f' and lot.lot_no = {lot} '

            if 'search' in request.query_params and request.query_params['search'] != 'undefined' and request.query_params['search'] != 'null':
                filters += f" and (product.product_name LIKE '%{searchText}%' or tag.tag_code LIKE '%{searchText}%' or des.design_name LIKE '%{searchText}%') "

            query = F"""SELECT tag.*  FROM erp_tagging tag
                    LEFT JOIN erp_lot_inward_details lot_det ON  lot_det.id_lot_inward_detail = tag.tag_lot_inward_details_id
                    LEFT JOIN erp_lot_inward lot ON lot.lot_no = lot_det.lot_no_id
                    LEFT JOIN erp_tag_log_details tl ON tl.tag_id_id  = tag.tag_id and tl.to_branch_id in ({id_branch})
                    LEFT JOIN erp_tag_log_details tl2 ON tl2.tag_id_id  = tag.tag_id and tl2.id_tag_log > tl.id_tag_log and tl2.date <= ( "{to_date}")
                    LEFT JOIN erp_product product ON product.pro_id = tag.tag_product_id_id
                    LEFT JOIN erp_design des ON des.id_design = tag.tag_design_id_id
                    WHERE  tl2.tag_id_id IS NULL and (tl.id_stock_status_id = 1 or tl.id_stock_status_id = 5)  and tl.date <= ( "{to_date}")
                    {filters}
                    ORDER BY tag.tag_id DESC
                    """
            print(query)
            stocks = ErpTagging.objects.raw(query)

            paginator, page = pagination.paginate_queryset(stocks, request,None,AVAILABLE_TAG_REPORT_LIST)

            data = ErpTaggingSerializer(page,many=True).data

            for item, instance in zip(data, stocks):
                purity = instance.tag_purity_id.purity if instance.tag_purity_id else None
                tag_tax_grp = instance.tag_tax_grp_id.tgi_tgrpcode.tgrp_name if instance.tag_tax_grp_id else None
                mc_type_display = instance.get_tag_mc_type_display()
                # tag_calculation_type_name = instance.tag_calculation_type.name if instance.tag_calculation_type else None
                lot_code = instance.tag_lot_inward_details.lot_no.lot_code if instance.tag_lot_inward_details else None
                supplier = instance.id_supplier.supplier_name if instance.id_supplier else None
                current_branch = instance.tag_current_branch.name if instance.tag_current_branch else None
                if instance.tag_date:
                    stock_age_days = (date.today() - instance.tag_date).days
                    item['stock_age'] = f"{stock_age_days} days"
                else:
                    item['stock_age'] = "N/A"
                    
                item['current_branch'] = current_branch
                item['supplier'] = supplier
                item['lot_code'] = lot_code
                item['tag_purity'] = purity
                item['tag_tax_grp'] = tag_tax_grp
                item['tag_mc_type_name'] = mc_type_display
                item['tag_calculation_type_name'] = ""

                
                if(ErpTaggingImages.objects.filter(erp_tag=item['tag_id'],is_default=True).exists()):
                    preview_images_query = ErpTaggingImages.objects.filter(erp_tag=item['tag_id'])
                    preview_images_serializer = ErpTaggingImagesSerializer(preview_images_query, many=True, context={"request": request})
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=item['tag_id']).first()
                    tag_image_seri = ErpTaggingImagesSerializer(tag_image, context={"request":request})
                    for image in preview_images_serializer.data:
                        image.update({"image":image['tag_image']})
                    item.update({"image":tag_image_seri.data['tag_image'], "image_text":item['tag_code'][len(item['tag_code'])-1],
                                 "preview_images":preview_images_serializer.data})
                else:
                    item.update({"image":None, "image_text":item['product_code'],"preview_images":[]})
            columns = get_reports_columns_template(request.user.pk,AVAILABLE_TAG_REPORT_LIST,request.data["path_name"])
            groupingColumns = []
            if report_type == 1:
                groupingColumns = ['supplier_name']
            elif report_type == 2:
                groupingColumns = ['product_name']
            elif report_type == 3:
                groupingColumns = ['design_name']
            elif report_type == 4:
                groupingColumns = ['supplier_name']

            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isProductFilterReq'] = True
            filters_copy['isTagCodeFilterReq'] = True
            filters_copy['isDeignFilterReq'] = True
            filters_copy['isSubDeignFilterReq'] = True
            filters_copy['isPurityFilterReq'] = True
            filters_copy['isSupplierFilterReq'] = True
            filters_copy['isLotFilterReq'] = True
            filters_copy['isMcTypeFilterReq'] = True
            filters_copy['isMcValueFilterReq'] = True
            filters_copy['isVaPercentFilterReq'] = True
            filters_copy['isVaFromToFilterReq'] = True
            filters_copy['isGwtFromToFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
                'groupingColumns': groupingColumns,
                'groupByOption': [ {'value': 1, 'label': 'Supplier'}, {'value': 2, 'label': 'Product'}, {'value': 3, 'label': 'Design'}],
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

class StockTransferAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        type = int(request.data.get('type',0))
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        transfer_from = request.data.get('transfer_from')
        transfer_to = request.data.get('transfer_to')
        item_type = request.data.get('item_type')


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpStockTransfer.objects.all()

            if(transfer_from):
                queryset  = queryset.filter(transfer_from__in = transfer_from)

            if(transfer_to):            
                queryset  = queryset.filter(transfer_to = transfer_to)
         
            if(item_type):            
                queryset  = queryset.filter(transfer_type = item_type)

            if from_date and to_date and type == 2:
                queryset = queryset.filter(approved_date__range=[from_date, to_date])

            if from_date and to_date and type == 1:
                queryset = queryset.filter(downloaded_date__range=[from_date, to_date])
            if from_date and to_date and type == 0:
                queryset = queryset.filter(trans_date__range=[from_date, to_date])

            queryset = queryset.select_related('transfer_from', 'transfer_to').order_by('id_stock_transfer')


            paginator, page = pagination.paginate_queryset(queryset, request,None,STOCK_TRANSFER_REPORT)

            data = ErpStockTransferSerializer(page,many=True).data

            response_data=[]

            for item, instance in zip(data, queryset):

                if(instance.transfer_type == 1):
        
                    transfer_list = ErpTagTransfer.objects.filter(stock_transfer=instance).annotate(
                        product_name=F('tag_id__tag_product_id__product_name'),
                        design_name=F('tag_id__tag_design_id__design_name'),
                        sub_design_name=F('tag_id__tag_sub_design_id__sub_design_name'),
                        tag_code=F('tag_id__tag_code'),
                        pieces=F('tag_id__tag_pcs'),
                        gross_wt=F('tag_id__tag_gwt'),
                        net_wt=F('tag_id__tag_nwt'),
                        less_wt=F('tag_id__tag_lwt'),
                        stn_wt=F('tag_id__tag_stn_wt'),
                        dia_wt=F('tag_id__tag_dia_wt'),
                        download_by=F('downloaded_by__first_name'),
                        download_date=F('downloaded_date'),
                    ).values(
                        'stock_transfer',
                        'product_name', 
                        'design_name',
                        'sub_design_name',
                        'tag_code',
                        'pieces',
                        'gross_wt', 
                        'net_wt',
                        'stn_wt',
                        'dia_wt',
                        'less_wt',
                        'download_by',
                        'download_date',
                    )

                    for tag in transfer_list:

                        response_data.append({
                            'pk_id': instance.id_stock_transfer,
                            'trans_date': format_date(instance.trans_date),
                            'transfer_from':instance.transfer_from.name,
                            'transfer_to': instance.transfer_to.name if instance.transfer_to else '',
                            'status': dict(ErpStockTransfer.TRANSFER_STATUS_CHOICES).get(instance.transfer_status, ''),
                            'trans_code': instance.trans_code,
                            'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(instance.trans_to_type, ''),
                            'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(instance.transfer_type, ''),
                            'tag_code':'',
                            **tag,
                            'downloaded_by':  tag['download_by'],
                            'downloaded_date': date_format_with_time(tag['download_date']),
                            'status_color':get_status_color(instance.transfer_status),
                            'approved_by':  instance.approved_by.first_name if instance.approved_by else None ,
                            'approved_date': date_format_with_time(instance.approved_date),
                            'rejected_by':  instance.rejected_by.first_name if instance.rejected_by else None ,
                            'rejected_on': date_format_with_time(instance.rejected_on),
                            })

                if(instance.transfer_type == 2):
            
                    transfer_list = ErpNonTagTransfer.objects.filter(stock_transfer=instance)

                    nt_data = ErpNonTagTransferSerializer(transfer_list,many=True).data

                    for non_tag,ins  in zip(nt_data, transfer_list):

                        response_data.append({
                            'pk_id': instance.id_stock_transfer,
                            'transfer_from':instance.transfer_from.name,
                            'transfer_to':instance.transfer_to.name,
                            'trans_code': instance.trans_code,
                            'trans_date': format_date(instance.trans_date),
                            'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(instance.trans_to_type, ''),
                            'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(instance.transfer_type, ''),
                            'status': dict(ErpStockTransfer.TRANSFER_STATUS_CHOICES).get(instance.transfer_status, ''),
                            **non_tag,
                            'tag_code':'',
                            'status_color':get_status_color(instance.transfer_status),
                            'downloaded_by':  instance.downloaded_by.first_name if instance.downloaded_by else None ,
                            'downloaded_date': date_format_with_time(instance.downloaded_date),
                            'approved_by':  instance.approved_by.first_name if instance.approved_by else None ,
                            'approved_date': date_format_with_time(instance.approved_date),
                            'rejected_by':  instance.rejected_by.first_name if instance.rejected_by else None ,
                            'rejected_on': date_format_with_time(instance.rejected_on),
                        })
            columns = get_reports_columns_template(request.user.pk,STOCK_TRANSFER_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = False
            filters_copy['isBranchFromToFilterReq'] = True
            filters_copy['StockTransferFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            # FILTERS['StockTransferFilterReq'] = False
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        


class SalesReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        report_type = request.data.get('optional_type')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        metal = request.data.get('id_metal')
        Product = request.data.get('product')
        section = request.data.get('section')
        id_counter = request.data.get('id_counter')
        item_type = request.data.get('item_type')


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1).order_by('id_product')

            if(bill_setting_type == 1 or bill_setting_type == 0):
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = bill_setting_type)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)

            if(id_counter):
                queryset  = queryset.filter(invoice_bill_id__id_counter = id_counter)

            if(item_type):
                queryset  = queryset.filter(item_type = item_type)

            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            
            if metal:
                queryset = queryset.filter(id_product__id_metal=metal)

            if Product:
                queryset = queryset.filter(id_product=Product)
            
            if section:
                queryset = queryset.filter(id_section=section)

           # queryset = queryset.select_related('transfer_from', 'transfer_to').order_by('id_stock_transfer')

            if int(report_type) == 2:

                paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_DETAIL_REPORT)

                data = ErpInvoiceSalesDetailsSerializer(page,many=True).data

                response_data=[]

                for item, instance in zip(data, queryset):

                    inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

                    inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                    
                    inv_data = get_invoice_no(inv_serializer)
                    #purity = instance.purity_id.purity if instance.tag_purity_id else None
                    tag_tax_grp = instance.tax_group_id.tgi_tgrpcode.tgrp_name if instance.tax_group_id else None
                    mc_type_display = instance.get_mc_type_display()
                    # tag_calculation_type_name = instance.calculation_type.name if instance.calculation_type else None
                    #item['tag_purity'] = purity
                    item['tax_grp'] = tag_tax_grp
                    item['mc_type_name'] = mc_type_display
                    item['calculation_type_name'] = ""


                    response_data.append({
                        **inv_serializer,
                        'invoice_date': format_date(inv_serializer['invoice_date']),
                        **item,
                        **inv_data,
                        'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                        'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                        'metal_name' : instance.id_product.id_metal.metal_name if instance.id_product and instance.id_product.id_metal.metal_name else None,
                        'product_name' : instance.id_product.product_name if instance.id_product.product_name else None,
                        'section_name' : instance.id_section.section_name if instance.id_section!=None else None,
                    })
                columns = get_reports_columns_template(request.user.pk,SALES_DETAIL_REPORT,request.data["path_name"])           
                filters_copy = FILTERS.copy()
                filters_copy['isDateFilterReq'] = True
                filters_copy['isBranchFilterReq'] = True
                filters_copy['isProductFilterReq'] = True
                filters_copy['isMetalFilterReq'] = True
                filters_copy['isSectionFilterReq'] = True
                filters_copy['isOpionalFilterReq'] = True
                filters_copy['itemTypeFilterReq'] = True
                filters_copy['isCounterFilterReq'] = True


                context={
                    'columns':columns,
                    'actions':ACTION_LIST,
                    'page_count':paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page.number,
                    'is_filter_req':True,
                    'filters':filters_copy,
                    'groupingColumns': ["product_name"],
                    'optionalType':[
                        { "value": 1, "label": "Product" },
                        { "value": 2, "label": "Product Design" },
                        { "value": 3, "label": "Section and Product" },
                        { "value": 4, "label": "Design" },
                        ]
                    }
            elif int(report_type) == 3:
                queryset= queryset.values('id_section').annotate( 
                                        product_name=F('id_product__product_name'),
                                        short_code=F('id_product__short_code'),
                                        section_name=F('id_section__section_name'),
                                        pcs=Sum('pieces'),
                                        grosswt=Sum('gross_wt'),
                                        netwt=Sum('net_wt'),
                                        diawt=Sum('dia_wt'),
                                        stonewt=Sum('stone_wt'),
                                        lesswt=Sum('less_wt'),
                                        taxable=Sum('taxable_amount'),
                                        wastage_wt=Sum('wastage_weight'),
                                        tax=Sum('tax_amount'),
                                        tot_amount=Sum('item_cost'),
                                        )
                
                

                paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_SECTION_SUMMARY_REPORT)

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_SECTION_SUMMARY_REPORT,request.data["path_name"])           
                filters_copy = FILTERS.copy()
                filters_copy['isDateFilterReq'] = True
                filters_copy['isBranchFilterReq'] = True
                filters_copy['isOpionalFilterReq'] = True
                filters_copy['isProductFilterReq'] = True
                filters_copy['isMetalFilterReq'] = True
                filters_copy['isSectionFilterReq'] = True
                filters_copy['itemTypeFilterReq'] = True
                filters_copy['isCounterFilterReq'] = True


                context={
                    'columns':columns,
                    'actions':ACTION_LIST,
                    'page_count':paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page.number,
                    'is_filter_req':True,
                    'filters':filters_copy,
                    'groupingColumns': ["section_name"],
                    'optionalType':[
                        { "value": 1, "label": "Product" },
                        { "value": 2, "label": "Product Design" },
                        { "value": 3, "label": "Section" },
                        { "value": 4, "label": "Design" },
                        ]
                    }
            elif int(report_type) == 4:
                queryset= queryset.values('id_design').annotate( 
                                        design_name=F('id_design__design_name'),
                                        pcs=Sum('pieces'),
                                        grosswt=Sum('gross_wt'),
                                        netwt=Sum('net_wt'),
                                        diawt=Sum('dia_wt'),
                                        stonewt=Sum('stone_wt'),
                                        lesswt=Sum('less_wt'),
                                        taxable=Sum('taxable_amount'),
                                        wastage_wt=Sum('wastage_weight'),
                                        tax=Sum('tax_amount'),
                                        tot_amount=Sum('item_cost'),
                                        )
                
                

                paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_DESIGN_SUMMARY_REPORT)

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_DESIGN_SUMMARY_REPORT,request.data["path_name"])           
                filters_copy = FILTERS.copy()
                filters_copy['isDateFilterReq'] = True
                filters_copy['isBranchFilterReq'] = True
                filters_copy['isOpionalFilterReq'] = True
                filters_copy['isProductFilterReq'] = True
                filters_copy['isMetalFilterReq'] = True
                filters_copy['isSectionFilterReq'] = True
                filters_copy['itemTypeFilterReq'] = True
                filters_copy['isCounterFilterReq'] = True


                context={
                    'columns':columns,
                    'actions':ACTION_LIST,
                    'page_count':paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page.number,
                    'is_filter_req':True,
                    'filters':filters_copy,
                    'groupingColumns': [],
                    'optionalType':[
                        { "value": 1, "label": "Product" },
                        { "value": 2, "label": "Product Design" },
                        { "value": 3, "label": "Section" },
                        { "value": 4, "label": "Design" },
                        ]
                    }
            else :


                queryset= queryset.values('id_product').annotate( 
                                        product_name=F('id_product__product_name'),
                                        short_code=F('id_product__short_code'),
                                        pcs=Sum('pieces'),
                                        grosswt=Sum('gross_wt'),
                                        netwt=Sum('net_wt'),
                                        diawt=Sum('dia_wt'),
                                        stonewt=Sum('stone_wt'),
                                        lesswt=Sum('less_wt'),
                                        taxable=Sum('taxable_amount'),
                                        wastage_wt=Sum('wastage_weight'),
                                        tax=Sum('tax_amount'),
                                        tot_amount=Sum('item_cost'),
                                        )
                
                

                paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_SUMMARY_REPORT)

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_SUMMARY_REPORT,request.data["path_name"])           
                filters_copy = FILTERS.copy()
                filters_copy['isDateFilterReq'] = True
                filters_copy['isBranchFilterReq'] = True
                filters_copy['isOpionalFilterReq'] = True
                filters_copy['isProductFilterReq'] = True
                filters_copy['isMetalFilterReq'] = True
                filters_copy['isSectionFilterReq'] = True
                filters_copy['itemTypeFilterReq'] = True
                filters_copy['isCounterFilterReq'] = True

                context={
                    'columns':columns,
                    'actions':ACTION_LIST,
                    'page_count':paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page.number,
                    'is_filter_req':True,
                    'filters':filters_copy,
                    'optionalType':[
                        { "value": 1, "label": "Product" },
                        { "value": 2, "label": "Product and Design" },
                        { "value": 3, "label": "Section" },
                        { "value": 4, "label": "Design" },
                        ]
                    }

            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class MiscBillReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        metal = request.data.get('id_metal')
        Product = request.data.get('product')
        id_counter = request.data.get('id_counter')


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1,invoice_bill_id__is_promotional_billing = 1).order_by('id_product')

            if(bill_setting_type == 1 or bill_setting_type == 0):
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = bill_setting_type)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)

            if(id_counter):
                queryset  = queryset.filter(invoice_bill_id__id_counter = id_counter)

            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            
            if metal:
                queryset = queryset.filter(id_product__id_metal=metal)

            if Product:
                queryset = queryset.filter(id_product=Product)
            

           # queryset = queryset.select_related('transfer_from', 'transfer_to').order_by('id_stock_transfer')


            paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_DETAIL_REPORT)

            data = ErpInvoiceSalesDetailsSerializer(page,many=True).data

            response_data=[]

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

                inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                
                inv_data = get_invoice_no(inv_serializer)
                #purity = instance.purity_id.purity if instance.tag_purity_id else None
                tag_tax_grp = instance.tax_group_id.tgi_tgrpcode.tgrp_name if instance.tax_group_id else None
                mc_type_display = instance.get_mc_type_display()
                # tag_calculation_type_name = instance.calculation_type.name if instance.calculation_type else None
                #item['tag_purity'] = purity
                item['tax_grp'] = tag_tax_grp
                item['mc_type_name'] = mc_type_display
                item['calculation_type_name'] = ""


                response_data.append({
                    **inv_serializer,
                    'invoice_date': format_date(inv_serializer['invoice_date']),
                    **item,
                    **inv_data,
                    'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                    'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                    'metal_name' : instance.id_product.id_metal.metal_name if instance.id_product and instance.id_product.id_metal.metal_name else None,
                    'product_name' : instance.id_product.product_name if instance.id_product.product_name else None,
                    'section_name' : instance.id_section.section_name if instance.id_section!=None else None,
                })
            columns = get_reports_columns_template(request.user.pk,SALES_DETAIL_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isProductFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            filters_copy['isCounterFilterReq'] = True


            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
                'groupingColumns': ["product_name"],
                }

            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

class SalesReportBasedOnWeightRangeAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        metal = request.data.get('id_metal')
        Product = request.data.get('product')
        section = request.data.get('section')
        id_category = request.data.get('id_category')
        size = request.data.get('id_size')
        weight_range = request.data.get('id_weight_range')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        group_by = (request.data.get('optional_type',1))
        if group_by == '':
            group_by =0
        elif group_by:
            group_by = int(group_by)
        if not from_date or not to_date or not id_branch:
            return Response({"message": "From date and To date and Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            branch = ",".join(map(str, id_branch))
            bill_setting_type_filter = ''
            if  bill_setting_type == 1:
                bill_setting_type_filter = 'and inv.setting_bill_type = 1'
            elif bill_setting_type == 0: 
                bill_setting_type_filter = 'and inv.setting_bill_type = 0'

            if metal:
                bill_setting_type_filter += f' and pro.id_metal_id = {metal}'

            if Product:
                bill_setting_type_filter += f' and pro.pro_id = {Product}'

            if id_category:
                bill_setting_type_filter += f' and pro.cat_id_id = {id_category}'
            
            if section:
                bill_setting_type_filter += f' and sa.id_section_id = {section}'

            if weight_range:
                bill_setting_type_filter += f' and wt.id_weight_range = {weight_range}'

            if size:
                bill_setting_type_filter += f' and tag.size_id = {size}'

            if group_by == 1:

                queryset = (
                    F"""SELECT
                        pro.product_name,
                        des.design_name,
                        wt.weight_range_name,
                        COALESCE(SUM(sa.pieces), 0) AS pieces,
                        COALESCE(SUM(sa.gross_wt), 0) AS gross_wt,
                        COALESCE(SUM(sa.net_wt), 0) AS net_wt,
                        COALESCE(SUM(sa.dia_wt), 0) AS dia_wt,
                        COALESCE(SUM(sa.stone_wt), 0) AS stone_wt,
                        COALESCE(SUM(sa.item_cost), 0) AS tot_amount,
                        COALESCE(SUM(sa.tax_amount), 0) AS tax,
                        COALESCE(SUM(sa.taxable_amount), 0) AS taxable,
                        COALESCE(SUM(sa.less_wt), 0) AS lesswt,
                        COALESCE(SUM(sa.wastage_weight), 0) AS wastage_wt
                    FROM erp_invoice_sales_details sa 
                    LEFT JOIN erp_invoice inv ON inv.erp_invoice_id = sa.invoice_bill_id_id
                    LEFT JOIN erp_product pro ON pro.pro_id = sa.id_product_id
                    LEFT JOIN erp_design des ON des.id_design = sa.id_design_id
                    LEFT JOIN erp_sub_design sub ON sub.id_sub_design = sa.id_sub_design_id
                    LEFT JOIN erp_weight_range wt ON wt.id_product_id = sa.id_product_id and wt.from_weight <= sa.net_wt and wt.to_weight >= sa.net_wt
                    WHERE pro.has_weight_range = 1 and
                    inv.invoice_status = 1 and wt.id_weight_range IS NOT NULL
                    and inv.id_branch_id in ({branch})
                    AND inv.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                    {bill_setting_type_filter}
                    GROUP BY sa.id_product_id,wt.id_weight_range 
                    Order By sa.id_product_id,wt.from_weight DESC"""
                )
                print(bill_setting_type_filter)
                print(queryset)

                result = generate_query_result(queryset)

                paginator, page = pagination.paginate_queryset(result, request,None,SALES_WEIGHT_RANGE_REPORT)

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_WEIGHT_RANGE_REPORT,request.data["path_name"])
            elif group_by == 3 :
                queryset = (
                    F"""SELECT
                        pro.product_name,
                        des.design_name,
                        IFNULL(size.name,'') as size_name,
                        wt.weight_range_name,
                        COALESCE(SUM(sa.pieces), 0) AS pieces,
                        COALESCE(SUM(sa.gross_wt), 0) AS gross_wt,
                        COALESCE(SUM(sa.net_wt), 0) AS net_wt,
                        COALESCE(SUM(sa.dia_wt), 0) AS dia_wt,
                        COALESCE(SUM(sa.stone_wt), 0) AS stone_wt,
                        COALESCE(SUM(sa.item_cost), 0) AS tot_amount,
                        COALESCE(SUM(sa.tax_amount), 0) AS tax,
                        COALESCE(SUM(sa.taxable_amount), 0) AS taxable,
                        COALESCE(SUM(sa.less_wt), 0) AS lesswt,
                        COALESCE(SUM(sa.wastage_weight), 0) AS wastage_wt
                    FROM erp_invoice_sales_details sa 
                    LEFT JOIN erp_invoice inv ON inv.erp_invoice_id = sa.invoice_bill_id_id
                    LEFT JOIN erp_tagging tag ON tag.tag_id = sa.tag_id_id
                    LEFT JOIN erp_product pro ON pro.pro_id = sa.id_product_id
                    LEFT JOIN erp_design des ON des.id_design = sa.id_design_id
                    LEFT JOIN erp_sub_design sub ON sub.id_sub_design = sa.id_sub_design_id
                    LEFT JOIN erp_size size ON size.id_size = tag.size_id
                    LEFT JOIN erp_weight_range wt ON wt.id_product_id = sa.id_product_id and wt.from_weight <= sa.net_wt and wt.to_weight >= sa.net_wt
                    WHERE pro.has_size = 1 and
                    pro.has_weight_range = 1 and
                    inv.invoice_status = 1 and tag.size_id IS NOT NULL and wt.id_weight_range IS NOT NULL
                    and inv.id_branch_id in ({branch})
                    AND inv.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                    {bill_setting_type_filter}
                    GROUP BY sa.id_product_id,wt.id_weight_range,tag.size_id 
                    Order By sa.id_product_id ASC,wt.from_weight ASC, CAST(size.value AS UNSIGNED) ASC"""
                )
                print(bill_setting_type_filter)
                print(queryset)

                result = generate_query_result(queryset)

                paginator, page = pagination.paginate_queryset(result, request,None,SALES_SIZE_REPORT)

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_SIZE_REPORT,request.data["path_name"])
            else :
                queryset = (
                    F"""SELECT
                        pro.product_name,
                        des.design_name,
                        IFNULL(size.name,'') as size_name,
                        COALESCE(SUM(sa.pieces), 0) AS pieces,
                        COALESCE(SUM(sa.gross_wt), 0) AS gross_wt,
                        COALESCE(SUM(sa.net_wt), 0) AS net_wt,
                        COALESCE(SUM(sa.dia_wt), 0) AS dia_wt,
                        COALESCE(SUM(sa.stone_wt), 0) AS stone_wt,
                        COALESCE(SUM(sa.item_cost), 0) AS tot_amount,
                        COALESCE(SUM(sa.tax_amount), 0) AS tax,
                        COALESCE(SUM(sa.taxable_amount), 0) AS taxable,
                        COALESCE(SUM(sa.less_wt), 0) AS lesswt,
                        COALESCE(SUM(sa.wastage_weight), 0) AS wastage_wt
                    FROM erp_invoice_sales_details sa 
                    LEFT JOIN erp_invoice inv ON inv.erp_invoice_id = sa.invoice_bill_id_id
                    LEFT JOIN erp_tagging tag ON tag.tag_id = sa.tag_id_id
                    LEFT JOIN erp_product pro ON pro.pro_id = sa.id_product_id
                    LEFT JOIN erp_design des ON des.id_design = sa.id_design_id
                    LEFT JOIN erp_sub_design sub ON sub.id_sub_design = sa.id_sub_design_id
                    LEFT JOIN erp_size size ON size.id_size = tag.size_id
                    WHERE pro.has_size = 1 and
                    inv.invoice_status = 1 and tag.size_id IS NOT NULL
                    and inv.id_branch_id in ({branch})
                    AND inv.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                    {bill_setting_type_filter}
                    GROUP BY sa.id_product_id,tag.size_id 
                    Order By sa.id_product_id ASC, CAST(size.value AS UNSIGNED) DESC"""
                )
                print(bill_setting_type_filter)
                print(queryset)

                result = generate_query_result(queryset)

                paginator, page = pagination.paginate_queryset(result, request,None,SALES_SIZE_REPORT)

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_SIZE_REPORT,request.data["path_name"])

            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isfilteredCatIdReq'] = True
            filters_copy['isOpionalFilterReq'] = True
            filters_copy['isCounterFilterReq'] = True
            filters_copy['isProductFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            filters_copy['isSectionFilterReq'] = True
            filters_copy['isWeightRangeFilterReq'] = True
            filters_copy['isSizeFilteredReq'] = True

            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
                'groupingColumns':  ["product_name","weight_range_name"] if group_by == 3 else  ["product_name"] ,
                'optionalType':[
                    { "value": 1, "label": "WeightRange" },
                    { "value": 2, "label": "Size" },
                    { "value": 3, "label": "WeightRange and Size" },
                    ]
                }

            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        


class PurchaseReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        metal = request.data.get('id_metal')
        Product = request.data.get('product')

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id__invoice_status = 1)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            
            if metal:
                queryset = queryset.filter(id_product_id__id_metal=metal)

            if Product:
                queryset = queryset.filter(id_product_id=Product)
            
            if  bill_setting_type == 1:
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = 0)

            paginator, page = pagination.paginate_queryset(queryset, request,None,PURCHASE_REPORT)

            data = ErpInvoiceOldMetalDetailsSerializer(page,many=True).data

            print(data)


            response_data=[]

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

                inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                 
                inv_data = get_invoice_no(inv_serializer)

                response_data.append({
                    **inv_serializer,
                    'invoice_date': format_date(inv_serializer['invoice_date']),
                    **item,
                    **inv_data,
                    "metal_name":instance.id_product.id_metal.metal_name,
                    "product_name":instance.id_product.product_name,
                })
            columns = get_reports_columns_template(request.user.pk,PURCHASE_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isProductFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True

            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
                'groupingColumns': ["metal_name"],

                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class CashAbstractReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('id_branch')
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:

            sales_queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1)

            if  bill_setting_type == 1:
                sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                sales_queryset  = sales_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                sales_queryset = sales_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            sales_queryset= sales_queryset.values('id_product').annotate( 
                                     product_name=F('id_product__product_name'),
                                     pcs=Sum('pieces'),
                                     grosswt=Sum('gross_wt'),
                                     netwt=Sum('net_wt'),
                                     diawt=Sum('dia_wt'),
                                     stonewt=Sum('stone_wt'),
                                     lesswt=Sum('less_wt'),
                                     taxable=Sum('taxable_amount'),
                                     tax=Sum('tax_amount'),
                                     tot_amount=Sum('item_cost'),
                                      )
            
            sales_data = list(sales_queryset)

            pur_queryset = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id__invoice_status = 1)

            if  bill_setting_type == 1:
                pur_queryset = pur_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                pur_queryset = pur_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                pur_queryset  = pur_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                pur_queryset = pur_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            pur_queryset= pur_queryset.values('id_product').annotate( 
                            product_name=F('id_product__product_name'),
                            pcs=Sum('pieces'),
                            grosswt=Sum('gross_wt'),
                            netwt=Sum('net_wt'),
                            diawt=Sum('dia_wt'),
                            stonewt=Sum('stone_wt'),
                            lesswt=Sum('less_wt'),
                            tot_amount=Sum('amount'),
                            )
            
            purchase_data = list(pur_queryset)

            sales_return_queryset = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id__invoice_status = 1)

            if  bill_setting_type == 1:
                sales_return_queryset = sales_return_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                sales_return_queryset = sales_return_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                sales_return_queryset  = sales_return_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                sales_return_queryset = sales_return_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            sales_return_queryset= sales_return_queryset.values('id_product').annotate( 
                                     product_name=F('id_product__product_name'),
                                     pcs=Sum('pieces'),
                                     grosswt=Sum('gross_wt'),
                                     netwt=Sum('net_wt'),
                                     diawt=Sum('dia_wt'),
                                     stonewt=Sum('stone_wt'),
                                     lesswt=Sum('less_wt'),
                                     taxable=Sum('taxable_amount'),
                                     tax=Sum('tax_amount'),
                                     tot_amount=Sum('item_cost'),
                                      )

            sales_return = list(sales_return_queryset)

            inv_payment_queryset = ErpInvoicePaymentModeDetail.objects.filter(invoice_bill_id__invoice_status = 1).values('payment_mode').annotate(
                total_amount=Sum(
                    Case(
                        When(payment_type=1, then=F('payment_amount')),
                        default=-F('payment_amount'),
                    )
                ),
                payment_type=F('payment_type'),
                mode_name=F('payment_mode__mode_name'),
                mode=F('payment_mode')
            )

            if  bill_setting_type == 1:
                inv_payment_queryset = inv_payment_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                inv_payment_queryset = inv_payment_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                inv_payment_queryset  = inv_payment_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                inv_payment_queryset = inv_payment_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            inv_payment_data = list(inv_payment_queryset)

            issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt__bill_status = 1).values('payment_mode').annotate(
                total_amount=Sum(
                    Case(
                        When(type=1, then=F('payment_amount')),
                        default=-F('payment_amount'),
                    )
                ),
                payment_type=F('type'),
                mode_name=F('payment_mode__mode_name'),
                mode=F('payment_mode')
            )

            if  bill_setting_type == 1:
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 0)

            if(id_branch):
                issue_payment_queryset  = issue_payment_queryset.filter(issue_receipt__branch__in = id_branch)
            if from_date and to_date:
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__bill_date__range=[from_date, to_date])

            issue_payment_data = list(issue_payment_queryset)

            payment_details = {}

            total_payment = total_sale_inward = adv_adjusted = chit_adjusted = gift_adjusted = 0

            adj_data = ErpReceiptAdvanceAdj.objects.filter(
                invoice_bill_id__invoice_status=1
            )

            if  bill_setting_type == 1:
                adj_data = adj_data.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                adj_data = adj_data.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                adj_data  = adj_data.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                adj_data = adj_data.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            adj_data = adj_data.aggregate(total_adj_amount=Sum('adj_amount'))

            if(adj_data['total_adj_amount']):
                adv_adjusted = adj_data['total_adj_amount']

            chit_adj_data = ErpInvoiceSchemeAdjusted.objects.filter(
                invoice_bill_id__invoice_status=1
            )

            if  bill_setting_type == 1:
                chit_adj_data = chit_adj_data.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                chit_adj_data = chit_adj_data.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                chit_adj_data  = chit_adj_data.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                chit_adj_data = chit_adj_data.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            chit_adj_data = chit_adj_data.aggregate(chit_amount=Sum('id_scheme_account__closing_amount'))

            if(chit_adj_data['chit_amount']):
                chit_adjusted = chit_adj_data['chit_amount']
                
                
            gift_adj_data = ErpInvoiceGiftDetails.objects.filter(
                invoice_bill_id__invoice_status=1
            )

            if  bill_setting_type == 1:
                gift_adj_data = gift_adj_data.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                gift_adj_data = gift_adj_data.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                gift_adj_data  = gift_adj_data.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                gift_adj_data = gift_adj_data.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            gift_adj_data = gift_adj_data.aggregate(amount=Sum('amount'))

            if(gift_adj_data['amount']):
                gift_adjusted = gift_adj_data['amount']
                
                
            print(adj_data)

            for payment in inv_payment_data:
                if payment['mode'] not in payment_details:
                    print(payment['mode'])
                    payment_details[payment['mode']] = {
                        'payment_amount': 0,
                    }
                payment_details[payment['mode']] = {
                    **payment,
                    "payment_amount" : float(payment['total_amount']) + float(payment_details[payment['mode']]['payment_amount'])
                }
                total_payment += float(payment['total_amount'])

            for payment in issue_payment_data:
                if payment['mode'] not in payment_details:
                    payment_details[payment['mode']] = {
                        'payment_amount': 0,
                    }
                payment_details[payment['mode']] = {
                    **payment,
                    "payment_amount" : float(payment['total_amount']) + float(payment_details[payment['mode']]['payment_amount'])
                }
                total_payment += float(payment['total_amount'])

            payment_details = [
                {**details} 
                for mode, details in payment_details.items()
            ]

            total_payment += float(adv_adjusted)

            total_payment += float(chit_adjusted)
            
            total_payment += float(gift_adjusted)
            



            sales_taxable_amt = 0

            sales_tax_amt = 0

            purchase_amt = 0

            sales_return_tax_amt = 0

            sales_return_taxable_amt = 0


            for sales in sales_data:
                print(sales)
                sales_taxable_amt += float(sales['taxable'])
                sales_tax_amt += float(sales['tax'])

            for purchase in purchase_data:
                purchase_amt += float(purchase['tot_amount'])

            for return_ in sales_return:
                sales_return_taxable_amt += float(return_['taxable'])
                sales_return_tax_amt += float(return_['tax'])


            receipt_queryset = ErpIssueReceipt.objects.filter(bill_status = 1)

            if(id_branch):
                receipt_queryset  = receipt_queryset.filter(branch__in = id_branch)
            if from_date and to_date:
                receipt_queryset = receipt_queryset.filter(bill_date__range=[from_date, to_date])
        
            if  bill_setting_type == 1:
                receipt_queryset = receipt_queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                receipt_queryset = receipt_queryset.filter(setting_bill_type = 0)

            receipt_data = ErpIssueReceiptSerializer(receipt_queryset,many=True).data

            adv_receipt = adv_deposit = adv_refund = credit_receipt = credit_issue = other_expence =  0

            for receipt in receipt_data:
                if ((receipt['receipt_type'] == 1 or receipt['receipt_type'] == 2) and receipt['type'] == 2):
                    adv_receipt += float(receipt['amount'])
                elif (receipt['receipt_type'] == 3 and receipt['type'] == 2):
                    adv_deposit += float(receipt['amount'])
                elif (receipt['receipt_type'] == 5 and receipt['type'] == 2 ):
                    credit_receipt += float(receipt['amount'])
                elif (receipt['issue_type'] == 2 and receipt['type'] == 1):
                    adv_refund += float(receipt['amount'])
                elif (receipt['issue_type'] == 3 and receipt['type'] == 1):
                    other_expence += float(receipt['amount'])
                elif (receipt['issue_type'] == 1 and receipt['type'] == 1):
                    credit_issue += float(receipt['amount'])

            #inv_queryset = ErpInvoice.objects.filter(invoice_status = 1,is_credit = 1)

            # if(id_branch):
            #     inv_queryset  = inv_queryset.filter(id_branch__in = id_branch)
            # if from_date and to_date:
            #     inv_queryset = inv_queryset.filter(invoice_date__range=[from_date, to_date])
            # inv_queryset = inv_queryset.aggregate(
            #     total_balance=Sum('due_amount')
            # )

            round_off_queryset = ErpInvoice.objects.filter(invoice_status = 1)

            if(id_branch):
                round_off_queryset  = round_off_queryset.filter(id_branch__in = id_branch)
            if from_date and to_date:
                round_off_queryset = round_off_queryset.filter(invoice_date__range=[from_date, to_date])
            round_off_queryset = round_off_queryset.aggregate(
                total_balance=Sum('round_off')
            )

            round_off = round_off_queryset['total_balance'] if round_off_queryset['total_balance'] is not None else 0


            #invoice_credit = inv_queryset['total_balance'] if inv_queryset['total_balance'] is not None else 0

            #credit_issue += float(invoice_credit)

            total_sale_inward = float(sales_taxable_amt) + float(sales_tax_amt) -float(sales_return_taxable_amt) - float(sales_return_tax_amt) +float(adv_receipt) + float(adv_deposit) - float(adv_refund) + float(credit_receipt) - float(credit_issue) - float(other_expence)  - float(purchase_amt) - float(round_off)
            
            sales_summary = [
                { 'lable' : 'SALES','value': sales_taxable_amt, 'sign' : '(+)'},
                { 'lable' : 'SALES TAX','value': sales_tax_amt, 'sign' : '(+)'},
                { 'lable' : 'SALES RETURN','value': sales_return_taxable_amt, 'sign' : '(-)'},
                { 'lable' : 'SALES RETURN TAX','value': sales_return_tax_amt, 'sign' : '(-)'},
                { 'lable' : 'PURCHASE','value': purchase_amt, 'sign' : '(-)'},
                { 'lable' : 'ADVANCE RECEIPT','value': adv_receipt, 'sign' : '(+)'},
                { 'lable' : 'ADVANCE DEPOSIT','value': adv_deposit, 'sign' : '(+)'},
                { 'lable' : 'ADVANCE REFUND','value': adv_refund, 'sign' : '(-)'},
                { 'lable' : 'CREDIT RECEIPT','value': credit_receipt, 'sign' : '(+)'},
                { 'lable' : 'CREDIT SALES','value': credit_issue, 'sign' : '(-)'},
                { 'lable' : 'OTHER EXPENCE','value': other_expence, 'sign' : '(-)'},
                { 'lable' : 'ROUND OFF','value': round_off, 'sign' : '(-)'}
            ]

            payment_summary = []
 
            for pay in payment_details:
                payment_summary.append({ 'lable' : pay['mode_name'],'value':  pay['payment_amount'], 'sign' : '(+)'})

            if adv_adjusted:
                payment_summary.append({ 'lable' : 'ADV ADJUSTED','value':  adv_adjusted, 'sign' : '(+)'})

            if chit_adjusted:
                payment_summary.append({ 'lable' : 'CHIT ADJUSTED','value':  chit_adjusted, 'sign' : '(+)'})
                
            if gift_adjusted:
                payment_summary.append({ 'lable' : 'GIFT ADJUSTED','value':  gift_adjusted, 'sign' : '(+)'})


            response_data={
                'sales_data' :sales_data,
                'purchase_data' :purchase_data,
                'sales_return' :sales_return,
                'sales_summary' : sales_summary,
                'payment_summary' : payment_summary,
                'total_payment' :total_payment,
                'total_sale_inward' :total_sale_inward,                        
            }
                            
            return Response(response_data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        


class StockAuditReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_section = request.data.get('section',None)
        id_product = request.data.get('product',None)
        if id_product == '':
           id_product =None
        if id_section == '':
           id_section =None
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            branch = ",".join(map(str, id_branch))
            result = call_stored_procedure('TagStockInandOut',branch,from_date,to_date,None,id_product,id_section)
            for index,data in enumerate(result['report_data']):
                scanned = self.get_scanned({'id_product':data['pro_id'],'id_branch':id_branch,'from_date':from_date,'to_date':to_date,'id_section':id_section})
                unscanned = self.get_unscanned({'id_product':data['pro_id'],'id_branch':branch,'from_date':from_date,'to_date':to_date,'id_section':id_section})
                data.update({'sno':index+1,**scanned,**unscanned})

            paginator, page = pagination.paginate_queryset(result['report_data'], request,None,STOCK_AUDIT_REPORT_LIST)
            columns = get_reports_columns_template(request.user.pk,STOCK_AUDIT_REPORT_LIST,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isProductFilterReq'] = True
            filters_copy['isSectionFilterReq'] = True

            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
           # result['report_data'] = format_data_with_decimal(result['report_data'],STOCK_AUDIT_REPORT_LIST)
            
            return pagination.paginated_response(result['report_data'],context) 
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        

    def get_scanned(self,data):
        queryset = ErpTagScanDetails.objects.filter(tag_id__tag_product_id = data['id_product'],id_tag_scan__id_branch__in=data['id_branch'],id_tag_scan__start_date__range=[data['from_date'], data['to_date']],id_tag_scan__status = 0)
        if data['id_section']:
            queryset = queryset.filter(id_tag_scan__id_section = data['id_section'])
        queryset = queryset.values('tag_id__tag_product_id').annotate( 
                            product_name=F('tag_id__tag_product_id__product_name'),
                            scanned_pieces=Sum('tag_id__tag_pcs'),
                            scanned_gross_wt=Sum('tag_id__tag_gwt'),
                            scanned_net_wt=Sum('tag_id__tag_nwt'),
                            scanned_diawt=Sum('tag_id__tag_dia_wt'),
                            scanned_stonewt=Sum('tag_id__tag_stn_wt'),
                            scanned_less_wt=Sum('tag_id__tag_lwt'),
                            ).order_by('tag_id__tag_product_id')
        result = queryset.first()  # or queryset.get() if you're sure there's only one
        if result:
            return dict(result)
        else:
            return {"scanned_pieces":0,"scanned_gross_wt":0,"scanned_net_wt":0,"scanned_less_wt":0,"scanned_stonewt":0,"scanned_diawt":0}

    
    def get_unscanned(self,data):
        try:
            with connection.cursor() as cursor:
                filters_sql = ''
                if data['id_section']:
                     filters_sql = f"and tag.tag_section_id_id = {data['id_section']} "
                query = F"""SELECT tag.tag_product_id_id,COALESCE(SUM(tag.tag_pcs), 0) AS unscanned_pieces,  
                        COALESCE(SUM(tag.tag_gwt), 0) AS unscanned_gross_wt,COALESCE(SUM(tag.tag_nwt), 0) AS unscanned_net_wt,
                        COALESCE(SUM(tag.tag_lwt), 0) AS unscanned_less_wt,COALESCE(SUM(tag.tag_stn_wt), 0) AS unscanned_stonewt,
                        COALESCE(SUM(tag.tag_dia_wt), 0) AS unscanned_diawt  
                        FROM erp_tagging tag
                        LEFT JOIN erp_tag_log_details tl ON tl.tag_id_id  = tag.tag_id and tl.to_branch_id in ("{data['id_branch']}")
                        LEFT JOIN erp_tag_log_details tl2 ON tl2.tag_id_id  = tag.tag_id and tl2.id_tag_log > tl.id_tag_log 
                        
                        LEFT JOIN erp_tag_scan s ON  s.id_section_id = tag.tag_section_id_id and s.start_date >= "{data['from_date']}" and s.status = 0
                        LEFT JOIN erp_tag_scan_details sd ON sd.tag_id_id = tag.tag_id and s.id_tag_scan = sd.id_tag_scan_id
                        WHERE  tl2.tag_id_id IS NULL and (tl.id_stock_status_id = 1 or tl.id_stock_status_id = 5) 
                        and tl.date <= ( "{data['to_date']}") and sd.tag_id_id IS NULL and tag.tag_product_id_id = "{data['id_product']}"
                        {filters_sql}
                        GROUP BY tag.tag_product_id_id
                        ORDER BY tag.tag_product_id_id;
                        """

                cursor.execute(query, '')
                print(connection.queries[-1])
                response_data = None
                if cursor.description:
                    result = cursor.fetchall()
                    field_names = [desc[0] for desc in cursor.description]
                    report_data = []
                    for row in result:
                        print(result)
                        field_value = dict(zip(field_names, row))
                        report_data.append(field_value)
                    response_data = report_data
                else:
                    result = None
                
                print(response_data)
                if(response_data):
                    return response_data[0]
                else :
                    return {"unscanned_pieces":0,"unscanned_gross_wt":0,"unscanned_net_wt":0,"unscanned_less_wt":0,"unscanned_stonewt":0,"unscanned_diawt":0}
        except DatabaseError as e:
            return Response({"error": f"Database error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                

class StockAuditDetailReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_section = request.data.get('id_section')
        id_product = request.data.get('id_product')
        type = int(request.data.get('type',1))
        branch = ",".join(map(str, id_branch))


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if(type==1):
                # query = F"""SELECT tag.*,s.* 
                # FROM erp_tagging tag
                # LEFT JOIN erp_tag_log_details tl ON tl.tag_id_id  = tag.tag_id and tl.to_branch_id in ("{branch}")
                # LEFT JOIN erp_tag_log_details tl2 ON tl2.tag_id_id  = tag.tag_id and tl2.id_tag_log > tl.id_tag_log 
                # LEFT JOIN erp_tag_scan s ON  s.id_section_id = tag.tag_section_id_id and s.start_date >= "{from_date}" and s.status = 0
                # LEFT JOIN erp_tag_scan_details sd ON sd.tag_id_id = tag.tag_id and s.id_tag_scan = sd.id_tag_scan_id
                # WHERE  tl2.tag_id_id IS NULL and (tl.id_stock_status_id = 1 or tl.id_stock_status_id = 5) 
                # and tl.date <= ( "{to_date}") and sd.tag_id_id IS NULL
                # """
                stock_audit_based_on = int(RetailSettings.objects.get(name='stock_audit_based_on').value) # 1 for section, 2 for Product
                if stock_audit_based_on == 1:
                    query = F"""SELECT tag.*,s.*,sd.* ,p.product_name,des.design_name,sec.section_name,IFNULL(sd.scale_wt,0) as scale_wt
                    FROM erp_tagging tag
                    left join erp_product p on p.pro_id = tag.tag_product_id_id
                    left join erp_design des on des.id_design = tag.tag_design_id_id
                    left join erp_section sec on sec.id_section = tag.tag_section_id_id
                    LEFT JOIN erp_tag_scan s ON  s.id_section_id = tag.tag_section_id_id and s.status = 0
                    LEFT JOIN erp_tag_scan_details sd ON sd.tag_id_id = tag.tag_id and s.id_tag_scan = sd.id_tag_scan_id
                    WHERE sd.tag_id_id IS NULL AND tag.tag_status_id = 1 AND tag.tag_current_branch_id in ("{branch}")
                    """
                else:
                    query = F"""SELECT tag.*,s.*,sd.* ,p.product_name,des.design_name,sec.section_name,IFNULL(sd.scale_wt,0) as scale_wt 
                    FROM erp_tagging tag
                    left join erp_product p on p.pro_id = tag.tag_product_id_id
                    left join erp_design des on des.id_design = tag.tag_design_id_id
                    left join erp_section sec on sec.id_section = tag.tag_section_id_id
                    LEFT JOIN erp_tag_scan s ON  s.id_product_id = tag.tag_product_id_id and s.status = 0
                    LEFT JOIN erp_tag_scan_details sd ON sd.tag_id_id = tag.tag_id and s.id_tag_scan = sd.id_tag_scan_id
                    WHERE sd.tag_id_id IS NULL AND tag.tag_status_id = 1 AND tag.tag_current_branch_id in ("{branch}")
                    """
            else :

                query = F"""SELECT tag.* ,s.*,sd.* ,p.product_name,des.design_name,sec.section_name,IFNULL(sd.scale_wt,0) as scale_wt
                FROM erp_tag_scan s
                LEFT JOIN erp_tag_scan_details sd ON sd.id_tag_scan_id  = s.id_tag_scan
                LEFT JOIN erp_tagging tag ON tag.tag_id  = sd.tag_id_id
                left join erp_product p on p.pro_id = tag.tag_product_id_id
                left join erp_design des on des.id_design = tag.tag_design_id_id
                left join erp_section sec on sec.id_section = tag.tag_section_id_id
                WHERE  s.status = 0 and s.id_branch in ("{branch}")
                """
            print(query)
            if id_section:
                query += f" AND tag.tag_section_id_id = {id_section}"

            if id_product:
                query += f" AND tag.tag_product_id_id = {id_product}"

            #stocks = ErpTagging.objects.raw(query)

            data = generate_query_result(query)

            paginator, page = pagination.paginate_queryset(data, request,100000,STOCK_AUDIT_DETAIL_REPORT_LIST)

            #data = ErpTaggingSerializer(page,many=True).data
            # columns = get_reports_columns_template(request.user.pk,STOCK_AUDIT_DETAIL_REPORT_LIST,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isProductFilterReq'] = True

            context={
                'columns':STOCK_AUDIT_DETAIL_REPORT_LIST,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class StockAuditDetailReportPrintAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_section = request.data.get('id_section')
        id_product = request.data.get('id_product')
        type = int(request.data.get('type',1))
        branch = ",".join(map(str, id_branch))


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            stock_audit_based_on = int(RetailSettings.objects.get(name='stock_audit_based_on').value) # 1 for section, 2 for Product

            if stock_audit_based_on==1:
                unscaned_query = F"""SELECT tag.*,s.*,sd.* ,p.product_name,des.design_name
                FROM erp_tagging tag
                LEFT JOIN erp_tag_scan s ON  s.id_section_id = tag.tag_section_id_id and s.status = 0
                left join erp_product p on p.pro_id = tag.tag_product_id_id
                left join erp_design des on des.id_design = tag.tag_design_id_id
                LEFT JOIN erp_tag_scan_details sd ON sd.tag_id_id = tag.tag_id and s.id_tag_scan = sd.id_tag_scan_id
                WHERE sd.tag_id_id IS NULL AND tag.tag_status_id = 1 AND tag.tag_current_branch_id in ("{branch}")
                """
            else:
                unscaned_query = F"""SELECT tag.*,s.* ,sd.*,p.product_name,des.design_name
                FROM erp_tagging tag
                left join erp_product p on p.pro_id = tag.tag_product_id_id
                left join erp_design des on des.id_design = tag.tag_design_id_id
                LEFT JOIN erp_tag_scan s ON  s.id_product_id = tag.tag_product_id_id and s.status = 0
                LEFT JOIN erp_tag_scan_details sd ON sd.tag_id_id = tag.tag_id and s.id_tag_scan = sd.id_tag_scan_id
                WHERE sd.tag_id_id IS NULL AND tag.tag_status_id = 1 AND tag.tag_current_branch_id in ("{branch}")
                """

            scanned_query = F"""SELECT tag.* ,s.*,sd.*,p.product_name,des.design_name
            FROM erp_tag_scan s
            LEFT JOIN erp_tag_scan_details sd ON sd.id_tag_scan_id  = s.id_tag_scan
            LEFT JOIN erp_tagging tag ON tag.tag_id  = sd.tag_id_id
            left join erp_product p on p.pro_id = tag.tag_product_id_id
            left join erp_design des on des.id_design = tag.tag_design_id_id
            WHERE  s.status = 0 AND tag.tag_current_branch_id in ("{branch}")
            """
            if id_section:
                unscaned_query += f" AND tag.tag_section_id_id = {id_section}"
                scanned_query += f" AND tag.tag_section_id_id = {id_section}"

            if id_product:
                unscaned_query += f" AND tag.tag_product_id_id = {id_product}"
                scanned_query += f" AND tag.tag_product_id_id = {id_product}"
            scanned_stocks = generate_query_result(scanned_query)

            unscanned_stocks = generate_query_result(unscaned_query)

            # scanned_stocks = ErpTaggingSerializer(scanned_stocks,many=True).data
            # unscanned_stocks = ErpTaggingSerializer(unscanned_stocks,many=True).data
            scanned = []
            print("scanned_stocks",scanned_stocks)
            for scanned_stock in scanned_stocks:
                #scanned_tag_obj = ErpTagScanDetails.objects.filter(tag_id=scanned_stock['tag_id']).first()
                #scale_wt = Decimal(scanned_tag_obj.scale_wt) if scanned_tag_obj and scanned_tag_obj.scale_wt else Decimal('0.000')
                tag_gwt = Decimal(scanned_stock['tag_gwt'])
                scale_wt = Decimal(scanned_stock.get('scale_wt',0))

                balance_weight = tag_gwt - scale_wt
                scanned.append({
                    'tag_id':scanned_stock['tag_id'],
                    'product_name':scanned_stock['product_name'],
                    'design_name':scanned_stock['design_name'],
                    'tag_code':scanned_stock['tag_code'],
                    'tag_pcs':scanned_stock['tag_pcs'],
                    'tag_gwt':scanned_stock['tag_gwt'],
                    'scale_wt': scale_wt,
                    'balance_weight': balance_weight
                    # 'tag_nwt':scanned_stock['tag_lwt'],
                    # 'tag_dia_wt':scanned_stock['tag_dia_wt'],
                    # 'tag_stn_wt':scanned_stock['tag_stn_wt'],

                })
            unscanned = []
            for unscanned_stock in unscanned_stocks:
                unscanned.append({
                    'tag_id':unscanned_stock['tag_id'],
                    'product_name':unscanned_stock['product_name'],
                    'design_name':unscanned_stock['design_name'],
                    'tag_code':unscanned_stock['tag_code'],
                    'tag_pcs':unscanned_stock['tag_pcs'],
                    'tag_gwt':unscanned_stock['tag_gwt'],
                    'scale_wt':0.000,
                    'balance_weight':0.000
                    # 'tag_nwt':unscanned_stock['tag_lwt'],
                    # 'tag_dia_wt':unscanned_stock['tag_dia_wt'],
                    # 'tag_stn_wt':unscanned_stock['tag_stn_wt'],
                })
            
            scanned.sort(key=lambda x: x['balance_weight'], reverse=True)

            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isProductFilterReq'] = True

            context={
                'columns':STOCK_AUDIT_DETAIL_REPORT_LIST,
                'actions':ACTION_LIST,
                'is_filter_req':True,
                'filters':filters_copy,
                "scanned":scanned,
                "unscanned":unscanned,
                }
            
            return Response(context,status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

class B2BSalesReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(invoice_status = 1,invoice_for=2)

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])
            
            if  bill_setting_type == 1:
                queryset = queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(setting_bill_type = 0)


            paginator, page = pagination.paginate_queryset(queryset, request,None,B2B_SALES_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={'invoice_no':True}).data

            response_data = []

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id = instance.erp_invoice_id).annotate( 
                            taxable=Sum('taxable_amount'),
                            tax=Sum('tax_amount'),
                            cgst=Sum('cgst_cost'),
                            sgst=Sum('sgst_cost'),
                            igst=Sum('igst_cost'),
                            cost=Sum('item_cost'),
                            ).values(
                                'invoice_bill_id',
                                'taxable',
                                'tax', 
                                'cgst',
                                'sgst',
                                'igst',
                                'cost',
                            ).get()
                invsales = dict(inv_queryset)


                response_data.append({
                    **item,
                    **invsales,
                    "invoice_no" : item['inv_no']['invoice_no']
                })
            columns = get_reports_columns_template(request.user.pk,B2B_SALES_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class AdvanceReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpIssueReceipt.objects.filter(bill_status = 1, receipt_type__in = [1,2,3,4],type = 2,
                                                      setting_bill_type=bill_setting_type)

            if(id_branch):
                queryset  = queryset.filter(branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(bill_date__range=[from_date, to_date])
            
            if  bill_setting_type == 1:
                queryset = queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(setting_bill_type = 0)


            paginator, page = pagination.paginate_queryset(queryset, request,None,ADVANCE_REPORT)

            data = ErpIssueReceiptSerializer(page,many=True).data

            response_data=[]

            for item, instance in zip(data, queryset):
                 
                refund_amount = advadj_amount = 0

                refund  = instance.refund_receipt.all()

                adv_adj  = instance.advance_receipt.all()

                if(refund):
                    for ref in refund:
                        refund_amount += float(ref.refund_amount)

                if(adv_adj):
                    for adv in adv_adj:
                        advadj_amount += float(adv.adj_amount)
                item.update({
                    "refund_amount":refund_amount,
                    "advadj_amount":advadj_amount,
                    "balance_amount": float(item['amount']) - float(refund_amount) - float(advadj_amount),
                    'bill_date': format_date(item['bill_date']),
                    'receipt_type': dict(ErpIssueReceipt.RECEIPT_TYPE_CHOICES).get(instance.receipt_type, ''),

                })


            columns = get_reports_columns_template(request.user.pk,ADVANCE_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class CreditReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(is_credit = 1,invoice_status = 1)

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                queryset = queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(setting_bill_type = 0)


            paginator, page = pagination.paginate_queryset(queryset, request,None,CREDIT_INVOICE_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={"invoice_no":True}).data

            for inv in data:
                inv.update({
                    'invoice_no': inv['inv_no']['invoice_no'],
                    'invoice_date': format_date(inv['invoice_date']),
                })

            columns = get_reports_columns_template(request.user.pk,CREDIT_INVOICE_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class CreditCollectionReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpReceiptCreditCollection.objects.filter(receipt__bill_status = 1)

            if(id_branch):
                queryset  = queryset.filter(receipt__branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(receipt__bill_date__range=[from_date, to_date])


            paginator, page = pagination.paginate_queryset(queryset, request,None,CREDIT_COLLECTION_REPORT)

            data = ErpReceiptCreditCollectionSerializer(page,many=True).data

            if  bill_setting_type == 1:
                queryset = queryset.filter(receipt__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(receipt__setting_bill_type = 0)

            for item, instance in zip(data, queryset):
                type = (1 if instance.issue == None else 2)
                received_amount = 0
                balance_amount =0
                if(type == 1):
                    issued_amount = float(instance.invoice_bill_id.due_amount)
                    col = ErpReceiptCreditCollection.objects.filter(invoice_bill_id =instance.invoice_bill_id.erp_invoice_id ,receipt__bill_status= 1,id__lt=item['id'])

                else :
                    issued_amount = float(instance.issue.amount)
                    col = ErpReceiptCreditCollection.objects.filter(issue = instance.issue.id,receipt__bill_status= 1,id__lt=item['id'])

                col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
                for collection in col_data:
                    received_amount += (float(collection['received_amount']) + float(collection['discount_amount']))
                balance_amount = issued_amount - received_amount - float(item['received_amount']) - float(item['discount_amount'])
                item.update({
                     'bill_date': format_date(instance.receipt.bill_date),
                     'bill_no': instance.receipt.bill_no,
                     'customer_name': instance.receipt.customer.firstname,
                     'customer_mobile': instance.receipt.customer.mobile,
                     'branch_name':instance.receipt.branch.name,
                     'against' : 'Credit Invoice' if instance.issue == None else 'Credit Issue',
                      'amount' : item['received_amount'],
                     'issued_amount':issued_amount,
                     'received_amount':received_amount + float(item['received_amount']) + float(item['discount_amount']),
                     'balance_amount':balance_amount,
                })

            columns = get_reports_columns_template(request.user.pk,CREDIT_COLLECTION_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class AIReorderReportView(generics.GenericAPIView):
    

    def post(self, request,*args, **kwargs):
        reorder_details = []
        product_details = Product.objects.filter(status=1)
        for val in product_details:
            # Get current stock for the product
            try:
                to_date = '2024-09-26'
                query = F"""SELECT tag.tag_id,tag.tag_product_id_id,sum(tag.tag_pcs) as piece  FROM erp_tagging tag
                    LEFT JOIN erp_tag_log_details tl ON tl.tag_id_id  = tag.tag_id and tl.to_branch_id = 1
                    LEFT JOIN erp_tag_log_details tl2 ON tl2.tag_id_id  = tag.tag_id and tl2.id_tag_log > tl.id_tag_log 
                    WHERE  tl2.tag_id_id IS NULL and (tl.id_stock_status_id = 1 or tl.id_stock_status_id = 5)  
                    and tl.date <= ( "{to_date}")
                    and tag.tag_product_id_id = "{val.pro_id}"
                    Group by tag.tag_product_id_id
                    """

                stocks = ErpTagging.objects.raw(query)

            except ErpTagging.DoesNotExist:
                continue

            # Prepare sales data for this product
            queryset = ErpInvoiceSalesDetails.objects.filter(
                invoice_bill_id__invoice_status=1,
                id_product=val.pro_id,
                item_type=0
            ).values('invoice_bill_id__invoice_date').annotate(
                total_pieces=Sum('pieces')
            )
            if queryset:
                sales_data = pd.DataFrame(queryset)
                sales_data['invoice_bill_id__invoice_date'] = pd.to_datetime(sales_data['invoice_bill_id__invoice_date'], errors='coerce')
                if not sales_data.empty:
                    # Train the model with sales data
                    print(sales_data)
                    model = train_sales_model(sales_data)
                    
                    # Predict sales for the next 30 days
                    predicted_sales = predict_future_sales(model, days_from_now=30)
                    print(f'Predicted sales: {predicted_sales}')

                    top_supplier = Supplier.objects.filter(
                                    lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__isnull=False, 
                                    lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__item_type=0, 
                                    lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__invoice_bill_id__invoice_status=1,
                                    lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__id_product=val.pro_id,
                                ).annotate(
                                    total_sold_items=Sum('lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__pieces')
                                ).order_by('-total_sold_items').first()
                    
                    reorder_details.append({
                            'product': val.product_name,
                            'current_stock': stocks[0].piece,
                            'predicted_sales_next_30_days': predicted_sales,
                            'reorder_needed': True if predicted_sales > stocks[0].piece else False,
                            'top_supplier': {
                                'name': top_supplier.supplier_name if top_supplier else None,
                                'total_sold_items': top_supplier.total_sold_items if top_supplier else None,
                            }
                        })

        return Response(reorder_details, status=200)


class SalesPredictionReportView(generics.GenericAPIView):
    
    def post(self, request, *args, **kwargs):
        branch_date = BranchEntryDate()
        entry_date = branch_date.get_entry_date(request.data['branch_id'])
        from_date = request.data["from_date"]
        to_date = request.data["to_date"]
        reorder_details = []
        SALES_PREDICTION_REPORT = [
            {'accessor': 'product', 'Header': 'Product'},
            {'accessor': 'current_stock', 'Header': 'Available Pcs', 'text_align': 'right', 'is_total_req': True,},
            {'accessor': 'supplier_name', 'Header': 'Top Supplier'},
            {'accessor': 'total_sold_items', 'Header': 'Sold Items', 'text_align': 'right', 'is_total_req': True,},
        ]
        product_details = Product.objects.filter(status=1)
        days_list = [30, 60, 90]
        for days in days_list:
            sales_key = f"{days}_days"
            SALES_PREDICTION_REPORT.append({"accessor":sales_key,"Header":f"{days} days", 'text_align': 'right', 'is_total_req': True,})
        for val in product_details:
            # Get current stock for the product
            try:
                query = f"""
                    SELECT tag.tag_id, tag.tag_product_id_id, SUM(tag.tag_pcs) AS piece
                    FROM erp_tagging tag
                    LEFT JOIN erp_tag_log_details tl ON tl.tag_id_id = tag.tag_id 
                    AND tl.to_branch_id = {request.data["branch_id"]}
                    LEFT JOIN erp_tag_log_details tl2 ON tl2.tag_id_id = tag.tag_id 
                    AND tl2.id_tag_log > tl.id_tag_log 
                    WHERE tl2.tag_id_id IS NULL 
                    AND (tl.id_stock_status_id = 1 OR tl.id_stock_status_id = 5)  
                    AND tl.date <= "{from_date}" 
                    AND tag.tag_product_id_id = "{val.pro_id}" 
                    GROUP BY tag.tag_product_id_id
                """

                stocks = ErpTagging.objects.raw(query)

            except ErpTagging.DoesNotExist:
                continue

            # Prepare sales data for this product
            queryset = ErpInvoiceSalesDetails.objects.filter(
                invoice_bill_id__invoice_status=1,
                id_product=val.pro_id,
                item_type=0,
                invoice_bill_id__invoice_date__range=[from_date, to_date]
            ).values('invoice_bill_id__invoice_date').annotate(
                total_pieces=Sum('pieces')
            )

            if queryset:
                sales_data = pd.DataFrame(queryset)
                sales_data['invoice_bill_id__invoice_date'] = pd.to_datetime(sales_data['invoice_bill_id__invoice_date'], errors='coerce')
                
                if not sales_data.empty:
                    # Train the model with sales data
                    print(sales_data)
                    model = train_sales_model(sales_data)
                    
                    # Predict sales for the next 30, 60, 90 days
                    
                    predicted_sales = dynamic_predict_future_sales(model, days_list)

                    print(f'Predicted sales: {predicted_sales}')

                    # Get the top supplier
                    top_supplier = Supplier.objects.filter(
                        lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__isnull=False, 
                        lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__item_type=0, 
                        lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__invoice_bill_id__invoice_status=1,
                        lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__id_product=val.pro_id,
                    ).annotate(
                        total_sold_items=Sum('lot_supplier__lot_details__lot_inward_detail_id__sales_tag_id__pieces')
                    ).order_by('-total_sold_items').first()
                    
                    # Initialize details for this product
                    product_reorder_details = {
                        'product': val.product_name,
                        'current_stock': stocks[0].piece if stocks else 0,  # Handle case when no stock
                        'predicted_sales': {},  # This will hold sales prediction for each period
                        'reorder_needed': {},  # This will hold reorder status for each period
                        'supplier_name': top_supplier.supplier_name if top_supplier else None,
                        'total_sold_items': top_supplier.total_sold_items if top_supplier else None,
                    }

                    # Loop through days_list to predict sales and check if reorder is needed
                    for days in days_list:
                        sales_key = f"{days}_days"
                        sales_value = predicted_sales.get(sales_key, 0) # Get the predicted sales for that period
                        reorder_status = sales_value > product_reorder_details['current_stock']  # Compare predicted sales with stock

                        # Add predicted sales and reorder status for this period
                        sales_value = format_number_with_decimal(predicted_sales.get(sales_key, 0),2)
                        product_reorder_details[sales_key] = sales_value
                        product_reorder_details['reorder_needed'][sales_key] = reorder_status

                    # Append the product reorder details to the reorder_details list
                    reorder_details.append(product_reorder_details)

    
            
        return Response({"columns":SALES_PREDICTION_REPORT,"reorder_details":reorder_details}, status=200)
    
class AdvanceAdjReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpReceiptAdvanceAdj.objects.filter(invoice_bill_id__invoice_status = 1)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = 0)


            paginator, page = pagination.paginate_queryset(queryset, request,None,ADVANCE_ADJ_REPORT)

            data = ErpReceiptAdvanceAdjSerializer(page,many=True).data

            response_data = []

            for item, instance in zip(data, queryset):
                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = item["invoice_bill_id"])
                inv_data = ErpInvoiceSerializer(inv_queryset,context={"invoice_no":True}).data

                response_data.append({
                     'bill_date': format_date(instance.receipt.bill_date),
                     'bill_no': instance.receipt.bill_no,
                     "adj_invoice_no" : inv_data['inv_no']['invoice_no'],
                     'customer_name': instance.receipt.customer.firstname,
                     'customer_mobile': instance.receipt.customer.mobile,
                     'branch_name':instance.receipt.branch.name,
                     'amount' : item['adj_amount'],
                })

            columns = get_reports_columns_template(request.user.pk,ADVANCE_ADJ_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class ChitAdjReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoiceSchemeAdjusted.objects.filter(invoice_bill_id__invoice_status = 1)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            
            if  bill_setting_type == 1:
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = 0)

            paginator, page = pagination.paginate_queryset(queryset, request,None,CHIT_ADJ_REPORT)

            data = ErpInvoiceSchemeAdjustedSerializer(page,many=True).data

            

            for item, instance in zip(data, queryset):
                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = item["invoice_bill_id"])
                inv_data = ErpInvoiceSerializer(inv_queryset,context={"invoice_no":True}).data
                item.update({
                     'bill_date': format_date(instance.invoice_bill_id.invoice_date),
                     'bill_no': inv_data['inv_no']['invoice_no'],
                     'customer_name': instance.invoice_bill_id.id_customer.firstname,
                     'customer_mobile': instance.invoice_bill_id.id_customer.mobile,
                     'branch_name':instance.invoice_bill_id.id_branch.name,
                     'amount' : instance.id_scheme_account.closing_amount,
                     'paid_installment': instance.id_scheme_account.total_paid_ins,
                     'total_installment': str(instance.id_scheme_account.total_paid_ins) + '/' + str(instance.id_scheme_account.acc_scheme_id.total_instalment) ,
                     'scheme_name': instance.id_scheme_account.acc_scheme_id.scheme_name,
                })

            columns = get_reports_columns_template(request.user.pk,CHIT_ADJ_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

class AdvanceRefundReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpReceiptRefund.objects.filter(issue__bill_status = 1)

            if(id_branch):
                queryset  = queryset.filter(issue__branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(issue__bill_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                queryset = queryset.filter(issue__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(issue__setting_bill_type = 0)


            paginator, page = pagination.paginate_queryset(queryset, request,None,ADV_REFUND_REPORT)

            data = ErpReceiptRefundSerializer(page,many=True).data

            

            for item, instance in zip(data, queryset):

                item.update({
                     'bill_date': format_date(instance.issue.bill_date),
                     'bill_no': instance.issue.bill_no,
                     'customer_name': instance.issue.customer.firstname,
                     'customer_mobile': instance.issue.customer.mobile,
                     'branch_name':instance.issue.branch.name,
                     'advance_bill_no' : instance.receipt.bill_no,
                      'amount' : item['refund_amount'],
                })

            columns = get_reports_columns_template(request.user.pk,ADV_REFUND_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

class SalesReturnReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        metal = request.data.get('id_metal')
        Product = request.data.get('product')
        id_counter = request.data.get('id_counter')
        report_type = int(request.data.get('optional_type', 1))
        if report_type == '':
            report_type =0
        elif report_type:
            report_type = int(report_type)
        groupingColumns = []

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:


            if (report_type == 2):
                queryset = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id__invoice_status = 1,
                                                            invoice_bill_id__setting_bill_type = bill_setting_type).order_by("id_product")

                if(id_branch):
                    queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)


                if from_date and to_date:
                    queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
                
                if metal:
                    queryset = queryset.filter(id_product__id_metal=metal)

                if Product:
                    queryset = queryset.filter(id_product=Product)

                paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_RETURN_REPORT)

                data = ErpInvoiceSalesReturnSerializer(page,many=True).data

                response_data=[]

                for item, instance in zip(data, queryset):

                    if instance.invoice_bill_id :
                        inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)
                        inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                        inv_data = get_invoice_no(inv_serializer)
                    else :
                        inv_data ={}
                        inv_serializer = {}
                    

                    weight_range = WeightRange.objects.filter(from_weight__lt=instance.net_wt,to_weight__gt=instance.net_wt,id_product=instance.id_product).first()
                    if(weight_range):
                        item['weight_range'] = weight_range.weight_range_name
                    else:
                        item['weight_range'] = ''


                    mc_type_display = instance.get_mc_type_display()
                    item['mc_type_name'] = mc_type_display
                    item['calculation_type_name'] = ""

                    response_data.append({
                        **inv_serializer,
                        'invoice_date': format_date(inv_serializer['invoice_date']),
                        **item,
                        **inv_data,
                        'tag_code': instance.invoice_sale_item_id.tag_id.tag_code if instance.invoice_sale_item_id and instance.invoice_sale_item_id.tag_id  else None,
                        'size_name': instance.invoice_sale_item_id.tag_id.size.name if instance.invoice_sale_item_id and instance.invoice_sale_item_id.tag_id and instance.invoice_sale_item_id.tag_id.size  else None,
                        'product_name': instance.id_product.product_name if instance.id_product.product_name else None,
                        'metal_name': instance.id_product.id_metal.metal_name if instance.id_product and instance.id_product.id_metal.metal_name else None,
                    })
                columns = get_reports_columns_template(request.user.pk,SALES_RETURN_REPORT,request.data["path_name"])         

                groupingColumns = ["product_name"]  

            elif report_type == 1 :
                queryset = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id__invoice_status = 1,
                                                            invoice_bill_id__setting_bill_type = bill_setting_type).order_by("id_product")

                if(id_branch):
                    queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)


                if from_date and to_date:
                    queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
                
                if metal:
                    queryset = queryset.filter(id_product__id_metal=metal)

                if Product:
                    queryset = queryset.filter(id_product=Product)
                queryset = queryset.values("id_product").annotate(
                    product_name=F('id_product__product_name'),
                    metal_name=F('id_product__id_metal__metal_name'),
                    pieces=Sum('pieces'),
                    gross_wt=Sum('gross_wt'),
                    less_wt=Sum('less_wt'),
                    net_wt=Sum('net_wt'),
                    stone_wt=Sum('stone_wt'),
                    dia_wt=Sum('dia_wt'),
                    item_cost=Sum('item_cost'),
                    rate_per_gram=Avg('rate_per_gram')
                )
                paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_RETURN_SUMMARY_REPORT)

                #data = ErpInvoiceSalesReturnSerializer(page,many=True).data

                response_data=queryset


                columns = get_reports_columns_template(request.user.pk,SALES_RETURN_SUMMARY_REPORT,request.data["path_name"])           
                
                groupingColumns = []  


            elif report_type == 5:
                branch = ",".join(map(str, id_branch))
                bill_setting_type_filter = ''
                if  bill_setting_type == 1:
                    bill_setting_type_filter = 'and inv.setting_bill_type = 1'
                elif bill_setting_type == 0: 
                    bill_setting_type_filter = 'and inv.setting_bill_type = 0'

                if metal:
                    bill_setting_type_filter += f' and pro.id_metal_id = {metal}'

                if Product:
                    bill_setting_type_filter += f' and pro.pro_id = {Product}'
                
                queryset = (
                    F"""SELECT
                        pro.product_name,
                        des.design_name,
                        IFNULL(size.name,'') as size_name,
                        wt.weight_range_name,
                        COALESCE(SUM(sa.pieces), 0) AS pieces,
                        COALESCE(SUM(sa.gross_wt), 0) AS gross_wt,
                        COALESCE(SUM(sa.net_wt), 0) AS net_wt,
                        COALESCE(SUM(sa.dia_wt), 0) AS dia_wt,
                        COALESCE(SUM(sa.stone_wt), 0) AS stone_wt,
                        COALESCE(SUM(sa.item_cost), 0) AS tot_amount,
                        COALESCE(SUM(sa.tax_amount), 0) AS tax,
                        COALESCE(SUM(sa.taxable_amount), 0) AS taxable,
                        COALESCE(SUM(sa.less_wt), 0) AS lesswt,
                        COALESCE(SUM(sa.wastage_weight), 0) AS wastage_wt
                    FROM erp_invoice_sales_return_details sa 
                    LEFT JOIN erp_invoice_sales_details rs ON rs.invoice_sale_item_id = sa.invoice_sale_item_id_id
                    LEFT JOIN erp_invoice inv ON inv.erp_invoice_id = sa.invoice_bill_id_id
                    LEFT JOIN erp_tagging tag ON tag.tag_id = rs.tag_id_id
                    LEFT JOIN erp_product pro ON pro.pro_id = sa.id_product_id
                    LEFT JOIN erp_design des ON des.id_design = sa.id_design_id
                    LEFT JOIN erp_sub_design sub ON sub.id_sub_design = sa.id_sub_design_id
                    LEFT JOIN erp_size size ON size.id_size = tag.size_id
                    LEFT JOIN erp_weight_range wt ON wt.id_product_id = sa.id_product_id and wt.from_weight <= sa.net_wt and wt.to_weight >= sa.net_wt
                    WHERE 
                    inv.invoice_status = 1 and tag.size_id IS NOT NULL and wt.id_weight_range IS NOT NULL
                    and inv.id_branch_id in ({branch})
                    AND inv.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                    {bill_setting_type_filter}
                    GROUP BY sa.id_product_id,wt.id_weight_range,tag.size_id 
                    Order By sa.id_product_id ASC,wt.from_weight ASC, CAST(size.value AS UNSIGNED) ASC"""
                )
                print(bill_setting_type_filter)
                print(queryset)

                result = generate_query_result(queryset)

                paginator, page = pagination.paginate_queryset(result, request,None,SALES_SIZE_REPORT)

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_SIZE_REPORT,request.data["path_name"])
                groupingColumns = ["product_name","weight_range_name"]  

            elif report_type == 3:
                branch = ",".join(map(str, id_branch))
                bill_setting_type_filter = ''
                if  bill_setting_type == 1:
                    bill_setting_type_filter = 'and inv.setting_bill_type = 1'
                elif bill_setting_type == 0: 
                    bill_setting_type_filter = 'and inv.setting_bill_type = 0'

                if metal:
                    bill_setting_type_filter += f' and pro.id_metal_id = {metal}'

                if Product:
                    bill_setting_type_filter += f' and pro.pro_id = {Product}'
                
                queryset = (
                    F"""SELECT
                        pro.product_name,
                        des.design_name,
                        IFNULL(size.name,'') as size_name,
                        wt.weight_range_name,
                        COALESCE(SUM(sa.pieces), 0) AS pieces,
                        COALESCE(SUM(sa.gross_wt), 0) AS gross_wt,
                        COALESCE(SUM(sa.net_wt), 0) AS net_wt,
                        COALESCE(SUM(sa.dia_wt), 0) AS dia_wt,
                        COALESCE(SUM(sa.stone_wt), 0) AS stone_wt,
                        COALESCE(SUM(sa.item_cost), 0) AS tot_amount,
                        COALESCE(SUM(sa.tax_amount), 0) AS tax,
                        COALESCE(SUM(sa.taxable_amount), 0) AS taxable,
                        COALESCE(SUM(sa.less_wt), 0) AS lesswt,
                        COALESCE(SUM(sa.wastage_weight), 0) AS wastage_wt
                    FROM erp_invoice_sales_return_details sa 
                    LEFT JOIN erp_invoice_sales_details rs ON rs.invoice_sale_item_id = sa.invoice_sale_item_id_id
                    LEFT JOIN erp_invoice inv ON inv.erp_invoice_id = sa.invoice_bill_id_id
                    LEFT JOIN erp_tagging tag ON tag.tag_id = rs.tag_id_id
                    LEFT JOIN erp_product pro ON pro.pro_id = sa.id_product_id
                    LEFT JOIN erp_design des ON des.id_design = sa.id_design_id
                    LEFT JOIN erp_sub_design sub ON sub.id_sub_design = sa.id_sub_design_id
                    LEFT JOIN erp_size size ON size.id_size = tag.size_id
                    LEFT JOIN erp_weight_range wt ON wt.id_product_id = sa.id_product_id and wt.from_weight <= sa.net_wt and wt.to_weight >= sa.net_wt
                    WHERE 
                    inv.invoice_status = 1 and wt.id_weight_range IS NOT NULL
                    and inv.id_branch_id in ({branch})
                    AND inv.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                    {bill_setting_type_filter}
                    GROUP BY sa.id_product_id,wt.id_weight_range
                    Order By sa.id_product_id ASC,wt.from_weight ASC"""
                )
                print(bill_setting_type_filter)
                print(queryset)

                result = generate_query_result(queryset)

                paginator, page = pagination.paginate_queryset(result, request,None,SALES_SIZE_REPORT)

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_SIZE_REPORT,request.data["path_name"])
                groupingColumns = ["product_name"]  

            else :
                branch = ",".join(map(str, id_branch))
                bill_setting_type_filter = ''
                if  bill_setting_type == 1:
                    bill_setting_type_filter = 'and inv.setting_bill_type = 1'
                elif bill_setting_type == 0: 
                    bill_setting_type_filter = 'and inv.setting_bill_type = 0'

                if metal:
                    bill_setting_type_filter += f' and pro.id_metal_id = {metal}'

                if Product:
                    bill_setting_type_filter += f' and pro.pro_id = {Product}'
                
                queryset = (
                    F"""SELECT
                        pro.product_name,
                        des.design_name,
                        IFNULL(size.name,'') as size_name,
                        COALESCE(SUM(sa.pieces), 0) AS pieces,
                        COALESCE(SUM(sa.gross_wt), 0) AS gross_wt,
                        COALESCE(SUM(sa.net_wt), 0) AS net_wt,
                        COALESCE(SUM(sa.dia_wt), 0) AS dia_wt,
                        COALESCE(SUM(sa.stone_wt), 0) AS stone_wt,
                        COALESCE(SUM(sa.item_cost), 0) AS tot_amount,
                        COALESCE(SUM(sa.tax_amount), 0) AS tax,
                        COALESCE(SUM(sa.taxable_amount), 0) AS taxable,
                        COALESCE(SUM(sa.less_wt), 0) AS lesswt,
                        COALESCE(SUM(sa.wastage_weight), 0) AS wastage_wt
                    FROM erp_invoice_sales_return_details sa 
                    LEFT JOIN erp_invoice_sales_details rs ON rs.invoice_sale_item_id = sa.invoice_sale_item_id_id
                    LEFT JOIN erp_invoice inv ON inv.erp_invoice_id = sa.invoice_bill_id_id
                    LEFT JOIN erp_tagging tag ON tag.tag_id = rs.tag_id_id
                    LEFT JOIN erp_product pro ON pro.pro_id = sa.id_product_id
                    LEFT JOIN erp_design des ON des.id_design = sa.id_design_id
                    LEFT JOIN erp_sub_design sub ON sub.id_sub_design = sa.id_sub_design_id
                    LEFT JOIN erp_size size ON size.id_size = tag.size_id
                    WHERE
                    inv.invoice_status = 1 and tag.size_id IS NOT NULL
                    and inv.id_branch_id in ({branch})
                    AND inv.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                    {bill_setting_type_filter}
                    GROUP BY sa.id_product_id,tag.size_id 
                    Order By sa.id_product_id ASC, CAST(size.value AS UNSIGNED) ASC"""
                )
                print(bill_setting_type_filter)
                print(queryset)

                result = generate_query_result(queryset)

                paginator, page = pagination.paginate_queryset(result, request,None,SALES_SIZE_REPORT)
                groupingColumns = ["product_name"]  

                response_data = list(page)
                columns = get_reports_columns_template(request.user.pk,SALES_SIZE_REPORT,request.data["path_name"])

            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isProductFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            filters_copy['isOpionalFilterReq'] = True
            filters_copy['isCounterFilterReq'] = True
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'groupingColumns': groupingColumns,
                'filters':filters_copy,
                'optionalType':[
                    { "value": 1, "label": "Product" },
                    { "value": 2, "label": "Item Wise" },
                    { "value": 3, "label": "Weight Range" },
                    { "value": 4, "label": "Size" },
                    { "value": 5, "label": "Weight Range and Size" },
                ]
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
   
class EmployeeSalesReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        metal = request.data.get('id_metal')
        Product = request.data.get('product')
        employee = request.data.get('filterEmployee')

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1)


            if  bill_setting_type == 1 or bill_setting_type == 0:
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = bill_setting_type)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            
            if metal:
                queryset = queryset.filter(id_product_id__id_metal=metal)

            if Product:
                queryset = queryset.filter(id_product_id=Product)
            
            if(employee):
                queryset = queryset.filter(invoice_bill_id__id_employee=employee)


            paginator, page = pagination.paginate_queryset(queryset, request,None,EMPLOYEE_SALES_REPORT)

            data = ErpInvoiceSalesDetailsSerializer(page,many=True).data

            print(data)


            response_data=[]

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

                inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                 
                inv_data = get_invoice_no(inv_serializer)
                emp = instance.ref_emp_id.firstname if instance.ref_emp_id else None
                tag_tax_grp = instance.tax_group_id.tgi_tgrpcode.tgrp_name if instance.tax_group_id else None
                mc_type_display = instance.get_mc_type_display()
                metal_name = instance.id_product.id_metal.metal_name if instance.id_product and instance.id_product.id_metal.metal_name else None
                product_name = instance.id_product.product_name if instance.id_product.product_name else None

                # tag_calculation_type_name = instance.calculation_type.name if instance.calculation_type else None
                item['emp_name'] = emp
                item['tax_grp'] = tag_tax_grp
                item['mc_type_name'] = mc_type_display
                item['calculation_type_name'] = ""
                item['metal_name'] = metal_name
                item['product_name'] = product_name
                response_data.append({
                    **inv_serializer,
                    'invoice_date': format_date(inv_serializer['invoice_date']),
                    **item,
                    **inv_data,
                    'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                    'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                })
            columns = get_reports_columns_template(request.user.pk,EMPLOYEE_SALES_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isMetalFilterReq'] = True
            filters_copy['isProductFilterReq'] = True
            filters_copy['isEmployeeFilterReq'] = True
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'groupingColumns': ["emp_name"],
                'filters':filters_copy

                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

class PettyCashReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpIssueReceipt.objects.filter(bill_status = 1,issue_type = 3)

            if(id_branch):
                queryset  = queryset.filter(branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(bill_date__range=[from_date, to_date])

            
            if  bill_setting_type == 1 or bill_setting_type == 0:
                queryset = queryset.filter(setting_bill_type = bill_setting_type)


            paginator, page = pagination.paginate_queryset(queryset, request,None,PETTY_CASH_REPORT)

            data = ErpIssueReceiptSerializer(page,many=True).data

            

            for item, instance in zip(data, queryset):

                item.update({
                     'bill_date': format_date(instance.bill_date),
                     'borrower_name': instance.customer.firstname if instance.issue_to == 1 else instance.employee.firstname,
                     'borrower_mobile': instance.customer.mobile if instance.issue_to == 1 else instance.employee.mobile,
                     'branch_name':instance.branch.name,
                     'issue_to': dict(instance.ISSUE_TO_CHOICES).get(instance.issue_to, ''),
                })

            columns = get_reports_columns_template(request.user.pk,PETTY_CASH_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class CreditPendingReportAPIViewNew(generics.GenericAPIView):

    permission_classes = [IsEmployee]

    def  post(self, request, *args, **kwargs):

        with connection.cursor() as cursor:
                sql = F""" 
                    SELECT 
                        r.id,r.firstname as cus_name,r.mobile,r.bill_no,
                        r.total_credit_amount,
                        COALESCE(recd.paid_amount, 0) AS paid_amount
                    FROM (
                        SELECT 
                            i.id,c.firstname,c.mobile,i.bill_no,
                            SUM(i.amount) AS total_credit_amount
                        FROM erp_issue_receipt i
                        left join customers c on c.id_customer = i.customer_id
                        WHERE i.issue_type = 1 AND i.customer_id IS NOT NULL
                        GROUP BY i.id
                    ) r
                    LEFT JOIN (
                        SELECT 
                            rcc.issue_id,
                            SUM(rcc.received_amount) AS paid_amount
                        FROM erp_receipt_credit_collection rcc
                        LEFT JOIN erp_issue_receipt recpt ON recpt.id = rcc.receipt_id
                        where recpt.bill_status = 1
                        GROUP BY rcc.issue_id
                    ) recd ON recd.issue_id = r.id;

                    """
                cursor.execute(sql)
                response_data = None
                if cursor.description:
                    result = cursor.fetchall()
                    field_names = [desc[0] for desc in cursor.description]
                    report_data = []
                    for row in result:
                        field_value = dict(zip(field_names, row))
                        report_data.append(field_value)
                    response_data = report_data
                return response_data



class CreditPendingReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            #queryset = ErpInvoice.objects.filter(is_credit = 1,credit_status = 0,invoice_status = 1)
            bill_setting_type_filter =''
            if  bill_setting_type == 1 or bill_setting_type == 0:
                bill_setting_type_filter = F" and inv.setting_bill_type = {bill_setting_type}"
            id_branch = ",".join(map(str, id_branch))
            queryset = ErpInvoice.objects.raw(
                F"""Select inv.* FROM erp_invoice inv
                    LEFT JOIN erp_invoice_sales_details sal ON sal.invoice_bill_id_id = inv.erp_invoice_id
                  WHere inv.is_credit = 1 and inv.credit_status = 0 and inv.invoice_status = 1 and inv.due_amount > 0
                  and inv.id_branch_id in ({id_branch})
                  {bill_setting_type_filter}
                  Group By inv.erp_invoice_id"""
            )

            # if(id_branch):
            #     queryset  = queryset.filter(id_branch__in = id_branch)


            # if from_date and to_date:
            #     queryset = queryset.filter(invoice_date__range=[from_date, to_date])


            paginator, page = pagination.paginate_queryset(queryset, request,None,CREDIT_PENDING_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={"invoice_no":True}).data

            for inv in data:
                received_amount = 0
                balance_amount =0
                issued_amount = float(inv["due_amount"])
                col = ErpReceiptCreditCollection.objects.filter(invoice_bill_id = inv["erp_invoice_id"] ,receipt__bill_status= 1)
                col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
                for collection in col_data:
                    received_amount += (float(collection['received_amount']) + float(collection['discount_amount']))
                balance_amount = issued_amount - received_amount
                inv.update({
                    'invoice_no': inv['inv_no']['invoice_no'],
                    'invoice_date': format_date(inv['invoice_date']),
                    'issued_amount':issued_amount,
                    'collected_amount':received_amount,
                    'balance_amount':balance_amount,
                })

            columns = get_reports_columns_template(request.user.pk,CREDIT_PENDING_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = False
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

class CreditIssuedPendingReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpIssueReceipt.objects.filter(issue_type = 1,bill_status = 1)

            if  bill_setting_type == 1 or bill_setting_type == 0:
                queryset = queryset.filter(setting_bill_type = bill_setting_type)

            if(id_branch):
                queryset  = queryset.filter(branch__in = id_branch)


            # if from_date and to_date:
            #     queryset = queryset.filter(invoice_date__range=[from_date, to_date])


            paginator, page = pagination.paginate_queryset(queryset, request,None,CREDIT_ISSUED_PENDING_REPORT)

            data = ErpIssueReceiptSerializer(page,many=True,context={"invoice_no":True}).data
            return_data = []
            for item, instance in zip(data, queryset):
                received_amount = 0
                balance_amount =0
                issued_amount = float(item["amount"])
                col = ErpReceiptCreditCollection.objects.filter(issue = item["id"] ,receipt__bill_status= 1)
                col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
                for collection in col_data:
                    received_amount += (float(collection['received_amount']) + float(collection['discount_amount']))
                balance_amount = issued_amount - received_amount
                item.update({
                    'bill_date': format_date(instance.bill_date),
                    'bill_no': instance.bill_no,
                    'customer_name': instance.customer.firstname if (instance.customer) else '',
                    'customer_mobile': instance.customer.mobile if (instance.customer) else '',
                    'branch_name':instance.branch.name,
                    'issued_amount':issued_amount,
                    'collected_amount':received_amount,
                    'balance_amount':balance_amount,
                    'remarks': instance.remarks if (instance.remarks) else '',
                })
                if(balance_amount > 0):
                    return_data.append(item)

            columns = get_reports_columns_template(request.user.pk,CREDIT_ISSUED_PENDING_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = False
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(return_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class PartlySalesReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1,is_partial_sale = 1)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            
            if bill_setting_type == 1 or bill_setting_type == 0:
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = bill_setting_type)

            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

           # queryset = queryset.select_related('transfer_from', 'transfer_to').order_by('id_stock_transfer')

            paginator, page = pagination.paginate_queryset(queryset, request,None,PARTLY_SALES_REPORT)

            data = ErpInvoiceSalesDetailsSerializer(page,many=True).data

            print(data)


            response_data=[]

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

                inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                 
                inv_data = get_invoice_no(inv_serializer)
                #purity = instance.purity_id.purity if instance.tag_purity_id else None
                tag_tax_grp = instance.tax_group_id.tgi_tgrpcode.tgrp_name if instance.tax_group_id else None
                mc_type_display = instance.get_mc_type_display()
                # tag_calculation_type_name = instance.calculation_type.name if instance.calculation_type else None
                #item['tag_purity'] = purity
                item['tax_grp'] = tag_tax_grp
                item['mc_type_name'] = mc_type_display
                item['calculation_type_name'] = ""

                response_data.append({
                    **inv_serializer,
                    'invoice_date': format_date(inv_serializer['invoice_date']),
                    **item,
                    **inv_data,
                    'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                    'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                    'tag_gwt': instance.tag_id.tag_gwt,
                    'tag_nwt': instance.tag_id.tag_nwt,
                    'tag_lwt': instance.tag_id.tag_lwt,
                    'tag_dia_wt': instance.tag_id.tag_dia_wt,
                    'tag_stn_wt': instance.tag_id.tag_stn_wt,
                    'tag_pcs': instance.tag_id.tag_pcs,
                    'tag_other_metal_wt': instance.tag_id.tag_other_metal_wt,
                })
            columns = get_reports_columns_template(request.user.pk,PARTLY_SALES_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class TagWiseProfitReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1,item_type = 0)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)

            if bill_setting_type == 1 or bill_setting_type == 0:
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = bill_setting_type)

            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

           # queryset = queryset.select_related('transfer_from', 'transfer_to').order_by('id_stock_transfer')

            paginator, page = pagination.paginate_queryset(queryset, request,None,TAG_WISE_PROFIT_REPORT)

            data = ErpInvoiceSalesDetailsSerializer(page,many=True).data

            print(data)


            response_data=[]

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

                inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                 
                inv_data = get_invoice_no(inv_serializer)
                #purity = instance.purity_id.purity if instance.tag_purity_id else None
                tag_tax_grp = instance.tax_group_id.tgi_tgrpcode.tgrp_name if instance.tax_group_id else None
                mc_type_display = instance.get_mc_type_display()
                # tag_calculation_type_name = instance.calculation_type.name if instance.calculation_type else None
                #item['tag_purity'] = purity
                item['tax_grp'] = tag_tax_grp
                item['mc_type_name'] = mc_type_display
                item['calculation_type_name'] = ""

                response_data.append({
                    **inv_serializer,
                    'invoice_date': format_date(inv_serializer['invoice_date']),
                    **item,
                    **inv_data,
                    'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                    'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                    'tag_pure_wt': instance.tag_id.tag_pure_wt,
                    'tag_purchase_mc': instance.tag_id.tag_purchase_mc,
                    'tag_purchase_mc_type': instance.tag_id.tag_purchase_mc_type,
                    'tag_purchase_va': instance.tag_id.tag_purchase_va,
                    'tag_purchase_touch': instance.tag_id.tag_purchase_touch,
                    'tag_purchase_calc_type': instance.tag_id.tag_purchase_calc_type,
                    'tag_purchase_rate': instance.tag_id.tag_purchase_rate,
                    'tag_purchase_rate_calc_type': instance.tag_id.tag_purchase_rate_calc_type,
                    'tag_purchase_cost': instance.tag_id.tag_purchase_cost,
                    'profit_cost': float(item["item_cost"]) - float(instance.tag_id.tag_purchase_cost),

                })
            columns = get_reports_columns_template(request.user.pk,TAG_WISE_PROFIT_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class KarigarWiseSalesReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1,item_type = 0)

            if(id_branch):
                queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)

            if bill_setting_type == 1 or bill_setting_type == 0:
                queryset = queryset.filter(invoice_bill_id__setting_bill_type = bill_setting_type)

            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

           # queryset = queryset.select_related('transfer_from', 'transfer_to').order_by('id_stock_transfer')

            paginator, page = pagination.paginate_queryset(queryset, request,None,SUPPLIER_WISE_SALES_REPORT)

            data = ErpInvoiceSalesDetailsSerializer(page,many=True).data

            print(data)


            response_data=[]

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

                inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                 
                inv_data = get_invoice_no(inv_serializer)
                #purity = instance.purity_id.purity if instance.tag_purity_id else None
                tag_tax_grp = instance.tax_group_id.tgi_tgrpcode.tgrp_name if instance.tax_group_id else None
                mc_type_display = instance.get_mc_type_display()
                # tag_calculation_type_name = instance.calculation_type.name if instance.calculation_type else None
                #item['tag_purity'] = purity
                item['tax_grp'] = tag_tax_grp
                item['mc_type_name'] = mc_type_display
                item['calculation_type_name'] = ""

                response_data.append({
                    **inv_serializer,
                    'invoice_date': format_date(inv_serializer['invoice_date']),
                    **item,
                    **inv_data,
                    'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                    'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                    'supplier_name': instance.tag_id.tag_lot_inward_details.lot_no.id_supplier.supplier_name if instance.tag_id.tag_lot_inward_details.lot_no.id_supplier else None,

                })
            columns = get_reports_columns_template(request.user.pk,SUPPLIER_WISE_SALES_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'groupingColumns': ["supplier_name"],
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class CancelBillsReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(invoice_status = 2)

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])


            paginator, page = pagination.paginate_queryset(queryset, request,None,CANCEL_BILLS_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={'invoice_no':True}).data

            response_data = []

            for item, instance in zip(data, queryset):

                response_data.append({
                    **item,
                    "emp_name" : instance.canceled_by.employee.firstname,
                    "canceled_on" : date_format_with_time(instance.canceled_on),
                    "remarks":instance.canceled_reason,
                    "invoice_no" : item['inv_no']['invoice_no']
                })
            columns = get_reports_columns_template(request.user.pk,CANCEL_BILLS_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

class DiscountBillsReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(invoice_status = 1,total_discount_amount__gt=0)

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])


            paginator, page = pagination.paginate_queryset(queryset, request,None,DISCOUNT_BILLS_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={'invoice_no':True}).data

            response_data = []

            for item, instance in zip(data, queryset):

                response_data.append({
                    **item,
                    "discount_per": format_number_with_decimal((( float(item["total_discount_amount"]) / float(item["sales_amount"]) ) * 100),2),
                    "emp_name" : instance.created_by.employee.firstname,
                    "invoice_no" : item['inv_no']['invoice_no']
                })
            columns = get_reports_columns_template(request.user.pk,DISCOUNT_BILLS_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class BillWiseTransactionReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_counter = request.data.get('id_counter')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        report_col = copy.deepcopy(BILLWISE_TRANSACTION_REPORT)

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(invoice_status = 1, setting_bill_type=bill_setting_type)

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)

            if(id_counter):
                queryset  = queryset.filter(id_counter = id_counter)


            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                queryset = queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(setting_bill_type = 0)

            paginator, page = pagination.paginate_queryset(queryset, request,None,BILLWISE_TRANSACTION_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={'invoice_no':True}).data

            payment_modes = PaymentMode.objects.filter(is_active=True).values('id_mode', 'mode_name', 'short_code')

            for mode in payment_modes:
                report_col.append({'accessor': mode["short_code"], 'Header': mode["mode_name"],'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True})

            report_col.append({'accessor': "chit_adj", 'Header': "Chit Adj",'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True})
            report_col.append({'accessor': "adv_adj", 'Header': "Advance Adj",'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True})
            report_col.append({'accessor': "deposit_amt", 'Header': "Deposit Amt",'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True})
           # report_col.append({'accessor': "refund_amount", 'Header': "Refunded",'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True})
            report_col.append({'accessor': "due_amount", 'Header': "Due Amount",'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True})
            report_col.append({'accessor': "gift_adj", 'Header': "Gift Adj",'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True})
            
            report_col.append({'accessor': 'received_amount', 'Header': 'Received Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
)

            
            response_data = []

            for item, instance in zip(data, queryset):

                chit_adjusted = adv_adjusted = deposit_amt = gift_adjusted = 0 

                paymentmodewise = {}

                chit_adj_data = ErpInvoiceSchemeAdjusted.objects.filter(invoice_bill_id= item["erp_invoice_id"]).aggregate(chit_amount=Sum('id_scheme_account__closing_amount'))
 
                if(chit_adj_data['chit_amount']):
                    chit_adjusted = chit_adj_data['chit_amount']
                    
                gift_adj_data = ErpInvoiceGiftDetails.objects.filter(invoice_bill_id= item["erp_invoice_id"]).aggregate(gift_amount=Sum('amount'))
                
                if(gift_adj_data['gift_amount']):
                    gift_adjusted = gift_adj_data['gift_amount']
                
                adv_adj_data  = instance.advance_adj_invoices.all()

                for adv in adv_adj_data:
                    adv_adjusted += float(adv.adj_amount)

                inv_payment_queryset = ErpInvoicePaymentModeDetail.objects.filter(invoice_bill_id= item["erp_invoice_id"]).values('payment_mode').annotate(
                    total_amount=Sum(
                        Case(
                            When(payment_type=1, then=F('payment_amount')),
                            default=-F('payment_amount'),
                        )
                    ),
                    payment_type=F('payment_type'),
                    mode_name=F('payment_mode__short_code'),
                    mode=F('payment_mode')
                )

                inv_payment_data = list(inv_payment_queryset)

                for pay in inv_payment_data:
                    paymentmodewise.update({
                      pay["mode_name"] :pay["total_amount"] 
                    })

                deposit_data  = instance.deposit_bill.first()

                if(deposit_data and deposit_data.type == 2):
                    deposit_amt = deposit_data.amount
                


                response_data.append({
                    **item,
                    "invoice_date": item['date'],
                    "adv_adj" :adv_adjusted,
                    "chit_adj":chit_adjusted,
                    "gift_adj":gift_adjusted,
                    "deposit_amt":deposit_amt,
                    "emp_name" : instance.id_employee.firstname,
                    "invoice_no" : item['inv_no']['invoice_no'],
                    **paymentmodewise
                })
            columns = get_reports_columns_template(request.user.pk,report_col,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isCounterFilterReq'] = True

            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
                'groupingColumns': ["counter_name"],
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class SalesAndReturnGstAbstractReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(invoice_status = 1)

            if  bill_setting_type == 1:
                queryset = queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(setting_bill_type = 0)

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])


            paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_AND_SALES_RETURN_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={'invoice_no':True}).data

            response_data = []

            for item, instance in zip(data, queryset):

                inv_sales_queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id = instance.erp_invoice_id).annotate( 
                            taxable=Sum('taxable_amount'),
                            tax=Sum('tax_amount'),
                            cgst=Sum('cgst_cost'),
                            sgst=Sum('sgst_cost'),
                            igst=Sum('igst_cost'),
                            cost=Sum('item_cost'),
                            ).values(
                                'invoice_bill_id',
                                'taxable',
                                'tax', 
                                'cgst',
                                'sgst',
                                'igst',
                                'cost',
                            ).first()

                inv_return_queryset = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id = instance.erp_invoice_id).annotate( 
                            taxable=Sum('invoice_sale_item_id__taxable_amount'),
                            tax=Sum('invoice_sale_item_id__tax_amount'),
                            cgst=Sum('invoice_sale_item_id__cgst_cost'),
                            sgst=Sum('invoice_sale_item_id__sgst_cost'),
                            igst=Sum('invoice_sale_item_id__igst_cost'),
                            cost=Sum('invoice_sale_item_id__item_cost'),
                            ).values(
                                'invoice_bill_id',
                                'taxable',
                                'tax', 
                                'cgst',
                                'sgst',
                                'igst',
                                'cost',
                            ).first()

                if(inv_sales_queryset):
                    invsales = dict(inv_sales_queryset)

                    response_data.append({
                        **item,
                        "type" : "SALES",
                        **invsales,
                        "invoice_no" : item['inv_no']['invoice_no']
                    })

                if(inv_return_queryset):
                    invreturn = dict(inv_return_queryset)

                    response_data.append({
                        **item,
                        **invreturn,
                        "type" : "SALES RETURN",
                        "invoice_no" : item['inv_no']['invoice_no']
                    })
            columns = get_reports_columns_template(request.user.pk,SALES_AND_SALES_RETURN_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':FILTERS,
                'groupingColumns': ["type"],
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class PanBillsReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(invoice_status = 1,pan_number__isnull=False)

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                queryset = queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(setting_bill_type = 0)


            paginator, page = pagination.paginate_queryset(queryset, request,None,PANBILLS_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={'invoice_no':True}).data

            response_data = []

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id = instance.erp_invoice_id).annotate( 
                            taxable=Sum('taxable_amount'),
                            tax=Sum('tax_amount'),
                            cgst=Sum('cgst_cost'),
                            sgst=Sum('sgst_cost'),
                            igst=Sum('igst_cost'),
                            cost=Sum('item_cost'),
                            ).values(
                                'invoice_bill_id',
                                'taxable',
                                'tax', 
                                'cgst',
                                'sgst',
                                'igst',
                                'cost',
                            ).get()
                invsales = dict(inv_queryset)


                response_data.append({
                    **item,
                    **invsales,
                    "invoice_no" : item['inv_no']['invoice_no']
                })
            columns = get_reports_columns_template(request.user.pk,PANBILLS_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)



class SalesTargetReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        bill_setting_type_filter = ''
        if  bill_setting_type == 1:
            queryset = queryset.filter(setting_bill_type = 1)
            bill_setting_type_filter = 'and i.setting_bill_type = 1 '
        elif bill_setting_type == 0: 
            bill_setting_type_filter = 'and i.setting_bill_type = 0 '
            queryset = queryset.filter(setting_bill_type = 0)
        query = f"""
        select s.section_name,t.product_id,p.product_name,date_format(t.from_date,'%d-%m-%Y') as from_date,date_format(t.to_date,'%d-%m-%Y') as to_date,t.target_pieces,t.target_weight,
            (select IFNULL(sum(s.pieces),0) as sold_pcs
            from erp_invoice_sales_details s 
            left join erp_invoice i on i.erp_invoice_id = s.invoice_bill_id_id
            where i.invoice_status = 1 {bill_setting_type_filter} and s.id_product_id = t.product_id and date(i.invoice_date) between t.from_date and t.to_date) as sold_pcs,
            
            (select IFNULL(sum(s.gross_wt),0) as gross_wt
            from erp_invoice_sales_details s 
            left join erp_invoice i on i.erp_invoice_id = s.invoice_bill_id_id
            where i.invoice_status = 1 {bill_setting_type_filter}  and s.id_product_id = t.product_id and date(i.invoice_date) between t.from_date and t.to_date) as sold_weight
        
        from counter_wise_target t
        left join erp_product p on p.pro_id = t.product_id
        left join erp_section s on s.id_section = t.section_id
                """
        result = generate_query_result(query)

        paginator, page = pagination.paginate_queryset(result, request,None, SALES_WISE_TARGET_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,SALES_WISE_TARGET_COLUMN_LIST,request.data["path_name"])           
        context={'columns':columns,'actions':ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':False}
        return pagination.paginated_response(result,context)


class CreditTobeReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(is_credit = 1,credit_status = 0,invoice_status = 1)

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)

            if  bill_setting_type == 1:
                queryset = queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(setting_bill_type = 0)


            # if from_date and to_date:
            #     queryset = queryset.filter(invoice_date__range=[from_date, to_date])


            paginator, page = pagination.paginate_queryset(queryset, request,None,CREDIT_PENDING_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={"invoice_no":True}).data

            for inv in data:
                received_amount = 0
                balance_amount =0
                issued_amount = float(inv["due_amount"])
                col = ErpReceiptCreditCollection.objects.filter(invoice_bill_id = inv["erp_invoice_id"] ,receipt__bill_status= 1)
                col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
                for collection in col_data:
                    received_amount += (float(collection['received_amount']) + float(collection['discount_amount']))
                balance_amount = issued_amount - received_amount
                inv.update({
                    'invoice_no': inv['inv_no']['invoice_no'],
                    'invoice_date': format_date(inv['invoice_date']),
                    'issued_amount':issued_amount,
                    'collected_amount':received_amount,
                    'balance_amount':balance_amount,
                })

            
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = False
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':CREDIT_PENDING_REPORT,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class CreditTobeReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            id_branch = ",".join(map(str, id_branch))
            queryset = ErpInvoice.objects.raw(
                F"""Select inv.* FROM erp_invoice inv
                    LEFT JOIN erp_invoice_sales_details sal ON sal.invoice_bill_id_id = inv.erp_invoice_id
                  WHere inv.is_credit = 1 and inv.credit_status = 0 and inv.invoice_status = 1 and sal.is_delivered=0
                  and inv.id_branch_id in ({id_branch})
                  Group By inv.erp_invoice_id"""
            )


            paginator, page = pagination.paginate_queryset(queryset, request,None,CREDIT_PENDING_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={"invoice_no":True}).data

            for inv in data:
                received_amount = 0
                balance_amount =0
                issued_amount = float(inv["due_amount"])
                col = ErpReceiptCreditCollection.objects.filter(invoice_bill_id = inv["erp_invoice_id"] ,receipt__bill_status= 1)
                col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
                for collection in col_data:
                    received_amount += (float(collection['received_amount']) + float(collection['discount_amount']))
                balance_amount = issued_amount - received_amount
                inv.update({
                    'invoice_no': inv['inv_no']['invoice_no'],
                    'invoice_date': format_date(inv['invoice_date']),
                    'issued_amount':issued_amount,
                    'collected_amount':received_amount,
                    'balance_amount':balance_amount,
                })

            columns = get_reports_columns_template(request.user.pk,CREDIT_PENDING_REPORT,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = False
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class JewelNotDeliveredReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpItemDelivered.objects.filter(bill__invoice_status = 1)

            if(id_branch):
                queryset  = queryset.filter(bill__id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(bill__invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                queryset = queryset.filter(bill__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(bill__setting_bill_type = 0)

            queryset = queryset.values('bill')

           # queryset = queryset.select_related('transfer_from', 'transfer_to').order_by('id_stock_transfer')

            paginator, page = pagination.paginate_queryset(queryset, request,None,SALES_REPORT)

            data = ErpItemDeliveredSerializer(page,many=True).data

            print(data)


            response_data=[]

            for item, instance in zip(data, queryset):

                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.bill.erp_invoice_id)

                #inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                 
                inv_data = get_invoice_no(inv_serializer)


                response_data.append({
                    **inv_serializer,
                    'invoice_date': format_date(inv_serializer['invoice_date']),
                    **item,
                    **inv_data,
                    "product_name": instance.product.product_name,
                    "branch_name": instance.bill.id_branch.name,
                    'status': dict([(1, 'Delivered'),(2, 'Not Delivered')]).get(instance.is_delivered, ''),
                    'status_color':dict([(1, 'success'),(2, 'warning')]).get(instance.is_delivered, ''),
                   
                })
            columns = get_reports_columns_template(request.user.pk,SALES_REPORT,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

class CategoryWiseDailyAbstractReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('id_branch')
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        counter = request.data.get('id_counter')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:

            sales_queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1,invoice_bill_id__is_promotional_billing = False).order_by("id_product__id_metal")

            if  bill_setting_type == 1:
                sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if  counter:
                sales_queryset = sales_queryset.filter(invoice_bill_id__id_counter = counter)

            if(id_branch):
                sales_queryset  = sales_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                sales_queryset = sales_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            discount = sales_queryset.aggregate(discount=Sum('discount_amount'))

            discount_amt = 0
 
            if  discount:
                discount_amt = discount['discount']

            sales_queryset= sales_queryset.values('id_product__cat_id').annotate( 
                                     product_name=F('id_product__cat_id__cat_name'),
                                     pcs=Sum('pieces'),
                                     grosswt=Sum('gross_wt'),
                                     netwt=Sum('net_wt'),
                                     diawt=Sum('dia_wt'),
                                     stonewt=Sum('stone_wt'),
                                     lesswt=Sum('less_wt'),
                                     taxable=Sum('taxable_amount'),
                                     tax=Sum('tax_amount'),
                                     igst=Sum('igst_cost'),
                                     sgst=Sum('sgst_cost'),
                                     cgst=Sum('cgst_cost'),
                                     tot_amount=Sum('item_cost'),
                                      )
            
            sales_data = list(sales_queryset)

            pur_queryset = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id__invoice_status = 1).order_by("id_product__id_metal")

            if(id_branch):
                pur_queryset  = pur_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                pur_queryset = pur_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                pur_queryset = pur_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                pur_queryset = pur_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if  counter:
                pur_queryset = pur_queryset.filter(invoice_bill_id__id_counter = counter)

            pur_queryset= pur_queryset.values('id_product__cat_id').annotate( 
                            product_name=F('id_product__cat_id__cat_name'),
                            pcs=Sum('pieces'),
                            grosswt=Sum('gross_wt'),
                            netwt=Sum('net_wt'),
                            diawt=Sum('dia_wt'),
                            stonewt=Sum('stone_wt'),
                            lesswt=Sum('less_wt'),
                            tot_amount=Sum('amount'),
                            )
            
            purchase_data = list(pur_queryset)

            sales_return_queryset = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id__invoice_status = 1).order_by("id_product__id_metal")

            if(id_branch):
                sales_return_queryset  = sales_return_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                sales_return_queryset = sales_return_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                sales_return_queryset = sales_return_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                sales_return_queryset = sales_return_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if  counter:
                sales_return_queryset = sales_return_queryset.filter(invoice_bill_id__id_counter = counter)

            sales_return_queryset= sales_return_queryset.values('id_product__cat_id').annotate( 
                                     product_name=F('id_product__cat_id__cat_name'),
                                     pcs=Sum('pieces'),
                                     grosswt=Sum('gross_wt'),
                                     netwt=Sum('net_wt'),
                                     diawt=Sum('dia_wt'),
                                     stonewt=Sum('stone_wt'),
                                     lesswt=Sum('less_wt'),
                                     taxable=Sum('taxable_amount'),
                                     tax=Sum('tax_amount'),
                                     tot_amount=Sum('item_cost'),
                                      )

            sales_return = list(sales_return_queryset)

            inv_payment_queryset = ErpInvoicePaymentModeDetail.objects.filter(
                invoice_bill_id__invoice_status=1  # Corrected filter syntax
            ).values('payment_mode').annotate(
                total_amount=Sum(
                    Case(
                        When(payment_type=1, then=F('payment_amount')),
                        default=-F('payment_amount'),
                        output_field=DecimalField()  # Specify DecimalField for consistency
                    )
                ),
                amount=Sum(
                    Case(
                        When(payment_type=1, then=Value(0.00)),
                        default=F('payment_amount'),
                        output_field=DecimalField()  # Specify DecimalField for consistency
                    )
                ),
                receipt_amount=Sum(
                    Case(
                        When(payment_type=1, then=F('payment_amount')),
                        default=Value(0.00),
                        output_field=DecimalField()  # Specify DecimalField for consistency
                    )
                ),
                payment_type=F('payment_type'),
                mode_name=F('payment_mode__mode_name'),
                mode=F('payment_mode')
            )

            if(id_branch):
                inv_payment_queryset  = inv_payment_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                inv_payment_queryset = inv_payment_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                inv_payment_queryset = inv_payment_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                inv_payment_queryset = inv_payment_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if  counter:
                inv_payment_queryset = inv_payment_queryset.filter(invoice_bill_id__id_counter = counter)

            inv_payment_data = list(inv_payment_queryset)

            issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt__bill_status = 1).values('payment_mode').annotate(
                total_amount=Sum(
                    Case(
                        When(type=1, then=F('payment_amount')),
                        default=-F('payment_amount'),
                    )
                ),
                amount=Sum(
                    Case(
                        When(type=1, then=Value(0.00)),
                        default=F('payment_amount'),
                        output_field=DecimalField()  # Specify DecimalField for consistency
                    )
                ),
                receipt_amount=Sum(
                    Case(
                        When(type=1, then=F('payment_amount')),
                        default=Value(0.00),
                        output_field=DecimalField()  # Specify DecimalField for consistency
                    )
                ),
                payment_type=F('type'),
                mode_name=F('payment_mode__mode_name'),
                mode=F('payment_mode')
            )

            if(id_branch):
                issue_payment_queryset  = issue_payment_queryset.filter(issue_receipt__branch__in = id_branch)
            if from_date and to_date:
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__bill_date__range=[from_date, to_date])

            if  counter:
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__id_counter = counter)

            if  bill_setting_type == 1:
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 0)

            issue_payment_data = list(issue_payment_queryset)

            payment_details = {}

            total_payment = total_sale_inward = adv_adjusted = chit_adjusted = gift_adjusted = 0

            adj_data = ErpReceiptAdvanceAdj.objects.filter(
                invoice_bill_id__invoice_status=1
            )

            if(id_branch):
                adj_data  = adj_data.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                adj_data = adj_data.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                adj_data = adj_data.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                adj_data = adj_data.filter(invoice_bill_id__setting_bill_type = 0)

            if  counter:
                adj_data = adj_data.filter(invoice_bill_id__id_counter = counter)

            adj_data = adj_data.aggregate(total_adj_amount=Sum('adj_amount'))
            

            if(adj_data['total_adj_amount']):
                adv_adjusted = adj_data['total_adj_amount']

            chit_adj_data = ErpInvoiceSchemeAdjusted.objects.filter(
                invoice_bill_id__invoice_status=1
            )
            print(chit_adj_data,"chit_adjusted")
            if  bill_setting_type == 1:
                chit_adj_data = chit_adj_data.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                chit_adj_data = chit_adj_data.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                chit_adj_data  = chit_adj_data.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                chit_adj_data = chit_adj_data.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            if  counter:
                chit_adj_data = chit_adj_data.filter(invoice_bill_id__id_counter = counter)

            chit_adj_data = chit_adj_data.aggregate(chit_amount=Sum('closing_amount'))
            print(chit_adjusted,"chit_amount")
            if(chit_adj_data['chit_amount']):
                chit_adjusted = chit_adj_data['chit_amount']
                
            gift_adj_data = ErpInvoiceGiftDetails.objects.filter(
                invoice_bill_id__invoice_status=1
            )

            if  bill_setting_type == 1:
                gift_adj_data = gift_adj_data.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                gift_adj_data = gift_adj_data.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                gift_adj_data  = gift_adj_data.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                gift_adj_data = gift_adj_data.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            if  counter:
                gift_adj_data = gift_adj_data.filter(invoice_bill_id__id_counter = counter)
            gift_adj_data = gift_adj_data.aggregate(amount=Sum('amount'))

            if(gift_adj_data['amount']):
                gift_adjusted = gift_adj_data['amount']    
                

            print(adj_data)

            misc_sales_queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1,invoice_bill_id__is_promotional_billing = 1)

            if  bill_setting_type == 1:
                misc_sales_queryset = misc_sales_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                misc_sales_queryset = misc_sales_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                misc_sales_queryset  = misc_sales_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            if from_date and to_date:
                misc_sales_queryset = misc_sales_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
            if  counter:
                misc_sales_queryset = misc_sales_queryset.filter(invoice_bill_id__id_counter = counter)

            misc_sales_queryset= misc_sales_queryset.values('id_product__cat_id').annotate( 
                                     product_name=F('id_product__cat_id__cat_name'),
                                     pcs=Sum('pieces'),
                                     grosswt=Sum('gross_wt'),
                                     netwt=Sum('net_wt'),
                                     diawt=Sum('dia_wt'),
                                     stonewt=Sum('stone_wt'),
                                     lesswt=Sum('less_wt'),
                                     taxable=Sum('taxable_amount'),
                                     tax=Sum('tax_amount'),
                                     igst=Sum('igst_cost'),
                                     sgst=Sum('sgst_cost'),
                                     cgst=Sum('cgst_cost'),
                                     tot_amount=Sum('item_cost'),
                                      )
            
            misc_sales_data = list(misc_sales_queryset)


            canceled_bills_queryset = ErpInvoice.objects.filter(invoice_status = 2)

            if  bill_setting_type == 1:
                canceled_bills_queryset = canceled_bills_queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                canceled_bills_queryset = canceled_bills_queryset.filter(setting_bill_type = 0)

            if(id_branch):
                canceled_bills_queryset  = canceled_bills_queryset.filter(id_branch__in = id_branch)
            if from_date and to_date:
                canceled_bills_queryset = canceled_bills_queryset.filter(invoice_date__range=[from_date, to_date])
            if  counter:
                canceled_bills_queryset = canceled_bills_queryset.filter(id_counter = counter)

            # canceled_bills_queryset= canceled_bills_queryset.values('id_product__cat_id').annotate( 
            #                          product_name=F('id_product__cat_id__cat_name'),
            #                          pcs=Sum('pieces'),
            #                          grosswt=Sum('gross_wt'),
            #                          netwt=Sum('net_wt'),
            #                          diawt=Sum('dia_wt'),
            #                          stonewt=Sum('stone_wt'),
            #                          lesswt=Sum('less_wt'),
            #                          taxable=Sum('taxable_amount'),
            #                          tax=Sum('tax_amount'),
            #                          igst=Sum('igst_cost'),
            #                          sgst=Sum('sgst_cost'),
            #                          cgst=Sum('cgst_cost'),
            #                          tot_amount=Sum('item_cost'),
            #                           )
            
            canceled_bills_queryset = ErpInvoiceSerializer(canceled_bills_queryset,many=True,context={'invoice_no':True}).data  

            for payment in inv_payment_data:
                if payment['mode'] not in payment_details:
                    print(payment['mode'])
                    payment_details[payment['mode']] = {
                        'payment_amount': 0,
                        'amount': 0,
                        'receipt_amount': 0,
                    }
                payment_details[payment['mode']] = {
                    **payment,
                    "payment_amount" : float(payment['total_amount']) + float(payment_details[payment['mode']]['payment_amount']),
                    "amount" : float(payment['amount']) + float(payment_details[payment['mode']]['amount']),
                    "receipt_amount" : float(payment['receipt_amount']) + float(payment_details[payment['mode']]['receipt_amount']),

                }
                total_payment += float(payment['total_amount'])

            for payment in issue_payment_data:
                if payment['mode'] not in payment_details:
                    payment_details[payment['mode']] = {
                        'payment_amount': 0,
                        'amount': 0,
                        'receipt_amount': 0,
                    }
                payment_details[payment['mode']] = {
                    **payment,
                    "payment_amount" : float(payment['total_amount']) + float(payment_details[payment['mode']]['payment_amount']),
                    "amount" : float(payment['amount']) + float(payment_details[payment['mode']]['amount']),
                    "receipt_amount" : float(payment['receipt_amount']) + float(payment_details[payment['mode']]['receipt_amount']),
                }
                total_payment += float(payment['total_amount'])

            payment_details = [
                {**details} 
                for mode, details in payment_details.items()
            ]

            total_payment += float(adv_adjusted)

            total_payment += float(chit_adjusted)

            total_payment += float(gift_adjusted)


            sales_taxable_amt = 0

            sales_tax_amt = 0

            purchase_amt = 0

            sales_return_tax_amt = 0

            sales_return_taxable_amt = 0

            sales_amt = 0

            sales_return_amt = 0

            for sales in sales_data:
                sales_amt +=float(sales['tot_amount'])
                sales_taxable_amt += float(sales['taxable'])
                sales_tax_amt += float(sales['tax'])
                sales['tot_amount'] = round(sales['tot_amount'])

            for purchase in purchase_data:
                purchase_amt += float(purchase['tot_amount'])

            for return_ in sales_return:
                sales_return_amt += float(return_['tot_amount'])


            receipt_queryset = ErpIssueReceipt.objects.filter(bill_status = 1)

            if  bill_setting_type == 1:
                receipt_queryset = receipt_queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                receipt_queryset = receipt_queryset.filter(setting_bill_type = 0)

            if(id_branch):
                receipt_queryset  = receipt_queryset.filter(branch__in = id_branch)
            if from_date and to_date:
                receipt_queryset = receipt_queryset.filter(bill_date__range=[from_date, to_date])

            if  counter:
                receipt_queryset = receipt_queryset.filter(id_counter = counter)

            receipt_data = ErpIssueReceiptSerializer(receipt_queryset,many=True).data

            adv_receipt = adv_deposit = adv_refund = credit_receipt = credit_issue = other_expence =  0

            for receipt in receipt_data:
                if ((receipt['receipt_type'] == 1 or receipt['receipt_type'] == 2) and receipt['type'] == 2):
                    adv_receipt += float(receipt['amount'])
                elif (receipt['receipt_type'] == 3  and receipt['type'] == 2 ):
                    adv_deposit += float(receipt['amount'])
                elif (receipt['receipt_type'] == 5  and receipt['type'] == 2 ):
                    credit_receipt += float(receipt['amount'])
                elif (receipt['issue_type'] == 2  and receipt['type'] == 1):
                    adv_refund += float(receipt['amount'])
                elif (receipt['issue_type'] == 3  and receipt['type'] == 1):
                    other_expence += float(receipt['amount'])
                elif (receipt['issue_type'] == 1  and receipt['type'] == 1):
                    credit_issue += float(receipt['amount'])

            # inv_queryset = ErpInvoice.objects.filter(invoice_status = 1,is_credit = 1)

            # if(id_branch):
            #     inv_queryset  = inv_queryset.filter(id_branch__in = id_branch)
            # if from_date and to_date:
            #     inv_queryset = inv_queryset.filter(invoice_date__range=[from_date, to_date])
            # inv_queryset = inv_queryset.aggregate(
            #     total_balance=Sum('due_amount')
            # )

            round_off_queryset = ErpInvoice.objects.filter(invoice_status = 1)

            if  bill_setting_type == 1:
                round_off_queryset = round_off_queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                round_off_queryset = round_off_queryset.filter(setting_bill_type = 0)

            if(id_branch):
                round_off_queryset  = round_off_queryset.filter(id_branch__in = id_branch)
            if from_date and to_date:
                round_off_queryset = round_off_queryset.filter(invoice_date__range=[from_date, to_date])
            if  counter:
                round_off_queryset = round_off_queryset.filter(id_counter = counter)
            round_off_queryset = round_off_queryset.aggregate(
                total_balance=Sum('round_off'),
                discount=Sum('total_discount_amount')
            )

            round_off = round_off_queryset['total_balance'] if round_off_queryset['total_balance'] is not None else 0

            discount = round_off_queryset['discount'] if round_off_queryset['discount'] is not None else 0

            # invoice_credit = inv_queryset['total_balance'] if inv_queryset['total_balance'] is not None else 0

           # credit_issue += float(invoice_credit)

            total_sale_inward = float(sales_amt)  -float(sales_return_amt) +float(adv_receipt) + float(adv_deposit) - float(adv_refund) + float(credit_receipt) - float(credit_issue) - float(other_expence)  - float(purchase_amt) - float(round_off)

            receipt = float(sales_amt) +float(adv_receipt) + float(adv_deposit) + float(credit_receipt) + float(round_off)

            payment = float(adv_refund) + float(credit_issue) + float(other_expence)  + float(purchase_amt)  + float(sales_return_amt)

            sales_summary = []
            
            if adv_receipt:
                sales_summary.append(
                    { 'lable' : 'ADVANCE RECEIPT','value': adv_receipt, 'sign' : '(+)','type':1},
                )
            
            if adv_deposit:
                sales_summary.append(
                    { 'lable' : 'ADVANCE DEPOSIT','value': adv_deposit, 'sign' : '(+)','type':1},
                )

            if adv_refund:
                sales_summary.append(
                    { 'lable' : 'ADVANCE REFUND','value': adv_refund, 'sign' : '(-)','type':2},
                )

            if credit_receipt:
                sales_summary.append(
                     { 'lable' : 'CREDIT RECEIPT','value': credit_receipt, 'sign' : '(+)','type':1},
                )

            if credit_issue:
                sales_summary.append(
                    { 'lable' : 'CREDIT SALES','value': credit_issue, 'sign' : '(-)','type':2},
                )
            
            if other_expence:
                sales_summary.append(
                    { 'lable' : 'OTHER EXPENCE','value': other_expence, 'sign' : '(-)','type':2},
                )

            if round_off:
                sales_summary.append(
                   { 'lable' : 'ROUND OFF','value': round_off, 'sign' : '(+)','type':1}
                )

            payment_summary = []
 
            for pay in payment_details:
                payment_summary.append({ 'lable' : pay['mode_name'],'value':  pay['payment_amount'], 'sign' : '(+)','receipt_amount':  pay['receipt_amount'],'payment_amount':  pay['amount'],})

            if adv_adjusted:
                payment_summary.append({ 'lable' : 'ADV ADJUSTED','value':  adv_adjusted, 'sign' : '(+)', 'receipt_amount': adv_adjusted,'payment_amount': 0,})

            if chit_adjusted:
                payment_summary.append({ 'lable' : 'CHIT ADJUSTED','value':  chit_adjusted, 'sign' : '(+)','receipt_amount':  chit_adjusted,'payment_amount':  0,})
            
            if gift_adjusted:
                payment_summary.append({ 'lable' : 'GIFT ADJUSTED','value':  gift_adjusted, 'sign' : '(+)'})
            
            difference = float(total_sale_inward) - float(total_payment)

            response_data={
                'sales_data' :sales_data,
                'purchase_data' :purchase_data,
                'sales_return' :sales_return,
                'sales_summary' : sales_summary,
                'payment_summary' : payment_summary,
                'total_payment' :total_payment,
                'total_sale_inward' :round(total_sale_inward),
                'round_off':round_off,
                'discount':discount,  
                'payment':round(payment),  
                'receipt':round(receipt),   
                'discount_amt':discount_amt,
                'misc_sales': misc_sales_data,  
                'difference': difference, 
                'canceled_bills': canceled_bills_queryset,           

            }
                            
            return Response(response_data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        


class MetalProcessReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        columns = ''
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        type = int(request.data.get('type',0))
        process = int(request.data.get('process',0))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpMetalProcess.objects.values('id_metal_process').filter(type = type,process_id = process)

            if(process == 1 and type == 1):
                queryset = queryset.annotate(
                    ref_no=F('ref_no'),
                    entry_date=F('entry_date'),
                    branch_name=F('id_branch__name'),
                    metal_name=F('process_ref_id__id_metal__metal_name'),
                    total_pcs=Sum('process_ref_id__melting_pieces'),
                    total_gross_wt=Sum('process_ref_id__gross_wt'),
                    total_less_wt=Sum('process_ref_id__less_wt'),
                    total_net_wt=Sum('process_ref_id__net_wt'),
                    total_dia_wt=Sum('process_ref_id__dia_wt'),
                    total_stone_wt=Sum('process_ref_id__stone_wt')
                )
                columns = MELTING_ISSUE_COLUMN_LIST

            elif (process == 1 and type == 2):
                queryset = queryset.annotate(
                    ref_no=F('ref_no'),
                    entry_date=F('entry_date'),
                    branch_name=F('id_branch__name'),
                    product_name=F('melting_receipt_process_ref_id__id_product__product_name'),
                    total_pcs=Sum('melting_receipt_process_ref_id__pieces'),
                    total_gross_wt=Sum('melting_receipt_process_ref_id__weight'),
                    issue_weight=Sum('melting_receipt_process_ref_id__melting_issue_ref_no__process_ref_id__gross_wt'),
                    total_charges=Sum('melting_receipt_process_ref_id__charges'),
                )
                columns = MELTING_RECIPTS_COLUMN_LIST
            elif (process == 2 and type == 1):
                queryset = queryset.annotate(
                    ref_no=F('ref_no'),
                    entry_date=F('entry_date'),
                    branch_name=F('id_branch__name'),
                    product_name=F('testing_issue_process_ref_idid_product__product_name'),
                    total_pcs=Sum('testing_issue_process_ref_id__pieces'),
                    total_tested_weight=Sum('testing_issue_process_ref_id__issue_weight'),
                )
                columns = TESTING_ISSUE_COLUMN_LIST

            elif (process == 2 and type == 2):
                queryset = queryset.annotate(
                    ref_no=F('ref_no'),
                    entry_date=F('entry_date'),
                    branch_name=F('id_branch__name'),
                    product_name=F('testing_receipt_process_ref_id__id_product__product_name'),
                    total_pcs=Sum('testing_receipt_process_ref_id__pieces'),
                    total_issue_weight=Sum('testing_receipt_process_ref_id__issue_weight'),
                    total_received_weight=Sum('testing_receipt_process_ref_id__received_weight'),
                    total_charges=Sum('testing_receipt_process_ref_id__charges'),
                )
                columns = TESTING_RECIPTS_COLUMN_LIST

            elif (process == 3 and type == 1):
                queryset = queryset.annotate(
                    ref_no=F('ref_no'),
                    entry_date=F('entry_date'),
                    branch_name=F('id_branch__name'),
                    product_name=F('refining_issue_process_ref_id__refining_issue_ref_id__id_melting_receipt__id_product__product_name'),
                    total_pcs=Sum('refining_issue_process_ref_id__refining_issue_ref_id__pieces'),
                    total_issue_weight=Sum('refining_issue_process_ref_id__refining_issue_ref_id__issue_weight'),
                )
                columns = REFINING_ISSUE_COLUMN_LIST

            elif (process == 3 and type == 2):
                queryset = queryset.annotate(
                    ref_no=F('ref_no'),
                    entry_date=F('entry_date'),
                    branch_name=F('id_branch__name'),
                    product_name=F('refining_receipt_process_ref_id__refining_receipt_ref_id__id_product__product_name'),
                    total_pcs=Sum('refining_receipt_process_ref_id__refining_receipt_ref_id__pieces'),
                    total_received_weight=Sum('refining_receipt_process_ref_id__refining_receipt_ref_id__weight'),
                    total_charges=Sum('refining_receipt_process_ref_id__charges'),
                    total_issue_weight=Sum('refining_receipt_process_ref_id__refining_issue_ref_id__issue_weight'),

                )
                columns = REFINING_RECIPTS_COLUMN_LIST

            if(id_branch):
                queryset  = queryset.filter(id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(entry_date__range=[from_date, to_date])

            paginator, page = pagination.paginate_queryset(queryset, request,None,columns)

            response_data = list(page)
            # print(response_data)
            columnss = get_reports_columns_template(request.user.pk,columns,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isIssueReciptFilterReq'] = True
            filters_copy['isProcessFilterReq'] = True
            context={
                'columns':columnss,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class PurchaseStockInAndOutAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate',None)
        section = request.data.get('section',None)
        product = request.data.get('product',None)
        metal = request.data.get('metal',None)
        stock_type = int(request.data.get('stock_type',0))

        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            id_branch = ",".join(map(str, id_branch))
            print(id_branch)
            result = []
            if(stock_type == 1):
                result = call_stored_procedure('SalesReturnStockInandOut',id_branch,from_date,to_date,metal,product,section)
            elif(stock_type == 2):
                result = call_stored_procedure('PartlySaleStockInandOut',id_branch,from_date,to_date,metal,product,section)
            elif(stock_type == 3):
                result = call_stored_procedure('OldMetalStockInandOut',id_branch,from_date,to_date,metal,product,section)

            #result = call_stored_procedure('OldMetalStockInandOut','1,2,3',"2024-11-18","2024-11-18",metal,product,section)
            result['report_data'] = format_data_with_decimal(result['report_data'],OTHER_STOCK_IN_AND_OUT_REPORT_LIST)
            paginator, page = pagination.paginate_queryset(result['report_data'], request,None,OTHER_STOCK_IN_AND_OUT_REPORT_LIST)
            columns = get_reports_columns_template(request.user.pk,OTHER_STOCK_IN_AND_OUT_REPORT_LIST,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isStockTypeFilterReq'] = True
            context={'columns':columns, 'filters':filters_copy,'actions':ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':True,'groupingColumns': ["type"]}

            return pagination.paginated_response(result['report_data'],context)        
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}","tb":tb}, status=status.HTTP_400_BAD_REQUEST)


class CashBookReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        report_type = int(request.data.get('reportType'))
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        return_data = []
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:

            # Invoice Sales Details
            sales_data = self.get_sales_details(from_date,to_date,id_branch,report_type,bill_setting_type)
            if(sales_data):
                for sales in sales_data:
                    if report_type == 2 :
                        bill_no=get_bill_no(sales['invoice_bill'])
                        return_data.append(
                            {
                                "trans_name": f"{bill_no} SALES CASH { 'RECEIVED FROM' if sales['type'] == 1 else 'ISSUED TO' } {sales['customer_name']}-{sales['customer_mobile']} ",
                                "date":sales['invoice_date'],
                                "credit":sales['issue'],
                                "debit":sales['receipt'],
                                "remarks": '',
                                "type_name":"Trans Type",
                                "type":sales['type'],
                            }
                        )
                    elif report_type == 1:
                        return_data.append(
                            {
                                "trans_name": f"SALES CASH { 'RECEIVED' if sales['type'] == 1 else 'ISSUED' }",
                                "date":sales['invoice_date'],
                                "credit":sales['issue'],
                                "debit":sales['receipt'],
                                "remarks": '',
                                "type_name":"Trans Type",
                                "type":sales['type'],
                            }
                        )



            # Chit Payment Details
            chit_payments = self.get_chit_payment_details(from_date,to_date,id_branch,report_type,bill_setting_type)
            for pay in chit_payments:
                template = f"{pay['receipt_no']} CHIT CASH RECEIVED FROM {pay['customer_name']}-{pay['customer_mobile']}" if report_type == 2 else "CHIT CASH RECEIVED"
                return_data.append(
                        {
                            "trans_name": f"{template} ",
                            "date":pay['invoice_date'],
                            "credit": 0,
                            "debit":pay['amount'],
                            "remarks": '',
                            "type_name":"Chit Cash",
                            "type": 2,
                        })
             # Chit Payment Details
            
            # Issue and Receipt Payment Details
            issue_payment_data = self.issue_receipt_details(from_date,to_date,id_branch,report_type,bill_setting_type)
            
            for payment in issue_payment_data:

                if report_type == 1:
                    trans_name = self.get_issue_trans_name({**payment,'issue_type':payment.get('issue_type',''),'receipt_type':payment.get('receipt_type','')},report_type)
                    return_data.append(
                        {
                            "trans_name":trans_name,
                            "date":payment['invoice_date'],
                            "credit":payment['issue'],
                            "debit":payment['receipt'],
                            "remarks": '',
                            "type_name":"Issue Recipt",
                            "type":payment['payment_type'],
                        }
                    )
                else :
                    trans_name = self.get_issue_trans_name(payment,report_type)
                    return_data.append(
                        {
                            "trans_name":trans_name,
                            "date":payment['invoice_date'],
                            "credit":payment['issue'],
                            "debit":payment['receipt'],
                            "remarks": payment['remarks'],
                            "type_name":"Issue Recipt",
                            "type":payment['payment_type'],
                        }
                    )

            
            branch_deposit_queryset = BankDeposit.objects.filter(entry_date__range=[from_date, to_date])
            
            if(id_branch):

                branch_deposit_queryset  = branch_deposit_queryset.filter(branch__in = id_branch)
            

            if report_type == 2:
                branch_deposit = BankDepositSerializer(branch_deposit_queryset,many=True).data
            else:
                branch_deposit_queryset = branch_deposit_queryset.values('entry_date')
                branch_deposit_queryset = branch_deposit_queryset.annotate(
                    payment_amount=Sum(F('amount')),
                    entry_dates=F('entry_date'),
                )
                branch_deposit = list(branch_deposit_queryset)

            for deposit,instance in  zip(branch_deposit, branch_deposit_queryset):
                if report_type == 2:
                    return_data.append(
                        {
                            "trans_name": f"CASH DEPOSITED TO {deposit['bank_name']} - {deposit['acc_number']}",
                            "date":instance.entry_date,
                            "credit":deposit['amount'],
                            "debit": 0,
                            "remarks": '',
                            "type_name":"Bank Deposit",
                            "type": 1,
                        }
                    )
                else:
                    return_data.append(
                        {
                            "trans_name": "CASH DEPOSIT",
                            "date":deposit['entry_dates'],
                            "credit":deposit['payment_amount'],
                            "debit": 0,
                            "remarks": '',
                            "type_name":"Bank Deposit",
                            "type": 1,
                        }
                    )
                    

            supplier_payment_queryset = ErpSupplierPaymentModeDetail.objects.filter(payment_mode = 1,purchase_payment__entry_date__range=[from_date, to_date])

            if(id_branch):
                supplier_payment_queryset  = supplier_payment_queryset.filter(purchase_payment__cash_from_branch__in = id_branch)

            if report_type == 2:
                supplier_payment = ErpSupplierPaymentModeDetailSerializer(supplier_payment_queryset,many=True).data
            else:
                supplier_payment_queryset = supplier_payment_queryset.values('purchase_payment__entry_date')
                supplier_payment_queryset = supplier_payment_queryset.annotate(
                    payment_amount=Sum(F('payment_amount')),
                    entry_date=F('purchase_payment__entry_date'),
                )
                supplier_payment = list(supplier_payment_queryset)


            for payment,instance in  zip(supplier_payment, supplier_payment_queryset):
                if report_type == 2:
                    return_data.append(
                        {
                            "trans_name": f"{instance.purchase_payment.ref_no} PAYMENT ISSUED TO SUPPLIER {instance.purchase_payment.id_supplier.supplier_name} ",
                            "date":instance.purchase_payment.entry_date,
                            "credit":payment['payment_amount'],
                            "debit": 0,
                            "remarks": '',
                            "type_name":"Supplier Payment",
                            "type": 1,
                        }
                    )
                else:
                    print(payment)
                    return_data.append(
                        {
                            "trans_name": "SUPPLIER PAYMENT CASH",
                            "date":payment['entry_date'],
                            "credit":payment['payment_amount'],
                            "debit": 0,
                            "remarks": '',
                            "type_name":"Supplier Payment",
                            "type": 1,
                        }
                    )
            

            return_grouped_data = self.get_grouped_data(return_data)

            response_data = []
            for index, data in return_grouped_data.items():
                # index_datetime = datetime.combine(index, datetime.min.time())
                date = index.strftime("%Y-%m-%d")
                opening = get_openning_cash(date,id_branch,bill_setting_type)
                response_data.append({
                    "entry_date" : format_date(index),
                    "opening" : opening,
                    "details": data
                })
            
            response_data = sorted(
                response_data,
                key=lambda x: datetime.strptime(x['entry_date'], "%d-%m-%Y")
            )
            if len(response_data) == 0:
                opening = get_openning_cash(to_date,id_branch,bill_setting_type)
                response_data.append({
                    "entry_date" : format_date(to_date),
                    "opening" : opening,
                    "details": []
                })

            return Response(response_data, status=status.HTTP_200_OK)                   
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def get_sales_details(self,from_date,to_date,id_branch,report_type,setting_bill_type):

        sales_queryset = ErpInvoicePaymentModeDetail.objects.filter(payment_mode = 1,invoice_bill_id__invoice_status = 1,invoice_bill_id__setting_bill_type = setting_bill_type,invoice_bill_id__invoice_date__range=[from_date, to_date])

        if  setting_bill_type == 1:
            sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 1)
        elif setting_bill_type == 0: 
            sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 0)

        if(id_branch):
            sales_queryset  = sales_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
        
        if report_type == 2 :
                sales_queryset= sales_queryset.values("invoice_bill_id").annotate( 
                    issue=Sum(
                        Case(
                            When(payment_type=1, then=Value(0.00)),
                            default=F('payment_amount'),
                            output_field=DecimalField()  
                        )
                    ),
                    receipt=Sum(
                        Case(
                            When(payment_type=1, then=F('payment_amount')),
                            default=Value(0.00),
                            output_field=DecimalField() 
                        )
                    ),
                    invoice_date = F('invoice_bill_id__invoice_date'),
                    customer_name = F('invoice_bill_id__customer_name'),
                    customer_mobile = F('invoice_bill_id__customer_mobile'),
                    invoice_bill = F('invoice_bill_id'),
                    type=F('payment_type'),
                )
        elif report_type == 1:
                sales_queryset= sales_queryset.values("invoice_bill_id__invoice_date","payment_type").annotate( 
                    issue=Sum(
                        Case(
                            When(payment_type=1, then=Value(0.00)),
                            default=F('payment_amount'),
                            output_field=DecimalField()  
                        )
                    ),
                    receipt=Sum(
                        Case(
                            When(payment_type=1, then=F('payment_amount')),
                            default=Value(0.00),
                            output_field=DecimalField() 
                        )
                    ),
                    type=F('payment_type'),
                    invoice_date = F('invoice_bill_id__invoice_date'),
                )
        sales_data = list(sales_queryset)
        return sales_data
    
    def get_chit_payment_details(self,from_date,to_date,id_branch,report_type,setting_bill_type):
        payments = PaymentModeDetail.objects.filter(id_pay__payment_status=1, id_pay__date_payment__range=[from_date, to_date],payment_mode = 1)

        if(id_branch):
            payments  = payments.filter(id_pay__id_branch__in = id_branch)
        
        if report_type == 2 :
            payments  = payments.values("id_pay").annotate(
                amount=Sum(F('payment_amount')),
                invoice_date = F('id_pay__date_payment'),
                customer_name = F('id_pay__id_scheme_account__id_customer__firstname'),
                customer_mobile = F('id_pay__id_scheme_account__id_customer__mobile'),
                receipt_no = F('id_pay__receipt_no'),
            )
        elif report_type == 1:
            payments  = payments.values("id_pay__date_payment").annotate(
                amount=Sum(F('payment_amount')),
                invoice_date = F('id_pay__date_payment'),
            )
        return payments
    
    def issue_receipt_details(self,from_date,to_date,id_branch,report_type,setting_bill_type):
        if report_type == 2 :
                issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(
                    issue_receipt__setting_bill_type = setting_bill_type,
                    issue_receipt__bill_status = 1,
                    issue_receipt__bill_date__range=[from_date, to_date],
                    payment_mode= 1).exclude(issue_receipt__receipt_type=7).values(
                        'issue_receipt__id'
                    ).annotate(
                    issue=Sum(
                        Case(
                            When(type=1, then=Value(0.00)),
                            default=F('payment_amount'),
                            output_field=DecimalField()  
                        )
                    ),
                    receipt=Sum(
                        Case(
                            When(type=1, then=F('payment_amount')),
                            default=Value(0.00),
                            output_field=DecimalField() 
                        )
                    ),
                    invoice_date = F('issue_receipt__bill_date'),
                    remarks=F('issue_receipt__remarks'),
                    receipt_type=F('issue_receipt__receipt_type'),
                    issue_type=F('issue_receipt__issue_type'),
                    issue_to=F('issue_receipt__issue_to'),
                    account_head=F('issue_receipt__account_head__name'),
                    payment_type=F('type'),
                    customer =F('issue_receipt__customer__firstname'),
                    cus_mobile =F('issue_receipt__customer__mobile'),
                    employee =F('issue_receipt__employee__firstname'),
                    emp_code =F('issue_receipt__employee__emp_code'),
                    bill_no =F('issue_receipt__bill_no')
                )
        elif report_type == 1:
                issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt__setting_bill_type = setting_bill_type,issue_receipt__bill_status = 1,issue_receipt__bill_date__range=[from_date, to_date],payment_mode= 1,issue_receipt__issue_type__in =[1,2,3,5]).values('issue_receipt__bill_date','issue_receipt__issue_type').annotate(
                    issue=Sum(
                        Case(
                            When(type=1, then=Value(0.00)),
                            default=F('payment_amount'),
                            output_field=DecimalField()  
                        )
                    ),
                    receipt=Sum(
                        Case(
                            When(type=1, then=F('payment_amount')),
                            default=Value(0.00),
                            output_field=DecimalField() 
                        )
                    ),
                    invoice_date = F('issue_receipt__bill_date'),
                    issue_type=F('issue_receipt__issue_type'),
                    payment_type=F('type'),
                )
                receipt_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt__setting_bill_type = setting_bill_type,issue_receipt__bill_status = 1,issue_receipt__bill_date__range=[from_date, to_date],payment_mode= 1,issue_receipt__receipt_type__in =[1,2,3,4,5,6]).values('issue_receipt__bill_date','issue_receipt__receipt_type').annotate(
                    issue=Sum(
                        Case(
                            When(type=1, then=Value(0.00)),
                            default=F('payment_amount'),
                            output_field=DecimalField()  
                        )
                    ),
                    receipt=Sum(
                        Case(
                            When(type=1, then=F('payment_amount')),
                            default=Value(0.00),
                            output_field=DecimalField() 
                        )
                    ),
                    invoice_date = F('issue_receipt__bill_date'),
                    receipt_type=F('issue_receipt__receipt_type'),
                    payment_type=F('type'),

                )

        if  setting_bill_type == 1:
            issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 1)
            if report_type == 1:
                    receipt_payment_queryset  = receipt_payment_queryset.filter(issue_receipt__setting_bill_type = 1)
        elif setting_bill_type == 0: 
            issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 0)
            if report_type == 1:
                    receipt_payment_queryset  = receipt_payment_queryset.filter(issue_receipt__setting_bill_type = 1)
        
        if(id_branch):
                issue_payment_queryset  = issue_payment_queryset.filter(issue_receipt__branch__in = id_branch)
                if report_type == 1:
                    receipt_payment_queryset  = receipt_payment_queryset.filter(issue_receipt__branch__in = id_branch)

        issue_payment_data = list(issue_payment_queryset)
        if report_type == 1:
            issue_payment_data += list(receipt_payment_queryset)

        return issue_payment_data



    
    def get_issue_trans_name(self,receipt,report_type):

        trans_name = ""

        if (receipt['receipt_type'] == 1):
            trans_name = "GENRAL ADVANCE CASH"
        elif (receipt['receipt_type'] == 2):
            trans_name = "ORDER ADVANCE CASH"
        elif (receipt['receipt_type'] == 3):
            trans_name = "ADVANCE DEPOSIT CASH"
        elif (receipt['receipt_type'] == 4):
            trans_name = "IMPORTED CASH"
        elif (receipt['receipt_type'] == 5):
            trans_name = "CREDIT COLLECTION CASH"
        elif (receipt['receipt_type'] == 6):
            trans_name = "REPAIR ORDER DELIVERY CASH"
        elif (receipt['issue_type'] == 1):
            trans_name = "CREDIT CASH"
        elif (receipt['issue_type'] == 2):
            trans_name = "REFUND CASH"
        elif (receipt['issue_type'] == 3):
            trans_name =  "PETTY CASH"
        

        if report_type == 2:
            temp_name  = ''
            temp_no =''
            if(receipt['issue_to'] == 2):
                temp_no = receipt['emp_code']
                temp_name = receipt['employee']
            else:
                temp_no = receipt['cus_mobile']
                temp_name = receipt['customer']
            trans_name = (
                f"{receipt['bill_no']} {trans_name} "
                f"{'RECEIVED FROM' if receipt['payment_type'] == 1 else 'ISSUED TO'} "
                f"{'EMPLOYEE' if receipt['issue_to'] == 2 else 'CUSTOMER'} "
                f"{temp_name}-{temp_no} "
                f"{'REMARKS: ' + receipt['remarks'] if receipt.get('remarks') else ''}"
            )

        return  trans_name


    def get_grouped_data(self,data):
        response_data1={}

        for payment in data:
            response_data1.setdefault(payment['date'], []).append(payment)

        return response_data1

def get_openning_cash(date,id_branch,setting_bill_type=1):

    opening_type = RetailSettings.objects.get(name='cash_opening_type').value
    opening_amount = 0

    if int(opening_type) == 1:
        branch_opening = ErpIssueReceipt.objects.filter()
        sales_queryset = ErpInvoicePaymentModeDetail.objects.filter(payment_mode = 1,invoice_bill_id__invoice_status = 1,invoice_bill_id__invoice_date__lt=date)

        issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt__bill_status = 1,issue_receipt__bill_date__lt=date,payment_mode= 1)
        if  setting_bill_type == 1:
            issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 1)
            sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 1)

        elif setting_bill_type == 0: 
            issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 0)
            sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 0)

        if(id_branch):
            issue_payment_queryset  = issue_payment_queryset.filter(issue_receipt__branch__in = id_branch)
            sales_queryset  = sales_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            branch_opening = branch_opening.filter(branch__in = id_branch)

        issue_payment_queryset = issue_payment_queryset.aggregate(
                amount=Sum(
                    Case(
                        When(type=1, then=F('payment_amount')),
                        default=-F('payment_amount'),
                        output_field=DecimalField()  
                    )
                ),
            )
        sales_queryset = sales_queryset.aggregate(
                amount=Sum(
                    Case(
                        When(payment_type=1, then=F('payment_amount')),
                        default=-F('payment_amount'),
                        output_field=DecimalField()  
                    )
                ),
            )
        
        branch_opening = branch_opening.aggregate(branch_opening=Sum('amount'))

        chit_payments = PaymentModeDetail.objects.filter(id_pay__payment_status=1, id_pay__date_payment__lt=date,payment_mode = 1)

        if(id_branch):
            chit_payments  = chit_payments.filter(id_pay__id_branch__in = id_branch)

        chit_payments  = chit_payments.aggregate(
            amount=Sum(F('payment_amount')),
        )
        branch_deposit_queryset = BankDeposit.objects.filter(entry_date__lt=date)
        
        if(id_branch):

            branch_deposit_queryset  = branch_deposit_queryset.filter(branch__in = id_branch)
        
        branch_deposit_queryset  = branch_deposit_queryset.aggregate(
            deposit_amount=Sum(F('amount')),
        )

        supplier_payment = ErpSupplierPaymentModeDetail.objects.filter(payment_mode = 1,purchase_payment__entry_date__lt=date)
        
        if(id_branch):

            supplier_payment  = supplier_payment.filter(purchase_payment__cash_from_branch__in = id_branch)
        
        supplier_payment  = supplier_payment.aggregate(
            amount=Sum(F('payment_amount')),
        )


        if(chit_payments['amount']):
            opening_amount += chit_payments['amount']

        if(issue_payment_queryset['amount']):
            opening_amount += issue_payment_queryset['amount']

        if(sales_queryset['amount']):
            opening_amount += sales_queryset['amount']
        if(branch_opening['branch_opening']):
            opening_amount += branch_opening['branch_opening']

        if(branch_deposit_queryset['deposit_amount']):
            opening_amount -= branch_deposit_queryset['deposit_amount']

        if(supplier_payment['amount']):
            opening_amount -= supplier_payment['amount']

    else:
        if(ErpIssueReceipt.objects.filter(receipt_type=7,bill_date = date,setting_bill_type = setting_bill_type)).exists():
            branch_opening = ErpIssueReceipt.objects.filter(receipt_type=7,bill_date = date,setting_bill_type = setting_bill_type)
            if(id_branch):
                branch_opening = branch_opening.filter(branch__in = id_branch)
            branch_opening = branch_opening.aggregate(branch_opening=Sum('amount'))

            if(branch_opening['branch_opening']):
                opening_amount += branch_opening['branch_opening']

    return opening_amount

class SupplierLegerReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_supplier = request.data.get('id_supplier',None)
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_metal = request.data.get('id_metal',None)
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        return_data = []
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_supplier or not id_metal:
            return Response({"message": "Metal and Supplier is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            filter_bill_type = ''
            rc_filter_bill_type = ''
            mi_filter_bill_type = ''
            pay_filter_bill_type = ''
            if bill_setting_type == 1 or bill_setting_type == 0:
                filter_bill_type = f' AND ent.setting_bill_type = {bill_setting_type} '
                rc_filter_bill_type = f' AND rc.setting_bill_type = {bill_setting_type} '
                mi_filter_bill_type = f' AND iss.setting_bill_type = {bill_setting_type} '
                pay_filter_bill_type = f' AND pay.setting_bill_type = {bill_setting_type} '



            is_qc_required = RetailSettings.objects.get(name='is_qc_required').value
            if(int(is_qc_required)==1):
                query1 = f"""
                            SELECT  "Purchase Entry" as name,
                                    UNIX_TIMESTAMP(iss.created_on) AS code,
                                    iss.issue_no as ref_no,
                                    DATE_FORMAT(issue_date, '%d-%m-%Y') as entry_date,
                                    issue_date as date,
                                    0 as amount_balance,
                                    1 as type,
                                    COALESCE(SUM(rec.recd_pure_wt), 0) AS credit_wt,
                                    0 AS credit_amt,
                                    0 AS debit_wt,
                                    0 AS debit_amt
                                FROM
                                    erp_purchase_item_issue_receipt_details rec
                                LEFT JOIN erp_purchase_item_issue_receipt iss ON
                                    iss.id_issue_receipt = rec.issue_receipt_id
                                LEFT JOIN erp_purchase_item_details pur ON
                                    pur.id_purchase_entry_detail = rec.purchase_entry_detail_id
                                LEFT JOIN erp_purchase_entry ent ON
                                    ent.id_purchase_entry = pur.purchase_entry_id
                                LEFT JOIN erp_product pro ON
                                    pro.pro_id = pur.id_product_id
                                WHERE
                                    iss.issue_type = 1 AND iss.status = 1
                                    {filter_bill_type}
                                    AND DATE_FORMAT(iss.issue_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                                    AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                GROUP BY iss.id_issue_receipt

                        """
            else:
                query1 = f"""
                            SELECT  "Purchase Entry" as name,
                                    UNIX_TIMESTAMP(ent.created_on) AS code,
                                    DATE_FORMAT(ent.entry_date, '%d-%m-%Y') as entry_date,
                                    CONCAT("Purchase Entry / ",ent.ref_no," / ",COALESCE(SUM(pur.gross_wt),0)," :<br>",GROUP_CONCAT(CONCAT(des.design_name," / ",pur.purchase_touch,"%"," / ",pur.gross_wt) SEPARATOR ' <br> '))  as name,
                                    ent.ref_no,
                                    ent.entry_date as date,
                                    0 as amount_balance,
                                    (COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0)) as credit_amt,
                                    1 as type,
                                    COALESCE(SUM(pur.pure_wt), 0) AS credit_wt,
                                    0 AS debit_amt,
                                    0 AS debit_wt
                                FROM erp_purchase_item_details pur
                                LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = pur.purchase_entry_id
                                LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                                left join erp_design des on des.id_design = pur.id_design_id
                                LEFT JOIN(
                                        SELECT
                                            pro.id_metal_id,
                                            item.purchase_entry_id,
                                            COALESCE(SUM(charges.charges_amount), 0) AS charges_amount
                                        FROM erp_purchase_item_charges_details charges
                                        LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = charges.purchase_entry_detail_id
                                        LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                        LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                        where ent.is_cancelled = 0
                                        AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                        GROUP BY item.purchase_entry_id
                                ) charges ON charges.purchase_entry_id = pur.purchase_entry_id AND charges.id_metal_id = pro.id_metal_id

                                LEFT JOIN(
                                        SELECT
                                            pro.id_metal_id,
                                            item.purchase_entry_id,
                                            COALESCE(SUM(stn.pur_stn_cost), 0) AS stone_amount
                                        FROM erp_purchase_stone_details stn
                                        LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = stn.purchase_entry_detail_id
                                        LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                        LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                        where ent.is_cancelled = 0
                                        AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                        GROUP BY item.purchase_entry_id
                                ) stn ON stn.purchase_entry_id = pur.purchase_entry_id AND stn.id_metal_id = pro.id_metal_id
                        
                                LEFT JOIN(
                                        SELECT
                                            pro.id_metal_id,
                                            item.purchase_entry_id,
                                            COALESCE(SUM(other_metal.other_metal_cost), 0) AS other_metal_cost
                                        FROM erp_purchase_other_metal other_metal
                                        LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = other_metal.purchase_entry_detail_id
                                        LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                        LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                        where ent.is_cancelled = 0
                                        AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                        GROUP BY item.purchase_entry_id
                                ) other_metal ON other_metal.purchase_entry_id = pur.purchase_entry_id AND other_metal.id_metal_id = pro.id_metal_id

                                WHERE
                                    ent.is_cancelled = 0
                                    {filter_bill_type}
                                    AND DATE_FORMAT(ent.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                                    AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                GROUP BY ent.id_purchase_entry

                        """
            result1 = generate_query_result(query1)

            query2 = f"""
                    SELECT
                        "Rate Cut" as name,
                        UNIX_TIMESTAMP(rc.created_on) AS code,
                        CONCAT("Rate Cut / ", rc.ref_no," / ",rc.pure_wt," / @",rc.rate_per_gram,IF(rc.discount > 0, CONCAT(" / Discount: ", rc.discount), ""),IF(rc.remarks IS NOT NULL, CONCAT(" / Remarks: ", rc.remarks), "") ) as name,
                        rc.ref_no,
                        rc.entry_date as date,
                        rc.id_metal_id,
                        rc.purchase_entry_id,
                        0 AS type,
                        rc.pure_wt as metal_balance,
                        rc.amount as amount_balance,
                        0 AS credit_wt,
                        rc.amount AS credit_amt,
                        rc.pure_wt AS debit_wt,
                        0 AS debit_amt,
                        DATE_FORMAT(rc.entry_date, '%d-%m-%Y') as entry_date
                    FROM
                        erp_rate_cut rc
                    WHERE rc.id_supplier_id = {id_supplier} and rc.id_metal_id = {id_metal}
                    {rc_filter_bill_type}
                    AND DATE_FORMAT(rc.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                    """
            result2 = generate_query_result(query2)

            query3 = f"""
                        SELECT
                            "Metal Issue" as name,
                            CONCAT("Metal Issue / ", iss.ref_no," / ",mi.issue_weight," / ",mi.touch,"%",IF(mi.discount > 0, CONCAT(" / Discount: ", mi.discount), ""),IF(iss.remarks IS NOT NULL, CONCAT(" / Remarks: ", iss.remarks), "") )  as name,
                            pro.id_metal_id,
                            mi.purchase_entry_id,
                            mi.issue_weight AS issue_weight,
                            mi.pure_wt as metal_balance,
                            iss.ref_no,
                            iss.entry_date as date,
                            0 AS type,
                            0 AS credit_wt,
                            0 AS credit_amt,
                            mi.pure_wt AS debit_wt,
                            0 AS debit_amt,
                            DATE_FORMAT(iss.entry_date, '%d-%m-%Y') as entry_date,
                            UNIX_TIMESTAMP(iss.created_on) AS code

                        FROM
                            erp_supplier_metal_issue_details mi
                        LEFT JOIN erp_product pro ON
                            pro.pro_id = mi.id_product_id
                        LEFT JOIN erp_supplier_metal_issue iss ON
                            iss.id_issue = mi.issue_id
                        WHERE
                           iss.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                            {mi_filter_bill_type}
                         AND DATE_FORMAT(iss.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                    """
            result3 = generate_query_result(query3)

            query4 = f"""
                        SELECT
                            "Supplier Payment" as name,
                            CONCAT("Supplier Payment / ", pay.ref_no," / ",COALESCE(SUM(p.paid_amount)),IF(pay.remarks IS NOT NULL, CONCAT(" / Remarks: ", pay.remarks), "") )  as name,
                            p.metal_id,
                            p.ref_id as purchase_entry_id,
                            0 as metal_balance,
                            pay.ref_no,
                            pay.entry_date as date,
                            0 AS type,
                            0 AS credit_wt,
                            0 AS credit_amt,
                            0 AS debit_wt,
                            pay.id_purchase_payment,
                            COALESCE(SUM(p.paid_amount), 0) AS debit_amt,
                            DATE_FORMAT(pay.entry_date, '%d-%m-%Y') as entry_date,
                            UNIX_TIMESTAMP(pay.created_on) AS code
                        FROM `erp_supplier_payment_details` p
                        LEFT JOIN erp_supplier_payment pay ON
                            pay.id_purchase_payment = p.purchase_payment_id
                        WHERE
                            p.id_supplier_id = {id_supplier} and p.metal_id = {id_metal}
                            {pay_filter_bill_type}
                            AND DATE_FORMAT(pay.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                        GROUP BY  pay.id_purchase_payment
                    """
            result4 = generate_query_result(query4)

            query5 = f"""
                        SELECT
                            "Purchase Return" as name,
                            CONCAT("Purchase Return / ",ret.ref_no," / ",COALESCE(SUM(pur_ret.pure_wt), 0),"<br>",GROUP_CONCAT(CONCAT(pro.product_name," / ",pur_ret.touch,"%"," / ",pur_ret.pure_wt) SEPARATOR ' <br> '))  as name,
                            DATE_FORMAT(ret.entry_date, '%d-%m-%Y') as entry_date,
                            pro.id_metal_id as metal_id,
                            0 as metal_balance,
                            ret.ref_no,
                            ret.entry_date as date,
                            0 AS type,
                            0 AS credit_wt,
                            0 AS debit_amt,
                            COALESCE(SUM(pur_ret.pure_wt), 0) AS debit_wt,
                            ret.id_purchase_return,
                            0 AS credit_amt,
                            UNIX_TIMESTAMP(ret.created_on) AS code
                        FROM `erp_purchase_return_details` pur_ret
                        LEFT JOIN erp_purchase_return ret ON
                            ret.id_purchase_return = pur_ret.purchase_return_id
                        LEFT JOIN erp_product pro ON
                            pro.pro_id = pur_ret.id_product_id
                        WHERE
                            ret.status = 1 and ret.supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                            AND DATE_FORMAT(ret.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                        GROUP BY  ret.id_purchase_return
                    """
            result5 = generate_query_result(query5)

            query6 = f"""
                select "Repair Order" as name,
                CONCAT("Repair Order / ",j.ref_no,"<br>",GROUP_CONCAT(mt.metal_name))  as name,
                j.id_job_order,coalesce(sum(r.weight),0) as debit_wt,j.assigned_date as date,
                date_format(j.assigned_date,'%d-%m-%Y') as entry_date,
                UNIX_TIMESTAMP(j.assigned_date) AS code
                from erp_order_repair_extra_metal r
                left join metal mt on mt.id_metal = r.id_metal_id
                left join erp_order_details d on d.detail_id = r.order_detail_id
                left join erp_job_order_details ord on ord.order_detail_id = d.detail_id
                left join erp_job_order j on j.id_job_order = ord.job_order_id
                where j.supplier_id = {id_supplier} and r.id_metal_id = {id_metal}
                AND DATE_FORMAT(j.assigned_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                group by j.id_job_order
                    """
            result6 = generate_query_result(query6)


            query7 = f"""
                        SELECT
                            "Purchase Entry Charges" as name,
                            concat(group_concat(c.name)," - ",ent.ref_no) as name,
                            DATE_FORMAT(ent.entry_date, '%d-%m-%Y') as entry_date,
                            "" as metal_id,group_concat(c.name) as charges,
                            0 as metal_balance,
                            ent.ref_no,
                            ent.entry_date as date,
                            0 AS type,
                            0 AS credit_wt,
                            0 AS debit_amt,
                            0 AS debit_wt,
                            ent.id_purchase_entry,
                            COALESCE(SUM(s.charges_amount), 0) AS credit_amt,
                            UNIX_TIMESTAMP(ent.created_on) AS code
                        FROM `erp_purchase_entry_charges_details` s
                        LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = s.id_purchase_entry_id
                        left join other_charges c on c.id_other_charge = s.id_charges_id
                        WHERE
                            ent.is_approved = 1 and ent.id_supplier_id = {id_supplier} {filter_bill_type}
                            AND DATE_FORMAT(ent.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                        GROUP BY  ent.id_purchase_entry
                    """

            result7 = generate_query_result(query7)

            return_data = result1+result2+result3+result4+result5+result6+result7

            return_data_sorted = sorted(return_data, key=lambda x: x["code"])

            opening = get_supplier_openning_details(from_date,id_metal,id_supplier,bill_setting_type)
            return Response({"opening": opening,"details":return_data_sorted}, status=status.HTTP_200_OK)                   
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
def get_supplier_openning_details(date,id_metal,id_supplier,bill_setting_type):
    filter_bill_type = ''
    rc_filter_bill_type = ''
    mi_filter_bill_type = ''
    pay_filter_bill_type = ''
    if bill_setting_type == 1 or bill_setting_type == 0:
        filter_bill_type = f' AND ent.setting_bill_type = {bill_setting_type} '
        rc_filter_bill_type = f' AND rc.setting_bill_type = {bill_setting_type} '
        mi_filter_bill_type = f' AND d.setting_bill_type = {bill_setting_type} '
        pay_filter_bill_type = f' AND pay.setting_bill_type = {bill_setting_type} '

    # LEFT JOIN(
    #                     SELECT COALESCE(SUM(rec.recd_pieces), 0) AS pieces,
    #                         COALESCE(SUM(rec.recd_pure_wt), 0) AS pure_wt,
    #                         COALESCE(SUM(rec.recd_purchase_cost), 0) AS purchase_cost,
    #                         pur.purchase_entry_id,
    #                         pro.id_metal_id,
    #                         ent.id_supplier_id
    #                     FROM
    #                         erp_purchase_item_issue_receipt_details rec
    #                     LEFT JOIN erp_purchase_item_issue_receipt iss ON
    #                         iss.id_issue_receipt = rec.issue_receipt_id
    #                     LEFT JOIN erp_purchase_item_details pur ON
    #                         pur.id_purchase_entry_detail = rec.purchase_entry_detail_id
    #                     LEFT JOIN erp_purchase_entry ent ON
    #                         ent.id_purchase_entry = pur.purchase_entry_id
    #                     LEFT JOIN erp_product pro ON
    #                         pro.pro_id = pur.id_product_id
    #                     WHERE
    #                         iss.issue_type = 1 AND iss.status = 1                                 
    #                         AND DATE_FORMAT(iss.issue_date, '%Y-%m-%d') < '{date}' 
    #                         AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal} 
    #                     GROUP BY
    #                         ent.id_supplier_id
    #                 ) recv
    query =  f""" SELECT
                        ent.id_supplier,
                        opn.purchase_cost,
                        opn.pure_wt,
                        COALESCE(COALESCE(recv.pure_wt, 0) + COALESCE(opn.pure_wt,0) - COALESCE(purchase_return.purchase_return_wt,0)-COALESCE(repair.metal_weight,0) - ((COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0)) ), 0) AS balance_weight,
                        COALESCE(COALESCE(recv.other_amount, 0) + COALESCE(rate_cut.paid_amount, 0) + COALESCE(opn.purchase_cost,0) - COALESCE(payment.paid_amount, 0) + COALESCE(other_charges.credit_amt, 0), 0) AS balance_amount
                    FROM
                        erp_supplier ent
                    LEFT JOIN(
                            SELECT COALESCE(SUM(pur.pieces), 0) AS pieces,
                            COALESCE(SUM(pur.pure_wt), 0) AS pure_wt,
                            COALESCE(SUM(pur.purchase_cost), 0) AS purchase_cost,
                            (COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0)) as other_amount,
                            pur.purchase_entry_id,
                            pro.id_metal_id,
                            ent.id_supplier_id
                        FROM
                            erp_purchase_item_details pur 
                        LEFT JOIN erp_purchase_entry ent ON
                            ent.id_purchase_entry = pur.purchase_entry_id
                        LEFT JOIN erp_product pro ON
                            pro.pro_id = pur.id_product_id
                        LEFT JOIN(
                                SELECT
                                    ent.id_supplier_id,
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(charges.charges_amount), 0) AS charges_amount
                                FROM erp_purchase_item_charges_details charges
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = charges.purchase_entry_detail_id
                                LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                where ent.is_cancelled = 0
                                AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                AND DATE_FORMAT(ent.entry_date, '%Y-%m-%d') < '{date}' 
                                {filter_bill_type}
                                GROUP BY ent.id_supplier_id
                        ) charges ON charges.id_supplier_id = ent.id_supplier_id

                        LEFT JOIN(
                                SELECT
                                    ent.id_supplier_id,
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(stn.pur_stn_cost), 0) AS stone_amount
                                FROM erp_purchase_stone_details stn
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = stn.purchase_entry_detail_id
                                LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                where ent.is_cancelled = 0
                                AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                AND DATE_FORMAT(ent.entry_date, '%Y-%m-%d') < '{date}' 
                                {filter_bill_type}
                                GROUP BY ent.id_supplier_id
                        ) stn ON stn.id_supplier_id = ent.id_supplier_id 
                
                        LEFT JOIN(
                                SELECT
                                    ent.id_supplier_id,
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(other_metal.other_metal_cost), 0) AS other_metal_cost
                                FROM erp_purchase_other_metal other_metal
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = other_metal.purchase_entry_detail_id
                                LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                where ent.is_cancelled = 0
                                AND ent.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                AND DATE_FORMAT(ent.entry_date, '%Y-%m-%d') < '{date}' 
                                {filter_bill_type}
                                GROUP BY ent.id_supplier_id
                        ) other_metal ON other_metal.id_supplier_id = ent.id_supplier_id 
                        WHERE
                            ent.is_cancelled = 0 and                      
                            DATE_FORMAT(ent.entry_date, '%Y-%m-%d') < '{date}' 
                            {filter_bill_type}
                            and pro.id_metal_id = {id_metal} 
                            AND ent.id_supplier_id = {id_supplier}
                        GROUP BY
                            ent.id_supplier_id
                    ) recv
                    ON
                        recv.id_supplier_id = ent.id_supplier
                    LEFT JOIN(
                        SELECT
                            COALESCE(SUM(pur.weight), 0) AS pure_wt,
                            COALESCE(SUM(pur.amount), 0) AS purchase_cost,
                            pur.id_metal_id,
                            pur.id_supplier_id
                        FROM
                            erp_purchase_supplier_opening pur 
                        WHERE                   
                            pur.id_metal_id = {id_metal} 
                            AND pur.id_supplier_id = {id_supplier}
                        GROUP BY
                            pur.id_supplier_id
                    ) opn
                    ON
                        opn.id_supplier_id = ent.id_supplier
                    LEFT JOIN(
                            SELECT
                                sp.id_supplier_id,
                                COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                            FROM
                                erp_supplier_payment_details sp
                            LEFT JOIN erp_supplier_payment pay ON
                                pay.id_purchase_payment = sp.purchase_payment_id
                            WHERE
                                sp.id_supplier_id = {id_supplier} and sp.metal_id = {id_metal}
                                AND DATE_FORMAT(pay.entry_date, '%Y-%m-%d') < '{date}'
                                {pay_filter_bill_type}
                            GROUP BY
                                sp.id_supplier_id
                    ) payment
                    ON
                        payment.id_supplier_id = ent.id_supplier
                    LEFT JOIN(
                        SELECT rc.id_supplier_id,
                            COALESCE(SUM(rc.amount), 0) AS paid_amount,
                            COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
                        FROM
                            erp_rate_cut rc
                        WHERE rc.id_supplier_id = {id_supplier} and rc.id_metal_id = {id_metal}
                        AND DATE_FORMAT(rc.entry_date, '%Y-%m-%d') < '{date}'
                         {rc_filter_bill_type}
                        GROUP BY
                            rc.id_supplier_id

                    ) rate_cut
                    ON
                        rate_cut.id_supplier_id = ent.id_supplier
                    LEFT JOIN(
                            SELECT
                                d.id_supplier_id,
                                COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                                COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                            FROM
                                erp_supplier_metal_issue_details mi
                            LEFT JOIN erp_product pro ON
                                pro.pro_id = mi.id_product_id
                            LEFT JOIN erp_supplier_metal_issue d ON
                                d.id_issue = mi.issue_id
                            WHERE
                                 d.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                                AND DATE_FORMAT(d.entry_date, '%Y-%m-%d') < '{date}'
                                {mi_filter_bill_type}

                            GROUP BY
                                d.id_supplier_id
                    ) metal_issue
                    ON
                        metal_issue.id_supplier_id = ent.id_supplier

                    LEFT JOIN (
                    SELECT
                        ret.supplier_id,
                        COALESCE(SUM(pur_ret.pure_wt), 0) AS purchase_return_wt
                    FROM `erp_purchase_return_details` pur_ret
                    LEFT JOIN erp_purchase_return ret ON
                        ret.id_purchase_return = pur_ret.purchase_return_id
                    LEFT JOIN erp_product pro ON
                        pro.pro_id = pur_ret.id_product_id
                    WHERE
                        ret.status = 1 and ret.supplier_id = {id_supplier} and pro.id_metal_id = {id_metal}
                        AND DATE_FORMAT(ret.entry_date, '%Y-%m-%d') < '{date}'
                    GROUP BY  ret.supplier_id

                    ) purchase_return
                    ON
                        purchase_return.supplier_id = ent.id_supplier


                    left join (select j.supplier_id,coalesce(sum(r.weight),0) as metal_weight
                    from erp_order_repair_extra_metal r
                    left join erp_order_details d on d.detail_id = r.order_detail_id
                    left join metal mt on mt.id_metal = r.id_metal_id
                    left join erp_job_order_details ord on ord.order_detail_id = d.detail_id
                    left join erp_job_order j on j.id_job_order = ord.job_order_id
                    where j.supplier_id = {id_supplier} and r.id_metal_id = {id_metal}  
                    AND DATE_FORMAT(j.assigned_date, '%Y-%m-%d') < '{date}'
                    group by j.supplier_id) as repair ON repair.supplier_id = ent.id_supplier

                    left join (SELECT
                            ent.id_supplier_id,
                            COALESCE(SUM(s.charges_amount), 0) AS credit_amt
                        FROM `erp_purchase_entry_charges_details` s
                        LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = s.id_purchase_entry_id
                        left join other_charges c on c.id_other_charge = s.id_charges_id
                        WHERE
                            ent.is_approved = 1 and ent.id_supplier_id = {id_supplier} {filter_bill_type}
                            AND DATE_FORMAT(ent.entry_date, '%Y-%m-%d') < '{date}'
                        GROUP BY  ent.id_supplier_id) as other_charges on other_charges.id_supplier_id = ent.id_supplier

                    WHERE
                        ent.id_supplier = {id_supplier}
                    GROUP BY
                        ent.id_supplier
                    """
    print(query)
    result = generate_query_result(query)
    return result[0]
    
class CustomerLedgerReportView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_customer = request.data.get('id_customer',None)
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_metal = request.data.get('id_metal',None)
        return_data = []
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_customer or not id_metal:
            return Response({"message": "Metal and Customer is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
         
            query1 = f"""
                        SELECT  "Purchase Entry" as name,
                                DATE_FORMAT(i.invoice_date, '%d-%m-%Y') as entry_date,
                                CONCAT("Purchase Entry / ",i.sales_invoice_no," / ",COALESCE(SUM(d.gross_wt),0)," :<br>",GROUP_CONCAT(CONCAT(pro.product_name,"/",d.gross_wt," / ",d.purchase_touch,"%"," / ",d.pure_weight) SEPARATOR ' <br> '))  as name,
                                i.sales_invoice_no,
                                i.invoice_date as date,
                                0 as amount_balance,
                                (COALESCE(SUM(d.total_mc_value), 0)) as credit_amt,
                                1 as type,
                                COALESCE(SUM(d.pure_weight), 0) AS credit_wt,
                                0 AS debit_amt,
                                0 AS debit_wt
                            FROM erp_invoice_sales_details d
                            LEFT JOIN erp_invoice i ON i.erp_invoice_id = d.invoice_bill_id_id
                            LEFT JOIN erp_product pro ON pro.pro_id = d.id_product_id
                            WHERE
                                i.invoice_status = 1
                                AND DATE_FORMAT(i.invoice_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                                AND i.id_customer_id = {id_customer} and pro.id_metal_id = {id_metal}
                            GROUP BY i.erp_invoice_id

                    """
            result1 = generate_query_result(query1)

            query2 = f"""
                    SELECT
                        "Rate Cut" as name,
                        CONCAT("Rate Cut / ", rc.ref_no," / ",rc.pure_wt," / @",rc.rate_per_gram,IF(rc.discount > 0, CONCAT(" / Discount: ", rc.discount), "") ) as name,
                        rc.ref_no,
                        rc.entry_date as date,
                        rc.id_metal_id,
                        rc.erp_invoice_id_id,
                        0 AS type,
                        rc.pure_wt as metal_balance,
                        rc.amount as amount_balance,
                        0 AS credit_wt,
                        rc.amount AS credit_amt,
                        rc.pure_wt AS debit_wt,
                        0 AS debit_amt,
                        DATE_FORMAT(rc.entry_date, '%d-%m-%Y') as entry_date
                    FROM
                        erp_customer_rate_cut rc
                    WHERE rc.id_customer_id = {id_customer} and rc.id_metal_id = {id_metal}
                    AND DATE_FORMAT(rc.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                    """
            result2 = generate_query_result(query2)

            query3 = f"""
                        SELECT
                            "Metal Issue" as name,
                            CONCAT("Metal Issue / ", iss.ref_no," / ",mi.issue_weight," / ",mi.touch,"%",IF(mi.discount > 0, CONCAT(" / Discount: ", mi.discount), "") )  as name,
                            pro.id_metal_id,
                            mi.purchase_entry_id,
                            mi.issue_weight AS issue_weight,
                            mi.pure_wt as metal_balance,
                            iss.ref_no,
                            iss.entry_date as date,
                            0 AS type,
                            0 AS credit_wt,
                            0 AS credit_amt,
                            mi.pure_wt AS debit_wt,
                            0 AS debit_amt,
                            DATE_FORMAT(iss.entry_date, '%d-%m-%Y') as entry_date

                        FROM
                            erp_supplier_metal_issue_details mi
                        LEFT JOIN erp_product pro ON
                            pro.pro_id = mi.id_product_id
                        LEFT JOIN erp_supplier_metal_issue iss ON
                            iss.id_issue = mi.issue_id
                        WHERE
                           iss.id_supplier_id = {id_customer} and pro.id_metal_id = {id_metal}
                         AND DATE_FORMAT(iss.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                    """
            result3 = generate_query_result(query3)

            query4 = f"""
                        SELECT
                            "Supplier Payment" as name,
                            CONCAT("Supplier Payment / ", pay.ref_no," / ",COALESCE(SUM(p.paid_amount)) )  as name,
                            pay.metal_id,
                            p.ref_id as purchase_entry_id,
                            0 as metal_balance,
                            pay.ref_no,
                            pay.entry_date as date,
                            0 AS type,
                            0 AS credit_wt,
                            0 AS credit_amt,
                            0 AS debit_wt,
                            pay.id,
                            COALESCE(SUM(p.paid_amount), 0) AS debit_amt,
                            DATE_FORMAT(pay.entry_date, '%d-%m-%Y') as entry_date
                        FROM `erp_customer_purchase_payment_details` p
                        LEFT JOIN erp_customer_purchase_payment pay ON
                            pay.id = p.customer_payment_id
                        WHERE
                            pay.id_customer_id = {id_customer} and pay.metal_id = {id_metal}
                            AND DATE_FORMAT(pay.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                        GROUP BY  pay.id
                    """
            result4 = generate_query_result(query4)

            query5 = f"""
                        SELECT
                            "Purchase Return" as name,
                            CONCAT("Purchase Return / ",ret.ref_no," / ",COALESCE(SUM(pur_ret.pure_wt), 0),"<br>",GROUP_CONCAT(CONCAT(pro.product_name," / ",pur_ret.touch,"%"," / ",pur_ret.pure_wt) SEPARATOR ' <br> '))  as name,
                            DATE_FORMAT(ret.entry_date, '%d-%m-%Y') as entry_date,
                            pro.id_metal_id as metal_id,
                            0 as metal_balance,
                            ret.ref_no,
                            ret.entry_date as date,
                            0 AS type,
                            0 AS credit_wt,
                            0 AS debit_amt,
                            COALESCE(SUM(pur_ret.pure_wt), 0) AS debit_wt,
                            ret.id_purchase_return,
                            0 AS credit_amt
                        FROM `erp_purchase_return_details` pur_ret
                        LEFT JOIN erp_purchase_return ret ON
                            ret.id_purchase_return = pur_ret.purchase_return_id
                        LEFT JOIN erp_product pro ON
                            pro.pro_id = pur_ret.id_product_id
                        WHERE
                            ret.status = 1 and ret.supplier_id = {id_customer} and pro.id_metal_id = {id_metal}
                            AND DATE_FORMAT(ret.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
                        GROUP BY  ret.id_purchase_return
                    """
            result5 = generate_query_result(query5)

            return_data = result1+result2+result3+result4+result5

            return_data_sorted = sorted(return_data, key=lambda x: x["date"])

            opening = self.get_customer_openning_details(from_date,id_metal,id_customer)
            return Response({"opening": opening,"details":return_data_sorted}, status=status.HTTP_200_OK)                   
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_customer_openning_details(self,date,id_metal,id_customer):

        query = F"""
            select c.id_customer,(coalesce(inv.pure_weight,0)-coalesce(rc.pure_wt,0)) as balance_weight,
            coalesce(coalesce(rc.amount,0) - coalesce(pay.paid_amount,0),0) as balance_amount
            from customers c 
            left join (select coalesce(sum(s.pure_weight),0) as pure_weight,
            i.id_customer_id
            from erp_invoice i 
            left join erp_invoice_sales_details s on s.invoice_bill_id_id = i.erp_invoice_id
                where i.invoice_status = 1 and date_format(i.invoice_date,'%Y-%m-%d') < '{date}'
                group by i.id_customer_id) as inv on inv.id_customer_id = c.id_customer

            left join (select coalesce(sum(c.pure_wt),0) as pure_wt,c.id_customer_id,coalesce(sum(c.amount),0) as amount
                    from erp_customer_rate_cut c
                    where date_format(c.entry_date, '%Y-%m-%d') < '{date}'
                    group by c.id_customer_id) as rc on rc.id_customer_id = c.id_customer
            left join (select coalesce(sum(pay.paid_amount),0) as paid_amount,p.id_customer_id
                    from erp_customer_purchase_payment_details pay
                    LEFT JOIN erp_customer_purchase_payment p on p.id =pay.customer_payment_id
                    where  p.id_customer_id = {id_customer} and p.metal_id = {id_metal} and date_format(p.entry_date, '%Y-%m-%d') < '{date}'
                    group by p.id_customer_id ) as pay on pay.id_customer_id = c.id_customer

            where c.id_customer = {id_customer}
        """
        result = generate_query_result(query)
        return result[0]


class PurchaseReturnReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        output = []
        fin_output = []
    
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
    
        try:
            queryset = ErpPurchaseReturn.objects.all()
            if id_branch:
                queryset = queryset.filter(branch__in=id_branch)
            if from_date and to_date:
                queryset = queryset.filter(entry_date__range=[from_date, to_date])
            serializer = ErpPurchaseReturnSerializer(queryset, many=True)
            for data in serializer.data:
                item_details = ErpPurchaseReturnDetails.objects.filter(purchase_return=data['id_purchase_return'])
                item_details_serializer = ErpPurchaseReturnDetailsSerializer(item_details, many=True)
                for item in item_details_serializer.data:
                    product_details = Product.objects.get(pro_id=item['id_product'])
                    if(item['type'] == 1):
                        item.update({"purchase_type":"General"})
                    elif(item['type'] == 2):
                        item.update({"purchase_type":"Tag"})
                    else:
                        item.update({"purchase_type":"Non Tag"})
                        
                    if(data['status'] == 1):
                        item.update({"status":"Success", "status_color":"success"})
                    else:
                        item.update({"status":"Canceled", "status_color":"danger"})
                        
                    item.update({
                        "stock_type": 'Tagged' if product_details.stock_type == 0 else 'Non Tag',
                        "id_category": product_details.cat_id.id_category,
                        "product_name":product_details.product_name,
                        "branch_name":data['branch_name'],
                        "supplier_name":data['supplier_name'],
                        "date":format_date(data['entry_date']),
                        "ref_no":data['ref_no'],
                    })
                    # print(item)
                    if item not in output:
                        output.append(item)
    
            paginator, page = pagination.paginate_queryset(output, request,None,PURCHASE_RETURN_REPORT)
            columns = get_reports_columns_template(request.user.pk,PURCHASE_RETURN_REPORT,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context = {
                'columns': columns,
                'actions': ACTION_LIST,
                'page_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req': True,
                'filters': filters_copy
            }
    
            return pagination.paginated_response(output, context)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
# class PurchaseReturnReportView(generics.GenericAPIView):
#     permission_classes = [IsEmployee]
    
#     def post(self, request, *args, **kwargs):
#         id_branch = request.data.get('branch')
#         from_date = request.data.get('fromDate')
#         to_date = request.data.get('toDate')
#         output = []

#         if not from_date or not to_date:
#             return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Apply initial filters on ErpPurchaseReturn
#             queryset = ErpPurchaseReturn.objects.all()
#             if id_branch:
#                 queryset = queryset.filter(branch__in=id_branch)
#             if from_date and to_date:
#                 queryset = queryset.filter(entry_date__range=[from_date, to_date])

#             # Serialize the purchase returns
#             serializer = ErpInvoiceDiscountOldMetalDetailsSerializer(queryset, many=True)

#             # Collect all purchase return IDs
#             purchase_return_ids = [data['id_purchase_return'] for data in serializer.data]

#             # Fetch all related purchase return details in one query
#             item_details = ErpPurchaseReturnDetails.objects.filter(purchase_return__in=purchase_return_ids).select_related('id_product__cat_id')

#             # Fetch all required products in bulk
#             product_ids = {item.id_product for item in item_details}
#             product_map = Product.objects.in_bulk(product_ids)  # Fetch all products in one query

#             # Process purchase return details efficiently
#             for item in item_details:
#                 product = product_map.get(item.id_product)  # Get product details from bulk query result
#                 if not product:
#                     continue  # Skip if product not found

#                 output.append({
#                     "id_purchase_return": item.purchase_return_id,
#                     "id_product": item.id_product,
#                     "stock_type": 'Tagged' if product.stock_type == 0 else 'Non Tag',
#                     "id_category": product.cat_id.id_category,
#                 })

#             # Apply pagination at the correct level (on the final output)
#             paginator, page = pagination.paginate_queryset(output, request)

#             filters_copy = FILTERS.copy()
#             filters_copy['isDateFilterReq'] = True
#             filters_copy['isBranchFilterReq'] = True
#             filters_copy['isSchemeFilterReq'] = False

#             context = {
#                 'columns': PURCHASE_REPORT,
#                 'actions': ACTION_LIST,
#                 'page_count': paginator.count,
#                 'total_pages': paginator.num_pages,
#                 'current_page': page.number,
#                 'is_filter_req': True,
#                 'filters': filters_copy
#             }

#             return pagination.paginated_response(page, context)

#         except KeyError as e:
#             return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class OtherMetalProfitLossReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        query = f"""
            select p.ref_no,s.supplier_name,date_format(p.entry_date,'%d-%m-%Y') as dateadd,ifnull(sum(i.gross_wt),0) as gross_wt,ifnull(sum(i.net_wt),0) as net_wt,
            avg(i.touch) as melting_touch,mt.metal_name,r.id_melting_receipt,r.melting_issue_ref_no_id,
            r.tested_touch,if(avg(i.touch) < r.tested_touch,'Profit','Loss') as type,
            IFNULL(tsd_supplier.supplier_name,'') as tested_supplier
            from erp_melting_receipt_details r
            left join erp_melting_issue_details i on i.id_metal_process_id = r.melting_issue_ref_no_id
            left join metal mt on mt.id_metal = i.id_metal_id
            left join erp_metal_process p on p.id_metal_process = i.id_metal_process_id
            left join erp_supplier s on s.id_supplier = p.id_supplier_id
            left join erp_testing_details t on t.id_melting_receipt_id = r.id_melting_receipt
            left join erp_metal_process tstd_center on tstd_center.id_metal_process = t.id_metal_process_id
            left join erp_supplier tsd_supplier on tsd_supplier.id_supplier = tstd_center.id_supplier_id
            WHere DATE_FORMAT(p.entry_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
            
            group by r.id_melting_receipt,mt.id_metal
            order by p.id_metal_process desc
                """
        result = generate_query_result(query)

        paginator, page = pagination.paginate_queryset(result, request,None,OTHER_METAL_PROFIT_LOSS_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,OTHER_METAL_PROFIT_LOSS_COLUMN_LIST,request.data["path_name"])
        context={'columns':columns,'actions':ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':True}
        return pagination.paginated_response(result,context)

class ClosingCash(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        id_branch = request.query_params.get('id_branch')
        branch_date = BranchEntryDate()
        entry_date = branch_date.get_entry_date(id_branch)
        entry_date = entry_date + timedelta(days=1)
        closing = get_openning_cash(entry_date,id_branch)
        return Response({"cash_balance":closing}, status=status.HTTP_200_OK)
    
class BankStatementReportsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
            id_branch = request.data.get('branch')
            from_date = request.data.get('fromDate')
            to_date = request.data.get('toDate')
            bank = request.data.get('bank')
            # if not bank:
            #     return Response({"message": "Bank is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not from_date or not to_date:
                return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        # try:
            response_data=[]

            sales_queryset = ErpInvoicePaymentModeDetail.objects.filter(id_bank__isnull = False,invoice_bill_id__invoice_status = 1,invoice_bill_id__invoice_date__range=[from_date, to_date])

            if(id_branch):
                sales_queryset  = sales_queryset.filter(invoice_bill_id__id_branch__in = id_branch)

            if(bank):
                sales_queryset  = sales_queryset.filter(id_bank = bank)
            
            if from_date and to_date:
                sales_queryset = sales_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            data = ErpInvoicePaymentModeDetailSerializer(sales_queryset,many=True).data

            for item, instance in zip(data, sales_queryset):
                bill_no=get_bill_no(item['invoice_bill_id'])
                response_data.append({
                    "ref_no": bill_no,
                    "payment_mode": item['mode_name'],
                    "payment_type": item['payment_type'],
                    "trans_name":f" {bill_no} {item['mode_name']} PAYMENT { 'CREDITED TO' if item['payment_type'] == 1 else 'DEBITED TO' } {item['bank_name']} - {item['acc_number']}",
                    "credit": item['payment_amount'] if item['payment_type'] == 1 else 0,
                    "debit":  0 if item['payment_type'] == 1 else item['payment_amount'],
                    "ref_id":item['invoice_pay_id'] ,
                    "bank_name":item['bank_name'] ,
                    "id_bank":item['id_bank'] ,
                    "type":1,
                    "date":instance.invoice_bill_id.invoice_date,
                })


            # Bank Deposit entry
            bakn_deposit_queryset = ErpIssueReceipt.objects.filter(bill_status = 1, issue_type = 5,bill_date__range=[from_date, to_date],id_bank__isnull= False)
            if(id_branch):
                bakn_deposit_queryset  = bakn_deposit_queryset.filter(branch__in = id_branch)

            if(bank):
                bakn_deposit_queryset  = bakn_deposit_queryset.filter(id_bank = bank)

            bank_depost_serializer = ErpIssueReceiptSerializer(bakn_deposit_queryset,many=True).data
            for item, instance in zip(bank_depost_serializer, bakn_deposit_queryset):
            # for item in bank_depost_serializer:
                response_data.append({
                    "ref_no": item['bill_no'],
                    "payment_mode": "Cash",
                    "payment_type" : 1,
                    "trans_name":  "Bank Deposit Remarks - " + item['remarks'] + " Ref NO" + item['bill_no'],
                    "credit": item['amount'],
                    "debit":  0,
                    "ref_id":item['id'] ,
                    "bank_name":item['bank_name'] ,
                    "id_bank":item['id_bank'] ,
                    "type":2,
                    "date":datetime.strptime(item['bill_date'], "%Y-%m-%d").date(),
                })
            # Bank Deposit entry

            issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt__bill_status = 1,issue_receipt__bill_date__range=[from_date, to_date],bank__isnull= False)
            if(id_branch):
                issue_payment_queryset  = issue_payment_queryset.filter(issue_receipt__branch__in = id_branch)

            if(bank):
                issue_payment_queryset  = issue_payment_queryset.filter(bank = bank)

            issue_payment = ErpIssueReceiptPaymentDetailsSerializer(issue_payment_queryset,many=True).data

            for item, instance in zip(issue_payment, issue_payment_queryset):
                response_data.append({
                    "ref_no": instance.issue_receipt.bill_no,
                    "payment_mode": item['mode_name'],
                    "payment_type": item['type'],
                    "trans_name":f" {instance.issue_receipt.bill_no} {item['mode_name']} PAYMENT { 'CREDITED TO' if item['type'] == 1 else 'DEBITED TO' } {item['bank_name']} - {item['acc_number']}",
                    "credit": item['payment_amount'] if item['type'] == 1 else 0,
                    "debit":  0 if item['type'] == 1 else item['payment_amount'],
                    "ref_id":item['issue_receipt'] ,
                    "bank_name":item['bank_name'] ,
                    "id_bank":item['bank'] ,
                    "type":2,
                    "date":instance.issue_receipt.bill_date,
                })

            supplier_payment_queryset = ErpSupplierPaymentModeDetail.objects.filter(id_bank__isnull= False,purchase_payment__entry_date__range=[from_date, to_date])

            if(id_branch):
                supplier_payment_queryset  = supplier_payment_queryset.filter(purchase_payment__cash_from_branch__in = id_branch)

            if(bank):
                supplier_payment_queryset  = supplier_payment_queryset.filter(id_bank = bank)

            supplier_payment = ErpSupplierPaymentModeDetailSerializer(supplier_payment_queryset,many=True).data

            for item, instance in zip(supplier_payment, supplier_payment_queryset):
                response_data.append({
                    "ref_no": instance.purchase_payment.ref_no,
                    "payment_mode": item['mode_name'],
                    "payment_type": item['payment_type'],
                    "trans_name":f" {instance.purchase_payment.ref_no} {item['mode_name']} PAYMENT { 'CREDITED TO' if item['payment_type'] == 1 else 'DEBITED TO' } {item['bank_name']} - {item['acc_number']}, Remarks:- {instance.purchase_payment.remarks}",
                    "credit": item['payment_amount'] if item['payment_type'] == 1 else 0,
                    "debit":  0 if item['payment_type'] == 1 else item['payment_amount'],
                    "ref_id":item['purchase_payment'] ,
                    "bank_name":item['bank_name'] ,
                    "id_bank":item['id_bank'] ,
                    "type":3,
                    "date":instance.purchase_payment.entry_date,
                })
            
            return_grouped_data = self.get_grouped_data(response_data)
            response_data1 = []
            for index, data in return_grouped_data.items():
                if isinstance(index, str):
                    date_obj = datetime.strptime(index, "%Y-%m-%d").date()
                elif isinstance(index, date):
                    date_obj = index
                opening = get_openning(date_obj,id_branch,bank)
                response_data1.append({
                    "entry_date" : format_date(index),
                    "opening" : opening,
                    "details": data
                })
            
            response_data1 = sorted(
                response_data1,
                key=lambda x: datetime.strptime(x['entry_date'], "%d-%m-%Y")
            )
            if len(response_data1) == 0:
                opening = get_openning(to_date,id_branch,bank)
                response_data1.append({
                    "entry_date" : format_date(to_date),
                    "opening" : opening,
                    "details": []
                })
            return Response(response_data1, status=status.HTTP_200_OK)
        
    def get_grouped_data(self,data):
        response_data1={}

        for payment in data:
            response_data1.setdefault(payment['date'], []).append(payment)

        return response_data1

def get_openning(date,id_branch,bank):

    opening_amount = 0

    sales_queryset = ErpInvoicePaymentModeDetail.objects.filter(id_bank__isnull= False,invoice_bill_id__invoice_status = 1,invoice_bill_id__invoice_date__lt=date)

    issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(bank__isnull= False, issue_receipt__bill_status = 1 , issue_receipt__bill_date__lt=date)

    if(id_branch):
        issue_payment_queryset  = issue_payment_queryset.filter(issue_receipt__branch__in = id_branch)
        sales_queryset  = sales_queryset.filter(invoice_bill_id__id_branch__in = id_branch)

    if(bank):
        issue_payment_queryset  = issue_payment_queryset.filter(bank = bank)
        sales_queryset  = sales_queryset.filter(id_bank = bank)

    issue_payment_queryset = issue_payment_queryset.aggregate(
            amount=Sum(
                Case(
                    When(type=1, then=F('payment_amount')),
                    default=-F('payment_amount'),
                    output_field=DecimalField()  
                )
            ),
        )
    sales_queryset = sales_queryset.aggregate(
            amount=Sum(
                Case(
                    When(payment_type=1, then=F('payment_amount')),
                    default=-F('payment_amount'),
                    output_field=DecimalField()  
                )
            ),
        )
    
    chit_payments = PaymentModeDetail.objects.filter(id_pay__payment_status=1, id_pay__date_payment__lt=date,id_bank__isnull= False)

    if(id_branch):
        chit_payments  = chit_payments.filter(id_pay__id_branch__in = id_branch)
    
    if(bank):
        chit_payments  = chit_payments.filter(id_bank = bank)

    chit_payments  = chit_payments.aggregate(
        amount=Sum(F('payment_amount')),
    )

    supplier_payment = ErpSupplierPaymentModeDetail.objects.filter(id_bank__isnull= False, purchase_payment__entry_date__lt=date)
    
    if(id_branch):

        supplier_payment  = supplier_payment.filter(purchase_payment__cash_from_branch__in = id_branch)

    if(bank):
        supplier_payment  = supplier_payment.filter(id_bank = bank)
    
    supplier_payment  = supplier_payment.aggregate(
        amount=Sum(F('payment_amount')),
    )

    # Bank Deposit entry
    bakn_deposit_queryset = ErpIssueReceipt.objects.filter(bill_status = 1, issue_type = 5 , bill_date__lt = date , id_bank__isnull= False)
    if(id_branch):
        bakn_deposit_queryset  = bakn_deposit_queryset.filter(branch__in = id_branch)

    if(bank):
        bakn_deposit_queryset  = bakn_deposit_queryset.filter(id_bank = bank)
    
    bank_deposit_payment = bakn_deposit_queryset.aggregate(amount=Sum(F('amount')))



    if(chit_payments['amount']):
        opening_amount += chit_payments['amount']

    if(issue_payment_queryset['amount']):
        opening_amount += issue_payment_queryset['amount']

    if(sales_queryset['amount']):
        opening_amount += sales_queryset['amount']

    if(supplier_payment['amount']):
        opening_amount -= supplier_payment['amount']
    
    opening_amount += Decimal(bank_deposit_payment['amount'] or 0)
    
    return opening_amount


class ReOrderReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        product_id = request.data.get('product')
        if not product_id :
            return Response({"message": "Select Product To View Report"}, status=status.HTTP_400_BAD_REQUEST)
        sub_design_req = RetailSettings.objects.get(name='is_sub_design_req').value
        try:
            queryset = ErpTagging.objects.filter(tag_status = 1,tag_product_id = product_id)

            product = Product.objects.get(pro_id = product_id)

            reorder_settings = ErpReorderSettings.objects.all()

            if(id_branch):
                queryset  = queryset.filter(tag_current_branch__in = id_branch)
                reorder_settings = reorder_settings.filter(branch__in = id_branch)
                
            total = queryset
            if(sub_design_req == 1):
                total = total.values("tag_current_branch","tag_product_id","tag_design_id","tag_sub_design_id")
                result = (queryset.values("tag_current_branch","tag_product_id","tag_design_id","tag_sub_design_id").annotate(
                    product = F("tag_product_id__product_name"),
                    design = F("tag_design_id__design_name"),
                    sub_design = F("tag_sub_design_id__sub_design_name"),
                    pcs=Sum("tag_pcs"),
                    wt =Sum("tag_gwt"),
                    branch_name = F("tag_current_branch__name"),
                    current_branch = F("tag_current_branch"),
                    ))
            else :
                total = total.values("tag_current_branch","tag_product_id","tag_design_id")
                result = (queryset.values("tag_current_branch","tag_product_id","tag_design_id").annotate(
                    product = F("tag_product_id__product_name"),
                    design = F("tag_design_id__design_name"),
                    pcs=Sum("tag_pcs"),
                    wt =Sum("tag_gwt"),
                    branch_name = F("tag_current_branch__name"),
                    current_branch = F("tag_current_branch"),
                ))
            
             
            print(result)
            weight_range = WeightRange.objects.filter(id_product = product)
            size = Size.objects.filter(id_product= product)
            reorder_based_on = product.reorder_based_on
            column = []
            if(reorder_based_on == 3):
                for weight, instance in zip(weight_range.values(), weight_range):
                    sett = reorder_settings.filter(weight_range=instance.pk)
                    size_details = []
                    seen_sizes = set()  # To track unique sizes
                    for s in sett:
                        if s.size.pk not in seen_sizes:
                            seen_sizes.add(s.size.pk)
                            size_details.append({
                                "size": s.size.pk,
                                "size_name": s.size.name
                            })
                    if(size_details):
                        column.append({
                            **weight,
                            "size_details": size_details
                        })
            elif(reorder_based_on == 2):
                sett = reorder_settings
                seen_sizes = set()
                for s in sett:
                    if s.size.pk not in seen_sizes:
                        seen_sizes.add(s.size.pk)
                        column.append({
                            "size": s.size.pk,
                            "size_name": s.size.name
                        })

            elif(reorder_based_on == 1):
                sett = reorder_settings
                seen_sizes = set()
                for s in sett:
                    if s.weight_range.pk not in seen_sizes:
                        seen_sizes.add(s.weight_range.pk)
                        column.append({
                            "id_weight_range": s.weight_range.pk,
                            "weight_range_name": s.weight_range.weight_range_name
                        })

            for data in result:
                settings = reorder_settings
                if(reorder_based_on == 3):
                    if(sub_design_req == 1):
                        settings = reorder_settings.filter(branch = data['current_branch'],product = product,design = data['tag_design_id'],sub_design = data['tag_sub_design_id'])
                    else:
                        settings = reorder_settings.filter(branch = data['current_branch'],product = product,design = data['tag_design_id'])

                    if(weight_range and size and settings):
                        temp_name=''
                        setting = settings
                        filtered_data = total
                        for weight in weight_range:
                            setting = settings.filter(weight_range = weight.pk)
                            if(sub_design_req == 1):
                                filtered_data = total.filter(tag_current_branch = data['current_branch'],tag_design_id = data['tag_design_id'],tag_sub_design_id = data['tag_sub_design_id'],tag_gwt__gte = weight.from_weight ,tag_gwt__lte = weight.to_weight)
                                temp_name = f"{product_id}_{data['tag_design_id']}_{data['tag_sub_design_id']}"
                            else:
                                filtered_data = total.filter(tag_current_branch = data['current_branch'],tag_design_id = data['tag_design_id'],tag_gwt__gte = weight.from_weight ,tag_gwt__lte = weight.to_weight)
                                temp_name = f"{product_id}_{data['tag_design_id']}"
                            if setting:

                                for tag in size:
                                    sett = setting.filter(size = tag.pk).first()
                                    filtered = filtered_data
                                    if sett:
                                        filtered = filtered_data.filter(size = tag.pk).aggregate(
                                            pcs=Coalesce(Sum('tag_pcs'), Value(0,output_field=PositiveIntegerField())),
                                            wt=Coalesce(Sum('tag_gwt'), Value(0,output_field=DecimalField())),
                                        )
                                                                                             
                                        data.update({
                                            "temp_name" : temp_name,
                                            "show_cart_button":True,
                                            f"{temp_name}_{weight.id_weight_range}_{tag.id_size}_pcs" :filtered['pcs'] ,
                                            f"{temp_name}_{weight.id_weight_range}_{tag.id_size}_wt" :filtered['wt'],
                                            f"{temp_name}_{weight.id_weight_range}_{tag.id_size}_min_pcs" :sett.min_pcs , 
                                            f"{temp_name}_{weight.id_weight_range}_{tag.id_size}_max_pcs" :sett.max_pcs , 
                                        })


                elif(reorder_based_on == 1):

                    if(sub_design_req == 1):
                        settings = reorder_settings.filter(branch = data['current_branch'],product = product,design = data['tag_design_id'],sub_design = data['tag_sub_design_id'])
                        temp_name = f"{product_id}_{data['tag_design_id']}_{data['tag_sub_design_id']}"

                    else:
                        settings = reorder_settings.filter(branch = data['current_branch'],product = product,design = data['tag_design_id'])
                        temp_name = f"{product_id}_{data['tag_design_id']}"


                    if(weight_range and settings):
                        
                        for weight in weight_range:
                            setting = settings.filter(weight_range = weight.pk).first()
                            filtered_data = total
                            if(sub_design_req == 1):
                                filtered_data = total.filter(tag_current_branch = data['current_branch'],tag_design_id = data['tag_design_id'],tag_sub_design_id = data['tag_sub_design_id'],tag_gwt__gte = weight.from_weight ,tag_gwt__lte = weight.to_weight)
                                temp_name = f"{product_id}_{data['tag_design_id']}_{data['tag_sub_design_id']}"

                            else:
                                filtered_data = total.filter(tag_current_branch = data['current_branch'],tag_design_id = data['tag_design_id'],tag_gwt__gte = weight.from_weight ,tag_gwt__lte = weight.to_weight)
                                temp_name = f"{product_id}_{data['tag_design_id']}"

  
                            filtered_data = filtered_data.aggregate(
                                pcs=Coalesce(Sum('tag_pcs'), Value(0,output_field=PositiveIntegerField())),
                                wt=Coalesce(Sum('tag_gwt'), Value(0,output_field=DecimalField())),
                            )
                            if(setting):                                                       
                                data.update({
                                    "temp_name" : temp_name,
                                    "show_cart_button":True,
                                    f"{temp_name}_{weight.id_weight_range}_pcs" :filtered_data['pcs'] ,
                                    f"{temp_name}_{weight.id_weight_range}_wt" :filtered_data['wt'] ,
                                    f"{temp_name}_{weight.id_weight_range}_min_pcs" :setting.min_pcs , 
                                    f"{temp_name}_{weight.id_weight_range}_max_pcs" :setting.max_pcs , 
                                })


                elif(reorder_based_on == 2):
                    filtered_data = total
                    if(sub_design_req == 1):
                        settings = reorder_settings.filter(branch = data['current_branch'],product = product,design = data['tag_design_id'],sub_design = data['tag_sub_design_id'])
                        temp_name = f"{product_id}_{data['tag_design_id']}_{data['tag_sub_design_id']}"
                        filtered_data = total.filter(tag_current_branch = data['current_branch'],tag_design_id = data['tag_design_id'],tag_sub_design_id = data['tag_sub_design_id'])

                    else:
                        settings = reorder_settings.filter(branch = data['current_branch'],product = product,design = data['tag_design_id'])
                        temp_name = f"{product_id}_{data['tag_design_id']}"
                        filtered_data = total.filter(tag_current_branch = data['current_branch'],tag_design_id = data['tag_design_id'])

                    for tag in size:
                        filtered = filtered_data
                        setting = settings.filter(size = tag.pk).first()
                        filtered = filtered.filter(size = tag.pk).aggregate(
                            pcs=Coalesce(Sum('tag_pcs'), Value(0,output_field=PositiveIntegerField())),
                            wt=Coalesce(Sum('tag_gwt'), Value(0,output_field=DecimalField())),
                        )
                        if(setting):                                                       
                            data.update({
                                "temp_name" : temp_name,
                                "show_cart_button":True,
                                f"{temp_name}_{tag.id_size}_pcs" :filtered['pcs'] ,
                                f"{temp_name}_{tag.id_size}_wt" :filtered['wt'],
                                f"{temp_name}_{tag.id_size}_min_pcs" :setting.min_pcs , 
                                f"{temp_name}_{tag.id_size}_max_pcs" :setting.max_pcs ,  
                            })

            response_data = {}
            for data in result:
                response_data.setdefault(data['branch_name'], []).append(data)

            return Response({"data": response_data,"column": column,"reorder_based_on": reorder_based_on,"is_sub_design_req":sub_design_req}, status=status.HTTP_200_OK)    
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)



class Above2LReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        id_branch = ",".join(map(str, id_branch))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            bill_setting_type_filter = ''
            if bill_setting_type == 1:
                bill_setting_type_filter = 'and inv.setting_bill_type = 1'
            elif bill_setting_type == 0:
                bill_setting_type_filter = 'and inv.setting_bill_type = 0'
            queryset = ErpInvoice.objects.raw( F"""Select inv.* FROM erp_invoice inv
                    LEFT JOIN erp_invoice_payment_details pay ON pay.invoice_bill_id_id = inv.erp_invoice_id and pay.payment_mode_id = 1 and pay.payment_amount >= 200000 and pay.payment_type = 1
                  WHere inv.invoice_status = 1 and pay.invoice_bill_id_id IS NOT NULL
                  and inv.id_branch_id in ({id_branch})
                  {bill_setting_type_filter}
                  AND inv.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                  Group By inv.erp_invoice_id""")

            paginator, page = pagination.paginate_queryset(queryset, request,None,ABOVE2L_REPORT)

            data = ErpInvoiceSerializer(page,many=True,context={'invoice_no':True}).data

            response_data = []

            for item, instance in zip(data, queryset):

                # inv_queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id = instance.erp_invoice_id).values("invoice_bill_id").annotate( 
                #             taxable=Sum('taxable_amount'),
                #             tax=Sum('tax_amount'),
                #             cgst=Sum('cgst_cost'),
                #             sgst=Sum('sgst_cost'),
                #             igst=Sum('igst_cost'),
                #             cost=Sum('item_cost'),
                #             ).values(
                #                 'invoice_bill_id',
                #                 'taxable',
                #                 'tax', 
                #                 'cgst',
                #                 'sgst',
                #                 'igst',
                #                 'cost',
                #             ).get()
                # invsales = dict(inv_queryset)


                response_data.append({
                    **item,
                    "invoice_no" : item['inv_no']['invoice_no']
                })
            columns = get_reports_columns_template(request.user.pk,ABOVE2L_REPORT,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class EmpIncentiveReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = IncentiveTransactions.objects.filter(sale_item__invoice_bill_id__invoice_status = 1)

            if(id_branch):
                queryset  = queryset.filter(sale_item__invoice_bill_id__id_branch__in = id_branch)


            if from_date and to_date:
                queryset = queryset.filter(transaction_date__range=[from_date, to_date])


            paginator, page = pagination.paginate_queryset(queryset, request,None,EMP_INCENTIVE_REPORT)

            data = IncentiveTransactionsSerializer(page,many=True).data

            print(data)


            response_data=[]

            for item, instance in zip(data, queryset):

                data = ErpInvoiceSalesDetailsSerializer(instance.sale_item).data

                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.sale_item.invoice_bill_id.erp_invoice_id)

                if inv_queryset.setting_bill_type != bill_setting_type and bill_setting_type != 2:
                    continue

                inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                 
                inv_data = get_invoice_no(inv_serializer)

                emp_name = instance.employee.firstname
                #purity = instance.purity_id.purity if instance.tag_purity_id else None
                tag_tax_grp = instance.sale_item.tax_group_id.tgi_tgrpcode.tgrp_name if instance.sale_item.tax_group_id else None
                mc_type_display = instance.sale_item.get_mc_type_display()
                # tag_calculation_type_name = instance.sale_item.calculation_type.name if instance.sale_item.calculation_type else None
                #item['tag_purity'] = purity
                item['tax_grp'] = tag_tax_grp
                item['mc_type_name'] = mc_type_display
                item['calculation_type_name'] = ""

                response_data.append({
                    **inv_serializer,
                    'invoice_date': format_date(inv_serializer['invoice_date']),
                    **data,
                    **item,
                    **inv_data,
                    "emp_name":emp_name,
                    'item_type': dict(ITEM_TYPE_CHOICES).get( instance.sale_item.item_type, ''),
                    'tag_code': instance.sale_item.tag_id.tag_code if instance.sale_item.tag_id else None,
                    "incentive_type": dict(IncentiveSettings.TYPE_CHOICES).get(instance.incentive.incentive_type, ''), 
                    "calculation_method": dict(IncentiveSettings.CALCULATION_METHOD_CHOICES).get(instance.incentive.calculation_method, ''),
                    "employee_role": dict(IncentiveTransactions.EMP_ROLES_CHOICES).get(instance.employee_role, ''), 
                })
            columns = get_reports_columns_template(request.user.pk,EMP_INCENTIVE_REPORT,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'groupingColumns': ["emp_name"],
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class SearchCustomerHistory(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        instance = {}
        id_customer = request.data['id_customer']
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        customer = Customers.objects.filter(id_customer=id_customer).first()
        customer_serializer = CustomerSerializer(customer, context={"request":request})
        if (CustomerAddress.objects.filter(customer = customer.pk).exists()):
            customer_address = CustomerAddress.objects.get(customer = customer.pk)
            customer_address_serializer = CustomerAddressSerializer(customer_address)
            address1 = customer_address.line1 if customer_address.line1 != None else ""
            address2 = customer_address.line2 if customer_address.line2 != None else ""
            address3 = customer_address.line3 if customer_address.line3 != None else ""
            address = f"{address1} {address2} {address3}".strip()
            # address.update({"state_name":State.objects.get(id_state=customer_address_serializer.data['state']).name})
            instance.update({"address":address})
        else:
            instance.update({"address":None})
            
        ##Chit Accounts
        chit_accounts = []
        if(SchemeAccount.objects.filter(id_customer=customer.pk, is_closed=False).exists()):
            scheme_account_query = SchemeAccount.objects.filter(id_customer=customer.pk, is_closed=False)
            scheme_account_serializer = SchemeAccountSerializer(scheme_account_query, many=True)
            for account_data in scheme_account_serializer.data:
                account_instance = {}
                branch_obj = Branch.objects.get(id_branch=account_data['id_branch'])
                scheme_obj = Scheme.objects.get(scheme_id=account_data['acc_scheme_id'])
                scheme_payment_details   = SchemeAccountPaidDetails()
                payment_details        = scheme_payment_details.get_scheme_account_paid_details(account_data['id_scheme_account'])
                account_instance.update({
                    'pk_id'             :account_data['id_scheme_account'],
                    'id_scheme_account'  :account_data['id_scheme_account'],
                    'account_name'       :account_data['account_name'],
                    'start_date'         :account_data['start_date'],
                    'scheme_acc_number'  :account_data['scheme_acc_number'] if (account_data['scheme_acc_number'] != None) else None,
                    'branch_name'        :branch_obj.name,
                    'scheme_name'        :scheme_obj.scheme_name,
                    'customer_name'      :customer.firstname,
                    # 'mobile'             :customer.mobile,
                    # 'paid_installments'  :payment_details['tot_paid_installment'],
                    # 'total_paid_amount'  :payment_details['total_paid_amount'],
                    # 'total_paid_weight'  :payment_details['total_paid_weight'],
                    'paid_installments'  :account_data['total_paid_ins'],
                    'total_paid_amount'  :Decimal(payment_details['total_paid_amount']) + Decimal(account_data['opening_balance_amount']),
                    'total_paid_weight'  :Decimal(payment_details['total_paid_weight']) + Decimal(account_data['opening_balance_weight']),
                })
                if (account_instance not in chit_accounts):
                    chit_accounts.append(account_instance)
            scheme_account_count = len(scheme_account_serializer.data)
            instance.update({"active_accounts":scheme_account_count})
        else:
            instance.update({"active_accounts":0})
        instance.update({"cus_name":customer.firstname,"mobile":customer.mobile, 
                         "cus_img": customer_serializer.data['cus_img'],
                         "chit_accounts":chit_accounts})
        
        ##sales
        invoice_details = ErpInvoice.objects.filter(id_customer=customer.pk)
        if  bill_setting_type == 1:
            invoice_details = invoice_details.filter(setting_bill_type = 1)
        elif bill_setting_type == 0: 
            invoice_details = invoice_details.filter(setting_bill_type = 0)
        invoice_details_serializer = ErpInvoiceSerializer(invoice_details, many=True)
        for invoice_det in invoice_details_serializer.data:
            invoice_det.update({"invoice_date":format_date(invoice_det['invoice_date']),
                                "due_date":format_date(invoice_det['due_date']),
                                })
        instance.update({"sales":invoice_details_serializer.data})
        
        ##Purchase
        purchase = []
        for invoice in invoice_details_serializer.data:
            purchase_details = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id=invoice['erp_invoice_id'])
            purchase_details_serializer = ErpInvoiceOldMetalDetailsSerializer(purchase_details, many=True)
            for pur_detail in purchase_details_serializer.data:
                if pur_detail not in purchase:
                    purchase.append(pur_detail)
        instance.update({"purchase":purchase})
        
        ##Orders
        order_output = []
        orders = ERPOrder.objects.filter(customer=customer.pk)
        orders_serializer = ErpOrdersSerializer(orders, many=True)
        for order in orders_serializer.data:
            detail_query = ERPOrderDetails.objects.filter(order=order['order_id'])
            detail_serializer = ErpOrdersDetailSerializer(detail_query, many=True)
            for details in detail_serializer.data:
                ord_instance = {}
                if(ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists()):
                    order_image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id']).earliest('det_order_img_id')
                    order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                    ord_instance.update({"image":order_image, "image_text":order['order_no'][0]})
                else:
                    ord_instance.update({"image":None, "image_text":order['order_no'][0]})
                # customer = Customers.objects.get(id_customer=order['customer'])
                order_status = ERPOrderStatus.objects.get(id=details['order_status'])
                if(details['product']!= None):
                    prod_obj = Product.objects.filter(pro_id=details['product']).first()
                    ord_instance.update({'product':prod_obj.product_name})
                else:
                    ord_instance.update({'product':None})
                ord_instance.update({"order_no":order['order_no'], "branch_name": order['branch_name'], "order_date":order['order_date'], "customer":customer.firstname,
                                 "mobile":customer.mobile, "order_status":details['order_status'],
                                 "design":details.get('design_name'), "sub_design":details.get('sub_design_name'), "pieces":details['pieces'],
                                 "gross_wt":details['gross_wt'], "less_wt":details['less_wt'], "net_wt":details['net_wt'],
                                 "colour":order_status.colour, "name":order_status.name,"cancel_reason":'','detail_id':details['detail_id'],
                                 'customer_order_type':'Customized Order' if details['is_reserved_item']==0 else 'Reserve Order'})
                if(ErpJobOrderDetails.objects.filter(order_detail=details['detail_id']).exists()):
                    job_order_query = ErpJobOrder.objects.all()
                    job_order_serializer = ErpJobOrderSerializer(job_order_query, many=True)
                    
                    for job_order in job_order_serializer.data: 
                        job_detail_query = ErpJobOrderDetails.objects.filter(job_order=job_order['id_job_order'], order_detail=details['detail_id'])
                        job_detail_serializer = ErpJobOrderDetailSerializer(job_detail_query, many=True)
                        for job_detail in job_detail_serializer.data:
                            job_order = ErpJobOrder.objects.get(id_job_order=job_detail['job_order'])
                            if(job_order.supplier):
                                ord_instance.update({"karigar":job_order.supplier.supplier_name, "karigar_id":job_order.supplier.pk})
                            else:
                                ord_instance.update({"karigar":None})
                else:
                    ord_instance.update({"karigar":None})
                    
                if(details['erp_tag']):
                    tag_query = ErpTagging.objects.get(tag_id=details['erp_tag'])
                    ord_instance['tag_code'] = tag_query.tag_code
                    ord_instance['karigar'] = tag_query.tag_lot_inward_details.lot_no.id_supplier.supplier_name
                else :
                    ord_instance.update({"karigar":None})
                if ord_instance not in order_output:
                    order_output.append(ord_instance)
        instance.update({"orders":order_output})
        
        ##credit
        credit_queryset = ErpIssueReceipt.objects.filter(customer=customer.pk, issue_type=1, bill_status=1)
        if  bill_setting_type == 1:
            credit_queryset = credit_queryset.filter(setting_bill_type = 1)
        elif bill_setting_type == 0: 
            credit_queryset = credit_queryset.filter(setting_bill_type = 0)
        credit_serializer = ErpIssueReceiptSerializer(credit_queryset, many=True).data
        credit_data = []
        outstanding_amount = 0  # Initialize outstanding amount
        for credits in credit_serializer:
            received_amount = 0
            issued_amount = float(credits['amount'])
            balance_amount = 0
            col = ErpReceiptCreditCollection.objects.filter(issue=credits['id'], receipt__bill_status=1)
            col_data = ErpReceiptCreditCollectionSerializer(col, many=True).data
            for collection in col_data:
                received_amount += float(collection['received_amount']) + float(collection['discount_amount'])
            balance_amount = issued_amount - received_amount
            if balance_amount > 0:
                outstanding_amount += balance_amount  # Add balance to outstanding amount
                credits.update({'issued_amount': issued_amount, 'balance_amount': balance_amount, 
                                'received_amount': received_amount, 'discount': 0, 'amount': 0,
                                "bill_date":format_date(credits['bill_date'])})
                credit_data.append(credits)
        instance.update({"credits": credit_data})
        
        ##advance in hand
        adv_queryset = ErpIssueReceipt.objects.filter(customer=customer.pk, receipt_type__in=[1, 2, 3, 4], bill_status=1)
        if  bill_setting_type == 1:
            adv_queryset = adv_queryset.filter(setting_bill_type = 1)
        elif bill_setting_type == 0: 
            adv_queryset = adv_queryset.filter(setting_bill_type = 0)
        adv_serializered_data = ErpIssueReceiptSerializer(adv_queryset, many=True).data
        advance_in_hand = 0  # Initialize advance in hand
        for adv_data in adv_serializered_data:
            refunded_amount = 0
            adjusted_amount = 0
            advance_amount = float(adv_data['amount'])
            balance_amount = 0
            refund = ErpReceiptRefund.objects.filter(receipt=adv_data['id'], issue__bill_status=1)
            refund_data = ErpReceiptRefundSerializer(refund, many=True).data
            for ref in refund_data:
                refunded_amount += float(ref['refund_amount'])
            adjusted = ErpReceiptAdvanceAdj.objects.filter(receipt=adv_data['id'], invoice_bill_id__invoice_status=1)
            adjusted_data = ErpReceiptAdvanceAdjSerializer(adjusted, many=True).data
            for adj in adjusted_data:
                adjusted_amount += float(adj['adj_amount'])
            twod_adjusted = ErpAdvanceAdj.objects.filter(receipt=adv_data['id'], invoice_bill_id__invoice_status=1)
            twod_adjusted_data = ErpAdvanceAdjSerializer(twod_adjusted, many=True).data
            for adj in twod_adjusted_data:
                adjusted_amount += float(adj['adj_amount'])
            balance_amount = advance_amount - refunded_amount - adjusted_amount
            advance_in_hand += balance_amount  # Add balance to advance in hand
            # if(balance_amount > 0):
            #     new_data = {'bill_no':data['bill_no'],'id_issue_receipt':data['id'],'advance_amount':advance_amount,'balance_amount':balance_amount,'refunded_amount':refunded_amount,'adjusted_amount':adjusted_amount,'discount':0,'amount':0, }
            #     response_data.append(new_data)
        instance.update({
            "advance_in_hand": advance_in_hand,
            "outstanding_amount": outstanding_amount,
        })
        return Response(instance, status=status.HTTP_200_OK)
        

class SearchSupplierHistory(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_supplier = request.data.get('supplier')
        code_format = RetailSettings.objects.get(name='purchase_entry_code_format').value

        lists = ErpPurchaseEntry.objects.select_related('id_supplier', 'id_branch').annotate(
            total_gross_wt=Sum('purchase_details__gross_wt'),
            total_net_wt=Sum('purchase_details__net_wt'),
            total_stn_wt=Sum('purchase_details__stone_wt'),
            total_dia_wt=Sum('purchase_details__dia_wt')
        ).values(
            'id_purchase_entry',
            'ref_no', 
            'id_branch__short_name',
            'fin_year__fin_year_code',
            'id_purchase_entry',
            'total_gross_wt', 
            'total_net_wt',
            'total_stn_wt',
            'total_dia_wt',
            'is_approved', 
            'entry_date',
            'id_supplier__supplier_name',
            'id_branch__name',
            'is_cancelled'
        )
        if id_supplier:
            lists = lists.filter(id_supplier=id_supplier)
         
        for purchase in lists:
            code = (code_format
                    .replace('@branch_code@',  purchase['id_branch__short_name'])
                    .replace('@code@', purchase['ref_no'])
                    .replace('@fy_code@', purchase['fin_year__fin_year_code']))
            purchase['is_active'] = purchase['is_approved']
            purchase['ref_code'] = code
            purchase['status_name'] = ('UnApproved' if purchase['is_approved']==0 else 'Approved') if purchase['is_cancelled']==False else 'Cancelled'
            purchase['colour'] = ('warning' if purchase['is_approved']==0 else 'success') if purchase['is_cancelled']==False else 'danger'
            purchase['entry_date'] = format_date(purchase['entry_date'])
            purchase['total_gross_wt'] = format(purchase['total_gross_wt'], '.3f')
            purchase['total_net_wt'] = format(purchase['total_net_wt'], '.3f')
            purchase['total_stn_wt'] = format(purchase['total_stn_wt'], '.3f')
            purchase['total_dia_wt'] = format(purchase['total_dia_wt'], '.3f')
        return Response(lists, status=status.HTTP_200_OK)
    

class SearchTagHistory(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        tag_code = request.data.get('tag_code')
        tag_huid = request.data.get('tag_huid') 
        try: 
            if tag_code:
                queryset = ErpTagging.objects.filter(tag_code=tag_code).first()
            elif tag_huid:
                queryset = ErpTagging.objects.filter(tag_huid=tag_huid).first()
            else:
                return Response({"message": "Tag Code or Tag HUID must be provided"}, status=status.HTTP_400_BAD_REQUEST)

            if not queryset:
                return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
            
            # if tag_code :
            # queryset = ErpTagging.objects.filter(tag_code=tag_code).get() 
            # else:
            #     queryset = ErpTagging.objects.filter(old_tag_code=old_tag_code)
            #queryset = queryset.filter(tag_status=1,order_tag__detail_id__isnull=True).get()
            serializer = ErpTaggingSerializer(queryset)
            output = serializer.data
            if(queryset.tag_status==2):
                invc_obj = ErpInvoiceSalesDetails.objects.filter(tag_id=queryset.pk).first()
                if(invc_obj and invc_obj.invoice_bill_id.invoice_status==1):
                    tag_age = (invc_obj.invoice_bill_id.invoice_date - queryset.tag_date).days
                else:
                    tag_age = (date.today() - queryset.tag_date).days
                output.update({'tag_age':(str(tag_age) + ' days')})
            if(queryset.tag_status!=2):
                tag_age = (date.today() - queryset.tag_date).days
                output.update({'tag_age':(str(tag_age) + ' days')})
            output.update({'tagged_date':format_date(queryset.tag_date)})
            if queryset.tag_lot_inward_details:
                lot = ErpLotInwardDetails.objects.filter(id_lot_inward_detail=queryset.tag_lot_inward_details.pk).get()
                output.update({"item_type":0, "lot_code":lot.lot_no.lot_code, "supplier_name":lot.lot_no.id_supplier.supplier_name,
                               "tag_current_status":queryset.tag_status.name, "purity":queryset.tag_purity_id.purity})
            else:
                output.update({"item_type":1,"lot_code":'', "supplier_name": queryset.id_supplier.supplier_name if queryset.id_supplier else None,
                               "tag_current_status":queryset.tag_status.name, "purity":queryset.tag_purity_id.purity})
            if(queryset.size != None):
                output.update({"size_name": queryset.size.name})
            if(ErpTaggingImages.objects.filter(erp_tag=queryset.tag_id).exists()):
                preview_images_query = ErpTaggingImages.objects.filter(erp_tag=queryset.tag_id)
                preview_images_serializer = ErpTaggingImagesSerializer(preview_images_query, many=True, context={"request": request})
                for image_data in preview_images_serializer.data:
                    image_data.update({"image":image_data['tag_image']})
                tag_image = ErpTaggingImages.objects.filter(erp_tag=queryset.tag_id).get(is_default=True)
                tag_image_seri = ErpTaggingImagesSerializer(tag_image, context={"request":request})
                output.update({"image":tag_image_seri.data['tag_image'], "image_text":queryset.tag_code[len(queryset.tag_code)-1],
                             "preview_images":preview_images_serializer.data})
            else:
                output.update({"image":None, "image_text":queryset.tag_code, "preview_images":[]})
            # if(ErpTaggingStone.objects.filter(tag_id=queryset.tag_id).exists()):
            #     stone_details_query = ErpTaggingStone.objects.filter(tag_id=queryset.tag_id)
            #     stone_details_serializer = ErpTagStoneSerializer(stone_details_query, many=True)
            tag_log_history = []
            tag_log_queryset = ErpTaggingLogDetails.objects.filter(tag_id=queryset.tag_id)
            tag_log_serializer = ErpTaggingLogSerializer(tag_log_queryset, many=True)
            
            for logs in tag_log_serializer.data:
                logs.update({"log_date":format_date(logs['date'])})
                
                if(logs['transaction_type']==1):
                    tag_obj = ErpTagging.objects.filter(tag_id=logs['ref_id']).first()
                    logs.update({"transaction_type":'Tagging', 'ref_no':  tag_obj.tag_code if tag_obj else '' })
                    
                elif(logs['transaction_type']==2):
                    bill_sales_obj = ErpInvoiceSalesDetails.objects.filter(invoice_sale_item_id=logs['ref_id']).first()
                    bill_obj = ErpInvoice.objects.get(erp_invoice_id=bill_sales_obj.invoice_bill_id.pk)
                    inv_serializer = ErpInvoiceSerializer(bill_obj).data
                    inv_data = get_invoice_no(inv_serializer)
                    logs.update({"transaction_type":'Billing', 'ref_no':inv_data['invoice_no']})
                
                elif(logs['transaction_type']==3):
                    branch_trans_detail = ErpTagTransfer.objects.filter(id_tag_transfer=logs['ref_id']).first()
                    logs.update({"transaction_type":'Branch Transfer', 
                                 'ref_no':branch_trans_detail.stock_transfer.trans_code})
                    
                elif(logs['transaction_type']==4):
                    pending_trans = ErpAccountStockProcessDetails.objects.filter(id_details=logs['ref_id']).first()
                    logs.update({"transaction_type":'Pending Transfer', 
                                 'ref_no':pending_trans.account_stock.ref_no})
                    
                elif(logs['transaction_type']==5):
                    metal_issue_obj = ErpSupplierMetalIssueDetails.objects.filter(id_metal_issue=logs['ref_id']).first()
                    logs.update({"transaction_type":'Metal Issue', 
                                 'ref_no':metal_issue_obj.issue.ref_no})
                    
                elif(logs['transaction_type']==9):
                    logs.update({"transaction_type":'Sales Outward', 
                                 'ref_no':None})
                    
                elif(logs['transaction_type']==6):
                    purchase_return_obj = ErpPurchaseReturnDetails.objects.filter(id_purchase_return_det=logs['ref_id']).first()
                    logs.update({"transaction_type":'Purchase Return', 
                                 'ref_no':purchase_return_obj.purchase_return.ref_no})
                                        
                if logs not in tag_log_history:
                    tag_log_history.append(logs)
            output.update({"tag_log_history":tag_log_history})
            return Response(output, status=status.HTTP_200_OK)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
        

class SupplierBalanceReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_supplier = request.data.get('id_supplier',None)
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_metal = request.data.get('id_metal',1)
        date = to_date
        return_data = []
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_metal:
            paginator, page = pagination.paginate_queryset([], request,None,SUPPLIER_BALANCE_REPORT)
            columns = get_reports_columns_template(request.user.pk,SUPPLIER_BALANCE_REPORT,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            context={"message": "Metal is required",'columns':columns, 'filters':filters_copy,'actions':ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':True}
            return pagination.paginated_response([],context)                
        try:

            result = get_supplier_balance(id_metal,date)
            for item in result:
                item.update({
                    "supplier_balance_amount": (item['balance_amount']),
                    "supplier_balance_weight": (item['balance_weight']),
                    "amount": f"{abs(item['balance_amount'])} {'CR' if float(item['balance_amount']) > 0 else 'DR'}",
                    "weight": f"{abs(item['balance_weight'])} {'CR' if float(item['balance_weight']) > 0 else 'DR'}",
                })


            paginator, page = pagination.paginate_queryset(result, request,None,SUPPLIER_BALANCE_REPORT)
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True

            context={'columns':SUPPLIER_BALANCE_REPORT, 'filters':filters_copy,'actions':ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number,'is_filter_req':True}
            return pagination.paginated_response(result,context)                
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

def get_supplier_balance(id_metal,date):
        query =  f""" SELECT
                m.id_metal,
                ent.id_supplier,
                ent.supplier_name,
                m.metal_name,
                ent.mobile_no,
                ent.short_code,
                COALESCE(COALESCE(recv.pure_wt, 0) + COALESCE(opn.pure_wt,0) - ( COALESCE(purchase_return.purchase_return_wt,0) + COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) ), 0) AS balance_weight,
                COALESCE(COALESCE(recv.other_amount, 0) + COALESCE(rate_cut.paid_amount, 0) + COALESCE(opn.purchase_cost,0) - COALESCE(payment.paid_amount, 0), 0) AS balance_amount
            FROM
                erp_supplier ent
            LEFT JOIN  metal m ON m.id_metal = {id_metal} 
            LEFT JOIN(
                SELECT COALESCE(SUM(pur.pieces), 0) AS pieces,
                COALESCE(SUM(pur.pure_wt), 0) AS pure_wt,
                COALESCE(SUM(pur.purchase_cost), 0) AS purchase_cost,
                (COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0)) as other_amount,
                pur.purchase_entry_id,
                pro.id_metal_id,
                ent.id_supplier_id
            FROM
                erp_purchase_item_details pur 
            LEFT JOIN erp_purchase_entry ent ON
                ent.id_purchase_entry = pur.purchase_entry_id
            LEFT JOIN erp_product pro ON
                pro.pro_id = pur.id_product_id
            LEFT JOIN(
                    SELECT
                        ent.id_supplier_id,
                        pro.id_metal_id,
                        item.purchase_entry_id,
                        COALESCE(SUM(charges.charges_amount), 0) AS charges_amount
                    FROM erp_purchase_item_charges_details charges
                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = charges.purchase_entry_detail_id
                    LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                    LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                    where ent.is_cancelled = 0
                        and pro.id_metal_id = {id_metal}
                    GROUP BY ent.id_supplier_id
            ) charges ON charges.id_supplier_id = ent.id_supplier_id

            LEFT JOIN(
                    SELECT
                        ent.id_supplier_id,
                        pro.id_metal_id,
                        item.purchase_entry_id,
                        COALESCE(SUM(stn.pur_stn_cost), 0) AS stone_amount
                    FROM erp_purchase_stone_details stn
                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = stn.purchase_entry_detail_id
                    LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                    LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                    where ent.is_cancelled = 0
                        and pro.id_metal_id = {id_metal}
                    GROUP BY ent.id_supplier_id
            ) stn ON stn.id_supplier_id = ent.id_supplier_id 
    
            LEFT JOIN(
                    SELECT
                        ent.id_supplier_id,
                        pro.id_metal_id,
                        item.purchase_entry_id,
                        COALESCE(SUM(other_metal.other_metal_cost), 0) AS other_metal_cost
                    FROM erp_purchase_other_metal other_metal
                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = other_metal.purchase_entry_detail_id
                    LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                    LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                    where ent.is_cancelled = 0
                        and pro.id_metal_id = {id_metal}
                    GROUP BY ent.id_supplier_id
            ) other_metal ON other_metal.id_supplier_id = ent.id_supplier_id 
            WHERE
                ent.is_cancelled = 0 and                      
                DATE_FORMAT(ent.entry_date, '%Y-%m-%d') <= '{date}' 
                and pro.id_metal_id = {id_metal} 
                
            GROUP BY
                ent.id_supplier_id
        ) recv
        ON
            recv.id_supplier_id = ent.id_supplier
        LEFT JOIN(
            SELECT
                COALESCE(SUM(pur.weight), 0) AS pure_wt,
                COALESCE(SUM(pur.amount), 0) AS purchase_cost,
                pur.id_metal_id,
                pur.id_supplier_id
            FROM
                erp_purchase_supplier_opening pur 
            WHERE                   
                pur.id_metal_id = {id_metal} 
            GROUP BY
                pur.id_supplier_id
        ) opn
        ON
            opn.id_supplier_id = ent.id_supplier
        LEFT JOIN(
                SELECT
                    sp.id_supplier_id,
                    COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                FROM
                    erp_supplier_payment_details sp
                LEFT JOIN erp_supplier_payment pay ON
                    pay.id_purchase_payment = sp.purchase_payment_id
                LEFT JOIN erp_purchase_entry ent ON
                        ent.id_purchase_entry = sp.ref_id
                WHERE
                    sp.metal_id = {id_metal}
                    AND DATE_FORMAT(pay.entry_date, '%Y-%m-%d') <= '{date}'
                GROUP BY
                    sp.id_supplier_id
        ) payment
        ON
            payment.id_supplier_id = ent.id_supplier
        LEFT JOIN(
            SELECT rc.id_supplier_id,
                COALESCE(SUM(rc.amount), 0) AS paid_amount,
                COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
            FROM
                erp_rate_cut rc
            WHERE  rc.id_metal_id = {id_metal}
            AND DATE_FORMAT(rc.entry_date, '%Y-%m-%d') <= '{date}'
            GROUP BY
                rc.id_supplier_id

        ) rate_cut
        ON
            rate_cut.id_supplier_id = ent.id_supplier
        LEFT JOIN(
                SELECT
                    d.id_supplier_id,
                    COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                    COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                FROM
                    erp_supplier_metal_issue_details mi
                LEFT JOIN erp_product pro ON
                    pro.pro_id = mi.id_product_id
                LEFT JOIN erp_supplier_metal_issue d ON
                    d.id_issue = mi.issue_id
                LEFT JOIN erp_purchase_entry ent ON
                    ent.id_purchase_entry = mi.purchase_entry_id
                WHERE
                    d.type = 1  and pro.id_metal_id = {id_metal}
                    AND DATE_FORMAT(d.entry_date, '%Y-%m-%d') <= '{date}'
                GROUP BY
                    d.id_supplier_id
        ) metal_issue
        ON
            metal_issue.id_supplier_id = ent.id_supplier

        LEFT JOIN (
        SELECT
            ret.supplier_id,
            COALESCE(SUM(pur_ret.pure_wt), 0) AS purchase_return_wt
        FROM `erp_purchase_return_details` pur_ret
        LEFT JOIN erp_purchase_return ret ON
            ret.id_purchase_return = pur_ret.purchase_return_id
        LEFT JOIN erp_product pro ON
            pro.pro_id = pur_ret.id_product_id
        WHERE
            ret.status = 1 and pro.id_metal_id = {id_metal}
            AND DATE_FORMAT(ret.entry_date, '%Y-%m-%d') <= '{date}'
        GROUP BY  ret.supplier_id

        ) purchase_return
        ON
            purchase_return.supplier_id = ent.id_supplier
        WHERE
            1
        GROUP BY
            ent.id_supplier
            """
        result = generate_query_result(query)
        return result
class PaymentDevicesReportsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
            id_branch = request.data.get('branch')
            from_date = request.data.get('fromDate')
            to_date = request.data.get('toDate')
            bank = request.data.get('bank')
            bill_setting_type = int(request.data.get('bill_setting_type',2))
            if not from_date or not to_date:
                return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)

            response_data=[]

            sales_queryset = ErpInvoicePaymentModeDetail.objects.filter(id_pay_device__isnull = False,invoice_bill_id__invoice_status = 1,invoice_bill_id__invoice_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                sales_queryset = sales_queryset.filter(invoice_bill_id__setting_bill_type = 0)

            if(id_branch):
                sales_queryset  = sales_queryset.filter(invoice_bill_id__id_branch__in = id_branch)
            
            if from_date and to_date:
                sales_queryset = sales_queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

            data = ErpInvoicePaymentModeDetailSerializer(sales_queryset,many=True).data

            for item, instance in zip(data, sales_queryset):
                bill_no=get_bill_no(item['invoice_bill_id'])
                response_data.append({
                    "ref_no": bill_no,
                    "payment_mode": item['mode_name'],
                    "payment_type": item['payment_type'],
                    "payment_amount": item['payment_amount'] ,
                     "payment_ref_number": item['payment_ref_number'] ,
                    "ref_id":item['invoice_pay_id'] ,
                    "device_name":instance.id_pay_device.device_name,
                    "type":'Sales Invoice',
                    "date": format_date(instance.invoice_bill_id.invoice_date),
                })

            issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt__bill_status = 1,issue_receipt__bill_date__range=[from_date, to_date],pay_device__isnull= False)
            if(id_branch):
                issue_payment_queryset  = issue_payment_queryset.filter(issue_receipt__branch__in = id_branch)

            if  bill_setting_type == 1:
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 1)
            elif bill_setting_type == 0: 
                issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type = 0)

            if(bank):
                issue_payment_queryset  = issue_payment_queryset.filter(bank = bank)

            issue_payment = ErpIssueReceiptPaymentDetailsSerializer(issue_payment_queryset,many=True).data

            for item, instance in zip(issue_payment, issue_payment_queryset):
                response_data.append({
                    "ref_no": instance.issue_receipt.bill_no,
                    "payment_mode": item['mode_name'],
                    "payment_type": item['type'],
                    "trans_name":f" {instance.issue_receipt.bill_no} {item['mode_name']} PAYMENT { 'CREDITED TO' if item['type'] == 1 else 'DEBITED TO' } {item['bank_name']} - {item['acc_number']}",
                    "payment_amount": item['payment_amount'] ,
                    "device_name":instance.pay_device.device_name,
                    "ref_id":item['issue_receipt'] ,
                    "payment_ref_number": item.get('ref_no') ,
                     "type":'Issue Receipt',
                    "date": format_date(instance.issue_receipt.bill_date),
                })

            supplier_payment_queryset = ErpSupplierPaymentModeDetail.objects.filter(id_pay_device__isnull= False,purchase_payment__entry_date__range=[from_date, to_date])

            if(id_branch):
                supplier_payment_queryset  = supplier_payment_queryset.filter(purchase_payment__cash_from_branch__in = id_branch)

            if(bank):
                supplier_payment_queryset  = supplier_payment_queryset.filter(id_bank = bank)

            supplier_payment = ErpSupplierPaymentModeDetailSerializer(supplier_payment_queryset,many=True).data

            for item, instance in zip(supplier_payment, supplier_payment_queryset):
                response_data.append({
                    "ref_no": instance.purchase_payment.ref_no,
                    "payment_mode": item['mode_name'],
                    "payment_type": item['payment_type'],
                    "trans_name":f" {instance.purchase_payment.ref_no} {item['mode_name']} PAYMENT { 'CREDITED TO' if item['payment_type'] == 1 else 'DEBITED TO' } {item['bank_name']} - {item['acc_number']}",
                    "payment_amount": item['payment_amount'] ,
                    "device_name":instance.id_pay_device.device_name,
                    "payment_ref_number": item['payment_ref_number'] ,
                    "ref_id":item['purchase_payment'] ,
                    "type":'Supplier Payment',
                    "date": format_date(instance.purchase_payment.entry_date),
                })
            paginator, page = pagination.paginate_queryset(response_data, request,None,PAYMNET_DEVICE_COLUMN_LIST)
            columns = get_reports_columns_template(request.user.pk,PAYMNET_DEVICE_COLUMN_LIST,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
                'groupingColumns': ["device_name"],

                }
            return pagination.paginated_response(response_data,context) 





class StockAnalysisReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        filter_by = request.data.get('filter_by')
        filter_details = request.data.get('filter_details')
    
        if not filter_by:
            return Response({"message": "Filter BY is required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(filter_details)==0:
            return Response({"message": "Filter Condition is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            today = now().date()
            filters = Q()
            for item in filter_details:
                if int(filter_by)==1:  ##Filter by tag date
                    if item['condition']=='less_than' and item['value1']!='':
                        filters &= Q(tag_date_lgte=today - timedelta(days=int(item['value1'])))
                    if item['condition']=='greater_than' and item['value1']!='':
                        filters &= Q(tag_date__gte=today - timedelta(days=int(item['value1'])))
                    if item['condition']=='between' and item['value1']!='' and item['value2']!='':
                        filters &= Q(tag_date__gte=today - timedelta(days=int(item['value2']))) & \
                        Q(tag_date__lte=today - timedelta(days=int(item['value1'])))
                
                 ##Filter by Gross weight
                if int(filter_by) == 2:
                    if item['condition'] == 'less_than' and item['value1'] != '':
                        filters &= Q(tag_gwt__lt=float(item['value1']))

                    if item['condition'] == 'greater_than' and item['value1'] != '':
                        filters &= Q(tag_gwt__gt=float(item['value1']))

                    if item['condition'] == 'between' and item['value1'] != '' and item['value2'] != '':
                        filters &= Q(tag_gwt__gte=float(item['value1'])) & Q(tag_gwt__lte=float(item['value2']))
                
                ##Filter by Net weight
                if int(filter_by) == 3:
                    if item['condition'] == 'less_than' and item['value1'] != '':
                        filters &= Q(tag_nwt__lt=float(item['value1']))

                    if item['condition'] == 'greater_than' and item['value1'] != '':
                        filters &= Q(tag_nwt__gt=float(item['value1']))

                    if item['condition'] == 'between' and item['value1'] != '' and item['value2'] != '':
                        filters &= Q(tag_nwt__gte=float(item['value1'])) & Q(tag_nwt__lte=float(item['value2']))
                
                ##Filter by MRP Rate
                if int(filter_by) == 4:
                    if item['condition'] == 'less_than' and item['value1'] != '':
                        filters &= Q(tag_sell_rate__lt=float(item['value1']))

                    if item['condition'] == 'greater_than' and item['value1'] != '':
                        filters &= Q(tag_sell_rate__gt=float(item['value1']))

                    if item['condition'] == 'between' and item['value1'] != '' and item['value2'] != '':
                        filters &= Q(tag_sell_rate__gte=float(item['value1'])) & Q(tag_sell_rate__lte=float(item['value2']))
            queryset = ErpTagging.objects.all()
            queryset = queryset.filter(filters,tag_status=1)
            paginator, page = pagination.paginate_queryset(queryset, request,None,STOCK_ANALYSIS_REPORT)
            columns = get_reports_columns_template(request.user.pk,STOCK_ANALYSIS_REPORT,request.data["path_name"])
            serializer = ErpTaggingSerializer(page, many=True)
            for index, data in enumerate(serializer.data):
                data.update({"sno": index+1})
            context={
                'columns':columns,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'actions':'',
                }

            return pagination.paginated_response(serializer.data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
def insert_data_return_id(table_name, params):
    columns = ', '.join(params.keys())
    values = ', '.join([f"%({key})s" for key in params.keys()])    
    query = f"""
        INSERT INTO {table_name} ({columns}) 
        VALUES ({values});
    """
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        inserted_id = cursor.lastrowid  # Get the last inserted ID
        #connection.commit()  # Commit the transaction
    return inserted_id

class ProductLotandTagDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        lot_id = request.data['lot_id']
        lot_details = ErpLotInwardDetails.objects.filter(lot_no=lot_id,status = 0).values('id_product__product_name').annotate(
            total_pieces=Sum('pieces'),
            total_gwt=Sum('gross_wt'),
            total_lwt=Sum('less_wt'),
            total_nwt=Sum('net_wt'),
            total_stn_wt=Sum('stone_wt'),
            total_dia_wt=Sum('dia_wt'),
            tagged_pcs=Sum('tagged_pcs'),
            tagged_gross_wt=Sum('tagged_gross_wt'),
            tagged_less_wt=Sum('tagged_less_wt'),
            tagged_net_wt=Sum('tagged_net_wt'),
            tagged_stone_wt=Sum('tagged_stone_wt'),
            tagged_dia_wt=Sum('tagged_dia_wt')
        )

        # # Get Tag Details grouped by product
        # tag_details = ErpTagging.objects.filter(tag_lot_inward_details__lot_no=lot_id).values('tag_product_id__product_name').annotate(
        #     total_tag_gwt=Sum('tag_gwt'),
        #     total_tag_lwt=Sum('tag_lwt'),
        #     total_tag_nwt=Sum('tag_nwt'),
        #     total_tag_stn_wt=Sum('tag_stn_wt'),
        #     total_tag_dia_wt=Sum('tag_dia_wt')
        # )

        # Convert to dictionary for easier lookup
        # tag_dict = {item['tag_product_id__product_name']: item for item in tag_details}
        final_result = []
        for lot in lot_details:
            product_name = lot['id_product__product_name']
            # tag = tag_dict.get(product_name, {})

            final_result.append({
                'product_name': product_name,
                'lot_pcs': lot['total_pieces'],
                'lot_gwt': lot['total_gwt'],
                'lot_lwt': lot['total_lwt'],
                'lot_nwt': lot['total_nwt'],
                'lot_stn_wt': lot['total_stn_wt'],
                'lot_dia_wt': lot['total_dia_wt'],
                'tag_pcs': lot['tagged_pcs'],
                'tag_gwt': lot['tagged_gross_wt'],
                'tag_lwt': lot['tagged_less_wt'],
                'tag_nwt': lot['tagged_net_wt'],
                'tag_stn_wt': lot['tagged_stone_wt'],
                'tag_dia_wt': lot['tagged_dia_wt'],
                'balance_pcs': lot['total_pieces'] - lot['tagged_pcs'],
                'balance_gwt': lot['total_gwt'] - lot['tagged_gross_wt'],
                'balance_lwt': lot['total_lwt'] - lot['tagged_less_wt'],
                'balance_nwt': lot['total_nwt'] - lot['tagged_net_wt'],
                'balance_stn_wt': lot['total_stn_wt'] - lot['tagged_stone_wt'],
                'balance_dia_wt': lot['total_dia_wt'] - lot['tagged_dia_wt'],
            })
        return Response(final_result, status=status.HTTP_200_OK)
    
class TagDetailsReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate',None)
        to_date = request.data.get('toDate',None)
        product = request.data.get('product',None)
        tag_details = ErpTagging.objects.filter(tag_date__lte=to_date, 
                                                tag_date__gte=from_date)
        if(product is not None):
            tag_details = tag_details.filter(tag_product_id=product).values('tag_product_id__product_name', 'tag_date').annotate(
                total_tag_gwt=Sum('tag_gwt'),
                total_tag_lwt=Sum('tag_lwt'),
                total_tag_nwt=Sum('tag_nwt'),
                total_tag_stn_wt=Sum('tag_stn_wt'),
                total_tag_dia_wt=Sum('tag_dia_wt')
            )
        else:
            tag_details = tag_details.values('tag_product_id__product_name', 'tag_date').annotate(
                total_tag_gwt=Sum('tag_gwt'),
                total_tag_lwt=Sum('tag_lwt'),
                total_tag_nwt=Sum('tag_nwt'),
                total_tag_stn_wt=Sum('tag_stn_wt'),
                total_tag_dia_wt=Sum('tag_dia_wt')
            )
            
        
        final_result = []
        for tag in tag_details:
            product_name = tag['tag_product_id__product_name']
            
            final_result.append({
                'product_name': product_name,
                'date' : format_date(tag['tag_date']),
                'total_tag_gwt': tag['total_tag_gwt'],
                'total_tag_lwt': tag['total_tag_lwt'],
                'total_tag_nwt': tag['total_tag_nwt'],
                'total_tag_stn_wt': tag['total_tag_stn_wt'],
                'total_tag_dia_wt': tag['total_tag_dia_wt'],
            })
        paginator, page = pagination.paginate_queryset(final_result, request,None,TAG_DETAILS_REPORT_COLUMNS)
        columns = get_reports_columns_template(request.user.pk,TAG_DETAILS_REPORT_COLUMNS,request.data["path_name"])
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isProductFilterReq'] = True
        context = {
            'columns': columns,
            'actions': ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy
        }

        return pagination.paginated_response(final_result, context)



class SupplierCatalogReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        product = request.data.get('product')
        design = request.data.get('design', None)

        queryset = MakingAndWastageSettings.objects.filter(id_product=product)

        if design:
            queryset = queryset.filter(id_design=design)
        queryset = queryset.prefetch_related('supplier')

        final_result = []

        for obj in queryset:
            for supplier in obj.supplier.all():
                final_result.append({
                    'supplier_name': supplier.supplier_name,
                    'product_name': obj.id_product.product_name,
                    'design_name': obj.id_design.design_name if obj.id_design else None,
                    'total_mc': obj.purchase_mc,
                    'total_va': obj.purchase_va,
                    'total_flat_mc': obj.purchase_flat_mc,
                    'total_touch': obj.purchase_touch,
                })

        # aggregated_data = {}
        # for entry in final_result:
        #     key = (entry['supplier_name'], entry['product_name'])
        #     if key not in aggregated_data:
        #         aggregated_data[key] = {
        #             'supplier_name': entry['supplier_name'],
        #             'product_name': entry['product_name'],
        #             'total_mc': 0,
        #             'total_va': 0,
        #             'total_flat_mc': 0,
        #             'total_touch': 0,
        #         }
        #     aggregated_data[key]['total_mc'] += entry['total_mc']
        #     aggregated_data[key]['total_va'] += entry['total_va']
        #     aggregated_data[key]['total_flat_mc'] += entry['total_flat_mc']
        #     aggregated_data[key]['total_touch'] += entry['total_touch']

        data = {
            'columns': SUPPLIER_CATALOG_REPORT_COLUMNS,
            'rows': (final_result),
        }

        return Response(data, status=status.HTTP_200_OK)


class CashBookReportAPI(generics.GenericAPIView):

    def post(self,request):
        bill_setting_type = int(request.data.get('setting_bill_type',1))
        metal_queryset = Metal.objects.all()
        metal_serializer = MetalSerializer(metal_queryset, many=True)
        metal_data = metal_serializer.data
        result = []
        total_gold_purhase_wt = 0
        total_silver_purchase_wt = 0
        old_gold_alone_bills = self.get_old_gold_alone_bills(request.data['from_date'],request.data['to_date'],request.data['id_branch'],bill_setting_type)
        for metal in metal_data:
            response_data = {}
            sales_details = self.get_metal_wise_bill(metal['id_metal'],request.data['from_date'],request.data['to_date'],request.data['id_branch'],bill_setting_type)
            if len(sales_details) > 0:
                for sales in sales_details:
                    total_gold_purhase_wt += float(sales['gold_purchase_wt'])
                    total_silver_purchase_wt += float(sales['silver_purchase_wt'])
                response_data.update({
                                'metal_name':metal['metal_name'],
                                'bills':sales_details,
                            })
                result.append(response_data)
        order_advance_details = self.get_order_advance_details(request.data['from_date'],request.data['to_date'],request.data['id_branch'],bill_setting_type)
        opening = get_openning_cash(request.data['from_date'],request.data['id_branch'],bill_setting_type)
        cash_issue_details = self.get_cash_issue_details(request.data['from_date'],request.data['to_date'],request.data['id_branch'],bill_setting_type)
        for old_purchase in old_gold_alone_bills:
            total_gold_purhase_wt += float(old_purchase['gold_purchase_wt'])
            total_silver_purchase_wt += float(old_purchase['silver_purchase_wt'])
        return Response({
            "status":True,
            "sales_details":result,
            "old_gold_alone_bills":old_gold_alone_bills,
            "order_advance":order_advance_details,
            "opening_csh_received":opening,
            "cash_issue_details":cash_issue_details,
            "total_gold_purhase_wt" : format(total_gold_purhase_wt , '.3f'),
            "total_silver_purchase_wt" : format(total_silver_purchase_wt , '.3f')
            }, status=status.HTTP_200_OK)


    def get_order_advance_details(self,from_date,to_date,id_branch,setting_bill_type):
        filter = ""
        if setting_bill_type == 1 or setting_bill_type == 0:
           filter = f" and r.setting_bill_type = '{setting_bill_type}'"
        with connection.cursor() as cursor:
            query = F"""
                        SELECT IFNULL(d.pieces,0) as sales_pcs,IFNULL(d.gross_wt,0) as sales_wt,t.tag_code,
                        COALESCE(csh.payment_amount, 0) AS csh_amt,
                        COALESCE(crd.payment_amount, 0) AS card_amt,
                        COALESCE(upi.payment_amount, 0) AS upi_amt,
                        COALESCE(nb.payment_amount, 0) AS nb_amt,r.order_id,o.order_no
                        FROM erp_issue_receipt r 
                        LEFT JOIN erp_order o ON o.order_id = r.order_id
                        LEFT JOIN erp_order_details d ON d.order_id = o.order_id
                        LEFT JOIN erp_tagging t ON t.tag_id = d.erp_tag_id
                        LEFT JOIN (SELECT IFNULL(COALESCE(p.payment_amount),0) as payment_amount,p.issue_receipt_id
                                FROM erp_issue_receipt_payment_details p 
                                LEFT JOIN paymentmode m ON m.id_mode = p.payment_mode_id
                                WHERE m.short_code = 'Csh'
                                GROUP BY p.issue_receipt_id) as csh ON csh.issue_receipt_id = r.id
                        LEFT JOIN (SELECT IFNULL(COALESCE(p.payment_amount),0) as payment_amount,p.issue_receipt_id
                                FROM erp_issue_receipt_payment_details p 
                                LEFT JOIN paymentmode m ON m.id_mode = p.payment_mode_id
                                WHERE m.short_code = 'CC'
                                GROUP BY p.issue_receipt_id) as crd ON crd.issue_receipt_id = r.id
                        LEFT JOIN (SELECT IFNULL(COALESCE(p.payment_amount),0) as payment_amount,p.issue_receipt_id
                                FROM erp_issue_receipt_payment_details p 
                                LEFT JOIN paymentmode m ON m.id_mode = p.payment_mode_id
                                WHERE m.short_code = 'UPI'
                                GROUP BY p.issue_receipt_id) as upi ON upi.issue_receipt_id = r.id
                        LEFT JOIN (SELECT IFNULL(COALESCE(p.payment_amount),0) as payment_amount,p.issue_receipt_id
                                FROM erp_issue_receipt_payment_details p 
                                LEFT JOIN paymentmode m ON m.id_mode = p.payment_mode_id
                                WHERE m.short_code = 'NB'
                                GROUP BY p.issue_receipt_id) as nb ON nb.issue_receipt_id = r.id
                        WHERE r.receipt_type = 2 AND r.order_id IS NOT NULL and r.branch_id = '{id_branch}' {filter}  AND (DATE(r.bill_date) BETWEEN '{from_date}' AND '{to_date}')
                        GROUP BY r.id;
                    """
            cursor.execute(query)
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for index,row in enumerate(result):
                    field_value = dict(zip(field_names, row))
                    order_details  = self.order_details(field_value['order_id'])
                    for index, tag in enumerate(order_details):
                        new_entry = field_value.copy()  # Copy all bill details
                        new_entry.pop("tag_details", None)  # Remove original tag_details field
                        new_entry["tag_code"] = tag["tag_code"]  # Assign tag_code to new entry
                        new_entry["sales_wt"] = tag["gross_wt"]  # Assign tag_code to new entry
                        new_entry["sales_pcs"] = tag["pieces"]  # Assign tag_code to new entry
                        if index > 0:
                            field_value['csh_amt'] = 0
                            field_value['card_amt'] = 0
                            field_value['upi_amt'] = 0
                            field_value['nb_amt'] = 0
                        report_data.append(new_entry)


                response_data = report_data
            return response_data

    def order_details(self,order_id):
        with connection.cursor() as cursor:
            sql = F"""
                    SELECT 
                    s.order_id AS order_id,t.tag_code,
                    SUM(s.pieces) AS pieces,
                    SUM(s.gross_wt) AS gross_wt
                    FROM erp_order_details s
                    LEFT JOIN erp_tagging t ON t.tag_id = s.erp_tag_id
                    WHERE s.order_id = '{order_id}'
                    GROUP BY s.order_id;
                    """
            cursor.execute(sql)
                
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.append(field_value)
                response_data = report_data
            return response_data

    def get_metal_wise_bill(self,id_metal,start_date="",end_date="",branch_id="",setting_bill_type=1):
        filter = ''
        if setting_bill_type == 1 or setting_bill_type == 0:
           filter = f" and i.setting_bill_type = '{setting_bill_type}' "
        with connection.cursor() as cursor:
            query = F"""
                    SELECT 
                    i.erp_invoice_id,i.sales_invoice_no,
                    DATE_FORMAT(i.invoice_date, '%d-%m-%Y') AS invoice_date,
                    COALESCE(sales.pieces, 0) AS sales_pcs,
                    COALESCE(sales.gross_wt, 0) AS sales_wt,
                    COALESCE(sales.item_cost, 0) AS sales_cost,
                    (COALESCE(gold_pur.gross_wt, 0) + COALESCE(ret_gold.gross_wt, 0)) AS gold_purchase_wt,
                    (COALESCE(gold_pur.amount, 0) + COALESCE(ret_gold.item_cost, 0)) AS gold_purchase_amt,
                    (COALESCE(silver_pur.gross_wt, 0)+ COALESCE(ret_silver.gross_wt, 0)) AS silver_purchase_wt,
                    (COALESCE(silver_pur.amount, 0)+ COALESCE(ret_silver.item_cost, 0)) AS silver_purchase_amt,
                    COALESCE(ret_gold.gross_wt, 0) AS ret_gross_wt,
                    COALESCE(ret_gold.item_cost, 0) AS ret_amt,
                    COALESCE(i.due_amount, 0) AS due_amount,
                    COALESCE(csh.payment_amount, 0) AS csh_recd_amt,
                    COALESCE(csh.paid_amount, 0) AS csh_paid_amt,
                    COALESCE(crd.payment_amount, 0) AS card_amt,
                    COALESCE(upi.payment_amount, 0) AS upi_amt,
                    COALESCE(nb.payment_amount, 0) AS nb_amt,
                    COALESCE(adv.adj_amt, 0) AS adj_amt,
                    COALESCE(chit_adv.adj_amt, 0) AS chit_adj_amt,
                    COALESCE(gift.gift_amt, 0) AS gift_amt,
                    COALESCE(sales.mrp_dis , 0) as mrp_dis
                    
                    
                FROM erp_invoice i
                LEFT JOIN (
                    SELECT 
                        s.invoice_bill_id_id AS erp_invoice_id,
                        SUM(s.pieces) AS pieces,
                        SUM(s.gross_wt) AS gross_wt,
                        SUM(s.item_cost) AS item_cost,
                        if(p.sales_mode=0,SUM(s.discount_amount),0) as mrp_dis
                    FROM erp_invoice_sales_details s
                    left join erp_product p on p.pro_id = s.id_product_id
                    JOIN erp_invoice i ON i.erp_invoice_id = s.invoice_bill_id_id
                    WHERE i.invoice_status = 1
                    GROUP BY s.invoice_bill_id_id
                ) AS sales ON sales.erp_invoice_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        p.invoice_bill_id_id, 
                        SUM(p.gross_wt) AS gross_wt, 
                        SUM(p.amount) AS amount
                    FROM erp_invoice_old_metal_details p
                    left join old_metal_item i ON i.id_item_type = item_type_id
                    where i.id_metal_id = 1
                    GROUP BY p.invoice_bill_id_id
                ) AS gold_pur ON gold_pur.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        p.invoice_bill_id_id, 
                        SUM(p.gross_wt) AS gross_wt, 
                        SUM(p.amount) AS amount
                    FROM erp_invoice_old_metal_details p
                    left join old_metal_item i ON i.id_item_type = item_type_id
                    where i.id_metal_id = 2
                    GROUP BY p.invoice_bill_id_id
                ) AS silver_pur ON silver_pur.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        r.invoice_bill_id_id, 
                        SUM(r.gross_wt) AS gross_wt, 
                        SUM(r.item_cost) AS item_cost
                    FROM erp_invoice_sales_return_details r
                    left join erp_product p on p.pro_id = r.id_product_id
                    where p.id_metal_id = 1
                    GROUP BY r.invoice_bill_id_id
                ) AS ret_gold ON ret_gold.invoice_bill_id_id = i.erp_invoice_id
                
                LEFT JOIN (
                    SELECT 
                        r.invoice_bill_id_id, 
                        SUM(r.gross_wt) AS gross_wt, 
                        SUM(r.item_cost) AS item_cost
                    FROM erp_invoice_sales_return_details r
                    left join erp_product p on p.pro_id = r.id_product_id
                    where p.id_metal_id = 2
                    GROUP BY r.invoice_bill_id_id
                ) AS ret_silver ON ret_silver.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        pay.invoice_bill_id_id, 
                        SUM(IF(pay.payment_type = 1, pay.payment_amount, 0 )) AS payment_amount,
                        SUM(IF(pay.payment_type != 1, pay.payment_amount, 0 )) AS paid_amount
                    FROM erp_invoice_payment_details pay
                    JOIN paymentmode m ON m.id_mode = pay.payment_mode_id
                    WHERE m.short_code = 'Csh'
                    GROUP BY pay.invoice_bill_id_id
                ) AS csh ON csh.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        pay.invoice_bill_id_id, 
                        SUM(pay.payment_amount) AS payment_amount
                    FROM erp_invoice_payment_details pay
                    JOIN paymentmode m ON m.id_mode = pay.payment_mode_id
                    WHERE m.short_code = 'CC'
                    GROUP BY pay.invoice_bill_id_id
                ) AS crd ON crd.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        pay.invoice_bill_id_id, 
                        SUM(pay.payment_amount) AS payment_amount
                    FROM erp_invoice_payment_details pay
                    JOIN paymentmode m ON m.id_mode = pay.payment_mode_id
                    WHERE m.short_code = 'UPI'
                    GROUP BY pay.invoice_bill_id_id
                ) AS upi ON upi.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        pay.invoice_bill_id_id, 
                        SUM(pay.payment_amount) AS payment_amount
                    FROM erp_invoice_payment_details pay
                    JOIN paymentmode m ON m.id_mode = pay.payment_mode_id
                    WHERE m.short_code = 'NB'
                    GROUP BY pay.invoice_bill_id_id
                ) AS nb ON nb.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        a.invoice_bill_id_id, 
                        SUM(a.adj_amount) AS adj_amt
                    FROM erp_advance_adj a
                    JOIN erp_issue_receipt iss ON iss.id = a.receipt_id
                    GROUP BY a.invoice_bill_id_id
                ) AS adv ON adv.invoice_bill_id_id = i.erp_invoice_id
                
                LEFT JOIN (
                    SELECT 
                        a.invoice_bill_id_id, 
                        SUM(a.amount) AS gift_amt
                    FROM erp_invoice_gift_adjusted_details a
                    JOIN erp_invoice i ON i.erp_invoice_id = a.invoice_bill_id_id
                    WHERE i.invoice_status = 1
                    GROUP BY a.invoice_bill_id_id
                ) AS gift ON gift.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        a.invoice_bill_id_id, 
                        SUM(a.closing_amount) AS adj_amt
                    FROM erp_invoice_scheme_adjusted_details a
                    GROUP BY a.invoice_bill_id_id
                ) AS chit_adv ON chit_adv.invoice_bill_id_id = i.erp_invoice_id

                WHERE i.metal_id = '{id_metal}' AND i.invoice_status = 1  {filter} and i.invoice_type != 2
                AND i.id_branch_id = '{branch_id}' AND (DATE(i.invoice_date) BETWEEN '{start_date}' AND '{end_date}')
                GROUP BY i.erp_invoice_id;
                """

            cursor.execute(query)
            
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                sno = 0
                for row in result:
                    field_value = dict(zip(field_names, row))
                    tag_details = self.sales_tag_details(field_value['erp_invoice_id'],setting_bill_type)
                    sno += 1
                    # Create separate bill entries for each tag
                    if len(tag_details) > 0 :
                        for index, tag in enumerate(tag_details):
                            new_entry = field_value.copy()  # Copy all bill details
                            new_entry.pop("tag_details", None)  # Remove original tag_details field
                            new_entry["tag_code"] = tag["tag_code"]  # Assign tag_code to new entry
                            new_entry["sales_wt"] = tag["gross_wt"]  # Assign tag_code to new entry
                            new_entry["sales_pcs"] = tag["pieces"]  # Assign tag_code to new entry
                            new_entry["sno"] = sno  # Assign tag_code to new entry
                            if index > 0:
                                new_entry["sales_invoice_no"] = ''  # Assign tag_code to new entry
                                new_entry["sales_cost"] = 0
                                new_entry["gold_purchase_wt"] = 0
                                new_entry["gold_purchase_amt"] = 0
                                new_entry["silver_purchase_wt"] = 0
                                new_entry["silver_purchase_amt"] = 0
                                new_entry["due_amount"] = 0
                                new_entry["csh_amt"] = 0
                                new_entry["card_amt"] = 0
                                new_entry["upi_amt"] = 0
                                new_entry["nb_amt"] = 0
                                new_entry["adj_amt"] = 0
                                new_entry["gift_amt"] = 0
                                new_entry["csh_paid_amt"] = 0
                                new_entry["csh_recd_amt"] = 0
                                new_entry["mrp_dis"] = 0
                            report_data.append(new_entry)
                            
                    else:
                        report_data.append(field_value)
                response_data = report_data
            return response_data

    def get_old_gold_alone_bills(self,start_date="",end_date="",branch_id="",setting_bill_type=1):
        filter = ''
        if setting_bill_type == 1 or setting_bill_type == 0:
           filter = f" and i.setting_bill_type = '{setting_bill_type}' "
        with connection.cursor() as cursor:
            query = F"""
                    SELECT 
                    i.erp_invoice_id,
                    concat("PU","-",i.purchase_invoice_no) as purchase_invoice_no,
                    DATE_FORMAT(i.invoice_date, '%d-%m-%Y') AS invoice_date,
                    COALESCE(sales.pieces, 0) AS sales_pcs,
                    COALESCE(sales.gross_wt, 0) AS sales_wt,
                    COALESCE(sales.item_cost, 0) AS sales_cost,
                    COALESCE(gold_pur.gross_wt, 0) AS gold_purchase_wt,
                    COALESCE(gold_pur.amount, 0) AS gold_purchase_amt,
                    COALESCE(silver_pur.gross_wt, 0) AS silver_purchase_wt,
                    COALESCE(silver_pur.amount, 0) AS silver_purchase_amt,
                    COALESCE(ret.gross_wt, 0) AS ret_gross_wt,
                    COALESCE(ret.item_cost, 0) AS ret_amt,
                    COALESCE(i.due_amount, 0) AS due_amount,
                    COALESCE(csh.payment_amount, 0) AS csh_recd_amt,
                    COALESCE(csh.paid_amount, 0) AS csh_paid_amt,
                    COALESCE(crd.payment_amount, 0) AS card_amt,
                    COALESCE(upi.payment_amount, 0) AS upi_amt,
                    COALESCE(nb.payment_amount, 0) AS nb_amt,
                    COALESCE(adv.adj_amt, 0) AS adj_amt,
                    COALESCE(chit_adv.adj_amt, 0) AS chit_adj_amt,
                    COALESCE(gift.gift_amt, 0) AS gift_amt
                    
                    
                FROM erp_invoice i
                LEFT JOIN (
                    SELECT 
                        s.invoice_bill_id_id AS erp_invoice_id,
                        SUM(s.pieces) AS pieces,
                        SUM(s.gross_wt) AS gross_wt,
                        SUM(s.item_cost) AS item_cost
                    FROM erp_invoice_sales_details s
                    JOIN erp_invoice i ON i.erp_invoice_id = s.invoice_bill_id_id
                    WHERE i.invoice_status = 1
                    GROUP BY s.invoice_bill_id_id
                ) AS sales ON sales.erp_invoice_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        p.invoice_bill_id_id, 
                        SUM(p.gross_wt) AS gross_wt, 
                        SUM(p.amount) AS amount
                    FROM erp_invoice_old_metal_details p
                    left join old_metal_item i ON i.id_item_type = item_type_id
                    where i.id_metal_id = 1
                    GROUP BY p.invoice_bill_id_id
                ) AS gold_pur ON gold_pur.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        p.invoice_bill_id_id, 
                        SUM(p.gross_wt) AS gross_wt, 
                        SUM(p.amount) AS amount
                    FROM erp_invoice_old_metal_details p
                    left join old_metal_item i ON i.id_item_type = item_type_id
                    where i.id_metal_id = 2
                    GROUP BY p.invoice_bill_id_id
                ) AS silver_pur ON silver_pur.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        r.invoice_bill_id_id, 
                        SUM(r.gross_wt) AS gross_wt, 
                        SUM(r.item_cost) AS item_cost
                    FROM erp_invoice_sales_return_details r
                    GROUP BY r.invoice_bill_id_id
                ) AS ret ON ret.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        pay.invoice_bill_id_id, 
                        SUM(IF(pay.payment_type = 1, pay.payment_amount, 0 )) AS payment_amount,
                        SUM(IF(pay.payment_type != 1, pay.payment_amount, 0 )) AS paid_amount
                    FROM erp_invoice_payment_details pay
                    JOIN paymentmode m ON m.id_mode = pay.payment_mode_id
                    WHERE m.short_code = 'Csh'
                    GROUP BY pay.invoice_bill_id_id
                ) AS csh ON csh.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        pay.invoice_bill_id_id, 
                        SUM(pay.payment_amount) AS payment_amount
                    FROM erp_invoice_payment_details pay
                    JOIN paymentmode m ON m.id_mode = pay.payment_mode_id
                    WHERE m.short_code = 'CC'
                    GROUP BY pay.invoice_bill_id_id
                ) AS crd ON crd.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        pay.invoice_bill_id_id, 
                        SUM(pay.payment_amount) AS payment_amount
                    FROM erp_invoice_payment_details pay
                    JOIN paymentmode m ON m.id_mode = pay.payment_mode_id
                    WHERE m.short_code = 'UPI'
                    GROUP BY pay.invoice_bill_id_id
                ) AS upi ON upi.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        pay.invoice_bill_id_id, 
                        SUM(pay.payment_amount) AS payment_amount
                    FROM erp_invoice_payment_details pay
                    JOIN paymentmode m ON m.id_mode = pay.payment_mode_id
                    WHERE m.short_code = 'NB'
                    GROUP BY pay.invoice_bill_id_id
                ) AS nb ON nb.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        a.invoice_bill_id_id, 
                        SUM(a.adj_amount) AS adj_amt
                    FROM erp_advance_adj a
                    JOIN erp_issue_receipt iss ON iss.id = a.receipt_id
                    GROUP BY a.invoice_bill_id_id
                ) AS adv ON adv.invoice_bill_id_id = i.erp_invoice_id
                
                LEFT JOIN (
                    SELECT 
                        a.invoice_bill_id_id, 
                        SUM(a.amount) AS gift_amt
                    FROM erp_invoice_gift_adjusted_details a
                    JOIN erp_invoice i ON i.erp_invoice_id = a.invoice_bill_id_id
                    WHERE i.invoice_status = 1
                    GROUP BY a.invoice_bill_id_id
                ) AS gift ON gift.invoice_bill_id_id = i.erp_invoice_id

                LEFT JOIN (
                    SELECT 
                        a.invoice_bill_id_id, 
                        SUM(a.closing_amount) AS adj_amt
                    FROM erp_invoice_scheme_adjusted_details a
                    GROUP BY a.invoice_bill_id_id
                ) AS chit_adv ON chit_adv.invoice_bill_id_id = i.erp_invoice_id

                WHERE  i.invoice_status = 1  {filter} and i.invoice_type = 2
                AND i.id_branch_id = '{branch_id}' AND (DATE(i.invoice_date) BETWEEN '{start_date}' AND '{end_date}')
                GROUP BY i.erp_invoice_id;
                """

            cursor.execute(query)
            
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.append(field_value)
                response_data = report_data
            return response_data


    def sales_tag_details(self,erp_invoice_id,setting_bill_type):
        with connection.cursor() as cursor:
            sql = F"""
                    SELECT 
                    s.invoice_bill_id_id AS erp_invoice_id,IF(t.old_tag_code IS NOT NULL, t.old_tag_code, if(t.tag_code!=null , t.tag_code , des.design_code)) AS tag_code,
                    SUM(s.pieces) AS pieces,
                    SUM(s.gross_wt) AS gross_wt,
                    SUM(s.item_cost) AS item_cost
                    FROM erp_invoice_sales_details s
                    left join erp_design des on des.id_design = s.id_design_id
                    LEFT JOIN erp_invoice i ON i.erp_invoice_id = s.invoice_bill_id_id
                    left join erp_tagging t on t.tag_id = s.tag_id_id
                    WHERE i.invoice_status = 1 and s.invoice_bill_id_id = '{erp_invoice_id}'
                    GROUP BY s.invoice_sale_item_id;
                    """
            cursor.execute(sql)
                
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.append(field_value)
                response_data = report_data
            return response_data


    def get_cash_issue_details(self,from_date,to_date,branch_id,setting_bill_type):

        supplier_payment_queryset = ErpSupplierPaymentModeDetail.objects.filter(
            payment_mode = 1,
            purchase_payment__entry_date__range=[from_date, to_date]
            ).values(
                'payment_amount'
            ).annotate(
                ref_id = F('purchase_payment__id_purchase_payment'),
                amount = F('payment_amount'),
                 type=Case(
                    When(payment_type=2, then=Value(1)),  # Debit
                    When(payment_type=1, then=Value(2)),  # Credit
                    default=Value(2),
                    output_field=IntegerField()
                ),
                invoice_date=F('purchase_payment__entry_date'),
                bill_no=F('purchase_payment__ref_no'),
                remarks=F('purchase_payment__remarks'),
            )

        issue_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(
            Q(issue_receipt__bill_status=1)&
            Q(issue_receipt__branch=branch_id)&
            Q(issue_receipt__bill_date__range=[from_date, to_date])&
            (Q(issue_receipt__issue_type__in=[1, 2, 3, 5]) | 
            Q(issue_receipt__receipt_type__in=[5,6,8]))&
            Q(payment_mode=1)
        ).values(
            'payment_amount',
        ).annotate(
            ref_id = F('issue_receipt__id'),
            amount = F('payment_amount'),
            type=F('issue_receipt__type'),
            invoice_date=F('issue_receipt__bill_date'),
            remarks=F('issue_receipt__remarks'),
            bill_no=F('issue_receipt__bill_no')
        )
        if setting_bill_type == 1 or setting_bill_type == 0:
            issue_payment_queryset = issue_payment_queryset.filter(issue_receipt__setting_bill_type=setting_bill_type)
            supplier_payment_queryset = supplier_payment_queryset.filter(purchase_payment__setting_bill_type=setting_bill_type)

        return list(issue_payment_queryset) + list(supplier_payment_queryset)


class MonthWiseSalesReportAPI(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self,request):
        branch = request.data['branch']
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        report_type = request.data['report_type']
        id_metal = request.data['id_metal']
        with connection.cursor() as cursor:
            if(report_type==1):
                sql = F"""
                    SELECT COALESCE(SUM(s.pieces),0) as pcs,COALESCE(SUM(s.gross_wt),0) as gross_wt,
                    date_format(i.invoice_date,'%M-%Y') as invoice_date,
                    COALESCE(SUM(s.taxable_amount),0) as taxable_amount,
                    COALESCE(SUM(s.cgst_cost),0) as cgst_cost,
                    COALESCE(SUM(s.sgst_cost),0) as sgst_cost,
                    COALESCE(SUM(s.igst_cost),0) as igst_cost,
                    COALESCE(SUM(s.item_cost),0) as item_cost,AVG(s.rate_per_gram) as avg_rate_per_gram,
                    mt.metal_name as metal_name,MIN(i.sales_invoice_no) AS starting_invoice_no,
                    MAX(i.sales_invoice_no) AS ending_invoice_no
                    FROM erp_invoice i
                    LEFT JOIN metal mt on mt.id_metal = i.metal_id
                    left JOIN erp_invoice_sales_details s ON s.invoice_bill_id_id = i.erp_invoice_id
                    WHERE i.invoice_status = 1 and i.setting_bill_type = 1
                    AND (DATE(i.invoice_date) BETWEEN '{from_date}' AND '{to_date}')
                """
            if(report_type==2):
                sql = F"""
                    SELECT COALESCE(SUM(s.pieces),0) as pcs,COALESCE(SUM(s.gross_wt),0) as gross_wt,
                    date_format(i.invoice_date,'%d-%m-%Y') as invoice_date,
                    COALESCE(SUM(s.taxable_amount),0) as taxable_amount,
                    COALESCE(SUM(s.cgst_cost),0) as cgst_cost,
                    COALESCE(SUM(s.sgst_cost),0) as sgst_cost,
                    COALESCE(SUM(s.igst_cost),0) as igst_cost,
                    COALESCE(SUM(s.item_cost),0) as item_cost,AVG(s.rate_per_gram) as avg_rate_per_gram,
                    mt.metal_name as metal_name,MIN(i.sales_invoice_no) AS starting_invoice_no,
                    MAX(i.sales_invoice_no) AS ending_invoice_no
                    FROM erp_invoice i 
                    LEFT JOIN metal mt on mt.id_metal = i.metal_id
                    left JOIN erp_invoice_sales_details s ON s.invoice_bill_id_id = i.erp_invoice_id
                    WHERE i.invoice_status = 1 and i.setting_bill_type = 1
                    AND (DATE(i.invoice_date) BETWEEN '{from_date}' AND '{to_date}')
                """
            if branch:
                sql += F" AND i.id_branch_id IN ({','.join(map(str, branch))})"
            if id_metal!='':
                sql += F" AND i.metal_id = {id_metal}"
            if(report_type==1):
                sql += """
                    GROUP BY date_format(i.invoice_date, '%m-%Y')
                    ORDER BY i.erp_invoice_id DESC;
                """
            if(report_type==2):
                sql += """
                    GROUP BY date(invoice_date)
                    ORDER BY i.erp_invoice_id DESC;
                """
            cursor.execute(sql)
                
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.append(field_value)
                response_data = report_data
            paginator, page = pagination.paginate_queryset(response_data, request,None,SUMMARY_SALES_REPORT_COLUMNS)
            columns = get_reports_columns_template(request.user.pk,SUMMARY_SALES_REPORT_COLUMNS,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            filters_copy['isReportTypeReq'] = True
            context = {
                'columns': columns,
                'actions': ACTION_LIST,
                'page_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req': True,
                'filters': filters_copy
            }

            return pagination.paginated_response(list(page), context)


class MonthWisePurchaseEntryReportAPI(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self,request):
        branch = request.data['branch']
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        report_type = request.data['report_type']
        id_metal = request.data.get('id_metal','')
        if(report_type==1):
            sql = F"""
                select 
                CONCAT(mt.metal_name,' ORNAMENTS PURCHASE') as group_name,
                date_format(e.entry_date,'%M-%Y') as invoice_date,
                COALESCE(SUM(s.pieces),0) as pcs,COALESCE(SUM(s.gross_wt),0) as gross_wt,
                COALESCE(SUM(s.pure_wt),0) as pure_wt,
                COALESCE(SUM(s.purchase_cost-s.tax_amount),0) as taxable_amount,
                COALESCE(SUM(s.cgst_cost),0) as cgst_cost,
                COALESCE(SUM(s.sgst_cost),0) as sgst_cost,
                COALESCE(SUM(s.igst_cost),0) as igst_cost,
                COALESCE(SUM(e.tds_amount),0) as tds_amount,
                COALESCE(SUM(e.net_amount),0) as item_cost,AVG(s.purchase_rate) as avg_rate_per_gram,
                mt.metal_name as metal_name,min(e.ref_no) as starting_invoice_no,
                max(e.ref_no) as ending_invoice_no
                from erp_purchase_entry e
                left join erp_purchase_item_details s on s.purchase_entry_id = e.id_purchase_entry
                left join erp_product p on p.pro_id = s.id_product_id
                left join metal mt on mt.id_metal = p.id_metal_id
                where e.is_cancelled = 0 and e.setting_bill_type = 1 AND e.entry_date IS NOT NULL
                AND (DATE(e.entry_date) BETWEEN '{from_date}' AND '{to_date}')
            """
        if(report_type==2):
            sql = F"""
                select 
                CONCAT(mt.metal_name,' ORNAMENTS PURCHASE') as group_name,
                date_format(e.entry_date,'%d-%m-%y') as invoice_date,
                COALESCE(SUM(s.pieces),0) as pcs,COALESCE(SUM(s.gross_wt),0) as gross_wt,
                COALESCE(SUM(s.pure_wt),0) as pure_wt,
                COALESCE(SUM(s.purchase_cost-s.tax_amount),0) as taxable_amount,
                COALESCE(SUM(s.cgst_cost),0) as cgst_cost,
                COALESCE(SUM(s.sgst_cost),0) as sgst_cost,
                COALESCE(SUM(s.igst_cost),0) as igst_cost,
                COALESCE(SUM(e.tds_amount),0) as tds_amount,
                COALESCE(SUM(e.net_amount),0) as item_cost,AVG(s.purchase_rate) as avg_rate_per_gram,
                mt.metal_name as metal_name,min(e.ref_no) as starting_invoice_no,
                max(e.ref_no) as ending_invoice_no
                from erp_purchase_entry e
                left join erp_purchase_item_details s on s.purchase_entry_id = e.id_purchase_entry
                left join erp_product p on p.pro_id = s.id_product_id
                left join metal mt on mt.id_metal = p.id_metal_id
                where e.is_cancelled = 0 and e.setting_bill_type = 1 AND e.entry_date IS NOT NULL
                AND (DATE(e.entry_date) BETWEEN '{from_date}' AND '{to_date}')
            """
        if branch:
            sql += F" AND e.id_branch_id IN ({','.join(map(str, branch))})"
        if id_metal!='':
            sql += F" AND mt.id_metal = {id_metal}"
        if(report_type==1):
            sql += """
                GROUP BY date_format(e.entry_date, '%M-%Y'),mt.id_metal
                ORDER BY MAX(e.entry_date) DESC;
            """
        if(report_type==2):
            sql += """
                GROUP BY date(e.entry_date),mt.id_metal
                ORDER BY MAX(e.entry_date) DESC;
            """
        
            
        response_data = generate_query_result(sql)

        if(report_type==1):
            sql2 = F"""
                select 
                CONCAT('OLD ',mt.metal_name,' PURCHASE') as group_name,
                date_format(e.invoice_date,'%M-%Y') as invoice_date,
                COALESCE(SUM(s.pieces),0) as pcs,COALESCE(SUM(s.gross_wt),0) as gross_wt,
                COALESCE(SUM(s.pure_weight),0) as pure_wt,
                COALESCE(SUM(s.amount),0) as taxable_amount,
                0 as cgst_cost,
                0 as sgst_cost,
                0 as igst_cost,
                0 as tds_amount,
                COALESCE(SUM(s.amount),0) as item_cost,AVG(s.rate_per_gram) as avg_rate_per_gram,
                mt.metal_name as metal_name,min(e.purchase_invoice_no) as starting_invoice_no,
                max(e.purchase_invoice_no) as ending_invoice_no
                from erp_invoice e
                left join erp_invoice_old_metal_details s on s.invoice_bill_id_id = e.erp_invoice_id
                left join erp_product p on p.pro_id = s.id_product_id
                left join metal mt on mt.id_metal = p.id_metal_id
                where e.invoice_status = 1 and e.setting_bill_type = 1 AND s.invoice_bill_id_id IS NOT NULL
                AND (DATE(e.invoice_date) BETWEEN '{from_date}' AND '{to_date}')
            """
        if(report_type==2):
            sql2 = F"""
                select date_format(e.invoice_date,'%d-%m-%y') as invoice_date,
                CONCAT('OLD ',mt.metal_name,' PURCHASE') as group_name,
                COALESCE(SUM(s.pieces),0) as pcs,COALESCE(SUM(s.gross_wt),0) as gross_wt,
                COALESCE(SUM(s.pure_weight),0) as pure_wt,
                COALESCE(SUM(s.amount),0) as taxable_amount,
                0 as cgst_cost,
                0 as sgst_cost,
                0 as igst_cost,
                0 as tds_amount,
                COALESCE(SUM(s.amount),0) as item_cost,AVG(s.rate_per_gram) as avg_rate_per_gram,
                mt.metal_name as metal_name,min(e.purchase_invoice_no) as starting_invoice_no,
                max(e.purchase_invoice_no) as ending_invoice_no
                from erp_invoice e
                left join erp_invoice_old_metal_details s on s.invoice_bill_id_id = e.erp_invoice_id
                left join erp_product p on p.pro_id = s.id_product_id
                left join metal mt on mt.id_metal = p.id_metal_id
                where e.invoice_status = 1 and e.setting_bill_type = 1 AND s.invoice_bill_id_id IS NOT NULL
                AND (DATE(e.invoice_date) BETWEEN '{from_date}' AND '{to_date}')
            """
        if branch:
            sql2 += F" AND e.id_branch_id IN ({','.join(map(str, branch))})"
        if id_metal!='':
            sql2 += F" AND mt.id_metal = {id_metal}"
        if(report_type==1):
            sql2 += """
                GROUP BY date_format(e.invoice_date, '%M-%Y'),mt.id_metal
                ORDER BY MAX(e.invoice_date) DESC;
            """
        if(report_type==2):
            sql2 += """
                GROUP BY date(e.invoice_date),mt.id_metal
                ORDER BY MAX(e.invoice_date) DESC;
            """
        
            
        response_data2 = generate_query_result(sql2)



        response_data = response_data + response_data2
        paginator, page = pagination.paginate_queryset(response_data, request,None,SUMMARY_PURCHASE_ENTRY_REPORT_COLUMNS)
        columns = get_reports_columns_template(request.user.pk,SUMMARY_PURCHASE_ENTRY_REPORT_COLUMNS,request.data["path_name"])
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isMetalFilterReq'] = True
        filters_copy['isReportTypeReq'] = True
        context = {
            'columns': columns,
            'groupingColumns': ["group_name"],
            'actions': ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy
        }

        return pagination.paginated_response(list(page), context)
                    
class StockInwardReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate',None)
        to_date = request.data.get('toDate',None)
        branch = request.data.get('branch',[])
        report_type = int(request.data.get('group_by',1))
        if report_type == '':
            report_type =0
        groupingColumns = ["section_name"] if report_type == 2 else []
        lot_type = 0
        if 'lotType' in request.data:
            lot_type = (request.data.get('lotType',0))

        non_tag_details = ErpLotNonTagInwardDetails.objects.filter(detail__entry_date__lte=to_date, 
                                                detail__entry_date__gte=from_date)
        lot_merge_details = ErpLotMergeDetails.objects.filter(lot_merge__entry_date__lte=to_date, 
                                                lot_merge__entry_date__gte=from_date)
        if(report_type == 1):
            tag_details = ErpTagging.objects.filter(tag_date__lte=to_date, 
                                                tag_date__gte=from_date).order_by('tag_lot_inward_details__lot_no__lot_type')
        else:
            tag_details = ErpTagging.objects.filter(tag_date__lte=to_date,tag_date__gte=from_date)
        if(branch):
            tag_details = tag_details.filter(tag_branch_id__in = branch)
            non_tag_details = non_tag_details.filter(detail__id_branch__in = branch).order_by('id_lot_inward_detail__lot_no__lot_type')
        if lot_type!='' and lot_type!=0:
            tag_details = tag_details.filter(tag_lot_inward_details__lot_no__lot_type = lot_type)
            non_tag_details = non_tag_details.filter(id_lot_inward_detail__lot_no__lot_type = lot_type)
            lot_merge_details = lot_merge_details.filter(id_lot_inward_detail__lot_no__lot_type = lot_type)
        if(report_type == 1):
            tag_details = tag_details.values('tag_design_id').annotate(
                product_name = F('tag_design_id__design_name'),
                sales_mode = F('tag_product_id__sales_mode'),
                lot_code = F('tag_lot_inward_details__lot_no__lot_code'),
                lot_type = F('tag_lot_inward_details__lot_no__lot_type'),
                total_tag_pcs=Sum('tag_pcs'),
                total_tag_gwt=Sum('tag_gwt'),
                total_tag_lwt=Sum('tag_lwt'),
                total_tag_nwt=Sum('tag_nwt'),
                total_tag_stn_wt=Sum('tag_stn_wt'),
                total_tag_dia_wt=Sum('tag_dia_wt')
            )
            non_tag_details = non_tag_details.values('id_lot_inward_detail__id_design').annotate(
                product_name = F('id_lot_inward_detail__id_design__design_name'),
                lot_code = F('id_lot_inward_detail__lot_no__lot_code'),
                lot_type = F('id_lot_inward_detail__lot_no__lot_type'),
                total_tag_pcs=Sum('pieces'),
                total_tag_gwt=Sum('gross_wt'),
                total_tag_lwt=Sum('less_wt'),
                total_tag_nwt=Sum('net_wt'),
                total_tag_stn_wt=Sum('stone_wt'),
                total_tag_dia_wt=Sum('dia_wt')
            )
            lot_merge_details = lot_merge_details.values('id_lot_inward_detail__id_design').annotate(
                product_name = F('id_lot_inward_detail__id_design__design_name'),
                lot_code = F('id_lot_inward_detail__lot_no__lot_code'),
                lot_type = F('id_lot_inward_detail__lot_no__lot_type'),
                total_tag_pcs=Sum('pieces'),
                total_tag_gwt=Sum('gross_wt'),
                total_tag_nwt=Sum('gross_wt'),
                total_tag_lwt = Value(0, output_field=DecimalField(max_digits=10, decimal_places=3)),
                total_tag_stn_wt = Value(0, output_field=DecimalField(max_digits=10, decimal_places=3)),
                total_tag_dia_wt = Value(0, output_field=DecimalField(max_digits=10, decimal_places=3))
            )
            final_result = []
            for tag in tag_details:
                product_name = tag['product_name']
                
                final_result.append({
                    'product_name': product_name,
                    'lot_code': tag['lot_code'],
                    'sales_mode': tag['sales_mode'],
                    'lot_type': (
                        'Stock outward' if tag['lot_type'] == 1 else
                        'Non stock plus' if tag['lot_type'] == 2 else
                        'Partly Sale' if tag['lot_type'] == 3 else
                        'Old Metal' if tag['lot_type'] == 4 else
                        'Lot Merge'
                    ),
                    'total_tag_pcs': tag['total_tag_pcs'],
                    'total_tag_gwt': tag['total_tag_gwt'] if int(tag['sales_mode']) == 1 else 0,
                    'total_tag_lwt': tag['total_tag_lwt'],
                    'total_tag_nwt': tag['total_tag_nwt'] if int(tag['sales_mode']) == 1 else 0,
                    'total_tag_stn_wt': tag['total_tag_stn_wt'],
                    'total_tag_dia_wt': tag['total_tag_dia_wt'],
                })
            for tag in lot_merge_details:
                product_name = tag['product_name']
                
                final_result.append({
                    'product_name': product_name,
                    'lot_code': tag['lot_code'],
                   'lot_type': (
                        'Stock outward' if tag['lot_type'] == 1 else
                        'Non stock plus' if tag['lot_type'] == 2 else
                        'Partly Sale' if tag['lot_type'] == 3 else
                        'Old Metal' if tag['lot_type'] == 4 else
                        'Lot Merge'
                    ),
                    'total_tag_pcs': tag['total_tag_pcs'],
                    'total_tag_gwt': tag['total_tag_gwt'],
                    'total_tag_lwt': tag['total_tag_lwt'],
                    'total_tag_nwt': tag['total_tag_nwt'],
                    'total_tag_stn_wt': tag['total_tag_stn_wt'],
                    'total_tag_dia_wt': tag['total_tag_dia_wt'],
                })
            
            for tag in non_tag_details:
                product_name = tag['product_name']
                
                final_result.append({
                    'product_name': product_name,
                    'lot_code': tag['lot_code'],
                    'lot_type': (
                        'Stock outward' if tag['lot_type'] == 1 else
                        'Non stock plus' if tag['lot_type'] == 2 else
                        'Partly Sale' if tag['lot_type'] == 3 else
                        'Old Metal' if tag['lot_type'] == 4 else
                        'Lot Merge'
                    ),
                    'total_tag_pcs': tag['total_tag_pcs'],
                    'total_tag_gwt': tag['total_tag_gwt'],
                    'total_tag_lwt': tag['total_tag_lwt'],
                    'total_tag_nwt': tag['total_tag_nwt'],
                    'total_tag_stn_wt': tag['total_tag_stn_wt'],
                    'total_tag_dia_wt': tag['total_tag_dia_wt'],
                })
            columns = get_reports_columns_template(request.user.pk,STOCK_INWARD_REPORT_COLUMNS,request.data["path_name"])
            
        elif(report_type == 3):
            groupingColumns= ['cat_name']

            tag_details = tag_details.values('tag_product_id').annotate(
                product_name = F('tag_product_id__product_name'),

                cat_name = F('tag_product_id__cat_id__cat_name'),

                sales_mode = F('tag_product_id__sales_mode'),

                total_tag_pcs=Sum('tag_pcs'),
                total_tag_gwt=Sum('tag_gwt'),
                total_tag_lwt=Sum('tag_lwt'),
                total_tag_nwt=Sum('tag_nwt'),
                total_tag_stn_wt=Sum('tag_stn_wt'),
                total_tag_dia_wt=Sum('tag_dia_wt')
            )
            non_tag_details = non_tag_details.values('id_lot_inward_detail__id_product').annotate(
                product_name = F('id_lot_inward_detail__id_product__product_name'),
                cat_name = F('id_lot_inward_detail__id_product__cat_id__cat_name'),
                total_tag_pcs=Sum('pieces'),
                total_tag_gwt=Sum('gross_wt'),
                total_tag_lwt=Sum('less_wt'),
                total_tag_nwt=Sum('net_wt'),
                total_tag_stn_wt=Sum('stone_wt'),
                total_tag_dia_wt=Sum('dia_wt')
            )
            final_result = []
            for tag in tag_details:
                product_name = tag['product_name']
                
                final_result.append({
                    'product_name': product_name,
                    'cat_name': tag['cat_name'],
                    'total_tag_pcs': tag['total_tag_pcs'],
                    'total_tag_gwt': tag['total_tag_gwt'] if int(tag['sales_mode']) == 1 else 0,
                    'total_tag_lwt': tag['total_tag_lwt'],
                    'total_tag_nwt': tag['total_tag_nwt'] if int(tag['sales_mode']) == 1 else 0,
                    'total_tag_stn_wt': tag['total_tag_stn_wt'],
                    'total_tag_dia_wt': tag['total_tag_dia_wt'],
                })
            for tag in non_tag_details:
                product_name = tag['product_name']
                
                final_result.append({
                    'product_name': product_name,
                    'cat_name': tag['cat_name'],
                    'total_tag_pcs': tag['total_tag_pcs'],
                    'total_tag_gwt': tag['total_tag_gwt'],
                    'total_tag_lwt': tag['total_tag_lwt'],
                    'total_tag_nwt': tag['total_tag_nwt'],
                    'total_tag_stn_wt': tag['total_tag_stn_wt'],
                    'total_tag_dia_wt': tag['total_tag_dia_wt'],
                })
            columns = get_reports_columns_template(request.user.pk,STOCK_INWARD_PRODUCT_REPORT_COLUMNS,request.data["path_name"])
        
        elif(report_type == 4):
            tag_details = tag_details.annotate(
                        cat_name=F('tag_product_id__cat_id__cat_name'),
                        product_name=F('tag_product_id__product_name'),
                        sales_mode = F('tag_product_id__sales_mode'),
                        lot_code=F('tag_lot_inward_details__lot_no__lot_code'),
                        design_name=F('tag_design_id__design_name'),
                        sub_design_name=F('tag_sub_design_id__sub_design_name'),
                        ).values(
                          'cat_name',
                          'product_name',
                          'design_name',
                          'sub_design_name',
                          'lot_code',
                          'tag_date',
                          'tag_code',
                          'tag_pcs',
                          'tag_gwt',
                          'tag_nwt',
                          'tag_lwt',
                          'tag_stn_wt',
                          'tag_dia_wt',
                        )
            final_result = []
            for tag in tag_details:                
                final_result.append({
                    **tag,
                    'date': format_date(tag['tag_date'])
                })
            columns = get_reports_columns_template(request.user.pk,TAG_INWARD_LIST,request.data["path_name"])
        elif(report_type == 5):
            groupingColumns = ['product_name']
            tag_details = tag_details.values('tag_product_id','size').annotate(
                cat_name=F('tag_product_id__cat_id__cat_name'),
                product_name = F('tag_product_id__product_name'),
                size_name = F('size__name'),
                total_tag_pcs=Sum('tag_pcs'),
                total_tag_gwt=Sum('tag_gwt'),
                total_tag_lwt=Sum('tag_lwt'),
                total_tag_nwt=Sum('tag_nwt'),
                total_tag_stn_wt=Sum('tag_stn_wt'),
                total_tag_dia_wt=Sum('tag_dia_wt')
            )
            final_result = []
            for tag in tag_details:
                product_name = tag['product_name']
                
                final_result.append({
                    'product_name': product_name,
                    'size_name': tag['size_name'],
                    'cat_name': tag['cat_name'],
                    'total_tag_pcs': tag['total_tag_pcs'],
                    'total_tag_gwt': tag['total_tag_gwt'],
                    'total_tag_lwt': tag['total_tag_lwt'],
                    'total_tag_nwt': tag['total_tag_nwt'],
                    'total_tag_stn_wt': tag['total_tag_stn_wt'],
                    'total_tag_dia_wt': tag['total_tag_dia_wt'],
                })
            columns = get_reports_columns_template(request.user.pk,STOCK_INWARD_PRODUCT_SIZE_REPORT_COLUMNS,request.data["path_name"])
        elif(report_type == 6):
            # tag_details = tag_details.values('tag_product_id','size').annotate(
            #     product_name = F('tag_product_id__product_name'),
            #     size_name = F('size__name'),
            #     total_tag_pcs=Sum('tag_pcs'),
            #     total_tag_gwt=Sum('tag_gwt'),
            #     total_tag_lwt=Sum('tag_lwt'),
            #     total_tag_nwt=Sum('tag_nwt'),
            #     total_tag_stn_wt=Sum('tag_stn_wt'),
            #     total_tag_dia_wt=Sum('tag_dia_wt')
            # )
            groupingColumns= ['product_name']

            branch = ",".join(map(str, branch))

            queryset = F"""SELECT
                        cat.cat_name,
                        pro.product_name,
                        des.design_name,
                        wt.weight_range_name,
                        COALESCE(SUM(tag.tag_pcs), 0) AS pieces,
                        COALESCE(SUM(tag.tag_gwt), 0) AS gross_wt,
                        COALESCE(SUM(tag.tag_nwt), 0) AS net_wt,
                        COALESCE(SUM(tag.tag_dia_wt), 0) AS dia_wt,
                        COALESCE(SUM(tag.tag_stn_wt), 0) AS stone_wt,
                        COALESCE(SUM(tag.tag_lwt), 0) AS lesswt
                    FROM erp_tagging tag 
                    LEFT JOIN erp_product pro ON pro.pro_id = tag.tag_product_id_id
                    LEFT JOIN erp_category cat ON cat.id_category = pro.cat_id_id
                    LEFT JOIN erp_design des ON des.id_design = tag.tag_design_id_id
                    LEFT JOIN erp_sub_design sub ON sub.id_sub_design = tag.tag_sub_design_id_id
                    LEFT JOIN erp_weight_range wt ON wt.id_product_id = tag.tag_product_id_id and wt.from_weight <= tag.tag_nwt and wt.to_weight >= tag.tag_nwt
                    WHERE wt.id_weight_range IS NOT NULL
                    and tag.tag_current_branch_id in ({branch})
                    AND tag.tag_date BETWEEN '{from_date}' AND '{to_date}'
                    GROUP BY tag.tag_product_id_id,wt.id_weight_range 
                    Order By tag.tag_product_id_id,wt.from_weight ASC"""
            result = generate_query_result(queryset)

            final_result = []
            for tag in result:
                product_name = tag['product_name']
                
                final_result.append({
                    'product_name': product_name,
                    'cat_name': tag['cat_name'],
                    'weight_range_name': tag['weight_range_name'],
                    'total_tag_pcs': tag['pieces'],
                    'total_tag_gwt': tag['gross_wt'],
                    'total_tag_lwt': tag['lesswt'],
                    'total_tag_nwt': tag['net_wt'],
                    'total_tag_stn_wt': tag['stone_wt'],
                    'total_tag_dia_wt': tag['dia_wt'],
                })
            columns = get_reports_columns_template(request.user.pk,STOCK_INWARD_PRODUCT_WEIGHT_RANGE_REPORT_COLUMNS,request.data["path_name"])
        else:
            tag_details = tag_details.values('tag_section_id','tag_design_id').annotate(
                section_name = F('tag_section_id__section_name'),
                sales_mode = F('tag_product_id__sales_mode'),
                product_name = F('tag_design_id__design_name'),
                total_tag_pcs=Sum('tag_pcs'),
                total_tag_gwt=Sum('tag_gwt'),
                total_tag_lwt=Sum('tag_lwt'),
                total_tag_nwt=Sum('tag_nwt'),
                total_tag_stn_wt=Sum('tag_stn_wt'),
                total_tag_dia_wt=Sum('tag_dia_wt')
            )
            non_tag_details = non_tag_details.values('id_lot_inward_detail__id_section','id_lot_inward_detail__id_design').annotate(
                section_name = F('id_lot_inward_detail__id_section__section_name'),
                product_name = F('id_lot_inward_detail__id_design__design_name'),
                total_tag_pcs=Sum('pieces'),
                total_tag_gwt=Sum('gross_wt'),
                total_tag_lwt=Sum('less_wt'),
                total_tag_nwt=Sum('net_wt'),
                total_tag_stn_wt=Sum('stone_wt'),
                total_tag_dia_wt=Sum('dia_wt')
            )
            final_result = []
            for tag in tag_details:
                section_name = tag['section_name']
                product_name = tag['product_name']
                final_result.append({
                    'section_name': section_name,
                    'product_name': product_name,
                    'total_tag_pcs': tag['total_tag_pcs'],
                    'total_tag_gwt': tag['total_tag_gwt'] if int(tag['sales_mode']) == 1 else 0,
                    'total_tag_lwt': tag['total_tag_lwt'],
                    'total_tag_nwt': tag['total_tag_nwt'] if int(tag['sales_mode']) == 1 else 0,
                    'total_tag_stn_wt': tag['total_tag_stn_wt'],
                    'total_tag_dia_wt': tag['total_tag_dia_wt'],
                })
            for tag in non_tag_details:
                section_name = tag['section_name']
                product_name = tag['product_name']
                final_result.append({
                    'section_name': section_name,
                    'product_name': product_name,
                    'total_tag_pcs': tag['total_tag_pcs'],
                    'total_tag_gwt': tag['total_tag_gwt'],
                    'total_tag_lwt': tag['total_tag_lwt'],
                    'total_tag_nwt': tag['total_tag_nwt'],
                    'total_tag_stn_wt': tag['total_tag_stn_wt'],
                    'total_tag_dia_wt': tag['total_tag_dia_wt'],
                })
            columns = get_reports_columns_template(request.user.pk,COUNTER_STOCK_INWARD_REPORT_COLUMNS,request.data["path_name"])

                
        paginator, page = pagination.paginate_queryset(final_result, request,None, columns)
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isReportGroupByReq'] = True
        filters_copy['isLotTypeFilterReq'] = True

        context = {
            'columns': COUNTER_STOCK_INWARD_REPORT_COLUMNS if report_type == 2 else  TAG_INWARD_LIST if report_type == 4 else columns,
            'actions': ACTION_LIST,
            'groupByOption': [ {'value': 1, 'label': 'Design'}, {'value': 2, 'label': 'Section'}, {'value': 3, 'label': 'Product'}, {'value': 4, 'label': 'Tag'}, {'value': 5, 'label': 'Size'}, {'value': 6, 'label': 'Weight Range'}],
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'groupingColumns':groupingColumns,
            'filters': filters_copy
        }

        return pagination.paginated_response(list(page), context)
    

class LotReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        report_type = int(request.data.get('group_by',1))
        response_data = []
        lot_details = ErpLotInwardDetails.objects.filter(lot_no__is_closed = False)
        if(id_branch):
                lot_details  = lot_details.filter(lot_no__id_branch__in = id_branch)

        if report_type == 1:
            lot_details =  lot_details.values('lot_no')
            lot_details = lot_details.annotate(
                lot_pcs=Sum('pieces', default=0),
                lot_gwt=Sum('gross_wt', default=0),
                lot_nwt=Sum('net_wt', default=0),
                lot_lwt=Sum('less_wt', default=0),
                lot_stn_wt=Sum('stone_wt', default=0),
                lot_dia_wt=Sum('dia_wt', default=0),
                tag_pcs=Sum('tagged_pcs', default=0),
                tag_gwt=Sum('tagged_gross_wt', default=0),
                tag_nwt=Sum('tagged_net_wt', default=0),
                tag_lwt=Sum('tagged_less_wt', default=0),
                tag_stn_wt=Sum('tagged_stone_wt', default=0),
                tag_dia_wt=Sum('tagged_dia_wt', default=0),
                balance_pcs=ExpressionWrapper(Sum('pieces', default=0) - Sum('tagged_pcs', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_gwt=ExpressionWrapper(Sum('gross_wt', default=0) - Sum('tagged_gross_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_nwt=ExpressionWrapper(Sum('net_wt', default=0) - Sum('tagged_net_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_lwt=ExpressionWrapper(Sum('less_wt', default=0) - Sum('tagged_less_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_stn_wt=ExpressionWrapper(Sum('stone_wt', default=0) - Sum('tagged_stone_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_dia_wt=ExpressionWrapper(Sum('dia_wt', default=0) - Sum('tagged_dia_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            ).values(
                'lot_no',
                'lot_no__lot_code',
                'lot_no__lot_date',
                'lot_pcs',
                'lot_gwt',
                'lot_nwt',
                'lot_lwt',
                'lot_stn_wt',
                'lot_dia_wt',
                'tag_pcs',
                'tag_gwt',
                'tag_nwt',
                'tag_lwt',
                'tag_stn_wt',
                'tag_dia_wt',
                'balance_pcs',
                'balance_gwt',
                'balance_nwt',
                'balance_lwt',
                'balance_stn_wt',
                'balance_dia_wt',
                'lot_no__is_closed'
            )
            for item in lot_details:
                if float(item['balance_pcs']) > 0 or float(item['balance_gwt']) > 0 :
                    item['lot_no__lot_date'] = format_date(item['lot_no__lot_date'])
                    item['is_active'] = item['lot_no__is_closed']
                    item['status_name'] = 'Open' if item['lot_no__is_closed']==0 else 'Closed'
                    item['is_editable'] = 1 if item['lot_no__is_closed']==0 else 0
                    item['pk_id'] = item['lot_no']
                    response_data.append(item)
        else:
            lot_details =  lot_details.values('id_lot_inward_detail')
            lot_details = lot_details.annotate(
                lot_pcs=Sum('pieces', default=0),
                lot_gwt=Sum('gross_wt', default=0),
                lot_nwt=Sum('net_wt', default=0),
                lot_lwt=Sum('less_wt', default=0),
                lot_stn_wt=Sum('stone_wt', default=0),
                lot_dia_wt=Sum('dia_wt', default=0),
                tag_pcs=Sum('tagged_pcs', default=0),
                tag_gwt=Sum('tagged_gross_wt', default=0),
                tag_nwt=Sum('tagged_net_wt', default=0),
                tag_lwt=Sum('tagged_less_wt', default=0),
                tag_stn_wt=Sum('tagged_stone_wt', default=0),
                tag_dia_wt=Sum('tagged_dia_wt', default=0),
                balance_pcs=ExpressionWrapper(Sum('pieces', default=0) - Sum('tagged_pcs', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_gwt=ExpressionWrapper(Sum('gross_wt', default=0) - Sum('tagged_gross_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_nwt=ExpressionWrapper(Sum('net_wt', default=0) - Sum('tagged_net_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_lwt=ExpressionWrapper(Sum('less_wt', default=0) - Sum('tagged_less_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_stn_wt=ExpressionWrapper(Sum('stone_wt', default=0) - Sum('tagged_stone_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_dia_wt=ExpressionWrapper(Sum('dia_wt', default=0) - Sum('tagged_dia_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            ).values(
                'lot_no',
                'lot_no__lot_code',
                'id_product__product_name',
                'lot_no__lot_date',
                'item_code',
                'id_lot_inward_detail',
                'lot_pcs',
                'lot_gwt',
                'lot_nwt',
                'lot_lwt',
                'lot_stn_wt',
                'lot_dia_wt',
                'tag_pcs',
                'tag_gwt',
                'tag_nwt',
                'tag_lwt',
                'tag_stn_wt',
                'tag_dia_wt',
                'balance_pcs',
                'balance_gwt',
                'balance_nwt',
                'balance_lwt',
                'balance_stn_wt',
                'balance_dia_wt',
                'lot_no__is_closed'
            )
            for item in lot_details:
                if float(item['balance_pcs']) > 0 or float(item['balance_gwt']) > 0 :
                    item['pk_id'] = item['lot_no']
                    item['lot_no__lot_date'] = format_date(item['lot_no__lot_date'])
                    item['lot_no__lot_code'] = f"{item['lot_no__lot_code']}-{str(item['item_code'])}"
                    item['is_active'] = item['lot_no__is_closed']
                    item['status_name'] = 'Open' if item['lot_no__is_closed']==0 else 'Closed'
                    item['is_editable'] = 1 if item['lot_no__is_closed']==0 else 0
                    item['pk_id'] = item['lot_no']
                    response_data.append(item)


        paginator, page = pagination.paginate_queryset(response_data, request,None,LOT_INWARD_REPORT_COLUMNS)
        columns = get_reports_columns_template(request.user.pk,LOT_INWARD_PRODUCT_REPORT_COLUMNS,request.data["path_name"])
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isReportGroupByReq'] = True
        context = {
            'columns': LOT_INWARD_REPORT_COLUMNS if report_type == 1 else columns,
            'actions': ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy,
            'groupingColumns': [] if report_type == 1 else ["id_product__product_name"],
            'groupByOption': [ {'value': 1, 'label': 'Lot'}, {'value': 2, 'label': 'Product'}],
        }

        return pagination.paginated_response(response_data, context)
    

class LotBalanceReportView(generics.GenericAPIView):

    permission_classes = [IsEmployee]

    def lot_balance_detail_query(self):

        sql = F"""
                select d.id_lot_inward_detail,concat(l.lot_code,'-',d.item_code) as lotno,p.product_name,date_format(l.lot_date,'%d-%m-%Y') as lot_date,des.design_name,d.gross_wt,d.pieces,
                
                (d.gross_wt - coalesce(d.tagged_gross_wt,0) - coalesce(merge.gross_wt,0) ) as balance_gwt,
                (d.pieces - coalesce(d.tagged_pcs,0) - coalesce(merge.pcs,0) ) as balance_pcs,

                if(d.status=0,1,0) as is_editable,if(d.status=0,'Pending','Completed') as is_active,d.id_lot_inward_detail as pk_id
                from erp_lot_inward_details d 

                left join (
                    select n.id_lot_inward_detail_id,sum(n.pieces) as non_tag_pcs,sum(n.gross_wt) as non_tag_gwt,
                    sum(n.net_wt) as non_tag_nwt
                    from erp_lot_non_tag_inward_details n
                group by n.id_lot_inward_detail_id) as nontag on nontag.id_lot_inward_detail_id = d.id_lot_inward_detail
                
                left join (select m.id_lot_inward_detail_id,coalesce(sum(m.pieces),0) as pcs,
                coalesce(sum(m.gross_wt),0) as gross_wt
                from erp_lot_merge_item_details m 
                group by m.id_lot_inward_detail_id) as merge on merge.id_lot_inward_detail_id = d.id_lot_inward_detail

                
                left join erp_product p on p.pro_id = d.id_product_id
                left join erp_design des on des.id_design = d.id_design_id
                left join erp_lot_inward l on l.lot_no = d.lot_no_id
                where d.id_lot_inward_detail is not null
                having balance_pcs > 0 or balance_gwt > 0
                order by l.lot_no desc
            """

        return sql

    def lot_balance_summary_query(self):

        sql = F"""
                select d.id_design_id,des.design_name,coalesce(sum(d.gross_wt) , 0) as gross_wt,
                coalesce(sum(d.pieces),0) as pieces,
                
                (coalesce(sum(d.gross_wt),0) - coalesce(sum(d.tagged_gross_wt),0) - coalesce(merge.gross_wt,0) ) as balance_gwt,
                (coalesce(sum(d.pieces),0) - coalesce(sum(d.tagged_pcs),0) - coalesce(merge.pcs,0) ) as balance_pcs

                from erp_lot_inward_details d 

                left join (
                    select d.id_design_id,sum(n.pieces) as non_tag_pcs,sum(n.gross_wt) as non_tag_gwt,
                    sum(n.net_wt) as non_tag_nwt
                    from erp_lot_non_tag_inward_details n
                    left join erp_lot_inward_details d on d.id_lot_inward_detail = n.id_lot_inward_detail_id
                group by d.id_design_id) as nontag on nontag.id_design_id = d.id_design_id
                
                left join (select d.id_design_id,coalesce(sum(m.pieces),0) as pcs,
                coalesce(sum(m.gross_wt),0) as gross_wt
                from erp_lot_merge_item_details m 
                left join erp_lot_inward_details d on d.id_lot_inward_detail = m.id_lot_inward_detail_id
                group by d.id_design_id) as merge on merge.id_design_id = d.id_design_id

                
                left join erp_product p on p.pro_id = d.id_product_id
                left join erp_design des on des.id_design = d.id_design_id
                left join erp_lot_inward l on l.lot_no = d.lot_no_id
                where d.id_lot_inward_detail is not null
                group by d.id_design_id
                having balance_pcs > 0 or balance_gwt > 0
                
            """

        return sql

    def post(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            group_by = int(request.data.get('group_by',1))
            report_type = int(request.data.get('report_type',1))
            if(group_by== 1):
                sql = self.lot_balance_detail_query()
                report_columns = LOT_BALANCE_REPORT_COLUMNS
            elif(group_by)== 2:
                if report_type == 1:
                    sql = self.lot_balance_summary_query()
                    report_columns = LOT_BALANCE_REPORT_SUMMARY_COLUMNS
                else:
                    sql = self.lot_balance_detail_query()
                    report_columns = LOT_BALANCE_REPORT_COLUMNS
            cursor.execute(sql)
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.append(field_value)
                response_data = report_data
            paginator, page = pagination.paginate_queryset(response_data, request,None,report_columns)
            columns = get_reports_columns_template(request.user.pk,report_columns,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = False
            filters_copy['isBranchFilterReq'] = False
            filters_copy['isReportGroupByReq'] = True
            filters_copy['isReportTypeReq'] = True
            action_list_copy = ACTION_LIST.copy()
            action_list_copy['is_print_req'] = True
            action_list_copy['is_edit_req'] = False
            action_list_copy['is_delete_req'] = False
            context = {
                'columns': columns,
                'groupByOption': [ {'value': 1, 'label': 'Lot'}, {'value': 2, 'label': 'Design'}],
                'actions': action_list_copy,
                'page_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters': filters_copy,
                'groupingColumns': ["design_name"] if (group_by==2 and report_type==2) else  [],
            }

            return pagination.paginated_response(list(page), context)


class SalesItemReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        customer = request.data.get('customer')
        product = request.data.get('product')
        design = request.data.get('design')
        metal = request.data.get('id_metal')
        from_wt = request.data.get('from_wt')
        to_wt = request.data.get('to_wt')

        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status = 1)

        if customer:
            queryset = queryset.filter(invoice_bill_id__id_customer = customer)

        if product:
            queryset = queryset.filter(id_product = product)

        if design:
            queryset = queryset.filter(id_design = design)

        if metal:
            queryset = queryset.filter(id_product__id_metal = metal)

        if from_wt and to_wt:
            queryset = queryset.filter(gross_wt__range=(from_wt, to_wt))

        if(bill_setting_type == 1 or bill_setting_type == 0):
            queryset = queryset.filter(invoice_bill_id__setting_bill_type = bill_setting_type)

        if(id_branch):
            queryset  = queryset.filter(invoice_bill_id__id_branch__in = id_branch)


        if from_date and to_date:
            queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

        paginator, page = pagination.paginate_queryset(queryset, request,None, SALES_DETAIL_REPORT)

        data = ErpInvoiceSalesDetailsSerializer(page,many=True).data

        print(data)


        response_data=[]

        for item, instance in zip(data, queryset):
            deposit_amount=0
            advance_adj_amount= 0

            inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

            inv_serializer = ErpInvoiceSerializer(inv_queryset).data
            
            inv_data = get_invoice_no(inv_serializer)

            sales_details = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id=inv_queryset.erp_invoice_id)
            sale_serializer = ErpInvoiceSalesDetailsSerializer(sales_details, many=True,context={'stone_details': True, 'charges_details': True})
            purchase_details = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id=inv_queryset.erp_invoice_id)
            purchase_serializer = ErpInvoiceOldMetalDetailsSerializer(purchase_details, many=True)
            inv_payment_details = ErpInvoicePaymentModeDetail.objects.filter(invoice_bill_id=inv_queryset.erp_invoice_id)
            payment_details_serializer = ErpInvoicePaymentModeDetailSerializer(inv_payment_details, many=True)
            return_details = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id=inv_queryset.erp_invoice_id)
            return_details_serializer = ErpInvoiceSalesReturnSerializer(return_details,many=True)
            deposit_bill  = None if inv_queryset.due_amount > 0 else inv_queryset.deposit_bill.first()
            advance_adj_bill  =inv_queryset.advance_adj_invoices.all()
            if(advance_adj_bill):
                for adj_bill in advance_adj_bill:
                    advance_adj_amount += float(adj_bill.adj_amount)
            if(deposit_bill):
                deposit_amount = format(deposit_bill.amount, '.2f')
            customer_address = CustomerAddress.objects.filter(customer=inv_queryset.id_customer).first()
            address = (
                f"{customer_address.line1 or ''} {customer_address.line2 or ''} {customer_address.line3 or ''}".strip()
                if customer_address else None
            )
            response_data.append({
                **inv_serializer,
                'invoice_date': format_date(inv_serializer['invoice_date']),
                **item,
                **inv_data,
                'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                "sales_details":sale_serializer.data,
                "sales_return_details":return_details_serializer.data,
                "purchase_details": purchase_serializer.data,
                "payment_details":payment_details_serializer.data,
                "deposit_amount": deposit_amount,
                "advance_adj_amount": advance_adj_amount,
                "emp_name": inv_queryset.id_employee.firstname,
                "customer_address":address,
            })
        columns = get_reports_columns_template(request.user.pk,SALES_DETAIL_REPORT,request.data["path_name"])
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isReportTypeReq'] = True
        context={
            'columns':columns,
            'actions':ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':filters_copy,
            }
        return pagination.paginated_response(response_data, context)


class DigiGoldReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_scheme = request.data.get('id_scheme')
        id_customer = request.data.get('customer')

        id_scheme = id_scheme if id_scheme != '' else None

        queryset = Payment.objects.all()

        if id_customer:
            queryset = queryset.filter(id_scheme_account__id_customer=id_customer)
        else:
            if from_date and to_date:
                queryset = queryset.filter(date_payment__range=[from_date, to_date])
            if id_branch is not None:
                queryset = queryset.filter(id_branch__in=id_branch)
            if id_scheme is not None:
                queryset = queryset.filter(id_scheme=id_scheme)

        serializer = PaymentSerializer(queryset, many=True)
        output = []
        all_modes_set = set()

        for index, data in enumerate(serializer.data):
            instance = {}
            sch_acnt_obj = SchemeAccount.objects.filter(id_scheme_account=data['id_scheme_account']).first()
            customer_obj = Customers.objects.filter(id_customer=sch_acnt_obj.id_customer.pk).first()
            scheme_obj = Scheme.objects.filter(scheme_id=data['id_scheme']).first()
            maturity_days = scheme_obj.digi_maturity_days

            
            mode_details = PaymentModeDetail.objects.filter(id_pay=data['id_payment']).select_related('payment_mode')
            mode_wise_amounts = {}
            for m in mode_details:
                if m.payment_mode:
                    mode_name = m.payment_mode.mode_name
                    all_modes_set.add(mode_name)
                    mode_wise_amounts[mode_name] = mode_wise_amounts.get(mode_name, Decimal('0.00')) + m.payment_amount

            if scheme_obj.scheme_type == 2:
                today = date.today()
                days_elapsed = (today - sch_acnt_obj.start_date).days
                interest_setting = SchemeDigiGoldInterestSettings.objects.filter(
                    scheme=scheme_obj.pk,
                    from_day__lte=days_elapsed,
                    to_day__gte=days_elapsed
                ).first()
                interest_percentage = 0
                if interest_setting:
                    interest_percentage = interest_setting.interest_percentage

                maturity_date = ""
                if sch_acnt_obj.start_date and maturity_days:
                    maturity_date = sch_acnt_obj.start_date + timedelta(days=maturity_days)

                total_weight = Decimal(data['metal_weight']) + Decimal(data['bonus_metal_weight'])

                instance.update({
                    'sno': index + 1,
                    'sch_pk_id': sch_acnt_obj.id_scheme_account,
                    'account_no': sch_acnt_obj.scheme_acc_number,
                    "name": customer_obj.firstname,
                    "mobile": customer_obj.mobile,
                    "date": format_date(data['date_payment']),
                    "paid_amnt": data['payment_amount'],
                    "rate": data['metal_rate'],
                    "weight": data['metal_weight'],
                    "bonus_weight": data['bonus_metal_weight'],
                    "total_weight": total_weight,
                    'curr_period_and_interest': f"{interest_setting.from_day}-{interest_setting.to_day}({interest_setting.interest_percentage}%)" if interest_setting else "",
                    'joined_on': format_date(sch_acnt_obj.start_date),
                    "maturity_date": format_date(maturity_date) if maturity_date else "",
                })

                
                for mode in mode_wise_amounts:
                    instance[mode] = mode_wise_amounts[mode]

                output.append(instance)

        
        all_modes_set = set()
        for row in output:
            for key in row:
                if key not in [col['accessor'] for col in DIGIGOLD_REPORT_COLUMNS] \
                   and key != 'sch_pk_id' and row[key] != '':
                    all_modes_set.add(key)
        
        # mode_columns = [
        #     {
        #         'accessor': mode,
        #         'Header': mode,
        #         'is_total_req': True,
        #         'text_align': 'right',
        #         'decimal_places': 2,
        #         'is_money_format': True
        #     }
        #     for mode in sorted(all_modes_set)
        # ]
        # DIGIGOLD_REPORT_COLUMNS.extend(mode_columns)
        for mode in sorted(all_modes_set): 
            DIGIGOLD_REPORT_COLUMNS.append({
                'accessor': mode,
                'Header': mode,
                'is_total_req': True,
                'text_align': 'right',
                'decimal_places': 2,
                'is_money_format': True,
            })
        paginator, page = pagination.paginate_queryset(output, request, None, DIGIGOLD_REPORT_COLUMNS)
        columns = get_reports_columns_template(request.user.pk,DIGIGOLD_REPORT_COLUMNS,request.data["path_name"])
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isSchemeFilterReq'] = True
        filters_copy['isCustomerFilterReq'] = True
        action_list_copy = ACTION_LIST.copy()
        action_list_copy['is_delete_req'] = False
        action_list_copy['is_edit_req'] = False

        context = {
            'columns': columns,
            'actions': action_list_copy,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy,
        }

        return pagination.paginated_response(output, context)
    

class DigiGoldAccountWiseReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_scheme = request.data.get('id_scheme')
        id_customer = request.data.get('customer')
    
        id_scheme = id_scheme if id_scheme != '' else None

        queryset = Payment.objects.filter(id_scheme__scheme_type=2)

        if id_customer:
            # If customer is provided, ignore all other filters
            queryset = queryset.filter(id_scheme_account__id_customer=id_customer)
        else:
            if from_date and to_date:
                queryset = queryset.filter(date_payment__range=[from_date, to_date])

            if id_branch is not None:
                queryset = queryset.filter(id_branch__in=id_branch)

            if id_scheme is not None:
                queryset = queryset.filter(id_scheme=id_scheme)

        serializer = PaymentSerializer(queryset, many=True)

        scheme_agg = defaultdict(lambda: {
            'sno': 0,
            'account_no': '',
            'customer_name': '',
            'mobile': '',
            'joined_on': '',
            'maturity_date': '',
            'paid_amnt': Decimal('0.000'),
            'rate': Decimal('0.000'),
            'weight': Decimal('0.000'),
            'bonus_weight': Decimal('0.000'),
            'total_weight': Decimal('0.000'),
            'payments': []
        })
        # mode_keys_set = set()
        for index, data in enumerate(serializer.data):
            scheme_account_id = data['id_scheme_account']
            sch_acnt_obj = SchemeAccount.objects.filter(id_scheme_account=scheme_account_id).first()
            if not sch_acnt_obj:
                continue

            customer_obj = Customers.objects.filter(id_customer=sch_acnt_obj.id_customer.pk).first()
            scheme_obj = Scheme.objects.filter(scheme_id=data['id_scheme']).first()
            maturity_days = scheme_obj.digi_maturity_days if scheme_obj else 0

            metal_weight = Decimal(data['metal_weight'])
            bonus_weight = Decimal(data['bonus_metal_weight'])
            total_weight = metal_weight + bonus_weight

            maturity_date = ""
            if sch_acnt_obj.start_date and maturity_days:
                maturity_date = sch_acnt_obj.start_date + timedelta(days=maturity_days)
            
            account_key = scheme_account_id
            account_data = scheme_agg[account_key]
            account_data['sno'] = index + 1
            account_data['sch_pk_id'] = sch_acnt_obj.id_scheme_account
            account_data['account_no'] = sch_acnt_obj.scheme_acc_number,
            account_data['acc_name'] = sch_acnt_obj.account_name
            account_data['customer_name'] = customer_obj.firstname if customer_obj else ""
            account_data['mobile'] = customer_obj.mobile if customer_obj else ""
            account_data['joined_on'] = format_date(sch_acnt_obj.start_date)
            
            # account_data['maturity_date'] = format_date(maturity_date)
            # account_data['status'] = 'Matured' if(date.today() >= maturity_date) else 'Active'
            # account_data['status_color'] = 'warning' if(date.today() >= maturity_date) else 'success'
            
            if maturity_date:
                account_data['status'] = 'Matured' if date.today() >= maturity_date else 'Active'
                account_data['status_color'] = 'warning' if date.today() >= maturity_date else 'success'
                account_data['maturity_date'] = format_date(maturity_date)
            else:
                account_data['status'] = ''
                account_data['status_color'] = ''
                account_data['maturity_date'] = ''

            account_data['paid_amnt'] += Decimal(data['payment_amount'])
            account_data['rate'] += Decimal(data['metal_rate'])
            account_data['weight'] += metal_weight
            account_data['bonus_weight'] += bonus_weight
            account_data['total_weight'] += total_weight
            account_data['payments'].append(data)
            
            # mode_details = PaymentModeDetail.objects.filter(id_pay=data['id_payment']).select_related('payment_mode')
            # for m in mode_details:
            #     if m.payment_mode:
            #         mode_name = m.payment_mode.mode_name
            #         mode_keys_set.add(mode_name)
            #         if mode_name not in account_data:
            #             account_data[mode_name] = Decimal('0.00')
            #         account_data[mode_name] += m.payment_amount

        output = list(scheme_agg.values())
        
        # for row in output:
        #     for key in row:
        #         if key not in [col['accessor'] for col in ACCOUNT_DIGIGOLD_REPORT_COLUMNS] \
        #            and key != 'pk_id' and row[key] != '' and key != 'payments' and row[key] != '' and key != 'rate' and row[key] != '' and key != 'status_color' and row[key] != '':
        #             mode_keys_set.add(key)
                    
        # for mode in sorted(mode_keys_set):
        #     ACCOUNT_DIGIGOLD_REPORT_COLUMNS.append({
        #         'accessor': mode,
        #         'Header': mode,
        #         'is_total_req': True,
        #         'text_align': 'right',
        #         'decimal_places': 2,
        #         'is_money_format': True,
        #     })
        paginator, page = pagination.paginate_queryset(output, request, None, ACCOUNT_DIGIGOLD_REPORT_COLUMNS)
        columns = get_reports_columns_template(request.user.pk,ACCOUNT_DIGIGOLD_REPORT_COLUMNS,request.data["path_name"])
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isSchemeFilterReq'] = True
        filters_copy['isCustomerFilterReq'] = True
        action_list_copy = ACTION_LIST.copy()
        action_list_copy['is_delete_req'] = False
        action_list_copy['is_edit_req'] = False
        context = {
            'columns': columns,
            'actions': action_list_copy,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy,
        }

        return pagination.paginated_response(output, context)
    

class EstimateReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        item_type = request.data.get('optional_type',3)
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if item_type == 1:
                queryset = ErpEstimationSalesDetails.objects.all()

                if(id_branch):
                    queryset  = queryset.filter(estimation_id__id_branch__in = id_branch)

                if from_date and to_date:
                    queryset = queryset.filter(estimation_id__entry_date__range=[from_date, to_date])

                paginator, page = pagination.paginate_queryset(queryset, request,None,ESTIMATE_SALES_REPORT)

                data = ErpEstimationSalesDetailsSerializer(page,many=True).data

                response_data=[]

                for item, instance in zip(data, queryset):

                    if instance.tag_id:
                        if instance.tag_id.tag_status.pk == 2:
                            item['row_colour'] = "rgb(72 14 209)"

                    if instance.invoice_sale_item_id:

                        inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_sale_item_id.invoice_bill_id.erp_invoice_id)

                        inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                        
                        inv_data = get_invoice_no(inv_serializer)



                        response_data.append({
                            **inv_serializer,
                            'invoice_date': format_date(inv_serializer['invoice_date']),
                            **item,
                            **inv_data,
                            "status" : "UnSold" if instance.status == 0 else "Sold" if instance.status == 1 else "Returned",
                            'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                            'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                            'section_name': instance.id_section.section_name if instance.id_section else None,
                            'est_no': instance.estimation_id.est_no if instance.estimation_id else None,
                            'entry_date': format_date(instance.estimation_id.entry_date) if instance.estimation_id else None,
                            'emp_name': (instance.ref_emp_id.firstname) if instance.ref_emp_id else None,
                            'customer_name': instance.estimation_id.id_customer.firstname if instance.estimation_id.id_customer else None,
                            'customer_mobile': instance.estimation_id.id_customer.mobile if instance.estimation_id.id_customer else None,

                        })
                    else:
                        response_data.append({
                            "invoice_no": "",
                            'invoice_date': "",
                            **item,
                            "status" : "UnSold" if instance.status == 0 else "Sold" if instance.status == 1 else "Returned",
                            'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                            'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                            'section_name': instance.id_section.section_name if instance.id_section else None,
                            'est_no': instance.estimation_id.est_no if instance.estimation_id else None,
                            'entry_date': format_date(instance.estimation_id.entry_date) if instance.estimation_id else None,
                            'emp_name': (instance.ref_emp_id.firstname) if instance.ref_emp_id else None,
                            'customer_name': instance.estimation_id.id_customer.firstname if instance.estimation_id.id_customer else None,
                            'customer_mobile': instance.estimation_id.id_customer.mobile if instance.estimation_id.id_customer else None,
                        })

            elif item_type == 2:
                queryset = ErpEstimationOldMetalDetails.objects.all()

                if(id_branch):
                    queryset  = queryset.filter(estimation_id__id_branch__in = id_branch)


                if from_date and to_date:
                    queryset = queryset.filter(estimation_id__entry_date__range=[from_date, to_date])


                paginator, page = pagination.paginate_queryset(queryset, request,None,ESTIMATE_PURCHASE_REPORT)

                data = ErpEstimationOldMetalDetailsSerializer(page,many=True).data

                print(data)


                response_data=[]

                for item, instance in zip(data, queryset):

                    if instance.invoice_old_metal_item_id:

                        inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_old_metal_item_id.invoice_bill_id.erp_invoice_id)

                        inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                        
                        inv_data = get_invoice_no(inv_serializer)

                        response_data.append({
                            **inv_serializer,
                            'invoice_date': format_date(inv_serializer['invoice_date']),
                            **item,
                            **inv_data,
                            "status" : "UnSold" if instance.status == 0 else "Sold" if instance.status == 1 else "Returned",
                            # 'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                            # 'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                            'est_no': instance.estimation_id.est_no if instance.estimation_id else None,
                            'entry_date': format_date(instance.estimation_id.entry_date) if instance.estimation_id else None,
                            'emp_name': instance.estimation_id.id_employee.firstname if instance.estimation_id.id_employee else None,
                            'customer_name': instance.estimation_id.id_customer.firstname if instance.estimation_id.id_customer else None,
                            'customer_mobile': instance.estimation_id.id_customer.mobile if instance.estimation_id.id_customer else None,
                        })
                    else:
                        response_data.append({
                            "invoice_no": "",
                            'invoice_date': "",
                            **item,
                            'est_no': instance.estimation_id.est_no if instance.estimation_id else None,
                            'entry_date': format_date(instance.estimation_id.entry_date) if instance.estimation_id else None,
                            'emp_name': instance.estimation_id.id_employee.firstname if instance.estimation_id.id_employee else None,
                            'customer_name': instance.estimation_id.id_customer.firstname if instance.estimation_id.id_customer else None,
                            'customer_mobile': instance.estimation_id.id_customer.mobile if instance.estimation_id.id_customer else None,
                        })

            elif item_type == 3:
                queryset = ErpEstimationSalesReturnDetails.objects.all()

                if(id_branch):
                    queryset  = queryset.filter(estimation_id__id_branch__in = id_branch)


                if from_date and to_date:
                    queryset = queryset.filter(estimation_id__entry_date__range=[from_date, to_date])


                paginator, page = pagination.paginate_queryset(queryset, request,None,ESTIMATE_SALES_RETURN_REPORT)

                data = ErpEstimationSalesReturnSerializer(page,many=True).data

                response_data=[]

                for item, instance in zip(data, queryset):

                    if instance.invoice_return_id:

                        inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_return_id.invoice_bill_id.erp_invoice_id)

                        inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                        
                        inv_data = get_invoice_no(inv_serializer)

                        response_data.append({
                            **inv_serializer,
                            'invoice_date': format_date(inv_serializer['invoice_date']),
                            **item,
                            **inv_data,
                            "status" : "sold",
                            'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                            'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
                            'est_no': instance.estimation_id.est_no if instance.estimation_id else None,
                            'entry_date': format_date(instance.estimation_id.entry_date) if instance.estimation_id else None,
                            'emp_name': instance.estimation_id.id_employee.firstname if instance.estimation_id.id_employee else None,
                            'customer_name': instance.estimation_id.id_customer.firstname if instance.estimation_id.id_customer else None,
                            'customer_mobile': instance.estimation_id.id_customer.mobile if instance.estimation_id.id_customer else None,
                        })
                    else:
                        response_data.append({
                            "invoice_no": "",
                            'invoice_date': "",
                            **item,
                            "status" : "Unsold",
                            'est_no': instance.estimation_id.est_no if instance.estimation_id else None,
                            'entry_date': format_date(instance.estimation_id.entry_date) if instance.estimation_id else None,
                            'emp_name': instance.estimation_id.id_employee.firstname if instance.estimation_id.id_employee else None,
                            'customer_name': instance.estimation_id.id_customer.firstname if instance.estimation_id.id_customer else None,
                            'customer_mobile': instance.estimation_id.id_customer.mobile if instance.estimation_id.id_customer else None,
                        })


            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isOpionalFilterReq'] = True

            context={
                'columns': ESTIMATE_SALES_REPORT if item_type == 1 else ESTIMATE_PURCHASE_REPORT if item_type == 2 else ESTIMATE_SALES_RETURN_REPORT,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
                'optionalType':[
                        { "value": 1, "label": "Sales" },
                        { "value": 2, "label": "Purchase" },
                        { "value": 3, "label": "Sales Return" },
                ]
                }
                
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class StockApprovalPendingReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            sql = f"""
                    select s.trans_code,
                    if(s.stock_issue_to=1,'Employee',if(s.stock_issue_to=2,'Customer','Supplier')) as issue_to,
                    if(s.stock_issue_to=1,e.firstname,if(s.stock_issue_to = 2,concat(c.firstname,'-',c.mobile),concat(k.supplier_name,'-',k.mobile_no))) as issue_to_name,
                    tag.tag_code,prod.product_name,stk.name as tagstatus,date_format(s.approved_date,'%d-%m-%Y') as trans_date,
                    tag.tag_pcs as pcs,tag.tag_gwt as gross_wt,tag.tag_nwt as net_wt,i.name as stock_issue_type,
                    emp.firstname as created_by,approved_emp.firstname as approved_emp,datediff(current_date(),s.approved_date) as no_of_days
                    from erp_stock_transfer s 
                    left join erp_transfer_tag_item t on t.stock_transfer_id = s.id_stock_transfer
                    left join erp_tagging tag on tag.tag_id = t.tag_id_id
                    left join erp_stock_issue_type i on i.id_stock_issue_type = s.stock_issue_type_id
                    left join erpemployee e on e.id_employee = s.id_employee_id
                    left join customers c on c.id_customer = s.id_customer_id
                    left join erp_supplier k on k.id_supplier = s.supplier_id
                    left join erp_product prod on prod.pro_id = tag.tag_product_id_id
                    left join erp_stock_status_master stk on stk.id_stock_status = tag.tag_status_id
                    left join erpemployee emp on emp.id_employee = s.created_by_id
                    left join erpemployee approved_emp on approved_emp.id_employee = s.approved_by_id
                    where s.stock_issue_type_id is not null and tag.tag_status_id = 8 and s.approved_date is not null
                """
            cursor.execute(sql)
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.append(field_value)
                response_data = report_data
            paginator, page = pagination.paginate_queryset(response_data, request,None,APPROVAL_PENDING_REPORT_COLUMNS)
            columns = get_reports_columns_template(request.user.pk,APPROVAL_PENDING_REPORT_COLUMNS,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isReportGroupByReq'] = True
            context = {
                'columns': columns,
                'actions': ACTION_LIST,
                'page_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy,
            }

            return pagination.paginated_response(response_data, context)
        
class LiablitySupplierPaymentReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        entries = (
            ErpLiablityEntry.objects
            .filter(supplier__is_vendor=6)
            .values('supplier_id', 'supplier__supplier_name')
            .annotate(
                total_amount=Sum('amount'),
                total_paid_amount=Sum('paid_amount'),
                total_balance=ExpressionWrapper(
                    Sum(F('amount') - F('paid_amount')),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        )
        paginator, page = pagination.paginate_queryset(list(entries), request,None,LIABLITY_SUPPLIER_PAYMENT_REPORT_COLUMNS)
        columns = get_reports_columns_template(request.user.pk,LIABLITY_SUPPLIER_PAYMENT_REPORT_COLUMNS,request.data["path_name"])
        context = {
            'columns': columns,
            'actions': ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
        }
        return pagination.paginated_response(list(entries), context)

       
class TaggedStockSQLAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        product = request.data.get('product')
        design = request.data.get('design')
        sub_design = request.data.get('subDesign')
        purity = request.data.get('purity')
        supplier = request.data.get('supplier')
        metal = request.data.get('id_metal')
        from_wt = request.data.get('from_wt')
        to_wt = request.data.get('to_wt')
        tag_code = request.data.get('tag_code')
        lot = request.data.get('lot')
        report_type = int(request.data.get('group_by',1))
        searchText = request.query_params.get('search')
        filters = ''

        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            id_branch = ",".join(map(str, id_branch))
            if product:
                filters += f' and tag.tag_product_id_id = {product} '
            if design:
                filters += f' and tag.tag_design_id_id = {design} '
            if sub_design:
                filters += f' and tag.tag_sub_design_id_id = {sub_design} '
            if purity:
                filters += f' and tag.tag_purity_id_id = {purity} '
            if supplier:
                filters += f' and tag.id_supplier_id = {supplier} '
            if metal:
                filters += f' and product.id_metal_id = {metal} '
            if tag_code:
                filters += f' and  tag.tag_code = "{tag_code}" '
            if from_wt and to_wt:
                filters += f' and tag.tag_nwt BETWEEN {from_wt} AND {to_wt} '
            elif from_wt:
                filters += f' and tag.tag_nwt >= {from_wt} '
            elif to_wt:
                filters += f' and tag.tag_nwt <= {to_wt} '
            order_by = "ORDER BY tag.tag_id DESC"
            groupingColumns = []
            if report_type == 2:
                groupingColumns = ['supplier_name']
                order_by = "ORDER BY sup.supplier_name ASC, tag.tag_id DESC"
            elif report_type == 3:
                groupingColumns = ['product_name']
                order_by = "ORDER BY product.product_name ASC, tag.tag_id DESC"
            elif report_type == 4:
                groupingColumns = ['design_name']
                order_by = "ORDER BY des.design_name ASC, tag.tag_id DESC"
            elif report_type == 5:
                groupingColumns = ['product_name','design_name']
                order_by = "ORDER BY product.product_name ASC,des.design_name ASC, tag.tag_id DESC"
            elif report_type == 6:
                groupingColumns = ['product_name','size_name']
                order_by = "ORDER BY product.product_name ASC,size.value ASC, tag.tag_id DESC"
            if lot:
                filters += f'and lot.lot_no = {lot}'

            if 'search' in request.query_params and request.query_params['search'] != 'undefined' and request.query_params['search'] != 'null':
                filters += f" and (product.product_name LIKE '%{searchText}%' or tag.tag_code LIKE '%{searchText}%' or des.design_name LIKE '%{searchText}%') "

            page = int(request.data.get("page", 1))
            records_per_page = int(request.data.get("records", 50))  # default to 50 if not passed
            offset = (page - 1) * records_per_page

            query = F"""SELECT tag.tag_code,tag.old_tag_code,product.product_name,des.design_name,subdes.sub_design_name,
                    lot.lot_code as lot_code,b.name as current_branch,sup.supplier_name as supplier_name,tag.tag_id,
                    tag.tag_pcs,tag.tag_gwt, tag.tag_lwt, tag.tag_nwt,pur.purity as tag_purity,
                    tag.tag_stn_wt, tag.tag_dia_wt, tag.tag_other_metal_wt,tag.tag_wastage_percentage,
                    tag.tag_wastage_wt, tag.tag_mc_type, tag.tag_mc_value,tag.tag_sell_rate,tag.tag_item_cost,
                    tag.tag_huid2, tag.tag_huid, DATE_FORMAT(tag.tag_date, '%d-%m-%Y') as tag_date,m.metal_name,
                    tag.tag_huid2,sec.section_name,CONCAT(DATEDIFF(CURDATE(), tag.tag_date), ' days') AS stock_age,IFNULL(size.name,'') as size_name
                    FROM erp_tagging tag
                    LEFT JOIN erp_lot_inward_details lot_det ON  lot_det.id_lot_inward_detail = tag.tag_lot_inward_details_id
                    LEFT JOIN erp_lot_inward lot ON lot.lot_no = lot_det.lot_no_id
                    LEFT JOIN erp_tag_log_details tl ON tl.tag_id_id  = tag.tag_id and tl.to_branch_id in ({id_branch})
                    LEFT JOIN erp_tag_log_details tl2 ON tl2.tag_id_id  = tag.tag_id and tl2.id_tag_log > tl.id_tag_log and tl2.date <= ( "{to_date}")
                    LEFT JOIN erp_product product ON product.pro_id = tag.tag_product_id_id
                    LEFT JOIN erp_design des ON des.id_design = tag.tag_design_id_id
                    LEFT JOIN erp_sub_design subdes ON subdes.id_sub_design = tag.tag_sub_design_id_id
                    LEFT JOIN erp_supplier sup ON sup.id_supplier = tag.id_supplier_id
                    LEFT JOIN erp_purity pur ON pur.id_purity = tag.tag_purity_id_id
                    LEFT JOIN branch b ON b.id_branch = tag.tag_current_branch_id
                    LEFT JOIN erp_section sec ON sec.id_section = tag.tag_section_id_id
                    LEFT JOIN metal m ON m.id_metal = product.id_metal_id
                    LEFT JOIN erp_size size ON size.id_size = tag.size_id
                    WHERE  tl2.tag_id_id IS NULL and (tl.id_stock_status_id = 1 or tl.id_stock_status_id = 5)  and tl.date <= ( "{to_date}")
                    {filters}
                    {order_by}
                    LIMIT {records_per_page} OFFSET {offset}
                    """
            print(query)

            result = generate_query_result(query)

            count_query = f"""
                        SELECT COUNT(*) as total
                        FROM erp_tagging tag
                        LEFT JOIN erp_lot_inward_details lot_det ON  lot_det.id_lot_inward_detail = tag.tag_lot_inward_details_id
                        LEFT JOIN erp_lot_inward lot ON lot.lot_no = lot_det.lot_no_id
                        LEFT JOIN erp_product product ON product.pro_id = tag.tag_product_id_id
                        LEFT JOIN erp_tag_log_details tl ON tl.tag_id_id  = tag.tag_id and tl.to_branch_id in ({id_branch})
                        LEFT JOIN erp_tag_log_details tl2 ON tl2.tag_id_id  = tag.tag_id and tl2.id_tag_log > tl.id_tag_log and tl2.date <= ( "{to_date}")
                        WHERE  tl2.tag_id_id IS NULL and (tl.id_stock_status_id = 1 or tl.id_stock_status_id = 5)  and tl.date <= ( "{to_date}")
                        {filters}
                        ORDER BY tag.tag_id DESC
                        """
            count_result = generate_query_result(count_query)
            total_records = count_result[0]['total']
            total_pages = (total_records + records_per_page - 1) // records_per_page 

            columns = get_reports_columns_template(request.user.pk,AVAILABLE_TAG_REPORT_LIST,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isProductFilterReq'] = True
            filters_copy['isTagCodeFilterReq'] = True
            filters_copy['isDeignFilterReq'] = True
            filters_copy['isSubDeignFilterReq'] = True
            filters_copy['isPurityFilterReq'] = True
            filters_copy['isSupplierFilterReq'] = True
            filters_copy['isLotFilterReq'] = True
            #filters_copy['isMcTypeFilterReq'] = True
            #filters_copy['isMcValueFilterReq'] = True
            #filters_copy['isVaPercentFilterReq'] = True
            #filters_copy['isVaFromToFilterReq'] = True
            filters_copy['isGwtFromToFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            filters_copy['isReportGroupByReq'] = True
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':total_records,
                'total_pages': total_pages,
                'current_page': page,
                'is_filter_req':True,
                'filters':filters_copy,
                'groupingColumns': groupingColumns,
                'groupByOption': [ {'value': 2, 'label': 'Supplier'}, {'value': 3, 'label': 'Product'}, {'value': 4, 'label': 'Design'},{'value': 5, 'label': 'Product and Design'},{'value': 6, 'label': 'Product and Size'}],
                }
            
            return pagination.paginated_response(result,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class StockApprovalAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        type = int(request.data.get('type',0))
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        transfer_from = request.data.get('transfer_from')
        #transfer_to = request.data.get('transfer_to')
        item_type = request.data.get('item_type')


        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpStockTransfer.objects.filter(trans_to_type = 2)

            if(transfer_from):
                queryset  = queryset.filter(transfer_from__in = transfer_from)
         
            if(item_type):            
                queryset  = queryset.filter(transfer_type = item_type)

            if from_date and to_date and type == 2:
                queryset = queryset.filter(approved_date__range=[from_date, to_date])

            if from_date and to_date and type == 1:
                queryset = queryset.filter(downloaded_date__range=[from_date, to_date])
            if from_date and to_date and type == 0:
                queryset = queryset.filter(trans_date__range=[from_date, to_date])

            queryset = queryset.order_by('id_stock_transfer')


            paginator, page = pagination.paginate_queryset(queryset, request,None,STOCK_TRANSFER_REPORT)

            data = ErpStockTransferSerializer(page,many=True).data

            response_data=[]

            for item, instance in zip(data, queryset):

                if(instance.transfer_type == 1):
        
                    transfer_list = ErpTagTransfer.objects.filter(stock_transfer=instance).annotate(
                        product_name=F('tag_id__tag_product_id__product_name'),
                        design_name=F('tag_id__tag_design_id__design_name'),
                        sub_design_name=F('tag_id__tag_sub_design_id__sub_design_name'),
                        issue_type=F('stock_transfer__stock_issue_type__name'),
                        tag_code=F('tag_id__tag_code'),
                        pieces=F('tag_id__tag_pcs'),
                        gross_wt=F('tag_id__tag_gwt'),
                        net_wt=F('tag_id__tag_nwt'),
                        less_wt=F('tag_id__tag_lwt'),
                        stn_wt=F('tag_id__tag_stn_wt'),
                        dia_wt=F('tag_id__tag_dia_wt'),
                        download_by=F('downloaded_by__first_name'),
                        download_date=F('downloaded_date'),
                    ).values(
                        'stock_transfer',
                        'product_name', 
                        'design_name',
                        'sub_design_name',
                        'tag_code',
                        'pieces',
                        'gross_wt', 
                        'net_wt',
                        'stn_wt',
                        'dia_wt',
                        'less_wt',
                        'download_by',
                        'download_date',
                        'issue_type',
                    )

                    for tag in transfer_list:

                        response_data.append({
                            'pk_id': instance.id_stock_transfer,
                            'trans_date': format_date(instance.trans_date),
                            'transfer_from':instance.transfer_from.name,
                            'transfer_to': instance.transfer_to.name if instance.transfer_to else '',
                            'status': dict(ErpStockTransfer.TRANSFER_STATUS_CHOICES).get(instance.transfer_status, ''),
                            'trans_code': instance.trans_code,
                            'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(instance.trans_to_type, ''),
                            'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(instance.transfer_type, ''),
                            'tag_code':'',
                            **tag,
                            'downloaded_by':  tag['download_by'],
                            'downloaded_date': date_format_with_time(tag['download_date']),
                            'status_color':get_status_color(instance.transfer_status),
                            'approved_by':  instance.approved_by.first_name if instance.approved_by else None ,
                            'approved_date': date_format_with_time(instance.approved_date),
                            'rejected_by':  instance.rejected_by.first_name if instance.rejected_by else None ,
                            'rejected_on': date_format_with_time(instance.rejected_on),
                            })

                if(instance.transfer_type == 2):
            
                    transfer_list = ErpNonTagTransfer.objects.filter(stock_transfer=instance)

                    nt_data = ErpNonTagTransferSerializer(transfer_list,many=True).data

                    for non_tag,ins  in zip(nt_data, transfer_list):

                        response_data.append({
                            'pk_id': instance.id_stock_transfer,
                            'transfer_from':instance.transfer_from.name,
                            'transfer_to':instance.transfer_to.name,
                            'trans_code': instance.trans_code,
                            'trans_date': format_date(instance.trans_date),
                            'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(instance.trans_to_type, ''),
                            'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(instance.transfer_type, ''),
                            'status': dict(ErpStockTransfer.TRANSFER_STATUS_CHOICES).get(instance.transfer_status, ''),
                            **non_tag,
                            'tag_code':'',
                            'status_color':get_status_color(instance.transfer_status),
                            'downloaded_by':  instance.downloaded_by.first_name if instance.downloaded_by else None ,
                            'downloaded_date': date_format_with_time(instance.downloaded_date),
                            'approved_by':  instance.approved_by.first_name if instance.approved_by else None ,
                            'approved_date': date_format_with_time(instance.approved_date),
                            'rejected_by':  instance.rejected_by.first_name if instance.rejected_by else None ,
                            'rejected_on': date_format_with_time(instance.rejected_on),
                        })
            columns = get_reports_columns_template(request.user.pk,STOCK_TRANSFER_APPROVAL_REPORT,request.data["path_name"])           
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = False
            filters_copy['isBranchFromToFilterReq'] = True
            filters_copy['StockTransferFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            # FILTERS['StockTransferFilterReq'] = False
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        



class JewelNotDeliveredReportSqlAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            filters = ''
            if(id_branch):
                branch = ",".join(map(str, id_branch))
                filters  = F" and inv.id_branch_id in ({branch})"

            if  bill_setting_type == 1:
                filters += ' and inv.setting_bill_type = 1'
            elif bill_setting_type == 0: 
                filters += ' and inv.setting_bill_type = 0'

            page = int(request.data.get("page", 1))
            records_per_page = int(request.data.get("records", 50))  # default to 50 if not passed

            count_query = f"""
                        SELECT COUNT(*) AS total
                        FROM (
                            SELECT d.bill_id
                            FROM erp_item_delivered d 
                            LEFT JOIN erp_invoice inv ON inv.erp_invoice_id = d.bill_id
                            WHERE inv.invoice_status = 1
                            AND inv.invoice_date BETWEEN '2025-01-23' AND '2025-06-23'
                            GROUP BY d.bill_id
                        ) AS grouped_bills;
 
                        """
            count_result = generate_query_result(count_query)
            total_records = count_result[0]['total']
            total_pages = (total_records + records_per_page - 1) // records_per_page 
            if total_pages < page:
                page = 1
            offset = (page - 1) * records_per_page

            queryset = f"""
                    SELECT d.*,(pro.product_name) as product_name,inv.*,
                    COALESCE(SUM(d.piece), 0) AS pieces,
                    COALESCE(SUM(d.weight), 0) AS weights                            
                    FROM erp_item_delivered d 
                    LEFT join erp_product pro ON pro.pro_id = d.product_id
                    LEFT join erp_invoice inv ON inv.erp_invoice_id = d.bill_id
                    Where   inv.invoice_status = 1
                    AND inv.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                    {filters}
                    GROUP BY  inv.erp_invoice_id
                    ORDER BY inv.erp_invoice_id DESC   
                    LIMIT {records_per_page} OFFSET {offset}                        
            """
            
            result = generate_query_result(queryset)



            for item in result:

                item.update({
                    "metal": item['metal_id'],
                    "fin_year": item['fin_year_id'],
                    "id_branch": item['id_branch_id'],
                })
                 
                inv_data = get_invoice_no(item)

                item.update({
                    'invoice_no':inv_data['invoice_no'],
                    'invoice_date': format_date(item['invoice_date']),
                    'status': dict([(1, 'Delivered'),(2, 'Not Delivered')]).get(item['is_delivered'], ''),
                    'status_color':dict([(1, 'success'),(2, 'warning')]).get(item['is_delivered'], ''),
                })
            columns = get_reports_columns_template(request.user.pk,SALES_REPORT,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':columns,
                'actions':ACTION_LIST,
                'page_count':total_records,
                'total_pages': total_pages,
                'current_page': page,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(result,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

class PurchaseReportSummary(generics.GenericAPIView):

    def post(self, request, *args, **kwargs):
        
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        id_metal = request.data.get('id_metal')
        with connection.cursor() as cursor:
            old_purchase = F"""
                    SELECT 
                    m.id_metal,m.metal_name,"OLD PURCHASE" as type,
                    COALESCE(old_pur.gross_wt , 0) AS weight,
                    COALESCE(old_pur.net_wt , 0) AS net_weight,
                    COALESCE(old_pur.amount , 0) AS amount
                    FROM metal m
                    LEFT JOIN (
                        SELECT 
                            COALESCE(SUM(s.gross_wt), 0) AS gross_wt,
                            COALESCE(SUM(s.net_wt), 0) AS net_wt,COALESCE(SUM(s.amount), 0) AS amount,
                            p.id_metal_id
                        FROM erp_invoice_old_metal_details s
                        LEFT JOIN erp_invoice e ON e.erp_invoice_id = s.invoice_bill_id_id
                        LEFT JOIN erp_product p ON p.pro_id = s.id_product_id
                        WHERE e.invoice_status = 1 AND e.sales_invoice_no IS NOT NULL
                        AND (DATE(e.invoice_date) BETWEEN '{from_date}' AND '{to_date}')
                        and e.setting_bill_type = {bill_setting_type}
                        GROUP BY p.id_metal_id
                    ) AS old_pur ON old_pur.id_metal_id = m.id_metal
                    where m.id_metal is not null
                    """
            if id_metal!='' and id_metal!=None:
                old_purchase += F" and m.id_metal = {id_metal}" 
            old_purchase_result = generate_query_result(old_purchase)
            sales_return = F"""
                SELECT 
                m.id_metal,m.metal_name,"SALES RETURN" as type,
                COALESCE(ret_pur.gross_wt , 0) AS weight,
                COALESCE(ret_pur.net_wt , 0) AS net_weight,
                COALESCE(ret_pur.item_cost , 0) AS amount
                FROM metal m
                LEFT JOIN (
                    SELECT 
                        COALESCE(SUM(s.gross_wt), 0) AS gross_wt,
                        COALESCE(SUM(s.net_wt), 0) AS net_wt,
                        COALESCE(SUM(s.item_cost), 0) AS item_cost,
                        p.id_metal_id
                    FROM erp_invoice_sales_return_details s
                    LEFT JOIN erp_invoice e ON e.erp_invoice_id = s.invoice_bill_id_id
                    LEFT JOIN erp_product p ON p.pro_id = s.id_product_id
                    WHERE e.invoice_status = 1 AND e.sales_invoice_no IS NOT NULL
                    AND (DATE(e.invoice_date) BETWEEN '{from_date}' AND '{to_date}')
                    and e.setting_bill_type = {bill_setting_type}
                    GROUP BY p.id_metal_id
                ) AS ret_pur ON ret_pur.id_metal_id = m.id_metal
                where m.id_metal is not null
            """
            if id_metal!='' and id_metal!=None:
                old_purchase += F" and m.id_metal = {id_metal}"  
            sales_return_result = generate_query_result(sales_return)

            return_data = old_purchase_result + sales_return_result

            paginator, page = pagination.paginate_queryset(return_data, request,None,PURCHASE_SUMMARY_REPORT_COLUMNS)
            columns = get_reports_columns_template(request.user.pk,PURCHASE_SUMMARY_REPORT_COLUMNS,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            context = {
                'columns': columns,
                'actions': ACTION_LIST,
                'groupingColumns': ["metal_name"],
                'page_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'filters':filters_copy,
                'is_filter_req' : True
            }
            return pagination.paginated_response(return_data, context)
        

class AreaCustomerSalesLogReportAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    

    def post(self, request, *args, **kwargs):
        try:
            from_date = request.data.get("fromDate")
            to_date = request.data.get("toDate")
            metal_id = request.data.get("id_metal")
            page = int(request.data.get("page", 1))
            records_per_page = int(request.data.get("records", 50))
            offset = (page - 1) * records_per_page
            report_type = int(request.data.get('group_by',1))
            print(metal_id)
            print(report_type)

            if not from_date or not to_date:
                return Response({"message": "From date and To date are required"}, status=400)
            
            groupingColumns = []
            if report_type == 1:
                groupingColumns = ['area_name']
                group_by_clause = "GROUP BY a.id_area"
                order_by_clause = "ORDER BY a.area_name ASC"
                column_template = AVAILABLE_CUSTOMER_SALES_LOG_REPORT_LIST_AREA

            elif report_type == 2:
                groupingColumns = ['region_name']
                group_by_clause = "GROUP BY r.id_region"
                order_by_clause = "ORDER BY r.region_name ASC"
                column_template = AVAILABLE_CUSTOMER_SALES_LOG_REPORT_LIST_REGION

            metal_filter = f"AND p.id_metal_id = '{metal_id}'" if metal_id else ""
            print("groupingColumns",groupingColumns)


            sql = f"""
                SELECT 
                    a.id_area,
                    a.area_name,
                    r.id_region,
                    r.region_name,
                    SUM(l.pieces) AS total_pieces,
                    SUM(l.gross_wt) AS total_gwt,
                    SUM(l.net_wt) AS total_nwt,
                    SUM(l.item_cost) AS item_cost,
                    COUNT(c.id_customer) AS cus_cnt,
                    SUM(l.item_cost) / NULLIF(COUNT(c.id_customer),0) AS average_order_value,
                    (
                        SELECT p2.product_name
                        FROM erp_customer_sales_log l2
                        JOIN erp_product p2 ON p2.pro_id = l2.id_product_id
                        WHERE DATE(l2.created_on) BETWEEN '{from_date}' AND '{to_date}'
                        {f"AND p2.id_metal_id = '{metal_id}'" if metal_id else ""}
                        GROUP BY l2.id_product_id
                        ORDER BY COUNT(*) DESC
                        LIMIT 1
                    ) AS top_selling_product

                FROM erp_customer_sales_log l
                LEFT JOIN customers c ON c.id_customer = l.id_customer_id
                LEFT JOIN customer_address addr ON addr.customer_id = c.id_customer
                LEFT JOIN area a ON a.id_area = addr.area_id
                LEFT JOIN area_region ar ON ar.area_id = a.id_area
                LEFT JOIN region r ON r.id_region = ar.region_id
                LEFT JOIN erp_product p ON p.pro_id = l.id_product_id 

                WHERE DATE(l.created_on) BETWEEN '{from_date}' AND '{to_date}' 
                {metal_filter}
                {group_by_clause}
                {order_by_clause}
            """

            
            response_data = generate_query_result(sql)
            paginator, page = pagination.paginate_queryset(response_data, request,None,column_template)
            columns = get_reports_columns_template(request.user.pk,column_template,request.data["path_name"])
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isMetalFilterReq'] = True
            filters_copy['isReportGroupByReq'] = True
            context = {
                'columns': columns,
                'actions': ACTION_LIST,
                'groupingColumns':[],
                'groupByOption': [ {'value': 1, 'label': 'Area'}, {'value': 2, 'label': 'Region'}],
                'page_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'filters':filters_copy,
                'is_filter_req' : True
            }
            return pagination.paginated_response(list(page), context)
        except Exception as e:
            return Response({"error": str(e)}, status=500)




