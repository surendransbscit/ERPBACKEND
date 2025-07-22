from django.shortcuts import render
from django.http import HttpResponse, request, Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import datetime, timedelta, date
from django.db import transaction , IntegrityError,DatabaseError,OperationalError,connection
from django.db.models import  Sum,Avg, F, ExpressionWrapper, DecimalField
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from utilities.utils import format_date,format_with_decimal
from utilities.constants import FILTERS
from utilities.pagination_mixin import PaginationMixin
import traceback
pagination = PaginationMixin()  # Apply pagination
import re
import os
import base64
from PIL import Image
from django.core.files.images import ImageFile
import io
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
from django.conf import settings
from django.db.models import ProtectedError
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee,isSuperuser
from core.views  import get_reports_columns_template


from retailmasters.views import BranchEntryDate

# model
from .models import (ErpPocket,ErpPocketDetails,ErpMetalProcess,ErpMeltingIssueDetails,ErpTestingIssueDetails,ErpRefining)
from employees.models import (Employee)
from retailmasters.models import (Branch,FinancialYear,Uom,Company)
from retailcataloguemasters.models import (Product,Design,SubDesign)
from billing.models import ErpInvoiceSalesDetails,ErpInvoiceOldMetalDetails,ErpInvoiceStoneDetails,ErpInvoice,ErpInvoiceSalesReturn,ErpInvoiceOtherMetal
from retailpurchase.models import ErpAccountStockProcessDetails
#serializers
from .serializers import (ErpPocketSerializer,ErpPocketDetailSerializer,ErpPocketDetailStoneSerializer,
                        ErpMeltingIssueDetailsSerializer,ErpPocketMeltingIssueSerializer,
                        ErpMetalProcessSerializer,ErpMeltingReceiptDetailsSerializer,ErpMeltingReceiptDetails,
                        ErpTestingIssueDetailsSerializer,ErpRefiningSerializer,ErpRefiningDetails,ErpRefiningDetailsSerializer,
                        ErpRefiningReceiptDetailsSerializer)
from billing.serializers import ErpInvoiceOldMetalDetailsSerializer,ErpInvoiceStoneDetailsSerializer,ErpInvoiceSerializer,ErpInvoiceOtherMetalSerializer
from retailpurchase.serializers import ErpAccountStockProcessDetailsSerializer

from retaildashboard.views import execute_raw_query

