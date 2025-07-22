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
from core.views  import get_reports_columns_template
from notifications.views import (send_notification_for_metal_rate)

from utilities.constants import (FILTERS, SERVICE_OPTIONS)
from utilities.notifications import (send_push_notification)
from utilities.utils import (base64_to_file, compress_image)
# Create your views here.
from .models import (Branch, Country, State, City, Company,  Department, Designation, FinancialYear,
                     Uom, Taxmaster, Taxgroupmaster, Taxgroupitems, Currency, ExchangeRate, Bank,
                     PaymentMode, Profile, Area, Profession, Tenant, MetalRates, RelationType,
                     PaymentGateway, PayDevice, District, Banner, NBType, ErpDayClosed, WeightRange, Size, metalRatePurityMaster,
                     Metal, Supplier, AttributeEntry, OtherCharges, ERPOrderStatus, ErpDayClosedLog, StockIssueType,
                     Floor, Counter, RegisteredDevices, Container, OldMetalItemType, OtherWeight, CashOpeningBalance,
                     AccountHead, SupplierAccountDetails, SupplierStaffDetails, ErpService, CustomerProof,IncentiveSettings,
                     SupplierProducts, SupplierProductImageDetails, SupplierProductDetails,BankDeposit,DepositMaster,DepositMasterInterest,
                     CustomerDeposit, CustomerDepositItems, CustomerDepositPayment, CustomerDepositPaymentDetail,Religion,
                     CustomerNotificationMaster, CustomerNotifications, DailyStatusMaster,Region)

from .serializers import (CompanySerializer, BranchSerializer, CountrySerializer, StateSerializer,
                          CitySerializer, DepartmentSerializer, DesignationSerializer, ErpDayClosedLogSerializer,
                          FinancialYearSerializer, UOMSerializer, TaxmasterSerializer,
                          TaxgroupmasterSerializer,  TaxgroupitemsSerializer, CurrencySerializer,
                          ExchangeSerializer, BankSerializer, PaymentModeSerializer, ProfileSerializer,
                          AreaSerializer, ProfessionSerializer, TenantSerializer, MetalRatesSerializer, PaymentGatewaySerializer,
                          PayDeviceSerializer, DistrictSerializer, BannerSerializer, NBTypeSerializer,
                          WeightRangeSerializer, SizeSerializer, MetalRatePurityMasterSerializer, SupplierSerializer,
                          AttributeEntrySerializer, OtherChargesSerializer, ERPOrderStatusSerializer, ErpDayClosedSerializer,
                          StockIssueTypeSerializer, FloorSerializer, CounterSerializer, RegisteredDevicesSerializer,
                          RelationTypeSerializer, ContainerSerializer, OldMetalItemTypeSerializer, OtherWeightSerializer,
                          CashOpeningBalanceSerializer, AccountHeadSerializer, SupplierAccountDetailSerializer, SupplierStaffDetailSerializer,
                          ErpServiceSerializer, CustomerProofSerializer, SupplierProductDetailsSerializer, SupplierProductsSerializer, 
                          SupplierProductImageDetailsSerializer,BankDepositSerializer,DepositMasterSerializer,DepositMasterInterestSerializer,
                          CustomerDepositSerializer, CustomerDepositItemsSerializer, CustomerDepositPaymentSerializer,IncentiveSettingsSerializer,
                          CustomerDepositPaymentDetailSerializer,ReligionSerializer, CustomerNotificationMasterSerializer, CustomerNotificationsSerializer,
                          DailyStatusMasterSerializer,RegionSerializer)

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView

from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee, isSuperuser,IsSuperuserOrEmployee

from knox.models import AuthToken

from django.db.models import Q, ProtectedError

from accounts import serializers

from datetime import datetime, timedelta, date
from customers.models import (Customers, CustomerDeviceIdMaster)
from customers.serializers import (CustomerSerializer, CustomerDeviceIdMasterSerializer)
from schememaster.models import (Scheme)
import json

from .constants import (DEPT_COLUMN_LIST, DEPT_ACTION_LIST, AREA_COLUMN_LIST, AREA_ACTION_LIST,INCENTIVE_COLUMN_LIST,INCENTIVE_ACTION_LIST,
                        DESIGNATION_COLUMN_LIST, DESIGNATION_ACTION_LIST,
                        BANK_COLUMN_LIST, BANK_ACTION_LIST, SERVICE_ACTION_LIST,
                        UOM_COLUMN_LIST, UOM_ACTION_LIST, SUPPLIER_COLUMN_LIST,
                        TAX_COLUMN_LIST, TAX_ACTION_LIST, SUPPLIER_ACTION_LIST,
                        PROFILE_COLUMN_LIST, PROFILE_ACTION_LIST, COMPANY_COLUMN_LIST, COMPANY_ACTION_LIST,
                        BRANCH_COLUMN_LIST, BRANCH_ACTION_LIST, FIN_YEAR_COLUMN_LIST, FIN_YEAR_ACTION_LIST,
                        METAL_RATE_COLUMN_LIST, METAL_RATE_ACTION_LIST, BANK_COLUMN_LIST, BANK_ACTION_LIST,
                        DESIGNATION_COLUMN_LIST, DESIGNATION_ACTION_LIST, SIZE_COLUMN_LIST, SIZE_ACTION_LIST,
                        ATTRIBUTE_COLUMN_LIST, ATTRIBUTE_ACTION_LIST, OTHER_CHARGES_ACTION_LIST, OTHER_CHARGES_COLUMN_LIST,
                        PAY_DEVICE_COLUMN_LIST, PAY_DEVICE_ACTION_LIST, STOCK_ISSUE_TYPE_ACTION_LIST, STOCK_ISSUE_TYPE_COLUMN_LIST,
                        WEIGHT_RANGE_COLUMN_LIST, WEIGHT_RANGE_ACTION_LIST, FLOOR_ACTION_LIST, FLOOR_COLUMN_LIST, COUNTER_COLUMN_LIST, COUNTER_ACTION_LIST,
                        REGISTERED_DEVICES_COLUMN_LIST, REGISTERED_DEVICES_ACTION_LIST, PROFESSION_ACTION_LIST, PROFESSION_COLUMN_LIST, CONTAINER_COLUMN_LIST, CONTAINER_ACTION_LIST,
                        OLD_METAL_ITEM_ACTION_LIST, OLD_METAL_ITEM_COLUMN_LIST, OTHER_WEIGHT_ACTION_LIST, OTHER_WEIGHT_COLUMN_LIST, CASH_OPENING_BALANCE_COLUMN_LIST, CASH_OPENING_BALANCE_ACTION_LIST,
                        ACCOUNT_HEAD_COLUMN_LIST, ACCOUNT_HEAD_ACTION_LIST, SERVICE_COLUMN_LIST, CUSTOMER_PROOF_COLUMN_LIST, CUSTOMER_PROOF_ACTION_LIST, COUNTRY_COLUMN_LIST, COUNTRY_ACTION_LIST,
                        STATE_COLUMN_LIST,STATE_ACTION_LIST,CITY_COLUMN_LIST,CITY_ACTION_LIST,BANK_DEPOSIT_COLUMN_LIST, RELATION_TYPE_COLUMN_LIST,
                        RELATION_TYPE_ACTION_LIST,DEPOSIT_MASTER_COLUMN_LIST,DEPOSIT_MASTER_ACTION_LIST,BANK_DEPOSIT_ACTION_LIST,BANNER_COLUMN_LIST,BANNER_ACTION_LIST,
                        CUSTOMER_DEPOSIT_COLUMN_LIST, CUSTOMER_DEPOSIT_ACTION_LIST,RELIGION_ACTION_LIST,RELIGION_COLUMN_LIST, DAILY_STATUS_MASTER_COLUMN_LIST,
                        DAILY_STATUS_MASTER_ACTION_LIST,REGION_COLUMN_LIST,REGION_ACTION_LIST)

fernet = Fernet(os.getenv('crypt_key'))

pagination = PaginationMixin()  # Apply pagination

from retailcataloguemasters.models import CounterWiseTarget
from retailcataloguemasters.serializers import CounterWiseTargetSerializer

def close_branch(branch_id, user):
    day_close = ErpDayClosed.objects.get(id_branch=branch_id)
    entry_date = day_close.entry_date+timedelta(days=1)
    ErpDayClosed.objects.filter(id_branch=branch_id).update(entry_date=entry_date, is_day_closed=True,
                                                            updated_on=date.today())
    if (user != None):
        close_log_data = {"id_branch": branch_id,
                          "created_by": user, "day_close_type": 1}
    else:
        close_log_data = {"id_branch": branch_id,
                          "created_by": None, "day_close_type": 2}
    close_log_serializer = ErpDayClosedLogSerializer(data=close_log_data)
    close_log_serializer.is_valid(raise_exception=True)
    close_log_serializer.save()


class RelationTypeListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = RelationType.objects.all()
    serializer_class = RelationTypeSerializer

    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            output = []
            queryset = RelationType.objects.filter(is_active=True)
            serializer = RelationTypeSerializer(queryset, many=True)
            for data in serializer.data:
                instance = {}
                instance.update({"label": data['name'], "value": data['id']})
                if instance not in output:
                    output.append(instance)
            return Response(output, status=status.HTTP_200_OK)
        queryset = RelationType.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,RELATION_TYPE_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id'],
                        'sno': index+1})
        context = {
            'columns': RELATION_TYPE_COLUMN_LIST,
            'actions': RELATION_TYPE_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        serializer = RelationTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    
class RelationTypeDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = RelationType.objects.all()
    serializer_class = RelationTypeSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        if ('changestatus' in request.query_params):
            if (queryset.is_active == True):
                queryset.is_active = False
            else:
                queryset.is_active = True
            queryset.save()
            return Response({"Message": "Relation Type status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = RelationTypeSerializer(queryset)
        output = serializer.data
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = RelationTypeSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Relation Type instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_202_ACCEPTED)


class CustomerProofListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee or isSuperuser]
    queryset = CustomerProof.objects.all()
    serializer_class = CustomerProofSerializer

    def get(self, request, *args, **kwargs):
        queryset = CustomerProof.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,CUSTOMER_PROOF_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            customer = Customers.objects.filter(
                id_customer=data['id_customer']).get()
            data.update({"pk_id": data['id_proof_identity'],
                        'sno': index+1, "customer_name": customer.firstname})
        context = {
            'columns': CUSTOMER_PROOF_COLUMN_LIST,
            'actions': CUSTOMER_PROOF_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        if (request.data['aadhar_img_page'] != None):
            b = ((base64.b64decode(request.data['aadhar_img_page']
                                   [request.data['aadhar_img_page'].find(",") + 1:])))
            img = Image.open(io.BytesIO(b))
            filename = 'aadhar_img_page_cus.jpeg'
            img_object = ImageFile(io.BytesIO(
                img.fp.getvalue()), name=filename)
            request.data.update({"aadhar_img_page": img_object})
        else:
            request.data.update({"aadhar_img_page": None})
        ######
        if (request.data['application_img_path'] != None):
            b = ((base64.b64decode(request.data['application_img_path']
                                   [request.data['application_img_path'].find(",") + 1:])))
            img = Image.open(io.BytesIO(b))
            filename = 'application_img_path_cus.jpeg'
            img_object = ImageFile(io.BytesIO(
                img.fp.getvalue()), name=filename)
            request.data.update({"application_img_path": img_object})
        else:
            request.data.update({"application_img_path": None})
        serializer = CustomerProofSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomerProofDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = CustomerProof.objects.all()
    serializer_class = CustomerProofSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = CustomerProofSerializer(
            obj, context={"request": request})
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        if (request.data['aadhar_img_page'] != None):
            if 'data:image/' in request.data['aadhar_img_page'][:30]:
                # update items  for which image is changed
                queryset.aadhar_img_page.delete()
                b = (
                    (base64.b64decode(request.data['aadhar_img_page'][request.data['aadhar_img_page'].find(",") + 1:])))
                img = Image.open(io.BytesIO(b))
                filename = 'aadhar_img_page_cus.jpeg'
                img_object = ImageFile(io.BytesIO(
                    img.fp.getvalue()), name=filename)
                request.data.update({"aadhar_img_page": img_object})

                serializer = self.get_serializer(queryset, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            del request.data['aadhar_img_page']

        if (request.data['application_img_path'] != None):
            if 'data:image/' in request.data['application_img_path'][:30]:
                # update items  for which image is changed
                queryset.application_img_path.delete()
                b = (
                    (base64.b64decode(request.data['application_img_path'][request.data['application_img_path'].find(",") + 1:])))
                img = Image.open(io.BytesIO(b))
                filename = 'application_img_path_cus.jpeg'
                img_object = ImageFile(io.BytesIO(
                    img.fp.getvalue()), name=filename)
                request.data.update({"application_img_path": img_object})

                serializer = self.get_serializer(queryset, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            del request.data['application_img_path']

            serializer = self.get_serializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            serializer = self.get_serializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Customer Proof instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DayCloseVerificationView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        output = []
        messages = []
        ids = []
        for data in request.data['branches']:
            instance = {}
            if (ErpDayClosed.objects.filter(id_branch=data, is_day_closed=False).exists()):
                if (ErpDayClosed.objects.filter(id_branch=data).get().entry_date != date.today()):
                    branch = Branch.objects.get(id_branch=data)
                    # instance.update({"message":f"For {branch.name} branch day has not been closed."})
                    instance.update(
                        {"id": branch.id_branch, "name": branch.name, "dayclose": False})
                    # ids.append(branch.id_branch)
                    if instance not in messages:
                        output.append(instance)
        # output.update({"ids":ids, "messages":messages})
        return Response(output, status=status.HTTP_200_OK)


class DayCloseVerifyUpdateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            for branches in request.data['branches']:
                if (branches['dayclose'] == True):
                    ErpDayClosed.objects.filter(id_branch=branches['id']).update(entry_date=date.today(), is_day_closed=True,
                                                                                 updated_on=date.today())
                    close_log_data = {
                        "id_branch": branches['id'], "created_by": request.user.pk}
                    close_log_serializer = ErpDayClosedLogSerializer(
                        data=close_log_data)
                    close_log_serializer.is_valid(raise_exception=True)
                    close_log_serializer.save()
            return Response({"message": "Branches closed successfully."}, status=status.HTTP_201_CREATED)


class ManualDayCloseView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        if (not (request.data['id_branch'])):
            return Response({"message": "Pass branch identifier."}, status=status.HTTP_400_BAD_REQUEST)
        if (ErpDayClosed.objects.filter(id_branch=request.data['id_branch'], is_day_closed=True)):
            return Response({"message": "This branch has been already closed"}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            close_branch(request.data['id_branch'], request.user.pk)
            # day_close = ErpDayClosed.objects.get(id_branch=request.data['id_branch'])
            # entry_date = day_close.entry_date+timedelta(days=1)
            # ErpDayClosed.objects.filter(id_branch=request.data['id_branch']).update(entry_date=entry_date, is_day_closed=True,
            #                                                                         updated_on=date.today())
            # close_log_data = {"id_branch":request.data['id_branch'], "created_by":request.user}
            # close_log_serializer = ErpDayClosedLogSerializer(data=close_log_data)
            # close_log_serializer.is_valid(raise_exception=True)
            # close_log_serializer.save()
            return Response({"message": "Day closed successfully."}, status=status.HTTP_201_CREATED)


class AutomaticDayCloseView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            branch = Branch.objects.filter(active=True)
            branch_serializer = BranchSerializer(branch, many=True)
            for branches in branch_serializer.data:
                if (ErpDayClosed.objects.filter(id_branch=branches['id_branch'], is_day_closed=True).exists() == False):
                    close_branch(branches['id_branch'], None)
                    # day_close = ErpDayClosed.objects.get(id_branch=branches['id_branch'])
                    # entry_date = day_close.entry_date+timedelta(days=1)
                    # ErpDayClosed.objects.filter(id_branch=branches['id_branch']).update(entry_date=entry_date, is_day_closed=True,
                    #                                                                 updated_on=date.today())
                    # close_log_data = {"id_branch":branches['id_branch'], "created_by":request.user}
                    # close_log_serializer = ErpDayClosedLogSerializer(data=close_log_data)
                    # close_log_serializer.is_valid(raise_exception=True)
                    # close_log_serializer.save()
            print("Branches closed successfully.")
            return Response({"message": "Branches closed successfully."}, status=status.HTTP_201_CREATED)


class RestDayCloseView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        print("Day Close Reseted")
        ErpDayClosed.objects.filter(is_day_closed=True).update(
            is_day_closed=False, updated_on=date.today())
        return Response({"message": "Branches reseted successfully."}, status=status.HTTP_200_OK)


class ErpOrderStatusListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        output = []
        queryset = ERPOrderStatus.objects.filter(status=True)
        serializer = ERPOrderStatusSerializer(queryset, many=True)
        for data in serializer.data:
            instance = {}
            instance.update({"label": data['name'], "value": data['id']})
            if instance not in output:
                output.append(instance)
        return Response(output, status=status.HTTP_200_OK)


class ErpServiceListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpServiceSerializer
    queryset = ErpService.objects.all()

    def get(self, request, *args, **kwargs):
        if 'options' in request.query_params:
            output = SERVICE_OPTIONS
            return Response(output, status=status.HTTP_200_OK)
        queryset = ErpService.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,SERVICE_COLUMN_LIST)
        serializer = self.serializer_class(
            page, many=True, context={'request': request})
        for index, data in enumerate(serializer.data):
            data.update({
                'pk_id': data['id_service'],
                'sno': index+1})
        context = {'columns': SERVICE_COLUMN_LIST, 'actions': SERVICE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.id})
        serializer = ErpServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ErpServiceDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    serializer_class = ErpServiceSerializer
    queryset = ErpService.objects.all()

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = ErpServiceSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = ErpServiceSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Service instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyAPI(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CompanySerializer

    def get_country(self, obj_id):
        try:
            country = Country.objects.get(id_country=obj_id)
            result = {}
            result.update({"value": country.id_country, "label": country.name,
                          "currency_code": country.currency_code})
            return result

        except Country.DoesNotExist:
            return None

    def get_state(self, obj_id):
        try:
            state = State.objects.get(id_state=obj_id)
            result = {}
            result.update({"value": state.id_state, "label": state.name})
            return result
        except State.DoesNotExist:
            return None

    def get_city(self, obj_id):
        try:
            city = City.objects.get(id_city=obj_id)
            result = {}
            result.update({"value": city.id_city, "label": city.name})
            return result
        except City.DoesNotExist:
            return None

    def get(self, request, format=None):
        companylist = Company.objects.all()

        # filter single instance by passing the ID
        if 'id' in request.query_params:
            try:
                company = Company.objects.get(
                    id_company=request.query_params['id'])
                serializer = CompanySerializer(company, context={"request":request})
                country = self.get_country(serializer.data['country'])
                state = self.get_state(serializer.data['state'])
                city = self.get_city(serializer.data['city'])
                output = serializer.data
                output.update({
                    "country_name": country['label'],
                    "city_name": state['label'],
                    "state_name": city['label'],
                    "currency_code": country['currency_code'],
                    "currency_sybmol": (country['currency_code'])
                })
                output.update(
                    {"id_country": country, "id_state": state, "id_city": city})
                return Response(output)
            except Company.DoesNotExist:
                raise Http404

        paginator, page = pagination.paginate_queryset(companylist, request,None,COMPANY_COLUMN_LIST)
        serializer = self.serializer_class(
            page, many=True, context={"request": request})

        # get  companies as select options : Label and Values
        if 'options' in request.query_params:
            output = []
            for data in serializer.data:
                instance = {}
                instance.update(
                    {"label": data['company_name'], "value": data['id_company']})
                if instance not in output:
                    output.append(instance)
            return Response(output)
        # return List O/P
        for data in serializer.data:
            if (data['image'] != None):
                data.update(
                    {"image": data['image'], "image_text": data['company_name'][0]})
            else:
                data.update(
                    {"image": None, "image_text": data['company_name'][0]})
            data.update({"pk_id": data['id_company']})
        context = {'columns': COMPANY_COLUMN_LIST, 'actions': COMPANY_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def put(self, request, format=None):
        if 'id' in request.query_params:
            id_company = request.query_params.get('id')
            company = Company.objects.get(id_company=id_company)
            if (request.data['image'] != None):
                if 'data:image/' in request.data['image'][:30]:
                    # update items  for which image is changed
                    company.image.delete()
                    b = (
                        (base64.b64decode(request.data['image'][request.data['image'].find(",") + 1:])))
                    img = Image.open(io.BytesIO(b))
                    filename = 'company_image.jpeg'
                    img_object = ImageFile(io.BytesIO(
                        img.fp.getvalue()), name=filename)
                    request.data.update({"image": img_object})

                    serializer = CompanySerializer(company, data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                del request.data['image']
                serializer = CompanySerializer(company, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            else:
                serializer = CompanySerializer(company, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response({"error_detail": ["Bad Request Format - Identifier Missing"]})

    def post(self, request, format=None):
        encrypted_gst = fernet.encrypt(
            str(request.data['gst_number']).encode())
        encrypted_cin = fernet.encrypt(
            str(request.data['cin_number']).encode())
        encrypted_bank = fernet.encrypt(
            str(request.data['bank_acc_number']).encode())
        del request.data['pan_number']
        del request.data['cin_number']
        del request.data['bank_acc_number']
        if (request.data['image'] != None):
            b = ((base64.b64decode(request.data['image']
                                   [request.data['image'].find(",") + 1:])))
            img = Image.open(io.BytesIO(b))
            filename = 'company_image.jpeg'
            img_object = ImageFile(io.BytesIO(
                img.fp.getvalue()), name=filename)
            request.data.update({"image": img_object})
        else:
            request.data.update({"image": None})
        request.data.update({"gst_number": encrypted_gst,
                            "cin_number": encrypted_cin, "bank_acc_number": encrypted_bank})
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, format=None):
        if 'id' in request.query_params:
            try:
                company = Company.objects.get(
                    id_company=request.query_params.get('id'))
                try:
                    company.delete()
                except ProtectedError:
                    return Response({"error_detail": ["Can't delete Company as it is in relation."]}, status=status.HTTP_423_LOCKED)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Company.DoesNotExist:
                raise Http404
        return Response({"error_detail": ["Bad Reqest Format - Identifer Misssing"]})


class BranchList(generics.GenericAPIView):
    permission_classes = [IsEmployee | IsCustomerUser]

    queryset = Branch.objects.all()
    serializer = BranchSerializer(queryset, many=True)

    def get(self, request, *args, **kwargs):
        queryset = Branch.objects.filter(active=1, is_ho=0)
        serializer = BranchSerializer(
            queryset, many=True, context={'request': request})
        output = serializer.data
        response_data = []
        try:
            for data in output:
                result = {}
                try:
                    city = City.objects.get(id_city=data['city'])
                    state = State.objects.get(id_state=data['state'])
                    city_name = city.name
                    state_name = state.name
                except City.DoesNotExist:
                    city_name = ''
                    state_name = ''
                result.update({
                                "id_branch":data['id_branch'],
                               "name": data['name'],
                               "short_name": data['short_name'],
                               "email": data['email'],
                               "address1": data['address1'],
                               "address2": data['address2'],
                               "mobile": data['mobile'],
                               "pincode": data['pincode'],
                               "city": city_name,
                               "state": state_name,
                               "stone_hours": "9:30 AM - 10.00 PM"
                               })
                response_data.append(result)
            return Response({"data": response_data}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)


class BranchAPI(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BranchSerializer

    def get_object(self, obj_id):
        try:
            return Branch.objects.get(id_branch=obj_id)
        except Branch.DoesNotExist:
            raise Http404

    def get_country(self, obj_id):
        try:
            country = Country.objects.get(id_country=obj_id)
            result = {}
            result.update({"value": country.id_country, "label": country.name})
            return result

        except Country.DoesNotExist:
            return None

    def get_state(self, obj_id):
        try:
            state = State.objects.get(id_state=obj_id)
            result = {}
            result.update({"value": state.id_state, "label": state.name})
            return result
        except State.DoesNotExist:
            return None

    def get_city(self, obj_id):
        try:
            city = City.objects.get(id_city=obj_id)
            result = {}
            result.update({"value": city.id_city, "label": city.name})
            return result
        except City.DoesNotExist:
            return None

    def get(self, request, format=None):
        if 'branchid' in request.query_params:
            id = request.query_params['branchid']
            brnch = self.get_object(id)
            if ('changestatus' in request.query_params):
                if (brnch.active == True):
                    brnch.active = False
                else:
                    brnch.active = True
                brnch.save()
                return Response({"Message": "Branch status changed successfully."}, status=status.HTTP_202_ACCEPTED)
            serializer = BranchSerializer(brnch, context={'request': request})
            data = serializer.data
            data.update({
                "id_city": brnch.city.pk,
                "id_state": brnch.state.pk,
                "id_country": brnch.country.pk,
                "id_company": brnch.id_company.id_company
            })
            return Response(data)
        if 'branch' in request.query_params and request.query_params['branch'] == 'is_ho':
            out = []
            try:
                instance = {}
                branch = Branch.objects.get(is_ho=1, active=1)
                instance.update(
                    {"label": branch.name, "value": branch.id_branch})
                out.append(instance)
            except (Branch.DoesNotExist, Branch.MultipleObjectsReturned):
                pass
                # instance = {}
                # # instance.update()
                # out.append(instance)
            return Response(out)
        if 'active' in request.query_params:
            brnch = Branch.objects.filter(active=1)
            if 'company' in request.query_params and int(request.query_params['company']) != 0:
                print(type(request.query_params['company']))
                brnch = brnch.filter(
                    id_company=request.query_params['company'])
                if 'branch' in request.query_params and int(request.query_params['branch']) != 0:
                    brnch = brnch.filter(
                        id_branch=request.query_params['branch'])

            serializer = BranchSerializer(brnch,
                                          many=True,
                                          context={'request': request})
            active_branches = []
            for data in serializer.data:
                instance = {}
                instance.update({
                    "label": data['name'],
                    "value": data['id_branch'],
                    "is_ho": data['is_ho']
                })
                active_branches.append(instance)

            return Response(active_branches)
        brnch = Branch.objects.all()
        paginator, page = pagination.paginate_queryset(brnch, request,None,BRANCH_COLUMN_LIST)
        serializer = self.serializer_class(
            page, many=True, context={'request': request})
        for index, data in enumerate(serializer.data):
            branch_name = str(data['name']).title()
            data.update({
                'pk_id': data['id_branch'],
                'name': branch_name,
                'is_active': data['active'],
                'sno': index+1})
            try:
                company_name = Company.objects.get(
                    id_company=data['id_company']).company_name
            except Company.DoesNotExist:
                company_name = None
            data.update({"company_name": company_name})

        context = {'columns': BRANCH_COLUMN_LIST, 'actions': BRANCH_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        if (not IsEmployee.has_permission(self, request, view=BranchAPI)):
            return Response({'error_detail': ['Your are not authorized']}, status=status.HTTP_401_UNAUTHORIZED)
        if 'is_ho' in request.data and request.data['is_ho'] == 'true':
            for each1 in Branch.objects.all():
                each1.is_ho = False
                each1.save()
        serializer = BranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if 'metal_rate_type' in request.data and request.data[
                'metal_rate_type'] != "2":
            serializer.save()
            return Response(serializer.data)
        serializer.save(active=1)
        return Response(serializer.data)

    def put(self, request, format=None):
        if (not IsEmployee.has_permission(self, request, view=BranchAPI)):
            return Response({'error_detail': ['Your are not authorized']}, status=status.HTTP_401_UNAUTHORIZED)
        # id=
        if 'branchid' in request.query_params:
            if 'is_ho' in request.data and request.data['is_ho'] == 'true':
                for each1 in Branch.objects.all():
                    each1.is_ho = False
                    each1.save()
            id = request.query_params['branchid']
            brnch = self.get_object(id)
            print(isinstance(request.data['logo'], str))

            company = Company.objects.filter(
                id_company=request.data['id_company']).get()
            country = Country.objects.filter(
                id_country=request.data['country']).get()
            state = State.objects.filter(id_state=request.data['state']).get()
            city = City.objects.filter(id_city=request.data['city']).get()
            if (request.data['logo'] == None):
                serializer = BranchSerializer(brnch, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(updated_by=self.request.user,
                                updated_on=datetime.now(tz=timezone.utc))
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            else:
                if ((isinstance(request.data['logo'], str))):
                    try:
                        brnch.id_company = company
                        brnch.show_to_all = request.data['show_to_all']
                        brnch.name = request.data['name']
                        brnch.warehouse = request.data['warehouse']
                        brnch.expo_warehouse = request.data['expo_warehouse']
                        brnch.short_name = request.data['short_name']
                        brnch.email = request.data['email']
                        brnch.address1 = request.data['address1']
                        brnch.address2 = request.data['address2']
                        brnch.country = country
                        brnch.state = state
                        brnch.city = city
                        brnch.phone = request.data['phone']
                        brnch.mobile = request.data['mobile']
                        brnch.cusromercare = request.data['cusromercare']
                        brnch.pincode = request.data['pincode']
                        brnch.metal_rate_type = request.data['metal_rate_type']
                        brnch.map_url = request.data['map_url']
                        brnch.fb_link = request.data['fb_link']
                        brnch.insta_link = request.data['insta_link']
                        brnch.sort = request.data['sort']
                        brnch.otp_verif_mobileno = request.data['otp_verif_mobileno']
                        brnch.branch_type = request.data['branch_type']
                        brnch.is_ho = True if request.data['is_ho'] == True else False
                        brnch.note = request.data['note']
                        brnch.gst_number = request.data['gst_number']
                        brnch.active = True if request.data['active'] == True else False
                        brnch.save()
                        serializer = BranchSerializer(brnch)
                        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                    except IntegrityError:
                        return Response({"error_detail": [
                            "Branch name already exists."]}, status=status.HTTP_400_BAD_REQUEST)
                if ((isinstance(request.data['logo'], str)) == False):
                    try:
                        brnch.logo = request.data['logo']
                        brnch.id_company = company
                        brnch.show_to_all = request.data['show_to_all']
                        brnch.name = request.data['name']
                        brnch.warehouse = request.data['warehouse']
                        brnch.expo_warehouse = request.data['expo_warehouse']
                        brnch.short_name = request.data['short_name']
                        brnch.email = request.data['email']
                        brnch.address1 = request.data['address1']
                        brnch.address2 = request.data['address2']
                        brnch.country = country
                        brnch.state = state
                        brnch.city = city
                        brnch.phone = request.data['phone']
                        brnch.mobile = request.data['mobile']
                        brnch.cusromercare = request.data['cusromercare']
                        brnch.pincode = request.data['pincode']
                        brnch.metal_rate_type = request.data['metal_rate_type']
                        brnch.map_url = request.data['map_url']
                        brnch.fb_link = request.data['fb_link']
                        brnch.insta_link = request.data['insta_link']
                        brnch.sort = request.data['sort']
                        brnch.otp_verif_mobileno = request.data['otp_verif_mobileno']
                        brnch.branch_type = request.data['branch_type']
                        brnch.is_ho = True if request.data['is_ho'] == 'true' else False
                        brnch.note = request.data['note']
                        brnch.gst_number = request.data['gst_number']
                        brnch.active = True if request.data['active'] == 'true' else False
                        brnch.save()
                        serializer = BranchSerializer(brnch)
                        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                    except IntegrityError:
                        return Response({"error_detail": [
                            "Branch name already exists."]}, status=status.HTTP_400_BAD_REQUEST)

            # # print('logo' in request.data)
            # # print(request.data['logo'] == '')
            # data = (request.data)
            # data._mutable = True
            # # print(data)
            # if ('logo' in request.data and request.data['logo'] == ''):
            #     data.pop('logo')
            # serializer = BranchSerializer(brnch, data=data)
            # # if ('logo' in request.data and request.data['logo'] == ''):
            # #     data = request.data
            # #     request.data._mutable = True
            # #     request.data.update({'logo': brnch.logo})
            # #     request.data._mutable = False

            # # else:
            # #     data = request.data
            # # serializer = BranchSerializer(brnch, data=data)
            # serializer.is_valid(raise_exception=True)
            # serializer.save(active=1)
            # return Response(serializer.data)
        return Response(
            {"Error": "Pass identifier(branchid as parameter) to edit data"},
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, format=None):
        if (not IsEmployee.has_permission(self, request, view=BranchAPI)):
            return Response({'error_detail': ['Your are not authorized']}, status=status.HTTP_401_UNAUTHORIZED)
        if 'branchid' in request.query_params:
            try:
                id = request.query_params['branchid']
                brnch = self.get_object(id)
                try:
                    brnch.delete()
                except ProtectedError:
                    return Response({"error_detail": ["Branch instance can't be deleted, as it is already in relation."]}, status=status.HTTP_423_LOCKED)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Branch.DoesNotExist:
                raise Http404
        return Response({"error_detail": ["Bad Reqest Format - Identifer Misssing"]})


class BranchStatusUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

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
            return Response({"Message": "Branch status changed successfully."}, status=status.HTTP_202_ACCEPTED)

# District


class DistrictViewAPI(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.id})
        serializer = DistrictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, format=None):
        queryset = District.objects.all()
        serializer = DistrictSerializer(queryset, many=True)
        output = []
        for data in serializer.data:
            instance = {}
            state = State.objects.get(id_state=data['state'])
            instance.update({"id_district": data['id_district'], "district_name": data['district_name'],
                             "district_code": data['district_code'], "state": state.name})
            if instance not in output:
                output.append(instance)
        return Response(output, status=status.HTTP_200_OK)


class DistrictViewDetailAPI(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = District.objects.all()
    serializer_class = DistrictSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = DistrictSerializer(queryset)
        output = serializer.data
        output.update({"created_by": queryset.created_by.username,
                       "updated_by": queryset.updated_by.username if queryset.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = DistrictSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["District instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Country
class CountryListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = Country.objects.filter(is_active=1)
            serializer = CountrySerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = Country.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,COUNTRY_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_country'], "sno": index+1})
        context = {'columns': COUNTRY_COLUMN_LIST, 'actions': COUNTRY_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.id})
        if(request.data['is_default'] == True):
            Country.objects.all().update(is_default=False)
        serializer = CountrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CountryDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = CountrySerializer(queryset)
        output = serializer.data
        output.update({"created_by": queryset.created_by.username,
                       "updated_by": queryset.updated_by.username if queryset.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        if(request.data['is_default'] == True):
            Country.objects.all().update(is_default=False)
        serializer = CountrySerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Country instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


# State
class StateViewAPI(APIView):
    permission_classes = [permissions.AllowAny]
    queryset = State.objects.all()
    serializer_class = StateSerializer

    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = State.objects.filter(is_active=1)
            serializer = StateSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = State.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,STATE_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            count = Country.objects.get(id_country=data['country'])
            data.update({"pk_id": data['id_state'], "sno": index+1,"country":count.name})
        context = {'columns': STATE_COLUMN_LIST, 'actions': STATE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.id})
        serializer = StateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    


class StateViewDetailAPI(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = State.objects.all()
    serializer_class = StateSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = StateSerializer(queryset)
        output = serializer.data
        output.update({"created_by": queryset.created_by.username,
                       "updated_by": queryset.updated_by.username if queryset.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = StateSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["State instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


# City
class CityViewAPI(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = City.objects.all()
    serializer_class = CitySerializer


    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = City.objects.filter(is_active=1)
            serializer = CitySerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = City.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,CITY_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            count = State.objects.get(id_state=data['state'])
            data.update({"pk_id": data['id_city'], "sno": index+1,"state":count.name})
        context = {'columns': CITY_COLUMN_LIST, 'actions': CITY_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.id})
        # district = District.objects.filter(
        #     id_district=request.data['district']).get()
        # request.data.update({"state": district.state.id_state})
        serializer = CitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    


class CityDetailViewAPI(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = City.objects.all()
    serializer_class = CitySerializer

    def get(self, request, *args, **kwargs):
        city = self.get_object()
        serializer = CitySerializer(city)
        output = serializer.data
        output.update({"created_by": city.created_by.username,
                       "updated_by": city.updated_by.username if city.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        # if (request.data['district'] != queryset.district.id_district):
        #     district = District.objects.filter(
        #         id_district=request.data['district']).get()
        #     request.data.update({"state": district.state.id_state})
        serializer = CitySerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["City instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)

# Financial Year





class FinancialYearDetails(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes=[permissions.AllowAny]
    permission_classes = [IsEmployee]
    queryset = FinancialYear.objects.all()
    serializer_class = FinancialYearSerializer

    def get(self, request, *args, **kwargs):
        finyear = self.get_object()
        # if ('changestatus' in request.query_params):
        #     if (finyear.fin_status == False):
        #         FinancialYear.objects.all().update(fin_status=False)
        #         finyear.fin_status = True
        #     else:
        #         finyear.fin_status = False
        #     finyear.updated_by = self.request.user
        #     finyear.updated_on = datetime.now(tz=timezone.utc)
        #     finyear.save()
        #     return Response({"Message": "Financial Year status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = FinancialYearSerializer(finyear)
        output = serializer.data
        output.update({"created_by": finyear.created_by.username,
                       "updated_by": finyear.updated_by.username if finyear.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = FinancialYearSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        if (queryset.fin_status == False):
            try:
                queryset.delete()
            except ProtectedError:
                return Response({"error_detail": ["Financial Year can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        else:
            return Response({"error_detail": ["Active Financial Year can't be deleted"]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RetUomListView(generics.ListCreateAPIView):
    # permission_classes=[permissions.AllowAny]
    permission_classes = [IsEmployee]
    queryset = Uom.objects.all()
    serializer_class = UOMSerializer

    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = Uom.objects.filter(uom_status=1)
            serializer = UOMSerializer(queryset, many=True)
            return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
        queryset = Uom.objects.all()
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,UOM_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['uom_id'], 'sno': index+1, 'is_active': data['uom_status']})
        context = {'columns': UOM_COLUMN_LIST, 'actions': UOM_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = UOMSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def carat_to_gram_conversion(self, stone_wt, uom_id):
        query_set = Uom.objects.get(uom_id=uom_id)
        stone_weight = stone_wt
        if ( query_set.divided_by_value and query_set.divided_by_value > 0):
            stone_weight = float(stone_wt)/query_set.divided_by_value
        return stone_weight


# currency

class CurrencyListView(generics.ListCreateAPIView):
    # permission_classes=[permissions.AllowAny]
    permission_classes = [IsEmployee]
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer

    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = Currency.objects.filter(uom_status=1)
            serializer = CurrencySerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = Currency.objects.all()
        serializer = CurrencySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = CurrencySerializer(data=request.data)
        serializer.is_valid()
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CurrencyDetails(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes=[permissions.AllowAny]
    permission_classes = [IsEmployee]
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = CurrencySerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = CurrencySerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class RetUomDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    # permission_classes=[permissions.AllowAny]
    queryset = Uom.objects.all()
    serializer_class = UOMSerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.uom_status == True):
                obj.uom_status = False
            else:
                obj.uom_status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "UOM status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = UOMSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):

        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = UOMSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["UOM instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaxmasterListView(generics.ListCreateAPIView):
    # permission_classes=[permissions.AllowAny]
    permission_classes = [IsEmployee]
    queryset = Taxmaster.objects.all()
    serializer_class = TaxmasterSerializer

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.pk})
        serializer = TaxmasterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = Taxmaster.objects.filter(tax_status=1)
            serializer = TaxmasterSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = Taxmaster.objects.all().order_by('-pk')
        paginator, page = pagination.paginate_queryset(queryset, request,None,TAX_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['tax_id'], 'sno': index+1, 'is_active': data['tax_status']})
        context = {'columns': TAX_COLUMN_LIST, 'actions': TAX_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)


class TaxmasterDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    # permission_classes=[permissions.AllowAny]
    queryset = Taxmaster.objects.all()
    # serializer_class = TaxmasterSerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.tax_status == True):
                obj.tax_status = False
            else:
                obj.tax_status = True
            obj.modified_by_id = self.request.user
            obj.modified_time = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Tax status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = TaxmasterSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.modified_by.username if obj.modified_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = TaxmasterSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(modified_by=self.request.user,
                        modified_time=datetime.now(tz=timezone.utc))
        return Response(serializer.data)

    def delete(self, request, pk, format=None):
        obj = self.get_object()
        try:
            obj.delete()
        except ProtectedError:
            return Response({"error_detail": ["Tax can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaxgroupmasteDetails(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = Taxgroupmaster.objects.all()
    serializer_class = TaxgroupmasterSerializer

    def get(self, request, *args, **kwargs):
        if 'id' in request.query_params:
            tax_grp = Taxgroupmaster.objects.filter(
                tgrp_id=request.query_params['id']).get()
            serializer = TaxgroupmasterSerializer(tax_grp)
            tax_grp_items = Taxgroupitems.objects.filter(
                tgi_tgrpcode=tax_grp.tgrp_id)
            itserializer = TaxgroupitemsSerializer(tax_grp_items, many=True)
            output = serializer.data
            output.update({'created_by': tax_grp.created_by.username,
                           'updated_by': tax_grp.modified_by.username if tax_grp.modified_by != None else None})
            output.update({"tax_grp_items": itserializer.data})
            return Response(output)

    def put(self, request, *args, **kwargs):
        if 'grp_data' and 'grp_item_data' in request.data:
            tax_grp_item = Taxgroupmaster.objects.filter(
                tgrp_id=request.query_params['tax_grp_id']).get()
            request.data['grp_data'].update(
                {"created_by": tax_grp_item.created_by.pk})
            serializer = TaxgroupmasterSerializer(
                tax_grp_item, data=request.data['grp_data'])
            serializer.is_valid(raise_exception=True)
            serializer.save(modified_by=request.user,
                            modified_time=datetime.now(tz=timezone.utc))
            existing = [item.tgi_sno for item in Taxgroupitems.objects.filter(
                tgi_tgrpcode=tax_grp_item.tgrp_id)]

            for item in existing:
                if item not in [item['tgi_sno'] for item in request.data['grp_item_data']]:
                    Taxgroupitems.objects.filter(tgi_sno=item).delete()

            for item in request.data['grp_item_data']:
                if item['tgi_sno'] not in existing:
                    item.pop('tgi_sno')
                    tax = Taxmaster.objects.get(
                        tax_id=item['tgi_taxcode'])

                    tgi_tgrpcode = Taxgroupmaster.objects.get(
                        tgrp_id=request.query_params['tax_grp_id'])
                    item.update(
                        {"tgi_taxcode": tax, "tgi_tgrpcode": tgi_tgrpcode})
                    print(" not in existing", item)
                    Taxgroupitems.objects.create(**item)
                    continue
                Taxgroupitems.objects.filter(
                    tgi_sno=item['tgi_sno']).update(**item)

            return Response(serializer.data)
        return Response(
            {"Error": "Required Datas missing grp data / grp item data"})

    def delete(self, request, *args, **kwargs):
        if 'tax_grp_id' in request.query_params:
            tax_grp = self.get_object(request.query_params['tax_grp_id'])
            try:
                tax_grp.delete()
            except ProtectedError:
                return Response({"error_detail": ["Tax Group can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
            return Response({"success": "Record Deleted successfully"},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({"Error": "Provide identifier to delete"})

# Tax GRoup


class TaxgroupmasterAPI(APIView):
    permission_classes = [IsEmployee]

    def get_object(self, obj_id):
        try:
            return Taxgroupmaster.objects.get(tgrp_id=obj_id)
        except Taxgroupmaster.DoesNotExist:
            raise Http404

    # permission_classes=[permissions.AllowAny]
    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = Taxgroupmaster.objects.filter(tgrp_status=1)
            serializer = TaxgroupmasterSerializer(queryset, many=True)
            for data in serializer.data:
                if (Taxgroupitems.objects.filter(tgi_tgrpcode=data['tgrp_id']).exists()):
                    tax_grp_items = Taxgroupitems.objects.filter(
                        tgi_tgrpcode=data['tgrp_id'])
                    tgrp_item_serializer = TaxgroupitemsSerializer(
                        tax_grp_items, many=True)
                    for item in tgrp_item_serializer.data:
                        tax_items = Taxmaster.objects.get(
                            tax_id=item['tgi_taxcode'])
                        tax_serializer = TaxmasterSerializer(
                            tax_items, many=False)
                        item.update(
                            {"tax_percentage": tax_serializer.data['tax_percentage']})
                    data.update({"tax_group_items": tgrp_item_serializer.data})
            return Response(serializer.data)
        tax_grp = Taxgroupmaster.objects.all()
        serializer = TaxgroupmasterSerializer(tax_grp, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        if 'grp_data' and 'grp_item_data' in request.data:
            with transaction.atomic():
                request.data['grp_data'].update(
                    {"created_by": request.user.pk})
                serializer = TaxgroupmasterSerializer(
                    data=request.data['grp_data'])
                serializer.is_valid(raise_exception=True)
                serializer.save()
                for item in request.data['grp_item_data']:

                    tax_grp_item = {
                        "tgi_tgrpcode": serializer.data['tgrp_id'],
                        "tgi_taxcode": item['tgi_taxcode'],
                        "tgi_calculation": item['tgi_calculation'],
                        "tgi_type": item['tgi_type']
                    }
                    tax_item_serializer = TaxgroupitemsSerializer(
                        data=tax_grp_item)
                    tax_item_serializer.is_valid(raise_exception=True)
                    tax_item_serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "Required Data's missing grp data / grp item data"}, status=status.HTTP_400_BAD_REQUEST)


class DepartmentListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Department.objects.filter(is_active=1)
            serializer = DepartmentSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,DEPT_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({'pk_id': data['id_dept'], 'sno': index+1})
        context = {'columns': DEPT_COLUMN_LIST, 'actions': DEPT_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        if Department.objects.filter(dept_code=request.data['dept_code']).exists():
            return Response({"error_detail": ["Department with this Department code already exists"]}, status=status.HTTP_400_BAD_REQUEST)
        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

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
            return Response({"Message": "Department status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = DepartmentSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):

        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = DepartmentSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Department instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DesignationListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Designation.objects.filter(is_active=1)
            serializer = DesignationSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if 'dept' in request.query_params:
            queryset = Designation.objects.filter(
                department=request.query_params['dept'])
            serializer = DesignationSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = Designation.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,DESIGNATION_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            dept = Department.objects.get(id_dept=data['department'])
            data.update({"pk_id": data['id_design'],
                        "sno": index+1, "department": dept.name})
        context = {'columns': DESIGNATION_COLUMN_LIST, 'actions': DESIGNATION_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = DesignationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DesignationDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer

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
            return Response({"Message": "Designation status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = DesignationSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):

        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = DesignationSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Designation instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BankListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Bank.objects.all()
    serializer_class = BankSerializer

    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = Bank.objects.filter(is_active=1)
            serializer = BankSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = Bank.objects.all().order_by('-pk')
        paginator, page = pagination.paginate_queryset(queryset, request,None,BANK_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,BANK_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_bank'], "sno": index+1})
        context = {'columns': columns, 'actions': BANK_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = BankSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BankDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Bank.objects.all()
    serializer_class = BankSerializer

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
            return Response({"Message": "Bank status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = BankSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = BankSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Bank instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentModeListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = PaymentMode.objects.all()
    serializer_class = PaymentModeSerializer

    def get(self, request, *args, **kwargs):
        if 'is_active' in request.query_params:
            queryset = PaymentMode.objects.filter(is_active=1)
            serializer = PaymentModeSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = PaymentMode.objects.all()
        serializer = PaymentModeSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = PaymentModeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentModeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = PaymentMode.objects.all()
    serializer_class = PaymentModeSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Payment Mode status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = PaymentModeSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):

        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = PaymentModeSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["PaymentMode instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AreaListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Area.objects.all()
    serializer_class = AreaSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Area.objects.filter(is_active=1)
            serializer = AreaSerializer(queryset, many=True)
            return Response(serializer.data)
        # paginator, page = pagination.paginate_queryset(self.queryset, request)
        # serializer = self.serializer_class(page, many=True)
        queryset = Area.objects.all().order_by("-id_area")
        serializer = AreaSerializer(queryset, many=True)
        return Response({"rows":serializer.data})

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = AreaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AreaDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Area.objects.all()
    serializer_class = AreaSerializer

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
            return Response({"Message": "Area status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = AreaSerializer(obj)
        output = serializer.data

        output["region"] = [
            {"label": r.region_name, "value": r.id_region}
            for r in obj.region.all()
        ]
        
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = AreaSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Area instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfessionListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Profession.objects.all()
    serializer_class = ProfessionSerializer

    def get(self, request, *args, **kwargs):
        if 'is_active' in request.query_params:
            queryset = Profession.objects.filter(is_active=True)
            serializer = ProfessionSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,PROFESSION_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_profession'], 'sno': index+1})
        context = {
            'columns': PROFESSION_COLUMN_LIST,
            'actions': PROFESSION_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.id})
        serializer = ProfessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProfessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Profession.objects.all()
    serializer_class = ProfessionSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Profession status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ProfessionSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = ProfessionSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Profession instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TenantListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Tenant.objects.filter(status=1)
            serializer = TenantSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = Tenant.objects.all()
        serializer = TenantSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.id})
        serializer = TenantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TenantDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = TenantSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = TenantSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Tenant instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)

# Metal Purity Rate Master


class MetalRatePurityListView(generics.ListCreateAPIView):

    def get(self, request, format=None):
        if metalRatePurityMaster.objects.exists():
            queryset = metalRatePurityMaster.objects.all()
            serializer = MetalRatePurityMasterSerializer(queryset, many=True)
            return Response({"message": "Data Retrieved Successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No Record Found"}, status=status.HTTP_200_OK)


# Metal Purity Rate Master

# Metal Rates
class DailyUpdateMetalRatesView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        request.data.update({"created_by": None})
        # gold_24ct_str = request.data.get('gold_24ct', None)
        # silver_g_str = request.data.get('silver_G', None)

        # if gold_24ct_str is not None:
        #     gold_24ct = float(gold_24ct_str)
        # else:
        #     gold_24ct = 0.0

        # if silver_g_str is not None:
        #     silver_g = float(silver_g_str)
        # else:
        #     silver_g = 0.0

        # gold_24ct = float(gold_24ct_str)
        # silver_g = float(silver_g_str)
        # gold_18ct = format((gold_24ct / 24) * 18, '.2f')
        # gold_20ct = format((gold_24ct / 24) * 20, '.2f')
        # gold_22ct = format((gold_24ct / 24) * 22, '.2f')
        # silver_kg = format(silver_g * 1000, '.2f')

        # request.data.update({"gold_18ct":gold_18ct, "gold_20ct":gold_20ct, "gold_22ct":gold_22ct,
        #                      "gold_24ct":gold_24ct, "silver_G":silver_g, "silver_KG":silver_kg, "status":True})

        serializer = MetalRatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MetalRatesListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        with transaction.atomic():
            request.data.update({"created_by": request.user.pk})
            serializer = MetalRatesSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            print(request.data['send_notification'] == '1')
            print(request.data['send_notification'] == 1)
            print(request.data['send_notification'] == '1' or request.data['send_notification'] == 1)
            if (request.data['send_notification'] == '1' or request.data['send_notification'] == 1):
                send_notification_for_metal_rate()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, format=None):
        if 'latest' in request.query_params:
            if MetalRates.objects.exists():
                response_data = {}
                gold_rate_difference = 0
                silver_rate_difference = 0
                is_gold_rate_increase = False
                is_silver_rate_increase = False
                queryset = MetalRates.objects.all().latest('rate_id')
                serializer = MetalRatesSerializer(queryset)
                try:
                    previous_record = MetalRates.objects.filter(
                        rate_id__lt=serializer.data["rate_id"]).latest('rate_id')
                    previous_serializer = MetalRatesSerializer(previous_record)
                    gold_rate_difference = format_number_with_decimal((float(
                        serializer.data["gold_22ct"]) - float(previous_serializer.data["gold_22ct"])), 2)
                    silver_rate_difference = format_number_with_decimal((float(
                        serializer.data["silver_G"]) - float(previous_serializer.data["silver_G"])), 2)
                    if float(serializer.data["gold_22ct"]) > float(previous_serializer.data["gold_22ct"]):
                        is_gold_rate_increase = True
                    if float(serializer.data["silver_G"]) > float(previous_serializer.data["silver_G"]):
                        is_silver_rate_increase = True
                except ObjectDoesNotExist:
                    previous_record = None  # No previous record exists
                response_data = serializer.data
                response_data["gold_rate_difference"] = gold_rate_difference
                response_data["silver_rate_difference"] = silver_rate_difference
                response_data["is_gold_rate_increase"] = is_gold_rate_increase
                response_data["is_silver_rate_increase"] = is_silver_rate_increase
                return Response({"message": "Data Retrieved Successfully", "data": response_data}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No Record Found"}, status=status.HTTP_200_OK)
        if 'active' in request.query_params:
            queryset = MetalRates.objects.filter(status=1)
            serializer = MetalRatesSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = MetalRates.objects.all().order_by('-rate_id')
        paginator, page = pagination.paginate_queryset(queryset, request,None,METAL_RATE_COLUMN_LIST)
        serializer = MetalRatesSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['rate_id'], "sno": index+1, "date_add": date_format_with_time(data['updatetime']),
                         "datetime": date_format_with_time(data['updatetime'])})
        context = {'columns': METAL_RATE_COLUMN_LIST, 'actions': METAL_RATE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)


class MetalRatesDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = MetalRates.objects.all()
    serializer_class = MetalRatesSerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Metal Rate status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = self.get_serializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        obj = self.get_object()
        request.data.update({"created_by": obj.created_by.pk})
        serializer = self.get_serializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            obj.delete()
        except ProtectedError:
            return Response({"error_detail": ["MetalRate can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NBTypeListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = NBType.objects.all()
    serializer_class = NBTypeSerializer

    def get(self, request, format=None):
        if 'status' in request.query_params:
            queryset = NBType.objects.filter(status=True)
            serializer = NBTypeSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = PayDevice.objects.all()
        serializer = PayDeviceSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = NBTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NBTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = NBType.objects.all()
    serializer_class = NBTypeSerializer

    def get(self, request, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "NB type status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = NBTypeSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, format=None):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = NBTypeSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class PayDeviceListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = PayDevice.objects.all()
    serializer_class = PayDeviceSerializer

    def get(self, request, format=None):
        if 'status' in request.query_params:
            queryset = PayDevice.objects.filter(device_status=1)
            serializer = PayDeviceSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,PAY_DEVICE_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {"pk_id": data['id_device'], 'sno': index+1, "is_active": data['device_status']})
            if (data['device_type'] == 1):
                data.update({"device_type": "Wallet"})
            else:
                data.update({"device_type": "Bank"})
        context = {
            'columns': PAY_DEVICE_COLUMN_LIST,
            'actions': PAY_DEVICE_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = PayDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PayDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    # permission_classes=[permissions.AllowAny]
    queryset = PayDevice.objects.all()
    serializer_class = PayDeviceSerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.device_status == True):
                obj.device_status = False
            else:
                obj.device_status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Pay Device status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = PayDeviceSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):

        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = PayDeviceSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["PayDevice instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentGatewayListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer

    def get(self, request, format=None):
        if 'status' in request.query_params:
            queryset = PaymentGateway.objects.filter(pg_active=1)
            serializer = PaymentGatewaySerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = PaymentGateway.objects.all()
        serializer = PaymentGatewaySerializer(queryset, many=True)
        output = []
        for data in serializer.data:
            instance = {}
            branch = Branch.objects.filter(id_branch=data['id_branch']).get()
            if data['api_type'] == 0:
                instance.update({"api_type": "Demo"})
            if data['api_type'] == 1:
                instance.update({"api_type": "Live"})

            instance.update({"id_pg": data['id_pg'], "pg_name": data['pg_name'], "pg_code": data['pg_code'],
                             "api_url": data['api_url'], "id_branch": branch.name, "is_default": data['is_default'],
                             "pg_active": data['pg_active']})
            if instance not in output:
                output.append(instance)
        return Response(output, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = PaymentGatewaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentGatewayDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    # permission_classes=[permissions.AllowAny]
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.pg_active == True):
                obj.pg_active = False
            else:
                obj.pg_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Payment gateway status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = PaymentGatewaySerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):

        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = PaymentGatewaySerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["PaymentGateway instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        queryset = Profile.objects.all()
        if 'is_active' in self.request.query_params:
            queryset = queryset.filter(is_active=1)
        return queryset

    def get(self, request, *args, **kwargs):
        if 'is_active' in request.query_params:
            queryset = Profile.objects.filter(is_active=1)
            serializer = ProfileSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request,None,PROFILE_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        for idx, data in enumerate(serializer.data):
            data.update({"sno": idx+1})
            data.update({"pk_id": data['id_profile']})
        # Return the paginated response
        context = {'columns': PROFILE_COLUMN_LIST, 'actions': PROFILE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = ProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Profile status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ProfileSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = ProfileSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Profession instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExchangeRatesView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = ExchangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        queryset = ExchangeRate.objects.all()
        output = [{"id_exchange": each.id_exchange, "from_currency": each.from_currency.name, "to_currency": each.to_currency.name, "rate": each.rate}
                  for each in queryset]
        return Response(output, status=status.HTTP_200_OK)


class ExchangeRatesDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    # permission_classes=[permissions.AllowAny]
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        output = serializer.data
        output.update({"from_currency": {"value": obj.from_currency.pk, "label": obj.from_currency.name},
                       "to_currency": {"value": obj.to_currency.pk, "label": obj.to_currency.name},
                       "rate": obj.rate,
                       "id_exchange": obj.id_exchange,
                       })
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            obj.delete()
        except ProtectedError:
            return Response({"error_detail": ["Exchange Rate can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_202_ACCEPTED)


class BannerList(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee | IsCustomerUser]
    serializer_class = BannerSerializer
    queryset = Banner.objects.all()

    def get(self, request, *args, **kwargs):
        # if 'status' in request.query_params:
        queryset = Banner.objects.filter(banner_status=True)
        serializer = BannerSerializer(queryset, many=True,context={'request':request})
        output =[]
        for data in serializer.data:
            instance = {}
            instance.update({
                "banner_id":data['banner_id'],
               "banner_name":data['banner_name'],
               "banner_img":data['banner_img'],
               "link":data['link'],
            })
            if instance not in output:
                output.append(instance)
        return Response({"data":output})
        # paginator, page = pagination.paginate_queryset(self.queryset, request,None,BANNER_COLUMN_LIST)
        # columns = get_reports_columns_template(request.user.pk,BANNER_COLUMN_LIST,request.query_params.get("path_name",''))
        # serializer = self.serializer_class(page, many=True, context={'request':request})
        # for index, data in enumerate(serializer.data):
        #     data.update(
        #         {'pk_id': data['banner_id'], 'sno': index+1, 'is_active': data['banner_status'],
        #          'image':data['banner_img']})
        # context = {'columns': columns, 'actions': BANNER_ACTION_LIST,
        #           'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        # return pagination.paginated_response(serializer.data, context)

class BannerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee | IsCustomerUser]
    serializer_class = BannerSerializer
    queryset = Banner.objects.all()
    
    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Banner.objects.filter(banner_status=True)
            serializer = BannerSerializer(queryset, many=True,context={'request':request})
            return Response({"data":serializer.data})
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,BANNER_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,BANNER_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True, context={'request':request})
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['banner_id'], 'sno': index+1, 'is_active': data['banner_status'],
                 'image':data['banner_img']})
        context = {'columns': columns, 'actions': BANNER_ACTION_LIST,
                  'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Banner.objects.filter(banner_id=request.data['id']).update(
                banner_status=request.data['status'])
            # serializer = self.get_serializer(queryset)
            return Response(status=status.HTTP_202_ACCEPTED)
        request.data.update({"created_by": request.user.pk})
        if (request.data['banner_img'] == None):
            return Response({"error": "Image is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # b = ((base64.b64decode(request.data['banner_img']
        #                        [request.data['banner_img'].find(",") + 1:])))
        # img = Image.open(io.BytesIO(b))
        # filename = 'banner.jpeg'
        # img_object = ImageFile(io.BytesIO(
        #     img.fp.getvalue()), name=filename)
        img_object = base64_to_file(request.data['banner_img'], filename_prefix="banner",file_extension="jpeg")
        compressed_image = compress_image(img_object)
        request.data.update({"banner_img": compressed_image})
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# RetrieveUpdateDestroy  api for  Banner entries in Admin panel
class BannerDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    serializer_class = BannerSerializer
    queryset = Banner.objects.all()

    def get(self, request, *args, **kwargs):
        banner = self.get_object()
        serializer = self.get_serializer(banner)
        output = serializer.data
        output.update({"created_by": banner.created_by.username,
                       "updated_by": banner.updated_by.username if banner.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk,
                             'updated_by': request.user.pk,
                             'updated_on': datetime.now(tz=timezone.utc)})
        if (request.data['banner_img'] != None):
            if 'data:image/' in request.data['banner_img'][:30]:
                # update items  for which image is changed
                queryset.banner_img.delete()
                # b = (
                #     (base64.b64decode(request.data['banner_img'][request.data['banner_img'].find(",") + 1:])))
                # img = Image.open(io.BytesIO(b))
                # filename = 'banner.jpeg'
                # img_object = ImageFile(io.BytesIO(
                #     img.fp.getvalue()), name=filename)
                img_object = base64_to_file(request.data['banner_img'], filename_prefix="banner",file_extension="jpeg")
                compressed_image = compress_image(img_object)
                request.data.update({"banner_img": compressed_image})

                serializer = self.get_serializer(queryset, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            # del request.data['banner_img']
            # serializer = self.get_serializer(queryset, data=request.data)
            # serializer.is_valid(raise_exception=True)
            # serializer.save()
            queryset.banner_name = request.data['banner_name']
            queryset.banner_status = request.data['banner_status']
            queryset.banner_description = request.data['banner_description']
            queryset.link = request.data['link']
            queryset.updated_by = request.user
            queryset.updated_on = datetime.now(tz=timezone.utc)
            queryset.save()
            serializer = self.get_serializer(queryset)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            queryset.banner_name = request.data['banner_name']
            queryset.banner_status = request.data['banner_status']
            queryset.banner_description = request.data['banner_description']
            queryset.link = request.data['link']
            queryset.updated_by = request.user
            queryset.updated_on = datetime.now(tz=timezone.utc)
            queryset.save()
            serializer = self.get_serializer(queryset)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        banner = self.get_object()
        banner.banner_img.delete()
        banner.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BranchEntryDate:

    def get_entry_date(self, id_branch):
        queryset = ErpDayClosed.objects.get(id_branch=id_branch)
        try:
            entry_date = queryset.entry_date
        except ErpDayClosed.DoesNotExist:
            raise ValueError(
                "Branch entry date not found for the given branch.")
        return entry_date


class WeightRangeListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = WeightRange.objects.all()
    serializer_class = WeightRangeSerializer

    def get(self, request, *args, **kwargs):
        subquery = WeightRange.objects.filter(id_product=OuterRef(
            'id_product')).order_by('id_weight_range').values('id_weight_range')[:1]

        queryset = WeightRange.objects.annotate(first_id=Subquery(
            subquery), count=Count('id_product')).filter(id=OuterRef('first_id'))
        paginator, page = pagination.paginate_queryset(queryset, request,None,WEIGHT_RANGE_COLUMN_LIST)
        serializer = WeightRangeSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_product'], 'sno': index+1})
        context = {'columns': WEIGHT_RANGE_COLUMN_LIST, 'actions': WEIGHT_RANGE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)


    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            product = request.data['product']
            weight_range_datas = []
            if (WeightRange.objects.filter(id_product=product).exists()):
                ids_to_delete = []
                existing_items = WeightRange.objects.filter(id_product=product)
                existing_item_map = {item.pk: item for item in existing_items}
                ids_to_delete = set(existing_item_map.keys())
                for detail in request.data['weight_ranges']:
                    from_weight = float(detail['from_weight'])
                    to_weight = float(detail['to_weight'])
                    try:
                        id_weight_range = detail.get('id_weight_range')
                        if isinstance(id_weight_range,int) :
                            ids_to_delete.discard(id_weight_range)
                            try:
                                instance = WeightRange.objects.get(pk=id_weight_range)
                                serializer = WeightRangeSerializer(instance, data=detail, partial=True)
                                validate_weight_range(
                                    from_weight, to_weight, product,instance.pk)
                                if serializer.is_valid(raise_exception=True):
                                    serializer.save()
                            except WeightRange.DoesNotExist:
                                validate_weight_range(
                                    from_weight, to_weight, product)
                                detail.update({"created_by": request.user.pk,"id_product": product})
                                serializer = WeightRangeSerializer(data=detail)
                                serializer.is_valid(raise_exception=True)
                                serializer.save()
                        else:
                            validate_weight_range(
                                    from_weight, to_weight, product)
                            detail.update({"created_by": request.user.pk,"id_product": product})
                            serializer = WeightRangeSerializer(data=detail)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()
                    except ValidationError as e:
                        del detail

                if ids_to_delete:
                    WeightRange.objects.filter(pk__in=ids_to_delete).delete()
            # if (len(weight_range_datas) == 0):
            #     return Response({"message": "The weight range overlaps with an existing range for the same product."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Weight ranges Updated successfully."}, status=status.HTTP_201_CREATED)



    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            products = request.data['product']
            weight_range_datas = []

            for product in products:
                if (WeightRange.objects.filter(id_product=product).exists()):
                    return Response({"message": "Weight range already exists for this product."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    for data in request.data['weight_ranges']:
                        from_weight = float(data['from_weight'])
                        to_weight = float(data['to_weight'])
                        try:
                            validate_weight_range(
                                from_weight, to_weight, product)
                            weight_range_datas.append(data)
                            data.update({"created_by": request.user.pk,"id_product": product})
                            serializer = WeightRangeSerializer(data=data)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()
                        except ValidationError as e:
                            del data
                        # return Response({'error': str(e)}, status=400)

            if (len(weight_range_datas) == 0):
                return Response({"message": "The weight range overlaps with an existing range for the same product."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Weight ranges created successfully."}, status=status.HTTP_201_CREATED)

def validate_weight_range(from_weight, to_weight, id_product,id=None):
    if id != None:
        overlaps = WeightRange.objects.filter(id_product=id_product).exclude(id_weight_range=id).filter(
            Q(from_weight__lt=to_weight) & Q(to_weight__gt=from_weight))
        if overlaps.exists():
            raise ValidationError(
                'The weight range overlaps with an existing range for the same product.')
    else:
        overlaps = WeightRange.objects.filter(id_product=id_product).filter(
            Q(from_weight__lt=to_weight) & Q(to_weight__gt=from_weight))
        if overlaps.exists():
            raise ValidationError(
                'The weight range overlaps with an existing range for the same product.')
class WeightRangeDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = WeightRange.objects.all()
    serializer_class = WeightRangeSerializer

    def get(self, request, *args, **kwargs):
        output = []
        queryset = WeightRange.objects.filter(id_product=kwargs['pk'])
        serializer = WeightRangeSerializer(queryset, many=True)
        for data in serializer.data:
            if data not in output:
                output.append(data)
        instance = {"weight_ranges": output}
        return Response(instance, status=status.HTTP_200_OK)

    

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Weight Range instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SizeListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Size.objects.all()
    serializer_class = SizeSerializer

    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = Size.objects.filter(active=True)
            serializer = SizeSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,SIZE_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,SIZE_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_size'], 'sno': index+1, 'is_active': data['active']})
        context = {'columns': columns, 'actions': SIZE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = SizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SizeDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Size.objects.all()
    serializer_class = SizeSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.active == True):
                obj.active = False
            else:
                obj.active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Payment gateway status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = SizeSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = SizeSerializer(queryset, data=request.data)
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


class SupplierListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def get(self, request, *args, **kwargs):
        if 'local_vendors' in request.query_params:
            queryset = Supplier.objects.filter(status=True, is_vendor=6)
            serializer = SupplierSerializer(queryset, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        if 'active' in request.query_params:
            queryset = Supplier.objects.filter(status=True)
            serializer = SupplierSerializer(queryset, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        queryset = Supplier.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None, SUPPLIER_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,SUPPLIER_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = SupplierSerializer(
            page, many=True, context={"request": request})
        for index, data in enumerate(serializer.data):
            data.update(
                {"pk_id": data['id_supplier'], "sno": index+1, "is_active": data['status']})
            if (data['image'] == None):
                data.update(
                    {"image": None, "image_text": data['supplier_name'][0]})
            if (data['image'] != None):
                data.update(
                    {"image": data['image'], "image_text": data['supplier_name'][0]})
        FILTERS['isDateFilterReq'] = True
        context = {
            'columns': columns,
            'actions': SUPPLIER_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            supplier_account_details = request.data['supplier_account_details']
            staff_details = request.data['staff_details']
            del request.data['staff_details']
            del request.data['supplier_account_details']
            request.data.update({"created_by": request.user.pk})
            if (request.data['img'] != None):
                b = ((base64.b64decode(request.data['img']
                                       [request.data['img'].find(",") + 1:])))
                img = Image.open(io.BytesIO(b))
                filename = 'supplier_img.jpeg'
                img_object = ImageFile(io.BytesIO(
                    img.fp.getvalue()), name=filename)
                request.data.update({"image": img_object})
            else:
                request.data.update({"image": None})
            serializer = SupplierSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            for acc_detail in supplier_account_details:
                acc_detail.update({"supplier": serializer.data['id_supplier']})
                acc_detail_serializer = SupplierAccountDetailSerializer(
                    data=acc_detail)
                acc_detail_serializer.is_valid(raise_exception=True)
                acc_detail_serializer.save()
            for staff_det in staff_details:
                staff_det.update({"supplier": serializer.data['id_supplier']})
                staff_detail_serializer = SupplierStaffDetailSerializer(
                    data=staff_det)
                staff_detail_serializer.is_valid(raise_exception=True)
                staff_detail_serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierDetailView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        if ('changestatus' in request.query_params):
            if (queryset.status == True):
                queryset.status = False
            else:
                queryset.status = True
            queryset.updated_by = self.request.user
            queryset.updated_on = datetime.now(tz=timezone.utc)
            queryset.save()
            return Response({"Message": "Supplier status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = self.get_serializer(
            queryset, context={"request": request})
        output = serializer.data
        staff_details = SupplierStaffDetails.objects.filter(
            supplier=queryset.id_supplier)
        staff_details_serializer = SupplierStaffDetailSerializer(
            staff_details, many=True)
        account_details = SupplierAccountDetails.objects.filter(
            supplier=queryset.id_supplier)
        account_details_serializer = SupplierAccountDetailSerializer(
            account_details, many=True)
        output.update({"created_by": queryset.created_by.username,
                       "updated_by": queryset.updated_by.username if queryset.updated_by != None else None,
                       "staff_details": staff_details_serializer.data, "account_details": account_details_serializer.data})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            queryset = self.get_object()
            supplier_account_details = request.data['supplier_account_details']
            staff_details = request.data['staff_details']
            del request.data['staff_details']
            del request.data['supplier_account_details']
            request.data.update({"created_by": queryset.created_by.pk, "updated_by": request.user.pk,
                                 "updated_on": datetime.now(tz=timezone.utc)})
            if (request.data['img'] != None):
                if 'data:image/' in request.data['img'][:30]:
                    # update items  for which image is changed
                    queryset.image.delete()
                    b = (
                        (base64.b64decode(request.data['img'][request.data['img'].find(",") + 1:])))
                    img = Image.open(io.BytesIO(b))
                    filename = 'supplier_img.jpeg'
                    img_object = ImageFile(io.BytesIO(
                        img.fp.getvalue()), name=filename)
                    request.data.update({"image": img_object})

                    serializer = self.get_serializer(
                        queryset, data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    if SupplierStaffDetails.objects.filter(supplier=queryset.id_supplier).exists():
                        SupplierStaffDetails.objects.filter(
                            supplier=queryset.id_supplier).delete()
                    for staff_det in staff_details:
                        staff_det.update({"supplier": queryset.id_supplier})
                        staff_detail_serializer = SupplierStaffDetailSerializer(
                            data=staff_det)
                        staff_detail_serializer.is_valid(raise_exception=True)
                        staff_detail_serializer.save()
                    if SupplierAccountDetails.objects.filter(supplier=queryset.id_supplier).exists():
                        SupplierAccountDetails.objects.filter(
                            supplier=queryset.id_supplier).delete()
                    for acc_detail in supplier_account_details:
                        acc_detail.update({"supplier": queryset.id_supplier})
                        acc_detail_serializer = SupplierAccountDetailSerializer(
                            data=acc_detail)
                        acc_detail_serializer.is_valid(raise_exception=True)
                        acc_detail_serializer.save()
                    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                del request.data['img']
                serializer = self.get_serializer(queryset, data=request.data,partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                if SupplierStaffDetails.objects.filter(supplier=queryset.id_supplier).exists():
                    SupplierStaffDetails.objects.filter(
                        supplier=queryset.id_supplier).delete()
                for staff_det in staff_details:
                    staff_det.update({"supplier": queryset.id_supplier})
                    staff_detail_serializer = SupplierStaffDetailSerializer(
                        data=staff_det)
                    staff_detail_serializer.is_valid(raise_exception=True)
                    staff_detail_serializer.save()
                if SupplierAccountDetails.objects.filter(supplier=queryset.id_supplier).exists():
                    SupplierAccountDetails.objects.filter(
                        supplier=queryset.id_supplier).delete()
                for acc_detail in supplier_account_details:
                    acc_detail.update({"supplier": queryset.id_supplier})
                    acc_detail_serializer = SupplierAccountDetailSerializer(
                        data=acc_detail)
                    acc_detail_serializer.is_valid(raise_exception=True)
                    acc_detail_serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            else:
                serializer = self.get_serializer(queryset, data=request.data,partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                if SupplierStaffDetails.objects.filter(supplier=queryset.id_supplier).exists():
                    SupplierStaffDetails.objects.filter(
                        supplier=queryset.id_supplier).delete()
                for staff_det in staff_details:
                    staff_det.update({"supplier": queryset.id_supplier})
                    staff_detail_serializer = SupplierStaffDetailSerializer(
                        data=staff_det)
                    staff_detail_serializer.is_valid(raise_exception=True)
                    staff_detail_serializer.save()
                if SupplierAccountDetails.objects.filter(supplier=queryset.id_supplier).exists():
                    SupplierAccountDetails.objects.filter(
                        supplier=queryset.id_supplier).delete()
                for acc_detail in supplier_account_details:
                    acc_detail.update({"supplier": queryset.id_supplier})
                    acc_detail_serializer = SupplierAccountDetailSerializer(
                        data=acc_detail)
                    acc_detail_serializer.is_valid(raise_exception=True)
                    acc_detail_serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Karigar instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)

class SupplierProductView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        queryset = SupplierProducts.objects.filter(supplier=kwargs['pk']).first()
        serializer = SupplierProductsSerializer(queryset)
        output = serializer.data
        supplier_product_details = SupplierProductDetails.objects.filter(supplier_product=queryset.pk)
        supplier_product_details_serializer = SupplierProductDetailsSerializer(supplier_product_details, many=True)
        for data in supplier_product_details_serializer.data:
            supplier_product_image = SupplierProductImageDetails.objects.filter(supplier_product_details=data['id'])
            supplier_product_image_serializer = SupplierProductImageDetailsSerializer(supplier_product_image, many=True, context={"request":request})
            for images in supplier_product_image_serializer.data:
                images.update({"id":images['id'], "default":False, "preview":images['image']})
            data.update({"image":supplier_product_image_serializer.data})
        output.update({"supplier_product_details":supplier_product_details_serializer.data})
        return Response(output, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            request.data.update({"created_by": request.user.pk})
            supplier_product_details = request.data['supplier_product_details']
            del request.data['supplier_product_details']
            if(SupplierProducts.objects.filter(supplier=request.data['supplier']).exists()):    
                queryset = SupplierProducts.objects.filter(supplier=request.data['supplier']).get()
                
                exist_prod_details = SupplierProductDetails.objects.filter(supplier_product=queryset.pk)
                exist_prod_detail_serializer = SupplierProductDetailsSerializer(exist_prod_details, many=True)
                for exist_data in exist_prod_detail_serializer.data:
                    SupplierProductImageDetails.objects.filter(supplier_product_details=exist_data['id']).delete()
                exist_prod_details.delete()
                supplier_product = queryset.pk
                queryset.show_wastage_details = request.data['show_wastage_details']
                queryset.show_macking_charge_details = request.data['show_macking_charge_details']
                queryset.updated_by = self.request.user
                queryset.updated_on = datetime.now(tz=timezone.utc)
                queryset.save()
                serializer = SupplierProductsSerializer(queryset)
            else:
                serializer = SupplierProductsSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                supplier_product = serializer.data['id']
            for data in supplier_product_details:
                images = data['image']
                del data['image']
                data.update({"supplier_product": supplier_product})
                supplier_product_detail_serializer = SupplierProductDetailsSerializer(data=data)
                supplier_product_detail_serializer.is_valid(raise_exception=True)
                supplier_product_detail_serializer.save()
                for index,image_data in enumerate(images):
                    if (image_data['image'] != None):
                        file_num = index + 1
                        file_id = supplier_product_detail_serializer.data['id']
                        name = 'product_detail_image_' + str(file_num)+ "_of_" + str(file_id)
                        b = ((base64.b64decode(image_data['image']
                                                [image_data['image'].find(",") + 1:])))
                        img = Image.open(io.BytesIO(b))
                        filename = 'product_detail_image.jpeg'
                        img_object = ImageFile(io.BytesIO(
                            img.fp.getvalue()), name=filename)
                        image_data.update({"image": img_object, "image_name":name})
                    image_data.update({"supplier_product_details":supplier_product_detail_serializer.data['id']})
                    image_serializer = SupplierProductImageDetailsSerializer(data=image_data)
                    image_serializer.is_valid(raise_exception=True)
                    image_serializer.save()
            
            return Response(serializer.data, status=status.HTTP_200_OK)


class AttributeEntryListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = AttributeEntry.objects.all()
    serializer_class = AttributeEntrySerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = AttributeEntry.objects.filter(is_active=1)
            serializer = AttributeEntrySerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,ATTRIBUTE_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_attribute'], 'sno': index+1})
        context = {
            'columns': ATTRIBUTE_COLUMN_LIST,
            'actions': ATTRIBUTE_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = AttributeEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AttributeEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = AttributeEntry.objects.all()
    serializer_class = AttributeEntrySerializer

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
            return Response({"Message": "Attribute status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = AttributeEntrySerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = AttributeEntrySerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Attribute instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OtherChargesListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = OtherCharges.objects.all()
    serializer_class = OtherChargesSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = OtherCharges.objects.filter(is_active=1)
            serializer = OtherChargesSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,OTHER_CHARGES_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_other_charge'], 'sno': index+1})
        context = {
            'columns': OTHER_CHARGES_COLUMN_LIST,
            'actions': OTHER_CHARGES_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = OtherChargesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OtherChargesDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = OtherCharges.objects.all()
    serializer_class = OtherChargesSerializer

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
            return Response({"Message": "Other Charges status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = OtherChargesSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = OtherChargesSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Other Charges instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockIssueTypeListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = StockIssueType.objects.all()
    serializer_class = StockIssueTypeSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = StockIssueType.objects.filter(is_active=1)
            serializer = StockIssueTypeSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = StockIssueType.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None, STOCK_ISSUE_TYPE_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_stock_issue_type'], "sno": index+1})
        context = {'columns': STOCK_ISSUE_TYPE_COLUMN_LIST, 'actions': STOCK_ISSUE_TYPE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = StockIssueTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StockIssueTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = StockIssueType.objects.all()
    serializer_class = StockIssueTypeSerializer

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
            return Response({"Message": "Stock Issue status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = StockIssueTypeSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = StockIssueTypeSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Stock Issue instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FloorListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Floor.objects.filter(is_active=1)
            serializer = FloorSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,FLOOR_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            br = Branch.objects.get(id_branch=data['id_branch'])
            data.update({"pk_id": data['id_floor'],
                        'sno': index+1, "branch": br.name})
        context = {
            'columns': FLOOR_COLUMN_LIST,
            'actions': FLOOR_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = FloorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FloorDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer

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
            return Response({"Message": "Floor status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = FloorSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = FloorSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Floor instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CounterListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Counter.objects.all()
    serializer_class = CounterSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Counter.objects.filter(is_active=1)
            serializer = CounterSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,COUNTER_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            flr = Floor.objects.get(id_floor=data['id_floor'])
            data.update({
                "pk_id": data['id_counter'],
                'sno': index+1, 
                "floor": flr.floor_name,
                "id_branch":flr.id_branch.pk
            })
        context = {
            'columns': COUNTER_COLUMN_LIST,
            'actions': COUNTER_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = CounterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CounterDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Counter.objects.all()
    serializer_class = CounterSerializer

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
            return Response({"Message": "Counter status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = CounterSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = CounterSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Counter instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisteredDevicesListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = RegisteredDevices.objects.all()
    serializer_class = RegisteredDevicesSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = RegisteredDevices.objects.filter(is_active=1)
            serializer = RegisteredDevicesSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,REGISTERED_DEVICES_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            contr = Counter.objects.get(id_counter=data['id_counter'])
            data.update({"pk_id": data['id_registered_device'],
                         'sno': index+1, "counter": contr.counter_name})
        context = {
            'columns': REGISTERED_DEVICES_COLUMN_LIST,
            'actions': REGISTERED_DEVICES_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = RegisteredDevicesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegisteredDevicesDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = RegisteredDevices.objects.all()
    serializer_class = RegisteredDevicesSerializer

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
            return Response({"Message": "Registered Device status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = RegisteredDevicesSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = RegisteredDevicesSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Registered Device instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


def delete_container_pdfs():
    container_dir = os.path.join(settings.MEDIA_ROOT, 'container')

    # Check if the container directory exists
    if os.path.exists(container_dir):
        # Iterate over each file in the container directory and delete
        for root, dirs, files in os.walk(container_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Optionally, remove empty folders as well
        for root, dirs, _ in os.walk(container_dir, topdown=False):
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))


def delete_container_pdfs_with_delay(delay=6):
    time.sleep(delay)
    delete_container_pdfs()


def generate_container_qr(skuid, pkid, name, request):

    print_data = {}
    code = skuid
    id = pkid
    save_dir = os.path.join(settings.MEDIA_ROOT, f'container/{id}')
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

    print_data.update({"qr_path": qr_path, "name": name, "uid": code})
    template = get_template('container_print.html')
    html = template.render({'data': print_data})
    result = io.BytesIO()
    pisa.pisaDocument(io.StringIO(html), result)
    pdf_path = os.path.join(save_dir, 'container.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(result.getvalue())
    pdf_path = request.build_absolute_uri(
        settings.MEDIA_URL + f'container/{id}/container.pdf')
    return pdf_path


class ContainerPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        output = {}
        pdf_url = generate_container_qr(obj.sku_id, obj.id_container, obj.container_name,
                                        request)
        output.update({"pdf_url": pdf_url})
        threading.Thread(
            target=delete_container_pdfs_with_delay, args=(6,)).start()
        return Response(output, status=status.HTTP_200_OK)


class ContainerListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer

    def get_queryset(self):
        queryset = Container.objects.all()
        if 'is_active' in self.request.query_params:
            queryset = queryset.filter(is_active=1)
        return queryset

    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = Container.objects.filter(is_active=1)
            serializer = ContainerSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request,None,CONTAINER_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        for idx, data in enumerate(serializer.data):
            bran = Branch.objects.get(id_branch=data['branch'])
            data.update({"sno": idx+1})
            data.update({"pk_id": data['id_container'], "branch": bran.name})
        # Return the paginated response
        context = {'columns': CONTAINER_COLUMN_LIST, 'actions': CONTAINER_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = ContainerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output = serializer.data
        pdf_url = generate_container_qr(serializer.data['sku_id'], serializer.data['id_container'], serializer.data['container_name'],
                                        request)
        output.update({"pdf_url": pdf_url})
        threading.Thread(
            target=delete_container_pdfs_with_delay, args=(6,)).start()
        return Response(output, status=status.HTTP_201_CREATED)


class ContainerDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Profile status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ContainerSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = ContainerSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Container instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OldMetalItemTypeListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = OldMetalItemType.objects.all()
    serializer_class = OldMetalItemTypeSerializer

    def get_queryset(self):
        queryset = OldMetalItemType.objects.all()
        if 'active' in self.request.query_params:
            queryset = queryset.filter(is_active=1)
        return queryset

    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = OldMetalItemType.objects.filter(is_active=1)
            serializer = OldMetalItemTypeSerializer(queryset, many=True)
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request,None,OLD_METAL_ITEM_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        for idx, data in enumerate(serializer.data):
            met = Metal.objects.get(id_metal=data['id_metal'])
            data.update({"sno": idx+1})
            data.update({"pk_id": data['id_item_type'],
                         "metal": met.metal_name
                         })
        # Return the paginated response
        context = {'columns': OLD_METAL_ITEM_COLUMN_LIST, 'actions': OLD_METAL_ITEM_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = OldMetalItemTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OldMetalItemTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = OldMetalItemType.objects.all()
    serializer_class = OldMetalItemTypeSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Old Metal Item status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = OldMetalItemTypeSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = OldMetalItemTypeSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Old Metal Item instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OtherWeightListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = OtherWeight.objects.all()
    serializer_class = OtherWeightSerializer

    def get_queryset(self):
        queryset = OtherWeight.objects.all()
        if 'active' in self.request.query_params:
            queryset = queryset.filter(is_active=1)
        return queryset

    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = OtherWeight.objects.filter(is_active=1)
            serializer = OtherWeightSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request,None,OTHER_WEIGHT_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        for idx, data in enumerate(serializer.data):
            data.update({"sno": idx+1})
            data.update({"pk_id": data['id_other_weight_master'],
                         })
        # Return the paginated response
        context = {'columns': OTHER_WEIGHT_COLUMN_LIST, 'actions': OTHER_WEIGHT_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = OtherWeightSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OtherWeightDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = OtherWeight.objects.all()
    serializer_class = OtherWeightSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Other Weight status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = OtherWeightSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = OtherWeightSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Other Weight instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CashOpeningBalanceListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = CashOpeningBalance.objects.all()
    serializer_class = CashOpeningBalanceSerializer

    def get_queryset(self):
        queryset = CashOpeningBalance.objects.all()
        if 'active' in self.request.query_params:
            queryset = queryset.filter(is_active=1)
        return queryset

    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = CashOpeningBalance.objects.filter(is_active=1)
            serializer = CashOpeningBalanceSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request,None,CASH_OPENING_BALANCE_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        for idx, data in enumerate(serializer.data):
            bran = Branch.objects.get(id_branch=data['branch'])
            data.update({"sno": idx+1})
            data.update({"pk_id": data['id_opening_balance'], "branch": bran.name
                         })
        # Return the paginated response
        context = {'columns': CASH_OPENING_BALANCE_COLUMN_LIST, 'actions': CASH_OPENING_BALANCE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = CashOpeningBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CashOpeningBalanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = CashOpeningBalance.objects.all()
    serializer_class = CashOpeningBalanceSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Cash Opening Balance status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = CashOpeningBalanceSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = CashOpeningBalanceSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Cash Opening Balance instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountHeadListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = AccountHead.objects.all()
    serializer_class = AccountHeadSerializer

    def get_queryset(self):
        queryset = AccountHead.objects.all()
        if 'active' in self.request.query_params:
            queryset = queryset.filter(is_active=1)
        return queryset

    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = AccountHead.objects.filter(is_active=1)
            serializer = AccountHeadSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = self.get_queryset().order_by('-pk')
        paginator, page = pagination.paginate_queryset(queryset, request,None,ACCOUNT_HEAD_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        for idx, data in enumerate(serializer.data):
            if (data['type'] == 1):
                data.update({"type": "Issue"})
            elif (data['type'] == 2):
                data.update({"type": "Receipt"})
            else:
                data.update({"type": "Others"})
                
            data.update({"sno": idx+1})
            data.update({"pk_id": data['id_account_head'],
                         })
        # Return the paginated response
        context = {'columns': ACCOUNT_HEAD_COLUMN_LIST, 'actions': ACCOUNT_HEAD_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = AccountHeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccountHeadDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = AccountHead.objects.all()
    serializer_class = AccountHeadSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Account Head status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = AccountHeadSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = AccountHeadSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Account Head instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BankDepositListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = BankDeposit.objects.all()
    serializer_class = BankDepositSerializer

    def get(self, request, format=None):
        if 'active' in request.query_params:
            queryset = BankDeposit.objects.filter(is_active=1)
            serializer = BankDepositSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = BankDeposit.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,BANK_DEPOSIT_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_bank_deposit'], "sno": index+1,"entry_date": format_date(data['entry_date']),})
        context = {'columns': BANK_DEPOSIT_COLUMN_LIST, 'actions': BANK_DEPOSIT_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        branch_date = BranchEntryDate()
        invoice_date = branch_date.get_entry_date(request.data['branch'])
        request.data.update({"created_by": request.user.id,'entry_date':invoice_date})
        serializer = BankDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BankDepositDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = BankDeposit.objects.all()
    serializer_class = BankDepositSerializer

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
            return Response({"Message": "Bank status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = BankDepositSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = BankDepositSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Bank Deposit instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DepositMasterListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = DepositMaster.objects.all()
    serializer_class = DepositMasterSerializer
    
    def get(self, request, format=None):
        queryset = DepositMaster.objects.all()
        if 'active' in request.query_params:
            output = []
            serializer = DepositMasterSerializer(queryset, many=True)
            for data in serializer.data:
                if data not in output:
                    output.append(data)
            return Response(output, status=status.HTTP_200_OK)
        paginator, page = pagination.paginate_queryset(queryset, request,None,DEPOSIT_MASTER_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,DEPOSIT_MASTER_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            # schem = Scheme.objects.get(scheme_id=data['scheme'])
            data.update({"pk_id": data['id_deposit_master'], "sno": index+1})
            
            if(data['type']==1):
                data.update({"type": "Amount"})
            elif(data['type']==2):
                data.update({"type": "Weight"})
            elif(data['type']==3):
                data.update({"type": "Both"})
                
            if(data['payable_type']==1):
                data.update({"payable_type": "Fixed"})
            elif(data['payable_type']==2):
                data.update({"payable_type": "Flexible"})
                
            if(data['interest_type']==1):
                data.update({"interest_type": "Fixed"})
            elif(data['interest_type']==2):
                data.update({"interest_type": "Time period"})
                
            if(data['interest']==1):
                data.update({"interest": "Yes"})
            elif(data['interest']==2):
                data.update({"interest": "No"})
                
            
        context = {'columns': columns, 'actions': DEPOSIT_MASTER_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            interest_details = request.data['interest_details']
            del request.data['interest_details']
            request.data.update({"created_by": request.user.id})
            serializer = DepositMasterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if(request.data['interest_type']==2):
                for data in interest_details:
                    from_days = int(data['from_days'])
                    to_days = int(data['to_days'])
                    data.update({"from_days":from_days,"to_days":to_days,"deposit_master": serializer.data['id_deposit_master']})
                    settings_serializer = DepositMasterInterestSerializer(data=data)
                    settings_serializer.is_valid(raise_exception=True)
                    settings_serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
class DepositMasterDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = DepositMaster.objects.all()
    serializer_class = DepositMasterSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = DepositMasterSerializer(queryset)
        output = serializer.data
        settings_data = DepositMasterInterest.objects.filter(deposit_master=queryset.id_deposit_master)
        settings_data_serializer = DepositMasterInterestSerializer(settings_data, many=True)
        output.update({"created_by": queryset.created_by.username,
                       "updated_by": queryset.updated_by.username if queryset.updated_by != None else None,
                       "deposit_master_settings":settings_data_serializer.data})
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            interest_details = request.data['interest_details']
            del request.data['interest_details']
            
            queryset = self.get_object()
            request.data.update({"created_by": queryset.created_by.id})
            serializer = DepositMasterSerializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)

        
            if(request.data['interest_type']==2):
                if DepositMasterInterest.objects.filter(deposit_master=queryset.id_deposit_master).exists():
                    DepositMasterInterest.objects.filter(deposit_master=queryset.id_deposit_master).delete()
                for data in interest_details:
                    from_days = int(data['from_days'])
                    to_days = int(data['to_days'])
                    data.update({"from_days":from_days,"to_days":to_days,"deposit_master": queryset.id_deposit_master})
                    settings_serializer = DepositMasterInterestSerializer(data=data)
                    settings_serializer.is_valid(raise_exception=True)
                    settings_serializer.save()
            serializer.save(updated_by=self.request.user,
                            updated_on=datetime.now(tz=timezone.utc))
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    
    def delete(self, request, *args, **kwargs):
        with transaction.atomic():
            queryset = self.get_object()
            try:
                DepositMasterInterest.objects.filter(deposit_master=queryset.id_deposit_master).delete()
                queryset.delete()
            except ProtectedError:
                return Response({"error_detail": ["Deposit Master instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
            return Response(status=status.HTTP_204_NO_CONTENT)
        
class CustomerDepositListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = CustomerDeposit.objects.all()
    serializer_class = CustomerDepositSerializer
    
    def get(self, request, format=None):
        queryset = CustomerDeposit.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,CUSTOMER_DEPOSIT_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,CUSTOMER_DEPOSIT_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id'], "sno": index+1})
        context = {'columns': columns, 'actions': CUSTOMER_DEPOSIT_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            item_details = request.data['item_details']
            payment_mode_details = request.data['payment_mode_details']
            del request.data['item_details']
            del request.data['payment_mode_details']
            
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(request.data['branch'])
            code =''
            last_ref=CustomerDeposit.objects.filter(branch=request.data['branch']).order_by('-id').first()
            if last_ref:
                code= int(last_ref.ref_no)
                code = str(code + 1).zfill(5)
            else:
                code = '00001'
            request.data.update({"created_by": request.user.id, 'entry_date':entry_date,
                                 "ref_no":code})
            depo_master_obj = DepositMaster.objects.filter(id_deposit_master=request.data['deposit']).first()
            if(depo_master_obj.type == 1 and request.data['deposit_amount'] == None):
                return Response({"error_detail": ["Deposit Amount is required for Amount Account"]}, status=status.HTTP_400_BAD_REQUEST)
            if(depo_master_obj.type == 2 and request.data['deposit_weight'] == None):
                return Response({"error_detail": ["Deposit Weight is required for Weight Account"]}, status=status.HTTP_400_BAD_REQUEST)
            serializer = CustomerDepositSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            if len(item_details) > 0:
                for item in item_details:
                    item.update({"cus_deposit":serializer.data['id']})
                    item_serializer = CustomerDepositItemsSerializer(data=item)
                    item_serializer.is_valid(raise_exception=True)
                    item_serializer.save()
            else:
                payment_data = {}
                payment_data.update({"paid_through":1, "date_payment":request.data['start_date'],
                                     "id_branch":request.data['branch'],"cus_deposit":serializer.data['id'],
                                     "id_payGateway":None, 'entry_date':entry_date, "trans_date":request.data['start_date'],
                                     "payment_amount": request.data['deposit_amount'], "net_amount": request.data['deposit_amount'],
                                     "payment_status":1, "payment_charges":0})
                payment_serializer = CustomerDepositPaymentSerializer(data=payment_data)
                payment_serializer.is_valid(raise_exception=True)
                payment_serializer.save()
                for pay_detail in payment_mode_details:
                    pay_detail.update({"id_pay":payment_serializer.data['id_payment']})
                    pay_detail_serializer = CustomerDepositPaymentDetailSerializer(data=pay_detail)
                    pay_detail_serializer.is_valid(raise_exception=True)
                    pay_detail_serializer.save()
                print("Payment")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        

class IncentiveSettingsListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = CounterWiseTarget.objects.all()
    serializer_class = CounterWiseTargetSerializer

    def get(self, request, format=None):
        queryset = CounterWiseTarget.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,INCENTIVE_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,INCENTIVE_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({ 
                         "sno": index+1,
                            "start_date": format_date(data['from_date']),
                            "end_date": format_date(data['to_date']),
                            "section": data['section'],
                            "pcs_target_value": data['pcs_target_value'],
                            "amt_target_value": data['amt_target_value'],
                            "wt_target_value": data['wt_target_value'],
                            "pk_id": data['id_counter_target'],
                         })
        context = {'columns': columns, 'actions': INCENTIVE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):

        target_data = {
            'pcs_target_type': request.data.get('pcs_target_type'),
            'pcs_target_value': request.data.get('pcs_target_value'),
            'amt_target_type': request.data.get('amt_target_type'),
            'amt_target_value': request.data.get('amt_target_value'),
            'wt_target_type': request.data.get('wt_target_type'),
            'wt_target_value': request.data.get('wt_target_value'),
            'target_pieces': request.data.get('target_pieces'),
            'from_date': request.data.get('start_date'),
            'to_date': request.data.get('end_date'),
            'branch': request.data.get('branch'),
            'section': request.data.get('sections')[0] if request.data.get('sections') else None,
            'target_weight': request.data.get('target_weight'),
            'amount': request.data.get('amount'),
        }
        counter_target_serializer = CounterWiseTargetSerializer(data=target_data)

        if counter_target_serializer.is_valid():

            counter_target = counter_target_serializer.save()
            print(f"CounterWiseTarget saved: {counter_target.id_counter_target}") 
        else:
            return Response(counter_target_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(counter_target_serializer.data, status=status.HTTP_201_CREATED)
    
class CounterWiseTargetDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = CounterWiseTarget.objects.all()
    serializer_class = CounterWiseTargetSerializer

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

    # Format and map fields
        response_data = {
            'pcs_target_type': data.get('pcs_target_type'),
            'pcs_target_value': data.get('pcs_target_value'),
            'amt_target_type': data.get('amt_target_type'),
            'amt_target_value': data.get('amt_target_value'),
            'wt_target_type': data.get('wt_target_type'),
            'wt_target_value': data.get('wt_target_value'),
            'target_pieces': data.get('target_pieces'),
            'start_date': format_date(data.get('from_date')),  # formatted
            'end_date': format_date(data.get('to_date')),      # formatted
            'branch': data.get('branch'),
            # 'section': data.get('section'),
            'section': [s.get('id_section') if isinstance(s, dict) else s for s in (data.get('section') if isinstance(data.get('section'), list) else [data.get('section')])] if data.get('section') else [],
            'target_weight': data.get('target_weight'),
            'amount': data.get('amount'),
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        target_data = {
            'pcs_target_type': request.data.get('pcs_target_type'),
            'pcs_target_value': request.data.get('pcs_target_value'),
            'amt_target_type': request.data.get('amt_target_type'),
            'amt_target_value': request.data.get('amt_target_value'),
            'wt_target_type': request.data.get('wt_target_type'),
            'wt_target_value': request.data.get('wt_target_value'),
            'target_pieces': request.data.get('target_pieces'),
            # 'from_date': request.data.get('start_date'),
            'from_date': request.data.get('from_date'),
            'to_date': request.data.get('to_date'),
            'branch': request.data.get('branch'),
            # 'section': request.data.get('sections')[0] if request.data.get('sections') else None,
            'section': request.data.get('section'), 
            'target_weight': request.data.get('target_weight'),
            'amount': request.data.get('amount'),
        }
        
        serializer = CounterWiseTargetSerializer(instance, data=target_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    
class IncentiveSettingsDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = IncentiveSettings.objects.all()
    serializer_class = IncentiveSettingsSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = IncentiveSettingsSerializer(queryset)
        output = serializer.data
        if output['employee_roles']:
            employee_roles = json.loads(output['employee_roles'])
        else:
            employee_roles = [0,0,0]
        
        if output['weight_ranges']:
            weight_ranges = json.loads(output['weight_ranges'])
        else:
            weight_ranges = []
            
        product = json.loads(output['applicable_products'])

        output.update({"created_by": queryset.created_by.username,"weight_ranges" : weight_ranges,
                       "employee_roles":employee_roles,"product":product,
                       "updated_by": queryset.updated_by.username if queryset.updated_by != None else None,
                       })
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            product = request.data['product']
            employee_roles = request.data['employee_roles']
            weight_ranges = request.data['weight_ranges']

            if not product:
                return Response({"Message": "Please Select Product"}, status=status.HTTP_400_BAD_REQUEST)
                            
            if employee_roles:
                employee_roles = json.dumps(employee_roles)
            else:
                employee_roles = None
            
            if weight_ranges:
                weight_ranges = json.dumps(weight_ranges)
            else:
                weight_ranges = None
            
            request.data.update({"employee_roles":employee_roles,"weight_ranges":weight_ranges,"applicable_products":json.dumps(product)})
            
            queryset = self.get_object()
            request.data.update({"created_by": queryset.created_by.id})
            serializer = IncentiveSettingsSerializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(updated_by=self.request.user,
                            updated_on=datetime.now(tz=timezone.utc))
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    
    def delete(self, request, *args, **kwargs):
        with transaction.atomic():
            queryset = self.get_object()
            try:
                IncentiveSettings.objects.filter(incentive_id=queryset.incentive_id).delete()
                queryset.delete()
            except ProtectedError:
                return Response({"error_detail": ["Incentive Settings instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
            return Response(status=status.HTTP_204_NO_CONTENT)


class ReligionListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Religion.objects.all()
    serializer_class = ReligionSerializer

    def get(self, request, format=None):
        if 'is_active' in request.query_params:
            queryset = Religion.objects.filter(is_active=1)
            serializer = ReligionSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        queryset = Religion.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,RELIGION_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_religion'], "sno": index+1})
        context = {'columns': RELIGION_COLUMN_LIST, 'actions': RELIGION_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.id})
        serializer = ReligionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReligionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Religion.objects.all()
    serializer_class = ReligionSerializer

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
            return Response({"Message": "Religion status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ReligionSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, pk, format=None):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = ReligionSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Religion instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class CustomerNotificationMasterListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = CustomerNotificationMaster.objects.all()
    serializer_class = CustomerNotificationMasterSerializer

    # def get(self, request, format=None):
    #     queryset = CustomerNotificationMaster.objects.all()
    #     paginator, page = pagination.paginate_queryset(queryset, request,None,RELIGION_COLUMN_LIST)
    #     serializer = self.serializer_class(page, many=True)
    #     for index, data in enumerate(serializer.data):
    #         data.update({"pk_id": data['id'], "sno": index+1})
    #     context = {'columns': RELIGION_COLUMN_LIST, 'actions': RELIGION_ACTION_LIST,
    #                'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
    #     return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            request.data.update({"created_by": request.user.id})
            if(request.data['send_to']== 1):
                del request.data['send_to_customers']
                customer_query = Customers.objects.filter(active=True)
                
                # request.data.update({"send_to_customers":customers})
                if (request.data['image'] != None):
                    b = ((base64.b64decode(request.data['image']
                                           [request.data['image'].find(",") + 1:])))
                    img = Image.open(io.BytesIO(b))
                    filename = 'customer_notification.jpeg'
                    img_object = ImageFile(io.BytesIO(
                        img.fp.getvalue()), name=filename)
                    request.data.update({"image": img_object}) 
                serializer = CustomerNotificationMasterSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(created_by=request.user)
                for cus in customer_query:
                    cus_notification_inst = {} 
                    cus_notification_inst.update({
                        'customers':cus.id_customer,
                        'notification':serializer.data['id'],
                    })
                    if(CustomerDeviceIdMaster.objects.filter(customer=cus.id_customer).exists()):
                        customer = CustomerDeviceIdMaster.objects.filter(customer=cus.id_customer)
                        device_serializers = CustomerDeviceIdMasterSerializer(customer, many=True)
                        for device in device_serializers.data:
                            if device['subscription_id'] != None and device['subscription_id']!='':
                                send_push_notification(device['subscription_id'], "Notification", serializer.data['content'])
                        cus_notification_serializer = CustomerNotificationsSerializer(data=cus_notification_inst)
                        cus_notification_serializer.is_valid(raise_exception=True)
                        cus_notification_serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            elif(request.data['send_to']== 2):
                if (request.data['image'] != None):
                    b = ((base64.b64decode(request.data['image']
                                           [request.data['image'].find(",") + 1:])))
                    img = Image.open(io.BytesIO(b))
                    filename = 'customer_notification.jpeg'
                    img_object = ImageFile(io.BytesIO(
                        img.fp.getvalue()), name=filename)
                    request.data.update({"image": img_object})  
                serializer = CustomerNotificationMasterSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(created_by=request.user)
                for cus in request.data['send_to_customers']:
                    cus_notification_inst = {} 
                    cus_notification_inst.update({
                        'customers':cus,
                        'notification':serializer.data['id'],
                    })
                    if(CustomerDeviceIdMaster.objects.filter(customer=cus).exists()):
                        customer = CustomerDeviceIdMaster.objects.filter(customer=cus)
                        device_serializers = CustomerDeviceIdMasterSerializer(customer, many=True)
                        for device in device_serializers.data:
                            if device['subscription_id'] != None and device['subscription_id']!='':
                                send_push_notification(device['subscription_id'], "Notification", serializer.data['content'])
                        cus_notification_serializer = CustomerNotificationsSerializer(data=cus_notification_inst)
                        cus_notification_serializer.is_valid(raise_exception=True)
                        cus_notification_serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

class DailyStatusMasterListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = DailyStatusMaster.objects.all()
    serializer_class = DailyStatusMasterSerializer
    
    def get(self, request, format=None):
        queryset = DailyStatusMaster.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,DAILY_STATUS_MASTER_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            if(data['type']==1):
                data.update({'type_name':"Image Status"})
            elif(data['type']==2):
                data.update({'type_name':"Audio Status"})
            elif(data['type']==3):
                data.update({'type_name':"Video Status"})
            elif(data['type']==4):
                data.update({'type_name':"Text Status"})
            data.update({"pk_id": data['id'], "sno": index+1, 'is_active':data['status']})
        context = {'columns': DAILY_STATUS_MASTER_COLUMN_LIST, 'actions': DAILY_STATUS_MASTER_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            request.data.update({"created_by": request.user.id})
            try:
                if(request.data['type'] == 1):
                    # b = ((base64.b64decode(request.data['image_file']
                    #                            [request.data['image_file'].find(",") + 1:])))
                    # img = Image.open(io.BytesIO(b))
                    # filename = 'daily_status_image.jpeg'
                    # img_object = ImageFile(io.BytesIO(
                    #     img.fp.getvalue()), name=filename)
                    img_object = base64_to_file(request.data['image_file'], filename_prefix="daily_status_image",file_extension="jpeg")
                    compressed_image = compress_image(img_object)
                    request.data.update({"image_file": compressed_image,
                                         "audio_file" : None,
                                         "video_file" : None,
                                         "text" : None})
                
                elif(request.data['type'] == 2):
                    audio_file = base64_to_file(request.data['audio_file'], filename_prefix="daily_status_audio",file_extension="mp3")
                    request.data.update({"image_file": None,
                                         "audio_file" : audio_file,
                                         "video_file" : None,
                                         "text" : None})
                    
                elif(request.data['type'] == 3):
                    video_file = base64_to_file(request.data['video_file'], filename_prefix="daily_status_video",file_extension="mp4")
                    request.data.update({"image_file": None,
                                         "audio_file" : None,
                                         "video_file" : video_file,
                                         "text" : None})
                    
                elif(request.data['type'] == 4):
                    request.data.update({"image_file": None,
                                         "audio_file" : None,
                                         "video_file" : None,
                                         "text" : request.data['text']})
                    
                serializer = DailyStatusMasterSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
            except KeyError as e:
                return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
            except ValidationError as e:
                return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)
            
class DailyStatusMasterDetailView(generics.RetrieveAPIView):
    permission_classes = [IsEmployee]
    queryset = DailyStatusMaster.objects.all()
    serializer_class = DailyStatusMasterSerializer

    def get(self, request, pk, format=None):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Daily Status master status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = DailyStatusMasterSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)
    
class CompanyInfoApi(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get(self, request, *args, **kwargs):
        comp_obj = Company.objects.latest('id_company')
        company_serializer = CompanySerializer(comp_obj, context={'request', request})
        address1 = comp_obj.address1 if (comp_obj.address1 and comp_obj.address1 != None and comp_obj.address1 != '') else ''
        address2 = comp_obj.address2 if (comp_obj.address2 and comp_obj.address2 != None and comp_obj.address2 != '') else ''
        company_address = (
            f"{address1} {address2}, {comp_obj.city.name}, {comp_obj.state.name}. {comp_obj.pincode}".strip()
        )
        instance = {
            "company_name": comp_obj.company_name,
            "short_code": comp_obj.short_code,
            "company_address":company_address,
            "whatsapp_number":comp_obj.whatsapp_no,
            "email":comp_obj.email,
            "website":comp_obj.website,
            "mobile":comp_obj.mobile,
            "general_enquiries":comp_obj.mobile,
            "scheme_related_enquiries":comp_obj.mobile,
            "contact_name":comp_obj.company_name,
        }
        return Response({"data":instance}, status=status.HTTP_200_OK)
    
class AboutCompanyApiView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get(self, request, *args, **kwargs):
        comp_obj = Company.objects.latest('id_company')
        company_serializer = CompanySerializer(comp_obj, context={'request', request})
        instance = {
            "about_us_html": """
                <h2>About Us</h2>
                <p>Welcome to <strong>Our Gold Jewels</strong>, where tradition meets craftsmanship. With a legacy rooted in elegance and trust, we bring you timeless gold jewellery that celebrates your moments — big and small.</p>
        
                <p>Founded with a passion for fine artistry, our collections are crafted to reflect the rich heritage of Indian design, while embracing modern sophistication. Whether it’s a wedding, festival, or daily wear, our gold jewellery adds a touch of grace and meaning to every occasion.</p>
        
                <h3>Why Choose Us?</h3>
                <ul>
                  <li>100% BIS Hallmarked Gold</li>
                  <li>Exquisite Handcrafted Designs</li>
                  <li>Transparent Pricing & Quality Assurance</li>
                  <li>Trusted by Thousands of Happy Customers</li>
                </ul>
        
                <h3>Our Promise</h3>
                <p>At <strong>Our Gold Jewels</strong>, we promise purity, authenticity, and an experience that sparkles as much as our jewellery. Your trust is our most valued ornament.</p>
        
                <p><em>Thank you for choosing us to be part of your special moments.</em></p>
            """
        }
        return Response({"data":instance}, status=status.HTTP_200_OK)
    
    
    
class RegionListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
     

    def get_queryset(self):
        queryset = Region.objects.all()
        if 'is_active' in self.request.query_params:
            queryset = queryset.filter(is_active=1)
        return queryset

    def get(self, request, *args, **kwargs):
        if 'is_active' in request.query_params:
            queryset = Region.objects.filter(is_active=1)
            serializer = RegionSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request,None,REGION_COLUMN_LIST)
        serializer = self.get_serializer(page, many=True)
        for idx, data in enumerate(serializer.data):
            data.update({"sno": idx+1})
            data.update({"pk_id": data['id_region']})
        # Return the paginated response
        context = {'columns': REGION_COLUMN_LIST, 'actions': REGION_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = RegionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.is_active == True):
                obj.is_active = False
            else:
                obj.is_active = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Region status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = RegionSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.id})
        serializer = RegionSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Region instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)