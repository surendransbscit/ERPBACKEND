from .serializers import (MetalSerializer, PuritySerializer, SchemeClassificationSerializer, ClaritySerializer,
                          StoneSerializer, ColorSerializer, ShapeSerializer, RetCutSerializer, ProductSerializer, 
                          CategorySerializer,DesignSerializer, CategorySerializer, ProductMappingSerializer, 
                          SubDesignSerializer, SubDesignMappingSerializer, MakingAndWastageSettingsMappingSerializer, 
                          SectionSerializer,QualityCodeSerializer, DiamondRateSerializer, ProductCalculationTypeSerializer,
                          ProductSectionSerializer,RepairDamageMasterSerializer,DiamondCentRateSerializer, 
                          ErpReorderSettingsSerializer,CounterWiseTargetSerializer, CustomerMakingAndWastageSettingsMappingSerializer,
                          PurchaseDiamondRateSerializer, PurchaseDiamondCentRateSerializer, CategoryPurityRateSerializer,CustomerEnquirySerializer)

from .models import (Metal, Purity, SchemeClassification, Clarity, Stone, Color, Shape, RetCut, Product, Category,CustomerEnquiry,
                     Design, SubDesign, ProductMapping, SubDesignMapping, MakingAndWastageSettings, Section, QualityCode, PurchaseDiamondCentRate, PurchaseDiamondRateMaster,RepairDamageMaster,
                     DiamondRateMaster, ProductCalculationType,ProductSection, DiamondCentRate, ErpReorderSettings, CounterWiseTarget,
                     CustomerMakingAndWastageSettings,CategoryPurityRate)
from retailmasters.models import (Taxmaster,Taxgroupmaster, Uom,SupplierProductDetails,SupplierProductImageDetails,Size, WeightRange)
from retailmasters.serializers import (SupplierProductDetailsSerializer,SupplierProductImageDetailsSerializer, SizeSerializer, WeightRangeSerializer)
from customerorder.models import (CustomerWishlist, CustomerCart)
from customers.models import (Customers)
from accounts.models import (User)
from django.conf import settings
from django.shortcuts import render
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from common.permissions import IsAdminUser, IsCustomerUser, IsCustomer,IsEmployee, isSuperuser,IsSuperuserOrEmployee, IsEmployeeOrCustomer
from rest_framework import generics, status
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import base64
import uuid
from django.db.models import Q, ProtectedError
from PIL import Image
from django.core.files.images import ImageFile
import io
from utilities.pagination_mixin import PaginationMixin
from retailsettings.models import (RetailSettings)
from utilities.utils import format_date,date_format_with_time,convert_tag_to_formated_data,calculate_item_cost
from .constants import (METAL_COLUMN_LIST, METAL_ACTION_LIST,CUT_COLUMN_LIST,CUT_ACTION_LIST,
                        STONE_COLUMN_LIST, STONE_ACTION_LIST,
                        COLOR_COLUMN_LIST, COLOR_ACTION_LIST,
                        SHAPE_COLUMN_LIST,SHAPE_ACTION_LIST,
                        CLARITY_COLUMN_LIST,CLARITY_ACTION_LIST,
                        QUALITY_COLUMN_LIST, QUALITY_ACTION_LIST,
                        PURITY_COLUMN_LIST, PURITY_ACTION_LIST,
                        SCHEME_CLASSIFICATION_ACTION_LIST, SCHEME_CLASSIFICATION_COLUMN_LIST, 
                        PRODUCT_ACTION_LIST, PRODUCT_COLUMN_LIST, DESIGN_ACTION_LIST, DESIGN_COLUMN_LIST, 
                        SUB_DESIGN_ACTION_LIST, SUB_DESIGN_COLUMN_LIST, SECTION_ACTION_LIST, SECTION_COLUMN_LIST, 
                        CATEGORY_ACTION_LIST, CATEGORY_COLUMN_LIST,
                        DIAMOND_RATE_COLUMN_LIST, DIAMOND_RATE_ACTION_LIST,REPAIR_COLUMN_LIST,REPAIR_ACTION_LIST,
                        COUNTER_WISE_TARGET_COLUMN_LIST, COUNTER_WISE_TARGET_ACTION_LIST, CATEGORY_PURITY_RATE_COLUMN_LIST,
                        CATEGORY_PURITY_RATE_ACTION_LIST)
from utilities.constants import FILTERS
from core.views  import get_reports_columns_template

pagination = PaginationMixin()  # Apply pagination

from retailmasters.models import (Taxmaster)
from inventory.models import (ErpTagging,ErpTaggingImages, ErpTagSetItems, ErpTagSet)
from inventory.serializers import ErpTaggingSerializer,ErpTaggingImagesSerializer


class PurchaseDiamondRateFilterView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        cent_rates = []
        instance = {}
        quality_code = request.data['quality']
        supplier_ids = request.data['supplier']
        
        base_filters = Q(quality_code=quality_code)

        # Filter by supplier if provided
        if len(supplier_ids) > 0:
            base_filters &= Q(supplier__in=supplier_ids)
        
        if(PurchaseDiamondRateMaster.objects.filter(base_filters).exists()):
            diamond_rate_master = PurchaseDiamondRateMaster.objects.filter(base_filters).get()
            cent_rate_master = PurchaseDiamondCentRate.objects.filter(
                id_rate=diamond_rate_master.rate_id
            )
            for rates in cent_rate_master:
                cent_rates.append({
                    "id_cent_rate":rates.id_cent_rate,
                    "purchase_from_cent":rates.from_cent,
                    "purchase_to_cent":rates.to_cent,
                    "purchase_rate":rates.rate,
                })
            # else:
            #     cent_rates.append({
            #         "id_cent_rate":uuid.uuid4(),
            #         "from_cent":0,
            #         "to_cent":0,
            #         "rate":0,
            #     })
        return Response(cent_rates, status=status.HTTP_200_OK)
    
class DiamondRateFilterView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        cent_rates = []
        quality_code = request.data['quality']
        
        base_filters = Q(quality_code=quality_code)

        if(DiamondRateMaster.objects.filter(base_filters).exists()):
            diamond_rate_master = DiamondRateMaster.objects.filter(base_filters).get()
            cent_rate_master = DiamondCentRate.objects.filter(
                id_rate=diamond_rate_master.rate_id
            )
            for rates in cent_rate_master:
                cent_rates.append({
                    "id_cents_rate":rates.id_cents_rate,
                    "from_cent":rates.from_cent,
                    "to_cent":rates.to_cent,
                    "rate":rates.rate,
                })
        # else:
        #     return Response({"message":})
            # else:
            #     cent_rates.append({
            #         "id_cents_rate":uuid.uuid4(),
            #         "from_cent":0,
            #         "to_cent":0,
            #         "rate":0,
            #     })
        return Response(cent_rates, status=status.HTTP_200_OK)
            
            
