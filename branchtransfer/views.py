from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import transaction , IntegrityError
from django.db.models import  Sum, F, ExpressionWrapper, DecimalField
from utilities.pagination_mixin import PaginationMixin
pagination = PaginationMixin()  # Apply pagination
from common.permissions import IsEmployee
from .models import *
from .serializers import *
from retailmasters.views import BranchEntryDate
from retailmasters.serializers import MetalRatesSerializer
from retailmasters.models import FinancialYear,MetalRates,City,State,Country,Area,Branch,Company
from customers.models import CustomerAddress
from customers.serializers import CustomerAddressSerializer
from inventory.serializers import ErpTaggingLogSerializer,ErpLotInwardNonTagSerializer,ErpLotInwardNonTagStoneSerializer,ErpTaggingSerializer
from utilities.constants import FILTERS
from utilities.utils import format_currency
from .constants import ACTION_LIST,TRANCFER_COLUMN_LIST
from datetime import datetime
from django.utils import timezone
from django.template.loader import get_template
import os
from xhtml2pdf import pisa
import io
import qrcode
from django.conf import settings
import traceback
from rest_framework.exceptions import ValidationError
from retailsettings.models import (RetailSettings)
from utilities.utils import format_date,format_wt
from inventory.views  import get_non_tag_stock
from billing.serializers import get_invoice_no
from core.views  import get_reports_columns_template

TRANSFER_STATUS_COLOUR = [
    {"status": 0, "status_color": "primary"},
    {"status": 1, "status_color": "warning"},
    {"status": 2, "status_color": "success"},
    {"status": 3, "status_color": "danger"},
]

def get_status_color(status):
    color = next((item['status_color'] for item in TRANSFER_STATUS_COLOUR if item['status'] == status), None)
    return color

class ErpBranchTransferCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpStockTransfer.objects.all()
    serializer_class = ErpStockTransferSerializer
    
    def get(self, request, *args, **kwargs):
        id_stock_transfer = self.kwargs.get('pk')
        print_type = int(request.query_params.get('print_type',1))
        pdf_url = self.get_print(id_stock_transfer,request,print_type)
        response_data = {'response_data':pdf_url['response_data']}
        return Response(response_data, status=status.HTTP_200_OK)
    
    def issue_to_details(self,queryset):
        if queryset.stock_issue_to == 1:
            return queryset.id_employee.firstname 
        if queryset.stock_issue_to == 2:
            return queryset.id_customer.firstname
        if queryset.stock_issue_to == 3:
            return queryset.supplier.supplier_name
        else:
            return ''
        

    def get_print(self, id_stock_transfer,request,print_type):

        if print_type == 1:
            queryset = ErpStockTransfer.objects.select_related('transfer_from', 'transfer_to').get(id_stock_transfer =id_stock_transfer)
            response_data = {}
            total_gross_wt = total_net_wt = total_less_wt = total_dia_wt = total_stone_wt = total_pcs = 0
            if(queryset.transfer_type == 1):
            
                transfer_list = ErpTagTransfer.objects.filter(stock_transfer=id_stock_transfer).values('tag_id__tag_product_id').annotate(
                    product_name=F('tag_id__tag_product_id__product_name'),
                    gross_wt=Sum('tag_id__tag_gwt'),
                    net_wt=Sum('tag_id__tag_nwt'),
                    less_wt=Sum('tag_id__tag_lwt'),
                    stn_wt=Sum('tag_id__tag_stn_wt'),
                    dia_wt=Sum('tag_id__tag_dia_wt'),
                    pcs=Sum('tag_id__tag_pcs'),

                ).values(
                    'stock_transfer',
                    'product_name',
                    'gross_wt', 
                    'net_wt',
                    'stn_wt',
                    'dia_wt',
                    'less_wt',
                    'pcs',
                )

                response_data = {
                    'transfer_type':int(queryset.transfer_type),
                    'id_stock_transfer': queryset.id_stock_transfer,
                    'transfer_from':queryset.transfer_from.name,
                    'transfer_to': (queryset.transfer_to.name if(queryset.transfer_to) else ''),
                    'customer': (queryset.id_customer.firstname if(queryset.id_customer) else ''),
                    'emp_name': (queryset.id_employee.firstname if(queryset.id_employee) else ''),
                    'trans_code': queryset.trans_code,
                    'trans_date': queryset.trans_date,
                    'issued_to' : self.issue_to_details(queryset),
                    'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(queryset.trans_to_type, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(queryset.transfer_type, ''),
                    'item_details' : transfer_list
                }

            if(queryset.transfer_type == 2):
        
                transfer_list = ErpNonTagTransfer.objects.filter(stock_transfer=id_stock_transfer).values('id_product').annotate(
                    product_name=F('id_product__product_name'),
                    total_gross_wt=Sum('gross_wt'),
                    total_net_wt=Sum('net_wt'),
                    total_less_wt=Sum('less_wt'),
                    total_stn_wt=Sum('stone_wt'),
                    total_dia_wt=Sum('dia_wt'),
                    pcs=Sum('pieces'),

                ).values(
                    'stock_transfer',
                    'product_name',
                    'total_gross_wt', 
                    'total_net_wt',
                    'total_less_wt',
                    'total_stn_wt',
                    'total_dia_wt',
                    'pcs'
                )

                for item in transfer_list:
                    print(item)
                    item.update ({
                        'gross_wt': item['total_gross_wt'],
                        'net_wt': item['total_net_wt'],  
                        'less_wt': item['total_less_wt'],  
                        'stn_wt': item['total_stn_wt'],
                        'dia_wt': item['total_dia_wt'],
                    })
                    


                response_data={
                    'transfer_type':int(queryset.transfer_type),
                    'id_stock_transfer': queryset.id_stock_transfer,
                    'transfer_from':queryset.transfer_from.name,
                    'transfer_to': (queryset.transfer_to.name if(queryset.transfer_to) else ''),
                    'customer': (queryset.id_customer.firstname if(queryset.id_customer) else ''),
                    'emp_name': (queryset.id_employee.firstname if(queryset.id_employee) else ''),
                    'trans_code': queryset.trans_code,
                    'trans_date': queryset.trans_date,
                    'issued_to' : self.issue_to_details(queryset),
                    'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(queryset.trans_to_type, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(queryset.transfer_type, ''),
                    'item_details' : transfer_list
                }

            for item  in response_data['item_details']:
                total_gross_wt += item.get('gross_wt', 0)
                total_net_wt += item.get('net_wt', 0)
                total_less_wt += item.get('less_wt', 0)
                total_stone_wt += item.get('stn_wt', 0)
                total_dia_wt += item.get('dia_wt', 0)
                total_pcs += item.get('pcs', 0)


            response_data.update({
            'total_gross_wt': format(total_gross_wt, '.3f'),
            'total_net_wt': format(total_net_wt, '.3f'),
            'total_less_wt': format(total_less_wt, '.3f'),
            'total_stone_wt': format(total_stone_wt, '.3f'),
            'total_dia_wt': format(total_dia_wt, '.3f'),
            'total_pcs': total_pcs
            })

        else:
            queryset = ErpStockTransfer.objects.select_related('transfer_from', 'transfer_to').get(id_stock_transfer =id_stock_transfer)
            response_data = {}
            total_gross_wt = total_net_wt = total_less_wt = total_dia_wt = total_stone_wt = total_pcs = 0
            if(queryset.transfer_type == 1):
            
                transfer_list = ErpTagTransfer.objects.filter(stock_transfer=id_stock_transfer).annotate(
                    product_name=F('tag_id__tag_product_id__product_name'),
                    gross_wt=F('tag_id__tag_gwt'),
                    net_wt=F('tag_id__tag_nwt'),
                    less_wt=F('tag_id__tag_lwt'),
                    stn_wt=F('tag_id__tag_stn_wt'),
                    dia_wt=F('tag_id__tag_dia_wt'),
                    pcs=F('tag_id__tag_pcs'),
                    tag_code=F('tag_id__tag_code'),

                ).values(
                    'stock_transfer',
                    'product_name',
                    'gross_wt', 
                    'net_wt',
                    'stn_wt',
                    'dia_wt',
                    'less_wt',
                    'pcs',
                    'tag_id',
                    'tag_code'
                )

                response_data = {
                    'transfer_type':int(queryset.transfer_type),
                    'id_stock_transfer': queryset.id_stock_transfer,
                    'transfer_from':queryset.transfer_from.name,
                    'transfer_to': (queryset.transfer_to.name if(queryset.transfer_to) else ''),
                    'customer': (queryset.id_customer.firstname if(queryset.id_customer) else ''),
                    'emp_name': (queryset.id_employee.firstname if(queryset.id_employee) else ''),
                    'trans_code': queryset.trans_code,
                    'trans_date': queryset.trans_date,
                    'issued_to' : self.issue_to_details(queryset),
                    'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(queryset.trans_to_type, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(queryset.transfer_type, ''),
                    'item_details' : transfer_list,

                }

            if(queryset.transfer_type == 2):
        
                transfer_list = ErpNonTagTransfer.objects.filter(stock_transfer=id_stock_transfer).annotate(
                    product_name=F('id_product__product_name'),
                    total_gross_wt=F('gross_wt'),
                    total_net_wt=F('net_wt'),
                    total_less_wt=F('less_wt'),
                    total_stn_wt=F('stone_wt'),
                    total_dia_wt=F('dia_wt'),
                    pcs=F('pieces'),

                ).values(
                    'stock_transfer',
                    'product_name',
                    'total_gross_wt', 
                    'total_net_wt',
                    'total_less_wt',
                    'total_stn_wt',
                    'total_dia_wt',
                    'pcs'
                )

                for item in transfer_list:
                    print(item)
                    item.update ({
                        'gross_wt': item['total_gross_wt'],
                        'net_wt': item['total_net_wt'],  
                        'less_wt': item['total_less_wt'],  
                        'stn_wt': item['total_stn_wt'],
                        'dia_wt': item['total_dia_wt'],
                    })
                    


                response_data={
                    'transfer_type':int(queryset.transfer_type),
                    'id_stock_transfer': queryset.id_stock_transfer,
                    'transfer_from':queryset.transfer_from.name,
                    'transfer_to': (queryset.transfer_to.name if(queryset.transfer_to) else ''),
                    'customer': (queryset.id_customer.firstname if(queryset.id_customer) else ''),
                    'emp_name': (queryset.id_employee.firstname if(queryset.id_employee) else ''),
                    'trans_code': queryset.trans_code,
                    'trans_date': queryset.trans_date,
                    'issued_to' : self.issue_to_details(queryset),
                    'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(queryset.trans_to_type, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(queryset.transfer_type, ''),
                    'item_details' : transfer_list
                }

            for item  in response_data['item_details']:
                total_gross_wt += item.get('gross_wt', 0)
                total_net_wt += item.get('net_wt', 0)
                total_less_wt += item.get('less_wt', 0)
                total_stone_wt += item.get('stn_wt', 0)
                total_dia_wt += item.get('dia_wt', 0)
                total_pcs += item.get('pcs', 0)


            response_data.update({
            'total_gross_wt': format(total_gross_wt, '.3f'),
            'total_net_wt': format(total_net_wt, '.3f'),
            'total_less_wt': format(total_less_wt, '.3f'),
            'total_stone_wt': format(total_stone_wt, '.3f'),
            'total_dia_wt': format(total_dia_wt, '.3f'),
            'total_pcs': total_pcs
            })


        comp = ''
        # comp = Company.objects.latest("id_company")
        response_data.update({'company_detail': comp})
        response_data['print_type'] = print_type
        
        # save_dir = os.path.join(settings.MEDIA_ROOT, f'stock_transfer/{id_stock_transfer}')

        # if not os.path.exists(save_dir):
        #     os.makedirs(save_dir)
        
        # qr = qrcode.QRCode(
        #     version=1,
        #     error_correction=qrcode.constants.ERROR_CORRECT_L,
        #     box_size=10,
        #     border=4,
        # )
        # qr.add_data(id_stock_transfer)
        # qr.make(fit=True)
        # qr_img = qr.make_image(fill_color="black", back_color="white")
        # qr_path = os.path.join(save_dir, 'qrcode.png')
        # qr_img.save(qr_path)

        
        # response_data['qr_path'] = qr_path
        # print(response_data)
        # template = get_template('stock_transfer_print.html')
        
        # if(print_type==2):
        #     template = get_template('stock_transfer_detail_print.html')
        # html = template.render(response_data)
        # result = io.BytesIO()
        # pisa.pisaDocument(io.StringIO(html), result)
        # pdf_path = os.path.join(save_dir, 'stock_transfer_print.pdf')
        # with open(pdf_path, 'wb') as f:
        #     f.write(result.getvalue())
        # # print(response_data)
        # pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'stock_transfer/{id_stock_transfer}/stock_transfer_print.pdf')

        # return pdf_path
        return {
            "response_data":response_data,
            # "pdf_url":pdf_path
        }
        
     
 

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                transfer_data = request.data
                stock_details = request.data.get('stock_details')
                print(stock_details)
                if not transfer_data:
                    return Response({"error": "Transfer data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not stock_details:
                    return Response({"error": F"Transfer Details is missing. {stock_details}"}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                fy=FinancialYear.objects.get(fin_status=True)
                transfer_date = branch_date.get_entry_date(transfer_data['transfer_from'])
                trans_code = self.generate_trans_code(fy.fin_id)
                transfer_data.update({"fin_year":fy.fin_id,"trans_code":trans_code,"trans_date":transfer_date,"created_by": request.user.id})
                transfer_serializer = ErpStockTransferSerializer(data = transfer_data)
                if transfer_serializer.is_valid(raise_exception=True):
                    transfer_serializer.save()
                    stock_transfer = transfer_serializer.data['id_stock_transfer']

                    if transfer_data['transfer_type'] == 1:
                        stock_details = insert_other_details(stock_details,ErpTagTransferSerializer,{"stock_transfer":stock_transfer})

                    if transfer_data['transfer_type'] == 2:
                        stock_details = self.insert_non_tag_details(stock_details,stock_transfer,transfer_data)

                    if transfer_data['transfer_type'] == 3:
                        stock_details = insert_other_details(stock_details,ErpOldMetalTransferSerializer,{"stock_transfer":stock_transfer})
                        
                    if transfer_data['transfer_type'] == 4:
                        stock_details = insert_other_details(stock_details,ErpSalesReturnTransferSerializer,{"stock_transfer":stock_transfer})

                    if transfer_data['transfer_type'] == 5:
                        stock_details = insert_other_details(stock_details,ErpPartlySaleTransfer,{"stock_transfer":stock_transfer})

                    pdf_url = self.get_print(stock_transfer,request,1)
                    
                        
                    return Response({"message":"Stock Transfer Created Successfully.","pdf_url": pdf_url}, status=status.HTTP_201_CREATED)
                return Response({"error":ErpStockTransferSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)

    def generate_trans_code(self,fin_id):
        code =''
        last_inv=ErpStockTransfer.objects.filter(fin_year =fin_id).order_by('-id_stock_transfer').first()
        if last_inv:
            code= int(last_inv.trans_code)
            code = str(code + 1).zfill(5)
        else:
           code = '00001'
        return code

    
    def insert_non_tag_details(self,non_tag_details,stock_transfer,transfer_data):
        return_data =[]
        for item in non_tag_details:
            item.update({"stock_transfer":stock_transfer})
            stone_details = item['stone_details']
            detail_serializer = ErpNonTagTransferSerializer(data=item)
            if(detail_serializer.is_valid(raise_exception=True)):
                detail_serializer.save()
                stone_details=insert_other_details(stone_details,ErpNonTagStoneTransferSerializer,{"id_non_tag_transfer":detail_serializer.data['id_non_tag_transfer']})            
            else:
                return Response({"error":ErpNonTagTransferSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return return_data


def insert_other_details(details,serializer_name,updated_data):
    return_data =[]
    for item in details:
        item.update(updated_data)
        serializer = serializer_name(data=item)
        if(serializer.is_valid(raise_exception=True)):
            serializer.save()
            return_data.append({**item,**serializer.data})
        else:
            return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    return return_data


class ErpBranchTransferApprovalAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpStockTransfer.objects.all()
    serializer_class = ErpStockTransferSerializer
    
    def get(self, request, *args, **kwargs):

        try :
            trans_code = request.query_params.get('trans_code')
            transfer_from = request.query_params.get('transfer_from')
            transfer_to = request.query_params.get('transfer_to')
            stock_type = (request.query_params.get('stock_type'))
            type = (request.query_params.get('type'))   

            if(type):
                type = int(request.query_params.get('type'))
            else:
                return Response({"message": "Type is a required field."}, status=status.HTTP_400_BAD_REQUEST)



            # if not transfer_from:
            #     return Response({"message": "Branch Details is a required field."}, status=status.HTTP_400_BAD_REQUEST)
            
            queryset = ErpStockTransfer.objects.all()

            if(transfer_from):
                queryset  = queryset.filter(transfer_from = transfer_from)

            if(transfer_to):            
                queryset  = queryset.filter(transfer_to = transfer_to)

            if(trans_code):         
                queryset  = queryset.filter(trans_code = trans_code,transfer_status__in = [0,1])
            else: 
                if(type==1):    
                    queryset  = queryset.filter(transfer_status = 0)
                elif(type==2):
                    queryset  = queryset.filter(transfer_status = 1)
        
            if(stock_type):         
                queryset  = queryset.filter(transfer_type = stock_type)

            # if(type==1):    
            #     queryset  = queryset.filter(transfer_status = 0)
            # elif(type==2):
            #     queryset  = queryset.filter(transfer_status = 1)


            queryset = queryset.select_related('transfer_from', 'transfer_to')

            response_data = []

            for stock_transfer in queryset:

                if(stock_transfer.transfer_type == 1):
            
                    transfer_list = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer).values('stock_transfer').annotate(
                        gross_wt=Sum('tag_id__tag_gwt'),
                        net_wt=Sum('tag_id__tag_nwt'),
                        less_wt=Sum('tag_id__tag_lwt'),
                        stn_wt=Sum('tag_id__tag_stn_wt'),
                        dia_wt=Sum('tag_id__tag_dia_wt')
                    ).values(
                        'stock_transfer',
                        'gross_wt', 
                        'net_wt',
                        'stn_wt',
                        'dia_wt',
                        'less_wt',
                    ).get()
                    details = []
                    if type == 2:
                        tag_details_query_set = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer , status=1)
                        for instance in tag_details_query_set:
                            details.append({
                                'pk_id': instance.id_tag_transfer,
                                'id_tag_transfer': instance.id_tag_transfer,
                                'tag_code': instance.tag_id.tag_code,
                                'old_tag_code': instance.tag_id.old_tag_code,
                                'product_name': instance.tag_id.tag_product_id.product_name,
                                'tag_gwt': instance.tag_id.tag_gwt,
                                'tag_nwt': instance.tag_id.tag_nwt,
                                'tag_lwt': instance.tag_id.tag_lwt,
                                'tag_stn_wt': instance.tag_id.tag_stn_wt,
                                'tag_dia_wt': instance.tag_id.tag_dia_wt,
                                'pcs': instance.tag_id.tag_pcs,
                            })

                    response_data.append({
                        'isChecked' : True,
                        'id_stock_transfer': stock_transfer.id_stock_transfer,
                        'transfer_from':stock_transfer.transfer_from.name,
                        'transfer_to':(stock_transfer.transfer_to.name if(stock_transfer.transfer_to) else ''),
                        'trans_code': stock_transfer.trans_code,
                        'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(stock_transfer.trans_to_type, ''),
                        'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(stock_transfer.transfer_type, ''),
                        'tag_code':'',
                        'transfer_status':stock_transfer.transfer_status,
                        'issued_to':stock_transfer.id_employee.firstname if stock_transfer.id_employee else stock_transfer.id_customer.firstname if stock_transfer.id_customer else '',
                        "details": details,
                        **transfer_list
                    })

                if(stock_transfer.transfer_type == 2):
            
                    transfer_list = ErpNonTagTransfer.objects.filter(stock_transfer=stock_transfer).values('stock_transfer').annotate(
                        total_gross_wt=Sum('gross_wt'),
                        total_net_wt=Sum('net_wt'),
                        total_less_wt=Sum('less_wt'),
                        total_stn_wt=Sum('stone_wt'),
                        total_dia_wt=Sum('dia_wt')
                    ).values(
                        'stock_transfer',
                        'total_gross_wt', 
                        'total_net_wt',
                        'total_less_wt',
                        'total_stn_wt',
                        'total_dia_wt',
                    ).get()

                    response_data.append({
                         'isChecked' : True,
                        'id_stock_transfer': stock_transfer.id_stock_transfer,
                        'transfer_from':stock_transfer.transfer_from.name,
                        'transfer_to':(stock_transfer.transfer_to.name if(stock_transfer.transfer_to) else ''),
                        'trans_code': stock_transfer.trans_code,
                        'transfer_status':stock_transfer.transfer_status,
                        'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(stock_transfer.trans_to_type, ''),
                        'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(stock_transfer.transfer_type, ''),
                        'gross_wt': transfer_list['total_gross_wt'],
                        'net_wt': transfer_list['total_net_wt'],  
                        'less_wt': transfer_list['total_less_wt'],  
                        'stn_wt': transfer_list['total_stn_wt'],
                        'dia_wt': transfer_list['total_dia_wt']
                    })

            if not response_data:
                return Response({"message": "No data found for the given Details."}, status=status.HTTP_200_OK)
            return Response({'list': response_data, 'message': "Data retrieved successfully"}, status=status.HTTP_200_OK)        
        except ErpStockTransfer.DoesNotExist:
            return Response({"message": "Stock Transfer Data Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                approval_details = request.data.get('approval_data')
                filter_data = request.data.get('filter_data')
                type = int(request.data.get('type'))
                
                filter_trans_status = 0
                if not approval_details:
                    return Response({"error": "Approval Detalis is missing."}, status=status.HTTP_400_BAD_REQUEST)

                if(type==3):
                    approval_data.update({
                        "transfer_status":3,
                        "reject_reason":approval_data['reject_reason'],
                        "rejected_on":approval_datetime,
                        "rejected_by": request.user.id,
                        "updated_by": request.user.pk, 
                        "updated_on":datetime.now(tz=timezone.utc)
                    })
                    for approval_data in approval_details:
                        transfer_instance= ErpStockTransfer.objects.filter(pk=approval_data['id_stock_transfer'],transfer_status = filter_trans_status).get()
                        if transfer_serializer.is_valid(raise_exception=True):
                            transfer_serializer.save()

                if(type==1):
                    for approval_data in approval_details:
                        transfer_instance= ErpStockTransfer.objects.filter(pk=approval_data['id_stock_transfer'],transfer_status = filter_trans_status).get()  
                        branch_date = BranchEntryDate()
                        approval_date = branch_date.get_entry_date(transfer_instance.transfer_from)
                        approval_datetime = datetime.combine(approval_date, datetime.now(tz=timezone.utc).time())
                        approval_data.update({
                            "transfer_status":1,
                            "approved_date":approval_datetime,
                            "approved_by": request.user.id,
                            "updated_by": request.user.pk, 
                            "updated_on":datetime.now(tz=timezone.utc)
                        })
                        transfer_serializer = ErpStockTransferSerializer(transfer_instance,data = approval_data, partial=True)
                        if transfer_serializer.is_valid(raise_exception=True):
                            transfer_serializer.save()
                            if(filter_data['stock_type'] == 1):      
                                self.approve_tag_transfer(transfer_serializer.data,approval_data['id_stock_transfer'],approval_data,request,approval_date,approval_datetime)

                    return Response({"message":"Stock Transfer Approved Successfully."}, status=status.HTTP_201_CREATED)
                
                if(type==2):
                    stock_downloded = []
                    tagged_items = []
                    response_status = ""
                    message = ""
                    for approval_data in approval_details:
                        transfer_instance = ErpStockTransfer.objects.filter(pk=approval_data['id_stock_transfer'],transfer_status = 1).get()  
                        transfer_serializer = ErpStockTransferSerializer(transfer_instance)
                        branch_date = BranchEntryDate()
                        approval_date = branch_date.get_entry_date(transfer_instance.transfer_from)
                        approval_datetime = datetime.combine(approval_date, datetime.now(tz=timezone.utc).time())
                        download_datetime = datetime.now(tz=timezone.utc)
                        if transfer_instance.transfer_to!=None:
                            received_branch_date = branch_date.get_entry_date(transfer_instance.transfer_to)
                            download_datetime = datetime.combine(received_branch_date, datetime.now(tz=timezone.utc).time())
                        if(transfer_instance.transfer_type == 1):
                            stock_download_type = int(RetailSettings.objects.get(name='stock_download_type').value)
                            response_data = self.download_tagged_items(transfer_serializer.data,approval_data['id_stock_transfer'],approval_data,request,approval_date,approval_datetime , download_datetime)
                            
                            stock_downloded = response_data['stock_downloded']
                            tagged_items = response_data['data']
                            response_status = response_data['status']
                            message = response_data['message']
                    if response_status:
                        return Response({"status" : response_status,"message":message,"stock_downloded" : stock_downloded, "data" : tagged_items}, status=status.HTTP_201_CREATED)
                    else:
                        return Response({"status" : False,"message": message }, status=status.HTTP_400_BAD_REQUEST)
                # if(type==2):
                #         filter_trans_status = 1
                # stock_download_type = int(RetailSettings.objects.get(name='stock_download_type').value)

                
                # for approval_data in approval_details:
                #     transfer_instance= ErpStockTransfer.objects.filter(pk=approval_data['id_stock_transfer'],transfer_status = filter_trans_status).get() 
                #     if(type==1 and int(transfer_instance.transfer_type) == 2 ):
                #         request.non_tag_stock = get_non_tag_stock(transfer_instance.transfer_from)  
                #     branch_date = BranchEntryDate()
                #     approval_date = branch_date.get_entry_date(transfer_instance.transfer_from)
                #     approval_datetime = datetime.combine(approval_date, datetime.now(tz=timezone.utc).time())
                    
                   
                #     # Stock Download
                #     if(type==2):
                #         if(stock_download_type == 1 or stock_download_type == 3):
                #             print("stock_download_type :1 or 3")
                #             approval_data.update({"stock_download_type":stock_download_type,"transfer_status":2,"downloaded_date":approval_datetime,"downloaded_by": request.user.id,"updated_by": request.user.pk, "updated_on":datetime.now(tz=timezone.utc)})
                #         else: 
                #             print("stock_download_type :2")
                #             approval_data.update({"stock_download_type":stock_download_type,"updated_by": request.user.pk, "updated_on":datetime.now(tz=timezone.utc)})

                #     if(type==3):
                #         approval_data.update({"transfer_status":3,"reject_reason":approval_data['reject_reason'],"rejected_on":approval_datetime,"rejected_by": request.user.id,"updated_by": request.user.pk, "updated_on":datetime.now(tz=timezone.utc)})
                    
                #     print(approval_data)
                #     transfer_serializer = ErpStockTransferSerializer(transfer_instance,data = approval_data, partial=True)
                #     if transfer_serializer.is_valid(raise_exception=True):
                #         transfer_serializer.save()
                #         stock_transfer = transfer_serializer.data['id_stock_transfer']
                #         if(type==2 and stock_download_type == 2 ):
                #             print("stock_download_type :2")
                #             approval_data.update({"stock_download_type":stock_download_type,"transfer_status":2})

                #         returned = self.update_stock_details_status(transfer_serializer.data,stock_transfer,approval_data,request,approval_date,approval_datetime)

                #         if(returned):
                #             return returned
                #     else:
                #         return Response({"error":ErpStockTransferSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except ErpStockTransfer.DoesNotExist:
            return Response({"status" : False,"message": "Stock Transfer not found"}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"status" : False,"message": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"status" : False,"message": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"status" : False,"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Given tag code and status does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except ErpTagTransfer.DoesNotExist:
            return Response({"message": "Given tag ID and status does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
    def approve_tag_transfer(self,transfer_data,stock_transfer,approval_data,request,approved_date,approval_datetime):

        tag_details = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer)
        tag_details = ErpTagTransferSerializer(tag_details,many=True).data
        for tag_detail in tag_details:
            reduce_in_stock = True
            id_stock_status = 4
            if int(transfer_data['trans_to_type'])==2:
                if transfer_data['stock_issue_type']:
                    stock_serializer = StockIssueType.objects.get(pk=transfer_data['stock_issue_type'])
                    if stock_serializer.reduce_in_stock == False:
                        reduce_in_stock = False
                        id_stock_status = 8
                    else:
                        id_stock_status = 4
            tag_instance = ErpTagging.objects.get(pk=tag_detail['tag_id'],tag_status= 1)
            if int(transfer_data['trans_to_type'])==1: 
                tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":4 }, partial=True)
            else:
                if reduce_in_stock:
                    tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":4 }, partial=True)
                else:
                    tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":8 }, partial=True)

            tag_serializer.is_valid(raise_exception=True)
            tag_serializer.save()

            if reduce_in_stock:
                log_details={
                    'from_branch': transfer_data['transfer_from'],
                    'to_branch': None,
                    'date': approved_date,
                    'id_stock_status': id_stock_status,
                    'tag_id': tag_detail['tag_id'],
                    'transaction_type': 3,
                    'ref_id': tag_detail['id_tag_transfer'],
                    "created_by": request.user.id
                }
                log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                log_tag_serializer.is_valid(raise_exception=True)
                log_tag_serializer.save()


    def download_tagged_items(self,transfer_data,stock_transfer,approval_data,request,approved_date,approval_datetime,download_datetime):
        stock_download_type = int(RetailSettings.objects.get(name='stock_download_type').value)
        if stock_download_type == 1:
            try:
                transfer_instance = ErpStockTransfer.objects.filter(pk=stock_transfer , transfer_status = 1).get()  
                approval_data.update({
                    "stock_download_type":stock_download_type,
                    "transfer_status":2,
                    "downloaded_date":download_datetime,
                    "downloaded_by": request.user.id,
                    "updated_by": request.user.pk, 
                    "updated_on":datetime.now(tz=timezone.utc)
                })
                transfer_serializer = ErpStockTransferSerializer(transfer_instance,data = approval_data, partial=True)
                if transfer_serializer.is_valid(raise_exception=True):
                    transfer_serializer.save()
                    tag_details = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer)
                    for tag_detail in tag_details:
                        tag_transfer_data = {
                            "downloaded_date": approval_data['downloaded_date'],
                            "downloaded_by": request.user.id,
                            "status": 2
                        }
                        tag_transfer_serializer = ErpTagTransferSerializer(tag_detail, data=tag_transfer_data, partial=True)
                        tag_transfer_serializer.is_valid(raise_exception=True)
                        tag_transfer_serializer.save()
                        update_in_stock = True
                        tag_status = 4
                        if int(transfer_data['trans_to_type'])==2 and transfer_data['stock_issue_type']:
                            stock_serializer = StockIssueType.objects.get(pk=transfer_data['stock_issue_type'])
                            if stock_serializer.reduce_in_stock == False:
                                update_in_stock = False
                            tag_status = 8

                        tag_instance = ErpTagging.objects.get(pk=tag_transfer_serializer.data['tag_id'],tag_status= tag_status)
                        tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":1,"tag_current_branch" : transfer_data['transfer_to']}, partial=True)
                        tag_serializer.is_valid(raise_exception=True)
                        tag_serializer.save()

                                
                        if update_in_stock:
                            log_details={
                                'from_branch': None  if tag_status == 8 else transfer_data['transfer_from'],
                                'to_branch': transfer_data['transfer_from']  if tag_status == 8 else transfer_data['transfer_to'],
                                'date': download_datetime,
                                'id_stock_status': 1,
                                'tag_id': tag_transfer_serializer.data['tag_id'],
                                'transaction_type': 3,
                                'ref_id': tag_transfer_serializer.data['id_tag_transfer'],
                                "created_by": request.user.id
                            }
                            log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                            log_tag_serializer.is_valid(raise_exception=True)
                            log_tag_serializer.save()
            except Exception as e:
                return Response({"message": f"Error in downloading stock: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        elif stock_download_type == 2 :
            try:
                update_in_stock = True
                tag_status = 4
                if int(transfer_data['trans_to_type'])==2 and transfer_data['stock_issue_type']:
                    stock_serializer = StockIssueType.objects.get(pk=transfer_data['stock_issue_type'])
                    if stock_serializer.reduce_in_stock == False:
                        update_in_stock = False

                    tag_status = 8
                if approval_data['tag_code']!='':
                    tag_instance = ErpTagging.objects.filter(tag_code = approval_data['tag_code'],tag_status = tag_status).get()
                elif approval_data['old_tag_code']!='':
                    tag_instance = ErpTagging.objects.filter(old_tag_code = approval_data['old_tag_code'],tag_status = tag_status).get()

                tag_details = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer,tag_id=tag_instance.pk,status = 1).get()
                tag_transfer_data = {
                    "downloaded_date": download_datetime,
                    "downloaded_by": request.user.id,
                    "status": 2
                }
                tag_transfer_serializer = ErpTagTransferSerializer(tag_details, data=tag_transfer_data, partial=True)
                tag_transfer_serializer.is_valid(raise_exception=True)
                tag_transfer_serializer.save()
                tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":1,"tag_current_branch" : transfer_data['transfer_to']}, partial=True)
                tag_serializer.is_valid(raise_exception=True)
                tag_serializer.save()
                if update_in_stock:
                    log_details={
                        'from_branch': None  if tag_status == 8 else transfer_data['transfer_from'],
                        'to_branch': transfer_data['transfer_from']  if tag_status == 8 else transfer_data['transfer_to'],
                        'date': download_datetime,
                        'id_stock_status': 1,
                        'tag_id': tag_serializer.data['tag_id'],
                        'transaction_type': 3,
                        'ref_id': tag_transfer_serializer.data['id_tag_transfer'],
                        "created_by": request.user.id
                    }
                    log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                    log_tag_serializer.is_valid(raise_exception=True)
                    log_tag_serializer.save()

                return_status = self.update_stock_transfer(stock_transfer,download_datetime,request)

                if (return_status):
                    return {"status" : True , "message":"Tag Downloaded Successfully" , "data" : tag_serializer.data,"stock_downloded":return_status }

                return {"status" : True, "message":"Tag Downloaded Successfully.","data" : tag_serializer.data,"stock_downloded":return_status }
            except ErpTagging.DoesNotExist:
                return {"status" : False, "message": "Given tag code and status does not exist.","data" : [] , "stock_downloded" : []}
            except ErpTagTransfer.DoesNotExist:
                return {"status" : False, "message": "Given tag ID and status does not exist." , "data" : [] , "stock_downloded" : []}

        elif stock_download_type == 3 :
            try:
                tag_details = request.data.get('downLoaded_stock', [])
                for tag_detail in tag_details:
                    instance = ErpTagTransfer.objects.get(id_tag_transfer=tag_detail['id_tag_transfer'])
                    tag_transfer_data = {
                        "downloaded_date": download_datetime,
                        "downloaded_by": request.user.id,
                        "status": 2
                    }

                    tag_transfer_serializer = ErpTagTransferSerializer(instance, data=tag_transfer_data, partial=True)
                    tag_transfer_serializer.is_valid(raise_exception=True)
                    tag_transfer_serializer.save()
                    update_in_stock = True
                    tag_status = 4
                    tag_current_branch = transfer_data['transfer_to']
                    if int(transfer_data['trans_to_type'])==2 and transfer_data['stock_issue_type']:
                        stock_serializer = StockIssueType.objects.get(pk=transfer_data['stock_issue_type'])
                        tag_current_branch = transfer_data['transfer_from']
                        if stock_serializer.reduce_in_stock == False:
                            update_in_stock = False
                        tag_status = 8

                    tag_instance = ErpTagging.objects.get(pk=tag_transfer_serializer.data['tag_id'],tag_status= tag_status)
                    tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":1,"tag_current_branch" : tag_current_branch}, partial=True)
                    tag_serializer.is_valid(raise_exception=True)
                    tag_serializer.save()

                            
                    if update_in_stock:
                        log_details={
                            'from_branch': None  if tag_status == 8 else transfer_data['transfer_from'],
                            'to_branch': transfer_data['transfer_from']  if tag_status == 8 else transfer_data['transfer_to'],
                            'date': download_datetime,
                            'id_stock_status': 1,
                            'tag_id': tag_transfer_serializer.data['tag_id'],
                            'transaction_type': 3,
                            'ref_id': tag_transfer_serializer.data['id_tag_transfer'],
                            "created_by": request.user.id
                        }
                        log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                        log_tag_serializer.is_valid(raise_exception=True)
                        log_tag_serializer.save()

                    return_status = self.update_stock_transfer(stock_transfer,download_datetime,request)

                return {"status" : True , "message":"Tag Downloaded Successfully" , "data" : [],"stock_downloded":[] }
            except ErpTagging.DoesNotExist:
                return {"status" : False, "message": "Given tag code and status does not exist.","data" : [] , "stock_downloded" : []}
            except ErpTagTransfer.DoesNotExist:
                return {"status" : False, "message": "Given tag ID and status does not exist." , "data" : [] , "stock_downloded" : []}
            

    def update_stock_transfer(self,stock_transfer,approval_datetime,request):

        stock = ErpTagTransfer.objects.filter(stock_transfer =stock_transfer)
        total_stock = stock.count()
        downloded_stock =stock.filter(status = 2).count()
        
        if total_stock == downloded_stock:
            transfer_instance= ErpStockTransfer.objects.get(pk=stock_transfer)
            approval_data = {
                "transfer_status":2,
                "downloaded_date":approval_datetime,
                "downloaded_by": request.user.id,
                "updated_by": request.user.pk, 
                "updated_on":datetime.now(tz=timezone.utc)
            }
            transfer_serializer = ErpStockTransferSerializer(transfer_instance,data = approval_data, partial=True)
            transfer_serializer.is_valid(raise_exception=True)
            transfer_serializer.save()
            return True
        return False
    
    def update_stock_details_status(self,transfer_data,stock_transfer,approval_data,request,approved_date,approval_datetime):
            if(approval_data['transfer_status']==1):
                if transfer_data['transfer_type'] == 1:
                   tag_details = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer)
                   tag_details = ErpTagTransferSerializer(tag_details,many=True).data

                   for tag_detail in tag_details:
                        tag_instance = ErpTagging.objects.get(pk=tag_detail['tag_id'],tag_status= 1)
                        if int(transfer_data['trans_to_type'])==1: 
                            tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":4 }, partial=True)
                        else:
                            tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":8 }, partial=True)
                        tag_serializer.is_valid(raise_exception=True)
                        tag_serializer.save()
                        reduce_in_stock = True
                        id_stock_status = 4
                        if int(transfer_data['trans_to_type'])==2:
                            if transfer_data['stock_issue_type']:
                                stock_serializer = StockIssueType.objects.get(pk=transfer_data['stock_issue_type'])
                                if stock_serializer.reduce_in_stock == False:
                                    reduce_in_stock = False
                                else:
                                    id_stock_status = 8
                        if reduce_in_stock:
                            log_details={
                                'from_branch': transfer_data['transfer_from'],
                                'to_branch': None,
                                'date': approved_date,
                                'id_stock_status': id_stock_status,
                                'tag_id': tag_detail['tag_id'],
                                'transaction_type': 3,
                                'ref_id': tag_detail['id_tag_transfer'],
                                "created_by": request.user.id
                            }
                            log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                            log_tag_serializer.is_valid(raise_exception=True)
                            log_tag_serializer.save()

                if transfer_data['transfer_type'] == 2:
                   
                   non_tag_details = ErpNonTagTransfer.objects.filter(stock_transfer=stock_transfer)
                   non_tag_details = ErpNonTagTransferSerializer(non_tag_details,many=True).data
                   for non_tag in non_tag_details:
                        statuss = check_non_stock_exist(non_tag,request)
                        log_details={
                            **non_tag,
                            'from_branch': transfer_data['transfer_from'],
                            'to_branch': transfer_data['transfer_to'],
                            'date': approved_date,
                            'id_stock_status': 4,
                            'transaction_type': 3,
                            'ref_id': non_tag['id_non_tag_transfer'],
                            "created_by": request.user.id
                        }
                        non_tag_serializer = ErpLotInwardNonTagSerializer(data=log_details)
                        non_tag_serializer.is_valid(raise_exception=True)
                        non_tag_serializer.save()
                        stone_details = ErpNonTagStoneTransfer.objects.filter(id_non_tag_transfer=non_tag['id_non_tag_transfer'])
                        print(stone_details)
                        stone_details = ErpNonTagStoneTransferSerializer(stone_details,many=True).data
                        insert_other_details(stone_details,ErpLotInwardNonTagStoneSerializer,{ "id_non_tag_log": non_tag_serializer.data['id_non_tag_log']})
                
            if(approval_data['transfer_status']==2):
                print("stock_download_type :2")
                if transfer_data['transfer_type'] == 1:
                    stock_download_type = int(approval_data['stock_download_type'])
                    if stock_download_type == 1 :
                        tag_details = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer)

                        for tag_detail in tag_details:
                            tag_transfer_data = {
                                "downloaded_date": approval_data['downloaded_date'],
                                "downloaded_by": request.user.id,
                                "status": 2
                            }
                            tag_transfer_serializer = ErpTagTransferSerializer(tag_detail, data=tag_transfer_data, partial=True)
                            tag_transfer_serializer.is_valid(raise_exception=True)
                            tag_transfer_serializer.save()
                            update_in_stock = True
                            tag_status = 4
                            if int(transfer_data['trans_to_type'])==2 and transfer_data['stock_issue_type']:
                                stock_serializer = StockIssueType.objects.get(pk=transfer_data['stock_issue_type'])
                                if stock_serializer.reduce_in_stock == False:
                                    update_in_stock = False
                                tag_status = 8

                            tag_instance = ErpTagging.objects.get(pk=tag_transfer_serializer.data['tag_id'],tag_status= tag_status)
                            tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":1,"tag_current_branch" : transfer_data['transfer_to']}, partial=True)
                            tag_serializer.is_valid(raise_exception=True)
                            tag_serializer.save()

                                    
                            if update_in_stock:
                                log_details={
                                    'from_branch': transfer_data['transfer_from'],
                                    'to_branch': transfer_data['transfer_to'],
                                    'date': approved_date,
                                    'id_stock_status': 1,
                                    'tag_id': tag_transfer_serializer.data['tag_id'],
                                    'transaction_type': 3,
                                    'ref_id': tag_transfer_serializer.data['id_tag_transfer'],
                                    "created_by": request.user.id
                                }
                                log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                                log_tag_serializer.is_valid(raise_exception=True)
                                log_tag_serializer.save()
                    elif stock_download_type == 3 :
                        tag_details = request.data.get('downLoaded_stock', [])
                        for tag_detail in tag_details:
                            
                            instance = ErpTagTransfer.objects.get(id_tag_transfer=tag_detail['id_tag_transfer'])
                            tag_transfer_data = {
                                "downloaded_date": approval_data['downloaded_date'],
                                "downloaded_by": request.user.id,
                                "status": 2
                            }

                            tag_transfer_serializer = ErpTagTransferSerializer(instance, data=tag_transfer_data, partial=True)
                            tag_transfer_serializer.is_valid(raise_exception=True)
                            tag_transfer_serializer.save()
                            update_in_stock = True
                            tag_status = 4
                            tag_current_branch = transfer_data['transfer_to']
                            if int(transfer_data['trans_to_type'])==2 and transfer_data['stock_issue_type']:
                                stock_serializer = StockIssueType.objects.get(pk=transfer_data['stock_issue_type'])
                                tag_current_branch = transfer_data['transfer_from']
                                if stock_serializer.reduce_in_stock == False:
                                    update_in_stock = False
                                tag_status = 8

                            tag_instance = ErpTagging.objects.get(pk=tag_transfer_serializer.data['tag_id'],tag_status= tag_status)
                            tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":1,"tag_current_branch" : tag_current_branch}, partial=True)
                            tag_serializer.is_valid(raise_exception=True)
                            tag_serializer.save()

                                    
                            if update_in_stock:
                                log_details={
                                    'from_branch': None  if tag_status == 8 else transfer_data['transfer_from'],
                                    'to_branch': transfer_data['transfer_from']  if tag_status == 8 else transfer_data['transfer_to'],
                                    'date': approved_date,
                                    'id_stock_status': 1,
                                    'tag_id': tag_transfer_serializer.data['tag_id'],
                                    'transaction_type': 3,
                                    'ref_id': tag_transfer_serializer.data['id_tag_transfer'],
                                    "created_by": request.user.id
                                }
                                log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                                log_tag_serializer.is_valid(raise_exception=True)
                                log_tag_serializer.save()
                    elif stock_download_type == 2 :
                        try:
                            print("stock_download_type :267345")
                            update_in_stock = True
                            tag_status = 4
                            if int(transfer_data['trans_to_type'])==2 and transfer_data['stock_issue_type']:
                                stock_serializer = StockIssueType.objects.get(pk=transfer_data['stock_issue_type'])
                                if stock_serializer.reduce_in_stock == False:
                                    update_in_stock = False

                                tag_status = 8
                            tag_instance = ErpTagging.objects.filter(tag_code=approval_data['tag_code'],tag_status= tag_status).get()
                            print("stock_download_type :2674")

                            tag_details = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer,tag_id=tag_instance.pk,status = 1).get()
                            tag_transfer_data = {
                                "downloaded_date": approval_datetime,
                                "downloaded_by": request.user.id,
                                "status": 2
                            }
                            tag_transfer_serializer = ErpTagTransferSerializer(tag_details, data=tag_transfer_data, partial=True)
                            tag_transfer_serializer.is_valid(raise_exception=True)
                            tag_transfer_serializer.save()
                            tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"tag_status":1,"tag_current_branch" : transfer_data['transfer_to']}, partial=True)
                            tag_serializer.is_valid(raise_exception=True)
                            tag_serializer.save()

                            if update_in_stock:

                                log_details={
                                    'from_branch': transfer_data['transfer_from'],
                                    'to_branch': transfer_data['transfer_to'],
                                    'date': approved_date,
                                    'id_stock_status': 1,
                                    'tag_id': tag_serializer.data['tag_id'],
                                    'transaction_type': 3,
                                    'ref_id': tag_transfer_serializer.data['id_tag_transfer'],
                                    "created_by": request.user.id
                                }
                                log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                                log_tag_serializer.is_valid(raise_exception=True)
                                log_tag_serializer.save()

                            return_status = self.update_stock_transfer(stock_transfer,approval_datetime,request)

                            print("stock_download_type :2674")


                            if (return_status):
                                return Response({"message":"Stock Downloaded Successfully.","data" : tag_serializer.data,"stock_downloded":return_status }, status=status.HTTP_201_CREATED)

                            return Response({"message":"Tag Downloaded Successfully.","data" : tag_serializer.data,"stock_downloded":return_status }, status=status.HTTP_201_CREATED)
                        except ErpTagging.DoesNotExist:
                            return Response({"message": "Given tag code and status does not exist."}, status=status.HTTP_404_NOT_FOUND)
                        except ErpTagTransfer.DoesNotExist:
                            return Response({"message": "Given tag ID and status does not exist."}, status=status.HTTP_404_NOT_FOUND)

                if transfer_data['transfer_type'] == 2:
                   non_tag_details = ErpNonTagTransfer.objects.filter(stock_transfer=stock_transfer)
                   non_tag_details = ErpNonTagTransferSerializer(non_tag_details,many=True).data
                   for non_tag in non_tag_details:
                        log_details={
                            **non_tag,
                            'from_branch': transfer_data['transfer_from'],
                            'to_branch': transfer_data['transfer_to'],
                            'date': approved_date,
                            'id_stock_status': 1,
                            'transaction_type': 3,
                            'ref_id': non_tag['id_non_tag_transfer'],
                            "created_by": request.user.id
                        }
                        non_tag_serializer = ErpLotInwardNonTagSerializer(data=log_details)
                        non_tag_serializer.is_valid(raise_exception=True)
                        non_tag_serializer.save()
                        stone_details = ErpNonTagStoneTransfer.objects.filter(id_non_tag_transfer=non_tag['id_non_tag_transfer'])
                        print(stone_details)
                        stone_details = ErpNonTagStoneTransferSerializer(stone_details,many=True).data
                        insert_other_details(stone_details,ErpLotInwardNonTagStoneSerializer,{ "id_non_tag_log": non_tag_serializer.data['id_non_tag_log']})


class ErpBranchTransferListAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpStockTransfer.objects.all()
    serializer_class = ErpStockTransferSerializer

    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        transfer_from = request.data.get('transfer_from')
        transfer_to = request.data.get('transfer_to')

        queryset = ErpStockTransfer.objects.all()

        if(transfer_from):
            queryset  = queryset.filter(transfer_from__in = transfer_from)

        if(transfer_to):            
            queryset  = queryset.filter(transfer_to = transfer_to)

        if from_date and to_date:
            queryset = queryset.filter(trans_date__range=[from_date, to_date])

        queryset = queryset.select_related('transfer_from', 'transfer_to').order_by('id_stock_transfer')

        response_data = []

        for stock_transfer in queryset:

            if(stock_transfer.transfer_type == 1):
        
                transfer_list = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer).values('stock_transfer').annotate(
                    pcs=Sum('tag_id__tag_pcs'),
                    gross_wt=Sum('tag_id__tag_gwt'),
                    net_wt=Sum('tag_id__tag_nwt'),
                    less_wt=Sum('tag_id__tag_lwt'),
                    stn_wt=Sum('tag_id__tag_stn_wt'),
                    dia_wt=Sum('tag_id__tag_dia_wt')
                ).values(
                    'stock_transfer',
                    'pcs',
                    'gross_wt', 
                    'net_wt',
                    'stn_wt',
                    'dia_wt',
                    'less_wt',
                ).get()

                response_data.append({
                    'pk_id': stock_transfer.id_stock_transfer,
                    'trans_date': format_date(stock_transfer.trans_date),
                    'transfer_from':stock_transfer.transfer_from.name,
                    'issued_to' : (
                        stock_transfer.id_employee.firstname if stock_transfer.stock_issue_to == 1
                        else stock_transfer.id_customer.firstname if stock_transfer.stock_issue_to == 2
                        else stock_transfer.supplier.supplier_name if stock_transfer.stock_issue_to == 3
                        else ''
                    ),
                    'transfer_to':(stock_transfer.transfer_to.name if(stock_transfer.transfer_to) else ''),
                    'status': dict(ErpStockTransfer.TRANSFER_STATUS_CHOICES).get(stock_transfer.transfer_status, ''),
                    'trans_code': stock_transfer.trans_code,
                    'trans_to_type_name': dict(ErpStockTransfer.ISSUE_TO).get(stock_transfer.stock_issue_to, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(stock_transfer.transfer_type, ''),
                    'tag_code':'',
                    **transfer_list,
                    'status_color':get_status_color(stock_transfer.transfer_status),
                    'gross_wt': format_wt(transfer_list['gross_wt']),
                    'is_cancelable': True if stock_transfer.transfer_status == 0 else False,

                })

            if(stock_transfer.transfer_type == 2):
        
                transfer_list = ErpNonTagTransfer.objects.filter(stock_transfer=stock_transfer).values('stock_transfer').annotate(
                    total_gross_wt=Sum('gross_wt'),
                    total_net_wt=Sum('net_wt'),
                    total_less_wt=Sum('less_wt'),
                    total_stn_wt=Sum('stone_wt'),
                    total_dia_wt=Sum('dia_wt'),
                    pcs=Sum('pieces'),
                ).values(
                    'stock_transfer',
                    'pcs',
                    'total_gross_wt', 
                    'total_net_wt',
                    'total_less_wt',
                    'total_stn_wt',
                    'total_dia_wt',
                ).get()

                response_data.append({
                    'pk_id': stock_transfer.id_stock_transfer,
                    'transfer_from':stock_transfer.transfer_from.name,
                    'transfer_to':(stock_transfer.transfer_to.name if(stock_transfer.transfer_to) else ''),
                    'trans_code': stock_transfer.trans_code,
                    'trans_date': format_date(stock_transfer.trans_date),
                    'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(stock_transfer.trans_to_type, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(stock_transfer.transfer_type, ''),
                    'status': dict(ErpStockTransfer.TRANSFER_STATUS_CHOICES).get(stock_transfer.transfer_status, ''),
                    'gross_wt': format_wt(transfer_list['total_gross_wt']),
                    'net_wt': transfer_list['total_net_wt'],  
                    'less_wt': transfer_list['total_less_wt'],  
                    'stn_wt': transfer_list['total_stn_wt'],
                    'dia_wt': transfer_list['total_dia_wt'],
                    'pcs': transfer_list['pcs'],
                    'tag_code':'',
                    'status_color':get_status_color(stock_transfer.transfer_status),
                    'is_cancelable': True if stock_transfer.transfer_status == 0 else False,
                })


        paginator, page = pagination.paginate_queryset(response_data, request,None,TRANCFER_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,TRANCFER_COLUMN_LIST,request.data.get('path_name',''))
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
        return pagination.paginated_response(response_data,context) 
    

class ErpBranchTransferCancelAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpStockTransfer.objects.all()
    serializer_class = ErpStockTransferSerializer

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                cancel_reason = request.data.get('cancel_reason')
                id_stock_transfer = request.data.get('pk_id')
                if not cancel_reason:
                    return Response({"error": "Approval Detalis is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not id_stock_transfer:
                    return Response({"error": "id_stock_transfer is missing."}, status=status.HTTP_400_BAD_REQUEST)
                transfer_instance= ErpStockTransfer.objects.filter(pk=id_stock_transfer,transfer_status = 0).get()   
                branch_date = BranchEntryDate()
                approval_date = branch_date.get_entry_date(transfer_instance.transfer_from)
                approval_datetime = datetime.combine(approval_date, datetime.now(tz=timezone.utc).time())
                approval_data = {"transfer_status":3,"reject_reason":cancel_reason,"rejected_on":approval_datetime,"rejected_by": request.user.id,"updated_by": request.user.pk, "updated_on":datetime.now(tz=timezone.utc)}
                transfer_serializer = ErpStockTransferSerializer(transfer_instance,data = approval_data, partial=True)
                if transfer_serializer.is_valid(raise_exception=True):
                    transfer_serializer.save()
                else:
                    return Response({"error":ErpStockTransferSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                return Response({"message":"Stock Transfer Cancel Successfully."}, status=status.HTTP_201_CREATED)

        except ErpStockTransfer.DoesNotExist:
            return Response({"message": "Stock Transfer not found"}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"message": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"message": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
    

def check_non_stock_exist(non_tag,request):
        stocks=request.non_tag_stock
        current_item_stock = [item for item in stocks if ( item['id_product_id'] == non_tag['id_product'] and item['id_design_id'] == non_tag['id_design'] and item['id_sub_design_id'] == non_tag['id_sub_design'])]

        if current_item_stock:
            if( float(current_item_stock[0]['gross_wt']) >= float(non_tag['gross_wt']) and float(current_item_stock[0]['pieces']) >= float(non_tag['pieces']) ):

                return True
            
        raise ValueError("Invalid Non Tag Stock Transtaction Check The Stock")


class ErpOldMetalDetailsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):

        try :
            branch = request.data.get('branch')
            metal = request.data.get('metal')
            from_date = request.data.get('from_date')
            to_date = (request.data.get('to_date'))

            if(not (from_date and to_date and branch)):

                return Response({"message": "From date, To date, Branch  is a required field."}, status=status.HTTP_400_BAD_REQUEST)

            
            queryset = ErpInvoiceOldMetalDetails.objects.filter(purchase_status = 1,invoice_bill_id__id_branch = branch,invoice_bill_id__invoice_date__range=[from_date, to_date])

            if metal:
                queryset  = queryset.filter(id_product__id_metal = metal)

            response_data = []

            for old_metal in queryset:
                obj = old_metal.invoice_bill_id
                inv_data = {
                    'invoice_type': obj.invoice_type,
                    'id_branch': obj.id_branch.id_branch,
                    'fin_year': obj.fin_year.fin_id,
                    'metal': obj.metal.id_metal if obj.metal else None,
                    'sales_invoice_no': obj.sales_invoice_no,
                    'purchase_invoice_no': obj.purchase_invoice_no,
                    'return_invoice_no': obj.return_invoice_no
                }
                invoice_info = get_invoice_no(inv_data)
                response_data.append({
                    'invoice_old_metal_item_id': old_metal.invoice_old_metal_item_id,
                    'branch_name':old_metal.invoice_bill_id.id_branch.name,
                    'invoice_no': invoice_info['invoice_no'],
                    'item_type': old_metal.item_type.name if old_metal.item_type else None,
                    'product_name':old_metal.id_product.product_name,
                    'gross_wt': old_metal.gross_wt,
                    'net_wt': old_metal.net_wt,
                    'less_wt': old_metal.less_wt,  
                    'stn_wt': old_metal.stone_wt,
                    'dia_wt': old_metal.dia_wt,
                    'pieces': old_metal.pieces,

                })

            if not response_data:
                return Response({"message": "No data found for the given Details."}, status=status.HTTP_200_OK)
            return Response({'list': response_data, 'message': "Data retrieved successfully"}, status=status.HTTP_200_OK)        
        except ErpStockTransfer.DoesNotExist:
            return Response({"message": "Stock Transfer Data Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        

class ErpStockIssuedDetailsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpStockTransfer.objects.all()
    serializer_class = ErpStockTransferSerializer
    
    def post(self, request, *args, **kwargs):

        try :
            trans_code = request.data.get('trans_code')
            transfer_from = request.data.get('transfer_from')
            if not trans_code or not transfer_from:
                return Response({"message": "Missing required fields: trans_code, transfer_from"}, status=status.HTTP_400_BAD_REQUEST)
            queryset = ErpStockTransfer.objects.filter(stock_issue_to = 2,trans_to_type= 2,trans_code = trans_code,transfer_status__in = [1,2],transfer_from = transfer_from).get()
            response_data = []
            details = []
            if(queryset.transfer_type == 1):
                tag_details_query_set = ErpTagTransfer.objects.filter(stock_transfer=queryset,status=1,tag_id__tag_status=8)
                for instance in tag_details_query_set:
                    tag_details = ErpTagging.objects.get(tag_id=instance.tag_id.pk)
                    tag_details = ErpTaggingSerializer(tag_details,context = {"weight_range":True}).data
                    details.append({
                        **tag_details,
                        'id_tag_transfer': instance.id_tag_transfer,
                        'id_stock_transfer': queryset.id_stock_transfer,
                        'item_type': 0,
                        'metal': instance.tag_id.tag_product_id.id_metal.pk,
                    })
                response_data = {
                    'id_stock_transfer': queryset.id_stock_transfer,
                    'transfer_from':queryset.transfer_from.name,
                    'transfer_to':(queryset.transfer_to.name if(queryset.transfer_to) else ''),
                    'trans_code': queryset.trans_code,
                    'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(queryset.trans_to_type, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(queryset.transfer_type, ''),
                    'transfer_status':queryset.transfer_status,
                    'issued_to':queryset.id_employee.firstname if queryset.stock_issue_to == 1 else queryset.id_customer.firstname if queryset.stock_issue_to == 2 else  queryset.supplier.supplier_name,
                    'id_customer': queryset.id_customer.pk,
                    'customer_name': queryset.id_customer.firstname if queryset.id_customer else '',
                    'customer_mobile': queryset.id_customer.mobile if queryset.id_customer else '',
                    "details": details,
                }

            if not details:
                return Response({"message": "No data found for the given Details."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'list': response_data, 'message': "Data retrieved successfully"}, status=status.HTTP_200_OK)        
        except ErpStockTransfer.DoesNotExist:
            return Response({"message": "Stock Transfer Data Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)