from django.shortcuts import render
from django.http import HttpResponse, request, Http404,FileResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import datetime, timedelta, date
from django.db import transaction , IntegrityError,DatabaseError,OperationalError
from django.db.models import  Sum, F, ExpressionWrapper, DecimalField, Q, ProtectedError,When, Case,Value,IntegerField,CharField,Count
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from utilities.utils import format_date,base64_to_file,compress_image
from utilities.constants import FILTERS
from .constants import ACTION_LIST,LOT_COLUMN_LIST,TAG_COLUMN_LIST,TAG_ISSUE_COLUMN_LIST,NON_TAG_INWARD_COLUMN_LIST,MONTH_CODE
from utilities.pagination_mixin import PaginationMixin
from utilities.utils import generate_query_result
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
import qrcode
from django.conf import settings
from django.db.models import ProtectedError
from random import randint
# Create your views here.
#Import Models
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee,isSuperuser,IsSuperuserOrEmployee, IsEmployeeOrCustomer
from .models import (ErpLotInward,ErpLotInwardStoneDetails,ErpLotInwardDetails,ErpTagScanDetails,ErpLotIssueReceipt,ErpLotIssueReceiptDetails,
                     ErpTagIssueReceipt,ErpTagIssueReceiptDetails,ErpLotNonTagInward,ErpLotNonTagInwardDetails,
                     ErpTagging,ErpTagScan, ErpTaggingImages,ErpLotInwardNonTagLogDetails,ErpTagAttribute, ErpTaggingContainerLogDetails,
                     ErpTagSetItems, ErpTagSet , ErpLotMerge , ErpLotMergeDetails)
from employees.models import (Employee)
from retailmasters.models import (Branch,FinancialYear,Uom,Company,Container)
from retailcataloguemasters.models import (Product,Design)
from retailsettings.models import (RetailSettings)
from billing.models import ErpInvoiceSalesDetails
from accounts.models import (User)
from retailmasters.models import (Profile)
from core.models import EmployeeOTP
#Import Views
from retailmasters.views import BranchEntryDate

import random
import string

#Import serializers
from .serializers import (ErpLotInwardNonTagStoneSerializer, ErpLotInwardSerializer,ErpLotInwardDetailsSerializer,ErpLotInwardStoneDetailsSerializer, 
                          ErpLotIssueReceiptSerializer,ErpLotIssueReceiptDetailsSerializer,ErpTagIssueReceiptSerializer,ErpTagIssueReceiptDetailsSerializer,
                          ErpTaggingLogSerializer,ErpLotInwardOtherMetalSerializer, ErpTaggingSerializer,ErpTagStoneSerializer,ErpLotNonTagInwardDetailsSerializer,
                          ErpLotInwardNonTagSerializer, ErpTaggingImagesSerializer,ErpTagAttributeSerializer,ErpTagChargesSerializer,ErpLotNonTagInwardSerializer,
                          ErpTagOtherMetalSerializer,ErpTagScanSerializer,ErpTagScanDetailsSerializer, ErpTaggingContainerLogDetailsSerializer,
                          ErpTagSetItemsSerializer, ErpTagSetSerializer, ErpLotMergeSerializer , ErpLotMergeDetailsSerializer)
from billing.serializers import ErpInvoiceSalesDetailsSerializer
from retailmasters.serializers import ContainerSerializer

from retailcataloguemasters.serializers import (ProductSerializer)
from core.views  import get_reports_columns_template

from django.db import connection
import threading
import time
from django.template.loader import get_template
from django.utils.timezone import localtime,make_aware,is_naive

from xhtml2pdf import pisa
import io
import qrcode
import pytz
from barcode.writer import ImageWriter
from django.db.models.functions import Concat
from django.contrib.staticfiles import finders
# from pyppeteer import launch
# import asyncio

os.environ['PYPPETEER_SKIP_CHROMIUM_DOWNLOAD'] = '1'


def delete_lot_qrs():
    lot_dir = os.path.join(settings.MEDIA_ROOT, 'lot')

    # Check if the container directory exists
    if os.path.exists(lot_dir):
        # Iterate over each file in the container directory and delete
        for root, dirs, files in os.walk(lot_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Optionally, remove empty folders as well
        for root, dirs, _ in os.walk(lot_dir, topdown=False):
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))


def delete_lot_qr_with_delay(delay=6):
    time.sleep(delay)
    delete_lot_qrs()