from .constants import ACTION_LIST,POCKET_COLUMN_LIST,POCKET_TYPE
class GetPurchaseStockDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        try:
            result_data = []
            from_date = request.data.get('from_date')
            to_date = request.data.get('to_date')
            from_branch = request.data.get('from_branch')
            stock_type = request.data.get('stock_type')
            id_metal = request.data.get('id_metal')
            if not from_date:
                    return Response({"error": "From Date is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not to_date:
                    return Response({"error": "To Date is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not from_branch:
                    return Response({"error": "Branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not stock_type:
                    return Response({"error": "Stock Type is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if stock_type=='1':
                  result_data = self.get_sales_return_stock(from_date,to_date,from_branch,id_metal)
            if stock_type=='2':
                  result_data = self.get_partly_stock(from_date,to_date,from_branch,id_metal)
            if stock_type=='3':
                  result_data = self.get_old_metal_stock(from_date,to_date,from_branch,id_metal)
            return Response({"message": "Data Retrieved Successfully","result":result_data}, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


    def get_old_metal_stock(self,from_date,to_date,from_branch,id_metal):
        return_data =[]
        metal_filter = ''
        if(id_metal):
            metal_filter = F"AND P.id_metal_id={id_metal} "
        
        old_metal_list = ErpInvoiceOldMetalDetails.objects.raw(
            F"""
             SELECT 
                E.invoice_old_metal_item_id,
                E.invoice_bill_id_id,
                P.product_name AS product_name,
                P.stock_type AS stock_type,
                P.uom_id_id AS uom_id,
                E.touch,
                E.id_product_id,
                E.gross_wt,
                E.pieces,
                E.less_wt,
                E.net_wt,
                E.dia_wt,
                E.stone_wt,
                E.dust_wt,
                E.wastage_weight,
                E.pure_weight,E.touch
            FROM 
                erp_invoice_old_metal_details AS E
            JOIN 
                erp_invoice AS I ON I.erp_invoice_id = E.invoice_bill_id_id
            LEFT JOIN 
                erp_pocket_details AS PO ON E.invoice_old_metal_item_id = PO.invoice_old_metal_item_id_id
            LEFT JOIN (
            SELECT  ASP.id_account_stock_process,ASD.invoice_old_metal_item_id_id 
            FROM erp_account_stock_process_details ASD
            LEFT JOIN erp_account_stock_process AS ASP ON ASP.id_account_stock_process = ASD.account_stock_id
            WHERE  ASP.status = 1 and ASP.process_type = 1
            ) as ASP ON  ASP.invoice_old_metal_item_id_id = E.invoice_old_metal_item_id
            JOIN 
                erp_product AS P ON E.id_product_id = P.pro_id
            WHERE 
                I.invoice_status = 1
                AND I.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                AND I.id_branch_id = '{from_branch}'
                AND PO.id_pocket_detail IS NULL
                AND ASP.id_account_stock_process IS NOT NULL
                {metal_filter}
            """
        )
        old_metal_list = ErpInvoiceOldMetalDetailsSerializer(old_metal_list,many=True).data
        
        if len(old_metal_list) > 0:
            for item in old_metal_list:
                # inv_queryset = ErpInvoice.objects.get(erp_invoice_id = item["invoice_bill_id"])
                # inv_data = ErpInvoiceSerializer(inv_queryset,context={"invoice_no":True,'invoice_type':2}).data
                stone_details = []
                try:
                    stone_query_set = ErpInvoiceStoneDetails.objects.filter(invoice_old_metal_item_id=item['invoice_old_metal_item_id']).all()
                    stone_serializer = ErpInvoiceStoneDetailsSerializer(stone_query_set,many = True)
                    stone_details = stone_serializer.data
                except ErpInvoiceStoneDetails.DoesNotExist:
                       continue
                return_data.append({
                        "invoice_old_metal_item_id":item['invoice_old_metal_item_id'],
                        "pk_id":item['invoice_old_metal_item_id'],
                        "type": "OLD METAL",
                        "product_name":item['product_name'],
                        "stock_type":item['stock_type'],
                        "stock_type_name": ("Non-Tagged" if item['stock_type'] == "1" else "Tagged"),
                        "id_product":item['id_product'],
                        "id_design": '',
                        "id_sub_design": '',
                        "id_purity": '',
                        "uom_id": item['uom_id'],
                        "touch": item['touch'],
                        "pieces":item['pieces'],
                        "gross_wt": item['gross_wt'],
                        "less_wt":item['less_wt'],
                        "net_wt":format_with_decimal((float(item['net_wt']) + float(item['dust_wt']) + float(item['wastage_weight'])),3),
                        "dia_wt":item['dia_wt'],
                        "stone_wt":item['stone_wt'],
                        "pure_weight":item['pure_weight'],
                        "touch":item['touch'],
                        "other_metal_wt":0,
                        "stone_details":stone_details,
                        "other_metal_details":[],
                        # "invoice_no" : inv_data['inv_no']['invoice_no'],
                        # "customer_name" : inv_data['customer_name'],
                        # "customer_mobile" : inv_data['customer_mobile'],
                  })
        return return_data
    
    def get_sales_return_stock(self,from_date,to_date,from_branch,id_metal):
        return_data =[]
        metal_filter = ''
        if(id_metal):
            metal_filter = F"AND P.id_metal_id={id_metal} "
        sales_return_list = ErpInvoiceSalesReturn.objects.raw(
            F"""
             SELECT 
                E.invoice_return_id,
                E.invoice_bill_id_id,
                P.product_name AS product_name,
                P.stock_type AS stock_type,
                P.uom_id_id AS uom_id,
                E.id_product_id,
                E.id_design_id,
                E.id_sub_design_id,
                E.id_purity_id,
                E.gross_wt,
                E.pieces,
                E.less_wt,
                E.net_wt,
                E.dia_wt,
                E.stone_wt,
                E.other_metal_wt
            FROM 
                erp_invoice_sales_return_details AS E
            JOIN 
                erp_invoice AS I ON I.erp_invoice_id = E.invoice_bill_id_id
            JOIN 
                erp_invoice_sales_details AS SA ON SA.invoice_sale_item_id = E.invoice_sale_item_id_id
            LEFT JOIN 
                erp_pocket_details AS PO ON E.invoice_return_id = PO.invoice_return_id_id
            LEFT JOIN (
            SELECT  ASP.id_account_stock_process,ASD.invoice_return_id_id,ASP.entry_date
            FROM erp_account_stock_process_details ASD
            LEFT JOIN erp_account_stock_process AS ASP ON ASP.id_account_stock_process = ASD.account_stock_id
            WHERE  ASP.status = 1
            GROUP BY  ASD.invoice_return_id_id 
            ) as ASP ON  ASP.invoice_return_id_id = E.invoice_return_id
            JOIN 
                erp_product AS P ON E.id_product_id = P.pro_id
            WHERE 
                I.invoice_status = 1
                AND ASP.entry_date BETWEEN '{from_date}' AND '{to_date}'
                AND I.id_branch_id = '{from_branch}'
                AND ASP.id_account_stock_process IS NOT NULL
                AND PO.id_pocket_detail IS NULL
                {metal_filter}
            """
        )
        for item in sales_return_list:
            stone_details = []
            queryset = ErpInvoiceOtherMetal.objects.filter(invoice_sale_item_id=item.invoice_sale_item_id.invoice_sale_item_id)
            other_metal_details= ErpInvoiceOtherMetalSerializer(queryset, many=True).data
            try:
                stone_query_set = ErpInvoiceStoneDetails.objects.filter(invoice_sale_item_id=item.invoice_sale_item_id.invoice_sale_item_id).all()
                stone_serializer = ErpInvoiceStoneDetailsSerializer(stone_query_set,many = True)
                stone_details = stone_serializer.data
            except ErpInvoiceStoneDetails.DoesNotExist:
                    continue
            return_data.append({
                    "invoice_return_id": item.invoice_return_id,
                    "pk_id": item.invoice_return_id,
                    "type": "SALES RETURN",
                    "stock_type":item.stock_type,
                    "stock_type_name": ("Non-Tagged" if item.stock_type == "1" else "Tagged"),
                    "product_name": item.product_name,
                    "id_product":item.id_product_id,
                    "id_design": item.id_design_id,
                    "id_sub_design": item.id_sub_design_id,
                    "id_purity": item.id_purity_id,
                    "id_section": '',
                    "uom_id": item.uom_id,
                    "pieces":item.pieces,
                    "gross_wt":item.gross_wt,
                    "less_wt":item.less_wt,
                    "net_wt":item.net_wt,
                    "dia_wt":item.dia_wt,
                    "stone_wt":item.stone_wt,
                    "other_metal_wt":item.other_metal_wt,
                    "stone_details":stone_details,
                    "other_metal_details":other_metal_details,
                    # "invoice_no" : inv_data['inv_no']['invoice_no'],
                    # "customer_name" : inv_data['customer_name'],
                    # "customer_mobile" : inv_data['customer_mobile'],
                })
        return return_data
    
    def get_partly_stock(self,from_date,to_date,from_branch,id_metal):
        return_data =[]
        old_metal_list = ErpAccountStockProcessDetails.objects.filter(account_stock__status = 1,account_stock__process_type = 1,account_stock__stock_type = 2,account_stock__entry_date__range=[from_date, to_date],account_stock__id_branch=from_branch,tag_id__pocket_partly_sale_tag_id__isnull=True)
        if(id_metal):
            old_metal_list = old_metal_list.filter(id_product__id_metal =id_metal )
        old_metal_list = ErpAccountStockProcessDetailsSerializer(old_metal_list,many=True).data
        if len(old_metal_list) > 0:
            for item in old_metal_list:
                # inv_queryset = ErpInvoice.objects.get(erp_invoice_id = item["invoice_bill_id"])
                # inv_data = ErpInvoiceSerializer(inv_queryset,context={"invoice_no":True,'invoice_type':2}).data
                stone_details = []
                queryset = ErpInvoiceOtherMetal.objects.filter(invoice_sale_item_id=item['invoice_sale_item_id'])
                other_metal_details= ErpInvoiceOtherMetalSerializer(queryset, many=True).data
                try:
                    stone_query_set = ErpInvoiceStoneDetails.objects.filter(invoice_sale_item_id=item['invoice_sale_item_id']).all()
                    stone_serializer = ErpInvoiceStoneDetailsSerializer(stone_query_set,many = True)
                    stone_details = stone_serializer.data
                except ErpInvoiceStoneDetails.DoesNotExist:
                       continue
                return_data.append({
                        "invoice_sale_item_id":item['invoice_sale_item_id'],
                        "pk_id":item['invoice_sale_item_id'],
                        "type": "PARTLY SALES",
                        "product_name":item['product_name'],
                        "stock_type":item['stock_type'],
                        "stock_type_name": ("Non-Tagged" if item['stock_type'] == "1" else "Tagged"),
                        "id_product":item['id_product'],
                        "id_design": item['id_design'],
                        "id_sub_design": item['id_sub_design'],
                        "id_purity": item['id_purity'],
                        "uom_id": item['uom_id'],
                        "pieces":item['pieces'],
                        "gross_wt": item['gross_wt'],
                        "less_wt":item['less_wt'],
                        "net_wt":item['net_wt'],
                        "dia_wt":item['dia_wt'],
                        "stone_wt":item['stone_wt'],
                        "other_metal_wt":item['other_metal_wt'],
                        "stone_details":stone_details,
                        "other_metal_details":other_metal_details,
                        "tag_id":item['tag_id'],
                        # "invoice_no" : inv_data['inv_no']['invoice_no'],
                        # "customer_name" : inv_data['customer_name'],
                        # "customer_mobile" : inv_data['customer_mobile'],
                  })
        return return_data
    
class CreatePocket(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def generate_ref_code(self):
        code = ''
        last_code=None
        last_code=ErpPocket.objects.order_by('-id_pocket').first()
        if last_code:
            last_code = last_code.pocket_no
            match = re.search(r'(\d{5})$', last_code)
            if match:
                code=match.group(1)
                code = str(int(code) + 1).zfill(5)
            else:
               code = '00001'
        else:
            code = '00001'
        
        return code
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                pocket_data = request.data
                item_details = request.data.get('item_details')
                if not pocket_data:
                    return Response({"error": "Purchase data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not item_details:
                    return Response({"error": "Item Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(pocket_data['id_branch'])
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                pocket_no = self.generate_ref_code()
                pocket_data.update({"entry_date":entry_date,"pocket_no":pocket_no,"fin_year":fin_id,"created_by": request.user.id})
                pocket_serializer = ErpPocketSerializer(data = pocket_data)
                if pocket_serializer.is_valid(raise_exception=True):
                    pocket_serializer.save()
                    if item_details:
                        self.insert_pocket_details(item_details,pocket_serializer.data['id_pocket'])
                    return Response({"message":"Pocket Created Successfully."}, status=status.HTTP_201_CREATED)
                return Response({"message":pocket_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    
    def insert_pocket_details(self,item_details,id_pocket):
        return_data =[]
        try:
            with transaction.atomic():    
                for item in item_details:
                    item.update({"id_pocket":id_pocket})
                    pocket_detail_serializer = ErpPocketDetailSerializer(data=item)
                    if(pocket_detail_serializer.is_valid(raise_exception=True)):
                        pocket_detail_serializer.save()
                        if len(item['stone_details']) > 0:
                            for stone_details in item['stone_details']:
                                stone_details.update({"id_pocket_detail":pocket_detail_serializer.data["id_pocket_detail"]})
                                pocket_stone_detail_serializer = ErpPocketDetailStoneSerializer(data=stone_details)
                                if(pocket_stone_detail_serializer.is_valid(raise_exception=True)):
                                    pocket_stone_detail_serializer.save()
                        return_data.append({**item,**pocket_detail_serializer.data})
                    else:
                        tb = traceback.format_exc()
                        return Response({"error":ErpPocketDetailSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            return return_data
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

class PocketDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        try:
            #pocket_no = request.data('pocket_no')
            query = """select d.id_pocket_detail,pk.pocket_no,d.id_pocket_id as id_pocket,d.id_product_id as id_product,p.product_name,p.id_metal_id,m.metal_name,p.id_metal_id as id_metal,
                IFNULL(sum(d.pieces),0) as total_pcs,IFNULL(sum(d.gross_wt),0) as total_gwt,
                IFNULL(melting.melting_pieces,0) as melting_pieces,
                (IFNULL(sum(d.pieces),0)-IFNULL(melting.melting_pieces,0)) as melting_pieces,
                (IFNULL(sum(d.gross_wt),0)-IFNULL(melting.melting_gwt,0)) as gross_wt,
                (IFNULL(sum(d.less_wt),0)-IFNULL(melting.melting_lwt,0)) as less_wt,
                (IFNULL(sum(d.net_wt),0)-IFNULL(melting.melting_nwt,0)) as net_wt,
                (IFNULL(sum(d.stone_wt),0)-IFNULL(melting.melting_stone_wt,0)) as stone_wt,
                (IFNULL(sum(d.dia_wt),0)-IFNULL(melting.melting_dia_wt,0)) as dia_wt,
                (IFNULL(sum(d.other_metal_wt),0)-IFNULL(melting.melting_other_metal_wt,0)) as other_metal_wt,
                ifnull(avg(d.touch),0) as touch_average
            from erp_pocket_details d 
            left join erp_pocket pk on pk.id_pocket = d.id_pocket_id
            left join erp_product p on p.pro_id = d.id_product_id
            left join metal m on m.id_metal = p.id_metal_id
            left join(select m.id_pocket_id,m.id_product_id,p.id_metal_id,
            IFNULL(sum(m.melting_pieces),0) as melting_pieces,
            IFNULL(sum(m.gross_wt),0) as melting_gwt,IFNULL(sum(m.less_wt),0) as melting_lwt,
            IFNULL(sum(m.net_wt),0) as melting_nwt,IFNULL(sum(m.stone_wt),0) as melting_stone_wt,IFNULL(sum(m.dia_wt),0) as melting_dia_wt,IFNULL(sum(m.other_metal_wt),0) as melting_other_metal_wt
            from erp_melting_issue_details m
            left join erp_product p on p.pro_id = m.id_product_id
            group by m.id_pocket_id) as melting ON melting.id_pocket_id = d.id_pocket_id
            group by d.id_pocket_id
            having gross_wt > 0
            """
            stocks = execute_raw_query(query)
            # stocks = ErpPocket.objects.raw(query)
            # data = ErpPocketMeltingIssueSerializer(stocks,many=True).data
            for item in stocks:
                item.update({
                    "max_pieces" : item["melting_pieces"],
                    "max_less_wt" : item["less_wt"],
                    "max_other_metal_wt" : item["other_metal_wt"],
                    "max_net_wt" : item["net_wt"],
                    "max_dia_wt" : item["dia_wt"],
                    "max_stone_wt" : item["stone_wt"],
                    "max_gross_wt" : item["gross_wt"],
                    "stone_details" : [],
                })



            return Response({"message": "Data Retrieved Successfully","result":stocks}, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)



class CreateMetalProcess(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def generate_ref_code(self,process_id):
        code = ''
        last_code=None
        last_code=ErpMetalProcess.objects.filter(process_id=process_id).order_by('-id_metal_process').first()
        if last_code:
            last_code = last_code.ref_no
            match = re.search(r'(\d{5})$', last_code)
            if match:
                code=match.group(1)
                code = str(int(code) + 1).zfill(5)
            else:
               code = '00001'
        else:
            code = '00001'
        
        return code
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                process = request.data
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(process['id_branch'])
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                ref_no = self.generate_ref_code(process['process_id'])
                process.update({"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": request.user.id})
                
            
                process_serializer = ErpMetalProcessSerializer(data = process)
                if process_serializer.is_valid(raise_exception=True):
                    process_serializer.save()

                    ##Issue Details
                    if process['type']=="1":  
                        issue_details = request.data.get('issue_details')
                        if not issue_details:
                            return Response({"error": "Item Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                        ##Melting Issue Details
                        if process['process_id']=="1":
                            self.insert_melting_issue_details(issue_details,process_serializer.data['id_metal_process'])
                        if process['process_id']=="2":
                            self.insert_testing_issue_details(issue_details,process_serializer.data['id_metal_process'])
                        if process['process_id']=="3":
                            item = {}
                            item.update({"issue_id_metal_process":process_serializer.data['id_metal_process']})
                            serializer = ErpRefiningSerializer(data=item)
                            if(serializer.is_valid(raise_exception=True)):
                                serializer.save()
                                self.insert_refining_issue_details(issue_details,serializer.data['id_refining'])
                        ##Melting

                    ##Receipt Details
                    if process['type']=="2":
                        receipt_details = request.data.get('receipt_details')
                        if not receipt_details:
                            return Response({"error": "Receipt Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                        ##Melting Receipt Details
                        if process['process_id']=="1":
                            receipt_details.update({"id_metal_process":process_serializer.data['id_metal_process']})
                            melting_issue_serializer = ErpMeltingReceiptDetailsSerializer(data=receipt_details)
                            if(melting_issue_serializer.is_valid(raise_exception=True)):
                                melting_issue_serializer.save()
                        ##Melting

                        ##Testing Receipt Details
                        if process['process_id']=="2":
                            self.update_testing_receipt_details(receipt_details,process_serializer.data['id_metal_process'])
                        ##Testing Receipt Details

                        ##Refining Receipt Details
                        if process['process_id']=="3":
                            self.insert_refining_receipt_details(receipt_details,process_serializer.data['id_metal_process'])
                        ##Refining Receipt Details
                    
                    return Response({"message":"Process Created Successfully."}, status=status.HTTP_201_CREATED)
                return Response({"message":process_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def insert_melting_issue_details(self,item_details,id_metal_process):
        return_data =[]
        try:
            with transaction.atomic():    
                for item in item_details:
                    item.update({"id_metal_process":id_metal_process})
                    melting_issue_serializer = ErpMeltingIssueDetailsSerializer(data=item)
                    if(melting_issue_serializer.is_valid(raise_exception=True)):
                        melting_issue_serializer.save()
                        # if len(item['stone_details']) > 0:
                        #     for stone_details in item['stone_details']:
                        #         stone_details.update({"id_pocket_detail":melting_issue_serializer.data["id_pocket_detail"]})
                        #         pocket_stone_detail_serializer = ErpPocketDetailStoneSerializer(data=stone_details)
                        #         if(pocket_stone_detail_serializer.is_valid(raise_exception=True)):
                        #             pocket_stone_detail_serializer.save()
                        return_data.append({**item,**melting_issue_serializer.data})
                    else:
                        tb = traceback.format_exc()
                        return Response({"error":ErpMeltingIssueDetailsSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            return return_data
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    

    def insert_testing_issue_details(self,item_details,id_metal_process):
        return_data =[]
        try:
            with transaction.atomic():    
                for item in item_details:
                    item.update({"id_metal_process":id_metal_process})
                    serializer = ErpTestingIssueDetailsSerializer(data=item)
                    if(serializer.is_valid(raise_exception=True)):
                        serializer.save()
                        return_data.append({**item,**serializer.data})
                    else:
                        tb = traceback.format_exc()
                        return Response({"error":ErpTestingIssueDetailsSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            return return_data
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
            
    

    def update_testing_receipt_details(self,item_details,id_metal_process):
        return_data =[]
        try:
            with transaction.atomic():    
                for item in item_details:
                    id_testing = item.get("id_testing")
                    id_melting_receipt = item.get("id_melting_receipt")
                    if not id_testing:
                        return Response({"error": "Testing id is missing."}, status=status.HTTP_400_BAD_REQUEST)
                    existing_record = ErpTestingIssueDetails.objects.get(id_testing=id_testing)
                    existing_record.received_weight = item.get("received_weight", existing_record.received_weight)
                    existing_record.touch = item.get("touch", existing_record.touch)
                    existing_record.charges = item.get("charges", existing_record.charges)
                    existing_record.receipt_metal_process = ErpMetalProcess.objects.get(id_metal_process=id_metal_process)
                    existing_record.save()
                    existing_melting_record = ErpMeltingReceiptDetails.objects.get(id_melting_receipt=id_melting_receipt)
                    existing_melting_record.tested_weight = item.get("received_weight", existing_melting_record.tested_weight)
                    existing_melting_record.tested_touch = item.get("touch", existing_melting_record.tested_touch)
                    existing_melting_record.save()
                    return_data.append({"status":"true"})
                return return_data
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    

    def insert_refining_issue_details(self,item_details,id_refining):
        return_data =[]
        try:
            with transaction.atomic():    
                for item in item_details:
                    item.update({"id_refining":id_refining})
                    serializer = ErpRefiningDetailsSerializer(data=item)
                    if(serializer.is_valid(raise_exception=True)):
                        serializer.save()
                        return_data.append({**item,**serializer.data})
                    else:
                        tb = traceback.format_exc()
                        return Response({"error":ErpRefiningDetailsSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            return return_data
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def insert_refining_receipt_details(self,item_details,id_metal_process):
        return_data =[]
        try:
            with transaction.atomic():    
                for item in item_details:
                    id_refining = item.get("id_refining")
                    existing_record = ErpRefining.objects.get(id_refining=id_refining)
                    existing_record.charges = item.get("charges", existing_record.charges)
                    existing_record.receipt_id_metal_process = ErpMetalProcess.objects.get(id_metal_process=id_metal_process)
                    existing_record.save()
                    for value in item['item_details']:
                        value.update({"id_refining":id_refining})
                        serializer = ErpRefiningReceiptDetailsSerializer(data=value)
                        if(serializer.is_valid(raise_exception=True)):
                            serializer.save()
                            return_data.append({**item,**serializer.data})
                        else:
                            tb = traceback.format_exc()
                            return Response({"error":ErpRefiningReceiptDetailsSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            return return_data
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class MeltingIssuedDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        result = []
        id_supplier = request.data.get('id_supplier')
        process_id = request.data.get('process_id')
        if not id_supplier:
            return Response({"message": "Supplier id is missing"}, status=status.HTTP_400_BAD_REQUEST)
        if not process_id:
            return Response({"message": "Process id is missing"}, status=status.HTTP_400_BAD_REQUEST)
        
        melting_issue_details = ErpMeltingIssueDetails.objects.select_related('melting_issue_process_ref_id').filter(
                id_metal_process__process_id=1,
                id_metal_process__id_supplier=id_supplier,
                id_metal_process__melting_issue_process_ref_id__isnull = True
                ).values(
                    'id_metal_process', 'id_metal_process__ref_no'
                ).annotate(
                    total_melting_pcs=Sum('melting_pieces'),
                    total_gross_wt=Sum('gross_wt'),
                    total_less_wt=Sum('less_wt'),
                    total_net_wt=Sum('net_wt'),
                    total_dia_wt=Sum('dia_wt'),
                    total_stone_wt=Sum('stone_wt'),
                    total_touch=Avg('touch')
                )
        for item in melting_issue_details:
            result.append({
                "melting_issue_ref_no":item['id_metal_process__ref_no'],
                "id_metal_process":item['id_metal_process'],
                "pieces":item["total_melting_pcs"],
                "weight":item["total_gross_wt"],
                "issue_weight":item["total_gross_wt"],
                "touch":item["total_touch"],
                "charges":0,
                "id_product":'',
            })

        return Response({"message":"List Retrieved Successfully.","result":result}, status=status.HTTP_201_CREATED)
    

class MeltingReceivedDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        results = []
         
        query = """
            select r.id_melting_receipt,p.ref_no,r.weight,r.pieces,(r.weight-IFNULL(t.issue_weight,0)) as balance_weight,r.tested_weight,
            (r.weight-IFNULL(t.issue_weight,0)) as issue_weight,prod.product_name,
            melting.melting_touch as melting_touch
            from erp_melting_receipt_details r
            left join (select i.id_metal_process_id,ifnull(avg(i.touch),0) as melting_touch
            from erp_melting_issue_details i 
            group by i.id_metal_process_id) as melting on melting.id_metal_process_id = r.melting_issue_ref_no_id
            left join erp_product prod ON prod.pro_id = r.id_product_id
            left join erp_metal_process p on p.id_metal_process = r.melting_issue_ref_no_id
            left join (select IFNULL(sum(t.issue_weight),0) as issue_weight,t.id_melting_receipt_id
            from erp_testing_details t 
            group by t.id_melting_receipt_id) as t ON t.id_melting_receipt_id = r.id_melting_receipt
            where r.tested_weight = 0
            having balance_weight > 0
        """
        
        generate_result = GenerateQueryResult()
        result = generate_result.generate_query_result(query)

        return Response({"message":"List Retrieved Successfully.","result":result}, status=status.HTTP_201_CREATED)

class TestingIssuedDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_supplier = request.data.get('id_supplier')
        if not id_supplier:
            return Response({"message": "Supplier id is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = F"""
            select t.id_melting_receipt_id as id_melting_receipt,t.id_testing,t.issue_weight,t.issue_weight as received_weight,p.ref_no,
            melting.touch,prod.product_name
            from  erp_testing_details t
            left join erp_melting_receipt_details m on m.id_melting_receipt = t.id_melting_receipt_id
            left join erp_product prod on prod.pro_id = m.id_product_id
            left join (select m.id_metal_process_id,avg(m.touch) as touch
            from erp_melting_issue_details m
            group by m.id_metal_process_id) as melting on melting.id_metal_process_id = m.melting_issue_ref_no_id
            left join erp_metal_process p on p.id_metal_process = t.id_metal_process_id
            where t.received_weight = 0 and p.id_supplier_id = {id_supplier}
        """
        
        generate_result = GenerateQueryResult()
        result = generate_result.generate_query_result(query)

        return Response({"message":"List Retrieved Successfully.","result":result}, status=status.HTTP_201_CREATED)

class TestingReceivedDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        query = """
            select p.ref_no,m.tested_touch,prod.product_name,
            m.pieces,IFNULL((m.weight-t.issue_weight),0) as weight,IFNULL((m.weight-t.issue_weight),0) as tested_weight,
            m.id_product_id,m.id_melting_receipt
            from erp_melting_receipt_details m 
            left join erp_metal_process p on p.id_metal_process = m.melting_issue_ref_no_id
            left join erp_product prod ON prod.pro_id = m.id_product_id
            left join erp_refining_details r on r.id_melting_receipt_id = m.id_melting_receipt
            left join erp_testing_details t ON t.id_melting_receipt_id = m.id_melting_receipt
            where m.tested_touch > 0 and r.id_melting_receipt_id is null
        """
        
        generate_result = GenerateQueryResult()
        result = generate_result.generate_query_result(query)

        return Response({"message":"List Retrieved Successfully.","result":result}, status=status.HTTP_201_CREATED)


class RefiningIssuedDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_supplier = request.data.get('id_supplier')
        if not id_supplier:
            return Response({"message": "Supplier id is missing"}, status=status.HTTP_400_BAD_REQUEST)
        query = F"""
            select r.id_refining,IFNULL(sum(d.issue_weight),0) as issue_weight,p.ref_no
            from erp_refining_details d
            left join erp_refining r on r.id_refining = d.id_refining_id
            left join erp_metal_process p on p.id_metal_process = r.issue_id_metal_process_id
            left join erp_refining_receipt_details rcd on rcd.id_refining_id = r.id_refining
            where rcd.id_refining_id is null and p.id_supplier_id = {id_supplier}
            group by d.id_refining_id
        """
        
        generate_result = GenerateQueryResult()
        result = generate_result.generate_query_result(query)

        return Response({"message":"List Retrieved Successfully.","result":result}, status=status.HTTP_201_CREATED)


class GenerateQueryResult(generics.GenericAPIView):

    def generate_query_result(self,query):
        results = []
         # Execute the query
        with connection.cursor() as cursor:
            cursor.execute(query)
            # Fetch all rows from the executed query
            rows = cursor.fetchall()

            # Get column names from the cursor
            columns = [col[0] for col in cursor.description]

        # Create a list of dictionaries to represent the result
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        return results

class PocketEntryListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_branch = request.data.get('branch')

        lists = ErpPocket.objects.select_related( 'id_branch').annotate(
            total_gross_wt=Sum('pocket_ref__gross_wt'),
            total_pieces=Sum('pocket_ref__pieces'),
            net_wt=Sum('pocket_ref__net_wt'),
            less_wt=Sum('pocket_ref__less_wt'),
            stone_wt=Sum('pocket_ref__stone_wt'),
            dia_wt=Sum('pocket_ref__dia_wt'),
        ).values(
            'id_pocket',
            'pocket_no', 
            'id_branch__short_name',
            'fin_year__fin_year_code',
            'entry_date',
            'total_gross_wt', 
            'total_pieces',
            'entry_date',
            'id_branch__name',
            'type',
            'net_wt',
            'less_wt',
            'stone_wt',
            'dia_wt',
        )
        if from_date and to_date:
            lists = lists.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            lists = lists.filter(id_branch__in=id_branch)


        for purchase in lists:
            purchase['pk_id'] = purchase['id_pocket']
            purchase['entry_date'] = format_date(purchase['entry_date'])
            purchase['gross_wt'] = format(purchase['total_gross_wt'], '.3f')
            purchase['pieces'] = purchase['total_pieces']
            purchase['type_name'] = dict(POCKET_TYPE).get(purchase['type'], ''),

        paginator, page = pagination.paginate_queryset(lists, request,None,POCKET_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,POCKET_COLUMN_LIST,request.data.get('path_name',''))
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        context={
            'columns':columns,
            'actions':ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(lists,context) 

