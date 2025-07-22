from django.shortcuts import render
from django.db import IntegrityError, transaction
from django.http import HttpResponse, request, Http404
from rest_framework import generics, permissions, status
from django.core.exceptions import ValidationError
from django.utils.timezone import utc
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone
from django.forms.models import model_to_dict
from rest_framework.response import Response
from django.core.paginator import Paginator
# Adjust import path
from utilities.utils import format_date, date_format_with_time, format_number_with_decimal
from utilities.pagination_mixin import PaginationMixin
from cryptography.fernet import Fernet
import os
import subprocess
from django.db import connection
import base64
import threading
import time
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
import qrcode
from django.conf import settings
from PIL import Image
from django.db.models import Count, OuterRef, Subquery
from django.core.files.images import ImageFile
from babel.numbers import get_currency_symbol
from django.core.exceptions import ObjectDoesNotExist
import io
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee, isSuperuser, IsSuperuserOrEmployee
from datetime import datetime, timedelta, date
from django.db.models import Q, ProtectedError
from utilities.constants import (FILTERS, SERVICE_OPTIONS)
import re
from django.db.models import Sum
from managescheme.models import (SchemeAccount)
from django.utils.timezone import now

from retailsettings.models import (RetailSettings)
from .models import (OtherInventoryCategory, OtherInventorySize, OtherInventoryItem, OtherInventoryPurchaseEntry,
                     OtherInventoryPurchaseEntryDetails, OtherInventoryPurchaseIssueLogs, OtherInventoryItemIssue,OtherInventoryItemReOrder,ProductItemMapping)
from .serializers import (OtherInventoryCategorySerializer, OtherInventorySizeSerializer, OtherInventoryItemSerializer,
                          OtherInventoryPurchaseEntrySerializer, OtherInventoryPurchaseEntryDetailsSerializer, OtherInventoryPurchaseLogsSerializer,
                          OtherInventoryItemIssueSerializer, OtherInventoryPurchaseLogsSerializer,OtherInventoryItemReOrderSerializer,ProductItemMappingSerializer)
from retailmasters.views import BranchEntryDate
from retailmasters.models import (Branch, FinancialYear, Company)
from employees.models import (Employee)
from customers.models import (Customers)
from .constants import (OTHER_INVENTORY_SIZE_ACTION_LIST, OTHER_INVENTORY_ITEM_COLUMN_LIST, OTHER_INVENTORY_ITEM_ACTION_LIST,
                        OTHER_INVENTORY_SIZE_COLUMN_LIST, OTHER_INVENTORY_CATEGORY_COLUMN_LIST, OTHER_INVENTORY_CATEGORY_ACTION_LIST,
                        PURCHASE_ENTRY_COLUMN_LIST, PURCHASE_ENTRY_ACTION_LIST, OTHER_INVENTORY_ITEM_ISSUE_COLUMN_LIST, OTHER_INVENTORY_ITEM_ISSUE_ACTION_LIST,

                        ITEM_LOG_COLUMN_LIST, ITEM_LOG_ACTION_LIST,ITEM_LOG_COLUMN_LIST, ITEM_LOG_ACTION_LIST, PURCHASE_REPORT_ACTION_LIST, PURCHASE_REPORT_COLUMN_LIST,
                        ISSUE_REPORT_COLUMN_LIST, ISSUE_REPORT_ACTION_LIST)

    
from django.db.models import Prefetch

from retailcataloguemasters.models import (
    Product,
)

                        

fernet = Fernet(os.getenv('crypt_key'))

pagination = PaginationMixin()


class OtherInventoryCategoryListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = OtherInventoryCategory.objects.all()
    serializer_class = OtherInventoryCategorySerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = OtherInventoryCategory.objects.all()
            serializer = OtherInventoryCategorySerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,OTHER_INVENTORY_CATEGORY_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):

            if (data['cat_type'] == 1):
                data.update({"cat_type": "Chit Gift"})
            elif (data['cat_type'] == 2):
                data.update({"cat_type": "Packing Items"})
            elif (data['cat_type'] == 3):
                data.update({"cat_type": "Retail Sales Gift"})
            else:
                data.update({"cat_type": "Others"})

            data.update({"pk_id": data['id'],
                        'sno': index+1})
        filters_copy = FILTERS.copy()
        context = {
            'columns': OTHER_INVENTORY_CATEGORY_COLUMN_LIST,
            'actions': OTHER_INVENTORY_CATEGORY_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = OtherInventoryCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OtherInventoryCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = OtherInventoryCategory.objects.all()
    serializer_class = OtherInventoryCategorySerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Category status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = OtherInventoryCategorySerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = OtherInventoryCategorySerializer(
            queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Category instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OtherInventorySizeListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = OtherInventorySize.objects.all()
    serializer_class = OtherInventorySizeSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = OtherInventorySize.objects.all()
            serializer = OtherInventorySizeSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,OTHER_INVENTORY_SIZE_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id'],
                        'sno': index+1, "is_active": data['active']})
        filters_copy = FILTERS.copy()
        context = {
            'columns': OTHER_INVENTORY_SIZE_COLUMN_LIST,
            'actions': OTHER_INVENTORY_SIZE_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = OtherInventorySizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OtherInventorySizeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = OtherInventorySize.objects.all()
    serializer_class = OtherInventorySizeSerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.active == True):
                obj.active = False
            else:
                obj.active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Size status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = OtherInventorySizeSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = OtherInventorySizeSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Size instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OtherInventoryItemListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    queryset = OtherInventoryItem.objects.prefetch_related(
        Prefetch('otherinventoryitemreorder_set', queryset=OtherInventoryItemReOrder.objects.all())
    ).order_by('-created_on')

    serializer_class = OtherInventoryItemSerializer

    def get(self, request, *args, **kwargs):
        
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,OTHER_INVENTORY_ITEM_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)

        for index, data in enumerate(serializer.data):
            category = OtherInventoryCategory.objects.filter(id=data['category']).first()
            data.update({"pk_id": data['id'], 'sno': index + 1, "category_cat_type": category.cat_type})

        filters_copy = FILTERS.copy()
        context = {
            'columns': OTHER_INVENTORY_ITEM_COLUMN_LIST,
            'actions': OTHER_INVENTORY_ITEM_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        with transaction.atomic(): 
            request.data.update({"created_by": request.user.id})
            serializer = OtherInventoryItemSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            item = serializer.save(created_by=request.user)

            if "reOrderSetting" in request.data:
                for reorder_data in request.data["reOrderSetting"]:
                    reorder_data["item"] = item.id 
                    reorder_serializer = OtherInventoryItemReOrderSerializer(data=reorder_data)
                    reorder_serializer.is_valid(raise_exception=True)
                    reorder_serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)



class OtherInventoryItemDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = OtherInventoryItem.objects.all()
    serializer_class = OtherInventoryItemSerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        serializer = OtherInventoryItemSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = OtherInventoryItemSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Item instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


def create_inventory_logs_of_purchase_issue(item_id, branch, pieces, ref_id, trans_type):
    instance = {}
    if(trans_type==1):
        instance.update({"status":1, "to_branch":branch, "item":item_id, "ref_id":ref_id,
                         "pieces":pieces})
    if(trans_type==2):
        instance.update({"status":2, "from_branch":branch, "item":item_id, "ref_id":ref_id,
                         "pieces":pieces})
    log_serializer = OtherInventoryPurchaseLogsSerializer(data=instance)
    log_serializer.is_valid(raise_exception = True)
    log_serializer.save()

class OtherInventoryPurchaseCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = OtherInventoryPurchaseEntry.objects.all()
    serializer_class = OtherInventoryPurchaseEntrySerializer

    def generate_ref_code(self, data, branch_code, fy, setting_bill_type):
        code = ''
        code_settings = RetailSettings.objects.get(
            name='purchase_entry_code_settings').value
        code_format = RetailSettings.objects.get(
            name='purchase_entry_code_format').value
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_code = None
        if code_settings == '0':  # GENERATE CODE
            last_code = OtherInventoryPurchaseEntry.objects.filter(
                setting_bill_type=setting_bill_type).order_by('-id').first()
        elif code_settings == '1':  # GENERATE CODE WITH FY AND BRANCH
            last_code = OtherInventoryPurchaseEntry.objects.filter(
                setting_bill_type=setting_bill_type, branch=data['branch'], fin_year=fin_id).order_by('-id').first()
        elif code_settings == '2':  # GENERATE CODE WITH BRANCH
            last_code = OtherInventoryPurchaseEntry.objects.filter(
                setting_bill_type=setting_bill_type, branch=data['branch']).order_by('-id').first()
        elif code_settings == '3':  # GENERATE CODE WITH FY
            last_code = OtherInventoryPurchaseEntry.objects.filter(
                setting_bill_type=setting_bill_type, fin_year=fin_id).order_by('-id').first()
        if last_code:
            last_code = last_code.ref_no
            match = re.search(r'(\d{5})$', last_code)
            if match:
                code = match.group(1)
                code = str(int(code) + 1).zfill(5)
            else:
                code = '00001'
        else:
            code = '00001'

        # code=code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code)

        return code

    def generate_print(self, id_purchase_entry, request):
        instance = OtherInventoryPurchaseEntry.objects.get(
            id=id_purchase_entry)
        serializer = OtherInventoryPurchaseEntrySerializer(instance)
        data = serializer.data
        item_details = OtherInventoryPurchaseEntryDetails.objects.filter(
            purchase_entry=id_purchase_entry)
        item_details_serializer = OtherInventoryPurchaseEntryDetailsSerializer(
            item_details, many=True)
        comp = Company.objects.latest("id_company")
        purchase_amount, total_pcs = 0, 0
        for item in item_details_serializer.data:
            total_pcs += int(item['pieces'])
            purchase_amount += float(item['total_amount'])

        data['total_pcs'] = format(total_pcs, '.0f')
        data['purchase_amount'] = format(purchase_amount, '.3f')
        data.update({"supplier_name": instance.supplier.supplier_name, "branch": instance.branch.name,
                    "item_details": item_details_serializer.data, 'company_detail': comp})

        save_dir = os.path.join(settings.MEDIA_ROOT,
                                'other_inventory_purchase_entry')
        save_dir = os.path.join(save_dir, f'{id_purchase_entry}')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        template = get_template('other_inventory_purchase_entry_print.html')
        html = template.render(data)
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        pdf_path = os.path.join(save_dir, 'other_inventory_purchase_entry.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        pdf_path = request.build_absolute_uri(
            settings.MEDIA_URL + f'other_inventory_purchase_entry/{id_purchase_entry}/other_inventory_purchase_entry.pdf')
        return pdf_path

    def post(self, request, *args, **kwargs):
        purchase_entry_details = request.data['purchase_entry_details']
        del request.data['purchase_entry_details']
        try:
            with transaction.atomic():
                if not len(purchase_entry_details) > 0:
                    return Response({"error": "Purchase Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(request.data['branch'])
                branch = Branch.objects.get(id_branch=request.data['branch'])
                fy = FinancialYear.objects.get(fin_status=True)
                bill_setting_type = int(
                    request.data.get('setting_bill_type', 1))
                fin_id = fy.fin_id
                ref_no = self.generate_ref_code(
                    request.data, branch.short_name, fy, bill_setting_type)
                request.data.update({"entry_date": entry_date, "ref_no": ref_no, "fin_year": fin_id,
                                     "created_by": request.user.id})
                purchase_serializer = OtherInventoryPurchaseEntrySerializer(
                    data=request.data)
                if purchase_serializer.is_valid(raise_exception=True):
                    purchase_serializer.save()
                    for detail_data in purchase_entry_details:
                        detail_data.update(
                            {"purchase_entry": purchase_serializer.data['id']})
                        purchase_detail_serializer = OtherInventoryPurchaseEntryDetailsSerializer(
                            data=detail_data)
                        purchase_detail_serializer.is_valid(
                            raise_exception=True)
                        purchase_detail_serializer.save()

                        create_inventory_logs_of_purchase_issue(ref_id=purchase_serializer.data['id'], branch=request.data['branch'],
                                                            trans_type=1, item_id=detail_data['item'], pieces=detail_data['pieces'])


                    purchase_print_url = self.generate_print(
                        purchase_serializer.data['id'], request)
                return Response({"message": "Purchase Entry Created Successfully.", 'pdf_url': purchase_print_url,
                                 "id": purchase_serializer.data['id'], "pdf_path": "other_inventory/purchase_entry/print"}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": f"A database error occurred:{e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        id_purchase_entry = self.kwargs.get('pk')
        est_url = self.generate_print(id_purchase_entry, request)
        response_data = {'pdf_url': est_url}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)


class OtherInventoryPurchaseEntryListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_branch = request.data.get('branch')
        id_branch = (id_branch) if id_branch != '' else 0
        bill_setting_type = int(request.data.get('bill_setting_type', 2))

        code_format = RetailSettings.objects.get(
            name='purchase_entry_code_format').value

        lists = OtherInventoryPurchaseEntry.objects.select_related('supplier', 'branch').annotate(
            total_pcs=Sum('other_inventory_purchase_details__pieces'),
            total_cost=Sum('other_inventory_purchase_details__total_amount'),
        ).values(
            'id',
            'ref_no',
            'branch__short_name',
            'fin_year__fin_year_code',
            'total_pcs',
            'total_cost',
            'entry_date',
            'supplier__supplier_name',
            'branch__name',
            'bill_status'
        )
        if from_date and to_date:
            lists = lists.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            lists = lists.filter(branch__in=id_branch)
        if bill_setting_type == 0 or bill_setting_type == 1:
            lists = lists.filter(setting_bill_type=bill_setting_type)

        paginator, page = pagination.paginate_queryset(lists, request,None,PURCHASE_ENTRY_COLUMN_LIST)

        for index, purchase in enumerate(page):
            code = (code_format
                    .replace('@branch_code@',  purchase['branch__short_name'])
                    .replace('@code@', purchase['ref_no'])
                    .replace('@fy_code@', purchase['fin_year__fin_year_code']))
            purchase['sno'] = index+1
            purchase['pk_id'] = purchase['id']
            purchase['ref_code'] = code
            purchase['status_name'] = (
                'Success' if purchase['bill_status'] == 1 else 'Cancelled')
            # purchase['is_editable'] = (1 if purchase['bill_status']==1 else 0)
            purchase['entry_date'] = format_date(purchase['entry_date'])
            purchase['total_pcs'] = format(purchase['total_pcs'], '.0f')
            purchase['total_cost'] = format(purchase['total_cost'], '.2f')
            purchase['is_cancelable'] = (
                True if purchase['bill_status'] == 1 else False)

        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        context = {
            'columns': PURCHASE_ENTRY_COLUMN_LIST,
            'actions': PURCHASE_ENTRY_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': FILTERS
        }
        return pagination.paginated_response(list(page), context)


class OtherInventoryPurchaseEntryCancelView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        queryset = OtherInventoryPurchaseEntry.objects.get(
            id=request.data['pk_id'])
        if (queryset.bill_status == 1):
            queryset.bill_status = 2
            queryset.is_cancelled = True
            queryset.cancelled_by = self.request.user
            queryset.cancelled_on = datetime.now(tz=timezone.utc)
            queryset.cancelled_reason = request.data['cancel_reason']
            queryset.save()
            return Response({"message": "Purchase Entry Cancelled Successfully."}, status=status.HTTP_202_ACCEPTED)
        return Response({"message": "Purchase Entry Cannot Be Cancelled."}, status=status.HTTP_400_BAD_REQUEST)


class OtherInventoryItemIssueListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = OtherInventoryItemIssue.objects.all()
    serializer_class = OtherInventoryItemIssueSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = OtherInventoryItemIssue.objects.all()
            serializer = OtherInventoryItemIssueSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,OTHER_INVENTORY_ITEM_ISSUE_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            br = Branch.objects.get(id_branch=data['branch'])
            sch = SchemeAccount.objects.get(
                id_scheme_account=data['scheme_account'])
            ite = OtherInventoryItem.objects.get(id=data['item'])
            if (data['issue_to'] == 1):
                data.update({"issue_to": "Customer"})
            elif (data['issue_to'] == 2):
                data.update({"issue_to": "Employee"})
            else:
                data.update({"issue_to": "Others"})

            data.update({"pk_id": data['id'],
                        'sno': index+1, "branch": br.name, "scheme_account": sch.account_name,"item": ite.name,
                         'is_cancelable': (True if data['issue_status'] == 1 else False)
                         })
        filters_copy = FILTERS.copy()
        context = {
            'columns': OTHER_INVENTORY_ITEM_ISSUE_COLUMN_LIST,
            'actions': OTHER_INVENTORY_ITEM_ISSUE_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        with transaction.atomic():
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(request.data['branch'])
            request.data.update(
                {"issued_by": request.user.id, "issue_date": entry_date})
            serializer = OtherInventoryItemIssueSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            create_inventory_logs_of_purchase_issue(ref_id=serializer.data['id'], branch=request.data['branch'],
                                                    trans_type=2, item_id=request.data['item'], pieces=request.data['pieces'])
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class OtherInventoryItemIssueCancelView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        queryset = OtherInventoryItemIssue.objects.get(
            id=request.data['pk_id'])
        if (queryset.issue_status == 1):
            queryset.issue_status = 2
            queryset.is_cancelled = True
            queryset.cancelled_by = self.request.user
            queryset.cancelled_on = datetime.now(tz=timezone.utc)
            queryset.cancelled_reason = request.data['cancel_reason']
            queryset.save()
            return Response({"message": "Item Issue Entry Cancelled Successfully."}, status=status.HTTP_202_ACCEPTED)
        return Response({"message": "Item Issue Entry Cannot Be Cancelled."}, status=status.HTTP_400_BAD_REQUEST)

class OtherInventoryLogReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        branch_id = request.data.get('transfer_to')
        start_date = request.data.get('fromDate')
        end_date = request.data.get('toDate')

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        filters = {}
        if start_date and end_date:
            filters["date__range"] = (start_date, end_date)
        if branch_id:
            filters["to_branch_id"] = branch_id 
        
        logs = OtherInventoryPurchaseIssueLogs.objects.filter(**filters)
        # report = {}
        
        initial_opening = {}
        if start_date:
            previous_logs = OtherInventoryPurchaseIssueLogs.objects.filter(
                date__lt=start_date
            )
            if branch_id:
                previous_logs = previous_logs.filter(to_branch_id=branch_id)

            for log in previous_logs:
                item_name = log.item.name
                if item_name not in initial_opening:
                    initial_opening[item_name] = 0
                if log.status == 1:
                    initial_opening[item_name] += log.pieces
                elif log.status == 2:
                    initial_opening[item_name] -= log.pieces

        report = {}
        for log in logs:
            date_str = log.date.strftime("%Y-%m-%d")
            item_name = log.item.name

            if date_str not in report:
                report[date_str] = {}
            if item_name not in report[date_str]:
                report[date_str][item_name] = {"inward_pieces": 0, "outward_pieces": 0}

            if log.status == 1:
                report[date_str][item_name]["inward_pieces"] += log.pieces
            elif log.status == 2:
                report[date_str][item_name]["outward_pieces"] += log.pieces

        sorted_dates = sorted(report.keys())

        item_balance_tracker = initial_opening.copy()
        formatted_report = []

        for date_str in sorted_dates:
            for item, data in report[date_str].items():
                inward = data["inward_pieces"]
                outward = data["outward_pieces"]

                prev_balance = item_balance_tracker.get(item, 0)
                closing_balance = prev_balance + inward - outward

                formatted_report.append({
                    "date": date_str,
                    "item": item,
                    "inward_pieces": inward,
                    "outward_pieces": outward,
                    "opening_balance": prev_balance,
                    "closing_balance": closing_balance,
                })

                item_balance_tracker[item] = closing_balance
        paginator, page = pagination.paginate_queryset(formatted_report, request,None,ITEM_LOG_COLUMN_LIST)
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFromToFilterReq'] = True
    
        context = {
            'columns': ITEM_LOG_COLUMN_LIST,
            'actions': ITEM_LOG_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy
        }
        return pagination.paginated_response(formatted_report, context)
    
class OtherInventoryPurchaseReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        bill_setting_type = int(request.data.get('bill_setting_type',2))
        
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = OtherInventoryPurchaseEntry.objects.all()

            if(id_branch):
                queryset  = queryset.filter(branch__in = id_branch)

            if from_date and to_date:
                queryset = queryset.filter(entry_date__range=[from_date, to_date])

            if  bill_setting_type == 1:
                queryset = queryset.filter(setting_bill_type = 1)
            elif bill_setting_type == 0: 
                queryset = queryset.filter(setting_bill_type = 0)
                
            paginator, page = pagination.paginate_queryset(queryset, request,None,PURCHASE_REPORT_COLUMN_LIST)
            serializer = OtherInventoryPurchaseEntrySerializer(page,many=True)
            response_data=[]

            for index, data in enumerate(serializer.data):
                grouped_items = {}
                purchase_detail = OtherInventoryPurchaseEntryDetails.objects.filter(purchase_entry=data['id'])
                purchase_detail_serializer = OtherInventoryPurchaseEntryDetailsSerializer(purchase_detail, many=True)
                
                for item, detail in zip(purchase_detail_serializer.data, purchase_detail):
                    item_name = detail.item.name
                    if item_name not in grouped_items:
                        grouped_items[item_name] = {"pieces": 0, "total_amount": 0}
                    grouped_items[item_name]["pieces"] += detail.pieces
                    grouped_items[item_name]["total_amount"] += float(detail.total_amount)
                
                for item_name, values in grouped_items.items():
                    new_entry = data.copy()
                    new_entry.update({
                        'sno': index + 1,
                        'date': format_date(data['entry_date']),
                        'item_name': item_name,
                        'pieces': values['pieces'],
                        'total_amount': values['total_amount']
                    })
                    response_data.append(new_entry)
                
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            context={
                'columns':PURCHASE_REPORT_COLUMN_LIST,
                'actions':PURCHASE_REPORT_ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            
            return pagination.paginated_response(response_data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class OtherInventoryIssueReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        # bill_setting_type = int(request.data.get('bill_setting_type',2))
        
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = OtherInventoryItemIssue.objects.all()
            
            if(id_branch):
                queryset  = queryset.filter(branch__in = id_branch)

            if from_date and to_date:
                queryset = queryset.filter(issue_date__range=[from_date, to_date])
            paginator, page = pagination.paginate_queryset(queryset, request,None,ISSUE_REPORT_COLUMN_LIST)
            serializer = OtherInventoryItemIssueSerializer(page,many=True)
            for index, data in enumerate(serializer.data):
                employee = Employee.objects.filter(user=data['issued_by']).first()
                
                if(data['issued_for']==1):
                    data.update({"issued_for":"Against Bill"})
                else:
                    data.update({"issued_for":"Against Chit"})
                    
                if(data['issue_to']==1):
                    customer = Customers.objects.filter(id_customer=data['issue_to_cus']).first()
                    data.update({"recieved_by":"Customer", "reciever_name":customer.firstname})
                elif(data['issue_to']==2):
                    rcv_employee = Employee.objects.filter(user=data['issue_to_emp']).first()
                    data.update({"recieved_by":"Employee", "reciever_name":rcv_employee.firstname})
                else:
                    data.update({"recieved_by":"Others"})
                
                data.update({'sno': index + 1,'date': format_date(data['issue_date']),
                             'issued_by_name':employee.firstname})
            
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            context={
                'columns':ISSUE_REPORT_COLUMN_LIST,
                'actions':ISSUE_REPORT_ACTION_LIST,
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req':True,
                'filters':filters_copy
                }
            return pagination.paginated_response(serializer.data,context) 
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class ItemMappingView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = ProductItemMapping.objects.all()
    serializer_class = ProductItemMappingSerializer

    # GET Item Mapping
    def get(self, request, *args, **kwargs):
        id_product = request.query_params.get('id_product')
        id_item = request.query_params.get('id_item')
        queryset = ProductItemMapping.objects.all()
        # Filter queryset based on id_product if provided
        if id_product:
            queryset = queryset.filter(id_product=id_product)
        # Further filter queryset based on id_item if provided
        if id_item:
            queryset = queryset.filter(id_item=id_item)
        serializer = ProductItemMappingSerializer(queryset, many=True)
        result = []
        for data in serializer.data:
            mapped_object = {}
            product_queryset = Product.objects.filter(
                pro_id=data['id_product'])
            item_queryset = OtherInventoryItem.objects.filter(
                id_item=data['id_item'])
            if (product_queryset.exists() and item_queryset.exists()):
                product = product_queryset.get()
                item = item_queryset.get()
                item_name = item.name
                mapped_object.update({
                    "id_product_mapping": data['id_product_mapping'],
                    "id_product": data['id_product'],
                    "id_design": data['id_item'],
                    "product_name": product.product_name,
                    "item_name": item_name})
                result.append(mapped_object)
        if (len(result) > 0):
            return Response({"message": "List Retrieved Successfully", "data": result}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "No Record Found", "data": result}, status=status.HTTP_201_CREATED)

    # CREATE Design Mapping
    def post(self, request, *args, **kwargs):
        try:
            id_product = request.data.get('id_product')
            id_item = request.data.get('id_item')

            # Check if id_design is an int or list
            if isinstance(id_item, (int, str)):
                id_item_list = [id_item]
            elif isinstance(id_item, list):
                id_item_list = id_item
            else:
                return Response({"detail": "id_item must be an integer or a list."}, status=status.HTTP_400_BAD_REQUEST)

            created_entries = []
            for item in id_item_list:
                data = {
                    "id_product": id_product,
                    "id_item": item,
                }
                serializer = ProductItemMappingSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                created_entries.append(serializer.data)

            return Response({"message": "Item Mapped Successfully."}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Item Mapped can't be deleted, as it is already in Stock"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ItemListView(generics.ListAPIView):
    queryset = OtherInventoryItem.objects.all()
    serializer_class = OtherInventoryItemSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().values("id", "name")
        return Response({"message": "List Retrieved Successfully", "data": list(queryset)}, status=status.HTTP_200_OK)