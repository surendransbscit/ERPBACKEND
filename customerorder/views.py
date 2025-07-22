from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import transaction , IntegrityError,DatabaseError,OperationalError
from utilities.pagination_mixin import PaginationMixin
import uuid
import os
from rest_framework.views import APIView
import base64
from PIL import Image
import traceback
import sys
from django.core.files.images import ImageFile
import io
import re
from django.db.models import Q, ProtectedError
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.http import JsonResponse
import requests
from django.core.files.base import ContentFile
from django.conf import settings
from django.template.loader import get_template
from xhtml2pdf import pisa
from collections import defaultdict
import json
from django.db import connection
from django.db.models import Sum
from core.views  import get_reports_columns_template
from num2words import num2words

from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee,isSuperuser, IsEmployeeOrCustomer
from .models import (ERPOrder, ERPOrderDetails, ERPOrderStoneDetails, ERPOrderImages, ERPOrderAttribute,ERPOrderVideos,ERPOrderAudios,
                     ERPOrderCharges, ErpOrderOtherMetal, ErpJobOrder, ErpJobOrderDetails, CustomerWishlist, CustomerCart,ErpOrderRepairExtraMetal)
from .serializers import (ErpOrdersSerializer, ErpOrderStoneSerializer, ErpOrdersDetailSerializer, ErpOrderAttributeSerializer,
                          ErpOrderChargesSerializer, ErpOrderImagesSerializer,ERPOrderVideosSerializer,ERPOrderAudiosSerializer, ErpOrderOtherMetalSerializer, ErpJobOrderSerializer,
                          ErpJobOrderDetailSerializer, CustomerCartSerializer, CustomerWishlistSerializer,ErpOrderRepairExtraMetalSerializer,
                          ErpOrderInternalProcessLogSerializer)
from retailmasters.models import (Branch, FinancialYear, Uom, Company, Taxmaster, ERPOrderStatus, Supplier,Size, MetalRates,
                                  PaymentMode, State)
from retailmasters.serializers import (MetalRatesSerializer, CompanySerializer)
from retailcataloguemasters.serializers import (CategoryPurityRateSerializer)
from retailcataloguemasters.models import (Product,Design,SubDesign, Category,Stone, CategoryPurityRate,RepairDamageMaster,
                                           Purity)
from retailsettings.models import (RetailSettings)
from customers.models import (Customers, CustomerAddress)
from employees.models import (Employee)
from inventory.models import (ErpTagging,ErpTaggingStone,ErpTagOtherMetal,ErpTagAttribute,ErpTagCharges, ErpTaggingImages,
                              ErpTagSet, ErpTagSetItems)
from inventory.serializers import (ErpTaggingSerializer,ErpTagStoneSerializer,ErpTagOtherMetalSerializer,ErpTagAttributeSerializer,
                                   ErpTagChargesSerializer, ErpTaggingImagesSerializer)
from utilities.constants import FILTERS

from utilities.utils import format_date,date_format_with_time,base64_to_file, convert_tag_to_formated_data,calculate_item_cost,format_date_short_year
from .constants import (ACTION_LIST,ORDER_TOTAL_COLUMN_LIST,ORDER_COLUMN_LIST, CUSTOMER_CART_COLUMN_LIST, PURCHASE_CART_COLUMN_LIST, 
                        CUSTOMER_CART_ACTION_LIST, PURCHASEORDER_COLUMN_LIST, PURCHASEORDER_SOLD_PURCHASE_COLUMN_LIST)
from retailmasters.views import BranchEntryDate
from billing.views import insert_other_details,generate_issue_receipt_billno,ErpInvoiceCreateAPIView,ErpInvoiceOldMetalDetails,ErpInvoiceSalesDetails
from billing.models import ErpIssueReceipt,ErpIssueReceiptPaymentDetails
from billing.serializers import ErpIssueReceiptSerializer,ErpIssueReceiptPaymentDetailsSerializer,ErpInvoiceSerializer,ErpInvoiceOldMetalDetailsSerializer
from django.db.models import Count
from django.utils.timezone import now
from utilities.whatsapp_message import send_message_with_image
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile


pagination = PaginationMixin()
API_URL = "https://api.qikchat.in/v1/messages"
API_KEY = "JAux-Zc2i-aDXg"

class ErpOrderDropdownView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ERPOrder.objects.all()
    serializer_class = ErpOrdersSerializer
    
    def post(self, request, *args, **kwargs):
        branch = request.data['branch']
        customer = request.data['customer']
        fin_year = request.data['fin_year']

        queryset = ERPOrder.objects.filter(order_branch=branch, fin_year=fin_year, customer=customer)
        serializer = ErpOrdersSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ErpPurchaseOrderPurchaseSoldDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        product = request.data.get('product', None)
        # product = request.data['product']
        # if not product:
        #     return Response({"message": "Product ID is required"}, status=400)

        purchase_queryset = (
            ERPOrderDetails.objects
            .filter(product_id=product, order__order_type=2)
            .values('order__supplier__id_supplier', 'order__supplier__supplier_name')
            .annotate(
                total_gross_wt=Sum('gross_wt'),
                total_pieces=Sum('pieces')
            ).order_by('order__supplier__id_supplier')
            )
        
        sold_queryset = (
            ErpInvoiceSalesDetails.objects
            .filter(id_product=product, tag_id__isnull=False)
            .values('tag_id__id_supplier', 'tag_id__id_supplier__supplier_name')
            .annotate(
                total_gross_wt=Sum('gross_wt'),
                total_pieces=Sum('pieces')
            )
            .order_by('tag_id__id_supplier')
            )
        
        purchase_data = {
            item['order__supplier__id_supplier']: {
                'supplier_name': item['order__supplier__supplier_name'],
                'purchased_wt': item['total_gross_wt'] or 0,
                'purchased_pieces': item['total_pieces'] or 0
            } for item in purchase_queryset
        }

        sold_data = {
            item['tag_id__id_supplier']: {
                'supplier_name': item['tag_id__id_supplier__supplier_name'],
                'sold_wt': item['total_gross_wt'] or 0,
                'sold_pieces': item['total_pieces'] or 0
            } for item in sold_queryset
        }

        results = []
        supplier_ids = set(purchase_data.keys()) | set(sold_data.keys())

        for supplier_id in supplier_ids:
            purchased = purchase_data.get(supplier_id, {})
            sold = sold_data.get(supplier_id, {})

            purchased_wt = purchased.get('purchased_wt', 0)
            purchased_pieces = purchased.get('purchased_pieces', 0)
            sold_wt = sold.get('sold_wt', 0)
            sold_pieces = sold.get('sold_pieces', 0)

            results.append({
                'supplier_id': supplier_id,
                'supplier_name': purchased.get('supplier_name') or sold.get('supplier_name', ''),
                'purchased_wt': purchased_wt,
                'purchased_pieces': purchased_pieces,
                'sold_wt': sold_wt,
                'sold_pieces': sold_pieces,
                'balance_wt': round(purchased_wt - sold_wt, 2),
                'balance_pieces': purchased_pieces - sold_pieces
            })
        paginator, page = pagination.paginate_queryset(results, request,None,PURCHASEORDER_SOLD_PURCHASE_COLUMN_LIST)

        output = []
        for index, data in enumerate(page):
            data.update({
                'sno': index + 1
            })
            output.append(data)
        filters_copy = FILTERS.copy()
        filters_copy['isProductFilterReq'] = True
        
        actions_copy = ACTION_LIST.copy()
        actions_copy['is_add_req'] = False
        actions_copy['is_edit_req'] = False
        context={
            'columns':PURCHASEORDER_SOLD_PURCHASE_COLUMN_LIST,
            'actions':actions_copy,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':filters_copy
            }
        return pagination.paginated_response(output,context)
    
class ErpPurchaseOrderListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ERPOrder.objects.all()
    serializer_class = ErpOrdersSerializer
    
    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        id_branch = (id_branch) if id_branch != '' else 1

        queryset = ERPOrder.objects.filter(order_type=2)
        if from_date and to_date:
                queryset = queryset.filter(order_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(order_branch__in=id_branch)
        else:
            queryset = queryset.filter(order_branch=id_branch)

        output = []
        paginator, page = pagination.paginate_queryset(queryset, request,None,PURCHASEORDER_COLUMN_LIST)
        serializer = ErpOrdersSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            supplier = Supplier.objects.filter(id_supplier=data['supplier']).first()
            data.update({"pk_id":data['order_id'], "sno":index+1})
            if  data['order_type'] == 1:
                data.update({"order_type":"Customer Order"})
            elif  data['order_type'] == 2:
                data.update({"order_type":"Purchase Order"})
            elif  data['order_type'] == 3:
                data.update({"order_type":"Repair Order"})
            else:
                data.update({"order_type":"Customized Order"})
            data.update({"supplier_name":supplier.supplier_name})
            if data not in output:
                output.append(data)
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        
        actions_copy = ACTION_LIST.copy()
        actions_copy['is_print_req'] = True
        context={
            'columns':PURCHASEORDER_COLUMN_LIST,
            'actions':actions_copy,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(output,context)

class ErpPurchaseOrderDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def update_deleted_details(self, item_details, order_id):
        existing_items = ERPOrderDetails.objects.filter(order=order_id)
        existing_item_map = {item.pk: item for item in existing_items}
        ids_to_delete = set(existing_item_map.keys())
        print(ids_to_delete)
        for detail in item_details:
            item_id = detail.get('detail_id')
            if item_id:
                ids_to_delete.discard(item_id)
        if ids_to_delete:
            print('delete')
            print(ids_to_delete)
            ERPOrderDetails.objects.filter(pk__in=ids_to_delete).delete() 
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = ErpOrdersSerializer(queryset)
        order_detail = ERPOrderDetails.objects.filter(order=queryset.order_id)
        order_detail_serializer = ErpOrdersDetailSerializer(order_detail, many=True)
        output = serializer.data
        order_details = []
        
        for details in order_detail_serializer.data:
            product = Product.objects.get(pro_id=details['product'])
            details.update({"cat_id":product.cat_id.pk})
            if details not in order_details:
                order_details.append(details)
        output.update({"order_details":order_details})
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            order_details = request.data['order_details']
            del request.data['order_details']
            queryset = self.get_object()
            request.data.update({"updated_by": request.user.pk, "updated_on":datetime.now(tz=timezone.utc)})
            
            ERPOrder.objects.filter(order_id=queryset.order_id).update(
                supplier                    = request.data.get('supplier'),
                updated_by                  = request.user.pk,
                updated_on                  = datetime.now(tz=timezone.utc)
            )
            if order_details:
                self.update_deleted_details(order_details, queryset.order_id)
            for details in order_details:
                if details['detail_id']!='':
                                      
                    order_detail = ERPOrderDetails.objects.get(detail_id=details['detail_id'])
                    details.update({"order":queryset.order_id})
                    details.update({"order_status":4})
                    order_detail_serializer = ErpOrdersDetailSerializer(order_detail, data=details)
                    order_detail_serializer.is_valid(raise_exception=True)
                    order_detail_serializer.save()
                else:
                    order_create = ErpOrderCreateView()
                    order_create.insert_order_details(details,queryset.order_id)
            return Response({"message":"Order Updated successfully."}, status=status.HTTP_200_OK)
    
class ErpPurchaseOrderPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def generate_order_print(self, order_id, serializer, output, request):
        order_details_qs = ERPOrderDetails.objects.filter(order=order_id)
        order_details_serialized = ErpOrdersDetailSerializer(order_details_qs, many=True).data

        branch = Branch.objects.filter(id_branch=serializer.data['order_branch']).first()
        supplier = Supplier.objects.filter(id_supplier=serializer.data['supplier']).first()
        company = Company.objects.latest("id_company")

        
        address = (
            f"{supplier.address1 or ''} {supplier.address2 or ''} {supplier.address3 or ''}".strip()
            if supplier.address1 else None
        )
        output.update({"address": address})

        # Set order type label
        order_type_labels = {1: "Customer Order", 2: "Purchase Order", 3: "Repair Order"}
        output.update({"order_type_label": order_type_labels.get(serializer.data['order_type'], "Unknown Order"),
                       'order_date':(serializer.data['order_date'])})

        # Calculate totals
        totals = defaultdict(float)
        order_details = []

        for details in order_details_serialized:
            if Product.objects.filter(pro_id=details['product']).exists():
                product = Product.objects.get(pro_id=details['product'])
                details.update({"cat_id": product.cat_id.pk})

            totals["total_pcs"] += int(details['pieces'])
            totals["total_gross_wt"] += float(details['gross_wt'])
            totals["total_net_wt"] += float(details['net_wt'])
            # totals["total_less_wt"] += float(details['less_wt'])
            # totals["total_mc"] += float(details['mc_value'])
            # totals["total_item_cost"] += float(details['item_cost'])

            order_details.append(details)

        output.update({
            "order_details": order_details,
            "total_pcs": f"{totals['total_pcs']:.0f}",
            "total_gross_wt": f"{totals['total_gross_wt']:.3f}",
            "total_net_wt": f"{totals['total_net_wt']:.3f}",
            # "total_less_wt": f"{totals['total_less_wt']:.3f}",
            # "total_item_cost": f"{totals['total_item_cost']:.2f}",
            # "total_mc": f"{totals['total_mc']:.2f}",
            "branch_name": branch.name,
            "supplier_name": supplier.supplier_name,
            "mobile": supplier.mobile_no,
            "company_name": company.short_code,
            # 'company_detail': company,
        })

        order_folder = "erp_purchase_order"
        save_dir = os.path.join(settings.MEDIA_ROOT, order_folder, str(serializer.data['order_no']))
        os.makedirs(save_dir, exist_ok=True)

        template = get_template('purchase_order_print.html')
        
        html = template.render(output)

        pdf_path = os.path.join(save_dir, f"{order_folder}.pdf")
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)

        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
            
        final_pdf_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{serializer.data['order_no']}/{order_folder}.pdf")

        # return request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{serializer.data['order_no']}/{order_folder}.pdf")
        return {"response_data":output,
                "pdf_url":final_pdf_url}

    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = ErpOrdersSerializer(queryset)
        output = serializer.data
        order_pdf_path = self.generate_order_print(queryset, serializer, output, request)
        response_data = { 'pdf_url': order_pdf_path['pdf_url'],
                         'response_data':order_pdf_path['response_data']}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
    
class ErpPurchaseOrderDeleteView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            order_detail = ERPOrderDetails.objects.filter(order=queryset.order_id)
            order_detail_serializer = ErpOrdersDetailSerializer(order_detail, many=True)
            for data in order_detail_serializer.data:
                print()
                # ERPOrderStoneDetails.objects.filter(order_detail=data['detail_id']).delete()
                # ERPOrderCharges.objects.filter(order_detail=data['detail_id']).delete()
                # ERPOrderAttribute.objects.filter(order_detail=data['detail_id']).delete()
                # ERPOrderImages.objects.filter(order_detail=data['detail_id']).delete()
                # # Video And Audio
                # ERPOrderVideos.objects.filter(order_detail=data['detail_id']).delete()
                # ERPOrderAudios.objects.filter(order_detail=data['detail_id']).delete()
                # ErpOrderOtherMetal.objects.filter(order_detail=data['detail_id']).delete()
            ERPOrderDetails.objects.filter(order=queryset.order_id).delete()
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Order instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class PurchaseOrderStatusListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        output = []
        karigar_fil = request.data.get('karigar',None)
        product_fil = request.data.get('product',None)
        branch_fil = request.data.get('branch',None)
        date = request.data.get('date',None)
        from_date = request.data.get('from_date',None)
        to_date = request.data.get('to_date',None)
        
        order_query = ERPOrder.objects.filter(order_type=2)
        if from_date != None and to_date!=None:
            order_query = order_query.filter(order_date__lte=to_date, order_date__gte=from_date)
        if karigar_fil != None and karigar_fil!='':
            order_query = order_query.filter(supplier=karigar_fil)
        if branch_fil != None:
            order_query = order_query.filter(order_branch=branch_fil)
        order_serializer = ErpOrdersSerializer(order_query, many=True)
        
        for data in order_serializer.data:
            supplier = Supplier.objects.filter(id_supplier=data['supplier']).first()
            order_detail_query = ERPOrderDetails.objects.filter(order=data['order_id'])
            if product_fil != None and product_fil != '':
                order_detail_query = order_detail_query.filter(product=product_fil)
            order_detail_serializer = ErpOrdersDetailSerializer(order_detail_query, many=True)
            for details in order_detail_serializer.data:
                instance = {}
                order_status = ERPOrderStatus.objects.get(id=details['order_status'])
                instance.update({"assign_status":{"label":order_status.name, "value":order_status.pk}})
                instance.update({"pieces":details['pieces'],"cancel_reason": '', "isChecked":False,
                     "gross_wt":details['gross_wt'], "net_wt":details['net_wt'], "detail_id":details['detail_id'],
                     "date":format_date(data['order_date']),"karigar_due_date":format_date(details['karigar_due_date']),
                     "order_no":data['order_no'], "order_status":details['order_status'],
                     'karigar':supplier.supplier_name, "product_name":details['product_name']})
        
                if instance not in output:
                    output.append(instance)
        sorted_output = sorted(output, key=lambda x: x['detail_id'], reverse=True)
        return Response(sorted_output, status=status.HTTP_200_OK)

class PurchaseOrderStatusUpdateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            for data in request.data:
                if(data['status'] == 6):
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=6,updated_by=request.user.pk, updated_on = datetime.now(tz=timezone.utc),
                                                                                       cancel_reason=data['cancel_reason'], cancelled_by=request.user.pk, cancelled_date=date.today())
                    
                if(data['status'] == 5 and data['added_through']==1):
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=5,updated_by=request.user.pk, updated_on = datetime.now(tz=timezone.utc),
                                                                                       delivered_on=date.today())
            return Response({"message":"Purchase Orders Status Updated successfully."}, status=status.HTTP_200_OK)

class ErpOrderListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ERPOrder.objects.all()
    serializer_class = ErpOrdersSerializer

    def get(self, request, *args, **kwargs):
        order_no = request.query_params.get('order_no')
        id_branch = request.query_params.get('id_branch')
        if not order_no:
            return Response({"error": "Order no is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"error": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ERPOrder.objects.filter(order_no=order_no,order_branch=id_branch)
            if request.data.get('order_type'):
                queryset = queryset.filter(order_type=request.data['order_type'])
            serializer = ErpOrdersSerializer(queryset,many=True)
            return Response(serializer.data[0], status=status.HTTP_200_OK)
        except ERPOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        customer = request.data.get('customer')
        id_branch = (id_branch) if id_branch != '' else 1

        queryset = ERPOrder.objects.filter(order_type=1).order_by('-pk')
        if from_date and to_date:
                queryset = queryset.filter(order_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(order_branch__in=id_branch)
        else:
            queryset = queryset.filter(order_branch=id_branch)

        if customer:
            queryset = queryset.filter(customer=customer)

        output = []
        paginator, page = pagination.paginate_queryset(queryset, request,None,ORDER_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,ORDER_COLUMN_LIST,request.data.get('path_name',''))
        serializer = ErpOrdersSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data['is_editable'] = 1
            if ERPOrderDetails.objects.filter(order=data['order_id']).exclude(order_status= 1).exists():
                data['is_editable'] = 0
            data.update({"pk_id":data['order_id'], "sno":index+1})
            if  data['order_type'] == 1:
                data.update({"order_type":"Customer Order"})
            # elif  data['order_type'] == 2:
            #     data.update({"order_type":"Purchase Order"})
            elif  data['order_type'] == 3:
                data.update({"order_type":"Repair Order"})
            else:
                data.update({"order_type":"Customized Order"})
            if data not in output:
                output.append(data)
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isCustomerFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        
        actions_copy = ACTION_LIST.copy()
        actions_copy['is_print_req'] = True
        context={
            'columns':columns,
            'actions':actions_copy,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(output,context) 
    
    
    
class ErpOrderCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    serializer_class = ErpOrdersSerializer


    def get(self, request, *args, **kwargs):
        order_id = self.kwargs.get('pk')
        queryset = ERPOrder.objects.get(order_id=order_id)
        serializer = ErpOrdersSerializer(queryset)
        output = serializer.data
        est_url = ''
        if(queryset.order_type==1):
            est_url = self.generate_custom_order_print(order_id,serializer,output,request)
        if(queryset.order_type==3):
            est_url = self.generate_repair_order_print(order_id,serializer,request)
        response_data = { "response_data" : est_url['response_data'] }
        return Response(response_data, status=status.HTTP_200_OK)

    def generate_custom_order_print(self, order_id, serializer, output, request):
        metal_rate_type = int(RetailSettings.objects.get(name='metal_rate_type').value)
        metalrates = MetalRates.objects.all().latest('rate_id')
        metalrates_serializer = MetalRatesSerializer(metalrates)
        category_rates_data = {}
        category_rates = CategoryPurityRate.objects.filter(show_in_listing=True)
        category_rates_serializer = CategoryPurityRateSerializer(category_rates, many=True)
        
        order_details_qs = ERPOrderDetails.objects.filter(order=order_id)
        order_details_serialized = ErpOrdersDetailSerializer(order_details_qs, many=True).data

        old_metal_details = ErpInvoiceOldMetalDetails.objects.filter(order=order_id)
        old_metal_details_serializer = ErpInvoiceOldMetalDetailsSerializer(old_metal_details, many=True).data
        
        total_stone_amnt = float(0)
        
        advance = ErpIssueReceipt.objects.filter(order=order_id).all()
        advance_serializer = ErpIssueReceiptSerializer(advance, many=True).data
        payment_serializer = []
        payment_amount = 0
        if len(advance_serializer) > 0:
            for advance_data in advance_serializer:
                payment = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt=advance_data['id']).all()
                payment_serializer = ErpIssueReceiptPaymentDetailsSerializer(payment, many=True).data
        
       
        if len(payment_serializer) > 0:
    
            for pay in payment_serializer:
                mode_obj = PaymentMode.objects.filter(id_mode=pay['payment_mode']).first()
                payment_amount +=float(pay['payment_amount'])
                pay.update({
                "mode_name":mode_obj.mode_name
                })
        
        branch = Branch.objects.filter(id_branch=serializer.data['order_branch']).first()
        customer = Customers.objects.filter(id_customer=serializer.data['customer']).first()
        comp = Company.objects.get(id_company=1)

        # Get customer address
        company_strip_address = None
        customer_address = CustomerAddress.objects.filter(customer=customer.pk).first()
        if customer_address != None :
            
            address1 = customer_address.line1 if (customer_address.line1 and customer_address.line1 != None and customer_address.line1 != '') else ''
            address2 = customer_address.line2 if (customer_address.line2 and customer_address.line2 != None and customer_address.line2 != '') else ''
            address3 = customer_address.line3 if (customer_address.line3 and customer_address.line3 != None and customer_address.line3 != '') else ''
            company_strip_address = (
            f"{address1} {address2} {address3}, {customer_address.city.name}, {customer_address.state.name}. {customer_address.pincode}".strip()
            )
            if customer_address.line1!=None and customer_address.line1!='':
                output.update({"cus_address1":customer_address.line1})
            if customer_address.line2!=None and customer_address.line2!='':
                output.update({"cus_address2":customer_address.line2})
            if customer_address.line3!=None and customer_address.line2!='':
                output.update({"cus_address3":customer_address.line3})
            if customer_address.city!=None and customer_address.city!='':
                output.update({"city":customer_address.city.name})
            if customer_address.pincode!=None and customer_address.pincode!='':
                output.update({"pin_code":customer_address.pincode})
            if customer_address.area!=None and customer_address.area!='':
                output.update({"area":customer_address.area.area_name})
        output.update({"address": company_strip_address})

        # Set order type label
        order_type_labels = {1: "Customer Order", 2: "Purchase Order", 3: "Repair Order"}
        output.update({"order_type_label": order_type_labels.get(serializer.data['order_type'], "Order")})

        # Calculate totals
        totals = defaultdict(float)
        order_details = []
        remarks_list = []
        total_old_metal_cost = 0
        metal_type = None
        for index,details in enumerate(order_details_serialized):
            details.update({"sno": index+1})
            item_stn_amnt = float(0)
            if(ERPOrderStoneDetails.objects.filter(order_detail=details['detail_id']).exists()):
                stone_query = ERPOrderStoneDetails.objects.filter(order_detail=details['detail_id'])
                stone_serializer = ErpOrderStoneSerializer(stone_query, many=True)
                for stn in stone_serializer.data:
                    total_stone_amnt +=float(stn['stone_amnt'])
                    item_stn_amnt +=float(stn['stone_amnt'])
            details.update({"item_stn_amnt": f"{item_stn_amnt:.2f}"})
            remarks_inst = {}
            remarks_inst.update({"remark": details['remarks']})
            if Product.objects.filter(pro_id=details['product']).exists():
                product = Product.objects.get(pro_id=details['product'])
                metal_type = product.id_metal.pk
                details.update({"cat_id": product.cat_id.pk})
            totals["customer_due_date"] =details['customer_due_date']
            totals["total_pcs"] += int(details['pieces'])
            totals["total_gross_wt"] += float(details['gross_wt'])
            totals["total_net_wt"] += float(details['net_wt'])
            totals["total_less_wt"] += float(details['less_wt'])
            totals["total_wastage_wt"] += float(details['wastage_wt'])
            totals["total_mc"] += float(details['mc_value'])
            totals["total_item_cost"] += float(details['item_cost'])
            totals["taxable_amnt"] += float(details['taxable_amnt'])
            totals["tax_amnt"] += float(details['tax_amnt'])
            totals["sgst_cost"] += float(details['sgst_amnt'])
            totals["cgst_cost"] += float(details['cgst_amnt'])
            totals["igst_cost"] += float(details['igst_amnt'])
            totals["tax_per"] += float(details['tax_percent'])

            order_details.append(details)
            if remarks_inst not in remarks_list:
                remarks_list.append(remarks_inst)
        
        for old_metal in old_metal_details_serializer:
            total_old_metal_cost += float(old_metal['amount'])
        
            
        for cat_rate_item in category_rates_serializer.data:
            category_obj = Category.objects.filter(id_category=cat_rate_item['category']).first()
            if category_obj.cat_code == 'GO':
                category_rates_data.update({
                    "gold_rate":cat_rate_item['rate_per_gram']
                })
            if category_obj.cat_code == 'SO':
                category_rates_data.update({
                    "silver_rate":cat_rate_item['rate_per_gram']
                })
            if category_obj.cat_code == 'GC':
                category_rates_data.update({
                    "gold_coin":cat_rate_item['rate_per_gram']
                })
            if category_obj.cat_code == 'SC':
                category_rates_data.update({
                    "silver_coin":cat_rate_item['rate_per_gram']
                })
                
        company = Company.objects.latest("id_company")
        company_serializer = CompanySerializer(company, context={'request':request})
        state = State.objects.latest("id_state")
        emp = Employee.objects.filter(user =serializer.data['created_by']).first()
        emp_name = emp.firstname
        emp_code = emp.emp_code
        
        output.update({
            "due_date": format_date_short_year(totals["customer_due_date"]),
            "date": format_date_short_year(output["order_date"]),
            "old_metal_details" : old_metal_details_serializer,
            "order_details": order_details,
            "total_pcs": f"{totals['total_pcs']:.0f}",
            "total_gross_wt": f"{totals['total_gross_wt']:.3f}",
            "total_wastage_wt": f"{totals['total_wastage_wt']:.3f}",
            "total_weight" : f"{totals['total_net_wt'] + totals['total_wastage_wt']:.3f}",
            "total_net_wt": f"{totals['total_net_wt']:.3f}",
            "total_less_wt": f"{totals['total_less_wt']:.3f}",
            "total_item_cost": f"{totals['total_item_cost']:.2f}",
            "tax_amnt": f"{totals['tax_amnt']:.2f}",
            "taxable_amnt": f"{totals['taxable_amnt']:.2f}",
            "sgst_cost": f"{totals['sgst_cost']:.2f}",
            "cgst_cost": f"{totals['cgst_cost']:.2f}",
            "igst_cost": f"{totals['igst_cost']:.2f}",
            "tax_per": f"{totals['tax_per']:.2f}",
            "total_old_metal_cost": f"{total_old_metal_cost:.2f}",
            "payment_amount": f"{payment_amount:.2f}",
            "total_stone_amnt": f"{total_stone_amnt:.2f}",
            "balance_amt" : f"{float(totals['total_item_cost']) - float(total_old_metal_cost) - float(payment_amount):.2f}",
            "total_mc": f"{totals['total_mc']:.2f}",
            "branch_name": branch.name,
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            "company_name" : comp.short_code,
            'metal_rates' : metalrates_serializer.data,
            'metal_rate_type' : metal_rate_type,
            'category_rates_data' : category_rates_data,
            'metal_type':metal_type,
            'payment_details':payment_serializer,
            'amount_in_words' : num2words(payment_amount, lang='en_IN') + " Only",
            'company_name' :   company.company_name,
            'company_strip_address' :   company_strip_address,
            'gst_number' :   company.gst_number,
            'company_mobile' :   company.mobile,
            'company_logo' :   company_serializer.data['image'],
            'remarks_list':remarks_list
        })

        

        return {"response_data":output}


    def generate_orderno(self, data, branch_code, fy, order_type):

        code = ''
        order_code_settings = RetailSettings.objects.get(name='order_code_settings').value
        fin_id = fy.fin_id
        last_order_code=None
        if order_code_settings == '1':#GENERATE CODE WITH FY, ORDER TYPE AND BRANCH
            last_order_code=ERPOrder.objects.filter(order_branch=data['order_branch'],fin_year=fin_id,
                                                   order_type=data['order_type']).order_by('-order_id').first()
        if last_order_code:
            last_order_code = last_order_code.order_no
            if last_order_code:
                code=last_order_code
                code = str(int(code) + 1).zfill(5)
            else:
               code = '00001'
        else:
            code = '00001'
        return code
 
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                if "added_through" in request.data:
                    added_through = request.data['added_through']
                else:
                    added_through = 1

                if "order_branch" not in request.data:
                    branch = Branch.objects.filter(is_ho=True).first()
                    data = request.data.copy()
                    data["order_branch"] = branch.pk
                else:
                    data = request.data  
                print(request.user.pk)
                purchase_details = []
                payment_details = []

                if 'purchase_details' in request.data:
                    purchase_details = data['purchase_details']
                if 'payment_details' in request.data:
                    payment_details = data['payment_details']
                order_details = data['order_details'] 
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(data['order_branch'])
                fy=FinancialYear.objects.get(fin_status=True)
                branch = Branch.objects.get(id_branch=data['order_branch'])
                order_no = self.generate_orderno(data, branch.short_name, fy, data['order_type'])
                data.update({"order_no":order_no,"order_date":entry_date, "created_by":request.user.pk, "fin_year":fy.pk})
                
                order_serializer = ErpOrdersSerializer(data=data)
                order_serializer.is_valid(raise_exception=True)
                if(order_serializer.save()):
                    for details in order_details:
                        if int(added_through)==1 or data['order_type']==4:
                            self.insert_order_details(details,order_serializer.data['order_id'],data['order_type'])
                        else:
                            if not ErpTagging.objects.filter(tag_id = details['erp_tag']).exists():
                                return Response({"message":"Tag Not Found"}, status=status.HTTP_400_BAD_REQUEST)
                            else:
                                tag_details_queryset = ErpTagging.objects.filter(tag_id = details['erp_tag']).first()
                                tag_serializer = ErpTaggingSerializer(tag_details_queryset)
                                tag_stone_queryset = ErpTaggingStone.objects.filter(tag_id = details['erp_tag'])
                                tag_stone_serializer = ErpTagStoneSerializer(tag_stone_queryset, many=True)
                                tag_stone_details = []
                                if len(tag_stone_serializer.data)>0:
                                    for tag_stone in tag_stone_serializer.data:
                                        stone_details = {}
                                        stone_type = Stone.objects.filter(stone_id=tag_stone['id_stone']).first()
                                        stone_details.update({
                                            "stone_type":stone_type.stone_type,
                                            "show_in_lwt":tag_stone['show_in_lwt'],
                                            "pieces":tag_stone['stone_pcs'],
                                            "stone_amnt":tag_stone['stone_amount'],
                                            "stone":tag_stone['id_stone'],
                                            "stone_calc_type":tag_stone['stone_calc_type'],
                                            "stone_wt":tag_stone['stone_wt'],
                                            "id_quality_code":tag_stone['id_quality_code'],
                                            "uom_id":tag_stone['uom_id'],
                                        })
                                        if(stone_details not in tag_stone_details):
                                            tag_stone_details.append(stone_details)
                                details.update({
                                    "purity":tag_serializer.data['tag_purity_id'],
                                    "product":tag_serializer.data['tag_product_id'],
                                    "design":tag_serializer.data['tag_design_id'],
                                    "size":tag_serializer.data['size'],
                                    "pieces":tag_serializer.data['tag_pcs'],
                                    "gross_wt":tag_serializer.data['tag_gwt'],
                                    "net_wt":tag_serializer.data['tag_nwt'],
                                    "less_wt":tag_serializer.data['tag_lwt'],
                                    "stone_wt":tag_serializer.data['tag_stn_wt'],
                                    "dia_wt":tag_serializer.data['tag_dia_wt'],
                                    "other_metal_wt":tag_serializer.data['tag_other_metal_wt'],
                                    "purchase_touch":tag_serializer.data['tag_purchase_touch'],
                                    "purchase_va":tag_serializer.data['tag_purchase_va'],
                                    "stone_details":tag_stone_details,
                                    "order_videos":[],
                                    "order_voices":[],
                                    "charges_details":[],
                                    "attribute_details":[],
                                    "other_metal_details":[],
                                    "order_images":[]
                                })
                                # print(details)
                                self.insert_order_details(details,order_serializer.data['order_id'],data['order_type'])
                                customer = Customers.objects.filter(user=request.user.id).first()
                                
                                
                                # cart_query = CustomerCart.objects.filter(customer=customer.pk)
                                if(CustomerCart.objects.filter(customer=customer.pk, erp_tag=details['erp_tag']).exists()):
                                    CustomerCart.objects.filter(customer=customer.pk, erp_tag=details['erp_tag']).delete()
                    if purchase_details:
                        billing = ErpInvoiceCreateAPIView()
                        invoice_data = {}
                        customer = Customers.objects.get(id_customer=data['customer'])
                        customer_name =  customer.firstname
                        customer_mobile =  customer.mobile   

                        invoice_data.update({
                            "fin_year":fy.pk,
                            "id_branch":data['order_branch'],  
                            "id_customer":data['customer'],
                            "invoice_for":1,
                            "purchase_amount":data['purchase_amount'],
                            "deposit_amount":data['purchase_amount'],
                            "net_amount":data['purchase_amount'],
                            "customer_mobile":customer_mobile,
                            "customer_name":customer_name,
                            "invoice_date":entry_date,
                            "metal":1,
                            "setting_bill_type":0,
                            "created_by":request.user.id
                        })

                        request.data.update({"invoice":invoice_data})
                        
                        invoice = billing.generate_invoice_no(data['order_branch'],fy,request,0)

                        inv_serializer = ErpInvoiceSerializer(data = invoice_data,context={"invoice_no":True})
                        if inv_serializer.is_valid(raise_exception=True):
                            inv_serializer.save()
                            erp_invoice_id = inv_serializer.data['erp_invoice_id']

                            for purchase in purchase_details :
                                purchase.update({"order":order_serializer.data['order_id']})
                            
                            purchase_details = billing.insert_purchase_details(purchase_details,erp_invoice_id,invoice_data)

                            if data['deposit_amount'] > 0: 

                                branch = Branch.objects.get(id_branch=data['order_branch'])

                                bill_no = generate_issue_receipt_billno({'branch':data['order_branch'],'type':2,'setting_bill_type':invoice_data['setting_bill_type']}, branch.short_name, fy, 1)

                                deposit_details = { 
                                    'type':2,
                                    'receipt_type':2,
                                    'order':order_serializer.data['order_id'],
                                    'fin_year':fy.fin_id,
                                    'bill_date':entry_date,
                                    'branch':data['order_branch'],
                                    'bill_no':bill_no,
                                    'customer':data['customer'],
                                    'deposit_bill':erp_invoice_id,
                                    'amount':data['deposit_amount'],
                                    'weight':0,
                                    "created_by": request.user.id,
                                    'id_counter' : request.data.get('id_counter', None),
                                }

                                deposit_details = insert_other_details([deposit_details],ErpIssueReceiptSerializer,{"invoice_bill_id":erp_invoice_id})

                
                    if payment_details:
                        branch = Branch.objects.get(id_branch=data['order_branch'])

                        bill_no = generate_issue_receipt_billno({'branch':data['order_branch'],'type':2,'setting_bill_type':1}, branch.short_name, fy, 1)
                        deposit_details = { 
                            'type':2,
                            'receipt_type':2,
                            'order':order_serializer.data['order_id'],
                            'fin_year':fy.fin_id,
                            'bill_date':entry_date,
                            'branch':data['order_branch'],
                            'bill_no':bill_no,
                            'customer':data['customer'],
                            'amount':data['payment_amount'],
                            'weight':0,
                            "created_by": request.user.id,
                            'id_counter' : request.data.get('id_counter', None),
                        }

                        deposit_details = insert_other_details([deposit_details],ErpIssueReceiptSerializer,{"order":order_serializer.data['order_id']})
                        for payment_data in payment_details:
                            payment_data.update({
                                "issue_receipt":deposit_details[0]['id'],
                                "type": 1 
                            })
                            payment_detail_serializer = ErpIssueReceiptPaymentDetailsSerializer(data=payment_data)
                            payment_detail_serializer.is_valid(raise_exception=True)
                            payment_detail_serializer.save()

                order_pdf_path = ''
            
                if data['order_type']==3:
                    order_pdf_path = self.generate_repair_order_print(order_serializer.data['order_id'],order_serializer,request) 
                    return Response({"status":True,"message":"Order Created Successfully","order_id":order_serializer.data['order_id'],"pdf_url":order_pdf_path['pdf_url'],"pdf_path":"orders/order/print", "print_data":order_pdf_path['response_data']}, status=status.HTTP_200_OK)
                if data['order_type']==1:
                    response = self.generate_custom_order_print(order_serializer.data['order_id'],order_serializer,order_serializer.data,request)            
                    return Response({"status":True,"message":"Order Created Successfully","order_id":order_serializer.data['order_id'],"pdf_url":order_pdf_path,"pdf_path":"orders/order/print","print_data":response['response_data']}, status=status.HTTP_200_OK)
                if data['order_type']==2:
                    purchase_order_view = ErpPurchaseOrderPrintView()
                    response = purchase_order_view.generate_order_print(order_serializer.data['order_id'], order_serializer, order_serializer.data, request)
                    return Response({"status":True,"message":"Order Created Successfully","order_id":order_serializer.data['order_id'],"pdf_url":response['pdf_url'],"pdf_path":"orders/order/print", "print_data":response['response_data']}, status=status.HTTP_200_OK)
                if data['order_type']==4:
                    return Response({"status":True,"message":"Order Created Successfully","order_id":order_serializer.data['order_id']}, status=status.HTTP_200_OK)
            except KeyError as e:
                transaction.set_rollback(True)
                tb = traceback.extract_tb(sys.exc_info()[2])[-1]
                line_number = tb.lineno
                return Response({"status":False,"message": f"Missing key: {e} at line {line_number}"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                transaction.set_rollback(True)
                tb = traceback.extract_tb(sys.exc_info()[2])[-1]
                line_number = tb.lineno
                return Response({"status":False,"message": f"An unexpected error occurred: {str(e)} {line_number} "}, status=status.HTTP_400_BAD_REQUEST)
            
    def insert_order_details(self,details,order_id,order_type):   
        stone_details = details['stone_details']
        charges_details = details['charges_details']
        attribute_details = details['attribute_details']
        other_metal_details = details['other_metal_details']

        order_images = details.get('order_images', [])
        order_videos = details.get('order_videos', [])
        order_audios = details.get('order_voices', [])

        del details['order_images']
        if "erp_tag" in details and  details['erp_tag']!='' and details['erp_tag']!=None:
            details.update({"is_reserved_item":True,"order_status":4})
        else:
            if order_type==2:
                details.update({"order_status":3})
            else:
                details.update({"order_status":1})
        
        other_metal_amount = 0
        for metal_val in other_metal_details:
            other_amounts = 0
            other_amounts += float(metal_val['other_metal_cost'])
            other_metal_amount += other_amounts
        
        if(details.get('tax')):
            tax_obj = Taxmaster.objects.get(tax_id=details['tax'])
            details.update({"tax_percent":tax_obj.tax_percentage,})    
        
        details.update({
            "order": order_id,
            # "uom_id": details['uom'] if details.get('uom') not in [None, '', 'undefined'] else None,
            "other_metal_amnt": round(other_metal_amount, 3)
        })
        order_detail_serializer = ErpOrdersDetailSerializer(data=details)
        order_detail_serializer.is_valid(raise_exception=True)
        if (order_detail_serializer.save()):
            if "erp_tag" in details and details['erp_tag']!='':
                ErpTagging.objects.filter(tag_id=details['erp_tag']).update(tag_order_det=order_detail_serializer.data['detail_id'])
            for stones in stone_details:
                stones.update({"order_detail":order_detail_serializer.data['detail_id']})
                stone_serializer = ErpOrderStoneSerializer(data=stones)
                stone_serializer.is_valid(raise_exception=True)
                stone_serializer.save()
            
            for charges in charges_details:
                charges.update({"order_detail":order_detail_serializer.data['detail_id']})
                charges_serializer = ErpOrderChargesSerializer(data=charges)
                charges_serializer.is_valid(raise_exception=True)
                charges_serializer.save()
            
            for attribute in attribute_details:
                attribute.update({"order_detail":order_detail_serializer.data['detail_id']})
                attribute_serializer = ErpOrderAttributeSerializer(data=attribute)
                attribute_serializer.is_valid(raise_exception=True)
                attribute_serializer.save()  
                
            for metals in other_metal_details:
                metals.update({"order_detail":order_detail_serializer.data['detail_id']})
                metals_serializer = ErpOrderOtherMetalSerializer(data=metals)
                metals_serializer.is_valid(raise_exception=True)
                metals_serializer.save() 
            
            for index, images in enumerate(order_images):    
                # if order_images:
                    try:
                        # first_image = order_images[0]
                        file_content = base64_to_file(images['base64'], filename_prefix="myfile",file_extension="jpg")
                    
                        image_data = {
                            "image": file_content,
                            "name": f"{now().strftime('%Y%m%d%H%M%S')}",
                            "order_detail": order_detail_serializer.data['detail_id']
                        }
                        image_serializer = ErpOrderImagesSerializer(data=image_data)
                        image_serializer.is_valid(raise_exception=True)
                        image_serializer.save()
                    except Exception as e:
                        return Response({"error": f"An unexpected error occurred: {str(e)}"})


            for index, video in enumerate(order_videos):
                # if order_videos:
                    try:
                        # first_video = order_videos[0]
                        file_content = base64_to_file(video['base64'], filename_prefix="myfile",file_extension="mp4")

                        video_data = {
                            "video": file_content,
                            "name": f"{now().strftime('%Y%m%d%H%M%S')}",
                            "order_detail": order_detail_serializer.data['detail_id']
                        }
                        video_serializer = ERPOrderVideosSerializer(data=video_data)
                        video_serializer.is_valid(raise_exception=True)
                        video_serializer.save()
                    except Exception as e:
                        print(f"❌ Error processing video: {e}")
            
            for index, audio in enumerate(order_audios):
                # if order_audios:
                    try:
                        # first_audio = order_audios[0]  
                        file_content = base64_to_file(audio['base64'], filename_prefix="myfile",file_extension="mp3")

                        audio_data = {
                            "audio": file_content,
                            "name": f"{now().strftime('%Y%m%d%H%M%S')}",
                            "order_detail": order_detail_serializer.data['detail_id']
                        }
                        audio_serializer = ERPOrderAudiosSerializer(data=audio_data)
                        audio_serializer.is_valid(raise_exception=True)
                        audio_serializer.save()
                    except Exception as e:
                        print(f"❌ Error processing audio: {e}")


    
    def generate_repair_order_print(self,order_id,serializer,request):
        output = serializer.data
        order_details_qs = ERPOrderDetails.objects.filter(order=order_id)
        order_details_serialized = ErpOrdersDetailSerializer(order_details_qs, many=True).data

        branch = Branch.objects.filter(id_branch=serializer.data['order_branch']).first()
        customer = Customers.objects.filter(id_customer=serializer.data['customer']).first()
        company = Company.objects.latest("id_company")

        # Get customer address
        customer_address = CustomerAddress.objects.filter(customer=customer.pk).first()
        address = (
            f"{customer_address.line1 or ''} {customer_address.line2 or ''} {customer_address.line3 or ''}".strip()
            if customer_address else None
        )
        output.update({"address": address})

        # Set order type label
        order_type_labels = {1: "Customer Order", 2: "Purchase Order", 3: "Repair Order"}
        output.update({"order_type_label": order_type_labels.get(serializer.data['order_type'], "Unknown Order")})

        # Calculate totals
        totals = defaultdict(float)
        order_details = []

        for details in order_details_serialized:

            repair_type_ids  = details['order_repair_type']
            repair_items = RepairDamageMaster.objects.filter(id_repair__in=repair_type_ids)
            repair_names = ", ".join(repair_items.values_list("name", flat=True))
            details.update({
                "repair_name":repair_names,
            })  
            
            if Product.objects.filter(pro_id=details['product']).exists():
                product = Product.objects.get(pro_id=details['product'])
                details.update({"cat_id": product.cat_id.pk})
            else:
                details.update({"product_name":details['customized_product_name']})

            totals["total_pcs"] += int(details['pieces'])
            totals["total_gross_wt"] += float(details['gross_wt'])
            totals["total_net_wt"] += float(details['net_wt'])
            totals["total_less_wt"] += float(details['less_wt'])
            totals["total_mc"] += float(details['mc_value'])
            totals["total_item_cost"] += float(details['item_cost'])

            order_details.append(details)

        output.update({
            "order_details": order_details,
            "total_pcs": f"{totals['total_pcs']:.0f}",
            "total_gross_wt": f"{totals['total_gross_wt']:.3f}",
            "total_net_wt": f"{totals['total_net_wt']:.3f}",
            "total_less_wt": f"{totals['total_less_wt']:.3f}",
            "total_item_cost": f"{totals['total_item_cost']:.2f}",
            "total_mc": f"{totals['total_mc']:.2f}",
            "branch_name": branch.name,
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            "company_name": company.short_code,
            # 'company_detail': company,
        })

        order_folder = "erp_repair_order" if serializer.data['order_type'] == 3 else "erp_order"
        save_dir = os.path.join(settings.MEDIA_ROOT, order_folder, str(order_id))
        os.makedirs(save_dir, exist_ok=True)
        template = get_template('repair_print.html')
        html = template.render(output)
        pdf_path = os.path.join(save_dir, f"{order_folder}.pdf")
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)

        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())

        final_pdf_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{order_id}/{order_folder}.pdf")
        return {"response_data":output,
                "pdf_url":final_pdf_url}
        # return request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{order_id}/{order_folder}.pdf")


    
                
class ErpOrderDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = ErpOrdersSerializer(queryset)
        order_detail = ERPOrderDetails.objects.filter(order=queryset.order_id)
        order_detail_serializer = ErpOrdersDetailSerializer(order_detail, many=True)
        output = serializer.data
        order_details = []
        
        for details in order_detail_serializer.data:
            product = Product.objects.get(pro_id=details['product'])
            details.update({"cat_id":product.cat_id.pk})
            if(ERPOrderStoneDetails.objects.filter(order_detail=details['detail_id']).exists()):
                stone_query = ERPOrderStoneDetails.objects.filter(order_detail=details['detail_id'])
                stone_serializer = ErpOrderStoneSerializer(stone_query, many=True)
                details.update({"stone_details":stone_serializer.data})
            if(ERPOrderCharges.objects.filter(order_detail=details['detail_id']).exists()):
                charge_query = ERPOrderCharges.objects.filter(order_detail=details['detail_id'])
                charge_serializer = ErpOrderChargesSerializer(charge_query, many=True)
                details.update({"charge_details":charge_serializer.data})
            if(ERPOrderAttribute.objects.filter(order_detail=details['detail_id']).exists()):
                attribute_query = ERPOrderAttribute.objects.filter(order_detail=details['detail_id'])
                attribute_serializer = ErpOrderAttributeSerializer(attribute_query, many=True)
                details.update({"attribute_details":attribute_serializer.data})
            if(ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists()):
                image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id'])
                image_serializer = ErpOrderImagesSerializer(image_query, many=True, context={"request":request})
                details.update({"image_details":image_serializer.data})
                # video and audio
            if(ERPOrderVideos.objects.filter(order_detail=details['detail_id']).exists()):
                video_query = ERPOrderVideos.objects.filter(order_detail=details['detail_id'])
                video_serializer = ERPOrderVideosSerializer(video_query, many=True, context={"request":request})
                details.update({"video_details":video_serializer.data})
            if(ERPOrderAudios.objects.filter(order_detail=details['detail_id']).exists()):
                audio_query = ERPOrderAudios.objects.filter(order_detail=details['detail_id'])
                audio_serializer = ERPOrderAudiosSerializer(audio_query, many=True, context={"request":request})
                details.update({"audio_details":audio_serializer.data})
            if details not in order_details:
                order_details.append(details)
    
        output.update({"order_details":order_details})
        return Response(output, status=status.HTTP_200_OK)
    
class ErpOrderDeleteView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            order_detail = ERPOrderDetails.objects.filter(order=queryset.order_id)
            order_detail_serializer = ErpOrdersDetailSerializer(order_detail, many=True)
            for data in order_detail_serializer.data:
                ERPOrderStoneDetails.objects.filter(order_detail=data['detail_id']).delete()
                ERPOrderCharges.objects.filter(order_detail=data['detail_id']).delete()
                ERPOrderAttribute.objects.filter(order_detail=data['detail_id']).delete()
                ERPOrderImages.objects.filter(order_detail=data['detail_id']).delete()
                # Video And Audio
                ERPOrderVideos.objects.filter(order_detail=data['detail_id']).delete()
                ERPOrderAudios.objects.filter(order_detail=data['detail_id']).delete()
                ErpOrderOtherMetal.objects.filter(order_detail=data['detail_id']).delete()
            ERPOrderDetails.objects.filter(order=queryset.order_id).delete()
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Order instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ErpOrderEditView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            order_details = request.data['order_details']
            del request.data['order_details']
            queryset = self.get_object()
            request.data.update({"updated_by": request.user.pk, "updated_on":datetime.now(tz=timezone.utc)})
            
            ERPOrder.objects.filter(order_id=queryset.order_id).update(
                customer                    = request.data.get('customer'),
                is_rate_fixed_on_order      = request.data.get('is_rate_fixed_on_order'),
                updated_by                  = request.user.pk,
                updated_on                  = datetime.now(tz=timezone.utc)
            )
            if order_details:
                self.update_deleted_details(order_details, queryset.order_id)
            for details in order_details:
                stone_details = details['stone_details']
                charges_details = details['charges_details']
                attribute_details = details['attribute_details']
                other_metal_details = details['other_metal_details']
                order_images = details.get('order_images',[])
                order_videos = details.get('order_videos',[])
                order_voices = details.get('order_voices',[])
                if details['detail_id']!='':
                                      
                    order_detail = ERPOrderDetails.objects.get(detail_id=details['detail_id'])
                    
                    ERPOrderStoneDetails.objects.filter(order_detail=details['detail_id']).delete()
                    ERPOrderCharges.objects.filter(order_detail=details['detail_id']).delete()
                    ERPOrderAttribute.objects.filter(order_detail=details['detail_id']).delete()
                    ERPOrderImages.objects.filter(order_detail=details['detail_id']).delete()
                    ERPOrderAudios.objects.filter(order_detail=details['detail_id']).delete()
                    ERPOrderVideos.objects.filter(order_detail=details['detail_id']).delete()
                    ErpOrderOtherMetal.objects.filter(order_detail=details['detail_id']).delete()
                    
                    other_metal_amount = 0
                        
                  
                    for metal_metal in other_metal_details:
                        other_amounts = 0
                        other_amounts += float(metal_metal['other_metal_cost'])
                        other_metal_amount += other_amounts

                    details.update({"order":queryset.order_id})
                    tax_obj = Taxmaster.objects.get(tax_id=details['tax'])
                    details.update({"tax_percent":tax_obj.tax_percentage, "order_status":1, "other_metal_amnt":round(other_metal_amount, 3)})
                    order_detail_serializer = ErpOrdersDetailSerializer(order_detail, data=details)
                    order_detail_serializer.is_valid(raise_exception=True)
                    order_detail_serializer.save()
                    
                   
                    for stones in stone_details:
                        stones.update({"order_detail":order_detail_serializer.data['detail_id']})
                        stone_serializer = ErpOrderStoneSerializer(data=stones)
                        stone_serializer.is_valid(raise_exception=True)
                        stone_serializer.save()
                        
                    for charges in charges_details:
                        charges.update({"order_detail":order_detail_serializer.data['detail_id']})
                        charges_serializer = ErpOrderChargesSerializer(data=charges)
                        charges_serializer.is_valid(raise_exception=True)
                        charges_serializer.save()
                    
                    for attribute in attribute_details:
                        attribute.update({"order_detail":order_detail_serializer.data['detail_id']})
                        attribute_serializer = ErpOrderAttributeSerializer(data=attribute)
                        attribute_serializer.is_valid(raise_exception=True)
                        attribute_serializer.save()
                    
                    for metals in other_metal_details:
                        metals.update({"order_detail":order_detail_serializer.data['detail_id']})
                        metals_serializer = ErpOrderOtherMetalSerializer(data=metals)
                        metals_serializer.is_valid(raise_exception=True)
                        metals_serializer.save() 

                    ERPOrderImages.objects.filter(order_detail=order_detail_serializer.data['detail_id']).delete()

                    for index, images in enumerate(order_images):    
                
                        try:
                        # first_image = order_images[0]
                            file_content = base64_to_file(images['base64'], filename_prefix="myfile",file_extension="jpg")
                    
                            image_data = {
                                "image": file_content,
                                "name": f"{now().strftime('%Y%m%d%H%M%S')}",
                                "order_detail": order_detail_serializer.data['detail_id']
                            }
                            image_serializer = ErpOrderImagesSerializer(data=image_data)
                            image_serializer.is_valid(raise_exception=True)
                            image_serializer.save()
                            print("✅ Image saved successfully:", file_content)
                        except Exception as e:
                            print(f"❌ Error processing image: {e}")


                    ERPOrderVideos.objects.filter(order_detail=order_detail_serializer.data['detail_id']).delete()

                    for index, video in enumerate(order_videos):
                        try:
                        # first_video = order_videos[0]
                            file_content = base64_to_file(video['base64'], filename_prefix="myfile",file_extension="mp4")

                            video_data = {
                                "video": file_content,
                                "name": f"{now().strftime('%Y%m%d%H%M%S')}",
                                "order_detail": order_detail_serializer.data['detail_id']
                            }
                            video_serializer = ERPOrderVideosSerializer(data=video_data)
                            video_serializer.is_valid(raise_exception=True)
                            video_serializer.save()
                            print("✅ Video saved successfully:", file_content)
                        except Exception as e:
                            print(f"❌ Error processing video: {e}")

                    ERPOrderAudios.objects.filter(order_detail=order_detail_serializer.data['detail_id']).delete()
            
                    for index, audio in enumerate(order_voices):
                
                        try: 
                            file_content = base64_to_file(audio['base64'], filename_prefix="myfile",file_extension="mp3")

                            audio_data = {
                                "audio": file_content,
                                "name": f"{now().strftime('%Y%m%d%H%M%S')}",
                                "order_detail": order_detail_serializer.data['detail_id']
                            }
                            audio_serializer = ERPOrderAudiosSerializer(data=audio_data)
                            audio_serializer.is_valid(raise_exception=True)
                            audio_serializer.save()
                            print("✅ Audio saved successfully:", file_content)
                        except Exception as e:
                            print(f"❌ Error processing audio: {e}")

                else:
                    order_create = ErpOrderCreateView()
                    order_create.insert_order_details(details,queryset.order_id,queryset.order_type)
            return Response({"message":"Order Updated successfully."}, status=status.HTTP_200_OK)
    

    def update_deleted_details(self, item_details, order_id):
        existing_items = ERPOrderDetails.objects.filter(order=order_id)
        existing_item_map = {item.pk: item for item in existing_items}
        ids_to_delete = set(existing_item_map.keys())
        print(ids_to_delete)
        for detail in item_details:
            item_id = detail.get('detail_id')
            if item_id:
                ids_to_delete.discard(item_id)
        if ids_to_delete:
            print('delete')
            print(ids_to_delete)
            ERPOrderDetails.objects.filter(pk__in=ids_to_delete).delete()


class ErpOrderPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def generate_order_print(self, order_id, serializer, output, request):
        order_details_qs = ERPOrderDetails.objects.filter(order=order_id)
        order_details_serialized = ErpOrdersDetailSerializer(order_details_qs, many=True).data

        old_metal_details = ErpInvoiceOldMetalDetails.objects.filter(order=order_id)
        old_metal_details_serializer = ErpInvoiceOldMetalDetailsSerializer(old_metal_details, many=True).data

        branch = Branch.objects.filter(id_branch=serializer.data['order_branch']).first()
        customer = Customers.objects.filter(id_customer=serializer.data['customer']).first()
        company = Company.objects.latest("id_company")

        # Get customer address
        customer_address = CustomerAddress.objects.filter(customer=customer.pk).first()
        address = (
            f"{customer_address.line1 or ''} {customer_address.line2 or ''} {customer_address.line3 or ''}".strip()
            if customer_address else None
        )
        output.update({"address": address})

        # Set order type label
        order_type_labels = {1: "Customer Order", 2: "Purchase Order", 3: "Repair Order"}
        output.update({"order_type_label": order_type_labels.get(serializer.data['order_type'], "Unknown Order")})

        # Calculate totals
        totals = defaultdict(float)
        order_details = []
        total_old_metal_cost = 0
        for details in order_details_serialized:
            if Product.objects.filter(pro_id=details['product']).exists():
                product = Product.objects.get(pro_id=details['product'])
                details.update({"cat_id": product.cat_id.pk})

            totals["total_pcs"] += int(details['pieces'])
            totals["total_gross_wt"] += float(details['gross_wt'])
            totals["total_net_wt"] += float(details['net_wt'])
            totals["total_less_wt"] += float(details['less_wt'])
            totals["total_wastage_wt"] += float(details['wastage_wt'])
            totals["total_mc"] += float(details['mc_value'])
            totals["total_item_cost"] += float(details['item_cost'])

            order_details.append(details)
        
        for old_metal in old_metal_details_serializer:
            total_old_metal_cost += float(old_metal['amount'])

        output.update({
            "old_metal_details" : old_metal_details_serializer,
            "order_details": order_details,
            "total_pcs": f"{totals['total_pcs']:.0f}",
            "total_gross_wt": f"{totals['total_gross_wt']:.3f}",
            "total_wastage_wt": f"{totals['total_wastage_wt']:.3f}",
            "total_net_wt": f"{totals['total_net_wt']:.3f}",
            "total_less_wt": f"{totals['total_less_wt']:.3f}",
            "total_item_cost": f"{totals['total_item_cost']:.2f}",
            "total_old_metal_cost": f"{total_old_metal_cost:.2f}",
            "balance_amt" : f"{float(totals['total_item_cost']) - float(total_old_metal_cost):.2f}",
            "total_mc": f"{totals['total_mc']:.2f}",
            "branch_name": branch.name,
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            'company_detail': company,
        })

        order_folder = "erp_repair_order" if serializer.data['order_type'] == 3 else "erp_order"
        save_dir = os.path.join(settings.MEDIA_ROOT, order_folder, str(serializer.data['order_no']))
        os.makedirs(save_dir, exist_ok=True)

        template_type = RetailSettings.objects.get(name='customer_order_print_format').value

        if int(template_type) == 1:
            template = get_template('order_print.html')
        elif int(template_type) == 2:
            template = get_template('order_print2.html')
        else:
            template = get_template('order_print3.html')

        # template = get_template('order_print.html')
        html = template.render(output)

        pdf_path = os.path.join(save_dir, f"{order_folder}.pdf")
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)

        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())

        return request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{serializer.data['order_no']}/{order_folder}.pdf")

    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = ErpOrdersSerializer(queryset)
        output = serializer.data
        if(serializer.data['order_type'] == 3):
            repair_print = ErpOrderCreateView()
            order_pdf_path = repair_print.generate_repair_order_print(queryset.order_id, serializer, request)
        else:
            order_pdf_path = self.generate_order_print(queryset, serializer, output, request)
        response_data = { 'pdf_url': order_pdf_path}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
     
class ErpJobOrderCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpJobOrderSerializer
    queryset = ErpJobOrder.objects.all()
    
    
    def generate_job_orderno(self, data, fy, assigned_type):

        code = ''
        job_order_code_settings = RetailSettings.objects.get(name='job_order_code_settings').value
        job_order_code_format = RetailSettings.objects.get(name='job_order_code_format').value
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_jobordercode=None
        if job_order_code_settings == '1':#GENERATE CODE WITH FY, ORDER TYPE AND BRANCH
            last_jobordercode=ErpJobOrder.objects.filter(fin_year=fin_id, assigned_to=data['assigned_to']).order_by('-id_job_order').first()
        # elif order_code_settings == '2':#GENERATE CODE WITH PRODUCT
        #     last_ordercode=ERPOrder.objects.filter(tag_product_id=data['tag_product_id']).order_by('-order_id').first()
        # elif order_code_settings == '3':#GENERATE CODE WITH FY
        #     last_ordercode=ERPOrder.objects.filter(fin_year=fin_id).order_by('-order_id').first()
        if last_jobordercode:
            last_jobordercode = last_jobordercode.ref_no
            match = re.search(r'(\d{5})$', last_jobordercode)
            if match:
                code=match.group(1)
                code = str(int(code) + 1).zfill(5)
            else:
               code = '00001'
        else:
            code = '00001'
        
        job_order_code=job_order_code_format.replace('@code@', code).replace('@fy_code@', fy_code).replace('@type@', str(assigned_type))

        return job_order_code
    
    
    def generate_order_print(self, queryset, serializer, output, request):
        

        branch = Branch.objects.filter(id_branch=serializer.data['order_branch']).first()
        customer = Customers.objects.filter(id_customer=serializer.data['customer']).first()
        company = Company.objects.latest("id_company")

       

        # Set order type label
        order_type_labels = {1: "Customer Order", 2: "Purchase Order", 3: "Repair Order"}
        output.update({"order_type_label": order_type_labels.get(serializer.data['order_type'], "Unknown Order")})

        # Calculate totals
        totals = defaultdict(float)
        order_details = []

        for details in order_details_serialized:
            product = Product.objects.get(pro_id=details['product'])
            details.update({"cat_id": product.cat_id.pk})

            

            order_details.append(details)

        output.update({
            "order_details": order_details,
            "branch_name": branch.name,
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
        })

        order_folder = "erp_repair_order" if serializer.data['order_type'] == 3 else "erp_order"
        save_dir = os.path.join(settings.MEDIA_ROOT, order_folder, str(queryset.order_no))
        os.makedirs(save_dir, exist_ok=True)

        template_type = RetailSettings.objects.get(name='customer_order_print_format').value

        if int(template_type) == 1:
            template = get_template('order_print.html')
        elif int(template_type) == 2:
            template = get_template('order_print2.html')
        else:
            template = get_template('order_print3.html')

        # template = get_template('order_print.html')
        html = template.render(output)

        pdf_path = os.path.join(save_dir, f"{order_folder}.pdf")
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)

        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())

        return request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{queryset.order_no}/{order_folder}.pdf")
    
    
    def post(self, request, *args, **kwargs):
        message = []
        try:    
            with transaction.atomic():
                if(len(request.data['order_detail_ids'])==0):
                    return Response({"message":"Pass order detail ids."}, status=status.HTTP_400_BAD_REQUEST)
                order_detail_ids = request.data['order_detail_ids']
                del request.data['order_detail_ids']
                
                orderType = request.data.get('orderType','')
                if(request.data['assigned_to']== 1 and request.data['supplier'] is None):
                    return Response({"message":"Please select supplier."}, status=status.HTTP_400_BAD_REQUEST)
                if(request.data['assigned_to']== 2 and request.data['employee'] is None):
                    return Response({"message":"Please select employee."}, status=status.HTTP_400_BAD_REQUEST)
                
                fy=FinancialYear.objects.get(fin_status=True)
                company = Company.objects.latest("id_company")
                job_order_no = self.generate_job_orderno(request.data, fy, request.data['assigned_to'])
                request.data.update({"assigned_by":request.user.pk, "assigned_date":date.today(),
                                    "fin_year":fy.fin_id, "ref_no":job_order_no})
                serializer = ErpJobOrderSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                order_details = []
                for index, each in enumerate(order_detail_ids):
                    total_pcs = 0
                    total_weight = 0
                    if(request.data['assigned_to'] == 1):
                        job_order_query  = ErpJobOrderDetails.objects.filter(order_detail=each['detail_id'],job_order__supplier=request.data['supplier'])
                    elif(request.data['assigned_to'] == 2):
                        job_order_query  = ErpJobOrderDetails.objects.filter(order_detail=each['detail_id'],job_order__employee=request.data['employee'])
                        
                    job_order = job_order_query.count()
                    if(job_order < 1): 
                        instance = {}
                        instance.update({
                                        "job_order":serializer.data['id_job_order'], 
                                        "order_detail":each['detail_id'], 
                                        "status":1,
                                        "due_date":each['karigar_due_date'],
                                        "remarks":each['remarks']})
                        
                        if(request.data.get('added_through') == 2):
                             instance.update({"status": 3})
                        
                        if orderType!='' and orderType == 3:
                            instance.update({"status": 3})


                        job_orderdetail_serializer = ErpJobOrderDetailSerializer(data=instance)
                        job_orderdetail_serializer.is_valid(raise_exception=True)
                        job_orderdetail_serializer.save()
                        message_data = []
                        company = Company.objects.latest("id_company")
                        if(request.data['assigned_to'] == 1):
                            message_instance = {}
                            supplier = Supplier.objects.filter(id_supplier=request.data['supplier']).first()
                            assigned_order_detail = ERPOrderDetails.objects.filter(detail_id=each['detail_id']).first()
                            if(ERPOrderImages.objects.filter(order_detail=each['detail_id']).exists()):
                                assigned_order_detail_image = ERPOrderImages.objects.filter(order_detail=each['detail_id']).latest('det_order_img_id')
                                assigned_order_detail_image_seri = ErpOrderImagesSerializer(assigned_order_detail_image, context={"request":request})
                                print(assigned_order_detail_image_seri)
                                message_instance.update({
                                    "image":assigned_order_detail_image_seri.data['image']
                                })

                            message_instance.update({
                                        "product_name":assigned_order_detail.customized_product_name if assigned_order_detail.customized_product_name!=None else assigned_order_detail.product.product_name,
                                        "design_name":assigned_order_detail.customized_design_name if assigned_order_detail.customized_design_name!=None else assigned_order_detail.design.design_name if assigned_order_detail.design and assigned_order_detail.design.design_name is not None else None,
                                        "mobile":supplier.mobile_no,
                                        "remarks":each['remarks'],
                                        "company_name":company.company_name,
                                        "gross_weight":assigned_order_detail.gross_wt
                                    })
                            if message_instance not in message_data:
                                message_data.append(message_instance)
                        
                       
                            ERPOrderDetails.objects.filter(detail_id=each['detail_id']).update(order_status=3, 
                                                                                           karigar_due_date=each['karigar_due_date'])
                            order_detail_query = ERPOrderDetails.objects.filter(detail_id=each['detail_id']).first()
                            branch = Branch.objects.filter(id_branch=order_detail_query.order.order_branch.pk).first()
                            
                            print_instance = {}
                            order_type_labels = {1: "Customer Order", 2: "Purchase Order", 3: "Repair Order"}
                            print_instance.update({"order_type_label": order_type_labels.get(order_detail_query.order.order_type, "Unknown Order")})
                            
                            if(request.data.get('orderType') == 3):
                                repair_type_ids  = order_detail_query.order_repair_type.all()
                                repair_items = RepairDamageMaster.objects.filter(id_repair__in=repair_type_ids)
                                repair_names = ", ".join(repair_items.values_list("name", flat=True))
                                print_instance.update({
                                    "repair_name":repair_names
                                }) 
                            if order_detail_query.product and Product.objects.filter(pro_id=order_detail_query.product.pk).exists():
                                product = Product.objects.get(pro_id=order_detail_query.product.pk)
                                print_instance.update({
                                    "cat_id":product.cat_id.pk,
                                    "product_name":order_detail_query.product.product_name
                                    })
                            else:
                                print_instance.update({
                                    "product_name":order_detail_query.customized_product_name
                                })
                            print_instance.update({
                                    "mobile":supplier.mobile_no,
                                    "name":supplier.supplier_name,
                                    "order_no":order_detail_query.order.order_no,
                                    "order_date":order_detail_query.order.order_date,
                                    "order_type":order_detail_query.order.order_type,
                                    "pieces":order_detail_query.pieces,
                                    "remarks":each['remarks'],
                                    "gross_wt":order_detail_query.gross_wt,
                                    "branch_name": branch.name,
                                    "due_date": each['karigar_due_date'],
                                    "company_detail":company
                                })
                            # print(print_instance)
                            if print_instance not in order_details:
                                order_details.append(print_instance)
                            
                                total_pcs = sum(item["pieces"] for item in order_details)
                                total_weight = sum(item["gross_wt"] for item in order_details)
                            
                           
                        print(message_data)
                        if len(message_data) > 0 and "image" in message_data[0]:
                            send_message_with_image(message_data)
                    else:
                        job = job_order_query.first()
                        message.append("Order No : "+job.order_detail.order.order_no+" Item Already Assigned this Karigar")
                pdf_url = ''
                order_folder = "repair_order_assign_print"
                save_dir = os.path.join(settings.MEDIA_ROOT, order_folder, str(job_order_no))
                os.makedirs(save_dir, exist_ok=True)
                
                template = get_template('repair_order_print.html')
                html = template.render({"order_details":order_details,"total_pcs":total_pcs,"total_weight":total_weight})
                pdf_path = os.path.join(save_dir, f"{order_folder}.pdf")
                result = io.BytesIO()
                pisa.pisaDocument(io.StringIO(html), result)
                with open(pdf_path, 'wb') as f:
                    f.write(result.getvalue())
                pdf_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{job_order_no}/{order_folder}.pdf")
                if(len(order_detail_ids) == len(message)):
                    raise ValueError("An error occurred, rolling back the transaction.")
                    
                return Response({"data":serializer.data,"message":"order Assigned Successfully", "pdf_path":pdf_url }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"data":{},"message":message }, status=status.HTTP_400_BAD_REQUEST)
        
class OpenOrderListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def post(self, request, *args, **kwargs):
        output = []
        queryset = ERPOrder.objects.all().order_by('-order_id')

        # Apply filters conditionally
        if request.data.get('branch'):
            queryset = queryset.filter(order_branch=request.data['branch'])

        if request.data.get('orderno'):
            queryset = queryset.filter(order_no__icontains=request.data['orderno'])

        if request.data.get('finyear'):
            queryset = queryset.filter(fin_year=request.data['finyear'])

        if request.data.get('order_type'):
            queryset = queryset.filter(order_type=request.data['order_type'])
        else:
            queryset = queryset.filter(order_type__in=[1,4])
            
        serializer = self.get_serializer(queryset, many=True)
        for data in serializer.data:
            data.update({"order_date":format_date(data['order_date'])})
            detail_query = ERPOrderDetails.objects.filter(order=data['order_id'], order_status__in=[1,2])
            detail_serializer = ErpOrdersDetailSerializer(detail_query, many=True)

            for details in detail_serializer.data:
                if(data['order_type']==4):
                    details.update({
                        "product_name":details['customized_product_name'],
                        "design_name":details['customized_design_name'],
                    })
                if(data['order_type']==3):
                    repair_type_ids  = details['order_repair_type']
                    repair_items = RepairDamageMaster.objects.filter(id_repair__in=repair_type_ids)
                    repair_names = ", ".join(repair_items.values_list("name", flat=True))
                    details.update({
                        "repair_name":repair_names,
                        "karigar_remark":details['remarks'],
                    })  
                    if(details['customized_product_name']!=None):
                        details.update({
                            "product_name":details['customized_product_name'],
                        })
                details.update({"customer_due_date":format_date(details['customer_due_date']),})


                if details['erp_tag']==None:
                    if ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists():
                        order_image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id']).earliest('det_order_img_id')
                        order_image_details = ERPOrderImages.objects.filter(order_detail=details['detail_id']).all()
                        order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                        order_image_details_serializer = ErpOrderImagesSerializer(order_image_details,many=True, context={"request": request})
                        details.update({"preview_images":order_image_details_serializer.data})
                        if(data['order_type']==4):
                            details.update({"image":order_image, "image_text":details['customized_product_name'][0]})
                        else:
                            details.update({"image":order_image, "image_text":details['product_name'][0]})
                    else:
                        if(data['order_type']==4):
                            details.update({"image":None, "image_text":details['customized_product_name'][0]})
                        else:
                            if details['product']!=None:
                                details.update({"image":None, "image_text":details['product_name'][0]})
                            else:
                                details.update({"image":None, "image_text":""})
                else:
                    if ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).exists():
                        order_image_query = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).earliest('id')
                        order_image_details = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).all()
                        order_image = ErpTaggingImagesSerializer(order_image_query, context={"request": request}).data['tag_image']
                        order_image_details_serializer = ErpTaggingImagesSerializer(order_image_details,many=True, context={"request": request})
                        details.update({"preview_images":order_image_details_serializer.data})
                        if(data['order_type']==4):
                                details.update({"image":order_image, "image_text":details['customized_product_name'][0]})
                        else:
                            details.update({"image":order_image, "image_text":details['product_name'][0]})
                    else:
                        if(data['order_type']==4):
                            details.update({"image":None, "image_text":details['customized_product_name'][0]})
                        else:
                            details.update({"image":None, "image_text":details['product_name'][0]})
                
                if ERPOrderVideos.objects.filter(order_detail=details['detail_id']).exists():
                    order_video_query = ERPOrderVideos.objects.filter(order_detail=details['detail_id']).earliest('det_order_vid_id')
                    order_video = ERPOrderVideosSerializer(order_video_query, context={"request": request}).data['video']
                    
                    order_video_details = ERPOrderVideos.objects.filter(order_detail=details['detail_id']).all()
                    order_video_details_serializer = ERPOrderVideosSerializer(order_video_details, many=True,context={"request": request})
                    details.update({"preview_videos":order_video_details_serializer.data})

                    if(data['order_type']==4):
                        details.update({"video": order_video,"video_text":details['customized_product_name'][0]})
                    else:
                        details.update({"video": order_video,"video_text":details['product_name'][0]})
                else:
                    if(data['order_type']==4):
                        details.update({"video": None,"video_text":details['customized_product_name'][0]})
                    else:
                        details.update({"video": None,"video_text":details['product_name'][0]})

                    
                if ERPOrderAudios.objects.filter(order_detail=details['detail_id']).exists():
                    order_audio_query = ERPOrderAudios.objects.filter(order_detail=details['detail_id']).earliest('det_order_audio_id')
                    order_audio = ERPOrderAudiosSerializer(order_audio_query, context={"request": request}).data['audio']
                    
                    order_audio_details = ERPOrderAudios.objects.filter(order_detail=details['detail_id']).all()
                    order_audio_details_serializers = ERPOrderAudiosSerializer(order_audio_details, many=True,context={"request": request})
                    details.update({"preview_voices":order_audio_details_serializers.data})
                    
                    if(data['order_type']==4):
                        details.update({"audio": order_audio,"audio_text":details['customized_product_name'][0]})
                    else:
                        details.update({"audio": order_audio,"audio_text":details['product_name'][0]})
                else:
                    if(data['order_type']==4):
                        details.update({"audio": None,"audio_text":details['customized_product_name'][0]})
                    else:
                        details.update({"audio": None,"audio_text":details['product_name'][0]})      
                if details not in output:
                    output.append({**details,**data})
        sorted_output = sorted(output, key=lambda x: x['detail_id'], reverse=True)
        return Response({"data":sorted_output,"message":"Data Retrieved successfully"}, status=status.HTTP_200_OK)
    
class OrderLinkListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def post(self, request, *args, **kwargs):
        output = []
        queryset = ERPOrder.objects.all()
        type = request.data['type']

        # Apply filters conditionally
        if request.data.get('branch'):
            queryset = queryset.filter(order_branch=request.data['branch'])

        if request.data.get('orderno'):
            queryset = queryset.filter(order_no__icontains=request.data['orderno'])

        if request.data.get('finId'):
            queryset = queryset.filter(fin_year=request.data['finId'])
            
        serializer = self.get_serializer(queryset, many=True)
        for data in serializer.data:
            if int(type) == 1:
                detail_query = ERPOrderDetails.objects.filter(order=data['order_id'], order_status__in=[1,2,3])
            else:
                detail_query = ERPOrderDetails.objects.filter(order=data['order_id'], order_status=4)
            detail_serializer = ErpOrdersDetailSerializer(detail_query, many=True)
            for details in detail_serializer.data:
                if int(type) == 2:
                    tag = ErpTagging.objects.get(tag_id=details['erp_tag'])
                    details.update({'tag_code':tag.tag_code,"tag_id": details['erp_tag']})
                     
                if(ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists()):
                    order_image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id']).earliest('det_order_img_id')
                    order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                    details.update({'unlink_reason':'',"tagId":'',"image":order_image, "image_text":details['product_name'][0]})
                else:
                    details.update({'unlink_reason':'',"tagId":'',"image":None, "image_text":details['product_name'][0]})
                if details not in output:
                    output.append({**details,**data})
        return Response(output, status=status.HTTP_200_OK)
    
class OrderLinkView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            type = int(request.data.get('type'))
            
            for data in request.data['orderDetailList']:
                if(type == 1):
                    tag = ErpTagging.objects.get(tag_id=data['tag_id'])
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=4,erp_tag=tag.pk, linked_by=request.user.pk, linked_date=date.today())
                elif(type == 2):
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=1,erp_tag=None, unlinked_by=request.user.pk, unlinked_date=date.today(),
                                                                                   unlinked_reason=data['unlink_reason'])
            if(type == 1):    
                return Response({"message": "Orders linked successfully"}, status=status.HTTP_200_OK)
            return Response({"message": "Orders Unlinked successfully"}, status=status.HTTP_200_OK)
            
        
class OrderUnLinkView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            for data in request.data:
                ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(erp_tag=None, unlinked_by=request.user.pk, unlinked_date=date.today(),
                                                                                   unlinked_reason=data['unlink_reason'])
            return Response({"message":"Orders unlinked successfully"}, status=status.HTTP_200_OK)
        
# class CustomerOrdersView(generics.GenericAPIView):
#     permission_classes = [IsEmployee]
    
#     def get(self, request, *args, **kwargs):
#         queryset = ERPOrder.objects.all()
#         serializer = ErpOrdersSerializer(queryset, many=True)
#         output = []
#         for data in serializer.data:
#             instance = {}
#             detail_query = ERPOrderDetails.objects.filter(order=data['order_id'])
#             detail_serializer = ErpOrdersDetailSerializer(detail_query, many=True)
#             for details in detail_serializer.data:
#                 if(ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists()):
#                     order_image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id']).earliest('det_order_img_id')
#                     order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
#                     instance.update({"image":order_image, "image_text":details['product_name'][0]})
#                 else:
#                     instance.update({"image":None, "image_text":details['product_name'][0]})
#                 customer = Customers.objects.get(id_customer=data['customer'])
#                 order_status = ERPOrderStatus.objects.get(id=details['order_status'])
#                 instance.update({"order_no":data['order_no'], "order_date":data['order_date'], "customer":customer.firstname,
#                                  "mobile":customer.mobile, "order_status":details['order_status'], "product":details['product_name'],
#                                  "design":details['design_name'], "sub_design":details['sub_design_name'], "pieces":details['pieces'],
#                                  "gross_wt":details['gross_wt'], "less_wt":details['less_wt'], "net_wt":details['net_wt'],
#                                  "colour":order_status.colour, "name":order_status.name})
#                 if(ErpJobOrderDetails.objects.filter(order_detail=details['detail_id']).exists()):
#                     job_detail_query = ErpJobOrderDetails.objects.filter(order_detail=details['detail_id'])
#                     job_detail_serializer = ErpJobOrderDetailSerializer(job_detail_query, many=True)
#                     for job_detail in job_detail_serializer.data:
#                         job_order = ErpJobOrder.objects.get(id_job_order=job_detail['order_detail'])
#                         instance.update({"karigar":job_order.supplier.supplier_name, "karigar_id":job_order.supplier.pk})
#                 else:
#                     instance.update({"karigar":None})
#                 if instance not in output:
#                     output.append(instance)
#         return Response(output, status=status.HTTP_200_OK)
    
#     def post(self, request, *args, **kwargs):
#         with transaction.atomic():
#             for data in request.data:
#                 ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=6, cancel_reason=data['cancel_reason'],
#                                                                                    cancelled_by=request.user.pk, cancelled_date=date.today())
#             return Response({"message":"Orders cancelled successfully."}, status=status.HTTP_200_OK)


# class JobOrdersView(generics.GenericAPIView):
#     permission_classes = [IsEmployee]
    
#     def post(self, request, *args, **kwargs):
#         queryset = ErpJobOrderDetails.objects.all()
#         serializer = ErpJobOrderDetailSerializer(queryset, many=True)
#         output = []
#         for data in serializer.data:
#             instance = {}
#             job_order = ErpJobOrder.objects.get(id_job_order=data['job_order'])
#             order_detail = ERPOrderDetails.objects.get(detail_id=data['order_detail'])
#             order_detail_serializer = ErpOrdersDetailSerializer(order_detail)
#             order_status = ERPOrderStatus.objects.get(id=data['status'])
#             if(ERPOrderImages.objects.filter(order_detail=order_detail.detail_id).exists()):
#                 order_image_query = ERPOrderImages.objects.filter(order_detail=order_detail.detail_id).earliest('det_order_img_id')
#                 order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
#                 instance.update({"image":order_image, "image_text":order_detail_serializer.data['product_name'][0]})
#             else:
#                 instance.update({"image":None, "image_text":order_detail_serializer.data['product_name'][0]})
#             instance.update({"ref_no":job_order.ref_no, "assigned_date":job_order.assigned_date,
#                              "karigar":job_order.supplier.supplier_name, "karigar_id":job_order.supplier.pk,
#                              "order_no":order_detail.order.order_no, "order_status":data['status'],
#                              "product":order_detail_serializer.data['product_name'], "colour":order_status.colour, "name":order_status.name,
#                              "design":order_detail_serializer.data['design_name'], "sub_design":order_detail_serializer.data['sub_design_name'], 
#                              "pieces":order_detail_serializer.data['pieces'],
#                              "gross_wt":order_detail_serializer.data['gross_wt'], "less_wt":order_detail_serializer.data['less_wt'], 
#                              "net_wt":order_detail_serializer.data['net_wt']})
#             if instance not in output:
#                 output.append(instance)
#         return Response(output, status=status.HTTP_200_OK)

        
class CustomerOrdersListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        
        output = []
        karigar_fil = request.data.get('karigar',None)
        order_fil = request.data.get('order_status',None)
        branch_fil = request.data.get('branch',None)
        date = request.data.get('date',None)
        from_date = request.data.get('from_date',None)
        to_date = request.data.get('to_date',None)
        order_type = request.data.get('order_type',1)
        customer = request.data.get('customer',None)
        print(karigar_fil)
        queryset = ERPOrder.objects.filter(order_type=order_type).all()
        if customer:
            queryset = queryset.filter(customer=customer).order_by('-order_id')
        elif from_date and to_date:
            queryset = queryset.filter(order_date__lte=to_date, order_date__gte=from_date).order_by('-order_id')
        if branch_fil:
            queryset = queryset.filter(order_branch=branch_fil).order_by('-order_id')

        serializer = ErpOrdersSerializer(queryset, many=True)
        
        detail_query = ERPOrderDetails.objects.all()
        if order_fil != None:
            detail_query = ERPOrderDetails.objects.filter(order_status=order_fil)
        detail_serializer = ErpOrdersDetailSerializer(detail_query, many=True)
        
        for data in serializer.data:
            for details in detail_serializer.data:
                instance = {}
                if (data['order_id'] == details['order']):
                    if details['erp_tag']==None:
                        if ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists():
                            order_image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id']).earliest('det_order_img_id')
                            order_image_details = ERPOrderImages.objects.filter(order_detail=details['detail_id']).all()
                            order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                            order_image_details_serializer = ErpOrderImagesSerializer(order_image_details,many=True, context={"request": request})
                            instance.update({"preview_images":order_image_details_serializer.data})
                            if(data['order_type']==4):
                                instance.update({"image":order_image, "image_text":details['customized_product_name'][0]})
                            else:
                                instance.update({"image":order_image, "image_text":details['product_name'][0]})
                        else:
                            if(data['order_type']==4):
                                instance.update({"image":None, "image_text":details['customized_product_name'][0]})
                            else:
                                instance.update({"image":None, "image_text":details['product_name'][0]})
                    else:
                        if ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).exists():
                            order_image_query = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).earliest('id')
                            order_image_details = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).all()
                            order_image = ErpTaggingImagesSerializer(order_image_query, context={"request": request}).data['tag_image']
                            order_image_details_serializer = ErpTaggingImagesSerializer(order_image_details,many=True, context={"request": request})
                            instance.update({"preview_images":order_image_details_serializer.data})
                            if(data['order_type']==4):
                                instance.update({"image":order_image, "image_text":details['customized_product_name'][0]})
                            else:
                                instance.update({"image":order_image, "image_text":details['product_name'][0]})
                        else:
                            if(data['order_type']==4):
                                instance.update({"image":None, "image_text":details['customized_product_name'][0]})
                            else:
                                instance.update({"image":None, "image_text":details['product_name'][0]})
                        
                    
                    if ERPOrderVideos.objects.filter(order_detail=details['detail_id']).exists():
                        order_video_query = ERPOrderVideos.objects.filter(order_detail=details['detail_id']).earliest('det_order_vid_id')
                        order_video = ERPOrderVideosSerializer(order_video_query, context={"request": request}).data['video']
                        
                        order_video_details = ERPOrderVideos.objects.filter(order_detail=details['detail_id']).all()
                        order_video_details_serializer = ERPOrderVideosSerializer(order_video_details, many=True,context={"request": request})
                        instance.update({"preview_videos":order_video_details_serializer.data})

                        if(data['order_type']==4):
                            instance.update({"video": order_video,"video_text":details['customized_product_name'][0]})
                        else:
                            instance.update({"video": order_video,"video_text":details['product_name'][0]})
                    else:
                        if(data['order_type']==4):
                            instance.update({"video": None,"video_text":details['customized_product_name'][0]})
                        else:
                            instance.update({"video": None,"video_text":details['product_name'][0]})

                    
                    if ERPOrderAudios.objects.filter(order_detail=details['detail_id']).exists():
                        order_audio_query = ERPOrderAudios.objects.filter(order_detail=details['detail_id']).earliest('det_order_audio_id')
                        order_audio = ERPOrderAudiosSerializer(order_audio_query, context={"request": request}).data['audio']
                        
                        order_audio_details = ERPOrderAudios.objects.filter(order_detail=details['detail_id']).all()
                        order_audio_details_serializers = ERPOrderAudiosSerializer(order_audio_details, many=True,context={"request": request})
                        instance.update({"preview_voices":order_audio_details_serializers.data})
                        
                        if(data['order_type']==4):
                            instance.update({"audio": order_audio,"audio_text":details['customized_product_name'][0]})
                        else:
                            instance.update({"audio": order_audio,"audio_text":details['product_name'][0]})
                    else:
                        if(data['order_type']==4):
                            instance.update({"audio": None,"audio_text":details['customized_product_name'][0]})
                        else:
                            instance.update({"audio": None,"audio_text":details['product_name'][0]})

                    customer = Customers.objects.filter(id_customer=data['customer']).first()
                    order_status = ERPOrderStatus.objects.get(id=details['order_status'])
                    if(data['order_type']==4):
                        instance.update({"product":details['customized_product_name'],
                                         "design":details['customized_design_name'], })
                    else:
                        instance.update({"product":details['product_name'],
                                         "design":details.get('design_name'),})
                    instance.update({
                        "order_no":data['order_no'], 
                        "order_date":data['order_date'], 
                        "customer":customer.firstname,
                        "mobile":customer.mobile, 
                        "order_status":details['order_status'],
                        "sub_design":details.get('sub_design_name'), 
                        "pieces":details['pieces'],
                        "gross_wt":details['gross_wt'], 
                        "less_wt":details['less_wt'], 
                        "net_wt":details['net_wt'],
                        "colour":order_status.colour, 
                        "name":order_status.name,
                        "cancel_reason":'',
                        'detail_id':details['detail_id'],
                        'customer_order_type':'Customized Order' if details['is_reserved_item']==0 else 'Reserve Order'
                    })
                    if(ErpJobOrderDetails.objects.filter(order_detail=details['detail_id']).exists()):
                        job_order_query = ErpJobOrder.objects.all()
                        if karigar_fil != None:
                            job_order_query = ErpJobOrder.objects.filter(supplier=karigar_fil)
                        job_order_serializer = ErpJobOrderSerializer(job_order_query, many=True)
                        
                        for job_order in job_order_serializer.data: 
                            job_detail_query = ErpJobOrderDetails.objects.filter(job_order=job_order['id_job_order'], order_detail=details['detail_id'])
                            job_detail_serializer = ErpJobOrderDetailSerializer(job_detail_query, many=True)
                            for job_detail in job_detail_serializer.data:
                                job_order = ErpJobOrder.objects.get(id_job_order=job_detail['job_order'])
                                if(job_order.supplier):
                                    instance.update({"karigar":job_order.supplier.supplier_name, "karigar_id":job_order.supplier.pk})
                                else:
                                    instance.update({"karigar":None})
                    else:
                        instance.update({"karigar":None})
                    if(details['erp_tag']):
                        tag_query = ErpTagging.objects.get(tag_id=details['erp_tag'])
                        instance['tag_code'] = tag_query.tag_code
                        instance['karigar'] = tag_query.id_supplier.supplier_name
                    else :
                        instance.update({"karigar":None})
                    
                    if instance not in output:
                        output.append(instance)
        return Response(output, status=status.HTTP_200_OK)
    
class CustomerOrdersUpdateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            for data in request.data['order_detail_ids']:
                ERPOrderDetails.objects.filter(detail_id= (data['detail_id'])).update(order_status=6, cancel_reason=data['cancel_reason'],
                                                                                   cancelled_by=request.user.pk, cancelled_date=date.today())
            return Response({"message":"Orders cancelled successfully."}, status=status.HTTP_200_OK)

class CustomerOrdersDeliveryUpdateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            for data in request.data['order_detail_ids']:
                ERPOrderDetails.objects.filter(detail_id= (data['detail_id'])).update(order_status=5,delivered_on= date.today())
            return Response({"message":"Orders cancelled successfully."}, status=status.HTTP_200_OK)
        
        
class JobOrdersListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        output = []
        karigar_fil = request.data.get('karigar',None)
        order_fil = request.data.get('order_status',None)
        branch_fil = request.data.get('branch',None)
        date = request.data.get('date',None)
        from_date = request.data.get('from_date',None)
        to_date = request.data.get('to_date',None)
        
        job_order_queryset = ErpJobOrder.objects.all()
        if karigar_fil != None and from_date != None and to_date!=None:
            job_order_queryset = ErpJobOrder.objects.filter(supplier=karigar_fil, assigned_date__lte=to_date, assigned_date__gte=from_date)
        if karigar_fil != None and from_date == None and to_date==None:
            job_order_queryset = ErpJobOrder.objects.filter(supplier=karigar_fil)
        if karigar_fil == None and from_date != None and to_date!=None:
            job_order_queryset = ErpJobOrder.objects.filter(assigned_date__lte=to_date, assigned_date__gte=from_date)
        job_order_serializer = ErpJobOrderSerializer(job_order_queryset, many=True)
        
        queryset = ErpJobOrderDetails.objects.all()
        if order_fil != None:
            queryset = ErpJobOrderDetails.objects.filter(status=order_fil)
        serializer = ErpJobOrderDetailSerializer(queryset, many=True)
        
        order_query = ERPOrder.objects.all()
        if branch_fil != None:
            order_query = ERPOrder.objects.filter(order_branch=branch_fil)
        order_serializer = ErpOrdersSerializer(order_query, many=True)
        
        order_detail_query = ERPOrderDetails.objects.all()
        order_detail_serializer = ErpOrdersDetailSerializer(order_detail_query, many=True)
        
        for data in serializer.data:
            for details in order_detail_serializer.data:
                for job_order in job_order_serializer.data:
                    for order in order_serializer.data:
                        
                        if((data['order_detail'] == details['detail_id']) and (data['job_order'] == job_order['id_job_order']) and 
                           details['order'] == order['order_id']):
                            order_status = ERPOrderStatus.objects.get(id=data['status'])
                            instance = {}
                            if(ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists()):
                                preview_images_query = ERPOrderImages.objects.filter(order_detail=details['detail_id'])
                                preview_images_serializer = ErpOrderImagesSerializer(preview_images_query, many=True, context={"request": request})
                                order_image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id']).earliest('det_order_img_id')
                                order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                                if(order['order_type']==4):
                                    instance.update({"image":order_image, "image_text":details['customized_product_name'][0], "preview_images":preview_images_serializer.data})
                                else:
                                    instance.update({"image":order_image, "image_text":details['product_name'][0], "preview_images":preview_images_serializer.data})
                            else:
                                if(order['order_type']==4):
                                    instance.update({"image":None, "image_text":details['customized_product_name'][0], "preview_images":[]})
                                else:
                                    if details['product']!=None:
                                        instance.update({"image":None, "image_text":details['product_name'][0], "preview_images":[]})
                                    else:
                                        instance.update({"image":None, "image_text":"", "preview_images":[]})
                                 
                            instance.update({"assign_status":{"label":order_status.name, "value":order_status.pk}})
            
                            if(job_order['assigned_to'] == 1):
                                instance.update({"assigned_to":"Supplier"})
                            if(job_order['assigned_to'] == 2):
                                employee = Employee.objects.get(id_employee=job_order['employee'])
                                instance.update({"assigned_to":"Employee", "employee":employee.firstname})
                            if(order['order_type']==4):
                                instance.update({"product":details['customized_product_name'],
                                                 "design":details['customized_design_name']})
                            if(order['order_type']!=4):
                                instance.update({
                                    "product":details['customized_product_name'] if details['customized_product_name']!=None else details['product_name'],
                                    "design":details.get('design_name'),
                                })
                            
                            instance.update({"ref_no":job_order['ref_no'], "assigned_date":format_date(job_order['assigned_date']),
                             "karigar":job_order['karigar_name'], "karigar_id":job_order['supplier'],
                             "order_no":order['order_no'], "order_status":data['status'],
                             "customer_due_date":format_date(details['customer_due_date']),"karigar_due_date":format_date(details['karigar_due_date']),
                            "colour":order_status.colour, "order_status_name":order_status.name,
                            "sub_design":details.get('sub_design_name'), 
                             "pieces":details['pieces'],"cancel_reason": '', "isChecked":False,
                             "gross_wt":details['gross_wt'], "less_wt":details['less_wt'], 
                             "net_wt":details['net_wt'], "id_job_order_detail":data['id_job_order_detail'],"detail_id":details['detail_id']
                             })
                            if instance not in output:
                                output.append(instance)
        sorted_output = sorted(output, key=lambda x: x['detail_id'], reverse=True)
        return Response(sorted_output, status=status.HTTP_200_OK)
    
    
class JobOrdersUpdateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            print(request.data)
            for data in request.data:
                print(data['status'])
                if(data['status'] == 7):
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=7,updated_by=request.user.pk, updated_on = datetime.now(tz=timezone.utc))

                if(data['status'] == 3):
                    ErpJobOrderDetails.objects.filter(id_job_order_detail=data['id_job_order_detail']).update(status=data['status'])
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=3,updated_by=request.user.pk, updated_on = datetime.now(tz=timezone.utc))


                if(data['status'] == 6):
                    ErpJobOrderDetails.objects.filter(id_job_order_detail=data['id_job_order_detail']).update(status=6, cancel_reason=data['cancel_reason'],cancelled_by=request.user.pk, cancelled_date=date.today())
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=1,updated_by=request.user.pk, updated_on = datetime.now(tz=timezone.utc))
                    
                if(data['status'] == 4 and data['added_through']==2):
                    ErpJobOrderDetails.objects.filter(id_job_order_detail=data['id_job_order_detail']).update(status=5,)
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=4,updated_by=request.user.pk, updated_on = datetime.now(tz=timezone.utc))

                if(data['status'] == 5 and data['added_through']==1):
                    ErpJobOrderDetails.objects.filter(id_job_order_detail=data['id_job_order_detail']).update(status=data['status'],delivery_date=date.today(),updated_on = datetime.now(tz=timezone.utc)) 
                    
                if(data['status'] == 5 and data['added_through']==2):
                    ERPOrderDetails.objects.filter(detail_id=data['detail_id']).update(order_status=5,updated_by=request.user.pk, delivery_date = date.today(),updated_on = datetime.now(tz=timezone.utc))
            return Response({"message":"Job Orders Status Updated successfully."}, status=status.HTTP_200_OK)
        

class ErpOrderDeliveryDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    
    def post(self, request, *args, **kwargs):
        fin_id =  request.data.get('fin_id')
        order_no = request.data.get('order_no')
        id_customer =request.data.get('id_customer') 
        id_branch = request.data.get('id_branch')
        if not order_no:
            return Response({"error": "Order no is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not fin_id:
            return Response({"error": "fin_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_customer:
            return Response({"error": "id_customer is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"error": "id_branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ERPOrder.objects.filter(customer = id_customer,order_no= order_no,order_branch = id_branch,fin_year=fin_id).get()
            serializer = ErpOrdersSerializer(queryset)
            order_detail = ERPOrderDetails.objects.filter(order=queryset.order_id,order_status = 4,erp_tag__tag_current_branch__id_branch =id_branch,erp_tag__tag_status__id_stock_status = 1)
            order_detail_serializer = ErpOrdersDetailSerializer(order_detail, many=True)
            output = serializer.data
            order_details = []
            for details, instance in zip(order_detail_serializer.data, order_detail):
                #order_details.append(details)
                if(instance.erp_tag):
                    query_set = ErpTaggingStone.objects.filter(tag_id=instance.erp_tag.tag_id)
                    stone_details= ErpTagStoneSerializer(query_set, many=True).data
                    for detail, instance_stn in zip(stone_details, query_set):
                        stone_name = instance_stn.id_stone.stone_name
                        detail.update({
                            'piece': detail['stone_pcs'],
                            'weight' : detail['stone_wt'],
                            'amount': detail['stone_amount'],
                            'stn_calc_type' : detail['stone_calc_type'],
                            'stone_name': stone_name,
                            'stone_type': instance_stn.id_stone.stone_type,
                        })
                
                    queryset = ErpTagOtherMetal.objects.filter(tag_id= instance.erp_tag.tag_id)
                    other_metal_details= ErpTagOtherMetalSerializer(queryset, many=True).data
                    for detail, instance_ot in zip(other_metal_details, queryset):
                        cat_name = instance_ot.id_category.cat_name
                        detail.update({
                            'cat_name': cat_name
                        })

                    queryset = ErpTagCharges.objects.filter(tag_id=instance.erp_tag.tag_id)
                    charges_details= ErpTagChargesSerializer(queryset, many=True).data

                
                    queryset = ErpTagAttribute.objects.filter(tag_id=instance.erp_tag.tag_id)
                    attribute_details= ErpTagAttributeSerializer(queryset, many=True).data
                    id_section = instance.erp_tag.tag_section_id
                    if(id_section):
                        id_section = instance.erp_tag.tag_section_id.id_section
                    data = {
                    "rate_type" : output['is_rate_fixed_on_order'],
                    "stone_details": stone_details,
                    "charges_details": charges_details,
                    "attribute_details": attribute_details,
                    "other_metal_details": other_metal_details,
                    "cat_id": instance.product.cat_id.id_category,
                    "tag_code": instance.erp_tag.tag_code,
                    "detail_id": details['detail_id'],
                    "item_type": 0,
                    "is_partial_sale": 0,
                    "pieces": instance.erp_tag.tag_pcs,
                    "gross_wt": instance.erp_tag.tag_gwt,
                    "less_wt": instance.erp_tag.tag_lwt,
                    "net_wt": instance.erp_tag.tag_nwt,
                    "dia_wt": instance.erp_tag.tag_dia_wt,
                    "stone_wt": instance.erp_tag.tag_stn_wt,
                    "wastage_percentage": instance.erp_tag.tag_wastage_percentage,
                    "wastage_weight": instance.erp_tag.tag_wastage_wt,
                    "other_metal_wt": instance.erp_tag.tag_other_metal_wt,
                    "mc_type": instance.erp_tag.tag_mc_type,
                    "mc_value": instance.erp_tag.tag_mc_value,
                    "total_mc_value": 0,
                    "other_charges_amount": 0,
                    "other_metal_amount": 0,
                    "rate_per_gram": details['rate_per_gram'],
                    "taxable_amount": 0,
                    "tax_amount": 0,
                    "cgst_cost": 0,
                    "sgst_cost": 0,
                    "igst_cost": 0,
                    "discount_amount": 0,
                    "item_cost": instance.erp_tag.tag_item_cost,
                    "wastage_discount": "0.00",
                    "mc_discount_amount": "0.00",
                    "status": 0,
                    "id_purity": instance.erp_tag.tag_purity_id.id_purity,
                    "uom_id": instance.erp_tag.tag_uom_id.uom_id,
                    "tag_id": instance.erp_tag.tag_id,
                    "id_product": instance.erp_tag.tag_product_id.pro_id,
                    "id_design": instance.erp_tag.tag_design_id.id_design,
                    "id_sub_design": instance.erp_tag.tag_sub_design_id.id_sub_design if instance.erp_tag.tag_sub_design_id else None,
                    "id_section": id_section,
                    # "calculation_type": instance.erp_tag.tag_calculation_type.id_calculation_type,
                    "product_name": instance.erp_tag.tag_product_id.product_name,
                    "design_name": instance.erp_tag.tag_design_id.design_name,
                    "sub_design_name": instance.erp_tag.tag_sub_design_id.sub_design_name if instance.erp_tag.tag_sub_design_id else ''
                    }
                    order_details.append(data)
        
            output.update({"order_details":order_details})
            return Response(output, status=status.HTTP_200_OK)
        except ERPOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        

class ErpRepairOrderDeliveryDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    
    def post(self, request, *args, **kwargs):
        supplier =request.data.get('supplier','') 
        id_customer =request.data.get('id_customer','') 

        if supplier=='' and id_customer =='':
            return Response({"error": "Supplier is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with connection.cursor() as cursor:
                sql = """
                    select j.id_job_order,d.order_detail_id,ord.detail_id,date_format(j.assigned_date,'%d-%m-%Y') as assign_date,
                    if(ord.product_id!='null',p.product_name,ord.customized_product_name) as product_name,
                    ord.pieces,ord.gross_wt,ord.net_wt,group_concat(r.name) as repair_type,c.firstname,c.mobile,
                    j.ref_no,o.order_no,d.id_job_order_detail,coalesce(ord.customer_charges,0) as total_charges
                    from erp_job_order j
                    left join erp_job_order_details d on d.job_order_id = j.id_job_order
                    left join erp_order_details ord on ord.detail_id = d.order_detail_id
                    left join erp_order o on o.order_id = ord.order_id
                    left join erp_product p on p.pro_id = ord.product_id
                    left join erp_order_details_order_repair_type t on t.erporderdetails_id = ord.detail_id
                    left join erp_repair_damage_master r on r.id_repair = t.repairdamagemaster_id
                    left join customers c on c.id_customer = o.customer_id
                    where o.order_type = 3
                    
                """
                if supplier!='':
                    sql += F" AND j.supplier_id = {supplier} AND d.status_id = 3 "
                elif id_customer!='':
                    sql += F" AND o.customer_id = {id_customer} AND ord.order_status_id = 4 "
                sql+="""
                    group by d.id_job_order_detail
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
            return Response(response_data, status=status.HTTP_200_OK)
        except ERPOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
class ErpRepairOrderDeliveryCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        order_details = request.data.get('order_details')
        if not order_details:
            return Response({"error": "Order Details is required"}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            try:
                for sales_item in order_details:
                    queryset = ERPOrderDetails.objects.get(detail_id=sales_item['order_detail_id'],order_status=3)
                    item = {
                        "customer_charges": sales_item["customer_charges"],
                        "karigar_charges": sales_item["karigar_charges"],
                        "order_status": 4,
                        "updated_by": request.user.pk, 
                        "updated_time": datetime.now(tz=timezone.utc)
                    }
                    serializer = ErpOrdersDetailSerializer(queryset, data=item,partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    if len(sales_item['extra_weight_details']) > 0:
                        for item in sales_item['extra_weight_details']:
                            item.update({"order_detail":sales_item['order_detail_id']})
                            extra_metal_serializer = ErpOrderRepairExtraMetalSerializer(data = item)
                            extra_metal_serializer.is_valid(raise_exception=True)
                            extra_metal_serializer.save()

                    ErpJobOrderDetails.objects.filter(id_job_order_detail=sales_item['id_job_order_detail'],status=3).update(status=5,updated_by= request.user.pk,updated_on = datetime.now(tz=timezone.utc)  )
                return Response({"message": "Repair Delivery Details Updated successfully"}, status=status.HTTP_200_OK)
            except ERPOrderDetails.DoesNotExist:
                return Response({"message": "Repair Orders Details not found"}, status=status.HTTP_404_NOT_FOUND)
        

class ErpRepairOrderListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ERPOrder.objects.all()
    serializer_class = ErpOrdersSerializer

    def get(self, request, *args, **kwargs):
        order_no = request.query_params.get('order_no')
        id_branch = request.query_params.get('id_branch')
        if not order_no:
            return Response({"error": "Order no is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"error": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ERPOrder.objects.filter(order_no=order_no,order_branch=id_branch)
            if request.data.get('order_type'):
                queryset = queryset.filter(order_type=request.data['order_type'])
            serializer = ErpOrdersSerializer(queryset,many=True)
            return Response(serializer.data[0], status=status.HTTP_200_OK)
        except ERPOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        id_branch = (id_branch) if id_branch != '' else 1

        queryset = ERPOrder.objects.filter(order_type=3).order_by('-order_id')
        if from_date and to_date:
                queryset = queryset.filter(order_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(order_branch__in=id_branch)
        else:
            queryset = queryset.filter(order_branch=id_branch)

        output = []
        paginator, page = pagination.paginate_queryset(queryset, request,None,ORDER_COLUMN_LIST)
        serializer = ErpOrdersSerializer(page, many=True)
        
        for index, data in enumerate(serializer.data):
            data.update({"pk_id":data['order_id'], "sno":index+1})
            if  data['order_type'] == 1:
                data.update({"order_type":"Customer Order"})
            elif  data['order_type'] == 2:
                data.update({"order_type":"Purchase Order"})
            else:
                data.update({"order_type":"Repair Order"})
            if data not in output:
                output.append(data)
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        context={
            'columns':ORDER_COLUMN_LIST,
            'actions':ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(output,context) 
    
class CustomerCartListCreateView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    queryset = CustomerCart.objects.all()
    serializer_class = CustomerCartSerializer
    
    def get(self, request, *args, **kwargs):
        customer = Customers.objects.filter(user=request.user.id).first()
        queryset = CustomerCart.objects.filter(customer = customer.pk, cart_type=1)
        serializer = CustomerCartSerializer(queryset, many=True)
        branch = Branch.objects.filter(is_ho=True).first()
        for data in serializer.data:
            if(data['erp_tag']==None):
                product = Product.objects.filter(pro_id=data['product']).get()
                # print(product.image == '')
                if(product.image == ''):
                    data.update({"image":None})
                else:
                    data.update({"image":product.image})
                data.update({"purchase_touch":0})
            else:
                if(ErpTaggingImages.objects.filter(erp_tag=data['erp_tag']).exists()):
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=data['erp_tag'])
                    tag_image_serializer = ErpTaggingImagesSerializer(tag_image, many=True,context={"request": request})
                    data.update({"image":tag_image_serializer.data})
                    # data.update({"image":None})
                else:
                    data.update({"image":None,"purchase_touch":0})
                tag_queryset = ErpTagging.objects.filter(tag_id=data['erp_tag']).first()
                data.update({"purchase_touch" : tag_queryset.tag_purchase_touch})
            data.update({
                        "added_on":date_format_with_time(data['added_on']),
                        "ho_branch":branch.pk, 
                        "is_cart":True
            })
        return Response({"status":True,"data":serializer.data}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        customer = Customers.objects.filter(user=request.user.id).first()
        # product = Product.objects.filter(pro_id=request.data['product']).first()
        request.data.update({"customer":customer.pk})
        if(request.data['erp_tag']!= None):
            tag = ErpTagging.objects.filter(tag_id=request.data['erp_tag']).first()
            if(tag.size != None):
                request.data.update({"size":tag.size.pk})
            elif(tag.size == None):
                request.data.update({"size":None})
            request.data.update({"uom":tag.tag_uom_id.pk, "purity":tag.tag_purity_id.pk,
                                 "product":tag.tag_product_id.pk, "design":tag.tag_design_id.pk,
                                 "pieces":tag.tag_pcs, "gross_wt":tag.tag_gwt,
                                 "less_wt":tag.tag_lwt, "tax_amnt":tag.tag_tax_amount,
                                 "net_wt" : tag.tag_nwt,
                                 "cart_type":1,
                                 "item_cost":tag.tag_item_cost, "taxable_amnt":None, "rate_per_gram":None,
                                 "tax_type":None, "tax_percent":None,"cgst_amnt":None, "sgst_amnt":None, "igst_amnt":None})
            if(tag.tag_sub_design_id != None):
                request.data.update({"sub_design":tag.tag_sub_design_id.pk, })
            elif(tag.tag_sub_design_id == None):
                request.data.update({"sub_design":None})
        request.data.update({"cart_type":1})
        serializer = CustomerCartSerializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data)

class CustomerCartDetailsView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    queryset = CustomerCart.objects.all()
    serializer_class = CustomerCartSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = CustomerCartSerializer(queryset)
        output = serializer.data
        branch = Branch.objects.filter(is_ho=True).first()
        if(queryset.erp_tag==None):
            product = Product.objects.filter(pro_id=queryset.product).get()
            output.update({"def_image":product.image, "images":product.image})
        else:
            tag_def_image = ErpTaggingImages.objects.filter(erp_tag=queryset.erp_tag, is_default=True).first()
            tag_image = ErpTaggingImages.objects.filter(erp_tag=queryset.erp_tag)
            tag_image_serializer = ErpTaggingImagesSerializer(tag_image, many=True)
            output.update({"def_image":tag_def_image.tag_image, "images":tag_image_serializer.data})
        output.update({"added_on":date_format_with_time(queryset.added_on),
                    "ho_branch":branch.pk})
        return Response(output, status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            obj.delete()
        except ProtectedError:
            return Response({"status":False,"message":"Cart Item can't be deleted, as it is in association."}, status=status.HTTP_423_LOCKED)
        return Response({"status":True,"message":"Cart Item Deleted Successfully"},status=status.HTTP_204_NO_CONTENT)
    
class CustomerWishlistListCreateView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    queryset = CustomerWishlist.objects.all()
    serializer_class = CustomerWishlistSerializer
    
    def get(self, request, *args, **kwargs):
        if "customer" not in request.query_params:
            return Response({"status":False,"message": "Customer id is required"}, status=status.HTTP_200_OK)
        else :
            queryset = CustomerWishlist.objects.filter(customer = request.query_params['customer']).order_by('-id')
            serializer = CustomerWishlistSerializer(queryset, many=True)
            response_data = []
            for data in serializer.data:
                result = {}
                size_name = ''
                tag = ErpTagging.objects.filter(tag_id=data['erp_tag']).first()
                tag_serializer = ErpTaggingSerializer(tag)
                tag_output = tag_serializer.data
                formatted_data = convert_tag_to_formated_data(tag_output)
                productDetails = Product.objects.get(pro_id = tag_output['tag_product_id'])
                cat_id = productDetails.cat_id
                stone_amount = other_metal_amount = other_charges_amount = 0
                is_wishlist = False
                is_cart = False
                if(CustomerWishlist.objects.filter(erp_tag =tag_output['tag_id'],customer = request.query_params['customer'])).exists():
                    is_wishlist = True
                if(CustomerCart.objects.filter(erp_tag =tag_output['tag_id'],customer = request.query_params['customer'])).exists():
                    is_cart = True
                image_details = []
                if ErpTaggingImages.objects.filter(erp_tag=data['erp_tag']).exists():
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=data['erp_tag'])
                    image_serializer = ErpTaggingImagesSerializer(tag_image, many=True, context={"request": request})
                    image_details = image_serializer.data
                    default = None
                    for detail in image_serializer.data:
                        detail.update({
                            'preview': detail['tag_image'],   
                            'default' :detail['is_default'],
                        })
                        if(detail['is_default'] == True):
                            default = detail['tag_image']
                    formatted_data['tag_images'] = image_serializer.data
                    formatted_data.update({"image":default, "image_text":tag_output['product_name'][len(tag_output['product_name'])-1]})
                else:
                    formatted_data['tag_images'] = []
                    formatted_data.update({"image":None, "image_text":tag_output['product_name'][len(tag_output['product_name'])-1]})
                cat_pur_rate = CategoryPurityRate.objects.filter(category = cat_id, purity = tag_output['tag_purity_id']).first()
                for stones in tag_output['stone_details']:
                    stone_amount += float(stones.get("stone_amount",0))
                for other in tag_output['other_metal_details']:
                    other_metal_amount += float(other.get("other_metal_cost",0))
                for charge in tag_output['charges_details']:
                    other_charges_amount += float(charge.get("charges_amount",0))
                if tag_output['size']!=None:
                    size = Size.objects.get(id_size=tag_output['size'])
                    size_name = size.name
                formatted_data.update({
                    "discount_amount": 0,
                    "invoice_type" : RetailSettings.objects.get(name='is_wholesale_or_retail').value,
                    "settings_billling_type":0,
                    "tax_type" : productDetails.tax_type,
                    "tax_percentage": productDetails.tax_id.tax_percentage,
                    "mc_calc_type": productDetails.mc_calc_type,
                    "wastage_calc_type": productDetails.wastage_calc_type,
                    "sales_mode": productDetails.sales_mode,
                    "fixwd_rate_type": productDetails.fixed_rate_type,
                    "productDetails":[],
                    "pure_wt" : formatted_data['pure_wt'],
                    "purchase_va" : formatted_data['purchase_va'],
                    "other_charges_amount" : other_charges_amount,
                    "other_metal_amount" : other_metal_amount,
                    "stone_amount" : stone_amount,
                    "rate_per_gram": cat_pur_rate.rate_per_gram if cat_pur_rate else 0 ,
                    "id_size":tag_output['size'],
                    "size_name":size_name
                })
                
                related_items = []
                tag_set = ErpTagSet.objects.filter(tag_id=tag_output['tag_id']).first()
                if tag_set:
                    tag_set_items = ErpTagSetItems.objects.filter(tag_set=tag_set)
                    for item in tag_set_items:
                        if item.tag:
                            related_serialized = ErpTaggingSerializer(item.tag, context={"request": request}).data
                            related_items.append({
                               **related_serialized
                            })

                else:
                    tag_set_item = ErpTagSetItems.objects.filter(tag_id=tag_output['tag_id']).first()
                    if tag_set_item:
                        parent_set = tag_set_item.tag_set
                        if parent_set and parent_set.tag:
                            
                            parent_serialized = ErpTaggingSerializer(parent_set.tag, context={"request": request}).data
                            related_items.append({
                                **parent_serialized
                            })

                        
                        sibling_items = ErpTagSetItems.objects.filter(tag_set=parent_set).exclude(tag_id=tag_output['tag_id'])
                        for sibling in sibling_items:
                            if sibling.tag:
                                sibling_serialized = ErpTaggingSerializer(sibling.tag, context={"request": request}).data
                                related_items.append({**sibling_serialized})
                
                item_cost = calculate_item_cost(formatted_data)
                for rel_item in related_items:
                    # print(rel_item['tag_id'])
                    if(ErpTaggingImages.objects.filter(erp_tag=rel_item['tag_id']).exists()):
                        tag_image_query = ErpTaggingImages.objects.filter(erp_tag=rel_item['tag_id'])
                        tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                        rel_item['tag_images'] = tag_image_serializer.data
                        if(ErpTaggingImages.objects.filter(erp_tag=rel_item['tag_id'], is_default=True).exists()):
                            tag_def_image_query = ErpTaggingImages.objects.filter(erp_tag=rel_item['tag_id'], is_default=True).first()
                            tag_def_image_serializer = ErpTaggingImagesSerializer(tag_def_image_query, context={'request':request})
                            rel_item['default_image'] = tag_def_image_serializer.data
                        else:
                            rel_item['default_image'] = tag_image_serializer.data[0]
                    elif(ErpTaggingImages.objects.filter(erp_tag=tag_output['tag_id']).exists()):
                        tag_image_query = ErpTaggingImages.objects.filter(erp_tag=tag_output['tag_id'])
                        tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                        rel_item['tag_images'] = tag_image_serializer.data
                        if(ErpTaggingImages.objects.filter(erp_tag=tag_output['tag_id'], is_default=True).exists()):
                            tag_def_image_query = ErpTaggingImages.objects.filter(erp_tag=tag_output['tag_id'], is_default=True).first()
                            tag_def_image_serializer = ErpTaggingImagesSerializer(tag_def_image_query, context={'request':request})
                            rel_item['default_image'] = tag_def_image_serializer.data
                        else:
                            rel_item['default_image'] = tag_image_serializer.data[0]
                    else:
                        rel_item['tag_images'] = []
                        rel_item['default_image'] = None
                formatted_data["related_items"] = related_items
                
                result.update({
                    "tag_id":tag_serializer.data['tag_id'],
                    "tag_code":tag_serializer.data['tag_code'],
                    "product_name":tag_serializer.data['product_name'],
                    "design_name":tag_serializer.data['design_name'],
                    "purity_name":tag_serializer.data['purity_name'],
                    "metal_name":tag_serializer.data['metal_name'],
                    "size_name":size_name,
                    "gross_wt":tag_serializer.data['tag_gwt'],
                    "net_wt":tag_serializer.data['tag_nwt'],
                    "less_wt":tag_serializer.data['tag_lwt'],
                    "stone_wt":tag_serializer.data['tag_stn_wt'],
                    "dia_wt":tag_serializer.data['tag_dia_wt'],
                    "other_metal_wt":tag_serializer.data['tag_other_metal_wt'],
                    "pure_wt":tag_serializer.data['tag_pure_wt'],
                    "id_product":tag_serializer.data['tag_product_id'],
                    "id_design":tag_serializer.data['tag_design_id'],
                    "id_sub_design":tag_serializer.data['tag_sub_design_id'],
                    "id_purity":tag_serializer.data['tag_purity_id'],
                    "id_size":tag_serializer.data['size'],
                    "pieces":tag_serializer.data['tag_pcs'],
                    "metal_name":tag_serializer.data['metal_name'],
                    "purchase_touch":tag_serializer.data['tag_purchase_touch'],
                    "purchase_va":tag_serializer.data['tag_purchase_va'],
                    "mc_value":tag_serializer.data['tag_mc_value'],
                    "item_cost":item_cost['item_cost'],
                    "stone_details":tag_serializer.data['stone_details'],
                    "image" : image_details,
                    "tag_status":"IN STOCK" if tag_serializer.data['tag_status'] == 1 else "OUT STOCK",
                    "color":"green" if tag_serializer.data['tag_status'] == 1 else "red",
                    "is_wishlist":is_wishlist,
                    "is_cart":is_cart,
                    "related_items": formatted_data["related_items"]
                })
                if result not in response_data:
                    response_data.append(result)
            
            return Response({"status":True,"data":response_data,"message":"No Record Found" if len(response_data)==0 else "Data Retrieved Successfully.."}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        if "erp_tag" not in request.data:
            return Response({"status":False,"message": "Tag id is required"}, status=status.HTTP_200_OK)
        elif "customer" not in request.data:
            return Response({"status":False,"message": "Customer id is required"}, status=status.HTTP_200_OK)
        elif not Customers.objects.filter(id_customer=request.data['customer']).exists():
            return Response({"status":False,"message": "Customer not found"}, status=status.HTTP_200_OK)
        else:
            if(ErpTagging.objects.filter(tag_id=request.data['erp_tag'])).exists():
                if(CustomerWishlist.objects.filter(erp_tag = request.data['erp_tag'],customer = request.data['customer'])).exists():
                    CustomerWishlist.objects.filter(erp_tag = request.data['erp_tag'],customer = request.data['customer']).delete()
                    return Response({"status":True,"message": "Wish List Removed Successfully.."}, status=status.HTTP_200_OK)
                else:
                    tag = ErpTagging.objects.filter(tag_id=request.data['erp_tag']).first()
                    request.data.update({
                        "purity":tag.tag_purity_id.pk,
                        "product":tag.tag_product_id.pk, 
                        "design":tag.tag_design_id.pk,
                        "pieces":tag.tag_pcs,
                        "gross_wt":tag.tag_gwt,
                        "net_wt":tag.tag_nwt,
                        "less_wt":tag.tag_lwt,
                        "stone_wt":tag.tag_stn_wt,
                        "purchase_touch":tag.tag_purchase_touch,
                        "purchase_va":tag.tag_purchase_va,
                        "remarks":request.data['remarks']
                    })
                    serializer = CustomerWishlistSerializer(data=request.data)
                    serializer.is_valid(raise_exception = True)
                    serializer.save()
                    return Response({"status":True,"message": "Wish List Added Successfully.."}, status=status.HTTP_200_OK)
            else:
                return Response({"status":False,"message": "No Tag Details Found"}, status=status.HTTP_200_OK)
class CustomerWishlistDetailView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    queryset = CustomerWishlist.objects.all()
    serializer_class = CustomerWishlistSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = CustomerWishlistSerializer(queryset)
        output = serializer.data
        branch = Branch.objects.filter(is_ho=True).first()
        if(queryset.erp_tag==None):
            product = Product.objects.filter(pro_id=queryset.product).get()
            output.update({"def_image":product.image, "images":product.image})
        else:
            tag_def_image = ErpTaggingImages.objects.filter(erp_tag=queryset.erp_tag, is_default=True).first()
            tag_image = ErpTaggingImages.objects.filter(erp_tag=queryset.erp_tag)
            tag_image_serializer = ErpTaggingImagesSerializer(tag_image, many=True)
            output.update({"def_image":tag_def_image.tag_image, "images":tag_image_serializer.data})
        output.update({"added_on":date_format_with_time(queryset.added_on),
                    "ho_branch":branch.pk})
        return Response(output, status=status.HTTP_200_OK)
    

class ERPAllDetails(APIView):
    def get(self, request, *args, **kwargs):
        status_ids = [1, 2, 3, 4, 5]
        status_id = [1,2,3,4,]
        today_date = now().date()
        seven_days_later = today_date + timedelta(days=7)
        fourteen_days_later = today_date + timedelta(days=14) 

    
        # Total Orders List cout
        total_Orders = (
            ERPOrderDetails.objects.filter(order_status_id__in=status_id)
            .values('order_id')
            .distinct()
            .count())
        
        # Today Recived count
        today_received = ERPOrderDetails.objects.filter(
            order_status_id__in=status_ids,
            order__order_date=today_date).values('order_id').distinct().count()
        
        # Today Delivery count
        today_due_orders = ERPOrderDetails.objects.filter(
            order_status_id__lte=5,  
            customer_due_date=today_date
        ).count()

        # Yet_To_Assign total pending details count
        Yet_To_Assign = ERPOrderDetails.objects.filter(order_status__id="1").count()
        
        #Yet To Approve customers
        yet_to_approve = Customers.objects.filter(approved_status=1).count()
        
        customer_cart_item_count = CustomerCart.objects.all().count()

        # Total Delivered
        total_delivered = ERPOrderDetails.objects.filter(order_status__id="5").count()

        # This Week Delivery
        Week_Delivery = ERPOrderDetails.objects.filter(
            order_status_id__lte=5,  
            customer_due_date__range=[today_date, seven_days_later]
        ).count()

        # Next Week Delivery
        next_week_due_orders = ERPOrderDetails.objects.filter(order_status_id__lte=5,
                            customer_due_date__range=[seven_days_later + timedelta(days=1), fourteen_days_later]).count()
        
        # Over Due Order Supplier
        total_overdue_job_orders = (ErpJobOrder.objects.filter(erpjoborderdetails__due_date__lt=today_date,
                                                               
        erpjoborderdetails__status__id__lt=4).distinct().count())

        # Customer Over Due Order
        customer_over_due = ERPOrderDetails.objects.filter(order_status__id__lt="5").count()

        # Customer Total Total Delivery Ready
        customer_total_delivery = ERPOrderDetails.objects.filter(order_status__id="4").count()

        # Customer Total Work Progress
        customer_total_work_progress = ERPOrderDetails.objects.filter(order_status__id="3").count()


        
        data = {
            "total_orders": total_Orders,
            "today_recived":today_received,
            "today_delivary":today_due_orders,
            "yet_to_assign":Yet_To_Assign,
            "yet_to_approve":yet_to_approve,
            "customer_cart_item_count":customer_cart_item_count,
            "total_delivered":total_delivered,
            "week_delivery":Week_Delivery,
            "next_week_delivery":next_week_due_orders,
            "over_due_order_supplier":total_overdue_job_orders,
            "customer_over_due":customer_over_due,
            "customer_total_delivery":customer_total_delivery,
            "customer_total_work_progress":customer_total_work_progress

        }
        return Response(data, status=status.HTTP_200_OK)
    

class ERPTotalOrders(APIView):
    def get(self, request, *args, **kwargs):
        status_id = [1,2,3,4]
        order_details = ERPOrderDetails.objects.filter(
            order_status_id__in=status_id
        ).select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).values(
            'detail_id','order__customer__id_customer','order__customer__firstname','order__customer__mobile','order__order_no', 'order__order_date',             
            'pieces','gross_wt','net_wt','less_wt','customer_due_date','product__product_name','design__design_name','order_status__name',          
        )
        column_mapping = {
            'detail_id': 'order_detail_id','order__customer__id_customer': 'customer_id','order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number','order__order_no': 'order_number','order__order_date': 'date_of_order',
            'pieces': 'total_pieces','gross_wt': 'gross_weight','net_wt': 'net_weight','less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery','product__product_name': 'product_title','design__design_name': 'design_title',
            'order_status__name': 'status',
        }

        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(order_details)
        ]

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data,
            }
        return Response(context, status=status.HTTP_200_OK)


class ERPreceivedOrders(APIView):
    def get(self, request, *args, **kwargs):
        today_date = date.today()
        status_ids = [1, 2, 3, 4, 5]
        order_details = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product','design', 'order_status'
        ).filter(
            order_status_id__in=status_ids,  
            order__order_date=today_date
        ).values(
            'detail_id','order__customer__id_customer','order__customer__firstname','order__customer__mobile',
            'order__order_no','order__order_date','pieces','gross_wt','net_wt','less_wt','customer_due_date',
            'product__product_name','design__design_name','order_status__name',
        )

        column_mapping = {
            'detail_id': 'order_detail_id','order__customer__id_customer': 'customer_id','order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number','order__order_no': 'order_number','order__order_date': 'date_of_order',
            'pieces': 'total_pieces','gross_wt': 'gross_weight','net_wt': 'net_weight','less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery','product__product_name': 'product_title','design__design_name': 'design_title',
            'order_status__name': 'status',
        }

        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(order_details)
        ]

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data,
        }
        return Response(context, status=status.HTTP_200_OK)
    
class ERPTodayDeliveredOrders(APIView):
    def get(self, request, *args, **kwargs):
        today_date = date.today()

        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
            order_status_id=4,  
            customer_due_date=today_date
        ).values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'customer_due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )
        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }

        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data,
            "actions": {"is_add_req": True, "is_edit_req": True, "is_delete_req": False, "is_print_req": False, "is_cancel_req": False, "is_total_req": True},
        }

        return Response(context, status=status.HTTP_200_OK)
    
class ERPYetToAssignOrders(APIView):
    def get(self, request, *args, **kwargs):
        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
            order_status__id="1",  
        ).values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'customer_due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )
        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }
        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data
        }
        return Response( context, status=status.HTTP_200_OK)


class ERPTotalDeliveredOrders(APIView):
    def get(self, request, *args, **kwargs):
        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
            order_status_id=5
        ).values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'customer_due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )
        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }
        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data,
        }
        return Response( context, status=status.HTTP_200_OK) 

class ERPWeekDeliveryOrders(APIView):
    def get(self, request, *args, **kwargs):
        today_date = now().date()
        seven_days_later = today_date + timedelta(days=7)

        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
             order_status_id__lte=5,  
            customer_due_date__range=[today_date, seven_days_later] 
        ).values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'customer_due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )

        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }

        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]
 

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data,
        }
        return Response( context, status=status.HTTP_200_OK)
    

class ERPNextWeekDeliveryOrders(APIView):
    def get(self, request, *args, **kwargs):
        today_date = now().date()
        seven_days_later = today_date + timedelta(days=7)
        fourteen_days_later = today_date + timedelta(days=14) 

        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
            order_status_id__lte=5,
            customer_due_date__range=[seven_days_later + timedelta(days=1), fourteen_days_later]
        ).values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'customer_due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )

        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }
        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]

        # Context for response
        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data,
        }
        return  Response( context, status=status.HTTP_200_OK)

class ERPOverDueOrderSupplier(APIView):
    def get(self, request, *args, **kwargs):
        today_date = now().date()

        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
            erpjoborderdetails__due_date__lt=today_date,
            erpjoborderdetails__status__id__lt=4
        
        ).distinct().values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'erpjoborderdetails__due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )
        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'erpjoborderdetails__due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }
        def format_date(date_value):
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]
        # Context for response
        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data,  
        }
        return Response( context, status=status.HTTP_200_OK)
    

class ERPCustomerOverDueOrder(APIView):
    def get(self, request, *args, **kwargs):
        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
            order_status__id__lt="5"
        ).distinct().values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'customer_due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )

        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }
        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data
        }
        return Response(context, status=status.HTTP_200_OK)
    

class ERPTotalDeliveryReady(APIView):
    def get(self, request, *args, **kwargs):
        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
            order_status__id="4"
        ).distinct().values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'customer_due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )

        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }
        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data
        }
        return Response(context, status=status.HTTP_200_OK)



class ERPWorkProgress(APIView):
    def get(self, request, *args, **kwargs):
        delivery_orders = ERPOrderDetails.objects.select_related(
            'order', 'order__customer', 'product', 'design', 'order_status'
        ).filter(
            order_status__id="3"
        ).distinct().values(
            'detail_id',
            'order__customer__id_customer',
            'order__customer__firstname',
            'order__customer__mobile',
            'order__order_no',
            'order__order_date',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'customer_due_date',
            'product__product_name',
            'design__design_name',
            'order_status__name',
        )

        column_mapping = {
            'detail_id': 'order_detail_id',
            'order__customer__id_customer': 'customer_id',
            'order__customer__firstname': 'customer_name',
            'order__customer__mobile': 'contact_number',
            'order__order_no': 'order_number',
            'order__order_date': 'date_of_order',
            'pieces': 'total_pieces',
            'gross_wt': 'gross_weight',
            'net_wt': 'net_weight',
            'less_wt': 'deduction_weight',
            'customer_due_date': 'expected_delivery',
            'product__product_name': 'product_title',
            'design__design_name': 'design_title',
            'order_status__name': 'status',
        }
        def format_date(date_value):
            """ Helper function to format date as DD-MM-YYYY """
            if date_value:
                return date_value.strftime('%d-%m-%Y')
            return None

        data = [
               { **{column_mapping[key]: (format_date(value) if key in ['order__order_date', 'customer_due_date'] else value) for key, value in entry.items()},
                "sno": index + 1,
                "pk_id": entry["detail_id"]}
            for index, entry in enumerate(delivery_orders)
        ]

        context = {
            "column": ORDER_TOTAL_COLUMN_LIST,
            "data":data
        }
        return Response(context, status=status.HTTP_200_OK)
    
class CustomerCustomizedOrderListView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    
    def post(self, request, *args, **kwargs):
        output = []
        if "id_customer" not in request.data:
            return Response({"status":False,"message": "Customer id is required"}, status=status.HTTP_200_OK)
        else:
            order_detail_query = ERPOrderDetails.objects.filter(order__customer=request.data['id_customer']).order_by('-detail_id')
            paginator, page = pagination.paginate_queryset(order_detail_query, request)
            order_detail_serializer = ErpOrdersDetailSerializer(page, many=True)
            for details in order_detail_serializer.data:
                instance = {}
                order_status = ERPOrderStatus.objects.filter(id=details['order_status']).first()
                instance.update({
                    "product_name":details['customized_product_name'] if details['customized_product_name']!=None else details['product_name'], 
                    "customer_nick_name":details['nick_name'], 
                    "design_name": (
                        details['customized_design_name'] if details['customized_design_name']!=None
                        else details['design_name'] if details.get('design') is not None 
                        else ""
                    ),
                    "pieces":details['pieces'], 
                    "customer_due_date":details['customer_due_date'],
                    "weight":details['gross_wt'], 
                    "status":order_status.name,
                    "status_colour":order_status.colour, 
                    "pk_id":details['detail_id']
                })
                if instance not in output:
                    output.append(instance)
            return Response({
                        "status":True,
                        "data": output,
                        'page_count':paginator.count,
                        'total_pages': paginator.num_pages,
                        'current_page': page.number
                    }, status=status.HTTP_200_OK)
    
class CustomerCustomizedOrderDetailView(generics.GenericAPIView):
    permission_classes = [IsCustomerUser]
    serializer_class = ErpOrdersDetailSerializer
    queryset = ERPOrderDetails.objects.all()
    
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = ErpOrdersDetailSerializer(obj)
        output = {}
        order = ERPOrder.objects.filter(order_id=obj.order.pk).first()
        customer = Customers.objects.filter(user=order.customer.pk).first()
        order_status = ERPOrderStatus.objects.filter(id=obj.order_status.pk).first()
        output.update({
            "customer_nick_name":obj.nick_name,
            "status":order_status.name,
            "status_colour":order_status.colour, 
            "order_no":order.order_no, 
            "order_type":"Customized Order",
            "customer_due_date":format_date(obj.customer_due_date), 
            "product_name":obj.customized_product_name if order.order_type ==4 else obj.product.product_name, 
            "design_name": (
                        obj.customized_design_name if order.order_type == 4 
                        else obj.design.design_name if obj.design is not None 
                        else ""
                    ),
            "stone_name":obj.customized_stone_name,
            "stone_wt":obj.customized_stone_wt, 
            "req_wt":obj.net_wt, 
            "pieces":obj.pieces,
            "dimension":obj.dimension, 
            "size_name":obj.dimension, 
            "remarks":obj.remarks
        })
        if(ERPOrderImages.objects.filter(order_detail=obj.detail_id).exists()):
            images = ERPOrderImages.objects.filter(order_detail=obj.detail_id)
            images_serializer = ErpOrderImagesSerializer(images, many=True,context={"request":request})
            for image_details in images_serializer.data:
                image_details.update({"doc_type":1})
            output.update({"images":images_serializer.data})
        if(ERPOrderAudios.objects.filter(order_detail=obj.detail_id).exists()):
            audios = ERPOrderAudios.objects.filter(order_detail=obj.detail_id)
            audios_serializer = ERPOrderAudiosSerializer(audios, many=True,context={"request":request})
            for audio_details in audios_serializer.data:
                audio_details.update({"doc_type":2})
            output.update({"audios":audios_serializer.data})
        if(ERPOrderVideos.objects.filter(order_detail=obj.detail_id).exists()):
            videos = ERPOrderVideos.objects.filter(order_detail=obj.detail_id)
            videos_serializer = ERPOrderVideosSerializer(videos, many=True,context={"request":request})
            for video_details in videos_serializer.data:
                video_details.update({"doc_type":3})
            output.update({"videos":videos_serializer.data})
        return Response({"status":True,"data":output}, status=status.HTTP_200_OK)
    
class ERPCustomerCartListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = CustomerCartSerializer
    queryset = CustomerCart.objects.all()
    
    def get(self, request, *args, **kwargs):
        queryset = CustomerCart.objects.all()
        # serializer = CustomerCartSerializer(queryset, many=True)
        branch = Branch.objects.filter(is_ho=True).first()
        preview_images = []
        paginator, page = pagination.paginate_queryset(queryset, request,None,CUSTOMER_CART_COLUMN_LIST)
        serializer = CustomerCartSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"sno":index+1})
            if(data['erp_tag']==None):
                product = Product.objects.filter(pro_id=data['product']).get()
                data.update({"image":product.image, "image_text":product.product_name[0]})
                preview_images.append({"image":product.image, "name":product.product_name})
            else:
                tag = ErpTagging.objects.filter(tag_id=data['erp_tag']).first()
                if(ErpTaggingImages.objects.filter(erp_tag=data['erp_tag'], is_default=True).exists()):
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=data['erp_tag'], is_default=True).first()
                    data.update({"image":tag_image.tag_image, "image_text":tag.tag_code[0]})
                    preview_images.append({"image":tag_image.tag_image, "name":tag.tag_code})
                else:
                    data.update({"image":None, "image_text":tag.tag_code[0]})
            data.update({"added_on":date_format_with_time(data['added_on']),
                        "ho_branch":branch.pk, "preview_images":preview_images})
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        context={
            'columns':CUSTOMER_CART_COLUMN_LIST,
            'actions':CUSTOMER_CART_ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':False,
            'filters':FILTERS
            }
        return pagination.paginated_response(serializer.data,context)
    

#Admin Mobile App Views    
class NonAssignedOrderListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpOrdersSerializer
    queryset = ERPOrder.objects.all()
    
    def post(self, request, *args, **kwargs):
        output = []
        queryset = ERPOrder.objects.all().order_by('-order_id')
        serializer = self.get_serializer(queryset, many=True)
        for data in serializer.data:
            data.update({"order_date":format_date(data['order_date'])})
            detail_query = ERPOrderDetails.objects.filter(order=data['order_id'], order_status__in=[1])
                
            detail_serializer = ErpOrdersDetailSerializer(detail_query, many=True)

            for details in detail_serializer.data:
                if(data['order_type']==4):
                    details.update({
                        "product_name":details['customized_product_name'],
                        "design_name":details['customized_design_name'],
                    })
                if(data['order_type']==3):
                    repair_type_ids  = details['order_repair_type']
                    repair_items = RepairDamageMaster.objects.filter(id_repair__in=repair_type_ids)
                    repair_names = ", ".join(repair_items.values_list("name", flat=True))
                    details.update({
                        "repair_name":repair_names,
                        "karigar_remark":details['remarks'],
                    })  
                    if(details['customized_product_name']!=None):
                        details.update({
                            "product_name":details['customized_product_name'],
                        })
                details.update({"customer_due_date":format_date(details['customer_due_date']),})

                if(details['purity'] is not None):
                    purity = Purity.objects.filter(id_purity=details['purity']).first()
                    details.update({"purity_value":purity.purity})
                else:
                    details.update({"purity_value":None})
                
                if details['erp_tag']==None:
                    if ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists():
                        order_image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id']).earliest('det_order_img_id')
                        order_image_details = ERPOrderImages.objects.filter(order_detail=details['detail_id']).all()
                        order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                        order_image_details_serializer = ErpOrderImagesSerializer(order_image_details,many=True, context={"request": request})
                        details.update({"preview_images":order_image_details_serializer.data})
                        if(data['order_type']==4):
                            details.update({"image":order_image, "image_text":details['customized_product_name'][0]})
                        else:
                            details.update({"image":order_image, "image_text":details['product_name'][0]})
                    else:
                        if(data['order_type']==4):
                            details.update({"image":None, "image_text":details['customized_product_name'][0]})
                        else:
                            if details['product']!=None:
                                details.update({"image":None, "image_text":details['product_name'][0]})
                            else:
                                details.update({"image":None, "image_text":""})
                else:
                    if ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).exists():
                        order_image_query = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).earliest('id')
                        order_image_details = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).all()
                        order_image = ErpTaggingImagesSerializer(order_image_query, context={"request": request}).data['tag_image']
                        order_image_details_serializer = ErpTaggingImagesSerializer(order_image_details,many=True, context={"request": request})
                        details.update({"preview_images":order_image_details_serializer.data})
                        if(data['order_type']==4):
                                details.update({"image":order_image, "image_text":details['customized_product_name'][0]})
                        else:
                            details.update({"image":order_image, "image_text":details['product_name'][0]})
                    else:
                        if(data['order_type']==4):
                            details.update({"image":None, "image_text":details['customized_product_name'][0]})
                        else:
                            details.update({"image":None, "image_text":details['product_name'][0]})
                        
                if details not in output:
                    output.append({**details,**data})
        sorted_output = sorted(output, key=lambda x: x['detail_id'], reverse=True)
        return Response(sorted_output, status=status.HTTP_200_OK)
    

class InprogressOrdersListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        output = []
        status_option = request.query_params.get('status', 'inprogress')
        id_supplier = request.data["id_supplier"]
        due_date = request.data["date"]
        id_customer = request.data["id_customer"]

        if status_option == 'inprogress':
            queryset = ErpJobOrderDetails.objects.filter(status=3).order_by('-id_job_order_detail')
            if id_supplier!="":
                    queryset = queryset.filter(job_order__supplier=id_supplier)
            serializer = ErpJobOrderDetailSerializer(queryset, many=True)
            for data in serializer.data:
                detail_query = ERPOrderDetails.objects.filter(detail_id=data['order_detail']).first()
                detail_serializer = ErpOrdersDetailSerializer(detail_query)
                detail_data = detail_serializer.data
                if 'detail_id' in detail_data:
                    order_query = ERPOrder.objects.filter(order_id=detail_serializer.data['order']).first()
                    order_serializer = ErpOrdersSerializer(order_query)
                    order_data = order_serializer.data
                    order_data.update({"order_date":format_date(order_data['order_date'])})
                    if(order_data['order_type']==4):
                        detail_data.update({
                            "product_name":detail_data['customized_product_name'],
                            "design_name":detail_data['customized_design_name'],
                        })
                    if(order_data['order_type']==3):
                        repair_type_ids  = detail_data['order_repair_type']
                        repair_items = RepairDamageMaster.objects.filter(id_repair__in=repair_type_ids)
                        repair_names = ", ".join(repair_items.values_list("name", flat=True))
                        detail_data.update({
                            "repair_name":repair_names,
                            "karigar_remark":detail_data['remarks'],
                        })  
                        if(detail_data['customized_product_name']!=None):
                            detail_data.update({
                                "product_name":detail_data['customized_product_name'],
                            })
                    detail_data.update({"customer_due_date":format_date(detail_data['customer_due_date']),})
                    if(detail_data['purity'] is not None):
                        purity = Purity.objects.filter(id_purity=detail_data['purity']).first()
                        detail_data.update({"purity_value":purity.purity})
                    else:
                        detail_data.update({"purity_value":None})
                    
                    if detail_data['erp_tag']==None:
                        if ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).exists():
                            order_image_query = ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).earliest('det_order_img_id')
                            order_image_details = ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).all()
                            order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                            order_image_details_serializer = ErpOrderImagesSerializer(order_image_details,many=True, context={"request": request})
                            detail_data.update({"preview_images":order_image_details_serializer.data})
                            if(order_data['order_type']==4):
                                detail_data.update({"image":order_image, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":order_image, "image_text":detail_data['product_name'][0]})
                        else:
                            if(order_data['order_type']==4):
                                detail_data.update({"image":None, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                if detail_data['product']!=None:
                                    detail_data.update({"image":None, "image_text":detail_data['product_name'][0]})
                                else:
                                    detail_data.update({"image":None, "image_text":""})
                    else:
                        if ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).exists():
                            order_image_query = ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).earliest('id')
                            order_image_details = ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).all()
                            order_image = ErpTaggingImagesSerializer(order_image_query, context={"request": request}).data['tag_image']
                            order_image_details_serializer = ErpTaggingImagesSerializer(order_image_details,many=True, context={"request": request})
                            detail_data.update({"preview_images":order_image_details_serializer.data})
                            if(order_data['order_type']==4):
                                    detail_data.update({"image":order_image, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":order_image, "image_text":detail_data['product_name'][0]})
                        else:
                            if(order_data['order_type']==4):
                                detail_data.update({"image":None, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":None, "image_text":detail_data['product_name'][0]})
                            
                    if data not in output:
                        if status_option == 'delivery_ready':
                            if detail_data['order_status'] == 4:
                                output.append({**detail_data,**order_data, **data})
                        else:
                            output.append({**detail_data,**order_data, **data})

        
        if status_option == 'delivery_ready' or status_option == 'delivered':
            if status_option == 'delivery_ready':
                queryset = ERPOrderDetails.objects.filter(order_status=4).order_by('-detail_id')
            elif status_option == 'delivered':
                queryset = ERPOrderDetails.objects.filter(order_status=5).order_by('-detail_id')
            serializer = ErpOrdersDetailSerializer(queryset, many=True)
            for detail_data in serializer.data:
                
                # detail_query = ERPOrderDetails.objects.filter(detail_id=data['order_detail']).first()
                
                # if status_option == 'delivery_ready':
                #     filters = {'detail_id': data['order_detail'], 'order_status': 4}
                #     if id_customer != "":
                #         filters['order__customer'] = id_customer
                    
                #     detail_query = ERPOrderDetails.objects.filter(**filters).first()
                # else:
                #     detail_query = ERPOrderDetails.objects.filter(detail_id=data['order_detail']).first()
        
                # if status_option == 'delivered':
                #     filters = {'detail_id': data['order_detail'], 'order_status': 5}
                #     if id_customer != "":
                #         filters['order__customer'] = id_customer
                #     if due_date!='':
                #         filters['delivered_on'] = due_date
                #     detail_query = ERPOrderDetails.objects.filter(**filters).first()
                # detail_serializer = ErpOrdersDetailSerializer(detail_query)
                # detail_data = detail_serializer.data
                if 'detail_id' in detail_data:
                    order_query = ERPOrder.objects.filter(order_id=detail_data['order']).first()
                    order_serializer = ErpOrdersSerializer(order_query)
                    order_data = order_serializer.data
                    order_data.update({"order_date":(order_data['date'])})
                    if(order_data['order_type']==4):
                        detail_data.update({
                            "product_name":detail_data['customized_product_name'],
                            "design_name":detail_data['customized_design_name'],
                        })
                    if(order_data['order_type']==3):
                        repair_type_ids  = detail_data['order_repair_type']
                        repair_items = RepairDamageMaster.objects.filter(id_repair__in=repair_type_ids)
                        repair_names = ", ".join(repair_items.values_list("name", flat=True))
                        detail_data.update({
                            "repair_name":repair_names,
                            "karigar_remark":detail_data['remarks'],
                        })  
                        if(detail_data['customized_product_name']!=None):
                            detail_data.update({
                                "product_name":detail_data['customized_product_name'],
                            })
                    detail_data.update({"customer_due_date":format_date(detail_data['customer_due_date']),})
                    if(detail_data['purity'] is not None):
                        purity = Purity.objects.filter(id_purity=detail_data['purity']).first()
                        detail_data.update({"purity_value":purity.purity})
                    else:
                        detail_data.update({"purity_value":None})
                    
                    if detail_data['erp_tag']==None:
                        if ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).exists():
                            order_image_query = ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).earliest('det_order_img_id')
                            order_image_details = ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).all()
                            order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                            order_image_details_serializer = ErpOrderImagesSerializer(order_image_details,many=True, context={"request": request})
                            detail_data.update({"preview_images":order_image_details_serializer.data})
                            if(order_data['order_type']==4):
                                detail_data.update({"image":order_image, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":order_image, "image_text":detail_data['product_name'][0]})
                        else:
                            if(order_data['order_type']==4):
                                detail_data.update({"image":None, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                if detail_data['product']!=None:
                                    detail_data.update({"image":None, "image_text":detail_data['product_name'][0]})
                                else:
                                    detail_data.update({"image":None, "image_text":""})
                    else:
                        if ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).exists():
                            order_image_query = ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).earliest('id')
                            order_image_details = ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).all()
                            order_image = ErpTaggingImagesSerializer(order_image_query, context={"request": request}).data['tag_image']
                            order_image_details_serializer = ErpTaggingImagesSerializer(order_image_details,many=True, context={"request": request})
                            detail_data.update({"preview_images":order_image_details_serializer.data})
                            if(order_data['order_type']==4):
                                    detail_data.update({"image":order_image, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":order_image, "image_text":detail_data['product_name'][0]})
                        else:
                            if(order_data['order_type']==4):
                                detail_data.update({"image":None, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":None, "image_text":detail_data['product_name'][0]})
                    # if ErpJobOrderDetails.objects.filter(order_detail=detail_data['detail_id']).exists():
                    #     job_order_query = ErpJobOrderDetails.objects.filter(order_detail=detail_data['detail_id']).first()
                    #     job_order_serializer = ErpJobOrderDetailSerializer(job_order_query)
                    #     job_order_data = job_order_serializer.data
                    #     if job_order_data['job_order'] is not None:
                    #         job_order = ErpJobOrder.objects.filter(id_job_order=job_order_data['job_order']).first()
                    #         job_order_serializer = ErpJobOrderSerializer(job_order)
                    #         job_order_data.update({"job_order":job_order_serializer.data})
                    #         detail_data.update({**job_order_data})
                    # else:
                    
                        
                    detail_data.update({
                        "id_job_order_detail":"",
                        "due_date":"",
                        "delivery_date":"",
                        "job_order":"",
                        "order_detail":"",
                        "status":"",
                        "supplier_name":"",
                        "supplier_mobile":"",
                    })
                    if ErpJobOrderDetails.objects.filter(order_detail=detail_data['detail_id'],status = 5).exists():
                        job_order_queryset = ErpJobOrderDetails.objects.filter(order_detail=detail_data['detail_id'],status = 5).get()
                        job_detail_serializer = ErpJobOrderDetailSerializer(job_order_queryset)
                        job_order = ErpJobOrder.objects.get(id_job_order=job_detail_serializer.data['job_order'])
                        detail_data.update({"supplier_name":job_order.supplier.supplier_name,"supplier_mobile":job_order.supplier.mobile_no})
                    output.append({**detail_data,**order_data})
                    # if data not in output:
                    #     if status_option == 'delivery_ready':
                    #         if detail_data['order_status'] == 4:
                    #             output.append({**detail_data,**order_data, **data})
                    #     else:
                    #         output.append({**detail_data,**order_data, **data})
        sorted_output = sorted(output, key=lambda x: x['detail_id'], reverse=True)
        return Response({"data":sorted_output,"message":"Data Retrieved Successfully"}, status=status.HTTP_200_OK)



# Inter order Process assign and tracking 
class ErpAssignInternalProcess(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        try:    
            with transaction.atomic():
                process_type = request.data['process_type']
                if(len(request.data['order_detail_ids'])==0):
                    return Response({"message":"Pass order detail ids."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    order_detail_ids = request.data['order_detail_ids']
                    del request.data['order_detail_ids']
                    for each in order_detail_ids:
        
                        if int(process_type) == 1:
                            ERPOrderDetails.objects.filter(detail_id=each['detail_id']).update(
                                order_status=3,
                                internal_order_process = process_type,
                            )
                        if int(process_type) == 9:
                            ERPOrderDetails.objects.filter(detail_id=each['detail_id']).update(
                                order_status=9,
                                cancel_reason = each['remarks'],
                                cancelled_date = datetime.now(),
                            )
                        if int(process_type) == 8:
                            ERPOrderDetails.objects.filter(detail_id=each['detail_id']).update(
                                order_status=5,
                                delivered_on = datetime.now()
                            )
                        else:
                            ERPOrderDetails.objects.filter(detail_id=each['detail_id']).update(
                                    internal_order_process = process_type,
                                )
                        if int(process_type) == 7:
                             ERPOrderDetails.objects.filter(detail_id=each['detail_id']).update(
                                order_status=4,
                            )
                        log_details = {"order_detail":each['detail_id'], "internal_order_process":process_type,"created_by":request.user.pk}   
                        log_serializer = ErpOrderInternalProcessLogSerializer(data=log_details)
                        if log_serializer.is_valid():
                            log_serializer.save()
                    return Response({"data":{},"message":"Internal process assigned successfully."}, status=status.HTTP_200_OK )
        except ValueError :
            return Response({"data":{},"message":"" }, status=status.HTTP_400_BAD_REQUEST)


class InternalOrderProcessListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        output = []
        filter_type = request.data['filter_type']
        # 0-Pending,
        # 1-CAD Issue,
        # 2-CAD Receipt,
        # 3-CAM Issue,
        # 4-CAM Receipt,
        # 5-Production Issue,
        # 6-Production Receipt,
        # 7-Delivery ready,
        # 8-Over due orders
        if int(filter_type) == 0: 
            queryset = ERPOrderDetails.objects.filter(order_status = 1).order_by('-detail_id')
        elif int(filter_type) == 7: 
            queryset = ERPOrderDetails.objects.filter(order_status = 4).order_by('-detail_id')
        elif int(filter_type) == 8:
            queryset = ERPOrderDetails.objects.filter(order_status=3,customer_due_date__lt = date.today()).order_by('-detail_id')
        else:
            queryset = ERPOrderDetails.objects.filter(internal_order_process = filter_type ).order_by('-detail_id')
            
        serializer = ErpOrdersDetailSerializer(queryset,many=True)
        for detail_data in serializer.data:
            if 'detail_id' in detail_data:
                    order_query = ERPOrder.objects.filter(order_id=detail_data['order']).first()
                    order_serializer = ErpOrdersSerializer(order_query)
                    order_data = order_serializer.data
                    order_data.update({"order_date":format_date(order_data['order_date'])})
                    if(order_data['order_type']==4):
                        detail_data.update({
                            "product_name":detail_data['customized_product_name'],
                            "design_name":detail_data['customized_design_name'],
                        })
                    if(order_data['order_type']==3):
                        repair_type_ids  = detail_data['order_repair_type']
                        repair_items = RepairDamageMaster.objects.filter(id_repair__in=repair_type_ids)
                        repair_names = ", ".join(repair_items.values_list("name", flat=True))
                        detail_data.update({
                            "repair_name":repair_names,
                            "karigar_remark":detail_data['remarks'],
                        })  
                        if(detail_data['customized_product_name']!=None):
                            detail_data.update({
                                "product_name":detail_data['customized_product_name'],
                            })
                    detail_data.update({"customer_due_date":format_date(detail_data['customer_due_date']),})
                    if(detail_data['purity'] is not None):
                        purity = Purity.objects.filter(id_purity=detail_data['purity']).first()
                        detail_data.update({"purity_value":purity.purity})
                    else:
                        detail_data.update({"purity_value":None})
                    
                    if detail_data['erp_tag']==None:
                        if ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).exists():
                            order_image_query = ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).earliest('det_order_img_id')
                            order_image_details = ERPOrderImages.objects.filter(order_detail=detail_data['detail_id']).all()
                            order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                            order_image_details_serializer = ErpOrderImagesSerializer(order_image_details,many=True, context={"request": request})
                            detail_data.update({"preview_images":order_image_details_serializer.data})
                            if(order_data['order_type']==4):
                                detail_data.update({"image":order_image, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":order_image, "image_text":detail_data['product_name'][0]})
                        else:
                            if(order_data['order_type']==4):
                                detail_data.update({"image":None, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                if detail_data['product']!=None:
                                    detail_data.update({"image":None, "image_text":detail_data['product_name'][0]})
                                else:
                                    detail_data.update({"image":None, "image_text":""})
                    else:
                        if ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).exists():
                            order_image_query = ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).earliest('id')
                            order_image_details = ErpTaggingImages.objects.filter(erp_tag_id=detail_data['erp_tag']).all()
                            order_image = ErpTaggingImagesSerializer(order_image_query, context={"request": request}).data['tag_image']
                            order_image_details_serializer = ErpTaggingImagesSerializer(order_image_details,many=True, context={"request": request})
                            detail_data.update({"preview_images":order_image_details_serializer.data})
                            if(order_data['order_type']==4):
                                    detail_data.update({"image":order_image, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":order_image, "image_text":detail_data['product_name'][0]})
                        else:
                            if(order_data['order_type']==4):
                                detail_data.update({"image":None, "image_text":detail_data['customized_product_name'][0]})
                            else:
                                detail_data.update({"image":None, "image_text":detail_data['product_name'][0]})
                    detail_data.update({
                        "id_job_order_detail":"",
                        "due_date":"",
                        "delivery_date":"",
                        "job_order":"",
                        "order_detail":"",
                        "status":"",
                        "supplier_name":"",
                        "supplier_mobile":"",
                    })
                    output.append({**detail_data,**order_data})
        
        sorted_output = sorted(output, key=lambda x: x['detail_id'], reverse=True)
        return Response({"data":sorted_output,"message":"Data Retrieved Successfully"}, status=status.HTTP_200_OK)

# Inter order Process assign and tracking 


class CustomerOrdersStatusListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        
        output = []
        karigar_fil = request.data.get('karigar',None)
        order_fil = request.data.get('order_status',None)
        branch_fil = request.data.get('branch',None)
        date = request.data.get('date',None)
        from_date = request.data.get('from_date',None)
        to_date = request.data.get('to_date',None)
        order_type = request.data.get('order_type', None)
        customer = request.data.get('customer',None)
        print(customer,"customer")
        print(karigar_fil)
        queryset = ERPOrder.objects.filter(order_type=order_type).all()
        if customer:
            queryset = queryset.filter(customer=customer).order_by('-order_id')
        elif from_date and to_date:
            queryset = queryset.filter(order_date__lte=to_date, order_date__gte=from_date).order_by('-order_id')
        if branch_fil:
            queryset = queryset.filter(order_branch=branch_fil).order_by('-order_id')

        serializer = ErpOrdersSerializer(queryset, many=True)
        
        detail_query = ERPOrderDetails.objects.all()
        if order_fil != None:
            detail_query = ERPOrderDetails.objects.filter(order_status=order_fil)
        detail_serializer = ErpOrdersDetailSerializer(detail_query, many=True)
        
        for data in serializer.data:
            for details in detail_serializer.data:
                instance = {}
                if (data['order_id'] == details['order']):
                    if details['erp_tag']==None:
                        if ERPOrderImages.objects.filter(order_detail=details['detail_id']).exists():
                            order_image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id']).earliest('det_order_img_id')
                            order_image_details = ERPOrderImages.objects.filter(order_detail=details['detail_id']).all()
                            order_image = ErpOrderImagesSerializer(order_image_query, context={"request": request}).data['image']
                            order_image_details_serializer = ErpOrderImagesSerializer(order_image_details,many=True, context={"request": request})
                            instance.update({"preview_images":order_image_details_serializer.data})
                            if(data['order_type']==4):
                                instance.update({"image":order_image, "image_text":details['customized_product_name'][0]})
                            else:
                                instance.update({"image":order_image, "image_text":details['product_name'][0]})
                        else:
                            if(data['order_type']==4):
                                instance.update({"image":None, "image_text":details['customized_product_name'][0]})
                            else:
                                instance.update({"image":None, "image_text":details['product_name'][0]})
                    else:
                        if ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).exists():
                            order_image_query = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).earliest('id')
                            order_image_details = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).all()
                            order_image = ErpTaggingImagesSerializer(order_image_query, context={"request": request}).data['tag_image']
                            order_image_details_serializer = ErpTaggingImagesSerializer(order_image_details,many=True, context={"request": request})
                            instance.update({"preview_images":order_image_details_serializer.data})
                            if(data['order_type']==4):
                                instance.update({"image":order_image, "image_text":details['customized_product_name'][0]})
                            else:
                                instance.update({"image":order_image, "image_text":details['product_name'][0]})
                        else:
                            if(data['order_type']==4):
                                instance.update({"image":None, "image_text":details['customized_product_name'][0]})
                            else:
                                instance.update({"image":None, "image_text":details['product_name'][0]})
                        
                    
                    if ERPOrderVideos.objects.filter(order_detail=details['detail_id']).exists():
                        order_video_query = ERPOrderVideos.objects.filter(order_detail=details['detail_id']).earliest('det_order_vid_id')
                        order_video = ERPOrderVideosSerializer(order_video_query, context={"request": request}).data['video']
                        
                        order_video_details = ERPOrderVideos.objects.filter(order_detail=details['detail_id']).all()
                        order_video_details_serializer = ERPOrderVideosSerializer(order_video_details, many=True,context={"request": request})
                        instance.update({"preview_videos":order_video_details_serializer.data})

                        if(data['order_type']==4):
                            instance.update({"video": order_video,"video_text":details['customized_product_name'][0]})
                        else:
                            instance.update({"video": order_video,"video_text":details['product_name'][0]})
                    else:
                        if(data['order_type']==4):
                            instance.update({"video": None,"video_text":details['customized_product_name'][0]})
                        else:
                            instance.update({"video": None,"video_text":details['product_name'][0]})

                    
                    if ERPOrderAudios.objects.filter(order_detail=details['detail_id']).exists():
                        order_audio_query = ERPOrderAudios.objects.filter(order_detail=details['detail_id']).earliest('det_order_audio_id')
                        order_audio = ERPOrderAudiosSerializer(order_audio_query, context={"request": request}).data['audio']
                        
                        order_audio_details = ERPOrderAudios.objects.filter(order_detail=details['detail_id']).all()
                        order_audio_details_serializers = ERPOrderAudiosSerializer(order_audio_details, many=True,context={"request": request})
                        instance.update({"preview_voices":order_audio_details_serializers.data})
                        
                        if(data['order_type']==4):
                            instance.update({"audio": order_audio,"audio_text":details['customized_product_name'][0]})
                        else:
                            instance.update({"audio": order_audio,"audio_text":details['product_name'][0]})
                    else:
                        if(data['order_type']==4):
                            instance.update({"audio": None,"audio_text":details['customized_product_name'][0]})
                        else:
                            instance.update({"audio": None,"audio_text":details['product_name'][0]})

                    customer = Customers.objects.filter(id_customer=data['customer']).first()
                    order_status = ERPOrderStatus.objects.get(id=details['order_status'])
                    if(data['order_type']==4):
                        instance.update({"product":details['customized_product_name'],
                                         "design":details['customized_design_name'], })
                    else:
                        instance.update({"product":details['product_name'],
                                         "design":details.get('design_name'),})
                    instance.update({
                        "order_no":data['order_no'], 
                        "order_date":data['order_date'],
                        "order_type":data['order_type'],
                        "supplier":data['supplier'],
                        "customer":customer.firstname,
                        "mobile":customer.mobile, 
                        "order_status":details['order_status'],
                        # "sub_design":details.get('sub_design_name'), 
                        "pieces":details['pieces'],
                        "gross_wt":details['gross_wt'], 
                        "less_wt":details['less_wt'], 
                        "net_wt":details['net_wt'],
                        "repair_type":details['repair_type'],
                        "colour":order_status.colour, 
                        "name":order_status.name,
                        "cancel_reason":'',
                        'detail_id':details['detail_id'],
                        'customer_order_type':'Customized Order' if details['is_reserved_item']==0 else 'Reserve Order'
                    })
                    if(details['order_status']!=6 and ErpJobOrderDetails.objects.filter(order_detail=details['detail_id']).exists()):

                        job_detail_query = ErpJobOrderDetails.objects.filter(order_detail = details['detail_id'])
                        if karigar_fil != None:
                            job_detail_query = ErpJobOrderDetails.objects.filter(job_order__supplier=karigar_fil, order_detail=details['detail_id'])
                        job_detail_query = job_detail_query.first()
                        job_order_query = ErpJobOrderDetailSerializer(job_detail_query)
                        instance.update({"karigar" : job_order_query.data['supplier_name']})
                        
                    else:
                        instance.update({"karigar":None})
                    if(details['erp_tag']):
                        tag_query = ErpTagging.objects.get(tag_id=details['erp_tag'])
                        instance['tag_code'] = tag_query.tag_code
                        instance['karigar'] = tag_query.tag_lot_inward_details.lot_no.id_supplier.supplier_name
                    # else :
                    #     instance.update({"karigar":None})

                    # Repair
                    repair_type_ids  = details['order_repair_type']
                    repair_items = RepairDamageMaster.objects.filter(id_repair__in=repair_type_ids)
                    repair_names = ", ".join(repair_items.values_list("name", flat=True))
                    instance.update({
                        "repair_name":repair_names,
                    })  
                    # Repair
                    
                    if instance not in output:
                        output.append(instance)
        return Response(output, status=status.HTTP_200_OK)
    

class PurchaseCartListCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = CustomerCart.objects.all()
    serializer_class = CustomerCartSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = CustomerCart.objects.filter(cart_type=2)
        serializer = CustomerCartSerializer(queryset, many=True)
        branch = Branch.objects.filter(is_ho=True).first()
        for data in serializer.data:
            if(data['erp_tag']==None):
                product = Product.objects.filter(pro_id=data['product']).get()
                # print(product.image == '')
                if(product.image == ''):
                    data.update({"image":None,
                                 "image_text":product.product_name[0]})
                else:
                    data.update({"image":product.image,
                                 "image_text":product.product_name[0]})
                data.update({"purchase_touch":0})
            else:
                if(ErpTaggingImages.objects.filter(erp_tag=data['erp_tag']).exists()):
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=data['erp_tag'])
                    tag_image_serializer = ErpTaggingImagesSerializer(tag_image, many=True,context={"request": request})
                    data.update({"image":tag_image_serializer.data})
                    # data.update({"image":None})
                else:
                    data.update({"image":None,"purchase_touch":0})
                tag_queryset = ErpTagging.objects.filter(tag_id=data['erp_tag']).first()
                data.update({"purchase_touch" : tag_queryset.tag_purchase_touch})
            data.update({
                        "added_on":date_format_with_time(data['added_on']),
                        "ho_branch":branch.pk, 
                        "is_cart":True,
                        "is_checked":False
            })
        return Response({"status":True,"data":{"rows": serializer.data,
                                               "columns" : PURCHASE_CART_COLUMN_LIST}}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        # product = Product.objects.filter(pro_id=request.data['product']).first()
        request.data.update({"customer":None})
        if(request.data['erp_tag']!= None):
            tag = ErpTagging.objects.filter(tag_id=request.data['erp_tag']).first()
            if(tag.size != None):
                request.data.update({"size":tag.size.pk})
            elif(tag.size == None):
                request.data.update({"size":None})
            request.data.update({"uom":tag.tag_uom_id.pk, "purity":tag.tag_purity_id.pk,
                                 "product":tag.tag_product_id.pk, "design":tag.tag_design_id.pk,
                                 "pieces":tag.tag_pcs, "gross_wt":tag.tag_gwt,
                                 "less_wt":tag.tag_lwt, "tax_amnt":tag.tag_tax_amount,
                                 "net_wt" : tag.tag_nwt,
                                 "cart_type":2,
                                 "item_cost":tag.tag_item_cost, "taxable_amnt":None, "rate_per_gram":None,
                                 "tax_type":None, "tax_percent":None,"cgst_amnt":None, "sgst_amnt":None, "igst_amnt":None})
            if(tag.tag_sub_design_id != None):
                request.data.update({"sub_design":tag.tag_sub_design_id.pk, })
            elif(tag.tag_sub_design_id == None):
                request.data.update({"sub_design":None})
        request.data.update({"cart_type":2})
        serializer = CustomerCartSerializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data)
    
    def put(self, request, *args, **kwargs):
        # print(request.data)
        for data in request.data['remv_cart_ids']:
            cart_obj = CustomerCart.objects.filter(id=data['id']).first()
            if cart_obj.cart_type == 2:
                cart_obj.delete()
        return Response({"status":True, "message":"Cart Items deleted successfully"}, status=status.HTTP_200_OK)
    
    
class ErpOrderAdminAppPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    serializer_class = ErpOrdersSerializer
    
    def get(self, request, *args, **kwargs):
        order_id = self.kwargs.get('pk')
        queryset = ERPOrder.objects.get(order_id=order_id)
        serializer = ErpOrdersSerializer(queryset)
        output = serializer.data
        est_url = ''
        est_url = self.generate_custom_order_print(order_id,serializer,output,request)
        response_data = { "response_data" : est_url['response_data'] , "response_data" : est_url['pdf_url'] }
        return Response(response_data, status=status.HTTP_200_OK)

    def generate_custom_order_print(self, order_id, serializer, output, request):
        order_details_qs = ERPOrderDetails.objects.filter(order=order_id)
        order_details_serialized = ErpOrdersDetailSerializer(order_details_qs, many=True).data

        old_metal_details = ErpInvoiceOldMetalDetails.objects.filter(order=order_id)
        old_metal_details_serializer = ErpInvoiceOldMetalDetailsSerializer(old_metal_details, many=True).data
        
        advance = ErpIssueReceipt.objects.filter(order=order_id).all()
        advance_serializer = ErpIssueReceiptSerializer(advance, many=True).data
        payment_serializer = []
        payment_amount = 0
        if len(advance_serializer) > 0:
            for advance_data in advance_serializer:
                payment = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt=advance_data['id']).all()
                payment_serializer = ErpIssueReceiptPaymentDetailsSerializer(payment, many=True).data

        if len(payment_serializer) > 0:
    
            for pay in payment_serializer:
                payment_amount +=float(pay['payment_amount'])
        
        branch = Branch.objects.filter(id_branch=serializer.data['order_branch']).first()
        customer = Customers.objects.filter(id_customer=serializer.data['customer']).first()
        comp = Company.objects.get(id_company=1)

        # Get customer address
        customer_address = CustomerAddress.objects.filter(customer=customer.pk).first()
        address = (
            f"{customer_address.line1 or ''} {customer_address.line2 or ''} {customer_address.line3 or ''}".strip()
            if customer_address else None
        )
        output.update({"address": address})

        # Set order type label
        order_type_labels = {1: "Customer Order", 2: "Purchase Order", 3: "Repair Order"}
        output.update({"order_type_label": order_type_labels.get(serializer.data['order_type'], "Order")})

        # Calculate totals
        totals = defaultdict(float)
        order_details = []
        total_old_metal_cost = 0
        for index,details in enumerate(order_details_serialized):
            
            if details['erp_tag']!=None:
                order_image_details = ErpTaggingImages.objects.filter(erp_tag_id=details['erp_tag']).all()
                order_image_details_serializer = ErpTaggingImagesSerializer(order_image_details,many=True, context={"request": request})
                for item in order_image_details_serializer.data:
                    item.update({"image" : item['tag_image']})
                details.update({"order_images" : order_image_details_serializer.data})
            else:
                image_query = ERPOrderImages.objects.filter(order_detail=details['detail_id'])
                image_serializer = ErpOrderImagesSerializer(image_query, many=True, context={'request':request})
                details.update({
                    "order_images":image_serializer.data
                })
            
            details.update({"sno": index+1})
            print('details' , details)
            if Product.objects.filter(pro_id=details['product']).exists():
                product = Product.objects.get(pro_id=details['product'])
                details.update({"cat_id": product.cat_id.pk})
            totals["customer_due_date"] =details['customer_due_date']
            totals["total_pcs"] += int(details['pieces'])
            totals["total_gross_wt"] += float(details['gross_wt'])
            totals["total_net_wt"] += float(details['net_wt'])
            totals["total_less_wt"] += float(details['less_wt'])
            totals["total_wastage_wt"] += float(details['wastage_wt'])
            totals["total_mc"] += float(details['mc_value'])
            totals["total_item_cost"] += float(details['item_cost'])
            totals["taxable_amnt"] += float(details['taxable_amnt'])
            totals["tax_amnt"] += float(details['tax_amnt'])

            order_details.append(details)
        
        for old_metal in old_metal_details_serializer:
            total_old_metal_cost += float(old_metal['amount'])

        output.update({
            "due_date": format_date_short_year(totals["customer_due_date"]),
            "date": format_date_short_year(output["order_date"]),
            "old_metal_details" : old_metal_details_serializer,
            "order_details": order_details,
            "total_pcs": f"{totals['total_pcs']:.0f}",
            "total_gross_wt": f"{totals['total_gross_wt']:.3f}",
            "total_wastage_wt": f"{totals['total_wastage_wt']:.3f}",
            "total_weight" : f"{totals['total_net_wt'] + totals['total_wastage_wt']:.3f}",
            "total_net_wt": f"{totals['total_net_wt']:.3f}",
            "total_less_wt": f"{totals['total_less_wt']:.3f}",
            "total_item_cost": f"{totals['total_item_cost']:.2f}",
            "tax_amnt": f"{totals['tax_amnt']:.2f}",
            "taxable_amnt": f"{totals['taxable_amnt']:.2f}",
            "total_old_metal_cost": f"{total_old_metal_cost:.2f}",
            "payment_amount": f"{payment_amount:.2f}",
            "balance_amt" : f"{float(totals['total_item_cost']) - float(total_old_metal_cost) - float(payment_amount):.2f}",
            "total_mc": f"{totals['total_mc']:.2f}",
            "branch_name": branch.name,
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            "company_name" : comp.short_code
        })

        save_dir = os.path.join(settings.MEDIA_ROOT,
                                'admin_app_customer_order_print')
        save_dir = os.path.join(save_dir, f'{order_id}')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        template = get_template('order_image_print.html')
        html = template.render(output)
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        pdf_path = os.path.join(save_dir, 'admin_app_customer_order_print.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        pdf_path = request.build_absolute_uri(
            settings.MEDIA_URL + f'admin_app_customer_order_print/{order_id}/admin_app_customer_order_print.pdf')

        return {"response_data":output, "pdf_url":pdf_path}