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

from .models import (Discount,Coupon,GiftVoucher, GiftVoucherIssue, GiftVoucherIssuePaymentDetail)
from .serializers import (DiscountSerializer,CouponSerializer,GiftVoucherSerializer, GiftVoucherIssueSerializer, GiftVoucherIssuePaymentDetailSerializer)
from .constants import (DISCOUNT_ACTION_LIST,DISCOUNT_COLUMN_LIST,COUPON_ACTION_LIST,COUPON_COLUMN_LIST,GIFT_VOUCHER_REPORT_ACTION_LIST,
                        GIFT_VOUCHER_ACTION_LIST,GIFT_VOUCHER_COLUMN_LIST, GIFT_VOUCHER_ISSUE_COLUMN_LIST, GIFT_VOUCHER_ISSUE_ACTION_LIST,GIFT_VOUCHER_REPORT_COLUMN_LIST,SNO_COLUMN)
from retailmasters.models import (Branch, Product, Supplier)
from billing.models import (ErpInvoice)
from employees.models import (Employee)
from customers.models import (Customers)
from retailmasters.models import Supplier

fernet = Fernet(os.getenv('crypt_key'))

pagination = PaginationMixin()


class DiscountListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Discount.objects.all()
            serializer = DiscountSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,DISCOUNT_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            if (data['discount_type'] == 1):
                data.update({"discount_type": "Wastage %"})
            elif (data['discount_type'] == 2):
                data.update({"discount_type": "Wastage Value"})
            elif (data['discount_type'] == 3):
                data.update({"discount_type": "Making Charges %"})
            elif (data['discount_type'] == 4):
                data.update({"discount_type": "Making Charges Value"})
            elif (data['discount_type'] == 5):
                data.update({"discount_type": "Gold Rate Discount"})
            elif (data['discount_type'] == 6):
                data.update({"discount_type": "Diamond Value Discount"})
            elif (data['discount_type'] == 7):
                data.update({"discount_type": "Flat Bill % Discount"})
            elif (data['discount_type'] == 8):
                data.update({"discount_type": "Flat Bill ₹ Discount"})
            elif (data['discount_type'] == 9):
                data.update({"discount_type": "Category Discount"})
            elif (data['discount_type'] == 10):
                data.update({"discount_type": "Product Discount"})                    
            else:
                data.update({"discount_type": "Customer Type Discount"})
                
                
                
                
            data.update({"pk_id": data['discount_id'],
                        'sno': index+1})
        filters_copy = FILTERS.copy()
        context = {
            'columns': DISCOUNT_COLUMN_LIST,
            'actions': DISCOUNT_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        if(request.data['apply_on']== '1'):
            products = []
            del request.data['product']
            prod_obj = Product.objects.filter(status=True)
            for prod in prod_obj:
                # print(prod.pro_id)
                products.append(prod.pro_id)
            request.data.update({"product":products})
            serializer = DiscountSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=request.user)                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif(request.data['apply_on']== '2'):
            serializer = DiscountSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class DiscountDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer

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
            return Response({"Message": "Discount status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        branches = []
        products =[]
        serializer = DiscountSerializer(obj)
        output = serializer.data
        for branch in serializer.data['branches']:
            branches.append(
                {"value": branch, "label": Branch.objects.get(id_branch=branch).name})
        for product in serializer.data['product']:
            products.append(
                {"value": product, "label": Product.objects.get(pro_id=product).product_name})
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None,
                       "branches":branches,"product":products})
        return Response(output, status=status.HTTP_200_OK)
       
    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        if(request.data['apply_on']== '1'):
            products = []
            del request.data['product']
            prod_obj = Product.objects.filter(status=True)
            for prod in prod_obj:
                # print(prod.pro_id)
                products.append(prod.pro_id)
            request.data.update({"product":products})
            serializer = DiscountSerializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        elif(request.data['apply_on']== '2'):
            serializer = DiscountSerializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Discount instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)




#COUPON

class CouponListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Coupon.objects.all()
            serializer = CouponSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,COUPON_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['coupon_id'],
                        'sno': index+1})
        filters_copy = FILTERS.copy()
        context = {
            'columns': COUPON_COLUMN_LIST,
            'actions': COUPON_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = CouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

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
            return Response({"Message": "Coupon status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        branches = []
        serializer = CouponSerializer(obj)
        output = serializer.data
        for branch in serializer.data['branches']:
            branches.append(
                {"value": branch, "label": Branch.objects.get(id_branch=branch).name})
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None,
                       "branches":branches})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = CouponSerializer(
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
            return Response({"error_detail": ["Coupon instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Gift voucher


class GiftVoucherListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = GiftVoucher.objects.all()
    serializer_class = GiftVoucherSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = GiftVoucher.objects.all()
            serializer = GiftVoucherSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,GIFT_VOUCHER_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['voucher_id'],
                        'sno': index+1})
        filters_copy = FILTERS.copy()
        context = {
            'columns': GIFT_VOUCHER_COLUMN_LIST,
            'actions': GIFT_VOUCHER_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        if(request.data['apply_on']== '1'):
            products = []
            del request.data['product']
            prod_obj = Product.objects.filter(status=True)
            for prod in prod_obj:
                # print(prod.pro_id)
                products.append(prod.pro_id)
            request.data.update({"product":products})
            serializer = GiftVoucherSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=request.user)            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif(request.data['apply_on']== '2'):
            serializer = GiftVoucherSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class GiftVoucherDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = GiftVoucher.objects.all()
    serializer_class = GiftVoucherSerializer

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
            return Response({"Message": "Gift Voucher status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = GiftVoucherSerializer(obj)
        output = serializer.data
        products =[]
        for product in serializer.data['product']:
            products.append(
                {"value": product, "label": Product.objects.get(pro_id=product).product_name})
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None,
                       "product":products})
        return Response(output, status=status.HTTP_200_OK)
       
    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        if(request.data['apply_on']== '1'):
            products = []
            del request.data['product']
            prod_obj = Product.objects.filter(status=True)
            for prod in prod_obj:
                # print(prod.pro_id)
                products.append(prod.pro_id)
            request.data.update({"product":products})
            serializer = GiftVoucherSerializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        elif(request.data['apply_on']== '2'):
            serializer = GiftVoucherSerializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Gift Voucher instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)

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

class GiftVoucherIssueListCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = GiftVoucherIssue.objects.all()
    serializer_class = GiftVoucherIssueSerializer
    
    def get(self, request, format=None):
        queryset = GiftVoucherIssue.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,GIFT_VOUCHER_ISSUE_COLUMN_LIST)
        serializer = GiftVoucherIssueSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            ISSUE_TO_OPTIONS = {
                "1":"Customer",
                "2":"Employee",
                "3":"Vendors",
                "4":"Others",
            }
            gift_voucher = GiftVoucher.objects.filter(voucher_id=data['voucher']).first()
            data.update({"pk_id": data['issue_id'],
                        'sno': index+1})
            
            if(data['status']==1):
                data.update({"status":'Pending'})
            elif(data['status']==2):
                data.update({"status":'Redeemed'})
            elif(data['status']==3):
                data.update({"status":'Cancelled'})
            
            if(gift_voucher.issued_to=='1'):
                customer = Customers.objects.filter(id_customer=data['customer']).first()
                data.update({'name':customer.firstname})
            elif(gift_voucher.issued_to=='2'):
                employee = Employee.objects.filter(id_employee=data['employee']).first()
                data.update({'name':employee.firstname})
            elif(gift_voucher.issued_to=='3'):
                supplier = Supplier.objects.filter(id_supplier=data['supplier']).first()
                data.update({'name':supplier.supplier_name})
                
            data.update({"issue_to":ISSUE_TO_OPTIONS.get(gift_voucher.issued_to),
                         'concated_voucher_code': str(gift_voucher.shortcode) + str(data['voucher_code'])})
        filters_copy = FILTERS.copy()
        context = {
            'columns': GIFT_VOUCHER_ISSUE_COLUMN_LIST,
            'actions': GIFT_VOUCHER_ISSUE_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)
    
    def generate_code(self):

        code = ''
        last_code=None
        last_code=GiftVoucherIssue.objects.all().order_by('-issue_id').first()
        if last_code:
            last_code = last_code.voucher_code
            if last_code:
                code=last_code
                code = str(int(code) + 1).zfill(6)
            else:
               code = '000001'
        else:
            code = '000001'
        return code

    def post(self, request, *args, **kwargs):
        created_by = request.user.id
        no_of_coupons = int(request.data.get("no_of_coupons", 1))
        created_vouchers = []
        print_data = []
        print_view = GiftVoucherPrintView()
        with transaction.atomic():
            for _ in range(no_of_coupons):
                print(request.data)
                payment_details = request.data['payment_mode_details']
                data = request.data.copy()
                voucher_code = self.generate_code()
                data["created_by"] = created_by
                data["issued_date"] = date.today()
                data["voucher_code"] = voucher_code
                serializer = GiftVoucherIssueSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                
                if len(payment_details) > 0:
                    for payment in payment_details:
                        payment.update({'payment_mode' : payment['id_mode']})
                    payment_details = insert_other_details(payment_details,GiftVoucherIssuePaymentDetailSerializer,
                                                           {"voucher_issue":serializer.data['issue_id']})
                created_vouchers.append(serializer.data)
            for created_vou in created_vouchers:
                print_query = GiftVoucherIssue.objects.filter(issue_id=created_vou['issue_id']).first()
                print_serializer = GiftVoucherIssueSerializer(print_query)
                print_output = print_serializer.data
                voucher_pdf_path = print_view.generate_voucher_print(created_vou['voucher'], print_serializer, print_output, request)
                print_data.append(voucher_pdf_path['response_data'])
        return Response({"print_data":print_data, "message":"Vouchers created successfully."}, status=status.HTTP_201_CREATED)
    

# class CouponSearch(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsEmployee]
#     queryset = GiftVoucherIssue.objects.all()
#     serializer_class = GiftVoucherIssueSerializer

#     def post(self, request, *args, **kwargs):
#         coupon_code = request.data.get('coupon_code')

#         if not coupon_code:
#             return Response({"message": "Coupon code is required"}, status=status.HTTP_400_BAD_REQUEST)
#         try:
#             queryset = GiftVoucherIssue.objects.latest()
#             if(coupon_code):
#                 queryset = GiftVoucherIssue.objects.filter(voucher_code__icontains=coupon_code)
#             serializer = GiftVoucherIssueSerializer(queryset)
#             voucher_obj = GiftVoucher.objects.filter(voucher_id=serializer.data['voucher']).first()
#             output = serializer.data
#             return Response(output, status=status.HTTP_200_OK)
#         except GiftVoucherIssue.DoesNotExist:
#             return Response({"message": "Coupon not found"}, status=status.HTTP_400_BAD_REQUEST)


class CouponSearch(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = GiftVoucherIssue.objects.all()
    serializer_class = GiftVoucherIssueSerializer

    def post(self, request, *args, **kwargs):
        coupon_code = request.data.get('coupon_code')
        if not coupon_code:
            return Response({"message": "Coupon code is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = GiftVoucherIssue.objects.filter(voucher_code__icontains=coupon_code)
            if not queryset.exists():
                return Response({"message": "Coupon not found"}, status=status.HTTP_400_BAD_REQUEST)
            voucher_issue = queryset.first()  
            serializer = GiftVoucherIssueSerializer(voucher_issue)

            voucher_obj = GiftVoucher.objects.filter(voucher_id=serializer.data['voucher']).first()
            voucher_obj_serializer = GiftVoucherSerializer(voucher_obj)

            if not voucher_obj:
                return Response({"message": "Associated Gift Voucher not found"}, status=status.HTTP_400_BAD_REQUEST)
            today = timezone.now().date()
            if voucher_obj.validity_from <= today <= voucher_obj.validity_to:
                output = serializer.data
                output.update({"voucher_name":voucher_obj.voucher_name,
                               "conditions":voucher_obj.conditions,
                               "apply_on":voucher_obj.apply_on,
                               "product":voucher_obj_serializer.data['product']})
                return Response(output, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Coupon is not valid today"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        
class VoucherIssueStatusDetailsListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = GiftVoucherIssue.objects.all()
    serializer_class = GiftVoucherIssueSerializer

    def post(self, request):
        from_date = parse_date(request.data.get("from_date"))
        to_date = parse_date(request.data.get("to_date"))

        vouchers = GiftVoucherIssue.objects.filter(status=1)  
        if from_date and to_date:
            vouchers = vouchers.filter(created_on__range=(from_date, to_date))

        serializer = GiftVoucherIssueSerializer(vouchers, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    

class VoucherIssueStatusDetailsUpdateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = GiftVoucherIssue.objects.all()
    serializer_class = GiftVoucherIssueSerializer

    def post(self, request, *args, **kwargs):
        issue_ids = request.data.get("issue_ids", [])
        if not issue_ids:
            return Response({"error": "No voucher provided."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            updated = GiftVoucherIssue.objects.filter(issue_id__in=issue_ids).update(status=3)

        return Response({"message": f"{updated} voucher(s) cancelled successfully."},status=status.HTTP_200_OK)
    
    
class GiftVoucherIssueReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        report_type = request.data.get('report_type', 2)
        columns = []
        queryset = GiftVoucherIssue.objects.all()
        if not from_date or not to_date:
            return Response({"message": "From date and To date are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            if from_date and to_date:
                queryset = queryset.filter(issued_date__range=[from_date, to_date])
                
            if(report_type):
                queryset = queryset.filter(status=report_type)
            
            if int(report_type) == 1:  
                columns = [
                    SNO_COLUMN,
                    {'accessor': 'voucher_name', 'Header': 'Voucher Name', 'text_align': 'center'},
                    {'accessor': 'voucher_code', 'Header': 'Voucher Code', 'text_align': 'center'},
                    {'accessor': 'issued_date', 'Header': 'Issued Date ', 'text_align': 'center'},
                    {'accessor': 'issued_to', 'Header': 'Issued To', 'text_align': 'center'},
                    {'accessor': 'amount', 'Header': 'Amount', 'text_align': 'center', 'is_money_format': True, 'is_total_req':True,"decimal_places":2},
                    # {'accessor': 'status', 'Header': 'Status', 'text_align': 'center'},
                ]
            
            elif int(report_type) == 2: 
                # queryset = queryset.filter(status=2) 
                columns = [
                    SNO_COLUMN,
                    {'accessor': 'voucher_name', 'Header': 'Voucher Name', 'text_align': 'center'},
                    {'accessor': 'voucher_code', 'Header': 'Voucher Code', 'text_align': 'center'},
                    {'accessor': 'bill_no', 'Header': 'Bill No', 'text_align': 'center'},
                    {'accessor': 'name', 'Header': 'Customer Name', 'text_align': 'center'},
                    {'accessor': 'mobile_no', 'Header': 'Mobile No', 'text_align': 'center'},
                    {'accessor': 'amount', 'Header': 'Amount', 'text_align': 'center', 'is_money_format': True, 'is_total_req':True,"decimal_places":2},
                    # {'accessor': 'status', 'Header': 'Status', 'text_align': 'center'},
                ]
            
            paginator, page = pagination.paginate_queryset(queryset, request,None,columns)
            serializer = GiftVoucherIssueSerializer(page, many=True)
            for index, data in enumerate(serializer.data):
                data.update({
                    'sno': index + 1,
                    'voucher_code': data['voucher_code'],
                    'amount': data['amount'],
                })
                
                if(data['customer'] is not None):
                    cus_obj = Customers.objects.filter(id_customer=data['customer']).first()
                    data.update({
                    'name':cus_obj.firstname,
                    'mobile_no':cus_obj.mobile,
                    'issued_to':'Customer'
                    })
                elif(data['employee'] is not None):
                    emp_obj = Employee.objects.filter(id_employee=data['employee']).first()
                    data.update({
                    'name':emp_obj.firstname,
                    'mobile_no':emp_obj.mobile,
                    'issued_to':'Employee'
                    })
                elif(data['supplier'] is not None):
                    supp_obj = Supplier.objects.filter(id_supplier=data['supplier']).first()
                    data.update({
                    'name':supp_obj.supplier_name,
                    'mobile_no':supp_obj.phone_no,
                    'issued_to':'Supplier'
                    })
                
                if(data['status']==2):
                    bill_obj = ErpInvoice.objects.filter(erp_invoice_id=data['ref_no']).first()
                    data.update({
                        'status':'Redeemed',
                        'bill_no':bill_obj.sales_invoice_no
                        })

                elif(data['status']==1):
                    data.update({
                        'status':'Issued'
                        })
                    
            filters_copy = FILTERS.copy()
            filters_copy.update({
                'isDateFilterReq': True,
                'isBranchFilterReq': True,
                'isVoucherIssueStatusFilter': True,
            })
            
            context = {
            'columns': columns,
            'actions': GIFT_VOUCHER_REPORT_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy
            }
            return pagination.paginated_response(serializer.data, context)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)



class GiftVoucherPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = GiftVoucherIssue.objects.all()
    serializer_class = GiftVoucherIssueSerializer
    
    def generate_voucher_print(self, voucher_id, serializer, output, request):
        voucher = GiftVoucher.objects.filter(voucher_id=voucher_id).first()

        output.update({
            "voucher_code" : str(voucher.shortcode) + str(serializer.data['voucher_code']),
            "voucher_name" : voucher.voucher_name,
            "amount":voucher.voucher_amount,
            "terms_and_conditions":voucher.terms_and_conditions
        })

        # order_folder = "gift_voucher"
        # save_dir = os.path.join(settings.MEDIA_ROOT, order_folder, str(serializer.data['voucher_code']))
        # os.makedirs(save_dir, exist_ok=True)

        # template = get_template('purchase_order_print.html')
        
        # html = template.render(output)

        # pdf_path = os.path.join(save_dir, f"{order_folder}.pdf")
        # result = io.BytesIO()
        # pisa.pisaDocument(io.StringIO(html), result)

        # with open(pdf_path, 'wb') as f:
        #     f.write(result.getvalue())
            
        # final_pdf_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{serializer.data['order_no']}/{order_folder}.pdf")

        # return request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{serializer.data['order_no']}/{order_folder}.pdf")
        return {"response_data":output,
                "pdf_url":""}
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = GiftVoucherIssueSerializer(queryset)
        output = serializer.data
        voucher_pdf_path = self.generate_voucher_print(queryset.voucher.voucher_id, serializer, output, request)
        print_data = [voucher_pdf_path['response_data']]
        response_data = {'pdf_url': voucher_pdf_path['pdf_url'],
                         'response_data':print_data}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)