def generate_lot_qr(lot_code, pkid, gwt, nwt, pcs, request):
    print_data={}
    code = lot_code
    id = pkid
    save_dir = os.path.join(settings.MEDIA_ROOT, f'lot/{id}')
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(code)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    qr_path = os.path.join(save_dir, 'qrcode.png')
    qr_img.save(qr_path)
    
    print_data.update({"qr_path":qr_path, "name":code, "uid":code, "gwt":gwt,
                       "nwt":nwt, "pcs":pcs})
    template = get_template('lot_qr_print.html')
    html = template.render({'data': print_data})
    result = io.BytesIO()
    pisa.pisaDocument(io.StringIO(html), result)
    pdf_path = os.path.join(save_dir, 'lot.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(result.getvalue())
    pdf_path = request.build_absolute_uri(settings.MEDIA_URL +f'lot/{id}/lot.pdf')
    return pdf_path


def generate_lot_detail_qr(detail_data, lot_code, lot_id, request,lot_date):
    data_array = []
    #type_ = int(RetailSettings.objects.get(name='lot_balance_type').value)
    type_ = 1
    for data in detail_data:
        print_data={}
        code = (str(lot_code) + "-" +str(data['id_lot_inward_detail']))
        id = data['id_lot_inward_detail']
        save_dir = os.path.join(settings.MEDIA_ROOT, f'lot/{id}')
        # qr = qrcode.QRCode(
        #     version=1,
        #     error_correction=qrcode.constants.ERROR_CORRECT_L,
        #     box_size=10,
        #     border=4,
        # )
        # qr.add_data(code)
        # qr.make(fit=True)
        # qr_img = qr.make_image(fill_color="black", back_color="white")

        # if not os.path.exists(save_dir):
        #     os.makedirs(save_dir)
        # qr_path = os.path.join(save_dir, 'qrcode.png')
        # qr_img.save(qr_path)
        if type_ == 2:
            issue_pcs = 0
            issue_gwt = 0
            issue_stn_wt = 0
            issue_dia_wt = 0
            issue_nwt = 0
            issue_lwt = 0
            receipt_pcs = 0
            receipt_gwt = 0
            receipt_stn_wt = 0
            receipt_dia_wt = 0
            receipt_nwt = 0
            receipt_lwt = 0
            issue_list_query = ErpLotIssueReceiptDetails.objects.filter(id_lot_inward_detail = data['id_lot_inward_detail'],detail__status = 1)
            issue_list_query = ErpLotIssueReceiptDetailsSerializer(issue_list_query,many=True).data
            for issue_list in issue_list_query:
                issue_pcs += int(issue_list['pieces'])
                issue_gwt += float(issue_list['gross_wt'])
                issue_nwt += float(issue_list['net_wt'])
                issue_lwt += float(issue_list['less_wt'])
                issue_stn_wt += float(issue_list['stone_wt'])
                issue_dia_wt += float(issue_list['dia_wt'])
                receipt_pcs += int(issue_list['receipt_pieces'])
                receipt_gwt += float(issue_list['receipt_gross_wt'])
                receipt_stn_wt += float(issue_list['receipt_stone_wt'])
                receipt_dia_wt += float(issue_list['receipt_dia_wt'])
                receipt_nwt  += float(issue_list['receipt_net_wt'])
                receipt_lwt  += float(issue_list['receipt_less_wt'])
            data.update({
                'tagged_pcs': issue_pcs - receipt_pcs ,
                'tagged_gross_wt': issue_gwt - receipt_gwt,
                'tagged_net_wt': issue_nwt - receipt_nwt,
                'tagged_less_wt': issue_lwt - receipt_lwt,
                'tagged_stone_wt':issue_stn_wt - receipt_stn_wt,
                'tagged_dia_wt':issue_dia_wt - receipt_dia_wt,
            })
        gwt = format((float(data['gross_wt'])-float(data['tagged_gross_wt'])), '.2f')
        nwt = format((float(data['net_wt'])-float(data['tagged_net_wt'])), '.2f')
        pcs = format((float(data['pieces'])-float(data['tagged_pcs'])), '.2f')
        print_data.update({"name":code, "uid":code, "gwt":gwt,
                           "nwt":nwt, "pcs":pcs,"size_name":data.get('size_name',''),"lot_date":format_date(data['lot_date'])})
        # print_data.update({"qr_path":qr_path, "name":code, "uid":code, "gwt":gwt,"lot_date": format_date(data['lot_date']),
        #                    "nwt":nwt, "pcs":pcs})
        print(data,print_data)
        if print_data not in data_array:
            data_array.append(print_data)
    # template = get_template('lot_detail_qr_print.html')
    # html = template.render({'data': data_array})
    # result = io.BytesIO()
    # pisa.pisaDocument(io.StringIO(html), result)
    # save_pdf_dir = os.path.join(settings.MEDIA_ROOT, f'lot_details/{lot_id}')
    # if not os.path.exists(save_pdf_dir):
    #     os.makedirs(save_pdf_dir)
    # pdf_path = os.path.join(save_pdf_dir, 'lot.pdf')
    # with open(pdf_path, 'wb') as f:
    #     f.write(result.getvalue())
    # pdf_path = request.build_absolute_uri(settings.MEDIA_URL +f'lot_details/{lot_id}/lot.pdf')
    return data_array


class LotQRPrintView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    queryset = ErpLotInward.objects.all()
    serializer_class = ErpLotInwardSerializer
    
    def post(self, request, *args, **kwargs):
        pk_id = request.data.get('id')
        qr_print_type = request.data.get('qrPrintType')
        output = []
        

        lot_balance = ErpLotCreateAPIView()
        with connection.cursor() as cursor:
            if qr_print_type == 'lotDetail':
                balance_sql = lot_balance.lot_balance_query("","","",pk_id)
            else:
                balance_sql = lot_balance.lot_balance_query(pk_id)

            cursor.execute(balance_sql)
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = {}
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.update(field_value)
                response_data = report_data
            if qr_print_type == 'lotDetail':
                print_data = {}
                print_data.update({
                    "name":response_data['code'], 
                    "uid":response_data['code'], 
                    "gwt":response_data['blc_gwt'],
                    "label_code":response_data['label_code'],
                    "nwt":response_data['blc_gwt'], 
                    "pcs":response_data['blc_pcs'],
                    "size_name":response_data['size_name'],
                    "lot_date": response_data['lot_date'],
                    "supplier_code": response_data['supplier_code'],
                    "sell_rate": response_data['sell_rate'],
                })
            else:
                for item in response_data:
                    print_data = {}
                    print_data.update({
                    "name":item['code'], 
                    "uid":item['code'], 
                    "gwt":item['blc_gwt'],
                    "label_code":item['label_code'],
                    "nwt":item['nwt'], 
                    "pcs":item['blc_pcs'],
                    "size_name":item['size_name'],
                    "lot_date": item['lot_date'],
                    "supplier_code": item['supplier_code'],
                    "sell_rate": item['sell_rate'],
                })
                
                
            output.append(print_data)
        return Response(output, status=status.HTTP_200_OK)


class LotInwardListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self,request , *args, **kwargs):
        if 'active' in request.query_params:
            queryset = ErpLotInward.objects.filter(is_closed=0).order_by('-pk')
            serializer = ErpLotInwardSerializer(queryset, many=True)
            for data in serializer.data:
                lot_detail = ErpLotInwardDetails.objects.filter(lot_no=data['lot_no'],status=0)
                lot_detail_serializer = ErpLotInwardDetailsSerializer(lot_detail,many=True)
                data.update({"item_details":lot_detail_serializer.data})
            return Response(serializer.data)
        
        lot_inward_detail_id = kwargs.get('lot_inward_detail_id')
        lot_balance = ErpLotCreateAPIView()
        with connection.cursor() as cursor:
            balance_sql = lot_balance.lot_balance_query("","","",lot_inward_detail_id)
            cursor.execute(balance_sql)
            response_data = None
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = {}
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.update(field_value)
                response_data = report_data
            response_data.update({"balance_pcs" : response_data['blc_pcs'] , "balance_gwt" : response_data['blc_gwt']})
            print('response_data' , response_data)
            return Response(response_data, status=status.HTTP_200_OK)

        

    def get_lot_balance_deails(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = ErpLotInward.objects.filter(is_closed=0).order_by('-pk')
            serializer = ErpLotInwardSerializer(queryset, many=True)
            for data in serializer.data:
                lot_detail = ErpLotInwardDetails.objects.filter(lot_no=data['lot_no'])
                lot_detail_serializer = ErpLotInwardDetailsSerializer(lot_detail,many=True)
                data.update({"lot_code": f"{data['lot_code']} - {data['supplier_name']}","item_details":lot_detail_serializer.data})
            return Response(serializer.data)
        
        lot_inward_detail_id = kwargs.get('lot_inward_detail_id')

        #type_ = int(RetailSettings.objects.get(name='lot_balance_type').value)
        type_ = 1

        if lot_inward_detail_id is None:
            return Response({"detail": "lot_inward_detail_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if type_ == 1:

            lot_details = ErpLotInwardDetails.objects.filter(id_lot_inward_detail=lot_inward_detail_id).annotate(
                id_metal = F('id_product__id_metal'),
                tag_pcs=Sum('lot_inward_detail_id__tag_pcs', default=0),
                tag_gwt=Sum('lot_inward_detail_id__tag_gwt', default=0),
                tag_nwt=Sum('lot_inward_detail_id__tag_nwt', default=0),
                tag_lwt=Sum('lot_inward_detail_id__tag_lwt', default=0),
                tag_stn_wt=Sum('lot_inward_detail_id__tag_stn_wt', default=0),
                tag_dia_wt=Sum('lot_inward_detail_id__tag_dia_wt', default=0),
                balance_pcs=ExpressionWrapper(F('pieces') - F('tagged_pcs'),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_gwt=ExpressionWrapper(F('gross_wt') - F('tagged_gross_wt'),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_nwt=ExpressionWrapper(F('net_wt') - F('tagged_net_wt'),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_lwt=ExpressionWrapper(F('less_wt') - F('tagged_less_wt'),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_stn_wt=ExpressionWrapper(F('stone_wt') - Sum('lot_inward_detail_id__tag_stn_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_dia_wt=ExpressionWrapper(F('dia_wt') - Sum('lot_inward_detail_id__tag_dia_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            ).values(
                'id_lot_inward_detail',
                'id_metal',
                'pieces',
                'gross_wt',
                'net_wt',
                'less_wt',
                'dia_wt',
                'stone_wt',
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
                'purchase_touch',
                'purchase_va',
                'purchase_rate',
                'purchase_rate',
                'purchase_mc',
                'purchase_mc_type',
                'pure_wt_cal_type',
                'purchase_rate_type',
            ).first()
        else:
            lot_details = ErpLotInwardDetails.objects.filter(id_lot_inward_detail=lot_inward_detail_id).annotate(
                tag_pcs=Sum('lot_inward_detail_id__tag_pcs', default=0),
                id_metal = F('id_product__id_metal'),
                tag_gwt=Sum('lot_inward_detail_id__tag_gwt', default=0),
                tag_nwt=Sum('lot_inward_detail_id__tag_nwt', default=0),
                tag_lwt=Sum('lot_inward_detail_id__tag_lwt', default=0),
                tag_stn_wt=Sum('lot_inward_detail_id__tag_stn_wt', default=0),
                tag_dia_wt=Sum('lot_inward_detail_id__tag_dia_wt', default=0),
                balance_pcs=ExpressionWrapper(F('pieces') - Sum('lot_inward_detail_id__tag_pcs', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_gwt=ExpressionWrapper(F('gross_wt') - Sum('lot_inward_detail_id__tag_gwt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_nwt=ExpressionWrapper(F('net_wt') - Sum('lot_inward_detail_id__tag_nwt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_lwt=ExpressionWrapper(F('less_wt') - Sum('lot_inward_detail_id__tag_lwt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_stn_wt=ExpressionWrapper(F('stone_wt') - Sum('lot_inward_detail_id__tag_stn_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
                balance_dia_wt=ExpressionWrapper(F('dia_wt') - Sum('lot_inward_detail_id__tag_dia_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            ).values(
                'id_lot_inward_detail',
                'id_metal',
                'pieces',
                'gross_wt',
                'net_wt',
                'less_wt',
                'dia_wt',
                'stone_wt',
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
                'purchase_touch',
                'purchase_va',
                'purchase_rate',
                'purchase_rate',
                'purchase_mc',
                'purchase_mc_type',
                'pure_wt_cal_type',
                'purchase_rate_type',
            ).first()
            for list_ in lot_details:
                issue_pcs = 0
                issue_gwt = 0
                issue_stn_wt = 0
                issue_dia_wt = 0
                issue_nwt = 0
                issue_lwt = 0
                issue_list_query = ErpLotIssueReceiptDetails.objects.filter(id_lot_inward_detail = list_['id_lot_inward_detail'],detail__status = 1)
                issue_list_query = ErpLotIssueReceiptDetailsSerializer(issue_list_query,many=True).data
                for issue_list in issue_list_query:
                    issue_pcs += int(issue_list['pieces'])
                    issue_gwt += float(issue_list['gross_wt'])
                    issue_nwt += float(issue_list['net_wt'])
                    issue_lwt += float(issue_list['less_wt'])
                    issue_stn_wt += float(issue_list['stone_wt'])
                    issue_dia_wt += float(issue_list['dia_wt'])
                list_.update({
                    'balance_pcs': issue_pcs,
                    'balance_gwt': issue_gwt,
                    'balance_nwt': issue_nwt,
                    'balance_lwt': issue_lwt,
                    'balance_stn_wt':issue_stn_wt,
                    'balance_dia_wt':issue_dia_wt,
                })

        if lot_details:
            return Response(lot_details, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    
    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_branch = request.data.get('branch')
        id_branch = (id_branch) if id_branch != '' else 0
        lot_list = ErpLotInward.objects.select_related('id_supplier', 'id_branch').annotate(
            total_pieces=Sum('lot_details__pieces'),
            total_gross_wt=Sum('lot_details__gross_wt'),
            total_net_wt=Sum('lot_details__net_wt'),
            total_stn_wt=Sum('lot_details__stone_wt'),
            total_dia_wt=Sum('lot_details__dia_wt'),
            lot_details_exist=Count('lot_details')
        ).values(
            'lot_no', 
            'id_branch',
            'lot_code',
            'total_pieces',
            'total_gross_wt', 
            'total_net_wt',
            'total_stn_wt',
            'total_dia_wt',
            'is_closed', 
            'lot_date',
            'id_supplier__supplier_name',
            'id_branch__name',
            'lot_details_exist'
        )
        if from_date and to_date:
            lot_list = lot_list.filter(lot_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            lot_list = lot_list.filter(id_branch__in=id_branch)

        lot_list = lot_list.order_by('-pk')
        paginator, page = pagination.paginate_queryset(lot_list, request,None,LOT_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,LOT_COLUMN_LIST,request.data.get('path_name',''))
        
        for index,lot in enumerate(page):
            if lot['lot_details_exist'] > 0:
                lot['pk_id'] = lot['lot_no']
                lot['is_active'] = lot['is_closed']
                lot['status_name'] = 'Open' if lot['is_closed']==0 else 'Closed'
                lot['is_editable'] = 1 if lot['is_closed']==0 else 0
                lot['lot_date'] = format_date(lot['lot_date'])
                lot['total_gross_wt'] = format(lot['total_gross_wt'], '.3f')
                lot['total_net_wt'] = format(lot['total_net_wt'], '.3f')
                lot['total_stn_wt'] = format(lot['total_stn_wt'], '.3f')
                lot['total_dia_wt'] = format(lot['total_dia_wt'], '.3f')


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
        return pagination.paginated_response(list(page),context) 

class ErpLotCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpLotInwardSerializer


    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                lot_data = request.data.get('lot')
                lot_details = request.data.get('lot_details')
                if not lot_data:
                    return Response({"error": "Lot data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not lot_details:
                    return Response({"error": "Lot Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(request.data['lot']['id_branch'])
                branch=Branch.objects.get(id_branch=request.data['lot']['id_branch'])
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                lot_code = generate_lot_code(lot_data,branch.short_name,fy)
                request.data['lot'].update({"lot_date":entry_date,"lot_code":lot_code,"fin_year":fin_id,"created_by": request.user.id})
                lot_serializer = ErpLotInwardSerializer(data = request.data['lot'])
                if lot_serializer.is_valid(raise_exception=True):
                    lot_serializer.save()
                    insert_lot_details(lot_details,entry_date,lot_serializer.data['lot_no'],request.data['lot']['id_branch'],request)
                    est_url = self.generate_lot_print(lot_serializer.data['lot_no'],request)
                    return Response({"message":"Lot Created Successfully.",'pdf_url': est_url,"lot_no":lot_serializer.data['lot_no'],"pdf_path":"inventory/lot/print"}, status=status.HTTP_201_CREATED)
                return Response({"message":lot_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self, request, *args, **kwargs):
        lot_no = self.kwargs.get('pk')
        est_url = self.generate_lot_balance_report(lot_no,request)
        response_data = { 'pdf_url': est_url}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)

    def lot_balance_query(self , lot_no="" , lot_code = "" , item_code = "" , lot_inward_detail_id=""):
        
            sql = F"""
                    select d.id_lot_inward_detail,date_format(l.lot_date,'%d-%m-%Y') as lot_date,l.lot_no,l.lot_code,
                    s.supplier_name,s.short_code as supplier_code,if(d.size_id!=null,sz.name,'') as size_name,des.design_name,p.product_name,concat(l.lot_code,'-',d.item_code) as code,
                    if(d.id_design_id!=null,concat(p.short_code,'-',des.design_code,p.short_code),p.short_code) as label_code,
                    d.pieces,d.gross_wt,d.less_wt,d.net_wt,d.sell_rate,      
                    d.tagged_gross_wt,d.tagged_pcs,d.tagged_net_wt,'True' as isChecked,
                    (d.gross_wt - coalesce(d.tagged_gross_wt,0) - coalesce(merge.gross_wt,0) ) as blc_gwt,
                    (d.net_wt - d.tagged_net_wt - merge.gross_wt) as blc_nwt,
                    (d.pieces - coalesce(d.tagged_pcs,0) - coalesce(merge.pcs,0) ) as blc_pcs,'' as merge_pcs , '' as merge_gwt
                    from erp_lot_inward_details d
                    left join erp_product p on p.pro_id = d.id_product_id
                    left join erp_design des on des.id_design = d.id_design_id
                    left join erp_lot_inward l on l.lot_no = d.lot_no_id
                    left join erp_supplier s on s.id_supplier = l.id_supplier_id
                    left join erp_size sz ON sz.id_size = d.size_id
                    left join (
						select n.id_lot_inward_detail_id,sum(n.pieces) as non_tag_pcs,sum(n.gross_wt) as non_tag_gwt,
						sum(n.net_wt) as non_tag_nwt
						from erp_lot_non_tag_inward_details n
                    group by n.id_lot_inward_detail_id) as nontag on nontag.id_lot_inward_detail_id = d.id_lot_inward_detail
                    
                    left join (select m.id_lot_inward_detail_id,coalesce(sum(m.pieces),0) as pcs,
                    coalesce(sum(m.gross_wt),0) as gross_wt
                    from erp_lot_merge_item_details m 
                    group by m.id_lot_inward_detail_id) as merge on merge.id_lot_inward_detail_id = d.id_lot_inward_detail
                    where l.lot_no is not null
                    """
            
            if lot_no!='':
                sql += F" and l.lot_no = {lot_no}"
            
            if lot_code!='':
                sql += F" and l.lot_code = {lot_code}"

            if lot_inward_detail_id!='':

                sql += F" and d.id_lot_inward_detail = {lot_inward_detail_id}"
            
            if item_code!='':
                sql += F" and d.item_code = {item_code}"
            
            sql += F" order by d.id_lot_inward_detail ASC"
            return sql

    def generate_lot_balance_report(self,lot_no , request):
        with connection.cursor() as cursor:
            sql = self.lot_balance_query(lot_no)
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
            save_dir = os.path.join(settings.MEDIA_ROOT, 'lot')
            save_dir = os.path.join(save_dir, f'{lot_no}')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            total_gross_wt = 0
            total_net_wt = 0
            total_pcs = 0
            total_tagged_pcs = 0
            total_tagged_gross_wt = 0
            total_tagged_net_wt = 0
            total_balance_pcs = 0
            total_balance_wt = 0
            for item in response_data:
                    total_gross_wt += float(item['gross_wt'])
                    total_net_wt += float(item['net_wt'])
                    total_pcs += int(item['pieces'])
                    total_tagged_gross_wt += float(item['tagged_gross_wt'])
                    total_tagged_net_wt += float(item['tagged_net_wt'])
                    total_tagged_pcs += int(item['tagged_pcs'])
                    total_balance_pcs += int(item['blc_pcs'])
                    total_balance_wt += float(item['blc_gwt'])
            template_type = RetailSettings.objects.get(name='lot_print_format').value

            if int(template_type) == 1:
                template = get_template('lot_print.html')
            elif int(template_type) == 2:
                template = get_template('lot_print2.html')
            else:
                template = get_template('lot_print3.html')
            response = {}
            response.update({
                "lot_code" : response_data[0]['lot_code'],
                "lot_date" : response_data[0]['lot_date'],
                "supplier_name" : response_data[0]['supplier_name'],
                "item_details" :response_data,
                "tagged_details" : response_data,
                "total_pcs" : format(total_pcs, '.0f'),
                "total_gross_wt" : format(total_gross_wt, '.3f'),
                "total_net_wt" : format(total_net_wt, '.3f'),
                "total_tagged_pcs" : int(total_tagged_pcs),
                "total_tagged_gross_wt" : format(total_tagged_gross_wt, '.3f'),
                "total_tagged_net_wt" : format(total_tagged_net_wt, '.3f'),
                "balance_pcs":total_balance_pcs,
                "balance_wt":format(total_balance_wt , '.3f'),
            })
            print(response)
            html = template.render(response)
            result = io.BytesIO()
            pisa.pisaDocument(io.StringIO(html), result)
            pdf_path = os.path.join(save_dir, 'lot.pdf')
            with open(pdf_path, 'wb') as f:
                f.write(result.getvalue())
            pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'lot/{lot_no}/lot.pdf')
            return pdf_path

    def generate_lot_print(self, lot_no,request):
        instance = ErpLotInward.objects.get(lot_no=lot_no)
        serializer = ErpLotInwardSerializer(instance)
        data = serializer.data
        item_details = ErpLotInwardDetails.objects.filter(lot_no=lot_no)
        item_details_serializer = ErpLotInwardDetailsSerializer(item_details, many=True)
        comp = Company.objects.latest("id_company")
        total_dia_wt,total_stn_wt,total_net_wt,total_gross_wt,purchase_amount,total_pcs,total_less_wt = 0,0,0,0,0,0,0
        total_tagged_pcs = 0
        total_tagged_gwt = 0
        total_tagged_nwt = 0
        for item in item_details_serializer.data:
            product_details = Product.objects.get(pro_id=item['id_product'])
            total_pcs += int(item['pieces'])
            total_gross_wt += float(item['gross_wt'])
            total_net_wt += float(item['net_wt'])
            total_stn_wt += float(item['stone_wt'])
            total_dia_wt += float(item['dia_wt'])
            total_less_wt += float(item['less_wt'])
            purchase_amount += float(item['purchase_cost'])
            total_tagged_pcs +=  int(item['tagged_pcs'])
            total_tagged_gwt +=  float(item['tagged_gross_wt'])
            total_tagged_nwt +=  float(item['tagged_net_wt'])
            item.update({
                "stock_type":'Tagged' if product_details.stock_type==0 else 'Non Tag',
                "id_category":product_details.cat_id.id_category
            })
        data['total_pcs'] = format(total_pcs, '.0f')
        data['total_gross_wt'] = format(total_gross_wt, '.3f')
        data['total_net_wt'] = format(total_net_wt, '.3f')
        data['total_less_wt'] = format(total_less_wt, '.3f')
        data['total_stn_wt'] = format(total_stn_wt, '.3f')
        data['total_dia_wt'] = format(total_dia_wt, '.3f')
        data['purchase_amount'] = format(purchase_amount, '.3f')
        queryset = ErpTagging.objects.filter(tag_lot_inward_details_id__lot_no=lot_no)
        queryset = queryset.values('tag_current_branch', 'tag_lot_inward_details_id') \
                           .annotate( pcs=Sum('tag_pcs'),
                                     gross_wt=Sum('tag_gwt'),
                                     net_wt=Sum('tag_nwt'),
                                     dia_wt=Sum('tag_dia_wt'),
                                     stone_wt=Sum('tag_stn_wt'),
                                     less_wt=Sum('tag_lwt'),
                                      )
        queryset = queryset.annotate(branch=F('tag_current_branch__name'))
        queryset = queryset.annotate(product_name=F('tag_product_id__product_name'))
        result = list(queryset)
        tagged_summary={
                    'pcs': 0,
                    'gross_wt': 0.000,
                    'net_wt': 0.000,
                    'dia_wt': 0.000,
                    'stone_wt': 0.000,
                    'less_wt': 0.000,
                }
        branch_summary ={}
        for entry in result:
            branch_id = entry['tag_current_branch']
            if branch_id not in branch_summary:
                branch_summary[branch_id] = {
                    'pcs': 0,
                    'gross_wt': 0.000,
                    'net_wt': 0.000,
                    'dia_wt': 0.000,
                    'stone_wt': 0.000,
                    'less_wt': 0.000,
                    'item_details':[]
                }
            
            branch_summary[branch_id]['branch'] = (entry['branch'])
            branch_summary[branch_id]['pcs'] += int(entry['pcs'])
            branch_summary[branch_id]['gross_wt'] += float(entry['gross_wt'])
            branch_summary[branch_id]['net_wt'] += float(entry['net_wt'])
            branch_summary[branch_id]['dia_wt'] += float(entry['dia_wt'])
            branch_summary[branch_id]['stone_wt'] += float(entry['stone_wt'])
            branch_summary[branch_id]['less_wt'] += float(entry['less_wt'])

            tagged_summary['pcs'] += int(entry['pcs'])
            tagged_summary['gross_wt'] += float(entry['gross_wt'])
            tagged_summary['net_wt'] += float(entry['net_wt'])
            tagged_summary['dia_wt'] += float(entry['dia_wt'])
            tagged_summary['stone_wt'] += float(entry['stone_wt'])
            tagged_summary['less_wt'] += float(entry['less_wt'])

            branch_summary[branch_id]['item_details'].append(entry)
        


        # Tag Details against lot details id
        tag_queryset = ErpTagging.objects.filter(tag_lot_inward_details_id__lot_no=lot_no)
        tag_queryset = tag_queryset.values('tag_lot_inward_details_id') \
                           .annotate( pcs=Sum('tag_pcs'),
                                     gross_wt=Sum('tag_gwt'),
                                     net_wt=Sum('tag_nwt'),
                                     dia_wt=Sum('tag_dia_wt'),
                                     stone_wt=Sum('tag_stn_wt'),
                                     less_wt=Sum('tag_lwt'),
                                     design_name=F('tag_design_id__design_name')
                                      )
        # Non tag 

        non_tag_queryset = ErpLotNonTagInwardDetails.objects.filter(
                id_lot_inward_detail__lot_no=lot_no
            ).values('id_lot_inward_detail').annotate(
                pcs=Sum('pieces'),
                gross_wt=Sum('gross_wt'),
                net_wt=Sum('net_wt'),
                dia_wt=Sum('dia_wt'),
                stone_wt=Sum('stone_wt'),
                less_wt=Sum('less_wt'),
                design_name=F('id_lot_inward_detail__id_design__design_name')
            )
        for item in non_tag_queryset:
            tagged_summary['gross_wt'] +=float(item['gross_wt'])
            tagged_summary['pcs'] +=int(item['pcs'])
            tagged_summary['net_wt'] +=float(item['net_wt'])

        tagged_and_nontagged = tag_queryset.union(non_tag_queryset, all=True)
        print('tagged_and_nontagged' , tagged_and_nontagged)
        balance_wt=0
        balance_pcs =0
        if tagged_summary:
            balance_wt = total_gross_wt - total_tagged_gwt
            balance_pcs = total_pcs - total_tagged_pcs
        data.update({
            "balance_pcs":balance_pcs,
            "balance_wt":balance_wt,
            "supplier_name":instance.id_supplier.supplier_name,
            "branch":instance.id_branch.name,
            "item_details": item_details_serializer.data,
            'company_detail': comp,
            'branch_summary': branch_summary,
            'tagged_summary': tagged_summary,
            'tagged_details' : tagged_and_nontagged
        })
        save_dir = os.path.join(settings.MEDIA_ROOT, 'lot')
        save_dir = os.path.join(save_dir, f'{lot_no}')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)


        template_type = RetailSettings.objects.get(name='lot_print_format').value

        if int(template_type) == 1:
            template = get_template('lot_print.html')
        elif int(template_type) == 2:
            template = get_template('lot_print2.html')
        else:
            template = get_template('lot_print3.html')


        # template = get_template('lot_print.html')
        html = template.render(data)
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        pdf_path = os.path.join(save_dir, 'lot.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'lot/{lot_no}/lot.pdf')
        return pdf_path


class LotProductClose(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    serializer_class = ErpLotInwardDetailsSerializer

    def get(self, request, *args, **kwargs):
        lot_detail_id = kwargs.get('pk')
        try:
            lot_detail = ErpLotInwardDetails.objects.get(id_lot_inward_detail=lot_detail_id)
            if lot_detail.status:
                return Response({"message": "Lot is already closed."}, status=status.HTTP_400_BAD_REQUEST)
            lot_detail.status = True
            lot_detail.closed_by = request.user
            lot_detail.closed_date = datetime.now(tz=timezone.utc)
            lot_detail.save()
            print(lot_detail)
            return Response({"message": "Lot closed successfully."}, status=status.HTTP_200_OK)
        except ErpLotInwardDetails.DoesNotExist:
            return Response({"message": "Lot detail not found."}, status=status.HTTP_404_NOT_FOUND)


class LotDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = ErpLotInward.objects.all()
    serializer_class = ErpLotInwardSerializer
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('close' in request.query_params):

            if(obj.is_closed == False):
                lot_details = ErpLotInwardDetails.objects.filter(lot_no=obj.lot_no).annotate(
                tag_pcs=Sum('lot_inward_detail_id__tag_pcs', default=0),
                tag_gwt=Sum('lot_inward_detail_id__tag_gwt', default=0),
                tag_nwt=Sum('lot_inward_detail_id__tag_nwt', default=0),
                tag_lwt=Sum('lot_inward_detail_id__tag_lwt', default=0),
                tag_stn_wt=Sum('lot_inward_detail_id__tag_stn_wt', default=0),
                tag_dia_wt=Sum('lot_inward_detail_id__tag_dia_wt', default=0),
                stock_type = F('id_product__stock_type')
                ).values(
                    'id_lot_inward_detail',
                    'stock_type',
                    'tag_pcs',
                    'tag_gwt',
                    'tag_nwt',
                    'tag_lwt',
                    'tag_stn_wt',
                    'tag_dia_wt',
                ).first()

                if(lot_details['stock_type']== '1' or (lot_details['tag_pcs'] > 0)):
                    obj.is_closed = True
                    obj.closed_by = self.request.user
                    obj.closed_date =  datetime.now(tz=timezone.utc)
                    obj.save()
                elif (lot_details['stock_type']== '0' and (lot_details['tag_pcs'] == 0)):
                    return Response({"message": "Lot Cannot Be Closed  Before Tagging ...."}, status=status.HTTP_400_BAD_REQUEST)

                return Response({"message": "Lot Closed Successfully."}, status=status.HTTP_202_ACCEPTED)
            else:
                obj.is_closed = False
                obj.closed_by = None
                obj.closed_date =  datetime.now(tz=timezone.utc)
                obj.save()
                return Response({"message": "Lot Closed Successfully Undo."}, status=status.HTTP_202_ACCEPTED)
    
        serializer = ErpLotInwardSerializer(obj)
        data = serializer.data
        item_details = ErpLotInwardDetails.objects.filter(lot_no=data['lot_no'])
        item_details_serializer = ErpLotInwardDetailsSerializer(item_details, many=True)
        for item in item_details_serializer.data:
            product_details = Product.objects.get(pro_id=item['id_product'])
            stone_details = ErpLotInwardStoneDetails.objects.filter(id_lot_inward_detail=item['id_lot_inward_detail'])
            stone_details = ErpLotInwardStoneDetailsSerializer(stone_details, many=True).data
            item.update({
                "stock_type":'Tagged' if int(product_details.stock_type)==0 else 'Non Tag',
                "id_category":product_details.cat_id.id_category,
                "stone_details":stone_details
            })
        data.update({"item_details": item_details_serializer.data})
        return Response(data, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                lot_no = kwargs.get('pk')
                lot_data = request.data.get('lot')
                item_details = request.data.get('lot_details')
                if not lot_no:
                    return Response({"error": "Lot ID is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not lot_data:
                    return Response({"error": "Lot data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not item_details:
                    return Response({"error": "Lot Details data is missing."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    lot_instance = ErpLotInward.objects.get(pk=lot_no)
                except ErpLotInward.DoesNotExist:
                    return Response({"error": "Lot not found."}, status=status.HTTP_404_NOT_FOUND)
                lot_data.update({"updated_by": request.user.id,'updated_on': datetime.now(tz=timezone.utc)})
                lot_serializer = ErpLotInwardSerializer(lot_instance, data=lot_data, partial=True)
                if lot_serializer.is_valid(raise_exception=True):
                    lot_serializer.save()

                    if item_details:
                        self.update_deleted_details(item_details, lot_no)
                        self.update_lot_details(item_details, lot_no,lot_serializer.data,request)

                    return Response({"message": "Lot updated successfully."}, status=status.HTTP_200_OK)
                tb = traceback.format_exc()
                return Response({"error": lot_serializer.errors,"traceback": tb }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}", "traceback": tb }, status=status.HTTP_400_BAD_REQUEST)

    def update_deleted_details(self, item_details, lot_no):
        existing_items = ErpLotInwardDetails.objects.filter(lot_no=lot_no)
        existing_item_map = {item.pk: item for item in existing_items}
        ids_to_delete = set(existing_item_map.keys())
        print(ids_to_delete)
        for detail in item_details:
            item_id = detail.get('id_lot_inward_detail')
            if item_id:
                ids_to_delete.discard(item_id)
        if ids_to_delete:
            print('delete')
            print(ids_to_delete)
            ErpLotInwardDetails.objects.filter(pk__in=ids_to_delete).delete()  

    def update_lot_details(self, item_details, lot_no,lot_data,request):  
        non_tag_settings = RetailSettings.objects.get(name='non_tag_inward_settings').value      
        for detail in item_details:
            item_id = detail.get('id_lot_inward_detail')
            if item_id:
                try:
                    detail.update({
                        "closed_by":None,
                        "status":0,
                    })
                    item_instance = ErpLotInwardDetails.objects.get(pk=item_id)
                    serializer = ErpLotInwardDetailsSerializer(item_instance, data=detail, partial=True)
                    stock_type=Product.objects.get(pro_id=detail['id_product']).stock_type
                    print('insert')
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        if(stock_type=='1' and int(non_tag_settings) == 1):
                           self.update_non_tag_lot_details(detail,lot_data,request)
                        update_other_details(detail.get('stone_details',[]),serializer.data['id_lot_inward_detail'],ErpLotInwardStoneDetailsSerializer,'id_lot_inward_detail','id_lot_inw_stn_detail')
                except ErpLotInwardDetails.DoesNotExist:
                    print('update')
                    self.insert_lot_details(detail,lot_no,lot_data,request,non_tag_settings)
            else:
                print('update')
                self.insert_lot_details(detail,lot_no,lot_data,request,non_tag_settings)


    def insert_lot_details(self,lot_item,item_id,lot_data,request,non_tag_settings):
        print('item_id' , item_id)
        stock_type=Product.objects.get(pro_id=lot_item['id_product']).stock_type
        lot_item.update({"lot_no":item_id})
        lot_detail_serializer = ErpLotInwardDetailsSerializer(data=lot_item)
        if(lot_detail_serializer.is_valid(raise_exception=True)):
            lot_detail_serializer.save()

            if(int(stock_type)==1 and int(non_tag_settings) == 1):
                log_details=lot_item
                log_details.update({"id_lot_inward_detail": lot_detail_serializer.data['id_lot_inward_detail'],"to_branch": lot_data['id_branch'],"date" : lot_data['lot_date'],"id_stock_status": 1,"created_by": request.user.id})
                non_tag_serializer = ErpLotInwardNonTagSerializer(data=log_details)
                non_tag_serializer.is_valid(raise_exception=True)
                non_tag_serializer.save()
                
            for stn in lot_item['stone_details']:
                stn.update({"id_lot_inward_detail":lot_detail_serializer.data['id_lot_inward_detail']})
                lot_detail_stone_serializer = ErpLotInwardStoneDetailsSerializer(data=stn)
                lot_detail_stone_serializer.is_valid(raise_exception=True)
                lot_detail_stone_serializer.save()
                if(stock_type=='1'):
                    log_stn_details=stn
                    log_stn_details.update({ "id_non_tag_log": non_tag_serializer.data['id_non_tag_log'],"stn_cal_type": stn['pur_stn_cal_type'],"stn_rate" : stn['pur_st_rate'],"stn_cost": stn['pur_stn_cost']})
                    non_tag_stn_serializer = ErpLotInwardNonTagStoneSerializer(data=log_stn_details)
                    non_tag_stn_serializer.is_valid(raise_exception=True)
                    non_tag_stn_serializer.save()
    
    def update_non_tag_lot_details(self,log_details,lot_data,request):
        try:
            non_tag_instance = ErpLotInwardNonTagLogDetails.objects.get(id_lot_inward_detail=log_details['id_lot_inward_detail'])
            non_tag_serializer = ErpLotInwardNonTagSerializer(non_tag_instance, data=log_details, partial=True)
            non_tag_serializer.is_valid(raise_exception=True)
            non_tag_serializer.save()
            for stn in log_details['stone_details']:
                log_stn_details=stn
                log_stn_details.update({ "id_non_tag_log": non_tag_serializer.data['id_non_tag_log'],"stn_cal_type": stn['pur_stn_cal_type'],"stn_rate" : stn['pur_st_rate'],"stn_cost": stn['pur_stn_cost']})
                update_other_details(log_details['stone_details'],non_tag_serializer.data['id_non_tag_log'],ErpLotInwardNonTagStoneSerializer,'id_non_tag_log','id_log_stn_detail')
        except ErpLotInwardNonTagLogDetails.DoesNotExist:
            log_details.update({"lot_no": lot_data['lot_no'],"id_lot_inward_detail": log_details['id_lot_inward_detail'],"to_branch": lot_data['id_branch'],"date" : lot_data['lot_date'],"id_stock_status": 1,"created_by": request.user.id})
            non_tag_serializer = ErpLotInwardNonTagSerializer(data=log_details)
            non_tag_serializer.is_valid(raise_exception=True)
            non_tag_serializer.save()
            for stn in log_details['stone_details']:
                log_stn_details=stn
                log_stn_details.update({ "id_non_tag_log": non_tag_serializer.data['id_non_tag_log'],"stn_cal_type": stn['pur_stn_cal_type'],"stn_rate" : stn['pur_st_rate'],"stn_cost": stn['pur_stn_cost']})
                non_tag_stn_serializer = ErpLotInwardNonTagStoneSerializer(data=log_stn_details)
                non_tag_stn_serializer.is_valid(raise_exception=True)
                non_tag_stn_serializer.save()

def generate_bulk_tag_print(tag_data,request):
        for data in tag_data:
            tag_code = data['tag_code']
            tag_id = data['tag_id']
            save_dir = os.path.join(settings.MEDIA_ROOT, f'tag/{tag_id}')

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(tag_code)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            qr_path = os.path.join(save_dir, 'qrcode.png')
            qr_img.save(qr_path)

        
            data.update({
                "qr_code_path":qr_path
            })

        template = get_template('tag_print.html')
        html = template.render({'item_details': tag_data})
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        pdf_path = os.path.join(save_dir, 'tag.pdf')
       # asyncio.run(generate_pdf_from_html(html, pdf_path))
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        pdf_path = request.build_absolute_uri(settings.MEDIA_URL +f'tag/{tag_id}/tag.pdf')
        return pdf_path
    
    
    
def update_tag_balance_in_lotinward(id_lot_inward_detail,data,request):
    pieces = 0
    gross_wt = 0
    less_wt = 0
    net_wt = 0
    dia_wt = 0
    stone_wt = 0
    other_metal_wt = 0
    
    tag_details = ErpLotInwardDetails.objects.filter(id_lot_inward_detail=id_lot_inward_detail)
    tag_details_serializer = ErpLotInwardDetailsSerializer(tag_details, many=True)
    for detail in tag_details_serializer.data:
        pieces += float(detail['tagged_pcs'])
        gross_wt += float(detail['tagged_gross_wt'])
        less_wt += float(detail['tagged_less_wt'])
        net_wt += float(detail['tagged_net_wt'])
        dia_wt += float(detail['tagged_dia_wt'])
        stone_wt += float(detail['tagged_stone_wt'])
        other_metal_wt += float(detail['tagged_other_metal_wt'])
    
    pieces += float(data['tag_pcs'])
    gross_wt += float(data['tag_gwt'])
    less_wt += float(data['tag_lwt'])
    net_wt += float(data['tag_nwt'])
    dia_wt += float(data['tag_dia_wt'])
    stone_wt += float(data['tag_stn_wt'])
    other_metal_wt += float(data['tag_other_metal_wt'])

    ErpLotInwardDetails.objects.filter(id_lot_inward_detail=id_lot_inward_detail).update(
        tagged_pcs = pieces,
        tagged_gross_wt = gross_wt,
        tagged_less_wt = less_wt,
        tagged_net_wt = net_wt,
        tagged_dia_wt = dia_wt,
        tagged_stone_wt = stone_wt,
        tagged_other_metal_wt = other_metal_wt
    )
    settings = int(RetailSettings.objects.get(name='lot_close_type').value) # 1 -> Manual 2-> Auto
    if settings == 2:
        lot_item_details =  ErpLotInwardDetails.objects.filter(id_lot_inward_detail=id_lot_inward_detail).get()
        if int(lot_item_details.tagged_pcs) >= int(lot_item_details.pieces):
            lot_item_details.status = 1
            lot_item_details.closed_by = request.user
            lot_item_details.save()
            lot_item =  ErpLotInwardDetails.objects.filter(status=0,lot_no = lot_item_details.lot_no.pk)
            if lot_item.exists() == False:
                lot_details = ErpLotInward.objects.filter(lot_no=lot_item_details.lot_no.pk).get()
                lot_details.is_closed = 1
                lot_details.closed_by = request.user
                lot_details.save()
        
    
class BulkTagPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.user.pk).get()
        emp = Employee.objects.filter(user_id = request.user.pk).get()
        emp_profile = Profile.objects.filter(id_profile=emp.id_profile.pk).get()

        if(emp_profile.isOTP_req_for_multi_tag_print == True):
            OTP_code = randint(100000, 999999)
            expiry_time = timezone.now() + timedelta(minutes=5)
            if (EmployeeOTP.objects.filter(employee=emp.pk, otp_for="5", expiry__gt=timezone.now()).exists()):
                return Response({"message": "A Tag print OTP already exists. Please use it / wait till its expire"}, status=status.HTTP_400_BAD_REQUEST)
            EmployeeOTP.objects.create(employee=emp, otp_for="5", email_id=user.email,
                                    otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
            return Response({"message": "Enter OTP sent to your mobile number to proceed further."})
        else:
            #tag_url = generate_bulk_tag_print(request.data['tagData'],request)
            return Response({"tag_url":""}, status=status.HTTP_200_OK)
    
    
class ErpTagCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        tag_code = request.query_params.get('tag_code')
        id_branch = request.query_params.get('id_branch')
        if not tag_code:
            return Response({"message": "Tag code is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpTagging.objects.filter(tag_code=tag_code,tag_current_branch=id_branch,tag_status=1).get()
            serializer = ErpTaggingSerializer(queryset,context = {"weight_range":True})
            #tag_url = self.generate_tag_print([serializer.data],request)
            return Response({'data':serializer.data,"tag_url": ''}, status=status.HTTP_200_OK)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
        
    # @staticmethod
    # def generate_tagcode(data,pro_code,fy):

    #     code = ''
    #     tag_code_settings = RetailSettings.objects.get(name='tag_code_settings').value
    #     tag_code_format = RetailSettings.objects.get(name='tag_code_format').value
    #     fy_code = fy.fin_year_code
    #     fin_id = fy.fin_id
    #     last_tagcode=None
    #     if tag_code_settings == '1':#GENERATE CODE WITH FY AND PRODUCT
    #         last_tagcode=ErpTagging.objects.filter(tag_product_id=data['tag_product_id'],fin_year=fin_id).order_by('-tag_id').first()
    #     elif tag_code_settings == '2':#GENERATE CODE WITH PRODUCT
    #         last_tagcode=ErpTagging.objects.filter(tag_product_id=data['tag_product_id']).order_by('-tag_id').first()
    #     elif tag_code_settings == '3':#GENERATE CODE WITH FY
    #         last_tagcode=ErpTagging.objects.filter(fin_year=fin_id).order_by('-tag_id').first()
    #     if last_tagcode:
    #         last_tagcode = last_tagcode.tag_code
    #         match = re.search(r'(\d{5})$', last_tagcode)
    #         if match:
    #             code=match.group(1)
    #             code = str(int(code) + 1).zfill(5)
    #         else:
    #            code = '00001'
    #     else:
    #         code = '00001'
        
    #     tag_code=tag_code_format.replace('@pro_code@', pro_code).replace('@code@', code).replace('@fy_code@', fy_code)

    #     return tag_code
    
    @staticmethod
    def generate_random_tag_code(product):
        attempts = 0
        max_attempts = 1000
        while attempts < max_attempts:
            random_part = random.randint(1000000, 9999999)
            tag_code = f"{product}-{random_part}"
            if not ErpTagging.objects.filter(tag_code=tag_code).exists():
                return tag_code
            attempts += 1

        return tag_code

    @staticmethod
    def generate_tagcode(data,pro_code,fy):
        tag_code_settings = RetailSettings.objects.get(name='tag_code_settings').value
        tag_code_format = RetailSettings.objects.get(name='tag_code_format').value
        is_tag_code_replace = RetailSettings.objects.get(name='is_tag_code_replace').value
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        design_code = ''
        if(is_tag_code_replace=='1' and tag_code_settings!='3'):
            # Define the filtering logic based on settings
            if tag_code_settings == '1':  # GENERATE CODE WITH FY AND PRODUCT
                queryset = ErpTagging.objects.select_for_update().filter(tag_product_id=data['tag_product_id'], fin_year=fin_id)
            elif tag_code_settings == '2':  # GENERATE CODE WITH PRODUCT
                queryset = ErpTagging.objects.select_for_update().filter(tag_product_id=data['tag_product_id'])
            elif tag_code_settings == '3':  # GENERATE CODE WITH FY
                queryset = ErpTagging.objects.select_for_update().filter(fin_year=fin_id)
            elif tag_code_settings == '5':  # GENERATE CODE WITH PRODUCT AND DESIGN
                queryset = ErpTagging.objects.select_for_update().filter(tag_product_id=data['tag_product_id'],tag_design_id=data['tag_design_id'])
                design_code = Design.objects.get(id_design=data['tag_design_id']).design_code
            else:
                queryset = ErpTagging.objects.none()

            existing_codes = list(queryset.values_list('tag_code', flat=True))

            # Extract numeric portions from tag codes
            numbers = []
            for tag in existing_codes:
                match = re.search(r'(\d{3})$', tag)
                if match:
                    numbers.append(int(match.group(1)))

            # If there are no tags, start from '00001'
            if not numbers:
                new_code_num = 1
            else:
                # Sort numbers and find the first missing number
                numbers.sort()
                new_code_num = 1
                for num in numbers:
                    if num == new_code_num:
                        new_code_num += 1
                    else:
                        break 

            # Ensure the new code is always 5 digits
            code = str(new_code_num).zfill(3)

            tag_code = tag_code_format.replace('@pro_code@', pro_code).replace('@code@', code).replace('@fy_code@', fy_code).replace('@design_code@', design_code)
        else:
            last_tag_code=None
            if tag_code_settings == '1':#GENERATE CODE WITH FY AND PRODUCT
                last_tag_code=ErpTagging.objects.select_for_update().filter(tag_product_id=data['tag_product_id'],fin_year=fin_id).order_by('-tag_id').first()
            elif tag_code_settings == '2':#GENERATE CODE WITH PRODUCT
                last_tag_code=ErpTagging.objects.select_for_update().filter(tag_product_id=data['tag_product_id']).order_by('-tag_id').first()
            elif tag_code_settings == '3':#GENERATE CODE WITH FY
                last_tag_code=ErpTagging.objects.select_for_update().filter(fin_year=fin_id).order_by('-tag_id').first()
            elif tag_code_settings == '5':  # GENERATE CODE WITH PRODUCT AND DESIGN
                last_tag_code = ErpTagging.objects.select_for_update().filter(tag_product_id=data['tag_product_id'],tag_design_id=data['tag_design_id'])
                design_code = Design.objects.get(id_design=data['tag_design_id']).design_code
            elif tag_code_settings == '6':  # GENERATE CODE WITH Year Product code Date Month tag sequence
                last_tag_code = ErpTagging.objects.select_for_update().filter(tag_product_id=data['tag_product_id'],tag_date = data['tag_date']).order_by('-tag_id').first()
                date_obj = data['tag_date']
                year = str(date_obj.year)[-2:]
                day = date_obj.day
                month = date_obj.month
                month_code = MONTH_CODE[month]

                if last_tag_code:
                    last_tag_code = last_tag_code.tag_code
                    
                    match = re.search(r'(\d+)$', last_tag_code)
                    if match:
                        code=match.group(1)
                        code=int(code)+1
                    else:
                        code = '1'
                else:
                    code = '1'
        
                tag_code = (
                                tag_code_format
                                .replace('@pro_code@', str(pro_code))
                                .replace('@code@', str(code))
                                .replace('@year_code@', str(year))
                                .replace('@month@', str(month_code))
                                .replace('@day@', str(day))
                            )

                return tag_code
            

            if last_tag_code:
                last_tag_code = last_tag_code.tag_code
                match = re.search(r'(\d{3})$', last_tag_code)
                if match:
                    code=match.group(1)
                    code = str(int(code) + 1).zfill(3)
                else:
                    code = '001'
            else:
                code = '001'
        
            tag_code=tag_code_format.replace('@pro_code@', pro_code).replace('@code@', code).replace('@fy_code@', fy_code).replace('@design_code@', design_code)
            
        return tag_code
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                tag_details = request.data
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(tag_details[0]['id_branch'])
                tag_code_settings = RetailSettings.objects.get(name='tag_code_settings').value
                #no_of_item = int(request.data.get('totalTags',1))
                return_data = []
                for tag in tag_details:
                    data = tag
                    tag_images = data['tag_images']
                    del data['tag_images']
                    product=Product.objects.get(pro_id=data['tag_product_id'])
                    # design=Design.objects.get(id_design=data['tag_design_id'])
                    # sub_design=SubDesign.objects.get(id_sub_design=data['tag_sub_design_id'])
                    uom=Uom.objects.get(uom_id=data['tag_uom_id'])
                    stone_detail = data['stone_details']
                    charges_detail = data['charges_details']
                    attribute_detail = data['attribute_details']
                    other_metal_detail = data['other_metal_detail']
                    data.update({
                        "tag_date":entry_date,
                        "tag_current_branch":data['id_branch'],
                    })
                    if tag_code_settings=='4':
                        tag_code = self.generate_random_tag_code(product.short_code)
                    else:  
                        tag_code = self.generate_tagcode(data,product.short_code,fy)
                    supplier_id = ErpLotInwardDetails.objects.filter(id_lot_inward_detail=data['tag_lot_inward_details']).get()
                    if supplier_id:
                        supplier_id = supplier_id.lot_no.id_supplier.pk
                    
                    data.update({
                        "tag_code":tag_code,
                        "tag_status":1,
                        "fin_year":fin_id,
                        "id_supplier":supplier_id,
                        "created_by": request.user.id
                    })
                  
                    tag_serializer = ErpTaggingSerializer(data=data,context = {"weight_range":True})
                    if tag_serializer.is_valid(raise_exception=True):
                        tag_serializer.save()
                        tag_img = []
                        for image_data in tag_images:
                            tag_img_data = {}
                            b = ((base64.b64decode(image_data['preview'][image_data['preview'].find(",") + 1:])))
                            img = Image.open(io.BytesIO(b))
                            filename = 'tag_image.jpeg'
                            img_object = ImageFile(io.BytesIO(
                            img.fp.getvalue()), name=filename)
                            tag_img_data.update({"tag_image":img_object})
                            tag_img_data.update({"erp_tag":tag_serializer.data['tag_id'],
                                                 "is_default":image_data['default']})
                            tagging_image_serializer = ErpTaggingImagesSerializer(data=tag_img_data)
                            tagging_image_serializer.is_valid(raise_exception=True)
                            tagging_image_serializer.save()
                            #tag_img.push(tagging_image_serializer.data)

                        for datas in charges_detail:
                            datas.update({
                                'id_charges' : datas['selectedCharge'],
                                'charges_amount' : datas['amount']
                            })

                        for datas in attribute_detail:
                            datas.update({
                                'id_attribute' : datas['selectedAttribute'],
                                'value' : datas['attrValue']
                            })

                        insert_other_details(stone_detail,ErpTagStoneSerializer,{"tag_id":tag_serializer.data['tag_id']})

                        insert_other_details(charges_detail,ErpTagChargesSerializer,{"tag_id":tag_serializer.data['tag_id']})

                        insert_other_details(attribute_detail,ErpTagAttributeSerializer,{"tag_id":tag_serializer.data['tag_id']})

                        insert_other_details(other_metal_detail,ErpTagOtherMetalSerializer,{"tag_id":tag_serializer.data['tag_id']})



                        log_details={
                            'to_branch': data['id_branch'],
                            'date': entry_date,
                            'id_stock_status': 1,
                            'tag_id': tag_serializer.data['tag_id'],
                            'transaction_type': 1,
                            'ref_id': tag_serializer.data['tag_id'],
                            "created_by": request.user.id
                        }
                        log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                        log_tag_serializer.is_valid(raise_exception=True)
                        log_tag_serializer.save()

                        update_tag_balance_in_lotinward(tag_serializer.data['tag_lot_inward_details'],data,request)                       
                        total_stone_pcs = sum(int(item.get("stone_pcs", 0)) for item in stone_detail)
                        data.update({
                            "stn_pcs":total_stone_pcs,
                            **tag_serializer.data,
                            "tag_images" : tag_img,
                        })
                        return_data.append(data)
                    else :
                        return Response({"error":tag_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                #tag_url = self.generate_tag_print(return_data,request)

                lot_balance = get_lot_balance(data['tag_lot_inward_details'])
                return Response({"message":"Tag Created Successfully.","data":return_data,"lot_balance":lot_balance,"tag_url":""}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def generate_tag_print(self, return_data,request):
        save_dir = os.path.join(settings.MEDIA_ROOT, f'tag/')
        template = RetailSettings.objects.get(name='tag_print_format').value
        company_name = Company.objects.first().company_name
        settings_data = {
            'company_name': company_name,
            'tag_print_template': template,
        } 
        prn_path  = tag_prn_print(return_data,settings_data, save_dir)
        # prn_path = request.build_absolute_uri(settings.MEDIA_URL +prn_path)
        return prn_path
    
    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                item =request.data
                try:
                    item_id = item['tag_id']
                    stone_details =[]
                    stone_details=item.get('stone_details')
                    charges_detail = item.get('charges_details')
                    other_metal_detail = item.get('other_metal_detail')
                    item_instance = ErpTagging.objects.get(pk=item_id)
                    serializer    = ErpTaggingSerializer(item_instance, data=item, partial=True)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        update_other_details(stone_details,serializer.data['tag_id'],ErpTagStoneSerializer,'tag_id','id_tag_stn_detail')
                        update_other_details(other_metal_detail,serializer.data['tag_id'],ErpTagOtherMetalSerializer,'tag_id','id_tag_other_metal')
            
                    attribute_details = item.get('attribute_details')
                    for datas in attribute_details:
                        datas.update({
                            'id_attribute' : datas['selectedAttribute'],
                            'value' : datas['attrValue']
                        })

                    for datas in charges_detail:
                            datas.update({
                                'id_charges' : datas['selectedCharge'],
                                'charges_amount' : datas['amount']
                            })

                    update_other_details(attribute_details,item_id,ErpTagAttributeSerializer,'tag_id','tag_attribute_id')

                    update_other_details(charges_detail,serializer.data['tag_id'],ErpTagChargesSerializer,'tag_id','tag_charges_id')


                    tag_images = item.get('tag_images')
                    tag_img_data_details = []
                    for image_data in tag_images:
                        tag_img_data = {}
                        if 'data:image/' in image_data['preview'][:30]:
                            b = ((base64.b64decode(image_data['preview'][image_data['preview'].find(",") + 1:])))
                            img = Image.open(io.BytesIO(b))
                            filename = 'tag_image.jpeg'
                            img_object = ImageFile(io.BytesIO(
                            img.fp.getvalue()), name=filename)
                            tag_img_data.update({ "tag_image":img_object,
                                                "erp_tag":item_id,
                                                "is_default":image_data['default'],
                                                "id":image_data.get('id')})
                        else :
                            tag_img_data.update({ 
                                "erp_tag":item_id,
                                "is_default":image_data['default'],
                                "id":image_data.get('id')})
                            
                        tag_img_data_details.push(tag_img_data)
                    print(tag_img_data_details)
                    update_other_details(tag_img_data_details,item_id,ErpTaggingImagesSerializer,'erp_tag','id')

                    lot_balance = get_lot_balance(serializer.data['tag_lot_inward_details'])
                    update_tag_balance_in_lotinward(serializer.data['tag_lot_inward_details'],request)

                    return Response({"message":"Tag Updated Successfully.","lot_balance":lot_balance,"updated_data":serializer.data}, status=status.HTTP_201_CREATED)

                except ErpLotInwardDetails.DoesNotExist:
                    return Response({"error": "Invalid Tag"}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    


class TagListView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpTagging.objects.all()
    serializer_class = ErpTaggingSerializer

    def get(self, request, *args, **kwargs):
        tag_code = request.query_params.get('tag_code')
        old_tag_code = request.query_params.get('old_tag_code')
        id_branch = request.query_params.get('id_branch')
        if (not tag_code and not old_tag_code):
            return Response({"message": "Tag code is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try: 
            if tag_code :
               queryset = ErpTagging.objects.filter(tag_code=tag_code)
            else:
                # queryset = ErpTagging.objects.filter(old_tag_code=old_tag_code)
                queryset = ErpTagging.objects.filter(Q(old_tag_code=old_tag_code) | Q(old_tag_id=old_tag_code))
            queryset = queryset.filter(tag_current_branch=id_branch,tag_status=1).get()
            if queryset.order_tag.exists():
                return Response({"message": "Tag Reserved For Order"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = ErpTaggingSerializer(queryset)
            output = serializer.data
            output.update({"item_type":0})
            return Response(output, status=status.HTTP_200_OK)
        except ErpTagging.DoesNotExist:
            try:
                if tag_code :
                   queryset = ErpTagging.objects.filter(tag_code=tag_code).get()
                else:
                    queryset = ErpTagging.objects.filter(old_tag_code=old_tag_code).get()

                if queryset.tag_status.pk == 1:
                    if queryset.order_tag:
                       return Response({"message": "Tag Reserved For Order"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                       return Response({"message": "Tag not found in this branch"}, status=status.HTTP_400_BAD_REQUEST)
                
                elif queryset.tag_status.pk == 2:
                    return Response({"message": "Tag is Sold Out"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": f"Tag is {queryset.tag_status.name}"}, status=status.HTTP_400_BAD_REQUEST)

                
            except ErpTagging.DoesNotExist:
                return Response({"message": "Invalid Tag"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        id_branch = (id_branch) if id_branch != '' else 0

        queryset = ErpTagging.objects.all()
        if from_date and to_date:
            queryset = queryset.filter(tag_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(tag_current_branch__in=id_branch)
        else:
            queryset = queryset.filter(tag_current_branch=id_branch)

        queryset = queryset.order_by('-pk')
        output = []
        paginator, page = pagination.paginate_queryset(queryset, request,None,TAG_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,TAG_COLUMN_LIST,request.data.get('path_name',''))
        serializer = ErpTaggingSerializer(page, many=True)
        for data in serializer.data:
            if(ErpTaggingImages.objects.filter(erp_tag=data['tag_id']).exists()):
                preview_images_query = ErpTaggingImages.objects.filter(erp_tag=data['tag_id'])
                preview_images_serializer = ErpTaggingImagesSerializer(preview_images_query, many=True, context={"request": request})
                for image_data in preview_images_serializer.data:
                    image_data.update({"image":image_data['tag_image']})
                if(ErpTaggingImages.objects.filter(erp_tag=data['tag_id'], is_default=True).exists()):
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=data['tag_id']).get(is_default=True)
                else:
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=data['tag_id']).first()
                tag_image_seri = ErpTaggingImagesSerializer(tag_image, context={"request":request})
                data.update({"image":tag_image_seri.data['tag_image'], "image_text":data['tag_code'][len(data['tag_code'])-1],
                             "preview_images":preview_images_serializer.data})
            else:
                data.update({"image":None, "image_text":data['tag_code'], "preview_images":[]})
            if data not in output:
                output.append(data)
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
        return pagination.paginated_response(output,context) 
    
    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            tag_lot_inward_details=queryset.tag_lot_inward_details.id_lot_inward_detail
            queryset.delete()
            lot_balance = get_lot_balance(tag_lot_inward_details)
            return Response({"message":"Tag Deleted Successfully.","lot_balance":lot_balance}, status=status.HTTP_202_ACCEPTED)
        except ProtectedError:
            return Response({"message": ["Tag can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)


def call_stored_procedure(proc_name, *args):
    """
    Call a stored procedure
    :param proc_name: Name of the stored procedure
    :param args: Arguments to pass to the stored procedure
    """
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
        raise e
        if 'does not exist' in str(e):
            return Response({"error": f"Error: Stored Procedure '{proc_name}' does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise e
    except DatabaseError as e:
        return Response({"error": f"Database error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)



class ErpNonTagStockAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpTaggingSerializer
    def get(self, request, *args, **kwargs):
        id_branch = request.query_params.get('id_branch')
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(id_branch)
            result = call_stored_procedure('NonTagStock',id_branch,entry_date)
            stone = call_stored_procedure('NonTagStockStone',id_branch,entry_date)
            for index,data in enumerate(result['report_data']):
                stone_details = [stn for stn in stone['report_data'] if ( stn['id_product_id'] == data['id_product_id'] and stn['id_design_id'] == data['id_design_id'] and stn['id_section_id'] == data['id_section_id'])]
                data.update({'sno':index+1,'stone_details':stone_details})
            return Response(result['report_data'], status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class ErpNonTagStockStoneAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpTaggingSerializer
    def get(self, request, *args, **kwargs):
        id_branch = request.query_params.get('id_branch')
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(id_branch)
            result = call_stored_procedure('NonTagStockStone',id_branch,entry_date)
            for index,data in enumerate(result['report_data']):
                data.update({'sno':index+1})
            return Response(result['report_data'], status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)



def insert_other_details(details,serializer_name,updated_data):
    return_data =[]
    for item in details:
        item.update(updated_data)
        serializer = serializer_name(data=item)
        if(serializer.is_valid(raise_exception=True)):
            serializer.save()
            return_data.append({*item,*serializer.data})
        else:
            return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    return return_data

class ErpBulkEditAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpTaggingSerializer
    queryset = ErpTagging.objects.all()

    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                details =request.data['tag_details']
                bulk_edit_type =request.data['bulk_edit_type']
                try:
                    for item in details:
                        item_id = item['tag_id']
                        if(bulk_edit_type!=12 and bulk_edit_type!=9 ):
                            stone_details =[]
                            if(bulk_edit_type==3):
                                stone_details=item.get('stone_details')
                                for detail in stone_details:
                                    detail.update({
                                        'stone_pcs': detail['piece'],
                                        'stone_wt' : detail['weight'],
                                        'stone_calc_type' : detail['stn_calc_type'],
                                    })

                            item_instance = ErpTagging.objects.get(pk=item_id)
                            serializer    = ErpTaggingSerializer(item_instance, data=item, partial=True)
                            if serializer.is_valid(raise_exception=True):
                                serializer.save()
                                if(bulk_edit_type==3):
                                    update_other_details(stone_details,serializer.data['tag_id'],ErpTagStoneSerializer,'tag_id','id_tag_stn_detail')

                        if(bulk_edit_type==9):
                            attribute_details = item.get('tag_attributes')
                            for datas in attribute_details:
                                datas.update({
                                    'id_attribute' : datas['selectedAttribute'],
                                    'value' : datas['attrValue']
                                })
                            update_other_details(attribute_details,item_id,ErpTagAttributeSerializer,'tag_id','tag_attribute_id')

                        if(bulk_edit_type==12):
                            tag_images = item.get('tag_images')
                            imagedata = []
                            for image_data in tag_images:
                                tag_img_data = {}
                                if 'data:image/' in image_data['preview'][:30]:
                                    b = ((base64.b64decode(image_data['preview'][image_data['preview'].find(",") + 1:])))
                                    img = Image.open(io.BytesIO(b))
                                    filename = 'tag_image.jpeg'
                                    img_object = ImageFile(io.BytesIO(
                                    img.fp.getvalue()), name=filename)
                                    tag_img_data.update({ "tag_image":img_object,
                                                        "erp_tag":item_id,
                                                        "is_default":image_data['default'],
                                                        "id":image_data.get('id')})
                                else :
                                    tag_img_data.update({ 
                                        "erp_tag":item_id,
                                        "is_default":image_data['default'],
                                        "id":image_data.get('id')})
                                    
                                imagedata.append(tag_img_data)      

                            update_other_details(imagedata,item_id,ErpTaggingImagesSerializer,'erp_tag','id')

                    return Response({"message":"Tag Updated Successfully."}, status=status.HTTP_201_CREATED)

                except ErpLotInwardDetails.DoesNotExist:
                    return Response({"error": "Invalid Tag"}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def post(self, request, *args, **kwargs):
        filter_details = request.data['filter_details']
        custom_filter_details = request.data['custom_filter_details']
        if not filter_details:
            return Response({"error": "filter_details is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpTagging.objects.filter(tag_status=1)
            cleaned_filter_data = {key: value for key, value in filter_details.items() if value != "" and value != None}
            if cleaned_filter_data:
                queryset = queryset.filter(**cleaned_filter_data)

            cleaned_custom_filter_details = {key: value for key, value in custom_filter_details.items() if value != "" and value != None}
            lotid = cleaned_custom_filter_details.get('lotId',None)
            supplier = cleaned_custom_filter_details.get('Supplier',None)
            tagdateto = cleaned_custom_filter_details.get('tagDateTo',None)
            tagdatefrom = cleaned_custom_filter_details.get('tagDateFrom',None)
            vaweightto = cleaned_custom_filter_details.get('vaWeightTo',None)
            vaweightfrom = cleaned_custom_filter_details.get('vaWeightFrom',None)
            grossweightto = cleaned_custom_filter_details.get('grossWeightTo',None)
            grossweightfrom = cleaned_custom_filter_details.get('grossWeightFrom',None)

            if cleaned_custom_filter_details:
                if lotid:
                    queryset = queryset.filter(tag_lot_inward_details__lot_no=lotid)
                if supplier:
                    queryset = queryset.filter(tag_lot_inward_details__lot_no__id_supplier=supplier)
                if tagdateto:
                    date_obj = datetime.strptime(tagdateto, "%Y-%m-%dT%H:%M:%S.%fZ")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                    queryset = queryset.filter(tag_date__lte = formatted_date)
                if tagdatefrom:
                    date_obj = datetime.strptime(tagdatefrom, "%Y-%m-%dT%H:%M:%S.%fZ")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                    queryset = queryset.filter(tag_date__gte = formatted_date)
                if vaweightto:
                    queryset = queryset.filter(tag_wastage_wt__lte=vaweightto)
                if vaweightfrom:
                    queryset = queryset.filter(tag_wastage_wt__gte=vaweightfrom)
                if grossweightto:
                    queryset = queryset.filter(tag_gwt__lte=grossweightto)
                if grossweightfrom:
                    queryset = queryset.filter(tag_gwt__gte=grossweightfrom)
            #print("Last executed query:", str(queryset.query))
            serializer = ErpTaggingSerializer(queryset, many=True, context={'stone_details': True, 'charges_details': True})
            for item, instance in zip(serializer.data, queryset):
                purity = instance.tag_purity_id.purity if instance.tag_purity_id else None
                mc_type_display = instance.get_tag_mc_type_display()
                tag_calculation_type_name = instance.tag_calculation_type.name if instance.tag_calculation_type else None
                item['tag_purity'] = purity
                item['tag_mc_type_name'] = mc_type_display
                item['tag_calculation_type_name'] = tag_calculation_type_name
                item['tag_purchase_mc_type_name'] = instance.get_tag_purchase_mc_type_display()
                item['tag_purchase_calc_type_name'] = instance.get_tag_purchase_calc_type_display()
                item['tag_purchase_rate_calc_type_name'] = instance.get_tag_purchase_rate_calc_type_display()
                item['isChecked'] = True
                

                if(ErpTaggingImages.objects.filter(erp_tag=item['tag_id']).exists()):
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=item['tag_id'])
                    tag_image_seri = ErpTaggingImagesSerializer(tag_image,many=True, context={"request":request})
                    default = None
                    print(tag_image)
                    for detail in tag_image_seri.data:
                        detail.update({
                            'preview': detail['tag_image'],   
                            'default' :detail['is_default'],
                        })
                        if(detail['is_default'] == True):
                            default = detail['tag_image']

                    item['tag_images'] = tag_image_seri.data
                    item.update({"image":default, "image_text":item['product_name'][len(item['product_name'])-1]})
                else:
                    item['tag_images'] = []
                    item.update({"image":None, "image_text":item['product_name'][len(item['product_name'])-1]})
                
                attribute_set = ErpTagAttribute.objects.filter(tag_id=item['tag_id'])
                tag_attribute= ErpTagAttributeSerializer(attribute_set, many=True).data
                for detail, instance in zip(tag_attribute, attribute_set):
                    detail.update({
                        'name':instance.id_attribute.attribute_name,
                        'selectedAttribute': detail['id_attribute'],   
                        'attrValue' :detail['value'],
                    })
                item['tag_attributes'] = tag_attribute                

            if not serializer.data:
                return Response({"message": "No tags found for the given filters"}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ErpTagging.DoesNotExist:
            return Response({"error": "Tag not found"}, status=status.HTTP_404_NOT_FOUND)

def update_other_details(details, parent_id, serializer_class, parent_field,id):

    existing_details = serializer_class.Meta.model.objects.filter(**{parent_field: parent_id})
    existing_detail_map = {detail.pk: detail for detail in existing_details}
    ids_to_delete = set(existing_detail_map.keys())
    for detail in details:
        detail_id = detail.get(id)
        if isinstance(detail_id, int):
            ids_to_delete.discard(detail_id)
            try:
                detail_instance = existing_detail_map[detail_id]
                serializer = serializer_class(detail_instance, data=detail, partial=True)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            except serializer_class.Meta.model.DoesNotExist:
                return Response({"error": f"{serializer_class.Meta.model.__name__} detail not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            detail.update({parent_field: parent_id})
            serializer = serializer_class(data=detail)
            if serializer.is_valid(raise_exception=True):
                serializer.save()

    if ids_to_delete:
        serializer_class.Meta.model.objects.filter(pk__in=ids_to_delete).delete()



def get_lot_balance(lot_inward_detail_id):
        
        lot_details = ErpLotInwardDetails.objects.filter(id_lot_inward_detail=lot_inward_detail_id).annotate(
            tag_pcs=Sum('lot_inward_detail_id__tag_pcs', default=0),
            tag_gwt=Sum('lot_inward_detail_id__tag_gwt', default=0),
            tag_nwt=Sum('lot_inward_detail_id__tag_nwt', default=0),
            tag_lwt=Sum('lot_inward_detail_id__tag_lwt', default=0),
            tag_stn_wt=Sum('lot_inward_detail_id__tag_stn_wt', default=0),
            tag_dia_wt=Sum('lot_inward_detail_id__tag_dia_wt', default=0),
            balance_pcs=ExpressionWrapper(F('pieces') - Sum('lot_inward_detail_id__tag_pcs', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            balance_gwt=ExpressionWrapper(F('gross_wt') - Sum('lot_inward_detail_id__tag_gwt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            balance_nwt=ExpressionWrapper(F('net_wt') - Sum('lot_inward_detail_id__tag_nwt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            balance_lwt=ExpressionWrapper(F('less_wt') - Sum('lot_inward_detail_id__tag_lwt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            balance_stn_wt=ExpressionWrapper(F('stone_wt') - Sum('lot_inward_detail_id__tag_stn_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            balance_dia_wt=ExpressionWrapper(F('dia_wt') - Sum('lot_inward_detail_id__tag_dia_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),


        ).values(
            'id_lot_inward_detail',
            'pieces',
            'gross_wt',
            'net_wt',
            'less_wt',
            'dia_wt',
            'stone_wt',
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
            'purchase_cost',
            'purchase_rate_type',
            'pure_wt_cal_type',
            'purchase_mc_type',
            'purchase_mc',
            'purchase_rate',
            'purchase_va',
            'purchase_touch',
        ).first()


        return lot_details


class TagAutoCompete(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpTagging.objects.all()
    serializer_class = ErpTaggingSerializer

    def post(self, request, *args, **kwargs):
        tag_code = request.data.get('tag_code')
        old_tag_code = request.data.get('old_tag_code')
        id_branch = request.data.get('id_branch')
        limit = 10
        if not tag_code and not old_tag_code:
            return Response({"message": "Tag code is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if(tag_code):
                queryset = ErpTagging.objects.filter(tag_code__icontains=tag_code)
            else:
                queryset = ErpTagging.objects.filter(old_tag_code__icontains=old_tag_code)

            queryset = queryset.filter(tag_current_branch=id_branch,tag_status=1)[:limit]
            serializer = ErpTaggingSerializer(queryset,many=True)
            for details in serializer.data:
                if(tag_code):
                    details.update({"label": details['tag_code'],"value":details['tag_id'],"item_type":0})
                else:
                    details.update({"label": details['old_tag_code'],"value":details['tag_id'],"item_type":0})

                if(ErpTaggingImages.objects.filter(erp_tag=details['tag_id']).exists()):
                    tag_images = ErpTaggingImages.objects.filter(erp_tag=details['tag_id'])
                    tag_images_serializer = ErpTaggingImagesSerializer(tag_images, many=True, context = {"request":request})
                    details.update({"tag_images":tag_images_serializer.data})
                else:
                    details.update({"tag_images":[]})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
        
class FilterdTag(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpTagging.objects.all()
    serializer_class = ErpTaggingSerializer

    def post(self, request, *args, **kwargs):
        tag_code = request.data.get('tag_code')
        id_branch = request.data.get('id_branch')
        lot_no = request.data.get('lot_no')
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpTagging.objects.filter(tag_current_branch=id_branch,tag_status=1)
            if(lot_no):
               queryset= queryset.filter(tag_lot_inward_details__lot_no = lot_no)

            if(tag_code):
               queryset= queryset.filter(tag_code = tag_code)
            
            serializer = ErpTaggingSerializer(queryset,many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
        


def get_non_tag_stock(id_branch):
    try:
        branch_date = BranchEntryDate()
        entry_date = branch_date.get_entry_date(id_branch)
        result = call_stored_procedure('NonTagStock',id_branch,entry_date)
        stone = call_stored_procedure('NonTagStockStone',id_branch,entry_date)
        for index,data in enumerate(result['report_data']):
            stone_details = [stn for stn in stone['report_data'] if ( stn['id_product_id'] == data['id_product_id'] and stn['id_design_id'] == data['id_design_id'] and stn['id_sub_design_id'] == data['id_sub_design_id'])]
            data.update({'sno':index+1,'stone_details':stone_details})
        return result['report_data']
    except KeyError as e:
        return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    


def extract_code(input_str):
    if input_str.startswith('$') and '$' in input_str:
        return input_str.split('$')[1]
    return input_str
class ErpTagScanView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ErpTagScan.objects.all()
    serializer_class = ErpTagScanSerializer

    def post(self, request,*args, **kwargs):
        try:
            with transaction.atomic():    
                id_branch  = request.data['id_branch']
                id_section  = request.data.get('id_section')
                id_product  = request.data.get('id_product')
                tag_code  = request.data.get('tag_code',None)
                old_tag_code  = request.data.get('old_tag_code',None)
                stock_audit_based_on = int(RetailSettings.objects.get(name='stock_audit_based_on').value) # 1 for section, 2 for Product
                if stock_audit_based_on == 1:
                    if tag_code:
                        tag_queryset = ErpTagging.objects.filter(tag_section_id = id_section,tag_status=1,tag_code = tag_code).get()
                    elif old_tag_code:
                        print("old_tag_code",old_tag_code)
                        tag_queryset = ErpTagging.objects.filter(tag_section_id = id_section,tag_status=1,old_tag_code = old_tag_code).get()
                    queryset = ErpTagScan.objects.filter(id_branch=id_branch,id_section = id_section,status=0)
                    
                else:
                    if tag_code:
                        tag_queryset = ErpTagging.objects.filter(tag_product_id = id_product,tag_status=1,tag_code = tag_code).get()
                    elif old_tag_code:
                        print("old_tag_code",old_tag_code)
                        tag_queryset = ErpTagging.objects.filter(tag_product_id = id_product,tag_status=1,old_tag_code = old_tag_code).get()
                    queryset = ErpTagScan.objects.filter(id_branch=id_branch,id_product = id_product,status=0)

                tag_serializer = ErpTaggingSerializer(tag_queryset).data
                request.data['tag_id'] = tag_serializer['tag_id']
                if(queryset.exists()):
                    tag_scan_data = queryset.get()
                    tag_scan_details = ErpTagScanDetails.objects.filter(id_tag_scan=tag_scan_data, tag_id=request.data['tag_id'])
                    if(tag_scan_details.exists()):
                        return Response({"message": "Tag Already Scanned"}, status=status.HTTP_400_BAD_REQUEST)
                    serializer_det = ErpTagScanDetailsSerializer(data={'tag_id':request.data['tag_id'],'id_tag_scan':tag_scan_data.id_tag_scan,"is_wt_scanned":request.data['is_wt_scanned'],"scale_wt":request.data['scale_weight']})
                    serializer_det.is_valid(raise_exception=True)
                    serializer_det.save(created_by=request.user)
                else:
                    entry_date = BranchEntryDate().get_entry_date(id_branch)
                    request.data['start_date'] = entry_date
                    serializer = ErpTagScanSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(created_by=request.user)
                    serializer_det = ErpTagScanDetailsSerializer(data={'tag_id':request.data['tag_id'],'id_tag_scan':serializer.data['id_tag_scan']})
                    serializer_det.is_valid(raise_exception=True)
                    serializer_det.save(created_by=request.user)
                return Response({"message": "Tag Scanned Sucessfully","data": tag_serializer}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"error": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
        
class ErpTagScanCloseView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ErpTagScan.objects.all()
    serializer_class = ErpTagScanSerializer

    def post(self, request,*args, **kwargs):
        try:
            with transaction.atomic():    
                id_branch  = request.data['id_branch']
                id_section  = request.data.get('id_section')
                id_product  = request.data.get('id_product')
                stock_audit_based_on = int(RetailSettings.objects.get(name='stock_audit_based_on').value) # 1 for section, 2 for Product
                if stock_audit_based_on == 1:
                    queryset = ErpTagScan.objects.filter(id_branch=id_branch,id_section = id_section,status=0)
                else:
                    queryset = ErpTagScan.objects.filter(id_branch=id_branch,id_product = id_product,status=0)
                
                if(queryset.exists()):
                    entry_date = BranchEntryDate().get_entry_date(id_branch)
                    tag_scan_data = queryset.get()
                    tag_scan_data.status = 1
                    tag_scan_data.closed_date =entry_date
                    tag_scan_data.closed_by = request.user
                    tag_scan_data.save()
                    return Response({"message": "Tag Scan Closed Sucessfully"}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"message": "Tag Scan Already Closed"}, status=status.HTTP_400_BAD_REQUEST)
                    
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"{e} is Required"}, status=status.HTTP_400_BAD_REQUEST)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
        
class PartlySoldTagListView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpTagging.objects.all()
    serializer_class = ErpTaggingSerializer

    def get(self, request, *args, **kwargs):
        tag_code = request.query_params.get('tag_code')
        id_branch = request.query_params.get('id_branch')
        if not tag_code:
            return Response({"message": "Tag code is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpTagging.objects.filter(tag_code=tag_code,tag_current_branch=id_branch,tag_status=2,is_partial_sale=1).get()
            serializer = ErpTaggingSerializer(queryset)
            sold_pcs = sold_grosswt = sold_netwt = sold_leswt = sold_diawt = sold_stnwt = sold_otherwt=0
            sold_details = ErpInvoiceSalesDetails.objects.filter(tag_id=queryset.tag_id,invoice_bill_id__invoice_status = 1)
            sold_data = ErpInvoiceSalesDetailsSerializer(sold_details,many=True,context={"stone_details":True}).data
            tag_stone_details = serializer.data["stone_details"]
            tag_other_details = serializer.data["other_metal_details"]
            balance_stone_detail=[]
            balance_other_detail=[]
            for item, sold in zip(sold_data, sold_details):
                sold_pcs += float(sold.pieces)
                sold_grosswt += float(sold.gross_wt)
                sold_netwt += float(sold.net_wt)
                sold_leswt += float(sold.less_wt)
                sold_diawt += float(sold.dia_wt)
                sold_stnwt += float(sold.stone_wt)
                sold_otherwt += float(sold.other_metal_wt)
                for tag_stn in tag_stone_details: # Need To Recheck This Condition ############
                    for stn in item["stone_details"]:
                        if(tag_stn["id_stone"] == stn['id_stone']):# Need To Recheck This Condition
                            tag_stn["stone_pcs"] = float(tag_stn["stone_pcs"]) - float(stn["stone_pcs"])
                            tag_stn["stone_wt"] = float(tag_stn["stone_wt"]) - float(stn["stone_wt"])
                    if(tag_stn["stone_pcs"] > 0 or tag_stn["stone_wt"] > 0):
                        balance_stone_detail.append(tag_stn)
                for tag_metal in tag_other_details: # Need To Recheck This Condition ############
                    for metal in item["other_metal_details"]:
                        if(tag_metal["id_category"] == metal['id_category']):# Need To Recheck This Condition
                            tag_metal["piece"] = float(tag_metal["piece"]) - float(metal["piece"])
                            tag_metal["weight"] = float(tag_metal["weight"]) - float(metal["weight"])
                    if(tag_metal["piece"] > 0 or tag_metal["weight"] > 0):
                        balance_other_detail.append(tag_metal)

            balance_wt = float(queryset.tag_gwt) - float(sold_grosswt)
            if(balance_wt > 0):
                output=serializer.data
                output.update({
                    "tag_gwt" : float(queryset.tag_gwt) - float(sold_grosswt),
                    "tag_nwt" : float(queryset.tag_nwt) - float(sold_netwt),
                    "tag_lwt" : float(queryset.tag_lwt) - float(sold_leswt),
                    "tag_dia_wt" : float(queryset.tag_dia_wt) - float(sold_diawt),
                    "tag_stn_wt" : float(queryset.tag_stn_wt) - float(sold_stnwt),
                    "tag_other_metal_wt" : float(queryset.tag_other_metal_wt) - float(sold_otherwt),
                    "stone_details" : balance_stone_detail,
                    "other_metal_details":balance_other_detail,
                    "item_type":2
                })
                return Response(output, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Tag Has No Balance Weight"}, status=status.HTTP_400_BAD_REQUEST)


            
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
        

def generate_lot_code(data,branch_code,fy):
    code = ''
    lot_code_settings = RetailSettings.objects.get(name='lot_code_settings').value
    lot_code_format = RetailSettings.objects.get(name='lot_code_format').value
    fy_code = fy.fin_year_code
    fin_id = fy.fin_id
    last_code=None
    if lot_code_settings == '0':#GENERATE CODE
        last_code=ErpLotInward.objects.order_by('-lot_no').first()
    elif lot_code_settings == '1':#GENERATE CODE WITH FY AND BRANCH
        last_code=ErpLotInward.objects.filter(id_branch=data['id_branch'],fin_year=fin_id).order_by('-lot_no').first()
    elif lot_code_settings == '2':#GENERATE CODE WITH BRANCH
        last_code=ErpLotInward.objects.filter(id_branch=data['id_branch']).order_by('-lot_no').first()
    elif lot_code_settings == '3':#GENERATE CODE WITH FY
        last_code=ErpLotInward.objects.filter(fin_year=fin_id).order_by('-lot_no').first()
    if last_code:
        last_code = last_code.lot_code
        match = re.search(r'(\d{5})$', last_code)
        if match:
            code=match.group(1)
            code = str(int(code) + 1).zfill(5)
        else:
            code = '00001'
    else:
        code = '00001'
    
    lot_code=lot_code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code)

    return lot_code


def insert_lot_details(lot_details,entry_date,lot_no,id_branch,request):
    non_tag_settings = RetailSettings.objects.get(name='non_tag_inward_settings').value
    item_code=0      
    for lot_item in lot_details:
        item_code += 1
        stock_type=Product.objects.get(pro_id=lot_item['id_product']).stock_type
        lot_item.update({"lot_no":lot_no,"item_code":item_code})
        lot_detail_serializer = ErpLotInwardDetailsSerializer(data=lot_item)
        if(lot_detail_serializer.is_valid(raise_exception=True)):
            lot_detail_serializer.save()

            if(stock_type=='1' and int(non_tag_settings) == 1):
                log_details=lot_item
                log_details.update({"lot_no": lot_no,"id_lot_inward_detail": lot_detail_serializer.data['id_lot_inward_detail'],"to_branch": id_branch,"date" : entry_date,"id_stock_status": 1,"transaction_type":1,"created_by": request.user.id})
                non_tag_serializer = ErpLotInwardNonTagSerializer(data=log_details)
                non_tag_serializer.is_valid(raise_exception=True)
                non_tag_serializer.save()

            other_metal_details=insert_other_details(lot_item.get('other_metal_details',[]),ErpLotInwardOtherMetalSerializer,{"id_lot_inward_detail":lot_detail_serializer.data['id_lot_inward_detail']})
            
                
            for stn in lot_item['stone_details']:
                stn.update({"id_lot_inward_detail":lot_detail_serializer.data['id_lot_inward_detail']})
                lot_detail_stone_serializer = ErpLotInwardStoneDetailsSerializer(data=stn)
                lot_detail_stone_serializer.is_valid(raise_exception=True)
                lot_detail_stone_serializer.save()
                if(stock_type=='1'):
                    log_stn_details=stn
                    log_stn_details.update({ "id_non_tag_log": non_tag_serializer.data['id_non_tag_log'],"stn_cal_type": stn['pur_stn_cal_type'],"stn_rate" : stn['pur_st_rate'],"stn_cost": stn['pur_stn_cost']})
                    non_tag_stn_serializer = ErpLotInwardNonTagStoneSerializer(data=log_stn_details)
                    non_tag_stn_serializer.is_valid(raise_exception=True)
                    non_tag_stn_serializer.save()


class ErpTaggingContainerLogDetailsListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        branch = request.data['branch']
        container = request.data['container']
        tag = request.data['tag']

        base_filters = Q()
        
        if branch is not None:
            base_filters |= Q(from_branch=branch) | Q(to_branch=branch)
        
        if container is not None:
            base_filters |= Q(from_container=container) | Q(to_container=container)
        
        if tag is not None:
            base_filters &= Q(tag=tag)
        queryset = ErpTaggingContainerLogDetails.objects.filter(base_filters)
        result = []
        for entry in queryset:
            from_branch = {
                "label": entry.to_branch.name if entry.from_branch_id != branch and entry.to_branch_id == branch else entry.from_branch.name,
                "value": entry.to_branch.pk if entry.from_branch_id != branch and entry.to_branch_id == branch else entry.from_branch.pk
            } if entry.from_branch or entry.to_branch else None

            to_branch = None if entry.from_branch_id != branch and entry.to_branch_id == branch else {
                "label": entry.to_branch.name if entry.to_branch else None,
                "value": entry.to_branch.pk if entry.to_branch else None
            }
            
            # from_container = {
            #     "label": entry.to_container.container_name if entry.from_container_id != container and entry.to_container_id == container else entry.from_container.container_name,
            #     "value": entry.to_container.pk if entry.from_container_id != container and entry.to_container_id == container else entry.from_container.pk
            # } if entry.from_container or entry.to_container else None

            to_container = None if entry.from_container_id != container and entry.to_container_id == container else {
                "label": entry.to_container.container_name if entry.to_container else None,
                "value": entry.to_container.pk if entry.to_container else None
            }
            
            # Build the response data
            data = {
                "id": entry.id,
                # "tag": {"label": entry.tag.name, "value": entry.tag.pk},
                "tag_code":None,
                "tag_name":entry.tag.tag_code,
                "pieces":entry.tag.tag_pcs,
                "tag": entry.tag.pk,
                "from_branch": entry.to_branch.pk,
                "to_branch": None,
                # "to_branch": entry.to_branch.pk,
                "from_container": entry.to_container.pk,
                "to_container": None,
                # "to_container": entry.to_container.pk,
                "transaction_type": entry.transaction_type,
                "status": {"label": entry.status.name, "value": entry.status.pk} if entry.status else None,
                # "updated_by": {"label": entry.updated_by.username, "value": entry.updated_by.pk} if entry.updated_by else None,
                # "updated_on": entry.updated_on,
            }
            result.append(data)
        return Response(result, status=status.HTTP_200_OK)         
                    
class ErpTaggingContainerLogDetailsCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            for data in request.data['tag_container_details']:
                ErpTagging.objects.filter(tag_id=data['tag']).update(container=data['to_container'])
                data.update({"updated_by":request.user.pk})
                serializer = ErpTaggingContainerLogDetailsSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            return Response({"message":"Tag assigned to container successfully."}, status=status.HTTP_200_OK)
        
class ErpTagContainerScanView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ErpTagScan.objects.all()
    serializer_class = ErpTagScanSerializer

    def post(self, request,*args, **kwargs):
        try:
            with transaction.atomic():    
                id_branch  = request.data['id_branch']
                id_container  = request.data['id_container']
                tag_queryset = ErpTagging.objects.filter(tag_current_branch=id_branch,tag_status=1,container = id_container)
                tag_serializer = ErpTaggingSerializer(tag_queryset,many=True).data
                request.data['tag_id'] = tag_serializer['tag_id']
                queryset = ErpTagScan.objects.filter(id_branch=id_branch,container = id_container,status=0)
                if(queryset.exists()):
                    tag_scan_data = queryset.get()
                    tag_scan_details = ErpTagScanDetails.objects.filter(id_tag_scan=tag_scan_data, tag_id=request.data['tag_id'])
                    if(tag_scan_details.exists()):
                        return Response({"message": "Tag Already Scanned"}, status=status.HTTP_400_BAD_REQUEST)
                    serializer_det = ErpTagScanDetailsSerializer(data={'tag_id':request.data['tag_id'],'id_tag_scan':tag_scan_data.id_tag_scan})
                    serializer_det.is_valid(raise_exception=True)
                    serializer_det.save(created_by=request.user)
                else:
                    entry_date = BranchEntryDate().get_entry_date(id_branch)
                    request.data['start_date'] = entry_date
                    serializer = ErpTagScanSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(created_by=request.user)
                    serializer_det = ErpTagScanDetailsSerializer(data={'tag_id':request.data['tag_id'],'id_tag_scan':serializer.data['id_tag_scan']})
                    serializer_det.is_valid(raise_exception=True)
                    serializer_det.save(created_by=request.user)
                return Response({"message": "Tag Scanned Sucessfully","data": tag_serializer}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"error": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)

class ErpTagContainerScanDetailView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ErpTagScan.objects.all()
    serializer_class = ErpTagScanSerializer

    def post(self, request,*args, **kwargs):
        try:
            with transaction.atomic():    
                id_branch  = request.data['id_branch']
                #id_container  = request.data['id_container']
                container_code = request.data['container_code']
                container_details=Container.objects.filter(sku_id = container_code,branch = id_branch).get()
                tag_queryset = ErpTagging.objects.filter(tag_current_branch=id_branch,tag_status=1,container = container_details.id_container)
                tag_serializer = ErpTaggingSerializer(tag_queryset,many=True).data
                # queryset = ErpTagScan.objects.filter(id_branch=id_branch,container = container_details.id_container,status=0)
                # if(queryset.exists()):
                #     queryset = queryset.get()
                #     for data in tag_serializer:
                #         product_details=Product.objects.get(pro_id = data['tag_product_id'])
                #         product_details = ProductSerializer(product_details).data
                #         data['product_other_wt'] = product_details['other_wt']
                #         data['isScanned'] = False
                #         tqueryset = ErpTagScanDetails.objects.filter(tag_id=data['tag_id'],id_tag_scan = queryset.id_tag_scan)
                #         if(tqueryset.exists()):
                #             data['isScanned'] = True
                #     container_data = ContainerSerializer(container_details).data
                #     return Response({"message": "Container Scanned Already","data": tag_serializer,"container_wt":container_details.weight,'container_data':container_data}, status=status.HTTP_201_CREATED)
                # else:
                #     entry_date = BranchEntryDate().get_entry_date(id_branch)
                #     request.data['start_date'] = entry_date
                #     request.data['container'] = container_details.id_container
                #     serializer = ErpTagScanSerializer(data=request.data)
                #     serializer.is_valid(raise_exception=True)
                #     serializer.save(created_by=request.user)
                #     # serializer_det = ErpTagScanDetailsSerializer(data={'tag_id':request.data['tag_id'],'id_tag_scan':serializer.data['id_tag_scan']})
                #     # serializer_det.is_valid(raise_exception=True)
                #     # serializer_det.save(created_by=request.user)
                for data in tag_serializer:
                    product_details=Product.objects.get(pro_id = data['tag_product_id'])
                    product_details = ProductSerializer(product_details).data
                    data['product_other_wt'] = product_details['other_wt']
                    data['isScanned'] = False

                container_data = ContainerSerializer(container_details).data
                return Response({"message": "Container Scanned Sucessfully","data": tag_serializer,"container_wt":container_details.weight,'container_data':container_data}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"error": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Container.DoesNotExist:
            return Response({"message": "Container not found"}, status=status.HTTP_400_BAD_REQUEST)
        
class ErpTagContainerScanCloseView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ErpTagScan.objects.all()
    serializer_class = ErpTagScanSerializer

    def post(self, request,*args, **kwargs):
        try:
            with transaction.atomic():    
                id_branch  = request.data['id_branch']
                id_container  = request.data['id_container']
                tag_details = request.data['tag_details']
                queryset = ErpTagScan.objects.filter(id_branch=id_branch,container = id_container,status=0)
                if(queryset.exists()):
                    entry_date = BranchEntryDate().get_entry_date(id_branch)
                    tag_scan_data = queryset.get()
                    for data in tag_details:
                        serializer_det = ErpTagScanDetailsSerializer(data={'tag_id':data['tag_id'],'id_tag_scan':tag_scan_data.id_tag_scan})
                        serializer_det.is_valid(raise_exception=True)
                        serializer_det.save(created_by=request.user)
                    tag_scan_data.status = 1
                    tag_scan_data.closed_date =entry_date
                    tag_scan_data.closed_by = request.user
                    tag_scan_data.save()
                    return Response({"message": "Tag Scan Closed Sucessfully"}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"message": "Tag Scan Already Closed"}, status=status.HTTP_400_BAD_REQUEST)
                    
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"{e} is Required"}, status=status.HTTP_400_BAD_REQUEST)
        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)
        
# async def generate_pdf_from_html(html_content,output_path):
#         chromium_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"
#         browser = await launch(headless=True,executablePath=chromium_path)
#         page = await browser.newPage()

#         # Set content to the Pyppeteer page
#         await page.setContent(html_content, {'waitUntil': 'load'})
        
#         # Generate the PDF and save it to the specified path
#         await page.pdf({'path': output_path, 'format': 'A4'})
        
#         # Close the browser
#         await browser.close()    
class LotIssueDetailListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):        
        lot_id = request.query_params.get('lot_id')
        issue_status = int(request.query_params.get('status',1))
        code = request.query_params.get('code')
        branch = request.query_params.get('branch')

        if issue_status == 1 :

            if lot_id is None:
                return Response({"detail": "lot_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            #lot_details = ErpLotInwardDetails.objects.filter(lot_no=lot_id)

            lot_details = ErpLotInwardDetails.objects.annotate(
                lot_identifier=Concat(
                    F('lot_no__lot_code'),  # lot_code from the related ErpLotInward model
                    Value('-'),
                    F('item_code'),
                    output_field=CharField()
                )
            ).filter(lot_identifier=lot_id)

            lot_list  = ErpLotInwardDetailsSerializer(lot_details,many=True).data

            for lot in lot_list:
                issue_pcs = 0
                issue_gwt = 0
                receipt_pcs = 0
                receipt_gwt = 0
                issue_nwt = 0
                receipt_nwt = 0
                issue_list_query = ErpLotIssueReceiptDetails.objects.filter(id_lot_inward_detail = lot['id_lot_inward_detail'])
                issue_list_query = ErpLotIssueReceiptDetailsSerializer(issue_list_query,many=True).data
                for issue_list in issue_list_query:
                    issue_pcs += int(issue_list['pieces'])
                    issue_gwt += float(issue_list['gross_wt'])
                    issue_nwt += float(issue_list['net_wt'])
                    receipt_pcs += int(issue_list['receipt_pieces'])
                    receipt_gwt += float(issue_list['receipt_gross_wt'])
                    receipt_nwt += float(issue_list['receipt_net_wt'])
                
                lot['lot_code'] = str(lot['lot_code']) + '-' + str(lot['item_code'])
                lot['gross_wt'] = format(float(lot['gross_wt']) - issue_gwt + receipt_gwt , '.3f')
                lot['net_wt'] = format(float(lot['net_wt']) - issue_nwt + receipt_gwt, '.3f')
                lot['pieces'] = int(lot['pieces']) - issue_pcs + receipt_pcs
                lot['lot_gross_wt'] = format(float(lot['gross_wt']) - issue_gwt + receipt_gwt , '.3f')
                lot['lot_net_wt'] = format(float(lot['net_wt']) - issue_nwt + receipt_gwt, '.3f')
                lot['lot_pieces'] = int(lot['pieces']) - issue_pcs + receipt_pcs
                if(float(lot['gross_wt']) <= 0):
                    return Response({"message": "Item Does not Contain Weight"}, status=status.HTTP_400_BAD_REQUEST) 

            if lot_details:
                return Response(lot_list, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND) 
            
        else:
            
            if branch is None and code is None:
                return Response({"detail": "Branch,Code is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            lot_details = ErpLotIssueReceiptDetails.objects.filter(detail__id_branch=branch,detail__ref_no = code,detail__status= 1)

            lot_list  = ErpLotIssueReceiptDetailsSerializer(lot_details,many=True).data

            for item, instance in zip(lot_list, lot_details):
                item.update({
                    "id": instance.detail.id,
                    "lot_code":instance.id_lot_inward_detail.lot_no.lot_code,
                    "product_name":instance.id_lot_inward_detail.id_product.product_name,
                    'lot_gross_wt' : instance.gross_wt,
                    'lot_net_wt': instance.net_wt,
                    'lot_pieces': instance.pieces,
                })
            if lot_list:
                return Response(lot_list, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Details Not found."}, status=status.HTTP_404_NOT_FOUND) 
        
    def generate_ref_code(self, data,branch_code,fy):
        code = ''
        code_format = "@fy_code@-@branch_code@-@code@"
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_code=None
        last_code=ErpLotIssueReceipt.objects.filter(id_branch=data['id_branch'],fin_year=fin_id).order_by('-id').first()

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
        
        code=code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code)

        return code
        
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                issue_data = request.data
                issue_details = request.data.get('issue_details')
                if not issue_data:
                    return Response({"error": "Issue data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not issue_details:
                    return Response({"error": "Issue Receipt Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if(int(issue_data["type"])== 1):
                    branch_date = BranchEntryDate()
                    entry_date = branch_date.get_entry_date(issue_data['id_branch'])
                    branch=Branch.objects.get(id_branch=issue_data['id_branch'])
                    fy=FinancialYear.objects.get(fin_status=True)
                    fin_id = fy.fin_id
                    ref_no = self.generate_ref_code(issue_data,branch.short_name,fy)
                    issue_data.update({"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": request.user.id})
                    issue_serializer = ErpLotIssueReceiptSerializer(data = issue_data)
                    if issue_serializer.is_valid(raise_exception=True):
                        issue_serializer.save()
                        for item in issue_details:
                            item.update({"detail":issue_serializer.data["id"]})
                            issue_detail_serializer = ErpLotIssueReceiptDetailsSerializer(data=item)
                            if(issue_detail_serializer.is_valid(raise_exception=True)):
                                issue_detail_serializer.save()
                        #insert_lot_details(lot_details,entry_date,lot_serializer.data['lot_no'],request.data['lot']['id_branch'],request)
                        #est_url = self.generate_lot_print(lot_serializer.data['lot_no'],request)
                        return Response({"message":"Issue Receipt Created Successfully.",'pdf_url': '',"ref_no":issue_serializer.data['ref_no'],"pdf_path":"inventory/lot/print"}, status=status.HTTP_201_CREATED)
                else:
                    branch_date = BranchEntryDate()
                    entry_date = branch_date.get_entry_date(issue_data['id_branch'])        
                    issue_data.update({"status":2,"receipt_entry_date":entry_date,"updated_by": request.user.id})
                    try:
                        instance = ErpLotIssueReceipt.objects.get(pk=issue_data['id'])
                    except ErpLotIssueReceipt.DoesNotExist:
                        return Response({"error": "Issue Receipt not found."}, status=status.HTTP_404_NOT_FOUND)
                    issue_serializer = ErpLotIssueReceiptSerializer(instance,data = issue_data, partial=True)
                    if issue_serializer.is_valid(raise_exception=True):
                        issue_serializer.save()
                        for item in issue_details:
                            item_instance = ErpLotIssueReceiptDetails.objects.get(pk=item['id_detail'])
                            serializer = ErpLotIssueReceiptDetailsSerializer(item_instance, data=item, partial=True)
                            if serializer.is_valid(raise_exception=True):
                                serializer.save()
                        return Response({"message":"Issue Receipt Updated Successfully.",'pdf_url': '',"ref_no":issue_serializer.data['ref_no'],"pdf_path":"inventory/lot/print"}, status=status.HTTP_201_CREATED)
                    

                return Response({"message":issue_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class LotIssueReceiptPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        pk_id = self.kwargs.get('pk')
        response_data = self.generate_issue_print(pk_id)
        return Response({"response_data" : response_data}, status=status.HTTP_202_ACCEPTED)
    
    def generate_issue_print(self,pk_id):

        queryset = ErpLotIssueReceipt.objects.get(id=pk_id)
        serializer = ErpLotIssueReceiptSerializer(queryset)
        data = serializer.data
        data.update({ 
            "entry_date": queryset.entry_date.strftime("%d-%m-%Y"),
            "issue_employee" : queryset.issue_employee.firstname,
        })
        item_queryset = ErpLotIssueReceiptDetails.objects.filter(detail = pk_id)
        item_serializer = ErpLotIssueReceiptDetailsSerializer(item_queryset, many=True)
        lot_details = item_serializer.data
        total_pcs = 0
        total_gross_weight = 0
        for item in lot_details:
            item.update({
                "lot_no": f"{item['lot_no']}-{item['id_lot_inward_detail']}"
            })
            total_pcs += int(item['pieces'])
            total_gross_weight += float(item['gross_wt'])
        data.update({
            "total_pcs": total_pcs,
            "total_gross_weight": format(total_gross_weight, '.3f'),
        })
        return {**data, "items": lot_details}
        

    
class TagIssueDetailListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):        
        section = request.query_params.get('section')
        issue_status = int(request.query_params.get('status',1))
        code = request.query_params.get('code')
        branch = request.query_params.get('branch')

        if issue_status == 1 :

            if section is None and branch is None:
                return Response({"detail": "section,branch is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            details = ErpTagging.objects.filter(tag_current_branch=branch,tag_section_id = section,is_issued_to_counter = False,tag_status = 1)

            details_list  = ErpTaggingSerializer(details,many=True).data

            print(details_list)

            for tag in details_list:
                tag['less_wt'] = tag['tag_lwt']
                tag['gross_wt'] = tag['tag_gwt']
                tag['net_wt'] = tag['tag_nwt']
                tag['pieces'] = tag['tag_pcs']
                tag['lot_gross_wt'] = tag['tag_gwt']
                tag['lot_net_wt'] = tag['tag_nwt']
                tag['lot_pieces'] = tag['tag_pcs']
                tag['lot_less_wt'] = tag['tag_lwt']


            if details_list:
                return Response(details_list, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND) 
            
        else:
            
            if branch is None and code is None:
                return Response({"detail": "Branch,Code is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            tag_details = ErpTagIssueReceiptDetails.objects.filter(detail__id_branch=branch,detail__ref_no = code,detail__status= 1)

            tag_list  = ErpTagIssueReceiptDetailsSerializer(tag_details,many=True).data

            for item, instance in zip(tag_list, tag_details):
                item.update({
                    "id": instance.detail.id,
                    "tag_code":instance.tag.tag_code,
                    "product_name":instance.tag.tag_product_id.product_name,
                    "pieces": instance.tag.tag_pcs,
                    "gross_wt": instance.tag.tag_gwt,
                    "net_wt": instance.tag.tag_nwt,
                    "less_wt": instance.tag.tag_lwt,
                })
            if tag_list:
                return Response(tag_list, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND) 
        
    def generate_ref_code(self, data,branch_code,fy):
        code = ''
        code_format = "@fy_code@-@branch_code@-@code@"
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_code=None
        last_code=ErpTagIssueReceipt.objects.filter(id_branch=data['id_branch'],fin_year=fin_id).order_by('-id').first()

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
        
        code=code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code)

        return code
        
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                issue_data = request.data
                issue_details = request.data.get('issue_details')
                if not issue_data:
                    return Response({"error": "Issue data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not issue_details:
                    return Response({"error": "Issue Receipt Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if(int(issue_data["type"])== 1):
                    branch_date = BranchEntryDate()
                    entry_date = branch_date.get_entry_date(issue_data['id_branch'])
                    branch=Branch.objects.get(id_branch=issue_data['id_branch'])
                    fy=FinancialYear.objects.get(fin_status=True)
                    fin_id = fy.fin_id
                    ref_no = self.generate_ref_code(issue_data,branch.short_name,fy)
                    issue_data.update({"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": request.user.id})
                    issue_serializer = ErpTagIssueReceiptSerializer(data = issue_data)
                    if issue_serializer.is_valid(raise_exception=True):
                        issue_serializer.save()
                        for item in issue_details:
                            item.update({"detail":issue_serializer.data["id"]})
                            tag_instance = ErpTagging.objects.get(pk=item['tag'])
                            tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":request.user.id,"is_issued_to_counter":True }, partial=True)
                            tag_serializer.is_valid(raise_exception=True)
                            tag_serializer.save()
                            issue_detail_serializer = ErpTagIssueReceiptDetailsSerializer(data=item)
                            if(issue_detail_serializer.is_valid(raise_exception=True)):
                                issue_detail_serializer.save()
                        #insert_lot_details(lot_details,entry_date,lot_serializer.data['lot_no'],request.data['lot']['id_branch'],request)
                        #est_url = self.generate_lot_print(lot_serializer.data['lot_no'],request)
                        return Response({"message":"Issue Receipt Created Successfully.",'pdf_url': '',"ref_no":issue_serializer.data['ref_no'],"pdf_path":"inventory/lot/print"}, status=status.HTTP_201_CREATED)
                else:
                    branch_date = BranchEntryDate()
                    entry_date = branch_date.get_entry_date(issue_data['id_branch'])        
                    issue_data.update({"status":2,"receipt_entry_date":entry_date,"updated_by": request.user.id})
                    try:
                        instance = ErpTagIssueReceipt.objects.get(pk=issue_data['id'])
                    except ErpTagIssueReceipt.DoesNotExist:
                        return Response({"error": "Issue Receipt not found."}, status=status.HTTP_404_NOT_FOUND)
                    issue_serializer = ErpTagIssueReceiptSerializer(instance,data = issue_data, partial=True)
                    if issue_serializer.is_valid(raise_exception=True):
                        issue_serializer.save()
                        for item in issue_details:
                            item_instance = ErpTagIssueReceiptDetails.objects.get(pk=item['id_detail'])
                            serializer = ErpTagIssueReceiptDetailsSerializer(item_instance, data=item, partial=True)
                            if serializer.is_valid(raise_exception=True):
                                serializer.save()
                        return Response({"message":"Issue Receipt Updated Successfully.",'pdf_url': '',"ref_no":issue_serializer.data['ref_no'],"pdf_path":"inventory/lot/print"}, status=status.HTTP_201_CREATED)
                return Response({"message":issue_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)





class TagIssueListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):        
        from_date = request.data.get('fromDate',None)
        to_date = request.data.get('toDate',None)
        id_branch = request.data.get('branch')       
        
        tag_details = ErpTagIssueReceipt.objects.filter(entry_date__lte=to_date,entry_date__gte=from_date)
        if id_branch:
            tag_details = tag_details.filter(id_branch__in = id_branch)

        tag_details =  tag_details.values('id')
        tag_details = tag_details.annotate(
            pieces=Sum('tag_issue_details__tag__tag_pcs', default=0),  # No need for ExpressionWrapper
            gross_wt=Sum('tag_issue_details__tag__tag_gwt', default=0),  # No need for ExpressionWrapper
            receipt_pieces=Sum(
                Case(
                    When(tag_issue_details__status=2, then=F('tag_issue_details__tag__tag_pcs')),
                    default=Value(0),
                    output_field=IntegerField()  # Explicitly set as IntegerField
                )
            ),
            receipt_gross_wt=Sum(
                Case(
                    When(tag_issue_details__status=2, then=F('tag_issue_details__tag__tag_gwt')),
                    default=Value(0),
                    output_field=DecimalField(max_digits=10, decimal_places=3)  # Explicitly set as DecimalField
                )
            )

        ).values(
            'ref_no',
            'issue_employee__firstname',
            'id_branch__name',
            'entry_date',
            'status',
            'pieces',
            'gross_wt',
            'receipt_pieces',
            'receipt_gross_wt',
            'issue_remarks'
        )

        for tag in tag_details:

            tag.update({
                'entry_date': format_date(tag['entry_date']),
                'status': dict([(1, 'Issued'),(2,'Receipted')]).get(tag['status'], ''),
                'status_color':dict([(1, 'primary'),(2,'success')]).get(tag['status'], ''),
            })


        paginator, page = pagination.paginate_queryset(tag_details, request,None,TAG_ISSUE_COLUMN_LIST)
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isReportGroupByReq'] = True
        context = {
            'columns': TAG_ISSUE_COLUMN_LIST,
            'actions': ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy,
        }

        return pagination.paginated_response(tag_details, context)
    

class LotIssueListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):        
        from_date = request.data.get('fromDate',None)
        to_date = request.data.get('toDate',None)
        id_branch = request.data.get('branch')       
        
        lot_details = ErpLotIssueReceipt.objects.filter(entry_date__lte=to_date,entry_date__gte=from_date)
        if id_branch:
            lot_details = lot_details.filter(id_branch__in = id_branch)

        lot_details =  lot_details.values('id')
        lot_details = lot_details.annotate(
            pieces=Sum('issue_details__pieces', default=0),
            gross_wt=Sum('issue_details__gross_wt', default=0),
            receipt_pieces=Sum('issue_details__receipt_pieces', default=0),
            receipt_gross_wt=Sum('issue_details__receipt_gross_wt', default=0),
        ).values(
            'id',
            'ref_no',
            'issue_employee__firstname',
            'id_branch__name',
            'entry_date',
            'status',
            'pieces',
            'gross_wt',
            'receipt_pieces',
            'receipt_gross_wt',
            'issue_remarks'
        )

        for tag in lot_details:

            tag.update({
                'pk_id' : tag['id'],
                'entry_date': format_date(tag['entry_date']),
                'status': dict([(1, 'Issued'),(2,'Receipted')]).get(tag['status'], ''),
                'status_color':dict([(1, 'primary'),(2,'success')]).get(tag['status'], ''),
            })


        paginator, page = pagination.paginate_queryset(lot_details, request,None,TAG_ISSUE_COLUMN_LIST)
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isReportGroupByReq'] = True
        context = {
            'columns': TAG_ISSUE_COLUMN_LIST,
            'actions': ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy,
        }

        return pagination.paginated_response(lot_details, context)


class ErpNonTagLotInwardAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpTaggingSerializer
    def get(self, request, *args, **kwargs):
        lot_id = request.query_params.get('lot_id')
        settings = 1
        if not lot_id:
            return Response({"message": "Lot Id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = ErpLotInward.objects.get(lot_no = lot_id)
            serializer = ErpLotInwardSerializer(obj)
            data = serializer.data
            item_details = ErpLotInwardDetails.objects.filter(lot_no=data['lot_no'])
            item_details_serializer = ErpLotInwardDetailsSerializer(item_details, many=True)
            output = []
            for item in item_details_serializer.data:
                product_details = Product.objects.get(pro_id=item['id_product'])
                stone_details = ErpLotInwardStoneDetails.objects.filter(id_lot_inward_detail=item['id_lot_inward_detail'])
                stone_details = ErpLotInwardStoneDetailsSerializer(stone_details, many=True).data
                if settings == 2 :
                    issue_pcs = 0
                    issue_gwt = 0
                    receipt_pcs = 0
                    receipt_gwt = 0
                    issue_nwt = 0
                    receipt_nwt = 0
                    issue_list_query = ErpLotIssueReceiptDetails.objects.filter(id_lot_inward_detail = item['id_lot_inward_detail'])
                    issue_list_query = ErpLotIssueReceiptDetailsSerializer(issue_list_query,many=True).data
                    for issue_list in issue_list_query:
                        issue_pcs += int(issue_list['pieces'])
                        issue_gwt += float(issue_list['gross_wt'])
                        issue_nwt += float(issue_list['net_wt'])
                        receipt_pcs += int(issue_list['receipt_pieces'])
                        receipt_gwt += float(issue_list['receipt_gross_wt'])
                        receipt_nwt += float(issue_list['receipt_net_wt'])
                    
                    
                    item['gross_wt'] = format(float(item['gross_wt']) - issue_gwt + receipt_gwt , '.3f')
                    item['net_wt'] = format(float(item['net_wt']) - issue_nwt + receipt_gwt, '.3f')
                    item['pieces'] = int(item['pieces']) - issue_pcs + receipt_pcs
                    item['lot_gross_wt'] = format(float(item['gross_wt']) - issue_gwt + receipt_gwt , '.3f')
                    item['lot_net_wt'] = format(float(item['net_wt']) - issue_nwt + receipt_gwt, '.3f')
                    item['lot_pieces'] = int(item['pieces']) - issue_pcs + receipt_pcs
                else:
                    balance_pcs = balance_gwt = balance_nwt = 0
                    balance_pcs = int(item['pieces']) - int(item['tagged_pcs'])
                    balance_gwt = format(float(item['gross_wt']) - float(item['tagged_gross_wt']), '.3f')
                    balance_nwt = format(float(item['net_wt']) - float(item['tagged_net_wt']), '.3f')
                    item.update({ 
                        "gross_wt": balance_gwt,
                        "net_wt": balance_nwt,
                        "pieces": balance_pcs,
                        "lot_gross_wt":balance_gwt,
                        "lot_net_wt":balance_nwt,
                        "lot_pieces":balance_pcs,
                    })

                item.update({ 
                    "stock_type":'Tagged' if int(product_details.stock_type)==0 else 'Non Tag',
                    "id_category":product_details.cat_id.id_category,
                    "stone_details":stone_details
                })
                if int(product_details.stock_type) == 1:
                    output.append(item)

            data.update({"item_details": output})

            return Response(data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

class LotNonTagListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        output = []
        queryset = ErpLotInward.objects.filter(is_closed=False)
        serializer = ErpLotInwardSerializer(queryset, many=True)
        for data in serializer.data:
            lot_detail = ErpLotInwardDetails.objects.filter(lot_no=data['lot_no'],id_product__stock_type=1)
            lot_detail_serializer = ErpLotInwardDetailsSerializer(lot_detail,many=True)
            data.update({"item_details":lot_detail_serializer.data})
            if lot_detail_serializer.data:
                output.append(data)
        return Response(output, status=status.HTTP_200_OK)
        
    def generate_ref_code(self, data,branch_code,fy):
        code = ''
        code_format = "@fy_code@-@branch_code@-@code@"
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_code=None
        last_code=ErpLotNonTagInward.objects.filter(id_branch=data['id_branch'],fin_year=fin_id).order_by('-id').first()

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
        
        code=code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code)

        return code
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                issue_data = request.data
                issue_details = request.data.get('issue_details')
                if not issue_data:
                    return Response({"error": "Issue data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not issue_details:
                    return Response({"error": "Issue Receipt Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(issue_data['id_branch'])
                branch=Branch.objects.get(id_branch=issue_data['id_branch'])
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                ref_no = self.generate_ref_code(issue_data,branch.short_name,fy)
                issue_data.update({"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": request.user.id})
                issue_serializer = ErpLotNonTagInwardSerializer(data = issue_data)
                if issue_serializer.is_valid(raise_exception=True):
                    issue_serializer.save()
                    for item in issue_details:
                        item.update({"detail":issue_serializer.data["id"]})
                        issue_detail_serializer = ErpLotNonTagInwardDetailsSerializer(data=item)
                        lot_item = ErpLotInwardDetails.objects.get(id_lot_inward_detail=item['id_lot_inward_detail'])
                        if(issue_detail_serializer.is_valid(raise_exception=True)):
                            issue_detail_serializer.save()
                            log_details=item
                            log_details.update({"id_lot_inward_detail": item['id_lot_inward_detail'],"to_branch": issue_data['id_branch'],"date" : entry_date,"id_stock_status": 1,"transaction_type":1,"created_by": request.user.id})
                            non_tag_serializer = ErpLotInwardNonTagSerializer(data=log_details)
                            non_tag_serializer.is_valid(raise_exception=True)
                            non_tag_serializer.save()

                            pieces = int(lot_item.tagged_pcs) + int(item['pieces'])
                            gross_wt = float(lot_item.tagged_gross_wt) + float(item['gross_wt'])
                            less_wt = float(lot_item.tagged_less_wt) + float(item['less_wt'])
                            net_wt = float(lot_item.tagged_net_wt) + float(item['net_wt'])
                            dia_wt = float(lot_item.tagged_dia_wt) + float(item['dia_wt'])
                            stone_wt = float(lot_item.tagged_stone_wt) + float(item['stone_wt'])
                            other_metal_wt = float(lot_item.tagged_other_metal_wt) + float(item['other_metal_wt'])

                            ErpLotInwardDetails.objects.filter(id_lot_inward_detail=item['id_lot_inward_detail']).update(
                                    tagged_pcs = pieces,
                                    tagged_gross_wt = gross_wt,
                                    tagged_less_wt = less_wt,
                                    tagged_net_wt = net_wt,
                                    tagged_dia_wt = dia_wt,
                                    tagged_stone_wt = stone_wt,
                                    tagged_other_metal_wt = other_metal_wt
                                )
                        
                    return Response({"message":"Lot Non Tag Inward Created Successfully.",'pdf_url': '',"ref_no":issue_serializer.data['ref_no'],"pdf_path":"inventory/lot/print"}, status=status.HTTP_201_CREATED)

                return Response({"message":issue_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class TagSearchAPIView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):

        product = request.data['selectedProduct']
        branch = request.data['branch']
        design = request.data['selectedDesign']
        supplier = request.data['selectSupplier']
        fromWeight = request.data['fromWeight']
        toWeight = request.data['toWeight']

        if product is None:
             return Response({"message": "Product is required."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            queryset = ErpTagging.objects.filter(tag_current_branch = branch,tag_product_id = product,tag_status = 1).all()
            if design:
                queryset = queryset.filter(tag_design_id = design)
            if supplier:
                queryset = queryset.filter(id_supplier = supplier)
            if fromWeight and toWeight:
                queryset = queryset.filter(tag_gwt__gte=fromWeight, tag_gwt__lte=toWeight)

            serializer = ErpTaggingSerializer(queryset,many=True)
            if len(serializer.data) > 0:
                return Response({"message":"Data retrieved successfully","data":serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message":"No Record Found"}, status=status.HTTP_201_CREATED)


class AdminAppTagImageEdit(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                item = request.data
                item_id = request.data['tag_id']
                tag_images = item.get('tag_images')
                tag_img_data_details = []
                for image_data in tag_images:
                    tag_img_data = {}
                    # if 'data:image/' in image_data['img'][:30]:
                    file_content = base64_to_file(image_data['img'], filename_prefix="myfile",
                                                    file_extension="jpg")
                    compressed_file = compress_image(file_content)
                    tag_img_data.update({
                                "tag_image":compressed_file,
                                "erp_tag":item_id,
                                "is_default":image_data['default'],
                                "id":image_data.get('id')
                            })
                    tag_img_serializer = ErpTaggingImagesSerializer(data=tag_img_data)
                    tag_img_serializer.is_valid(raise_exception=True)
                    tag_img_serializer.save()
                    # if isinstance(image_data.get('id'), int):
                    #     if(ErpTaggingImages.objects.filter(id=image_data.get('id'), erp_tag=item_id).exists()):
                    #         queryset = ErpTaggingImages.objects.filter(id=image_data.get('id'), erp_tag=item_id).first()
                    #         tag_img_data.update({
                    #         "tag_image":file_content,
                    #         "erp_tag":item_id,
                    #         "is_default":image_data['default'],
                    #         "id":image_data.get('id')
                    #         })
                    #         tag_img_serializer = ErpTaggingImagesSerializer(queryset, data=tag_img_data)
                    #         tag_img_serializer.is_valid(raise_exception=True)
                    #         tag_img_serializer.save()
                    #     else:
                    #         tag_img_data.update({
                    #             "tag_image":file_content,
                    #             "erp_tag":item_id,
                    #             "is_default":image_data['default'],
                    #             "id":image_data.get('id')
                    #         })
                    #         tag_img_serializer = ErpTaggingImagesSerializer(data=tag_img_data)
                    #         tag_img_serializer.is_valid(raise_exception=True)
                    #         tag_img_serializer.save()
                # tag_img_data_details.append(tag_img_data)
                # else:
                #     if isinstance(image_data.get('id'), int):
                #         if(ErpTaggingImages.objects.filter(id=image_data.get('id'), erp_tag=item_id).exists()):
                #             ErpTaggingImages.objects.filter(id=image_data.get('id'), erp_tag=item_id).update(is_default=image_data['is_default'])
                   
                        
                # update_other_details(tag_img_data_details,item_id,ErpTaggingImagesSerializer,'erp_tag','id')
                return Response({"message":"Tag Updated Successfully."}, status=status.HTTP_202_ACCEPTED)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

class AdminAppTagImageDelete(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                item = request.data
                item_id = request.data['tag_id']
                tag_images = item.get('tag_images')
                for image_data in tag_images:
                    if(ErpTaggingImages.objects.filter(id=image_data.get('id'), erp_tag=item_id).exists()):
                        ErpTaggingImages.objects.filter(id=image_data.get('id'), erp_tag=item_id).delete()
                return Response({"message":"Tag Images Deleted Successfully."}, status=status.HTTP_202_ACCEPTED)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)        


class AdminAppTagSearch(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpTagging.objects.all()
    serializer_class = ErpTaggingSerializer

    def post(self, request, *args, **kwargs):
        tag_code = request.data.get('tag_code')
        old_tag_code = request.data.get('old_tag_code')
        
        if not tag_code and not old_tag_code:
            return Response({"message": "Tag code is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if(tag_code):
                queryset = ErpTagging.objects.filter(old_tag_code__icontains=tag_code,tag_status = 1).get()
            else:
                queryset = ErpTagging.objects.filter(old_tag_code__icontains=old_tag_code,tag_status = 1).get()

            serializer = ErpTaggingSerializer(queryset,many=False)
            details = serializer.data
            if details:
                if(ErpTaggingImages.objects.filter(erp_tag=details['tag_id']).exists()):
                    tag_images = ErpTaggingImages.objects.filter(erp_tag=details['tag_id'])
                    tag_images_serializer = ErpTaggingImagesSerializer(tag_images, many=True, context = {"request":request})
                    details.update({"tag_images":tag_images_serializer.data})
                else:
                    details.update({"tag_images":[]})
                
                related_items = []
                tag_set = ErpTagSet.objects.filter(tag_id=details['tag_id']).first()
                if tag_set:
                    tag_set_items = ErpTagSetItems.objects.filter(tag_set=tag_set)
                    for item in tag_set_items:
                        if item.tag:
                            related_serialized = ErpTaggingSerializer(item.tag, context={"request": request}).data
                            related_items.append({
                               **related_serialized
                            })

                else:
                    tag_set_item = ErpTagSetItems.objects.filter(tag_id=details['tag_id']).first()
                    if tag_set_item:
                        parent_set = tag_set_item.tag_set
                        if parent_set and parent_set.tag:
                            
                            parent_serialized = ErpTaggingSerializer(parent_set.tag, context={"request": request}).data
                            related_items.append({
                                **parent_serialized
                            })

                        
                        sibling_items = ErpTagSetItems.objects.filter(tag_set=parent_set).exclude(tag_id=details['tag_id'])
                        for sibling in sibling_items:
                            if sibling.tag and sibling.tag.pk != details['tag_id']:
                                sibling_serialized = ErpTaggingSerializer(sibling.tag, context={"request": request}).data
                                related_items.append({**sibling_serialized})

                
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
                    elif(ErpTaggingImages.objects.filter(erp_tag=details['tag_id']).exists()):
                        tag_image_query = ErpTaggingImages.objects.filter(erp_tag=details['tag_id'])
                        tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                        rel_item['tag_images'] = tag_image_serializer.data
                        if(ErpTaggingImages.objects.filter(erp_tag=details['tag_id'], is_default=True).exists()):
                            tag_def_image_query = ErpTaggingImages.objects.filter(erp_tag=details['tag_id'], is_default=True).first()
                            tag_def_image_serializer = ErpTaggingImagesSerializer(tag_def_image_query, context={'request':request})
                            rel_item['default_image'] = tag_def_image_serializer.data
                        else:
                            rel_item['default_image'] = tag_image_serializer.data[0]
                    else:
                        rel_item['tag_images'] = []
                        rel_item['default_image'] = None
                details.update({'related_items':related_items})
                return Response({"data":details,"message":"Tag Retrieved Successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Tag not found"}, status=status.HTTP_200_OK)

        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)



class NonTagInwardListView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpTagging.objects.all()
    serializer_class = ErpTaggingSerializer

    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        id_branch = (id_branch) if id_branch != '' else 0
        queryset = ErpLotNonTagInward.objects.annotate(
            total_gross_wt=Sum('non_tag_issue_details__gross_wt'),
            total_pieces=Sum('non_tag_issue_details__pieces'),
        ).values(
            'ref_no', 
            'id_branch',
            'total_gross_wt', 
            'entry_date',
            'issue_employee__firstname',
            'id_branch__name',
            'total_pieces',
            'id'
        )
        if from_date and to_date:
            queryset = queryset.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(id_branch__in=id_branch)
        else:
            queryset = queryset.filter(id_branch=id_branch)

        queryset = queryset.order_by('-pk')
        paginator, page = pagination.paginate_queryset(queryset, request,None,NON_TAG_INWARD_COLUMN_LIST)

        for lot in queryset:
            lot['pk_id'] = lot['id']
            lot['entry_date'] = format_date(lot['entry_date'])
            lot['total_gross_wt'] = format(lot['total_gross_wt'], '.3f')


        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        context={
            'columns':NON_TAG_INWARD_COLUMN_LIST,
            'actions':ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(queryset,context) 

def tag_prn_print(item_details, settings, output_dir='.'):
    prn = ''
    unique_file_name = f"labels_{int(datetime.now().timestamp() * 1000)}_sds.prn"
    template = settings.get("tag_print_template")
    company_name = settings.get("company_name", "")
    show_wt_in_secret_code = int(RetailSettings.objects.get(name='show_wt_secret_code').value) # 1 for Yes, 2 for No

    for element in item_details:
        tagcode = element.get("tag_code")
        metal = int(element.get("metal"))
        stn_pcs = element.get("stn_pcs", 0)
        product_name = element.get("product_name", "")
        cat_id = int(element.get("cat_id", ""))
        gross_weight = element.get("tag_gwt", "")
        net_weight = element.get("tag_nwt", "")
        less_weight = element.get("tag_lwt", "")
        dia_weight = element.get("tag_dia_wt", "")
        stn_weight = element.get("tag_stn_wt", "")
        size = element.get("size_name")
        wastage_percentage = element.get("tag_wastage_percentage", 0)
        mc = element.get("total_mc_value", "")
        sell_rate = element.get("tag_sell_rate", "")
        fixed_rate_type = int(element.get("fixed_rate_type"))
        purity_name = element.get("purity_name", "")
        month_sup_code = element.get("month_sup_code", "")
        huid = element.get("tag_huid") or ""
        huid2 = element.get("tag_huid2") or ""
        size_label = size or ""
        va_label = f"VA:{(wastage_percentage)}%"
        mc_label = f"MC:{mc}"
        gross_wt_label = f"WT:{gross_weight}"

        if fixed_rate_type == 1:
            sell_rate = element.get("tag_sell_rate")
        else:
            sell_rate = element.get("tag_item_cost")
        
        sell_rate = element.get("tag_item_cost")

        sales_mode = int(element.get("sales_mode"))
        stone_label = f"Stn : {stn_pcs}" if int(stn_pcs) > 0 else ""

        if sales_mode == 0:
            mc_label = f"Rs:{sell_rate}/-"
            va_label = ''
            gross_wt_label = ''

        if template == 1:
            code = f"""^O0
^D0
^C1
^P1
^Q10.0,3.0
^W70
^L
W300,9,5,2,L,8,3,8,0
{tagcode}
AB,17,8,1,1,0,0,{tagcode}
AB,17,39,1,1,0,0,{company_name}
AA,115,12,1,1,0,0,{month_sup_code}
AA,115,39,1,1,0,0,{size_label}
AA,196,7,1,1,0,0,{mc_label}
AA,196,26,1,1,0,0,{va_label}
AB,196,49,1,1,0,0,{gross_wt_label}
E
"""
        elif template == 2:

            gross_weight_label = 'G.WT:'

            if float(less_weight) == 0:
                gross_weight_label = ''
                gross_weight = ''

            sell_rate = element.get("tag_sell_rate")
            if float(sell_rate) > 0:
                gross_weight_label = 'Rs:'
                gross_weight = f"{sell_rate}/-"

            if metal == 2:
                purity_name = ''

            net_weight_label = 'N.WT:'
            if fixed_rate_type == 2 and sales_mode == 0:
                net_weight_label = ''
                net_weight = ''
            if show_wt_in_secret_code == 1 and int(element.get("weight_show_in_print")) == 0:
                code = convert_to_code_word(float(net_weight))
                net_weight_label = ''
                net_weight = code
            if huid and huid2:
                huid = huid +"/"+huid2

            code= f"""G0
n
M0500
MT
O0214
V0
t1
Kf0070
SG
c0000
e
L
D11
H24
PG
pG
SG
ySPM
A2
4911C1000150030{company_name}
4911C0800070059{purity_name}
1W1c55000001200652000000000{tagcode}
1911C0800450118{tagcode}
1911C0800180118{net_weight_label}
1911C0800180158{net_weight}
1911C0800320118{gross_weight_label}
1911C0800320155{gross_weight}
4911C0800150045{stone_label}
1911C0800030118{huid}
Q0001
E"""
            
        elif template == 3:
            print("template 3")
            if fixed_rate_type == 1:
                sell_rate = element.get("tag_sell_rate")
            else:
                sell_rate = element.get("tag_item_cost")
            # gross_weight_label = 'G.WT:'

            # if float(less_weight) == 0:
            #     gross_weight_label = ''
            #     gross_weight = ''

            # sell_rate = element.get("tag_sell_rate")
            # if float(sell_rate) > 0:
            #     gross_weight_label = 'Rs:'
            #     gross_weight = f"{sell_rate}/-"

            # if metal == 2:
            #     purity_name = ''

            # net_weight_label = 'N.WT:'
            # if fixed_rate_type == 2 and sales_mode == 0:
            #     net_weight_label = ''
            #     net_weight = ''
            # if show_wt_in_secret_code == 1 and int(element.get("weight_show_in_print")) == 0:
            #     code = convert_to_code_word(float(net_weight))
            #     net_weight_label = ''
            #     net_weight = code
            if huid and huid2:
                huid = huid +"/"+huid2
            weight_range = element.get("weight_range", "")
            design_name = element.get("design_name", "")
            size_name = element.get("size_name", "")

            if cat_id == 1 or cat_id == 8:

                code= f"""SIZE 93.5 mm, 15 mm
    DIRECTION 0,0
    REFERENCE 0,0
    OFFSET 0 mm
    SET PEEL OFF
    SET CUTTER OFF
    SET PARTIAL_CUTTER OFF
    SET TEAR ON
    CLS
    QRCODE 673,105,L,3,A,180,M2,S7,"{tagcode}"
    CODEPAGE 1252
    TEXT 704,36,"0",180,10,8,"{tagcode}"
    TEXT 493,79,"0",180,9,6,"WT: "
    TEXT 447,80,"0",180,9,7,"{net_weight}"
    TEXT 378,80,"0",180,7,7,"{weight_range}"
    TEXT 493,105,"0",180,9,6,"{purity_name}"
    TEXT 589,47,"0",90,10,8,"RSD"
    TEXT 493,53,"0",180,7,6,"{product_name}"
    TEXT 493,26,"0",180,7,6,"{design_name}"
    TEXT 384,105,"0",180,9,6,"{size_name}"
    TEXT 564,37,"0",90,6,5,"{huid}"
    PRINT 1,1
    """
            elif cat_id == 2 or cat_id == 8:
                print("template 3 cat id 2")
                code= f"""SIZE 93.5 mm, 15 mm
GAP 3 mm, 0 mm
SPEED 5
DENSITY 9
SET RIBBON ON
DIRECTION 0,0
REFERENCE 0,0
OFFSET 0 mm
SET PEEL OFF
SET CUTTER OFF
SET PARTIAL_CUTTER OFF
SET TEAR ON
CLS
QRCODE 693,105,L,3,A,180,M2,S7,"{tagcode}"
CODEPAGE 1252
TEXT 714,31,"0",180,7,6,"{tagcode}"
TEXT 525,83,"0",180,8,8,"WT: "
TEXT 478,82,"0",180,8,7,"{net_weight}"
TEXT 597,45,"0",90,9,8,"RSD"
TEXT 525,56,"0",180,8,7,"{product_name}"
TEXT 525,27,"0",180,7,6,"{design_name}"
TEXT 525,105,"0",180,9,6,"SILVER"
TEXT 390,79,"0",180,7,6,"{size_name}"
PRINT 1,1
    """
            elif cat_id == 3:
                code= f"""SIZE 93.5 mm, 15 mm
DIRECTION 0,0
REFERENCE 0,0
OFFSET 0 mm
SET PEEL OFF
SET CUTTER OFF
SET PARTIAL_CUTTER OFF
SET TEAR ON
CLS
QRCODE 689,103,L,2,A,180,M2,S7,"{tagcode}"
CODEPAGE 1252
TEXT 714,29,"ROMAN.TTF",180,1,8,"{tagcode}"
TEXT 574,45,"ROMAN.TTF",90,1,8,"RSD"
TEXT 511,98,"ROMAN.TTF",180,1,5,"VESSELS"
TEXT 511,64,"ROMAN.TTF",180,1,6,"WT:"
TEXT 511,32,"ROMAN.TTF",180,1,6,"{product_name}"
TEXT 478,65,"ROMAN.TTF",180,1,9,"{net_weight}"
TEXT 445,102,"ROMAN.TTF",180,1,9,"{size_name}"
PRINT 1,1
    """
            elif cat_id == 4:
                code= f"""SIZE 93.5 mm, 15 mm
GAP 3 mm, 0 mm
SPEED 5
DENSITY 9
SET RIBBON ON
DIRECTION 0,0
REFERENCE 0,0
OFFSET 0 mm
SET PEEL OFF
SET CUTTER OFF
SET PARTIAL_CUTTER OFF
SET TEAR ON
CLS
QRCODE 672,102,L,3,A,180,M2,S7,"{tagcode}"
CODEPAGE 1252
TEXT 713,32,"0",180,8,7,"{tagcode}"
TEXT 518,84,"0",180,8,8,"WT: "
TEXT 471,84,"0",180,9,8,"{net_weight}"
TEXT 589,43,"0",90,8,8,"RSD"
TEXT 518,31,"ROMAN.TTF",180,1,8,"{product_name}"
TEXT 518,107,"ROMAN.TTF",180,1,7,"SILVER  92"
TEXT 518,55,"ROMAN.TTF",180,1,7,"{sell_rate}"
TEXT 396,107,"ROMAN.TTF",180,1,7,"{size_name}"
PRINT 1,1
    """
            elif cat_id == 5:
                code= f"""SIZE 93.5 mm, 15 mm
GAP 3 mm, 0 mm
SPEED 5
DENSITY 9
DIRECTION 0,0
REFERENCE 0,0
OFFSET 0 mm
SET PEEL OFF
SET CUTTER OFF
SET PARTIAL_CUTTER OFF
SET TEAR ON
CLS
QRCODE 695,103,L,3,A,180,M2,S7,"{tagcode}"
CODEPAGE 1252
TEXT 720,33,"0",180,9,7,"{tagcode}"
TEXT 465,69,"0",180,8,6,"{dia_weight} Ct"
TEXT 615,51,"0",90,7,7,"RSD"
TEXT 375,4,"0",90,6,6,"{product_name}"
TEXT 569,54,"0",90,5,7,"22KT"
TEXT 465,103,"0",180,7,7,"{net_weight}"
TEXT 593,40,"0",90,6,7,"VVS/EF"
TEXT 522,106,"0",180,7,8,"G  Wt: "
TEXT 465,37,"0",180,8,6,"{stn_weight} Ct"
TEXT 522,75,"0",180,7,8,"D Wt: "
TEXT 522,44,"0",180,7,8,"S  Wt: "
PRINT 1,1
    """

        else:
            size_label = f"Sz:{size_label}" if size else ''
            code = f"""I8,A,001
Q125,024
q1020
S2
D08
ZT
JF
O
R58,0
F100
N
A700,85,2,4,1,1,N,"{tagcode}"
A700,55,2,4,1,1,N,"G:{gross_weight}gm"
A700,20,2,3,1,1,N,"{size_label}"
A500,90,2,3,1,1,N,"{product_name}"
A500,60,2,1,1,2,N,"VA:{wastage_percentage}/gm"
A500,30,2,1,1,2,N,"Mc:{mc}/-"

b320,10,Q,m2,s3,eL,iA,"{tagcode}"
P1
"""

        prn += code

    file_path = f"{output_dir}/{unique_file_name}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(prn)

    return file_path


class TagSqlListView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpTagging.objects.all()
    serializer_class = ErpTaggingSerializer

    def get(self, request, *args, **kwargs):
        tag_code = request.query_params.get('tag_code')
        old_tag_code = request.query_params.get('old_tag_code')
        id_branch = request.query_params.get('id_branch')
        if (not tag_code and not old_tag_code):
            return Response({"message": "Tag code is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        try: 
            if tag_code :
               queryset = ErpTagging.objects.filter(tag_code=tag_code)
            else:
                # queryset = ErpTagging.objects.filter(old_tag_code=old_tag_code)
                queryset = ErpTagging.objects.filter(Q(old_tag_code=old_tag_code) | Q(old_tag_id=old_tag_code))
            queryset = queryset.filter(tag_current_branch=id_branch,tag_status=1).get()
            if queryset.order_tag.exists():
                return Response({"message": "Tag Reserved For Order"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = ErpTaggingSerializer(queryset)
            output = serializer.data
            output.update({"item_type":0})
            return Response(output, status=status.HTTP_200_OK)
        except ErpTagging.DoesNotExist:
            try:
                if tag_code :
                   queryset = ErpTagging.objects.filter(tag_code=tag_code).get()
                else:
                    queryset = ErpTagging.objects.filter(old_tag_code=old_tag_code).get()

                if queryset.tag_status.pk == 1:
                    if queryset.order_tag:
                       return Response({"message": "Tag Reserved For Order"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                       return Response({"message": "Tag not found in this branch"}, status=status.HTTP_400_BAD_REQUEST)
                
                elif queryset.tag_status.pk == 2:
                    return Response({"message": "Tag is Sold Out"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": f"Tag is {queryset.tag_status.name}"}, status=status.HTTP_400_BAD_REQUEST)

                
            except ErpTagging.DoesNotExist:
                return Response({"message": "Invalid Tag"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
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
        id_weight_range = request.data.get('id_weight_range')
        report_type = int(request.data.get('group_by',1))
        id_branch = (id_branch) if id_branch != '' else 0
        page = int(request.data.get("page", 1))
        records_per_page = int(request.data.get("records", 50))  # default to 50 if not passed
        offset = (page - 1) * records_per_page
        report_type = int(request.data.get('group_by',1))
        
        filters = ''
        filters += f' and tag.tag_date BETWEEN "{from_date}" AND "{to_date}" '
        if isinstance(id_branch, list):
            placeholders = ', '.join(str(branch) for branch in id_branch)
            filters += f" AND tag.tag_current_branch_id IN ({placeholders})"
        elif id_branch :
            filters += f" AND tag.tag_current_branch_id = {id_branch}"

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
        if lot:
            filters += f' and lot.lot_no = {lot} '
        if id_weight_range:
            filters += f' and wt.id_weight_range = {id_weight_range} '

        order_by = "ORDER BY tag.tag_id DESC"
        groupingColumns = []
        if report_type == 2:
            groupingColumns = ['supplier_name']
            #order_by = "ORDER BY sup.supplier_name ASC, tag.tag_id DESC"
        elif report_type == 3:
            groupingColumns = ['product_name']
            #order_by = "ORDER BY product.product_name ASC, tag.tag_id DESC"
        elif report_type == 4:
            groupingColumns = ['design_name']
            #order_by = "ORDER BY des.design_name ASC, tag.tag_id DESC"
        elif report_type == 1:
            groupingColumns = ['lot_code']
            #order_by = "ORDER BY lot.lot_code ASC , tag.tag_id DESC"
        
        sql = F"""SELECT tag.tag_code,tag.old_tag_code,product.product_name,des.design_name,subdes.sub_design_name,
                CONCAT(lot.lot_code,'-',sup.supplier_name) as lot_code,b.name as branch_name,sup.supplier_name as supplier_name,tag.tag_id,
                tag.tag_pcs,tag.tag_gwt, tag.tag_lwt, tag.tag_nwt,pur.purity as tag_purity,
                tag.tag_stn_wt, tag.tag_dia_wt, tag.tag_other_metal_wt,tag.tag_wastage_percentage,
                tag.tag_wastage_wt, tag.tag_mc_type, tag.tag_mc_value,tag.tag_sell_rate,tag.tag_item_cost,
                tag.tag_huid2, tag.tag_huid, DATE_FORMAT(tag.tag_date, '%d-%m-%Y') as date,m.metal_name,tag.created_on,
                tag.tag_huid2,sec.section_name,CONCAT(DATEDIFF(CURDATE(), tag.tag_date), ' days') AS stock_age,wt.weight_range_name
                FROM erp_tagging tag
                LEFT JOIN erp_lot_inward_details lot_det ON  lot_det.id_lot_inward_detail = tag.tag_lot_inward_details_id
                LEFT JOIN erp_lot_inward lot ON lot.lot_no = lot_det.lot_no_id
                LEFT JOIN erp_product product ON product.pro_id = tag.tag_product_id_id
                LEFT JOIN erp_design des ON des.id_design = tag.tag_design_id_id
                LEFT JOIN erp_sub_design subdes ON subdes.id_sub_design = tag.tag_sub_design_id_id
                LEFT JOIN erp_supplier sup ON sup.id_supplier = tag.id_supplier_id
                LEFT JOIN erp_purity pur ON pur.id_purity = tag.tag_purity_id_id
                LEFT JOIN branch b ON b.id_branch = tag.tag_current_branch_id
                LEFT JOIN erp_section sec ON sec.id_section = tag.tag_section_id_id
                LEFT JOIN metal m ON m.id_metal = product.id_metal_id
                LEFT JOIN erp_weight_range wt ON product.has_weight_range = 1 and wt.id_product_id = tag.tag_product_id_id and wt.from_weight <= tag.tag_nwt and wt.to_weight >= tag.tag_nwt
                WHERE 1
                {filters}
                {order_by}
                LIMIT {records_per_page} OFFSET {offset}
                """
        print(sql)

        result = generate_query_result(sql)

        count_query = f"""
                    SELECT COUNT(*) as total
                    FROM erp_tagging tag
                    LEFT JOIN erp_product product ON product.pro_id = tag.tag_product_id_id
                    LEFT JOIN erp_lot_inward_details lot_det ON  lot_det.id_lot_inward_detail = tag.tag_lot_inward_details_id
                    LEFT JOIN erp_lot_inward lot ON lot.lot_no = lot_det.lot_no_id
                    LEFT JOIN erp_weight_range wt ON product.has_weight_range = 1 and wt.id_product_id = tag.tag_product_id_id and wt.from_weight <= tag.tag_nwt and wt.to_weight >= tag.tag_nwt
                    WHERE  1
                    {filters}
                    ORDER BY tag.tag_id DESC
                    """
        count_result = generate_query_result(count_query)
        total_records = count_result[0]['total']
        total_pages = (total_records + records_per_page - 1) // records_per_page 
        for index, data in enumerate(result):
            created_on = data['created_on']
            if created_on.tzinfo is None:
                created_on = created_on.replace(tzinfo=pytz.utc)
            time = localtime(created_on).strftime('%I:%M %p')
            data['date']  = f"{data['date']} {time}"

        output = []
        columns = get_reports_columns_template(request.user.pk,TAG_COLUMN_LIST,request.data.get('path_name',''))
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isProductFilterReq'] = True
        filters_copy['isTagCodeFilterReq'] = True
        filters_copy['isDeignFilterReq'] = True
        filters_copy['isPurityFilterReq'] = True
        filters_copy['isSupplierFilterReq'] = True
        filters_copy['isLotFilterReq'] = True
        filters_copy['isGwtFromToFilterReq'] = True
        filters_copy['isMetalFilterReq'] = True
        filters_copy['isReportGroupByReq'] = True
        filters_copy['isWeightRangeFilterReq'] = True
        context={
            'columns':columns,
            'actions':ACTION_LIST,
            'page_count':total_records,
            'total_pages': total_pages,
            'current_page': page,
            'is_filter_req':True,
            'filters':filters_copy,
            'groupingColumns': groupingColumns,
            'groupByOption': [ {'value': 1, 'label': 'Lot'},{'value': 2, 'label': 'Supplier'}, {'value': 3, 'label': 'Product'}, {'value': 4, 'label': 'Design'}],
            }
        return pagination.paginated_response(result,context) 
    
    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            tag_lot_inward_details=queryset.tag_lot_inward_details.id_lot_inward_detail
            queryset.delete()
            lot_balance = get_lot_balance(tag_lot_inward_details)
            return Response({"message":"Tag Deleted Successfully.","lot_balance":lot_balance}, status=status.HTTP_202_ACCEPTED)
        except ProtectedError:
            return Response({"message": ["Tag can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)

class ErpTagPrintAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        tag_ids = request.data.get('tag_ids')
        if not tag_ids:
            return Response({"message": "Tag Id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpTagging.objects.filter(tag_id__in=tag_ids)
            serializer = ErpTaggingSerializer(queryset, many=True,context = {"weight_range":True,"stone_pcs":True})
            save_dir = os.path.join(settings.MEDIA_ROOT, f'tag/')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            template = int(RetailSettings.objects.get(name='tag_print_template').value)
            company_name = Company.objects.first().short_code
            settings_data = {
                'company_name': company_name,
                'tag_print_template': template,
            }
            prn_path  = tag_prn_print(serializer.data,settings_data, save_dir)
            # prn_path = request.build_absolute_uri(settings.MEDIA_URL +prn_path)
            file_handle = open(prn_path, 'rb')
            response = FileResponse(file_handle, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(prn_path)}"'
            return response

        except ErpTagging.DoesNotExist:
            return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)


def convert_to_code_word(number):
    digit_map = {
        '0': 'A', '1': 'B', '2': 'C', '3': 'D', '4': 'E',
        '5': 'F', '6': 'G', '7': 'H', '8': 'I', '9': 'J'
    }

    # Ensure number is formatted as string with 3 decimal places
    formatted_number = f"{number:.3f}"  # e.g., 2.89 -> '2.890'

    integer_part, decimal_part = formatted_number.split('.')
    # Map the parts
    # Map each digit of integer and decimal part
    integer_code = ''.join(digit_map[d] for d in integer_part)
    decimal_code = ''.join(digit_map[d] for d in decimal_part)

    return f"{integer_code}.{decimal_code}"

class ErpTagSetListCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    
    def generate_set_no(self):
        code = ''
        last_code=None
        last_code=ErpTagSet.objects.order_by('-id').first()
        if last_code:
            last_code = last_code.set_no
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
        with transaction.atomic():
            tag_id = request.data.get('tag_id')
            set_items_data = request.data.get('set_items', [])
    
            if not tag_id:
                return Response({"message": "Tag ID is required."}, status=status.HTTP_400_BAD_REQUEST)
    
            try:
                main_tag = ErpTagging.objects.get(pk=tag_id)
            except ErpTagging.DoesNotExist:
                return Response({"message": "Main tag not found."}, status=status.HTTP_400_BAD_REQUEST)
    
            # Either get existing set or create new one
            tag_set, created = ErpTagSet.objects.get_or_create(
                tag=main_tag,
                defaults={
                    'date': timezone.now().date(),
                    'created_by': request.user,
                    'created_on': timezone.now(),
                }
            )
    
            errors = []
            created_items = []
    
            for item in set_items_data:
                tag_code = item.get('tag_code')
                if not tag_code:
                    errors.append("Missing tag_code in one of the set_items.")
                    continue
                
                try:
                    item_tag = ErpTagging.objects.get(Q(tag_code=tag_code) | Q(old_tag_code=tag_code))
                except ErpTagging.DoesNotExist:
                    errors.append(f"Tag code '{tag_code}' not found by either tag_code or old_tag_code.")
                    continue
                
                if ErpTagSetItems.objects.filter(tag=item_tag).exists():
                    errors.append(f"Tag '{tag_code}' is already in a set.")
                    continue
                
                ErpTagSetItems.objects.create(tag_set=tag_set, tag=item_tag)
                created_items.append(tag_code)
    
            if errors:
                return Response({
                    "message": "Partial success. Some tags could not be added.",
                    "errors": errors,
                    "created_items": created_items,
                    "tag_set_id": tag_set.id
                }, status=status.HTTP_207_MULTI_STATUS)
    
            return Response({
                "message": "Tag set items added successfully.",
                "created_items": created_items,
                "tag_set_id": tag_set.id
            }, status=status.HTTP_201_CREATED)
    
    # def post(self, request, *args, **kwargs):
        # item_ids = []
        # for item_id in request.data['set_items']:
        #     item_ids.append(item_id['tag_code'])
        # if ErpTagSetItems.objects.filter(tag=request.data['tag']).exists():
        #     return Response({"message": "The main Tag is already in set."}, status=status.HTTP_400_BAD_REQUEST)
        # elif (ErpTagSet.objects.filter(tag__in=item_ids).exists()):
        #     return Response({"message": "The tags are already in set."}, status=status.HTTP_400_BAD_REQUEST)
        # item_ids = []
        # for item_id in request.data['set_items']:
        #     item_ids.append(item_id['tag'])
        # if ErpTagSetItems.objects.filter(tag=request.data['tag']).exists():
        #     return Response({"message": "The main Tag is already in set."}, status=status.HTTP_400_BAD_REQUEST)
        # elif (ErpTagSet.objects.filter(tag__in=item_ids).exists()):
        #     return Response({"message": "The tags are already in set."}, status=status.HTTP_400_BAD_REQUEST)
        # else:
        #     with transaction.atomic():
        #         set_items = request.data['set_items']
        #         del request.data['set_items']
        #         request.data.update({
        #             "date":date.today(),
        #             "created_by":request.user.id,
        #             "set_no":self.generate_set_no()
        #         })
        #         serializer = ErpTagSetSerializer(data=request.data)
        #         serializer.is_valid(raise_exception=True)
        #         serializer.save()
        #         for items in set_items:
        #             items.update({
        #                 "tag_set":serializer.data['id']
        #             })
        #             item_serializer = ErpTagSetItemsSerializer(data=items)
        #             item_serializer.is_valid(raise_exception=True)
        #             item_serializer.save()
        #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get(self, request, *args, **kwargs):
        queryset = ErpTagSet.objects.all()
        serializer = ErpTagSetSerializer(queryset, many=True)
        output = []
        for data in serializer.data:
            instance = {}
            item_data = []
            tag_items = ErpTagSetItems.objects.filter(tag_set=data['id'])
            tag_items_serializer = ErpTagSetItemsSerializer(tag_items, many=True)
            for item in tag_items_serializer.data:
                item_instance = {}
                tag_item_obj = ErpTagging.objects.filter(tag_id=item['tag']['tag_id']).first()
                tag_item_obj_serializer = ErpTaggingSerializer(tag_item_obj)
                if(ErpTaggingImages.objects.filter(erp_tag=item['tag']['tag_id']).exists()):
                    tag_image_query = ErpTaggingImages.objects.filter(erp_tag=item['tag']['tag_id'])
                    tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                    item_instance.update({'tag_images':tag_image_serializer.data})
                else:
                    tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag'])
                    tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                    item_instance.update({'tag_images':tag_image_serializer.data})
                item_instance.update({
                    **tag_item_obj_serializer.data
                })
                if(item_instance not in item_data):
                    item_data.append(item_instance)
            tag_obj = ErpTagging.objects.filter(tag_id=data['tag']).first()
            tag_obj_serializer = ErpTaggingSerializer(tag_obj)
            if(ErpTaggingImages.objects.filter(erp_tag=data['tag']).exists()):
                main_tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag'])
                main_tag_image_serializer = ErpTaggingImagesSerializer(main_tag_image_query, many=True, context={'request':request})
                instance.update({'tag_images':main_tag_image_serializer.data})
                if(ErpTaggingImages.objects.filter(erp_tag=data['tag'], is_default=True).exists()):
                    default_tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag'],is_default=True).first()
                    default_tag_image_serializer = ErpTaggingImagesSerializer(default_tag_image_query, context={'request':request})
                    instance.update({'default_tag_image':default_tag_image_serializer.data})
                else:
                    instance.update({'default_tag_image':main_tag_image_serializer.data[0]})
            else:
                instance.update({'default_tag_image':None})
            instance.update({
                "set_no":data['set_no'],
                "set_name":data['set_name'],
                "tag_set_items": item_data,
                **tag_obj_serializer.data
                })
            if instance not in output:
                output.append(instance)
        return Response(output, status=status.HTTP_200_OK)

class ErpRemoveTagSetDetailView(generics.GenericAPIView):

    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):

        tag_id = request.query_params.get('tag_id')
        if not ErpTagSetItems.objects.filter(tag = tag_id).exists():
            return Response({"status" : False,"message" : "Tag Details not found.." } , status=status.HTTP_200_OK)
        else:
            ErpTagSetItems.objects.filter(tag = tag_id).delete()
            return Response({"status" : True , "message" : "Tag Removed Successfully.."} ,  status=status.HTTP_200_OK)

class ErpTagWithOutImages(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        queryset = ErpTagging.objects.annotate(
            image_count=Count('erptaggingimages')
        ).filter(image_count=0)
        
        tag_serializer = ErpTaggingSerializer(queryset, many=True)

        response_data = []
        for item in tag_serializer.data:
            result = {
                "tag_id": item["tag_id"],
                "tag_code": item["old_tag_code"],
                "product_name": item['product_name'],
                "gross_wt": item['tag_gwt'],
                "net_wt": item['tag_nwt'],
            }
            if result not in response_data:
                response_data.append(result)

        return Response({"status": True, "data": response_data}, status=status.HTTP_200_OK)

class ErpTagWithImages(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        queryset = ErpTagging.objects.annotate(
            image_count=Count('erptaggingimages')
        ).filter(
            image_count__gt=0,
            tag_status=1
        ).prefetch_related('erptaggingimages')

        tag_serializer = ErpTaggingSerializer(queryset, many=True)

        response_data = []
        for item in queryset:
            result = {
                "tag_id": item.tag_id,
                "tag_code": item.tag_code,
                "old_tag_code": item.old_tag_code,
                "product_name": item.tag_product_id.product_name,
                "gross_wt": item.tag_gwt,
                "net_wt": item.tag_nwt,
                "images": [
                    request.build_absolute_uri(image.tag_image.url)
                    for image in item.erptaggingimages.all()
                ]
            }
            if result not in response_data:
                response_data.append(result)

        return Response({"status": True, "data": response_data}, status=status.HTTP_200_OK)

# Lot Merge
class LotBalanceDetailView(generics.GenericAPIView):

    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):

        lot_id = request.data.get('lot_id')
        split_codes = lot_id.split("-")
        lot_code = split_codes[0]
        item_code = split_codes[1]
        lot_balance = ErpLotCreateAPIView()
        with connection.cursor() as cursor:
            # Here need to pass lot code and item code
            sql = lot_balance.lot_balance_query('' , lot_code , item_code)  
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
            return_data = []
            for item in response_data:
                result ={}
                if item['blc_pcs']>0:
                    result.update(item)
                if item not in return_data:
                    return_data.append(item)
            if len(return_data) > 0 :
                return Response({"data" : return_data },status=status.HTTP_201_CREATED)
            else:
                return Response({"data" : [] ,"status" : False , "message" :"No Record Found.." },status=status.HTTP_201_CREATED)

class LotMergeDetail(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):        
        lot_id = request.query_params.get('lot_id')
        split_codes = lot_id.split("-")
        lot_code = split_codes[0]
        item_code = split_codes[1]
        lot_balance = ErpLotCreateAPIView()
        with connection.cursor() as cursor:
            sql = lot_balance.lot_balance_query(lot_id , lot_code , item_code)
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
            return_data = []
            for item in response_data:
                result ={}
                if item['blc_pcs']>0:
                    result.update(item)
                if item not in return_data:
                    return_data.append(item)
            if len(return_data) > 0 :
                return Response({"data" : return_data },status=status.HTTP_201_CREATED)
            else:
                return Response({"data" : [] ,"status" : False , "message" :"No Record Found.." },status=status.HTTP_201_CREATED)

            

    def generate_ref_code(self, data):
        code = ''
        last_code=None
        last_code=ErpLotMerge.objects.filter(id_branch=data['id_branch']).order_by('-id').first()

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
                issue_data = request.data
                merge_details = request.data.get('merge_details')
                if not issue_data:
                    return Response({"error": "Issue data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not merge_details:
                    return Response({"error": "Lot Merge Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(issue_data['id_branch'])
                ref_no = self.generate_ref_code(issue_data)
                issue_data.update({
                    "entry_date":entry_date,
                    "ref_no":ref_no,
                    "created_by": request.user.id
                })
                issue_serializer = ErpLotMergeSerializer(data = issue_data)
                if issue_serializer.is_valid(raise_exception=True):
                    if issue_serializer.save():
                        lot_gross_weight = 0
                        for item in merge_details:
                            lot_gross_weight += float(item['merge_gwt'])
                            item.update({
                                "lot_merge":issue_serializer.data["id"],
                                "pieces" : item['merge_pcs'],
                                "gross_wt" : item['merge_gwt'],
                            })
                            issue_detail_serializer = ErpLotMergeDetailsSerializer(data=item)
                            if(issue_detail_serializer.is_valid(raise_exception=True)):
                                issue_detail_serializer.save()
                        branch=Branch.objects.get(id_branch = issue_data['id_branch'])
                        fy=FinancialYear.objects.get(fin_status=True)
                        fin_id = fy.fin_id
                        lot_code = generate_lot_code(issue_data,branch.short_name,fy)
                        lot_data = {
                            "id_supplier" : issue_data['id_supplier'],
                            "lot_date":entry_date,
                            "lot_code":lot_code,
                            "fin_year":fin_id,
                            "id_branch" : issue_data['id_branch'],
                            "created_by": request.user.id,
                            "lot_type" : 5
                        }
                        lot_serializer = ErpLotInwardSerializer(data = lot_data)
                        if lot_serializer.is_valid(raise_exception=True):
                            lot_serializer.save()
                            lot_details = {
                                "id_product" : issue_data['id_product'],
                                "id_design" : issue_data['id_design'],
                                "pieces" : issue_data['noOfPcs'],
                                "gross_wt" : lot_gross_weight,
                                "net_wt" : lot_gross_weight,
                                "less_wt" : 0,
                                "stone_wt" : 0,
                                "sell_rate" : 0,
                                "dia_wt" : 0,
                                "stone_details" : []
                            }
                            non_tag_settings = RetailSettings.objects.get(name='non_tag_inward_settings').value
                            lot_details_view = LotDetailsView()
                            lot_details_view.insert_lot_details(lot_details,lot_serializer.data['lot_no'],issue_data['id_branch'],request,non_tag_settings)
                        return Response({"message":"Lot Merged Successfully.",'pdf_url': '','lot_no' : lot_serializer.data['lot_no'],"ref_no":issue_serializer.data['ref_no'],"pdf_path":"inventory/lot/print"}, status=status.HTTP_201_CREATED)
                    return Response({"message":issue_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                return Response({"message":issue_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data":output}, status=status.HTTP_200_OK)
    
class ErpTagSetDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    queryset = ErpTagging.objects.all()
    serializer_class = ErpTaggingSerializer
    
    def get(self, request, *args, **kwargs):
        tag = self.get_object()
        response_data = {
            "original_tag": ErpTaggingSerializer(tag).data,
            "related_items": [],
            "parent_tag": None,
        }
        
        if(ErpTaggingImages.objects.filter(erp_tag=response_data['original_tag']['tag_id']).exists()):
            org_tag_image_query = ErpTaggingImages.objects.filter(erp_tag=response_data['original_tag']['tag_id'])
            org_tag_image_serializer = ErpTaggingImagesSerializer(org_tag_image_query, many=True, context={'request':request})
            response_data['original_tag']['tag_images'] = org_tag_image_serializer.data
            if(ErpTaggingImages.objects.filter(erp_tag=response_data['original_tag']['tag_id'], is_default=True).exists()):
                org_tag_def_image_query = ErpTaggingImages.objects.filter(erp_tag=response_data['original_tag']['tag_id'], is_default=True).first()
                org_tag_def_image_serializer = ErpTaggingImagesSerializer(org_tag_def_image_query, context={'request':request})
                response_data['original_tag']['default_image'] = org_tag_def_image_serializer.data
            else:
                response_data['original_tag']['default_image'] = org_tag_image_serializer.data[0]
        else:
            response_data['original_tag']['default_image'] = None
            response_data['original_tag']['tag_images'] = []
            
        try:
            tag_set = getattr(tag, "tag_set_tag_id", None)
            if tag_set:
                related_items = ErpTagSetItems.objects.filter(
                    tag_set=tag_set
                ).exclude(tag=tag)
                response_data["related_items"] = ErpTagSetItemsSerializer(related_items, many=True).data

            else:
                tag_set_item = getattr(tag, "tag_set_item_tag_id", None)
                if tag_set_item:
                    tag_set = tag_set_item.tag_set
                    related_items = list(
                        ErpTagSetItems.objects.filter(tag_set=tag_set).exclude(tag=tag)
                    )
                    
                    parent_tag = tag_set.tag
                    response_data["parent_tag"] = ErpTaggingSerializer(parent_tag).data
                    
                    if parent_tag != tag: 
                        from collections import namedtuple
                        FakeItem = namedtuple("FakeItem", ["id", "tag", "tag_set"])
                        parent_item = FakeItem(id=None, tag=parent_tag, tag_set=tag_set)
                        related_items.insert(0, parent_item) 
                    response_data["related_items"] = ErpTagSetItemsSerializer(related_items, many=True).data
                    
                    for data in response_data["related_items"]:
                        if(ErpTaggingImages.objects.filter(erp_tag=data['tag']['tag_id']).exists()):
                            tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag']['tag_id'])
                            tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                            data['tag']['tag_images'] = tag_image_serializer.data
                            if(ErpTaggingImages.objects.filter(erp_tag=data['tag']['tag_id'], is_default=True).exists()):
                                tag_def_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag']['tag_id'], is_default=True).first()
                                tag_def_image_serializer = ErpTaggingImagesSerializer(tag_def_image_query, context={'request':request})
                                data['tag']['default_image'] = tag_def_image_serializer.data
                            else:
                                data['tag']['default_image'] = tag_image_serializer.data[0]
                        elif(ErpTaggingImages.objects.filter(erp_tag=response_data["parent_tag"]['tag_id']).exists()):
                            tag_image_query = ErpTaggingImages.objects.filter(erp_tag=response_data["parent_tag"]['tag_id'])
                            tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                            data['tag']['tag_images'] = tag_image_serializer.data
                            if(ErpTaggingImages.objects.filter(erp_tag=response_data["parent_tag"]['tag_id'], is_default=True).exists()):
                                tag_def_image_query = ErpTaggingImages.objects.filter(erp_tag=response_data["parent_tag"]['tag_id'], is_default=True).first()
                                tag_def_image_serializer = ErpTaggingImagesSerializer(tag_def_image_query, context={'request':request})
                                data['tag']['default_image'] = tag_def_image_serializer.data
                            else:
                                data['tag']['default_image'] = tag_image_serializer.data[0]
                        else:
                            data['tag']['tag_images'] = []
                            data['tag']['default_image'] = None

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data":response_data}, status=status.HTTP_200_OK)
    
    # def get(self, request, *args, **kwargs):
    #     if(ErpTagSet.objects.filter(id=kwargs['pk']).exists()):
    #         queryset = self.get_object()
    #         serializer = ErpTagSetSerializer(queryset)
    #         output = serializer.data
    #         item_data = []
    #         tag_items = ErpTagSetItems.objects.filter(tag_set=queryset.id)
    #         tag_items_serializer = ErpTagSetItemsSerializer(tag_items, many=True)
    #         for item in tag_items_serializer.data:
    #             item_instance = {}
    #             tag_item_obj = ErpTagging.objects.filter(tag_id=item['tag']).first()
    #             tag_item_obj_serializer = ErpTaggingSerializer(tag_item_obj)
    #             if(ErpTaggingImages.objects.filter(erp_tag=item['tag']).exists()):
    #                 tag_image_query = ErpTaggingImages.objects.filter(erp_tag=item['tag'])
    #                 tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
    #                 item_instance.update({'tag_images':tag_image_serializer.data})
    #             else:
    #                 tag_image_query = ErpTaggingImages.objects.filter(erp_tag=serializer.data['tag'])
    #                 tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
    #                 item_instance.update({'tag_images':tag_image_serializer.data})
    #             item_instance.update({
    #                 **tag_item_obj_serializer.data
    #             })
    #             if(item_instance not in item_data):
    #                 item_data.append(item_instance)
    #         tag_obj = ErpTagging.objects.filter(tag_id=serializer.data['tag']).first()
    #         tag_obj_serializer = ErpTaggingSerializer(tag_obj)
    #         if(ErpTaggingImages.objects.filter(erp_tag=serializer.data['tag']).exists()):
    #             main_tag_image_query = ErpTaggingImages.objects.filter(erp_tag=serializer.data['tag'])
    #             main_tag_image_serializer = ErpTaggingImagesSerializer(main_tag_image_query, many=True, context={'request':request})
    #             output.update({'tag_images':main_tag_image_serializer.data})
    #             if(ErpTaggingImages.objects.filter(erp_tag=serializer.data['tag'], is_default=True).exists()):
    #                 default_tag_image_query = ErpTaggingImages.objects.filter(erp_tag=serializer.data['tag'],is_default=True).first()
    #                 default_tag_image_serializer = ErpTaggingImagesSerializer(default_tag_image_query, context={'request':request})
    #                 output.update({'default_tag_image':default_tag_image_serializer.data})
    #             else:
    #                 output.update({'default_tag_image':main_tag_image_serializer.data[0]})
    #         else:
    #             output.update({'default_tag_image':None})
    #         output.update({
    #             "tag_set_items": item_data,
    #             **tag_obj_serializer.data
    #             })
    #         return Response({"data":output}, status=status.HTTP_200_OK)
    #     else:
    #         return Response({"status":False,"message": "Tag set not found"}, status=status.HTTP_400_BAD_REQUEST)
        

# class ErpTagSetSearchView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsEmployee]
#     queryset = ErpTagSet.objects.all()
#     serializer_class = ErpTagSetSerializer

#     def post(self, request, *args, **kwargs):
#         tag_code = request.data.get('tag_code')
#         old_tag_code = request.data.get('old_tag_code')
        
#         if not tag_code and not old_tag_code:
#             return Response({"message": "Tag code is required"}, status=status.HTTP_400_BAD_REQUEST)
#         try:
#             if(tag_code):
#                 queryset = ErpTagging.objects.filter(old_tag_code__icontains=tag_code,tag_status = 1).get()
#             else:
#                 queryset = ErpTagging.objects.filter(old_tag_code__icontains=old_tag_code,tag_status = 1).get()
            
#             # output = {}
#             if(ErpTagSet.objects.filter(tag=queryset.pk).exists()):
#                 set_queryset = ErpTagSet.objects.filter(tag=queryset.pk)
#                 set_serializer = ErpTagSetSerializer(set_queryset, many=True)
#                 output = []
#                 for data in set_serializer.data:
#                     instance = {}
#                     item_data = []
#                     tag_items = ErpTagSetItems.objects.filter(tag_set=data['id'])
#                     tag_items_serializer = ErpTagSetItemsSerializer(tag_items, many=True)
#                     for item in tag_items_serializer.data:
#                         item_instance = {}
#                         tag_item_obj = ErpTagging.objects.filter(tag_id=item['tag']).first()
#                         tag_item_obj_serializer = ErpTaggingSerializer(tag_item_obj)
#                         if(ErpTaggingImages.objects.filter(erp_tag=item['tag']).exists()):
#                             tag_image_query = ErpTaggingImages.objects.filter(erp_tag=item['tag'])
#                             tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
#                             item_instance.update({'tag_images':tag_image_serializer.data})
#                         else:
#                             tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag'])
#                             tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
#                             item_instance.update({'tag_images':tag_image_serializer.data})
#                         item_instance.update({
#                             **tag_item_obj_serializer.data
#                         })
#                         if(item_instance not in item_data):
#                             item_data.append(item_instance)
#                     tag_obj = ErpTagging.objects.filter(tag_id=data['tag']).first()
#                     tag_obj_serializer = ErpTaggingSerializer(tag_obj)
#                     if(ErpTaggingImages.objects.filter(erp_tag=data['tag']).exists()):
#                         main_tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag'])
#                         main_tag_image_serializer = ErpTaggingImagesSerializer(main_tag_image_query, many=True, context={'request':request})
#                         instance.update({'tag_images':main_tag_image_serializer.data})
#                         if(ErpTaggingImages.objects.filter(erp_tag=data['tag'], is_default=True).exists()):
#                             default_tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag'],is_default=True).first()
#                             default_tag_image_serializer = ErpTaggingImagesSerializer(default_tag_image_query, context={'request':request})
#                             instance.update({'default_tag_image':default_tag_image_serializer.data})
#                         else:
#                             instance.update({'default_tag_image':main_tag_image_serializer.data[0]})
#                     else:
#                         instance.update({'default_tag_image':None})
#                     instance.update({
#                         "set_no":data['set_no'],
#                         "set_name":data['set_name'],
#                         "tag_set_items": item_data,
#                         **tag_obj_serializer.data
#                         })
#                     if instance not in output:
#                         output.append(instance)
#         except ErpTagSet.DoesNotExist:
#             return Response({"message": "Tag not found"}, status=status.HTTP_400_BAD_REQUEST)


class TagImagePrintPDFView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    @staticmethod
    def link_callback(uri, rel):
        """
        Convert HTML URIs to absolute system paths so xhtml2pdf can access them
        """
        if uri.startswith(settings.MEDIA_URL):
            path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        elif uri.startswith(settings.STATIC_URL):
            path = finders.find(uri.replace(settings.STATIC_URL, ""))
        else:
            return uri
        return path

    def post(self, request, *args, **kwargs):
        tag_data = request.data
        if not isinstance(tag_data, list) or not tag_data:
            return Response({"detail": "Request body must be a non-empty list of objects with 'tag_id'"}, status=400)
        serialized_images = []
        for item in tag_data:
            tag_id = item.get("tag_id")
            if not tag_id:
                continue
            try:
                tag = ErpTagging.objects.get(tag_id=tag_id)
                tag_images = ErpTaggingImages.objects.filter(erp_tag=tag)
                for img in tag_images:
                    image_path = os.path.join(settings.MEDIA_URL, img.tag_image.name)
                    serialized_images.append({
                        "image": image_path,
                        "tag_code": tag.tag_code,
                        "tag_gwt": f"{tag.tag_gwt:.3f}",
                        "tag_nwt": f"{tag.tag_nwt:.3f}",
                    })
            except ErpTagging.DoesNotExist:
                continue
        if not serialized_images:
            return Response({"detail": "No valid tag data found."}, status=404)
        
        # Render HTML
        context = {"tags": serialized_images}
        template = get_template('tag_image_print.html')
        html = template.render(context)
        result = io.BytesIO()
        pisa_status = pisa.pisaDocument(io.StringIO(html), result, link_callback=self.link_callback)
        if pisa_status.err:
            return Response({"detail": "PDF generation failed."}, status=500)
        # Save PDF
        save_path = os.path.join(settings.MEDIA_ROOT, 'tag_prints', 'batch')
        os.makedirs(save_path, exist_ok=True)
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        pdf_filename = f'tag_image_print_{timestamp}.pdf'
        pdf_file_path = os.path.join(save_path, pdf_filename)
        with open(pdf_file_path, 'wb') as pdf_file:
            pdf_file.write(result.getvalue())
        # Build URL to access the file
        pdf_url = request.build_absolute_uri(
            os.path.join(settings.MEDIA_URL, 'tag_prints', 'batch', pdf_filename)
        )
        return Response({"pdf_url": pdf_url}, status=200)