class PurchaseDiamondRatemasterCreateView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        cent_ranges = []
        # Function to check if the new range overlaps with any previous range
        def is_overlapping( new_from, new_to, ranges):
            for r in ranges:
                if not (float(new_to) < r["from_cent"] or float(new_from) > r["to_cent"]):
                    return True
            return False
        with transaction.atomic():
            if(PurchaseDiamondRateMaster.objects.filter(quality_code=request.data['quality_code'], 
                                                        supplier__in=request.data['supplier']).exists()):
                rate_master = PurchaseDiamondRateMaster.objects.filter(quality_code=request.data['quality_code'],
                                                                       supplier__in=request.data['supplier'])
                for rates in rate_master:
                    if(PurchaseDiamondCentRate.objects.filter(id_rate=rates.rate_id).exists()):
                        cent_rate_master = PurchaseDiamondCentRate.objects.filter(
                            id_rate=rates.rate_id
                        ).delete()
                PurchaseDiamondRateMaster.objects.filter(quality_code=request.data['quality_code'],
                                                                       supplier__in=request.data['supplier']).delete()
            diamond_cent_rate = request.data['diamond_cent_rate']
            del request.data['diamond_cent_rate']
            request.data.update({"created_by":request.user.pk, "effective_date":date.today()})
            for data in diamond_cent_rate:
                if is_overlapping(data["from_cent"], data["to_cent"], cent_ranges):
                    return Response({"message":"Overlap found for cent values"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    cent_ranges.append({"from_cent": float(data["from_cent"]), "to_cent": float(data["to_cent"]), "rate":data['rate']})
            diamond_rate_master_serializer = PurchaseDiamondRateSerializer(data=request.data)
            diamond_rate_master_serializer.is_valid(raise_exception=True)
            diamond_rate_master_serializer.save()
            for cent_rates in cent_ranges:
                cent_rates.update({"id_rate":diamond_rate_master_serializer.data['rate_id']})
                cent_rate_serializer = PurchaseDiamondCentRateSerializer(data=cent_rates)
                cent_rate_serializer.is_valid(raise_exception=True)
                cent_rate_serializer.save()
            return Response(diamond_rate_master_serializer.data, status=status.HTTP_201_CREATED)            
    

class DiamondRatemasterCreateView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            cent_rate_details = DiamondCentRate.objects.all()
            cent_rate_details_serializer = DiamondCentRateSerializer(cent_rate_details, many=True)
            return Response(cent_rate_details_serializer.data)
        queryset = DiamondRateMaster.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,DIAMOND_RATE_COLUMN_LIST)
        serializer = DiamondRateSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['rate_id'], 'sno': index+1})
        context = {'columns': DIAMOND_RATE_COLUMN_LIST, 'actions': DIAMOND_RATE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        cent_ranges = []
        # Function to check if the new range overlaps with any previous range
        def is_overlapping( new_from, new_to, ranges):
            for r in ranges:
                if not (float(new_to) < r["from_cent"] or float(new_from) > r["to_cent"]):
                    return True
            return False
        with transaction.atomic():
            if(DiamondRateMaster.objects.filter(quality_code=request.data['quality_code']).exists()):
                rate_master = DiamondRateMaster.objects.filter(quality_code=request.data['quality_code'])
                for rates in rate_master:
                    if(DiamondCentRate.objects.filter(id_rate=rates.rate_id).exists()):
                        cent_rate_master = DiamondCentRate.objects.filter(
                            id_rate=rates.rate_id
                        ).delete()
                DiamondRateMaster.objects.filter(quality_code=request.data['quality_code']).delete()
            diamond_cent_rate = request.data['diamond_cent_rate']
            del request.data['diamond_cent_rate']
            request.data.update({"created_by":request.user.pk, "effective_date":date.today()})
            for data in diamond_cent_rate:
                if is_overlapping(data["from_cent"], data["to_cent"], cent_ranges):
                    return Response({"message":"Overlap found for cent values"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    cent_ranges.append({"from_cent": float(data["from_cent"]), "to_cent": float(data["to_cent"]), "rate":data['rate']})
            diamond_rate_master_serializer = DiamondRateSerializer(data=request.data)
            diamond_rate_master_serializer.is_valid(raise_exception=True)
            diamond_rate_master_serializer.save()
            for cent_rates in cent_ranges:
                cent_rates.update({"id_rate":diamond_rate_master_serializer.data['rate_id']})
                cent_rate_serializer = DiamondCentRateSerializer(data=cent_rates)
                cent_rate_serializer.is_valid(raise_exception=True)
                cent_rate_serializer.save()
            return Response(diamond_rate_master_serializer.data, status=status.HTTP_201_CREATED)
        
class DiamondRatemasterDetailsView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = DiamondRateMaster.objects.all()
    serializer_class = DiamondRateSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = DiamondRateSerializer(queryset)
        output = serializer.data
        cent_rate_details = DiamondCentRate.objects.filter(id_rate=queryset.rate_id)
        cent_rate_details_serializer = DiamondCentRateSerializer(cent_rate_details, many=True)
        output.update({"cent_rate_details":cent_rate_details_serializer.data})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            cent_ranges = []
            # Function to check if the new range overlaps with any previous range
            def is_overlapping( new_from, new_to, ranges):
                for r in ranges:
                    if not (new_to < r["from_cent"] or new_from > r["to_cent"]):
                        return True
                return False
            queryset = self.get_object()
            diamond_cent_rate = request.data['diamond_cent_rate']
            del request.data['diamond_cent_rate']
            request.data.update({"created_by": queryset.created_by.pk, "effective_date":queryset.effective_date})

            cent_rate_details = DiamondCentRate.objects.filter(id_rate=queryset.rate_id).delete()
            # cent_rate_details_serializer = DiamondCentRateSerializer(cent_rate_details, many=True)

            for data in diamond_cent_rate:
                if is_overlapping(data["from_cent"], data["to_cent"], cent_ranges):
                    return Response({"message":"Overlap found for cent values"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    cent_ranges.append({"from_cent": data["from_cent"], "to_cent": data["to_cent"], "rate":data['rate']})
            diamond_rate_master_serializer = DiamondRateSerializer(queryset, data=request.data)
            diamond_rate_master_serializer.is_valid(raise_exception=True)
            diamond_rate_master_serializer.save()
            for cent_rates in cent_ranges:
                cent_rates.update({"id_rate":queryset.rate_id})
                cent_rate_serializer = DiamondCentRateSerializer(data=cent_rates)
                cent_rate_serializer.is_valid(raise_exception=True)
                cent_rate_serializer.save()
            return Response(diamond_rate_master_serializer.data, status=status.HTTP_202_ACCEPTED)

class MetalListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Metal.objects.all()
    serializer_class = MetalSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Metal.objects.filter(metal_status=1)
            serializer = MetalSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,METAL_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,METAL_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_metal'], 'sno': index+1, 'is_active': data['metal_status']})
        context = {'columns': columns, 'actions': METAL_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            request.data.update({"metal_code": None})
        request.data.update({"created_by": request.user.pk})
        serializer = MetalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            Metal.objects.filter(id_metal=serializer.data['id_metal']).update(metal_code=serializer.data['id_metal'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MetalDetailsView(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes=[permissions.AllowAny]
    permission_classes = [IsEmployee]
    queryset = Metal.objects.all()
    serializer_class = MetalSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if(obj.metal_status == True):
                obj.metal_status = False
            else:
                obj.metal_status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Metal status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = MetalSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            request.data.update({"metal_code": queryset.id_metal})
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = MetalSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Metal instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PurityListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = Purity.objects.all()
    serializer_class = PuritySerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Purity.objects.filter(status=1)
            serializer = PuritySerializer(queryset, many=True)
            return Response(serializer.data)
        if 'active' in request.query_params:
            queryset = Purity.objects.filter(status=1)
            serializer = PuritySerializer(queryset, many=True)
            return Response({"data":serializer.data})
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,PURITY_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,PURITY_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_purity'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': columns, 'actions': PURITY_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = PuritySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PurityDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Purity.objects.all()
    serializer_class = PuritySerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if(obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Purity status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = PuritySerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = PuritySerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Purity instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SchemeClassListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = SchemeClassification.objects.all()
    serializer_class = SchemeClassificationSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = SchemeClassification.objects.filter(active=True)
            serializer = SchemeClassificationSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = SchemeClassification.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,SCHEME_CLASSIFICATION_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_classification'],
                        'sno': index+1, 'is_active': data['active']})
        context = {
            'columns': SCHEME_CLASSIFICATION_COLUMN_LIST,
            'actions': SCHEME_CLASSIFICATION_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        if (request.data['logo'] != None):
            b = ((base64.b64decode(request.data['logo']
                                   [request.data['logo'].find(",") + 1:])))
            img = Image.open(io.BytesIO(b))
            filename = 'scheme_class_img.jpeg'
            img_object = ImageFile(io.BytesIO(
                img.fp.getvalue()), name=filename)
            request.data.update({"logo": img_object})
        else:
            request.data.update({"logo": None})
        serializer = SchemeClassificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SchemeClassDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = SchemeClassification.objects.all()
    serializer_class = SchemeClassificationSerializer

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
            return Response({"Message": "Scheme classification status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = SchemeClassificationSerializer(
            obj, context={"request": request})
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        if (request.data['logo'] != None):
            if 'data:image/' in request.data['logo'][:30]:
                # update items  for which image is changed
                queryset.logo.delete()
                b = (
                    (base64.b64decode(request.data['logo'][request.data['logo'].find(",") + 1:])))
                img = Image.open(io.BytesIO(b))
                filename = 'scheme_class_img.jpeg'
                img_object = ImageFile(io.BytesIO(
                    img.fp.getvalue()), name=filename)
                request.data.update({"logo": img_object})

                serializer = self.get_serializer(queryset, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            del request.data['logo']
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
            return Response({"error_detail": ["Scheme classification instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CounterWiseTargetItemsListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = CounterWiseTarget.objects.all()
    serializer_class = CounterWiseTargetSerializer
    
    def post(self, request, *args, **kwargs):
        section_id = request.data['section_id']  
        # branch_id = request.data['branch_id']  

        # if not section_id or not branch_id:
        if not section_id:
            return Response({"error": "section_id and branch_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        product_sections = ProductSection.objects.filter(id_section_id=section_id)
        response_data = []
        if not product_sections.exists():
            return Response(response_data, status=status.HTTP_200_OK)

        for prod_section in product_sections:
            product = prod_section.id_product
            product_id = product.pro_id
            product_name = product.product_name
            counter_target = CounterWiseTarget.objects.filter(
                Q(section_id=section_id) &
                # Q(branch_id=branch_id) &
                Q(product=product)
            ).first()

            if counter_target:
                pieces = counter_target.target_pieces
                weight = counter_target.target_weight
            else:
                pieces = 0
                weight = 0
            response_data.append({
                "product_id": product_id,
                "product_name": product_name,
                "target_pieces": pieces,
                "target_weight": weight
            })
        return Response(response_data, status=status.HTTP_200_OK)

class CounterWiseTargetListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = CounterWiseTarget.objects.all()
    serializer_class = CounterWiseTargetSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = CounterWiseTarget.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,COUNTER_WISE_TARGET_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id": data['id_counter_target'],
                        'sno': index+1, "from_date":format_date(data['from_date']),
                        "to_date":format_date(data['to_date'])})
        context = {
            'columns': COUNTER_WISE_TARGET_COLUMN_LIST,
            'actions': COUNTER_WISE_TARGET_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        if(CounterWiseTarget.objects.filter(Q(section_id=request.data['section']) & Q(branch_id=request.data['branch'])
                                            & Q(from_date=request.data['from_date']) & Q(to_date=request.data['to_date']))).exists():
            CounterWiseTarget.objects.filter(Q(section_id=request.data['section']) & Q(branch_id=request.data['branch'])
                                             & Q(from_date=request.data['from_date']) & Q(to_date=request.data['to_date'])).delete()
        for data in request.data['section_wise_target']:
            serializer = CounterWiseTargetSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response({"message":"Sales Target created successfully."}, status=status.HTTP_201_CREATED)


# class CounterWiseTargetDetailView(generics.ListCreateAPIView):
#     permission_classes = [IsEmployee, isSuperuser]
#     queryset = CounterWiseTarget.objects.all()
#     serializer_class = CounterWiseTargetSerializer
    
#     def get(self, request, *args, **kwargs):
#         queryset = self.get_object()
#         serializer = CounterWiseTargetSerializer(queryset)
#         output = serializer.data
#         products = []
#         for product in serializer.data['products']:
#             products.append(
#                     {"value": product, "label": Product.objects.get(pro_id=product).product_name})
#         output.update({"products": products})
#         return Response(output, status=status.HTTP_200_OK)
    
#     def put(self, request, *args, **kwargs):
#         queryset = self.get_object()
#         serializer = CounterWiseTargetSerializer(queryset, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class QualityCodeView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = QualityCode.objects.all()
    serializer_class = QualityCodeSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            try:
                queryset = QualityCode.objects.filter(status=1)
                serializer = QualityCodeSerializer(queryset, many=True)
                for data in serializer.data:
                    diamond_rate = DiamondRateMaster.objects.filter(
                        quality_code=data['quality_id']).exists()
                    if (diamond_rate):
                        diamond_queryset = DiamondRateMaster.objects.filter(
                            quality_code=data['quality_id'])
                        diamond_serializer = DiamondRateSerializer(
                            diamond_queryset, many=True)
                        data.update({"diamond_rates": diamond_serializer.data})
                return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
            except QualityCode.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
        queryset = QualityCode.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,QUALITY_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,QUALITY_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = QualityCodeSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            cut = RetCut.objects.get(id_cut=data['cut'])
            color = Color.objects.get(id_color = data['color'])
            shape = Shape.objects.get(id_ret_shape = data['shape'])
            clarity = Clarity.objects.get(id_clarity = data['clarity'])
            
            data.update({"pk_id": data['quality_id'], 'sno': index+1, 
                         'is_active': data['status'], 
                         'cutName': cut.cut,
                         'colorName': color.color,
                         'shapeName' : shape.shape,
                         'clarityName' : clarity.clarity
                         })
        context = {
            'columns': columns,
            'actions': QUALITY_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number
        }
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = QualityCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message":"Quality Code Created Successfully."}, status=status.HTTP_201_CREATED)
    
class QualityDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = QualityCode.objects.all()
    serializer_class = QualityCodeSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if(obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Quality status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = QualityCodeSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = QualityCodeSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response({"Message": "Quality code updated successfully."}, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Quality can't be deleted, as it is already used in transaction"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
  



class ClarityListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Clarity.objects.all()
    serializer_class = ClaritySerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Clarity.objects.filter(status=True)
            serializer = ClaritySerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = Clarity.objects.all()
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,CLARITY_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,CLARITY_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_clarity'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': columns, 'actions': CLARITY_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    
    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = ClaritySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ClarityDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Clarity.objects.all()
    serializer_class = ClaritySerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Clarity status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ClaritySerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = ClaritySerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    
    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Clarity can't be deleted, as it is already used in transaction"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StoneListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Stone.objects.all()
    serializer_class = StoneSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Stone.objects.filter(stone_status=1)
            serializer = StoneSerializer(queryset, many=True)
            return Response({"data":serializer.data})
        queryset = Stone.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,STONE_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,STONE_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            uom = Uom.objects.get(uom_id=data['uom_id'])
            stone_instance = queryset.get(pk=data['stone_id'])
            data.update({"pk_id": data['stone_id'], 'sno': index+1, 'stone_type': stone_instance.get_stone_type_display(
            ), 'is_active': data['stone_status'], 'uom_name': uom.uom_name})
        context = {
            'columns': columns,
            'actions': STONE_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = StoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StoneDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Stone.objects.all()
    serializer_class = StoneSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.stone_status == True):
                obj.stone_status = False
            else:
                obj.stone_status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Stone status updated successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = StoneSerializer(obj)
        output = serializer.data
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = StoneSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Stone instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ColorListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Color.objects.all()
    serializer_class = ColorSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Color.objects.filter(status=1)
            serializer = ColorSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = Color.objects.all()
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,COLOR_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,COLOR_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_color'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': columns, 'actions': COLOR_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)
        
       

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = ColorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ColorDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Color.objects.all()
    serializer_class = ColorSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if(obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Color status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ColorSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = ColorSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Color can't be deleted, as it is already used in transaction"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShapeListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Shape.objects.all()
    serializer_class = ShapeSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Shape.objects.filter(status=1)
            serializer = ShapeSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = Shape.objects.all()
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,SHAPE_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,SHAPE_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_ret_shape'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': columns, 'actions': SHAPE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = ShapeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ShapeDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Shape.objects.all()
    serializer_class = ShapeSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if(obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Shape status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ShapeSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = ShapeSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Shape can't be deleted, as it is already used in transaction"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class CutListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = RetCut.objects.all()
    serializer_class = RetCutSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = RetCut.objects.filter(status=True)
            serializer = RetCutSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = RetCut.objects.all()
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,CUT_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,CUT_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_cut'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': columns, 'actions': CUT_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = RetCutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CutDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = RetCut.objects.all()
    serializer_class = RetCutSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if(obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Cut status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = RetCutSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = RetCutSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    
    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Cut can't be deleted, as it is already used in transaction"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ActiveProductListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee | IsCustomer]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    def get(self, request, *args, **kwargs):
        show_catalogue = True
        # 1-Pending,2-Approved
        catalogue_req_status = 2 
        message = "Data Retrieved Successfully"
        # show_catalogue_restriction = 1 General Settings to show the catalogue 
        show_catalogue_restriction = RetailSettings.objects.get(name = 'show_catalogue_restriction').value
        if int(show_catalogue_restriction)==1:  
            customer = Customers.objects.filter(user=request.user.pk).first()
            catalogue_req_status = customer.catalogue_req_status
            if catalogue_req_status == 1:
                message = "Your request is pending for approval."
            if catalogue_req_status == 0:
                message = "You Don't have access to catalogue."
            if customer!=None and catalogue_req_status==2 :
                now = timezone.now()
                catalogue_validity = customer.show_catalogue_date
                if customer.catalogue_visible_type !=0:
                    if now >= catalogue_validity:
                        show_catalogue = False
                        message = "Your catalogue Time is expired."
            else:
                show_catalogue = False
        queryset = Product.objects.filter(status=True).filter(Q(image__isnull=False))
        response_data = []
        serializer = self.serializer_class(queryset, many=True, context={"request":request})
        
        for data in serializer.data:
            result = {}
            if data['image']!=None:
                result.update({
                    "pro_id":data['pro_id'],
                    "product_name":data['product_name'],
                    "image":data['image']
                })
                if(result not in response_data):
                            response_data.append(result)
        return Response({
            "message":message,
            "data":response_data,
            "show_catalogue":show_catalogue,
            "catalogue_req_status":catalogue_req_status,
        }, status=status.HTTP_201_CREATED)
        

class OutStockProductListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    serializer_class = SupplierProductDetailsSerializer

    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product')
        if not product_id:
            return Response({"status":False,"message": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            query = """
                SELECT prod.product_name, des.design_name, subDes.sub_design_name, 
                    p.from_weight, p.to_weight, p.id, p.from_wastage, p.to_wastage,
                    p.from_making_charge, p.to_making_charge, p.approx_delivery_date, 
                    supplier.supplier_name
                FROM erp_supplier_product_details p
                left join erp_supplier_products sp on sp.id = p.supplier_product_id
                left join erp_supplier supplier on supplier.id_supplier = sp.supplier_id 
                LEFT JOIN erp_supplier_product_details_design d ON d.supplierproductdetails_id = p.id
                LEFT JOIN erp_supplier_product_details_sub_design s ON s.supplierproductdetails_id = p.id
                LEFT JOIN erp_product prod ON prod.pro_id = p.product_id
                LEFT JOIN erp_design des ON des.id_design = d.design_id
                LEFT JOIN erp_sub_design subDes ON subDes.id_sub_design = s.subdesign_id
                LEFT JOIN erp_supplier_product_image_details i ON i.supplier_product_details_id = p.id
                WHERE p.supplier_product_id = %s
            """

            with connection.cursor() as cursor:
                cursor.execute(query, [product_id])
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            for item in results:
                supplier_product_image = SupplierProductImageDetails.objects.filter(supplier_product_details=item['id'])
                supplier_product_image_serializer = SupplierProductImageDetailsSerializer(supplier_product_image, many=True, context={"request":request})
                for images in supplier_product_image_serializer.data:
                    images.update({"id":images['id'], "default":False, "preview":images['image']})
                item.update({"image":supplier_product_image_serializer.data})
            

            # Paginate results
            paginator,page = pagination.paginate_queryset(results, request)

            return Response({
                "status":True,
                "data": list(page),
                'page_count':paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number
            }, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response({"status":False,"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    


class OutStockProductListViewold(generics.ListCreateAPIView):
    permission_classes = [IsEmployee | IsCustomer]
    serializer_class = SupplierProductDetailsSerializer

    def post(self, request, *args, **kwargs):
        queryset = SupplierProductDetails.objects.filter(product=request.data['product'])
        response_data = []
        serializer = self.serializer_class(queryset, many=True, context={"request":request})
        for data in serializer.data:
            print(data)
            sub_design_queryset = SubDesign.objects.filter(id_sub_design__in=data['sub_design'])
            sub_design_serializer = SubDesignSerializer(sub_design_queryset, many=True)
            for sub_design in sub_design_serializer.data:
                design_queryset = Design.objects.filter(id_design__in=data['design'])
                design_serializer = DesignSerializer(design_queryset, many=True)
                for design in design_serializer.data:
                    result = {}
                    product = Product.objects.get(pro_id=data['product'])
                    wastage_percentage = data['from_wastage']+" "+"%"
                    making_charge = data['from_making_charge']
                    weight_range = data['from_weight']+" "+" Grams"
                    approx_delivery_date = str(data['approx_delivery_date'])+" Day"
                    if data['from_wastage']!=data['to_wastage']:
                        wastage_percentage = data['from_wastage']+"-"+data['to_wastage']+" "+"%"
                    if data['from_making_charge']!=data['to_making_charge']:
                        making_charge = data['from_making_charge']+"-"+data['to_making_charge']
                    if data['from_weight']!=data['to_weight']:
                        weight_range = data['from_weight']+" "+data['to_weight']+" "+" Grams"
                    if int(data['approx_delivery_date']) > 1:
                        approx_delivery_date = str(data['approx_delivery_date'])+" "+"Days"
                    image_details = SupplierProductImageDetails.objects.filter(supplier_product_details=data['id'])
                    image_serializer = SupplierProductImageDetailsSerializer(image_details,many=True,context={"request":request})
                    if len(image_serializer.data) > 0 :
                        result.update({
                            "id":data['id'],
                            "id_sub_design":sub_design['id_sub_design'],
                            "product_name":product.product_name,
                            "wastage_percentage":wastage_percentage,
                            "making_charge":making_charge,
                            "design_name":design['design_name'],
                            "sub_design_name":sub_design['sub_design_name'],
                            "weight_range":weight_range,
                            "approx_delivery_date":approx_delivery_date,
                            "image_details":image_serializer.data,
                        })
                        if result not in response_data:
                            response_data.append(result)
                    
            # Use the common pagination method
        paginator, page = pagination.paginate_queryset(response_data, request)
        paginated_response_data = list(page)

        return Response({
            "data": response_data,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number
        }, status=status.HTTP_200_OK)
    


class ProductListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee | IsCustomer]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            queryset = Product.objects.filter(status=True)
            serializer = ProductSerializer(queryset, many=True,context={"request":request})
            for data in serializer.data:
                tax_master = Taxmaster.objects.filter(tax_id=data['tax_id']).get()
                data.update({"tax_percentage":tax_master.tax_percentage}) 
                if (data['image'] == None):
                    data.update({"image":None, "image_text":data['product_name'][0],"product_name":data['short_code'] + " -"+ data['product_name']})
                if (data['image'] != None):
                    data.update({"image":data['image'], "image_text":data['product_name'][0],"product_name":data['short_code'] + " -"+ data['product_name']})

            return Response(serializer.data)
        if 'active' in request.query_params:
            queryset = Product.objects.filter(status=True)
            serializer = ProductSerializer(queryset, many=True,context={"request":request})
            product_list = []
            for data in serializer.data:
                product = {}
                product.update({
                    "pro_id":data['pro_id'],
                    "product_name":data['product_name'],
                    "short_code":data['short_code']
                })
                product_list.append(product)
               
            return Response({"status":True,"data":product_list}, status=status.HTTP_200_OK)
        paginator, page = pagination.paginate_queryset(self.queryset.order_by('pro_id'), request,None,PRODUCT_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,PRODUCT_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True, context={"request":request})
       
        for index,data in enumerate( serializer.data):
            preview_images =[]
            metal = Metal.objects.filter(id_metal = data['id_metal']).values_list('metal_name', flat=True).first()
            category = Category.objects.filter(id_category = data['cat_id']).values_list('cat_name', flat=True).first()
            tax = Taxmaster.objects.filter(tax_id = data['tax_id']).values_list('tax_name', flat=True).first()
            cal_type = ProductCalculationType.objects.filter(id_calculation_type = data['calculation_based_on']).values_list('name', flat=True).first()
            product_instance = Product.objects.get(pk=data['pro_id'])
            stock_type = product_instance.get_stock_type_display()
            sales_based_on = product_instance.get_sales_mode_display()
            mc_calc_type = product_instance.get_mc_calc_type_display()
            wastage_calc_type = product_instance.get_wastage_calc_type_display()
            tax_type = product_instance.get_tax_type_display()
            if (data['image'] == None):
                data.update({"image":None, "image_text":data['product_name'][0]})
            if (data['image'] != None):
                preview_images.append({"image":data['image'], "name":data['product_name']})
                data.update({"image":data['image'], "image_text":data['product_name'][0]})
            data.update({'pk_id':data['pro_id'],
                        "preview_images":preview_images,
                        'sno':index+1,
                        'is_active':data['status'],
                        'metal':metal,
                        'category':category,
                        'tax':tax,
                        'calculation_based_on':cal_type,
                        'stock_type':stock_type,
                        "tax_type":tax_type,
                        "va_on":mc_calc_type,
                        "mc_on":wastage_calc_type,
                        'sales_based_on':sales_based_on})
        context={'columns':columns,'actions':PRODUCT_ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number}
        return pagination.paginated_response(serializer.data,context)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            data.update({"short_code": None})
        data.update({"created_by": request.user.pk})
        if(request.data['image'] != None):
            b = ((base64.b64decode(request.data['image']
            [request.data['image'].find(",") + 1:])))
            img = Image.open(io.BytesIO(b))
            filename = 'image.jpeg'
            img_object = ImageFile(io.BytesIO(
            img.fp.getvalue()), name=filename)
            data.update({"image":img_object})
        else:
            data.update({"image":None})
        sections = data.pop('sections', [])
        productserializer = ProductSerializer(data=data)
        productserializer.is_valid(raise_exception=True)
        productserializer.save()
        id_product = productserializer.data['pro_id']
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            Product.objects.filter(pro_id=id_product).update(short_code=id_product)
        for section in sections:
            result={'id_section':section,'id_product':id_product,"created_by": request.user.pk}
            sectionserializer = ProductSectionSerializer(data=result)
            sectionserializer.is_valid(raise_exception=True)
            sectionserializer.save()
        return Response({"message":"Product Created Successfully."}, status=status.HTTP_201_CREATED)



class ErpReorderSettingsListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = ErpReorderSettings.objects.all()
    serializer_class = ErpReorderSettingsSerializer
    
    def validate_reorder_settings(self, min_pcs, max_pcs, id_product, id_branch, id_size, id_design, id_sub_design, id_weight_range):
        overlaps = ErpReorderSettings.objects.filter(product=id_product, branch=id_branch, size=id_size,
                                                     design=id_design, sub_design=id_sub_design, weight_range = id_weight_range).filter(Q(min_pcs__lt=max_pcs) & Q(max_pcs__gt=min_pcs))
        if overlaps.exists():
            raise ValidationError('The min and max pieces overlaps with an existing range for the same combination.')
        
    def get(self, request, *args, **kwargs):
        reorder_settings = []
        branch = request.query_params.get('branch')
        product = request.query_params.get('product')
        if(ErpReorderSettings.objects.filter(product=product, branch=branch).exists()):
            queryset = ErpReorderSettings.objects.filter(product=product, branch=branch)
            serializer = ErpReorderSettingsSerializer(queryset, many=True)
            for data in serializer.data:
                del data['branch']
                del data['product']
                if data not in reorder_settings:
                    reorder_settings.append(data)
            instance = {"reorder_settings":reorder_settings}
            instance.update({"product":product, "branch":branch})
            return Response({"data":instance}, status=status.HTTP_200_OK)
        else:
            return Response({"message":"No data found","data":{}}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            reorder_datas =[]
            if(ErpReorderSettings.objects.filter(product=request.data['product'], branch=request.data['branch']).exists()):
                ErpReorderSettings.objects.filter(product=request.data['product'], branch=request.data['branch']).delete()
            for data in request.data['reorder_settings']:
                min_pcs = float(data['min_pcs'])
                max_pcs = float(data['max_pcs'])
                    
                try:
                    self.validate_reorder_settings(min_pcs, max_pcs, request.data['product'], request.data['branch'], data['size'], data['design'],
                                                   data['sub_design'], data['weight_range'])
                    reorder_datas.append(data)
                    data.update({"created_by": request.user.pk, "branch":request.data['branch'], "product":request.data['product']})
                    serializer = ErpReorderSettingsSerializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                except ValidationError as e:
                    del data
                    # return Response({'error': str(e)}, status=400)

            if(len(reorder_datas) == 0):
                return Response({"message":"The min and max pieces overlaps with an existing range for the same combination."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message":"Reorder settings created successfully."}, status=status.HTTP_201_CREATED)

class ProductDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get(self, request, *args, **kwargs):
        return_data = []
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Product status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ProductSerializer(obj, context={"request":request})
        return_data = serializer.data
        other_wt = []  # Ensure it exists
        for item in obj.other_weight.all():  # Use `.all()` to fetch related items
            other_wt.append({
                "label": item.name,
                "value": item.pk
            })

        return_data['other_weight'] = other_wt  
        return Response(return_data, status=status.HTTP_200_OK)


    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            request.data.update({"short_code": queryset.pro_id})
        request.data.update({"created_by": queryset.created_by.pk})
        #request.data.update({"image": None})
        
        metal = Metal.objects.filter(id_metal = request.data['id_metal']).get()
        category = Category.objects.filter(id_category = request.data['cat_id']).get()
        tax_id = Taxmaster.objects.filter(tax_id = request.data['tax_id']).get()

        metal = Metal.objects.filter(id_metal=request.data['id_metal']).get()
        category = Category.objects.filter(
            id_category=request.data['cat_id']).get()
        sections = request.data.pop('sections', [])
        image_data = request.data.pop("image", None)
        # if(request.data['image'] != None):
        #     b = ((base64.b64decode(request.data['image']
        #     [request.data['image'].find(",") + 1:])))
        #     img = Image.open(io.BytesIO(b))
        #     filename = 'image.jpeg'
        #     img_object = ImageFile(io.BytesIO(
        #     img.fp.getvalue()), name=filename)
        #     request.data.update({"image":img_object})
        # else:
        #     request.data.update({"image":None})

        if image_data is None:
            request.data.update({"image": None})

        elif not image_data.startswith('http'):
            try:
                b = base64.b64decode(image_data[image_data.find(",") + 1:])
                img = Image.open(io.BytesIO(b))
                filename = 'image.jpeg'
                img_object = ImageFile(io.BytesIO(b), name=filename)
                request.data.update({"image": img_object})
            
            except (base64.binascii.Error, ValueError) as e:
                print(f"Image decoding error: {e}")
                #request.data.pop("image")

        request.data.update(
            {"updated_by": request.user.pk, "updated_time": datetime.now(tz=timezone.utc)})
        serializer = ProductSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        id_product = serializer.data['pro_id']
        existing_sections = ProductSection.objects.filter(id_product=id_product)
        sections_to_keep = []
        for section in sections:
            existing_section = existing_sections.filter(id_section=section).first()
            if existing_section:
                sections_to_keep.append(existing_section.id_pro_section)
            else:
                result = {'id_section': section, 'id_product': id_product, "created_by": request.user.pk}
                sectionserializer = ProductSectionSerializer(data=result)
                sectionserializer.is_valid(raise_exception=True)
                sectionserializer.save()
                sections_to_keep.append(sectionserializer.data['id_pro_section'])
        existing_sections.exclude(id_pro_section__in=sections_to_keep).delete()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    
    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Product  can't be deleted, as it is already in Stock"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class CategoryListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get(self, request, *args, **kwargs):
        if 'status' in request.query_params:
            try:
                queryset = Category.objects.filter(status=True)
                serializer = CategorySerializer(queryset, many=True)
                return Response(serializer.data)
            except Exception:
                return Response({'status': False, 'message': 'Field Does not Exist'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = Category.objects.all()
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,CATEGORY_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,CATEGORY_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {"pk_id": data['id_category'], 'sno': index+1, "is_active": data['status'],"cat_type": data['cat_type_name']})
        context = {
            'columns': columns,
            'actions': CATEGORY_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': False,
            'filters': FILTERS
        }
        return pagination.paginated_response(serializer.data, context)

    def post(self, request, *args, **kwargs):
        purity_arr = []
        for each in request.data['purity']:
            try:
                purity = Purity.objects.get(id_purity=each)
                purity_arr.append(purity.pk)
            except Purity.DoesNotExist:
                pass
        if (request.data['image'] != None):
            b = ((base64.b64decode(request.data['image']
                                   [request.data['image'].find(",") + 1:])))
            img = Image.open(io.BytesIO(b))
            filename = 'category_image.jpeg'
            img_object = ImageFile(io.BytesIO(
                img.fp.getvalue()), name=filename)
            request.data.update({"image": img_object})
        else:
            request.data.update({"image": None})
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            request.data.update({"cat_code": None})
        request.data.update({"id_purity": purity_arr})
        request.data.update({"created_by": request.user.pk})
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            Category.objects.filter(id_category=serializer.data['id_category']).update(cat_code=serializer.data['id_category'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Category status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = CategorySerializer(obj)
        output = serializer.data
        # purities = []
        # for purity in serializer.data['id_purity']:
        #     purities.append(
        #             {"value": purity, "label": Purity.objects.get(id_purity=purity).purity})
        # output.update({"id_purity": purities})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        if(int(RetailSettings.objects.get(name='is_short_code_req').value)==1):
            request.data.update({"cat_code": queryset.id_category})
        purity_arr = []
        for each in request.data['purity']:
            try:
                purity = Purity.objects.get(id_purity=each)
                purity_arr.append(purity.pk)
            except Purity.DoesNotExist:
                pass
        request.data.update({"id_purity": purity_arr})
        request.data.update({"created_by": queryset.created_by.pk, "created_on":queryset.created_on})
        if (request.data['image'] != None):
            if 'data:image/' in request.data['image'][:30]:
                queryset.image.delete()
                b = (
                    (base64.b64decode(request.data['image'][request.data['image'].find(",") + 1:])))
                img = Image.open(io.BytesIO(b))
                filename = 'category_image.jpeg'
                img_object = ImageFile(io.BytesIO(
                    img.fp.getvalue()), name=filename)
                request.data.update({"image": img_object})
                serializer = self.get_serializer(queryset, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            del request.data['image']
            serializer = self.get_serializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            serializer = CategorySerializer(queryset, data=request.data)
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
    
class CategoryPurityRateListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = CategoryPurityRate.objects.all()
    serializer_class = CategoryPurityRateSerializer
    
    def get(self, request, *args, **kwargs):
        output = []
        queryset = Category.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None,CATEGORY_PURITY_RATE_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,CATEGORY_PURITY_RATE_COLUMN_LIST,request.query_params.get("path_name",''))
        output = []
        serializer = CategorySerializer(page, many=True)
        for index, data in enumerate(serializer.data, start=1):
            for purities in data['id_purity']:
                instance = {}
                purity = Purity.objects.filter(id_purity=purities).first()
                instance.update({"category":data['id_category'], "purity":purities, "id":uuid.uuid4(),
                                 "category_name":data['cat_name'], "purity_name":purity.purity,
                                 "sno": index,})
                if(CategoryPurityRate.objects.filter(category = data['id_category'], purity = purities).exists()):
                    cat_pur_rate = CategoryPurityRate.objects.filter(category = data['id_category'], purity = purities).get()
                    user = User.objects.filter(id=cat_pur_rate.created_by.pk).first()
                    instance.update({"rate_per_gram": cat_pur_rate.rate_per_gram,
                                     "created_by":user.first_name,
                                     "date": date_format_with_time(cat_pur_rate.created_on)})
                else:
                    instance.update({"rate_per_gram": None})
                if instance not in output:
                    output.append(instance)
        context = {'columns': columns, 'actions': CATEGORY_PURITY_RATE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(output, context)
    
class CategoryPurityRateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = CategoryPurityRate.objects.all()
    serializer_class = CategoryPurityRateSerializer
    
    def get(self, request, *args, **kwargs):
        output = []
        queryset = Category.objects.filter(show_in_metal_rate = True)
        serializer = CategorySerializer(queryset, many=True)
        for data in serializer.data:
            
            for purities in data['id_purity']:
                instance = {}
                instance.update({"category":data['id_category'], "purity":purities, "id":uuid.uuid4()})
                if(CategoryPurityRate.objects.filter(category = data['id_category'], purity = purities).exists()):
                    cat_pur_rate = CategoryPurityRate.objects.filter(category = data['id_category'], purity = purities).get()
                    instance.update({"rate_per_gram": cat_pur_rate.rate_per_gram, "show_in_listing":cat_pur_rate.show_in_listing})
                else:
                    instance.update({"rate_per_gram": None})
                if instance not in output:
                    output.append(instance)
        return Response(output, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        for data in request.data['cat_pur_rate']:
            if(CategoryPurityRate.objects.filter(category = data['category'], purity = data['purity']).exists()):
                cat_pur_rate = CategoryPurityRate.objects.filter(category = data['category'], purity = data['purity']).get()
                cat_pur_rate.rate_per_gram = data['rate_per_gram']
                cat_pur_rate.show_in_listing = data['show_in_listing']
                cat_pur_rate.updated_by = request.user
                cat_pur_rate.updated_on = datetime.now(tz=timezone.utc)
                cat_pur_rate.save()
            else:
                data.update({"created_by": request.user.pk})
                serializer = CategoryPurityRateSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return Response({"message":"Category Purity Rate created successfully"}, status=status.HTTP_201_CREATED)
    
class CategoryPurityRates(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        queryset = CategoryPurityRate.objects.filter(show_in_listing=True)
        serializer = CategoryPurityRateSerializer(queryset, many=True)
        for data in serializer.data:
            instance = {}
            cat = Category.objects.filter(id_category=data['category']).first()
            purity = Purity.objects.filter(id_purity=data['purity']).first()
            instance.update({"category":data['category'], "purity":purity.purity, "id":uuid.uuid4(),
                            "category_name":cat.cat_name, "rate":data['rate_per_gram']})
            if instance not in output:
                output.append(instance)
        return Response(output, status=status.HTTP_200_OK)
    
class DesignListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Design.objects.all()
    serializer_class = DesignSerializer

    # GET ALL DESIGN
    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:  # GET ACTIVE DESIGN
            queryset = Design.objects.filter(status=True)
            serializer = DesignSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset.order_by('-pk'), request,None, DESIGN_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,DESIGN_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_design'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': columns, 'actions': DESIGN_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    # CREATE DESIGN
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            request.data.update({"created_by": request.user.pk})
            # if(int(RetailSettings.objects.get(name='is_design_mapping_req').value) == 1 and len(request.data['product'])==0):
            #     return Response({"error_detail": ["Product mapping is required"]}, status=status.HTTP_400_BAD_REQUEST)
            # elif(int(RetailSettings.objects.get(name='is_design_mapping_req').value) == 1 and len(request.data['product'])>0):
            #     serializer = DesignSerializer(data=request.data)
            #     serializer.is_valid(raise_exception=True)
            #     serializer.save()
            #     for ids in request.data['product']:
            #         instance = {}
            #         instance.update({"id_product":ids, "id_design":serializer.data['id_design'], "created_by": request.user.pk})
            #         map_serializer = ProductMappingSerializer(data=instance)
            #         map_serializer.is_valid(raise_exception=True)
            #         map_serializer.save()
            #     return Response({"message":"Design created successfully"}, status=status.HTTP_200_OK)
            # elif(int(RetailSettings.objects.get(name='is_design_mapping_req').value) != 1):
            serializer = DesignSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class DesignDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Design.objects.all()
    serializer_class = DesignSerializer
    # GET  DESIGN WITH ID

    def get(self, request, *args, **kwargs):
        products = []
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Design status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = DesignSerializer(obj)
        output = serializer.data
        if(int(RetailSettings.objects.get(name='is_design_mapping_req').value) == 1):
            map_queryset = ProductMapping.objects.filter(id_design=obj.id_design)
            map_serializer = ProductMappingSerializer(map_queryset, many=True)
            for product in map_serializer.data:
                    products.append(
                        {"value": product['id_product'], "label": Product.objects.get(pro_id=product['id_product']).product_name})
        output.update({"products":products})
        return Response(output, status=status.HTTP_200_OK)
    # UPDATE DESIGN

    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            queryset = self.get_object()
            request.data.update({"created_by": queryset.created_by.pk})
            if(int(RetailSettings.objects.get(name='is_design_mapping_req').value) == 1 and len(request.data['product'])==0):
                return Response({"error_detail": ["Product mapping is required"]}, status=status.HTTP_400_BAD_REQUEST)
            elif(int(RetailSettings.objects.get(name='is_design_mapping_req').value) != 1):
                serializer = DesignSerializer(queryset, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(updated_by=self.request.user,
                                updated_on=datetime.now(tz=timezone.utc))
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            elif(int(RetailSettings.objects.get(name='is_design_mapping_req').value) == 1 and len(request.data['product'])>0):
                serializer = DesignSerializer(queryset, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(updated_by=self.request.user,
                                updated_on=datetime.now(tz=timezone.utc))
                if(ProductMapping.objects.filter(id_design=queryset.id_design).exists()):
                    ProductMapping.objects.filter(id_design=queryset.id_design).delete()
                for ids in request.data['product']:
                    instance = {}
                    instance.update({"id_product":ids, "id_design":serializer.data['id_design'], "created_by": request.user.pk})
                    map_serializer = ProductMappingSerializer(data=instance)
                    map_serializer.is_valid(raise_exception=True)
                    map_serializer.save()
                return Response({"message":"Design updated successfully"}, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            # if(ProductMapping.objects.filter(id_design=queryset.id_design).exists()):
            #     ProductMapping.objects.filter(id_design=queryset.id_design).delete()
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Design instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubDesignListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = SubDesign.objects.all()
    serializer_class = SubDesignSerializer

    # GET ALL SUB DESIGN
    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = SubDesign.objects.filter(status=True)
            serializer = SubDesignSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset.order_by('-pk'), request,None, SUB_DESIGN_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,SUB_DESIGN_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_sub_design'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': columns, 'actions': SUB_DESIGN_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    # CREATE SUB DESIGN
    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = SubDesignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Sub Design Created Successfully."}, status=status.HTTP_201_CREATED)


class SubDesignDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = SubDesign.objects.all()
    serializer_class = SubDesignSerializer
    # GET SUB DESIGN WITH ID

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Area status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = SubDesignSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
     # UPDATE SUB DESIGN

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = SubDesignSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Sub Design instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DesignMappingView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee | IsCustomerUser]
    queryset = ProductMapping.objects.all()
    serializer_class = ProductMappingSerializer

    # GET Design Mapping
    def get(self, request, *args, **kwargs):
        id_product = request.query_params.get('id_product')
        id_design = request.query_params.get('id_design','')
        queryset = ProductMapping.objects.all()
        # Filter queryset based on id_product if provided
        if id_product:
            queryset = queryset.filter(id_product=id_product)
        # Further filter queryset based on id_design if provided
        if id_design:
            queryset = queryset.filter(id_design=id_design)
        serializer = ProductMappingSerializer(queryset, many=True)
        result = []
        for data in serializer.data:
            mapped_object = {}
            product_queryset = Product.objects.filter(
                pro_id=data['id_product'], status=1)
            design_queryset = Design.objects.filter(
                id_design=data['id_design'], status=1)
            if (product_queryset.exists() and design_queryset.exists()):
                product = product_queryset.get()
                design = design_queryset.get()
                design_name = design.design_name
                mapped_object.update({
                    "id_product_mapping": data['id_product_mapping'],
                    "id_product": data['id_product'],
                    "id_design": data['id_design'],
                    "product_name": product.product_name,
                    "design_name": design_name})
                result.append(mapped_object)
        if (len(result) > 0):
            return Response({"message": "List Retrieved Successfully", "data": result}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No Record Found", "data": result}, status=status.HTTP_200_OK)

    # CREATE Design Mapping
    def post(self, request, *args, **kwargs):
        try:
            request.data.update({"created_by": request.user.pk})
            id_product = request.data.get('id_product')
            id_design = request.data.get('id_design')

            # Check if id_design is an int or list
            if isinstance(id_design, (int, str)):
                id_design_list = [id_design]
            elif isinstance(id_design, list):
                id_design_list = id_design
            else:
                return Response({"detail": "id_design must be an integer or a list."}, status=status.HTTP_400_BAD_REQUEST)

            created_entries = []
            for design in id_design_list:
                data = {
                    "id_product": id_product,
                    "id_design": design,
                    "created_by": request.user.pk
                }
                serializer = ProductMappingSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                created_entries.append(serializer.data)

            return Response({"message": "Design Mapped Successfully."}, status=status.HTTP_201_CREATED)
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
            return Response({"error_detail": ["Design Mapped can't be deleted, as it is already in Stock"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class SubDesignMappingView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee | IsCustomerUser]
    queryset = SubDesignMapping.objects.all()
    serializer_class = SubDesignMappingSerializer

    # GET Sub Design Mapping
    def get(self, request, *args, **kwargs):
        id_product = request.query_params.get('id_product')
        id_design = request.query_params.get('id_design')
        id_sub_design = request.query_params.get('id_sub_design')
        queryset = SubDesignMapping.objects.all()
        # Filter queryset based on id_product if provided
        if id_product:
            queryset = queryset.filter(id_product=id_product)
        # Further filter queryset based on id_design if provided
        if id_design:
            queryset = queryset.filter(id_design=id_design)
        # Further filter queryset based on id_sub_design if provided
        if id_sub_design:
            queryset = queryset.filter(id_sub_design=id_sub_design)
        serializer = SubDesignMappingSerializer(queryset, many=True)
        result = []
        for data in serializer.data:
            mapped_object = {}
            product_queryset = Product.objects.filter(
                pro_id=data['id_product'], status=1)
            design_queryset = Design.objects.filter(
                id_design=data['id_design'], status=1)
            sub_design_queryset = SubDesign.objects.filter(
                id_sub_design=data['id_sub_design'], status=1)
            if (product_queryset.exists() and design_queryset.exists() and sub_design_queryset.exists()):
                product = product_queryset.get()
                design = design_queryset.get()
                sub_design = sub_design_queryset.get()
                mapped_object.update({
                    "id_product_mapping": data['id_product_mapping'],
                    "id_product": data['id_product'],
                    "id_design": data['id_design'],
                    "id_sub_design": data['id_sub_design'],
                    "product_name": product.product_name,
                    "design_name": design.design_name,
                    "sub_design_name": sub_design.sub_design_name,
                })
                result.append(mapped_object)
        if (len(result) > 0):
            return Response({"message": "List Retrieved Successfully", "data": result}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "No Record Found", "data": result}, status=status.HTTP_201_CREATED)

    # CREATE Sub Design Mapping

    def post(self, request, *args, **kwargs):
        try:
            request.data.update({"created_by": request.user.pk})
            id_product = request.data.get('id_product')
            id_design = request.data.get('id_design')
            id_sub_design = request.data.get('id_sub_design')

            # Check if id_design is an int or list
            if isinstance(id_sub_design, (int, str)):
                id_sub_design_list = [id_sub_design]
            elif isinstance(id_sub_design, list):
                id_sub_design_list = id_sub_design
            else:
                return Response({"detail": "id_sub_design must be an integer or a list."}, status=status.HTTP_400_BAD_REQUEST)

            created_entries = []
            for sub_design in id_sub_design_list:
                data = {
                    "id_product": id_product,
                    "id_design": id_design,
                    "id_sub_design": sub_design,
                    "created_by": request.user.pk
                }
                serializer = SubDesignMappingSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                created_entries.append(serializer.data)

            return Response({"message": "Sub Design Mapped Successfully."}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)

    # Delete Sub Design Mapping
    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Design Mapped can't be deleted, as it is already in Stock"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MakingAndWastageSettingsListView(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = MakingAndWastageSettings.objects.all()
    serializer_class = MakingAndWastageSettingsMappingSerializer
    def get(self, request, *args, **kwargs):
        retail_queryset = MakingAndWastageSettings.objects.all()
        retail_serializer = MakingAndWastageSettingsMappingSerializer(
            retail_queryset, many=True)
        customer_queryset = CustomerMakingAndWastageSettings.objects.all()
        customer_serializer = CustomerMakingAndWastageSettingsMappingSerializer(
            customer_queryset, many=True)
        data = { "retail" : retail_serializer.data,"customer" : customer_serializer.data }
        return Response(data, status=status.HTTP_200_OK)
    
    def validate_mcva_settings(self, min_value, max_value, min_percent, max_percent, id_product, id_design, id_sub_design, id_weight_range):
        overlaps = MakingAndWastageSettings.objects.filter(id_product=id_product,
                                                     id_design=id_design, id_sub_design=id_sub_design, id_weight_range = id_weight_range).filter(Q(min_mc_value__lt=max_value) & Q(max_mc_value__gt=min_value) & Q(min_wastage_percentage__lt=max_percent) & Q(max_wastage_percentage__gt=min_percent))
        if overlaps.exists():
            raise ValidationError('The min and max values overlaps with an existing range for the same combination.')

    def post(self, request, *args, **kwargs):
        mcva_settings = []
        instance = {}
        product = request.data['product']
        supplier_ids = request.data['supplier']
        purity = request.data['purity']
        # print(product)
        # print(supplier_ids)
        # print(purity)
        # Fetch is_sub_design_req value from RetailSettings
        is_sub_design_req = int(RetailSettings.objects.get(name='is_sub_design_req').value)
        # print(is_sub_design_req)
        
        base_filters = Q(id_product=product)

        # Filter by supplier if provided
        if len(supplier_ids) > 0:
            base_filters &= Q(supplier__in=supplier_ids)
        
        # Filter by purity if provided
        if purity is not None:
            base_filters &= Q(purity=purity)

        # Filter mappings based on is_sub_design_req flag
        product_obj = Product.objects.filter(pro_id=product).first()
        if is_sub_design_req == int(1):
            instance = {}
            sub_design_mappings = SubDesignMapping.objects.filter(id_product=product)
            for mapping in sub_design_mappings:
                wastage_settings_result = MakingAndWastageSettings.objects.filter(
                    base_filters, 
                    id_design=mapping.id_design, 
                    id_sub_design=mapping.id_sub_design
                )
                if wastage_settings_result:
                    for wastage_settings in wastage_settings_result:
                    # Check if wastage settings exist, else set defaults
                        if wastage_settings:
                            instance = {}
                            if(wastage_settings.pure_wt_type == 1):
                                instance.update({"label":"Touch", "value":1})
                            elif(wastage_settings.pure_wt_type == 2):
                                instance.update({"label":"Touch+VA", "value":2})
                            else:
                                instance.update({"label":"Wt * VA %", "value":3})
                            mcva_settings.append({
                            "is_sub_design_req":True,
                            "isChecked": True if wastage_settings.id_weight_range else False,
                            "id_product": {"label": mapping.id_product.product_name, "value": mapping.id_product.pk},
                            # "id_design": {"label": mapping.id_design.design_name, "value": mapping.id_design.pk},
                            # "id_sub_design": {"label": mapping.id_sub_design.sub_design_name, "value": mapping.id_sub_design.pk} if mapping.id_sub_design else None,
                            "id_design": mapping.id_design.pk,
                            "design_name": mapping.id_design.design_name,
                            "id_sub_design": mapping.id_sub_design.pk if mapping.id_sub_design else None,
                            "sub_design_name":  mapping.id_sub_design.sub_design_name if mapping.id_sub_design else None,
                            "id_weight_range": wastage_settings.id_weight_range.pk if wastage_settings.id_weight_range else None,
                            
                            "purchase_touch": wastage_settings.purchase_touch,
                            "pure_wt_type":instance,
                            "purchase_mc_type": {"label": "Gross weight" if wastage_settings.purchase_mc_type == 1  else "Net weight", "value": wastage_settings.purchase_mc_type},
                            "purchase_mc": wastage_settings.purchase_mc,
                            "purchase_va_type": {"label": "Gross weight" if wastage_settings.purchase_va_type == 1 else "Net weight", "value": wastage_settings.purchase_va_type},
                            "purchase_va": wastage_settings.purchase_va,
                            "purchase_flat_mc": wastage_settings.purchase_flat_mc,
                            "purchase_sales_rate": wastage_settings.purchase_sales_rate if product_obj.sales_mode=='0' else None,
                            
                            "retail_touch": wastage_settings.retail_touch,
                            "retail_mc_type": {"label": "Gross weight" if wastage_settings.retail_mc_type == 1 else "Net weight", "value": wastage_settings.retail_mc_type},
                            "retail_mc": wastage_settings.retail_mc,
                            "retail_va_type": {"label": "Gross weight" if wastage_settings.retail_va_type == 1 else "Net weight", "value": wastage_settings.retail_va_type},
                            "retail_va": wastage_settings.retail_va,
                            "retail_flat_mc": wastage_settings.retail_flat_mc,
                            
                            "vip_retail_touch": wastage_settings.vip_retail_touch,
                            "vip_retail_mc_type": {"label": "Gross weight" if wastage_settings.vip_retail_mc_type == 1 else "Net weight", "value": wastage_settings.vip_retail_mc_type},
                            "vip_retail_mc": wastage_settings.vip_retail_mc,
                            "vip_retail_va_type": {"label": "Gross weight" if wastage_settings.vip_retail_va_type == 1 else "Net weight", "value": wastage_settings.vip_retail_va_type},
                            "vip_retail_va": wastage_settings.vip_retail_va,
                            "vip_retail_flat_mc": wastage_settings.vip_retail_flat_mc,
                            
                        })
                else:
                    # Append default values if no wastage settings exist
                    mcva_settings.append({
                        "is_sub_design_req":True,
                        "isChecked": False,
                        "id_product": {"label": mapping.id_product.product_name, "value": mapping.id_product.pk},
                        # "id_design": {"label": mapping.id_design.design_name, "value": mapping.id_design.pk},
                        # "id_sub_design": {"label": mapping.id_sub_design.sub_design_name, "value": mapping.id_sub_design.pk} if mapping.id_sub_design else None,
                        "id_design": mapping.id_design.pk,
                        "design_name": mapping.id_design.design_name,
                        "id_sub_design": mapping.id_sub_design.pk if mapping.id_sub_design else None,
                        "sub_design_name":  mapping.id_sub_design.sub_design_name if mapping.id_sub_design else None,
                        "id_weight_range": None,
                        
                        "purchase_touch": 0.00,
                        "pure_wt_type": {"label": "Touch+VA", "value": 2},
                        "purchase_mc_type": {"label": "Gross weight", "value": 1},
                        "purchase_mc": 0.00,
                        "purchase_va_type": {"label": "Gross weight", "value": 1},
                        "purchase_va": 0.00,
                        "purchase_flat_mc": 0.00,
                        "purchase_sales_rate": 0.00 if product_obj.sales_mode =='0' else None,
                        
                        "retail_touch": 0.00,
                        "retail_mc_type": {"label": "Gross weight", "value": 1},
                        "retail_mc": 0.00,
                        "retail_va_type": {"label": "Gross weight", "value": 1},
                        "retail_va": 0.00,
                        "retail_flat_mc": 0.00,
                        
                        "vip_retail_touch": 0.00,
                        "vip_retail_mc_type": {"label": "Gross weight", "value": 1},
                        "vip_retail_mc": 0.00,
                        "vip_retail_va_type": {"label": "Gross weight", "value": 1},
                        "vip_retail_va": 0.00,
                        "vip_retail_flat_mc": 0.00,
                        
                    })

        if is_sub_design_req == int(0):
            instance = {}
            product_mappings = ProductMapping.objects.filter(id_product=product)
            for mapping in product_mappings:
                wastage_settings = MakingAndWastageSettings.objects.filter(
                    base_filters,
                    id_design=mapping.id_design
                ).first()

                if wastage_settings:
                    instance = {}
                    if(wastage_settings.pure_wt_type == 1):
                        instance.update({"label":"Touch", "value":1})
                    elif(wastage_settings.pure_wt_type == 2):
                        instance.update({"label":"Touch+VA", "value":2})
                    else:
                        instance.update({"label":"Wt * VA %", "value":3})
                    mcva_settings.append({
                        "is_sub_design_req":False,
                        "isChecked": True if wastage_settings.id_weight_range else False,
                        "id_product": {"label": mapping.id_product.product_name, "value": mapping.id_product.pk},
                        # "id_design": {"label": mapping.id_design.design_name, "value": mapping.id_design.pk},
                        "id_design": mapping.id_design.pk,
                        "design_name": mapping.id_design.design_name,
                        "id_sub_design": None,
                        "id_weight_range": wastage_settings.id_weight_range.pk if wastage_settings.id_weight_range else None,
                        
                        "purchase_touch": wastage_settings.purchase_touch,
                        "pure_wt_type":instance,
                        "purchase_mc_type": {"label": "Gross weight" if wastage_settings.purchase_mc_type == 1 else "Net weight", "value": wastage_settings.purchase_mc_type},
                        "purchase_mc": wastage_settings.purchase_mc,
                        "purchase_va_type": {"label": "Gross weight" if wastage_settings.purchase_va_type == 1 else "Net weight", "value": wastage_settings.purchase_va_type},
                        "purchase_va": wastage_settings.purchase_va,
                        "purchase_flat_mc": wastage_settings.purchase_flat_mc,
                        "purchase_sales_rate": wastage_settings.purchase_sales_rate if product_obj.sales_mode=='0' else None,
                        
                        "retail_touch": wastage_settings.retail_touch,
                        "retail_mc_type": {"label": "Gross weight" if wastage_settings.retail_mc_type == 1 else "Net weight", "value": wastage_settings.retail_mc_type},
                        "retail_mc": wastage_settings.retail_mc,
                        "retail_va_type": {"label": "Gross weight" if wastage_settings.retail_va_type == 1 else "Net weight", "value": wastage_settings.retail_va_type},
                        "retail_va": wastage_settings.retail_va,
                        "retail_flat_mc": wastage_settings.retail_flat_mc,
                        
                        "vip_retail_touch": wastage_settings.vip_retail_touch,
                        "vip_retail_mc_type": {"label": "Gross weight" if wastage_settings.vip_retail_mc_type == 1 else "Net weight", "value": wastage_settings.vip_retail_mc_type},
                        "vip_retail_mc": wastage_settings.vip_retail_mc,
                        "vip_retail_va_type": {"label": "Gross weight" if wastage_settings.vip_retail_va_type == 1 else "Net weight", "value": wastage_settings.vip_retail_va_type},
                        "vip_retail_va": wastage_settings.vip_retail_va,
                        "vip_retail_flat_mc": wastage_settings.vip_retail_flat_mc,
                    })
                else:
                    mcva_settings.append({
                        "is_sub_design_req":False,
                        "isChecked": False,
                        "id_product": {"label": mapping.id_product.product_name, "value": mapping.id_product.pk},
                        # "id_design": {"label": mapping.id_design.design_name, "value": mapping.id_design.pk},
                        "id_design": mapping.id_design.pk,
                        "design_name": mapping.id_design.design_name,
                        "id_sub_design": None,
                        "id_weight_range": None,
                        
                        "purchase_touch": 0.00,
                        "pure_wt_type": {"label": "Touch+VA", "value": 2},
                        "purchase_mc_type": {"label": "Gross weight", "value": 1},
                        "purchase_mc": 0.00,
                        "purchase_va_type": {"label": "Gross weight", "value": 1},
                        "purchase_va": 0.00,
                        "purchase_flat_mc": 0.00,
                        "purchase_sales_rate": 0.00 if product_obj.sales_mode=='0' else None,
                        
                        "retail_touch": 0.00,
                        "retail_mc_type": {"label": "Gross weight", "value": 1},
                        "retail_mc": 0.00,
                        "retail_va_type": {"label": "Gross weight", "value": 1},
                        "retail_va": 0.00,
                        "retail_flat_mc": 0.00,
                        
                        "vip_retail_touch": 0.00,
                        "vip_retail_mc_type": {"label": "Gross weight", "value": 1},
                        "vip_retail_mc": 0.00,
                        "vip_retail_va_type": {"label": "Gross weight", "value": 1},
                        "vip_retail_va": 0.00,
                        "vip_retail_flat_mc": 0.00,
                    })

        return Response(mcva_settings, status=status.HTTP_200_OK)


class MakingAndWastageSettingsCreateView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = MakingAndWastageSettings.objects.all()
    serializer_class = MakingAndWastageSettingsMappingSerializer
    # CREATE MC VA Setting
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            mcva_datas =[]
            supplier_ids = request.data.get('supplier', [])
            if(MakingAndWastageSettings.objects.filter(id_product=request.data['id_product'], purity=request.data['purity'],
                                                       supplier__in=supplier_ids).exists()):
                MakingAndWastageSettings.objects.filter(id_product=request.data['id_product'], purity=request.data['purity'],
                                                        supplier__in=supplier_ids).delete()
            for data in request.data['mcva_settings']:
                data.update({"created_by": request.user.pk})
                serializer = MakingAndWastageSettingsMappingSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            return Response({"message":"Making & wastage settings created successfully."}, status=status.HTTP_201_CREATED)
                # min_value = float(data['min_mc_value'])
                # max_value = float(data['max_mc_value'])
                # min_percent = float(data['min_wastage_percentage'])
                # max_percent = float(data['max_wastage_percentage'])
                    
                # try:
                #     self.validate_mcva_settings(min_value, max_value,min_percent, max_percent, request.data['id_product'], data['id_design'],
                #                                    data['id_sub_design'], data['id_weight_range'])
                #     mcva_datas.append(data)
                #     data.update({"created_by": request.user.pk, "id_product":request.data['id_product']})
                #     serializer = MakingAndWastageSettingsMappingSerializer(data=data)
                #     serializer.is_valid(raise_exception=True)
                #     serializer.save()
                # except ValidationError as e:
                #     del data
                    # return Response({'error': str(e)}, status=400)

            # if(len(mcva_datas) == 0):
            #     return Response({"message":"The min and max values overlaps with an existing range for the same combination."}, status=status.HTTP_400_BAD_REQUEST)
            # return Response({"message":"Making & wastage settings created successfully."}, status=status.HTTP_201_CREATED)


# class MakingAndWastageSettingsDetailsView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsEmployee, isSuperuser]
#     queryset = MakingAndWastageSettings.objects.all()
#     serializer_class = MakingAndWastageSettingsMappingSerializer
#     # GET MC VA Setting  WITH ID

#     def get(self, request, *args, **kwargs):
#         obj = self.get_object()
#         serializer = MakingAndWastageSettingsMappingSerializer(obj)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#      # UPDATE MC VA Setting

#     def put(self, request, *args, **kwargs):
#         queryset = self.get_object()
#         request.data.update({"created_by": queryset.created_by.pk})
#         serializer = MakingAndWastageSettingsMappingSerializer(
#             queryset, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(updated_by=self.request.user,
#                         updated_on=datetime.now(tz=timezone.utc))
#         return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
#      # Delete MC VA Setting

#     def delete(self, request, *args, **kwargs):
#         id_mc_wast_settings = request.data.get('id_mc_wast_settings')

#         if not id_mc_wast_settings:
#             return Response({"detail": "id_mc_wast_settings is required."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             settings = MakingAndWastageSettings.objects.get(
#                 pk=id_mc_wast_settings)
#         except MakingAndWastageSettings.DoesNotExist:
#             return Response({"detail": "Mc And Va Settings not found."}, status=status.HTTP_404_NOT_FOUND)

#         settings.delete()
#         return Response({"detail": "Mc And Va Settings deleted successfully."}, status=status.HTTP_200_OK)


class CustomerMakingAndWastageSettingsListView(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = CustomerMakingAndWastageSettings.objects.all()
    serializer_class = CustomerMakingAndWastageSettingsMappingSerializer
    
    def validate_mcva_settings(self, min_value, max_value, min_percent, max_percent, id_product, id_design, id_sub_design, id_weight_range):
        overlaps = CustomerMakingAndWastageSettings.objects.filter(id_product=id_product,
                                                     id_design=id_design, id_sub_design=id_sub_design, id_weight_range = id_weight_range).filter(Q(min_mc_value__lt=max_value) & Q(max_mc_value__gt=min_value) & Q(min_wastage_percentage__lt=max_percent) & Q(max_wastage_percentage__gt=min_percent))
        if overlaps.exists():
            raise ValidationError('The min and max values overlaps with an existing range for the same combination.')

    def post(self, request, *args, **kwargs):
        mcva_settings = []
        instance = {}
        product = request.data['product']
        purity = request.data['purity']
        base_filters = Q(id_product=product)

        # Filter by supplier if provided
        # if supplier_ids:
        #     base_filters &= Q(supplier__in=supplier_ids)
        
        # Filter by purity if provided
        if purity is not None:
            base_filters &= Q(purity=purity)

        # Fetch is_sub_design_req value from RetailSettings
        is_sub_design_req = int(RetailSettings.objects.get(name='is_sub_design_req').value)
        print(is_sub_design_req)

        # Filter mappings based on is_sub_design_req flag
        product_obj = Product.objects.filter(pro_id=product).first()
        if is_sub_design_req == int(1):
            instance = {}
            sub_design_mappings = SubDesignMapping.objects.filter(id_product=product)
            for mapping in sub_design_mappings:
                wastage_settings = CustomerMakingAndWastageSettings.objects.filter(
                    base_filters, 
                    id_design=mapping.id_design, 
                    id_sub_design=mapping.id_sub_design
                ).first()

                # Check if wastage settings exist, else set defaults
                if wastage_settings:
                    mcva_settings.append({
                        "id":wastage_settings.pk,
                        "is_sub_design_req":True,
                        "isChecked": True if wastage_settings.id_weight_range else False,
                        "id_product": {"label": mapping.id_product.product_name, "value": mapping.id_product.pk},
                        # "id_design": {"label": mapping.id_design.design_name, "value": mapping.id_design.pk},
                        # "id_sub_design": {"label": mapping.id_sub_design.sub_design_name, "value": mapping.id_sub_design.pk} if mapping.id_sub_design else None,
                        "id_design": mapping.id_design.pk,
                        "design_name": mapping.id_design.design_name,
                        "id_sub_design": mapping.id_sub_design.pk if mapping.id_sub_design else None,
                        "sub_design_name":  mapping.id_sub_design.sub_design_name if mapping.id_sub_design else None,
                        "id_weight_range": wastage_settings.id_weight_range.pk if wastage_settings.id_weight_range else None,
                        
                        
                        "mc_type": {"label": "Gross weight" if wastage_settings.mc_type == 1 else "Net weight", "value": wastage_settings.mc_type},
                        "min_mc_value": wastage_settings.min_mc_value,
                        "max_mc_value": wastage_settings.max_mc_value,
                        "flat_mc_max": wastage_settings.flat_mc_max,
                        "flat_mc_min": wastage_settings.flat_mc_min,
                        "sales_rate": wastage_settings.sales_rate if product_obj.sales_mode=='0' else None,
                        "va_type": {"label": "Gross weight" if wastage_settings.va_type == 1 else "Net weight", "value": wastage_settings.va_type},
                        "min_va_value": wastage_settings.min_va_value,
                        "max_va_value": wastage_settings.max_va_value,
                        
                    })
                else:
                    # Append default values if no wastage settings exist
                    mcva_settings.append({
                        "is_sub_design_req":True,
                        "isChecked": False,
                        "id_product": {"label": mapping.id_product.product_name, "value": mapping.id_product.pk},
                        # "id_design": {"label": mapping.id_design.design_name, "value": mapping.id_design.pk},
                        # "id_sub_design": {"label": mapping.id_sub_design.sub_design_name, "value": mapping.id_sub_design.pk} if mapping.id_sub_design else None,
                        "id_design": mapping.id_design.pk,
                        "design_name": mapping.id_design.design_name,
                        "id_sub_design": mapping.id_sub_design.pk if mapping.id_sub_design else None,
                        "sub_design_name":  mapping.id_sub_design.sub_design_name if mapping.id_sub_design else None,
                        "id_weight_range": None,
                        
                        
                        "mc_type": {"label": "Gross weight", "value": 1},
                        "min_mc_value": 0.00,
                        "max_mc_value": 0.00,
                        "flat_mc_max": 0.00,
                        "flat_mc_min": 0.00,
                        "sales_rate": 0.00 if product_obj.sales_mode=='0' else None,
                        "va_type": {"label": "Gross weight", "value": 1},
                        "min_va_value": 0.00,
                        "max_va_value": 0.00,
                        
                        
                    })

        if is_sub_design_req == int(0):
            instance = {}
            product_mappings = ProductMapping.objects.filter(id_product=product)
            for mapping in product_mappings:
                customer_wastage_settings = CustomerMakingAndWastageSettings.objects.filter(
                    base_filters, 
                    id_design=mapping.id_design
                )

                if customer_wastage_settings:
                     for wastage_settings in customer_wastage_settings:
                            mcva_settings.append({
                                "id":wastage_settings.pk,
                                "is_sub_design_req":False,
                                "isChecked": True if wastage_settings.id_weight_range else False,
                                "id_product": {"label": mapping.id_product.product_name, "value": mapping.id_product.pk},
                                # "id_design": {"label": mapping.id_design.design_name, "value": mapping.id_design.pk},
                                "id_design": mapping.id_design.pk,
                                "design_name": mapping.id_design.design_name,
                                "id_sub_design": None,
                                "id_weight_range": wastage_settings.id_weight_range.pk if wastage_settings.id_weight_range else None,
                                
                                "mc_type": {"label": "Gross weight" if wastage_settings.mc_type == 1 else "Net weight", "value": wastage_settings.mc_type},
                                "min_mc_value": wastage_settings.min_mc_value,
                                "max_mc_value": wastage_settings.max_mc_value,
                                "flat_mc_max": wastage_settings.flat_mc_max,
                                "flat_mc_min": wastage_settings.flat_mc_min,
                                "sales_rate": wastage_settings.sales_rate if product_obj.sales_mode=='0' else None,
                                "sales_rate_type": wastage_settings.sales_rate_type if product_obj.sales_mode=='0' else None,
                                "sales_rate_type_label": (
                                    'Amount' if (product_obj.sales_mode == '0' and wastage_settings.sales_rate_type == 1)
                                    else 'Percentage' if (product_obj.sales_mode == '0' and wastage_settings.sales_rate_type == 2)
                                    else None
                                ),
                                "va_type": {"label": "Gross weight" if wastage_settings.va_type == 1 else "Net weight", "value": wastage_settings.va_type},
                                "min_va_value": wastage_settings.min_va_value,
                                "max_va_value": wastage_settings.max_va_value,
                            })
                else:
                    mcva_settings.append({
                        "is_sub_design_req":False,
                        "isChecked": False,
                        "id_product": {"label": mapping.id_product.product_name, "value": mapping.id_product.pk},
                        # "id_design": {"label": mapping.id_design.design_name, "value": mapping.id_design.pk},
                        "id_design": mapping.id_design.pk,
                        "design_name": mapping.id_design.design_name,
                        "id_sub_design": None,
                        "id_weight_range": None,
                        
                        "mc_type": {"label": "Gross weight", "value": 1},
                        "min_mc_value": 0.00,
                        "max_mc_value": 0.00,
                        "flat_mc_max": 0.00,
                        "flat_mc_min": 0.00,
                        "sales_rate": 0.00 if product_obj.sales_mode=='0' else None,
                        "sales_rate_type": 1 if product_obj.sales_mode=='0' else None,
                        "sales_rate_type_label": 'Amount' if product_obj.sales_mode=='0' else None,
                        "va_type": {"label": "Gross weight", "value": 1},
                        "min_va_value": 0.00,
                        "max_va_value": 0.00,
                    })

        return Response(mcva_settings, status=status.HTTP_200_OK)
    

class CustomerMakingAndWastageSettingsCreateView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    queryset = CustomerMakingAndWastageSettings.objects.all()
    serializer_class = CustomerMakingAndWastageSettingsMappingSerializer
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            
            if(CustomerMakingAndWastageSettings.objects.filter(id_product=request.data['id_product'], purity=request.data['purity']).exists()):
                CustomerMakingAndWastageSettings.objects.filter(id_product=request.data['id_product'],purity=request.data['purity']).delete()
            for data in request.data['mcva_settings']:
                data.update({"created_by": request.user.pk})
                serializer = CustomerMakingAndWastageSettingsMappingSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            print(request.data)
            print(request.data['mcva_settings'])
            return Response({"message":"Making & wastage settings created successfully."},status=status.HTTP_200_OK)


class SectionListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    # GET ALL SECTION
    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = Section.objects.filter(status=True)
            serializer = SectionSerializer(queryset, many=True)
            return Response(serializer.data)
        if 'product_section' in request.query_params:
            queryset = ProductSection.objects.all()
            serializer = ProductSectionSerializer(queryset, many=True)
            for data in serializer.data:
                section_name = Section.objects.get(id_section=data['id_section']).section_name
                data.update({"section_name":section_name})
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,SECTION_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,SECTION_COLUMN_LIST,request.query_params.get("path_name",''))
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_section'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': columns, 'actions': SECTION_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    # CREATE SECTION
    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = SectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SectionDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    # GET SECTION WITH ID

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if(obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Section status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = SectionSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
     # UPDATE SECTION

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = SectionSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["SECTION  can't be deleted, as it is already in Stock"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductCalculationTypeListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = ProductCalculationType.objects.all()
    serializer_class = ProductCalculationTypeSerializer

    def get(self, request, *args, **kwargs):
        queryset = ProductCalculationType.objects.all()
        serializer = ProductCalculationTypeSerializer(queryset, many=True)
        return Response(serializer.data)



class RepairDamageMasterListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = RepairDamageMaster.objects.all()
    serializer_class = RepairDamageMasterSerializer

    # GET ALL SUB DESIGN
    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = RepairDamageMaster.objects.filter(status=True)
            serializer = RepairDamageMasterSerializer(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,REPAIR_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_repair'], 'sno': index+1, 'is_active': data['status']})
        context = {'columns': REPAIR_COLUMN_LIST, 'actions': REPAIR_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    # CREATE SUB DESIGN
    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = RepairDamageMasterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Repair Damage Master Created Successfully."}, status=status.HTTP_201_CREATED)


class RepairDamageMasterView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = RepairDamageMaster.objects.all()
    serializer_class = RepairDamageMasterSerializer
    # GET SUB DESIGN WITH ID

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if ('changestatus' in request.query_params):
            if (obj.status == True):
                obj.status = False
            else:
                obj.status = True
            obj.updated_by = self.request.user
            obj.updated_on = datetime.now(tz=timezone.utc)
            obj.save()
            return Response({"Message": "Repair Damage Master status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = RepairDamageMasterSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
     # UPDATE SUB DESIGN

    def put(self, request, *args, **kwargs):
        queryset = self.get_object()
        request.data.update({"created_by": queryset.created_by.pk})
        serializer = RepairDamageMasterSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Repair Damage Master instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class InStockProductListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee | IsCustomerUser]
    serializer_class = ErpTaggingSerializer
    queryset = ErpTagging.objects.all()

    def post(self, request, *args, **kwargs):
        if "product" not in request.data or request.data['product']=="":
            return Response({"message":"Product is required."}, status=status.HTTP_400_BAD_REQUEST)
        if "customer" not in request.data or request.data['customer']=="":
            return Response({"message":"Customer is required."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            product=request.data['product']
            customer=request.data['customer']
            sub_design=request.data.get("sub_design",[])
            design=request.data.get("design",[])
            purchase_va_to = request.data.get('purchase_va_to',None)
            purchase_va_from = request.data.get('purchase_va_from',None)
            purchase_touch_to = request.data.get('purchase_touch_to',None)
            purchase_touch_from = request.data.get('purchase_touch_from',None)
            mc_to = request.data.get('mc_to',None)
            mc_from = request.data.get('mc_from',None)
            weight_to = request.data.get('weight_to',None)
            weight_from = request.data.get('weight_from',None)
            id_size = request.data.get('id_size',None)
            tag_status = request.data.get('status',None)
            response_data = []
            queryset = ErpTagging.objects.filter(tag_product_id=product).order_by("-tag_id")
            
            if len(sub_design) > 0 :
                sub_design = list(map(int, sub_design))
                queryset = queryset.filter(tag_sub_design_id__in = sub_design)
            if len(design) > 0 :
                design = list(map(int, design))
                queryset = queryset.filter(tag_design_id__in = design)
            if id_size:
                size = list(map(int, id_size))
                queryset = queryset.filter(size_id__in = size)
            if (weight_from and weight_to) :
                queryset = queryset.filter(tag_nwt__gte=weight_from)
                queryset = queryset.filter(tag_nwt__lte=weight_to)
            if (purchase_va_from and purchase_va_to) :
                queryset = queryset.filter(tag_purchase_va__gte=purchase_va_from)
                queryset = queryset.filter(tag_purchase_va__lte=purchase_va_to)
            if (purchase_touch_from and purchase_touch_to) :
                queryset = queryset.filter(tag_purchase_touch__gte=purchase_touch_from)
                queryset = queryset.filter(tag_purchase_touch__lte=purchase_touch_to)
            if (mc_from and mc_to) : 
                queryset = queryset.filter(tag_mc_value__gte=mc_from)
                queryset = queryset.filter(tag_mc_value__lte=mc_to)
            if (tag_status and tag_status is not None) :
                queryset = queryset.filter(tag_status=tag_status)
                
            paginator, page = pagination.paginate_queryset(queryset, request,no_of_records=10)
            serializer = ErpTaggingSerializer(page, many=True)

            for data in serializer.data:
                size_name = ''
                formatted_data = convert_tag_to_formated_data(data)
                productDetails = Product.objects.get(pro_id = data['tag_product_id'])
                cat_id = productDetails.cat_id
                stone_amount = other_metal_amount = other_charges_amount = 0
                is_wishlist = False
                is_cart = False
                if(CustomerWishlist.objects.filter(erp_tag =data['tag_id'],customer = customer)).exists():
                    is_wishlist = True
                if(CustomerCart.objects.filter(erp_tag =data['tag_id'],customer = customer)).exists():
                    is_cart = True

                if(ErpTaggingImages.objects.filter(erp_tag=data['tag_id']).exists()):
                    tag_image = ErpTaggingImages.objects.filter(erp_tag=data['tag_id'])
                    tag_image_seri = ErpTaggingImagesSerializer(tag_image,many=True, context={"request":request})
                    default = None
                    for detail in tag_image_seri.data:
                        detail.update({
                            'preview': detail['tag_image'],   
                            'default' :detail['is_default'],
                        })
                        if(detail['is_default'] == True):
                            default = detail['tag_image']

                    formatted_data['tag_images'] = tag_image_seri.data
                    formatted_data.update({"image":default, "image_text":data['product_name'][len(data['product_name'])-1]})
                else:
                    formatted_data['tag_images'] = []
                    formatted_data.update({"image":None, "image_text":data['product_name'][len(data['product_name'])-1]})
            
                cat_pur_rate = CategoryPurityRate.objects.filter(category = cat_id, purity = data['tag_purity_id']).first()
                for stones in data['stone_details']:
                    stone_amount += float(stones.get("stone_amount",0))
                for other in data['other_metal_details']:
                    other_metal_amount += float(other.get("other_metal_cost",0))
                for charge in data['charges_details']:
                    other_charges_amount += float(charge.get("charges_amount",0))
                if data['size']!=None:
                    size = Size.objects.get(id_size=data['size'])
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
                    "id_size":data['size'],
                    "size_name":size_name
                })
                
                related_items = []
                tag_set = ErpTagSet.objects.filter(tag_id=data['tag_id']).first()
                if tag_set:
                    tag_set_items = ErpTagSetItems.objects.filter(tag_set=tag_set)
                    for item in tag_set_items:
                        if item.tag:
                            related_serialized = ErpTaggingSerializer(item.tag, context={"request": request}).data
                            rel_formatted_data = convert_tag_to_formated_data(related_serialized)
                            # print(rel_formatted_data)
                            # related_items.append({
                            #    **related_serialized
                            # })
                            related_items.append({
                               "tag_id":related_serialized['tag_id'],
                                "tag_code":related_serialized['tag_code'],
                                "size_name": rel_formatted_data['size_name'] if rel_formatted_data.get('size_name') else "",
                                "product_name": related_serialized['product_name'],
                                "design_name": related_serialized['design_name'],
                                "purity_name": related_serialized['purity_name'],
                                "metal_name": related_serialized['metal_name'],
                                "pieces": rel_formatted_data['pieces'],
                                "gross_wt": rel_formatted_data['gross_wt'],
                                "net_wt": rel_formatted_data['net_wt'],
                                "less_wt": rel_formatted_data['less_wt'],
                                "stone_wt":rel_formatted_data['stone_wt'],
                                "dia_wt":rel_formatted_data['dia_wt'],
                                "other_metal_wt":rel_formatted_data['other_metal_wt'],
                                "pure_wt": rel_formatted_data['pure_wt'],
                                # "image":rel_formatted_data['tag_images'],
                                "id_product":rel_formatted_data['id_product'],
                                "id_design":rel_formatted_data['id_design'],
                                "id_purity":rel_formatted_data['id_purity'],
                                "id_size":rel_formatted_data['id_size'] if rel_formatted_data.get('id_size') else "",
                                "id_sub_design":rel_formatted_data['id_sub_design'],
                                "purchase_touch":rel_formatted_data['purchase_touch'],
                                "purchase_va":rel_formatted_data['purchase_va'],
                                "mc_value":rel_formatted_data['mc_value'],
                                "old_tag_code":formatted_data['old_tag_code'],
                                "tag_status":"Ready Stock" if related_serialized['tag_status'] == 1 else "Out of Stock",
                                "tag_status_id":related_serialized['tag_status'],
                                "color":"green" if related_serialized['tag_status'] == 1 else "red",
                                # "item_cost":rel_formatted_data['item_cost'],
                                "stone_details":related_serialized['stone_details'],
                                # "is_wishlist":is_wishlist,
                                # "is_cart":is_cart,
                            })

                else:
                    tag_set_item = ErpTagSetItems.objects.filter(tag_id=data['tag_id']).first()
                    if tag_set_item:
                        parent_set = tag_set_item.tag_set
                        if parent_set and parent_set.tag:
                            
                            parent_serialized = ErpTaggingSerializer(parent_set.tag, context={"request": request}).data
                            parent_formatted_data = convert_tag_to_formated_data(parent_serialized)
                            # related_items.append({
                            #     **parent_serialized
                            # })
                            related_items.append({
                               "tag_id":parent_serialized['tag_id'],
                                "tag_code":parent_serialized['tag_code'],
                                "size_name": parent_formatted_data['size_name'] if parent_formatted_data.get('size_name') else "",
                                "product_name": parent_serialized['product_name'],
                                "design_name": parent_serialized['design_name'],
                                "purity_name": parent_serialized['purity_name'],
                                "metal_name": parent_serialized['metal_name'],
                                "pieces": parent_formatted_data['pieces'],
                                "gross_wt": parent_formatted_data['gross_wt'],
                                "net_wt": parent_formatted_data['net_wt'],
                                "less_wt": parent_formatted_data['less_wt'],
                                "stone_wt":parent_formatted_data['stone_wt'],
                                "dia_wt":parent_formatted_data['dia_wt'],
                                "other_metal_wt":parent_formatted_data['other_metal_wt'],
                                "pure_wt": parent_formatted_data['pure_wt'],
                                # "image":parent_formatted_data['tag_images'],
                                "id_product":parent_formatted_data['id_product'],
                                "id_design":parent_formatted_data['id_design'],
                                "id_purity":parent_formatted_data['id_purity'],
                                "id_size":parent_formatted_data['id_size'] if parent_formatted_data.get('id_size') else "",
                                "id_sub_design":parent_formatted_data['id_sub_design'],
                                "purchase_touch":parent_formatted_data['purchase_touch'],
                                "purchase_va":parent_formatted_data['purchase_va'],
                                "mc_value":parent_formatted_data['mc_value'],
                                "old_tag_code":formatted_data['old_tag_code'],
                                "tag_status":"Ready Stock" if parent_serialized['tag_status'] == 1 else "Out of Stock",
                                "tag_status_id":parent_serialized['tag_status'],
                                "color":"green" if parent_serialized['tag_status'] == 1 else "red",
                                # "item_cost":parent_formatted_data['item_cost'],
                                "stone_details":parent_serialized['stone_details'],
                                # "is_wishlist":is_wishlist,
                                # "is_cart":is_cart,
                            })

                        
                        sibling_items = ErpTagSetItems.objects.filter(tag_set=parent_set).exclude(tag_id=data['tag_id'])
                        for sibling in sibling_items:
                            if sibling.tag and sibling.tag.pk != data['tag_id']:
                                sibling_serialized = ErpTaggingSerializer(sibling.tag, context={"request": request}).data
                                sibling_formatted_data = convert_tag_to_formated_data(parent_serialized)
                                # related_items.append({**sibling_serialized})
                                related_items.append({
                               "tag_id":sibling_serialized['tag_id'],
                                "tag_code":sibling_serialized['tag_code'],
                                "size_name": sibling_formatted_data['size_name'] if sibling_formatted_data.get('size_name') else "",
                                "product_name": sibling_serialized['product_name'],
                                "design_name": sibling_serialized['design_name'],
                                "purity_name": sibling_serialized['purity_name'],
                                "metal_name": sibling_serialized['metal_name'],
                                "pieces": sibling_formatted_data['pieces'],
                                "gross_wt": sibling_formatted_data['gross_wt'],
                                "net_wt": sibling_formatted_data['net_wt'],
                                "less_wt": sibling_formatted_data['less_wt'],
                                "stone_wt":sibling_formatted_data['stone_wt'],
                                "dia_wt":sibling_formatted_data['dia_wt'],
                                "other_metal_wt":sibling_formatted_data['other_metal_wt'],
                                "pure_wt": sibling_formatted_data['pure_wt'],
                                # "image":sibling_formatted_data['tag_images'],
                                "id_product":sibling_formatted_data['id_product'],
                                "id_design":sibling_formatted_data['id_design'],
                                "id_purity":sibling_formatted_data['id_purity'],
                                "id_size":sibling_formatted_data['id_size'] if sibling_formatted_data.get('id_size') else "",
                                "id_sub_design":sibling_formatted_data['id_sub_design'],
                                "purchase_touch":sibling_formatted_data['purchase_touch'],
                                "purchase_va":sibling_formatted_data['purchase_va'],
                                "mc_value":sibling_formatted_data['mc_value'],
                                "old_tag_code":formatted_data['old_tag_code'],
                                "tag_status":"Ready Stock" if sibling_serialized['tag_status'] == 1 else "Out of Stock",
                                "tag_status_id":sibling_serialized['tag_status'],
                                "color":"green" if sibling_serialized['tag_status'] == 1 else "red",
                                # "item_cost":sibling_formatted_data['item_cost'],
                                "stone_details":sibling_serialized['stone_details'],
                                # "is_wishlist":is_wishlist,
                                # "is_cart":is_cart,
                            })

                item_cost = calculate_item_cost(formatted_data)
                formatted_data.update({
                    **item_cost
                })
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
                    elif(ErpTaggingImages.objects.filter(erp_tag=data['tag_id']).exists()):
                        tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag_id'])
                        tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                        rel_item['tag_images'] = tag_image_serializer.data
                        if(ErpTaggingImages.objects.filter(erp_tag=data['tag_id'], is_default=True).exists()):
                            tag_def_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag_id'], is_default=True).first()
                            tag_def_image_serializer = ErpTaggingImagesSerializer(tag_def_image_query, context={'request':request})
                            rel_item['default_image'] = tag_def_image_serializer.data
                        else:
                            rel_item['default_image'] = tag_image_serializer.data[0]
                    else:
                        rel_item['tag_images'] = []
                        rel_item['default_image'] = None
                formatted_data["related_items"] = related_items
                response_data.append({
                    "tag_id":data['tag_id'],
                    "tag_code":data['tag_code'],
                    "size_name": formatted_data['size_name'],
                    "product_name": data['product_name'],
                    "design_name": data['design_name'],
                    "purity_name": data['purity_name'],
                    "metal_name": data['metal_name'],
                    "pieces": formatted_data['pieces'],
                    "gross_wt": formatted_data['gross_wt'],
                    "net_wt": formatted_data['net_wt'],
                    "less_wt": formatted_data['less_wt'],
                    "stone_wt":formatted_data['stone_wt'],
                    "dia_wt":formatted_data['dia_wt'],
                    "other_metal_wt":formatted_data['other_metal_wt'],
                    "pure_wt": formatted_data['pure_wt'],
                    "image":formatted_data['tag_images'],
                    "id_product":formatted_data['id_product'],
                    "id_design":formatted_data['id_design'],
                    "id_purity":formatted_data['id_purity'],
                    "id_size":formatted_data['id_size'],
                    "id_sub_design":formatted_data['id_sub_design'],
                    "purchase_touch":formatted_data['purchase_touch'],
                    "purchase_va":formatted_data['purchase_va'],
                    "mc_value":formatted_data['mc_value'],
                    "old_tag_code":formatted_data['old_tag_code'],
                    "tag_status":"Ready Stock" if data['tag_status'] == 1 else "Out of Stock",
                    "tag_status_id":data['tag_status'],
                    "color":"green" if data['tag_status'] == 1 else "red",
                    "item_cost":formatted_data['item_cost'],
                    "stone_details":data['stone_details'],
                    "is_wishlist":is_wishlist,
                    "is_cart":is_cart,
                    "related_items": formatted_data["related_items"],
                })
            
                # Use the common pagination method
            if len(response_data) > 0:
                if(int(request.query_params['page']) > paginator.num_pages):
                    return Response({
                    "data": response_data,
                    "message":"No record Found"
                    }, status=status.HTTP_200_OK)
                
                else:
                    return Response({
                        "data": response_data,
                        'page_count':paginator.count,
                        'total_pages': paginator.num_pages,
                        'current_page': page.number
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "data": response_data,
                    "message":"No record Found"
                }, status=status.HTTP_200_OK)
    



class CustomerEnquiryListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = CustomerEnquiry.objects.all()
    serializer_class = CustomerEnquirySerializer

    # GET ALL SUB DESIGN
    def get(self, request, *args, **kwargs):
        if 'active' in request.query_params:
            queryset = CustomerEnquiry.objects.filter(status=True)
            serializer = CustomerEnquiry(queryset, many=True)
            return Response(serializer.data)
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,REPAIR_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_query'], 'sno': index+1})
        context = {'columns': REPAIR_COLUMN_LIST, 'actions': REPAIR_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)

    # CREATE SUB DESIGN
    def post(self, request, *args, **kwargs):
        request.data.update({"created_by": request.user.pk})
        serializer = CustomerEnquirySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Customer Enquiry Created Successfully."}, status=status.HTTP_201_CREATED)
    

class NewArrivalsProductListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee | IsCustomerUser]
    serializer_class = ErpTaggingSerializer
    queryset = ErpTagging.objects.all()

    def post(self, request, *args, **kwargs):
        days = int(RetailSettings.objects.get(name='new_arrival_days').value)
        from_date = datetime.now().date() - timedelta(days=days)
        
        sub_design=request.data.get("sub_design",[])
        design=request.data.get("design",[])
        purchase_va_to = request.data.get('purchase_va_to',None)
        purchase_va_from = request.data.get('purchase_va_from',None)
        purchase_touch_to = request.data.get('purchase_touch_to',None)
        purchase_touch_from = request.data.get('purchase_touch_from',None)
        mc_to = request.data.get('mc_to',None)
        mc_from = request.data.get('mc_from',None)
        weight_to = request.data.get('weight_to',None)
        weight_from = request.data.get('weight_from',None)
        id_size = request.data.get('id_size',None)
        tag_status = request.data.get('status',None)
        
        response_data = []
        queryset = ErpTagging.objects.filter(tag_date__gte=from_date).order_by("-tag_id")
        
        if len(sub_design) > 0 :
            sub_design = list(map(int, sub_design))
            queryset = queryset.filter(tag_sub_design_id__in = sub_design)
        if len(design) > 0 :
            design = list(map(int, design))
            queryset = queryset.filter(tag_design_id__in = design)
        if id_size:
            size = list(map(int, id_size))
            queryset = queryset.filter(size_id__in = size)
        if (weight_from and weight_to) :
            queryset = queryset.filter(tag_nwt__gte=weight_from)
            queryset = queryset.filter(tag_nwt__lte=weight_to)
        if (purchase_va_from and purchase_va_to) :
            queryset = queryset.filter(tag_purchase_va__gte=purchase_va_from)
            queryset = queryset.filter(tag_purchase_va__lte=purchase_va_to)
        if (purchase_touch_from and purchase_touch_to) :
            queryset = queryset.filter(tag_purchase_touch__gte=purchase_touch_from)
            queryset = queryset.filter(tag_purchase_touch__lte=purchase_touch_to)
        if (mc_from and mc_to) : 
            queryset = queryset.filter(tag_mc_value__gte=mc_from)
            queryset = queryset.filter(tag_mc_value__lte=mc_to)
        if (tag_status and tag_status is not None) :
            queryset = queryset.filter(tag_status=tag_status)
                
        paginator, page = pagination.paginate_queryset(queryset, request,no_of_records=10)
        serializer = ErpTaggingSerializer(page, many=True)
        for data in serializer.data:
            size_name = ''
            formatted_data = convert_tag_to_formated_data(data)
            productDetails = Product.objects.get(pro_id = data['tag_product_id'])
            cat_id = productDetails.cat_id
            stone_amount = other_metal_amount = other_charges_amount = 0
            is_wishlist = False
            is_cart = False
            
            if(ErpTaggingImages.objects.filter(erp_tag=data['tag_id']).exists()):
                tag_image = ErpTaggingImages.objects.filter(erp_tag=data['tag_id'])
                tag_image_seri = ErpTaggingImagesSerializer(tag_image,many=True, context={"request":request})
                default = None
                for detail in tag_image_seri.data:
                    detail.update({
                        'preview': detail['tag_image'],   
                        'default' :detail['is_default'],
                    })
                    if(detail['is_default'] == True):
                        default = detail['tag_image']
                formatted_data['tag_images'] = tag_image_seri.data
                formatted_data.update({"image":default, "image_text":data['product_name'][len(data['product_name'])-1]})
            else:
                formatted_data['tag_images'] = []
                formatted_data.update({"image":None, "image_text":data['product_name'][len(data['product_name'])-1]})
        
            cat_pur_rate = CategoryPurityRate.objects.filter(category = cat_id, purity = data['tag_purity_id']).first()
            for stones in data['stone_details']:
                stone_amount += float(stones.get("stone_amount",0))
            for other in data['other_metal_details']:
                other_metal_amount += float(other.get("other_metal_cost",0))
            for charge in data['charges_details']:
                other_charges_amount += float(charge.get("charges_amount",0))
            if data['size']!=None:
                size = Size.objects.get(id_size=data['size'])
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
                "id_size":data['size'],
                "size_name":size_name
            })
            
            related_items = []
            tag_set = ErpTagSet.objects.filter(tag_id=data['tag_id']).first()
            if tag_set:
                tag_set_items = ErpTagSetItems.objects.filter(tag_set=tag_set)
                for item in tag_set_items:
                    if item.tag:
                        related_serialized = ErpTaggingSerializer(item.tag, context={"request": request}).data
                        rel_formatted_data = convert_tag_to_formated_data(related_serialized)
                        # print(rel_formatted_data)
                        # related_items.append({
                        #    **related_serialized
                        # })
                        related_items.append({
                           "tag_id":related_serialized['tag_id'],
                            "tag_code":related_serialized['tag_code'],
                            "size_name": rel_formatted_data['size_name'] if rel_formatted_data.get('size_name') else "",
                            "product_name": related_serialized['product_name'],
                            "design_name": related_serialized['design_name'],
                            "purity_name": related_serialized['purity_name'],
                            "metal_name": related_serialized['metal_name'],
                            "pieces": rel_formatted_data['pieces'],
                            "gross_wt": rel_formatted_data['gross_wt'],
                            "net_wt": rel_formatted_data['net_wt'],
                            "less_wt": rel_formatted_data['less_wt'],
                            "stone_wt":rel_formatted_data['stone_wt'],
                            "dia_wt":rel_formatted_data['dia_wt'],
                            "other_metal_wt":rel_formatted_data['other_metal_wt'],
                            "pure_wt": rel_formatted_data['pure_wt'],
                            # "image":rel_formatted_data['tag_images'],
                            "id_product":rel_formatted_data['id_product'],
                            "id_design":rel_formatted_data['id_design'],
                            "id_purity":rel_formatted_data['id_purity'],
                            "id_size":rel_formatted_data['id_size'] if rel_formatted_data.get('id_size') else "",
                            "id_sub_design":rel_formatted_data['id_sub_design'],
                            "purchase_touch":rel_formatted_data['purchase_touch'],
                            "purchase_va":rel_formatted_data['purchase_va'],
                            "mc_value":rel_formatted_data['mc_value'],
                            "old_tag_code":rel_formatted_data['old_tag_code'],
                            "tag_status":"Ready Stock" if related_serialized['tag_status'] == 1 else "Out of Stock",
                            "tag_status_id":related_serialized['tag_status'],
                            "color":"green" if related_serialized['tag_status'] == 1 else "red",
                            # "item_cost":rel_formatted_data['item_cost'],
                            "stone_details":related_serialized['stone_details'],
                            # "is_wishlist":is_wishlist,
                            # "is_cart":is_cart,
                        })
            else:
                tag_set_item = ErpTagSetItems.objects.filter(tag_id=data['tag_id']).first()
                if tag_set_item:
                    parent_set = tag_set_item.tag_set
                    if parent_set and parent_set.tag:
                        
                        parent_serialized = ErpTaggingSerializer(parent_set.tag, context={"request": request}).data
                        parent_formatted_data = convert_tag_to_formated_data(parent_serialized)
                        # related_items.append({
                        #     **parent_serialized
                        # })
                        related_items.append({
                           "tag_id":parent_serialized['tag_id'],
                            "tag_code":parent_serialized['tag_code'],
                            "size_name": parent_formatted_data['size_name'] if parent_formatted_data.get('size_name') else "",
                            "product_name": parent_serialized['product_name'],
                            "design_name": parent_serialized['design_name'],
                            "purity_name": parent_serialized['purity_name'],
                            "metal_name": parent_serialized['metal_name'],
                            "pieces": parent_formatted_data['pieces'],
                            "gross_wt": parent_formatted_data['gross_wt'],
                            "net_wt": parent_formatted_data['net_wt'],
                            "less_wt": parent_formatted_data['less_wt'],
                            "stone_wt":parent_formatted_data['stone_wt'],
                            "dia_wt":parent_formatted_data['dia_wt'],
                            "other_metal_wt":parent_formatted_data['other_metal_wt'],
                            "pure_wt": parent_formatted_data['pure_wt'],
                            # "image":parent_formatted_data['tag_images'],
                            "id_product":parent_formatted_data['id_product'],
                            "id_design":parent_formatted_data['id_design'],
                            "id_purity":parent_formatted_data['id_purity'],
                            "id_size":parent_formatted_data['id_size'] if parent_formatted_data.get('id_size') else "",
                            "id_sub_design":parent_formatted_data['id_sub_design'],
                            "purchase_touch":parent_formatted_data['purchase_touch'],
                            "purchase_va":parent_formatted_data['purchase_va'],
                            "mc_value":parent_formatted_data['mc_value'],
                            "old_tag_code":parent_formatted_data['old_tag_code'],
                            "tag_status":"Ready Stock" if parent_serialized['tag_status'] == 1 else "Out of Stock",
                            "tag_status_id":parent_serialized['tag_status'],
                            "color":"green" if parent_serialized['tag_status'] == 1 else "red",
                            # "item_cost":parent_formatted_data['item_cost'],
                            "stone_details":parent_serialized['stone_details'],
                            # "is_wishlist":is_wishlist,
                            # "is_cart":is_cart,
                        })
                    
                    sibling_items = ErpTagSetItems.objects.filter(tag_set=parent_set).exclude(tag_id=data['tag_id'])
                    for sibling in sibling_items:
                        if sibling.tag and sibling.tag.pk != data['tag_id']:
                            sibling_serialized = ErpTaggingSerializer(sibling.tag, context={"request": request}).data
                            sibling_formatted_data = convert_tag_to_formated_data(parent_serialized)
                            # related_items.append({**sibling_serialized})
                            related_items.append({
                           "tag_id":sibling_serialized['tag_id'],
                            "tag_code":sibling_serialized['tag_code'],
                            "size_name": sibling_formatted_data['size_name'] if sibling_formatted_data.get('size_name') else "",
                            "product_name": sibling_serialized['product_name'],
                            "design_name": sibling_serialized['design_name'],
                            "purity_name": sibling_serialized['purity_name'],
                            "metal_name": sibling_serialized['metal_name'],
                            "pieces": sibling_formatted_data['pieces'],
                            "gross_wt": sibling_formatted_data['gross_wt'],
                            "net_wt": sibling_formatted_data['net_wt'],
                            "less_wt": sibling_formatted_data['less_wt'],
                            "stone_wt":sibling_formatted_data['stone_wt'],
                            "dia_wt":sibling_formatted_data['dia_wt'],
                            "other_metal_wt":sibling_formatted_data['other_metal_wt'],
                            "pure_wt": sibling_formatted_data['pure_wt'],
                            # "image":sibling_formatted_data['tag_images'],
                            "id_product":sibling_formatted_data['id_product'],
                            "id_design":sibling_formatted_data['id_design'],
                            "id_purity":sibling_formatted_data['id_purity'],
                            "id_size":sibling_formatted_data['id_size'] if sibling_formatted_data.get('id_size') else "",
                            "id_sub_design":sibling_formatted_data['id_sub_design'],
                            "purchase_touch":sibling_formatted_data['purchase_touch'],
                            "purchase_va":sibling_formatted_data['purchase_va'],
                            "mc_value":sibling_formatted_data['mc_value'],
                            "old_tag_code":sibling_formatted_data['old_tag_code'],
                            "tag_status":"Ready Stock" if sibling_serialized['tag_status'] == 1 else "Out of Stock",
                            "tag_status_id":sibling_serialized['tag_status'],
                            "color":"green" if sibling_serialized['tag_status'] == 1 else "red",
                            # "item_cost":sibling_formatted_data['item_cost'],
                            "stone_details":sibling_serialized['stone_details'],
                            # "is_wishlist":is_wishlist,
                            # "is_cart":is_cart,
                        })
            item_cost = calculate_item_cost(formatted_data)
            formatted_data.update({
                **item_cost
            })
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
                elif(ErpTaggingImages.objects.filter(erp_tag=data['tag_id']).exists()):
                    tag_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag_id'])
                    tag_image_serializer = ErpTaggingImagesSerializer(tag_image_query, many=True, context={'request':request})
                    rel_item['tag_images'] = tag_image_serializer.data
                    if(ErpTaggingImages.objects.filter(erp_tag=data['tag_id'], is_default=True).exists()):
                        tag_def_image_query = ErpTaggingImages.objects.filter(erp_tag=data['tag_id'], is_default=True).first()
                        tag_def_image_serializer = ErpTaggingImagesSerializer(tag_def_image_query, context={'request':request})
                        rel_item['default_image'] = tag_def_image_serializer.data
                    else:
                        rel_item['default_image'] = tag_image_serializer.data[0]
                else:
                    rel_item['tag_images'] = []
                    rel_item['default_image'] = None
            formatted_data["related_items"] = related_items
            response_data.append({
                "tag_id":data['tag_id'],
                "tag_code":data['tag_code'],
                "size_name": formatted_data['size_name'],
                "product_name": data['product_name'],
                "design_name": data['design_name'],
                "purity_name": data['purity_name'],
                "metal_name": data['metal_name'],
                "pieces": formatted_data['pieces'],
                "gross_wt": formatted_data['gross_wt'],
                "net_wt": formatted_data['net_wt'],
                "less_wt": formatted_data['less_wt'],
                "stone_wt":formatted_data['stone_wt'],
                "dia_wt":formatted_data['dia_wt'],
                "other_metal_wt":formatted_data['other_metal_wt'],
                "pure_wt": formatted_data['pure_wt'],
                "image":formatted_data['tag_images'],
                "id_product":formatted_data['id_product'],
                "id_design":formatted_data['id_design'],
                "id_purity":formatted_data['id_purity'],
                "id_size":formatted_data['id_size'],
                "id_sub_design":formatted_data['id_sub_design'],
                "purchase_touch":formatted_data['purchase_touch'],
                "purchase_va":formatted_data['purchase_va'],
                "mc_value":formatted_data['mc_value'],
                "old_tag_code":formatted_data['old_tag_code'],
                "tag_status":"Ready Stock" if data['tag_status'] == 1 else "Out of Stock",
                "tag_status_id":data['tag_status'],
                "color":"green" if data['tag_status'] == 1 else "red",
                "item_cost":formatted_data['item_cost'],
                "stone_details":data['stone_details'],
                "is_wishlist":is_wishlist,
                "is_cart":is_cart,
                "related_items": formatted_data["related_items"],
            })
        
            # Use the common pagination method
        if len(response_data) > 0:
            if(int(request.query_params['page']) > paginator.num_pages):
                return Response({
                "data": response_data,
                "message":"No record Found"
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    "data": response_data,
                    'page_count':paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page.number
                }, status=status.HTTP_200_OK)
        else:
            return Response({
                "data": response_data,
                "message":"No record Found"
            }, status=status.HTTP_200_OK)
            
class CustomerEnquiryProducts(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    
    def post(self, request, *args, **kwargs):
        metal = request.data['metal']
        queryset = Product.objects.filter(show_in_enquiry_form=True, id_metal=metal)
        serializer = ProductSerializer(queryset, many=True)
        output = []
        for data in serializer.data:
            instance = {}
            instance.update({
                "label":data['product_name'],
                "value":data['pro_id']
            })
            if instance not in output:
                output.append(instance)
        return Response({"data": output}, status=status.HTTP_200_OK)
    
class CustomerEnquiryDesignsAndWeightOfProducts(generics.GenericAPIView):
    permission_classes = [IsEmployeeOrCustomer]
    
    def post(self, request, *args, **kwargs):
        product = request.data['product']
        if not product:
            return Response({"message": "Product is required"}, status=status.HTTP_400_BAD_REQUEST)
        design_op = []
        size_op = []
        weight_range_op = []
        prod_map_queryset = ProductMapping.objects.filter(id_product=product)
        prod_map_serializeer = ProductMappingSerializer(prod_map_queryset, many=True)
        for prod_data in prod_map_serializeer.data:
            design_obj = Design.objects.filter(id_design=prod_data['id_design']).first()
            if design_obj.show_in_enquiry_form == True:
                design_inst = {}
                design_inst.update({
                    "label": design_obj.design_name,
                    "value": design_obj.pk
                })
                if design_inst not in design_op:
                    design_op.append(design_inst)
        size_queryset = Size.objects.filter(id_product=product)
        size_serializer = SizeSerializer(size_queryset, many=True)
        for size_data in size_serializer.data:
            size_inst = {}
            size_inst.update({
                "label": size_data['name'],
                "value": size_data['id_size']
            })
            if size_inst not in size_op:
                size_op.append(size_inst)
        weight_range_query = WeightRange.objects.filter(id_product=product)
        weight_range_serializer = WeightRangeSerializer(weight_range_query, many=True)
        for weight_data in weight_range_serializer.data:
            weight_inst = {}
            weight_inst.update({
                "label": weight_data['weight_range_name'],
                # "label": weight_data['from_weight'] + " - " + weight_data['to_weight'],
                "value": weight_data['id_weight_range']
            })
            if weight_inst not in weight_range_op:
                weight_range_op.append(weight_inst)
        data = {
            "designs": design_op if len(design_op) > 0 else [],
            "sizes": size_op if len(size_op) > 0 else [],
            "weight_ranges": weight_range_op if len(weight_range_op) > 0 else []
        }
        return Response({"data": data}, status=status.HTTP_200_OK)