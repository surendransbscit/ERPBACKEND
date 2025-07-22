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
from .models import (LoyaltyTier,LoyaltySettings,LoyaltyCustomer,LoyaltyTransaction)
from .serializers import (LoyaltySettingsSerializer,LoyaltyTierSerializer,LoyaltyCustomerSerializer,LoyaltyTransactionSerializer)
from retailmasters.views import BranchEntryDate
from retailmasters.models import (Branch, FinancialYear, Company)
from employees.models import (Employee)
from customers.models import (Customers)
from .constants import (LOYALTY_TIER_COLUMN_LIST,LOYALTY_TIER_ACTION_LIST,LOYALTY_SETTINGS_ACTION_LIST,LOYALTY_SETTINGS_COLUMN_LIST,
                        LOYALTY_CUSTOMER_ACTION_LIST,LOYALTY_CUSTOMER_COLUMN_LIST,LOYALTY_TRANSACTION_COLUMN_LIST,LOYALTY_TRANSACTION_ACTION_LIST)
from django.db.models import Prefetch


fernet = Fernet(os.getenv('crypt_key'))

pagination = PaginationMixin()


class LoyaltyTierListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = LoyaltyTier.objects.all()
    serializer_class = LoyaltyTierSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = LoyaltyTier.objects.all()
            serializer = LoyaltyTierSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,LOYALTY_TIER_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id'],
                        'sno': index+1})
        filters_copy = FILTERS.copy()
        context = {
            'columns': LOYALTY_TIER_COLUMN_LIST,
            'actions': LOYALTY_TIER_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = LoyaltyTierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoyaltyTierDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = LoyaltyTier.objects.all()
    serializer_class = LoyaltyTierSerializer

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
        serializer = LoyaltyTierSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = LoyaltyTierSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Loyalty Tier instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    
class LoyaltySettingsListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = LoyaltySettings.objects.all()
    serializer_class = LoyaltySettingsSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = LoyaltySettings.objects.all()
            serializer = LoyaltySettingsSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,LOYALTY_SETTINGS_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id'],
                        'sno': index+1})
        filters_copy = FILTERS.copy()
        context = {
            'columns': LOYALTY_SETTINGS_COLUMN_LIST,
            'actions': LOYALTY_SETTINGS_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = LoyaltySettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoyaltySettingsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = LoyaltySettings.objects.all()
    serializer_class = LoyaltySettingsSerializer

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
        serializer = LoyaltySettingsSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = LoyaltySettingsSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Loyalty Tier instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    
class LoyaltyCustomerListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = LoyaltyCustomer.objects.all()
    serializer_class = LoyaltyCustomerSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = LoyaltyCustomer.objects.all()
            serializer = LoyaltyCustomerSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,LOYALTY_CUSTOMER_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            cus = Customers.objects.get(id_customer=data['customer'])
            tr = LoyaltyTier.objects.get(id=data['current_tier'])
            data.update({"pk_id": data['id'],"customer": cus.firstname,"current_tier":tr.tier_name,
                        'sno': index+1})
        filters_copy = FILTERS.copy()
        context = {
            'columns': LOYALTY_CUSTOMER_COLUMN_LIST,
            'actions': LOYALTY_CUSTOMER_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = LoyaltyCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoyaltyCustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = LoyaltyCustomer.objects.all()
    serializer_class = LoyaltyCustomerSerializer

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
            return Response({"Message": "Loyalty Customer status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = LoyaltyCustomerSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = LoyaltyCustomerSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Loyalty Customer instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    

class LoyaltyTransactionListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = LoyaltyTransaction.objects.all()
    serializer_class = LoyaltyTransactionSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = LoyaltyTransaction.objects.all()
            serializer = LoyaltyTransactionSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,LOYALTY_TRANSACTION_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            cus = Customers.objects.get(id_customer=data['customer'])
            data.update({"pk_id": data['id'],"customer": cus.firstname,'sno': index+1})
        filters_copy = FILTERS.copy()
        context = {
            'columns': LOYALTY_TRANSACTION_COLUMN_LIST,
            'actions': LOYALTY_TRANSACTION_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = LoyaltyTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoyaltyTransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = LoyaltyTransaction.objects.all()
    serializer_class = LoyaltyTransactionSerializer

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
            return Response({"Message": "Loyalty Transaction status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = LoyaltyTransactionSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = LoyaltyTransactionSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Loyalty Transaction instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)