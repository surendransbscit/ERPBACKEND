from django.shortcuts import render
from django.db import IntegrityError, transaction
from django.http import HttpResponse, request, Http404
from rest_framework import generics, permissions, status
from django.utils.timezone import utc
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone
from django.forms.models import model_to_dict
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee,isSuperuser,IsSuperuserOrEmployee
from knox.models import AuthToken
from django.db.models import Q, ProtectedError
from datetime import datetime, timedelta
from django.db.models import Count,OuterRef, Subquery
from django.core.exceptions import ValidationError
from core.views  import get_reports_columns_template


from utilities.pagination_mixin import PaginationMixin
from .models import (Scheme, PaymentSettings,SchemePaymentFormula, SchemeBenefitSettings,SchemeDigiGoldInterestSettings,
                     SchemeGiftSettings)
from customers.models import Customers
from managescheme.models import SchemeAccount
from accounts import serializers
from .serializers import (SchemeSerializer,PaymentSettingsSerializer,SchemePaymentFormulaSerializer, SchemeBenefitSettingsSerializer,
                          SchemeDigiGoldInterestSettingsSerializer, SchemeGiftSettingsSerializer)
from .constants import (condition,limit_by_arr,denom_type_arr,discount_type_arr,payment_chance_type_arr,SCHEME_COLUMN_LIST, ACTION_LIST)
# Create your views here.
pagination = PaginationMixin()  # Apply pagination


class SchemeBenefitSettingsListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = SchemeBenefitSettings.objects.all()
    serializer_class = SchemeBenefitSettingsSerializer

    def get(self, request, *args, **kwargs):
        subquery = SchemeBenefitSettings.objects.filter(scheme=OuterRef('scheme')).order_by('id').values('id')[:1]

        queryset = SchemeBenefitSettings.objects.annotate(first_id=Subquery(subquery), count=Count('scheme')).filter(id=OuterRef('first_id'))
        paginator, page = pagination.paginate_queryset(queryset, request,None, WEIGHT_RANGE_COLUMN_LIST)
        serializer = SchemeBenefitSettingsSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_product'], 'sno': index+1})
        context = {'columns': WEIGHT_RANGE_COLUMN_LIST, 'actions': WEIGHT_RANGE_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)
    
    def validate_benefit_settings(self, installment_from, installment_to, scheme):
        overlaps = SchemeBenefitSettings.objects.filter(scheme=scheme).filter(Q(installment_from__lt=installment_to) & Q(installment_to__gt=installment_from))
        if overlaps.exists():
            raise ValidationError('The weight range overlaps with an existing range for the same product.')

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            scheme_benefit_datas =[]
            if(SchemeBenefitSettings.objects.filter(scheme=request.data['scheme']).exists()):
                    SchemeBenefitSettings.objects.filter(scheme=request.data['scheme']).delete()
            for data in request.data['scheme_benefit_settings']:
                installment_from = float(data['installment_from'])
                installment_to = float(data['installment_to'])
                    
                try:
                    self.validate_benefit_settings(installment_from, installment_to, data['scheme'])
                    scheme_benefit_datas.append(data)
                    # data.update({"created_by": request.user.pk})
                    serializer = SchemeBenefitSettingsSerializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                except ValidationError as e:
                    del data
                    # return Response({'error': str(e)}, status=400)

            if(len(scheme_benefit_datas) == 0):
                return Response({"message":"The weight range overlaps with an existing range for the same product."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message":"Weight ranges created successfully."}, status=status.HTTP_201_CREATED)


class SchemeBenefitSettingsDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = SchemeBenefitSettings.objects.all()
    serializer_class = SchemeBenefitSettingsSerializer

    def get(self, request, *args, **kwargs):
        output=[]
        queryset = SchemeBenefitSettings.objects.filter(scheme=kwargs['pk'])
        serializer = SchemeBenefitSettingsSerializer(queryset, many=True)
        for data in serializer.data:
            if data not in output:
                output.append(data)
        instance = {"scheme_benefit_settings":output}
        return Response(instance, status=status.HTTP_200_OK)

    # def put(self, request, *args, **kwargs):
    #     queryset = self.get_object()
    #     request.data.update({"created_by": queryset.created_by.pk})
    #     serializer = WeightRangeSerializer(queryset, data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save(updated_by=self.request.user,
    #                     updated_on=datetime.now(tz=timezone.utc))
    #     return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Weight Range instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)

class SchemePaymentFormulaList(generics.ListCreateAPIView):
    permission_classes=[IsAdminUser]
    queryset = SchemePaymentFormula.objects.all()
    serializer_class = SchemePaymentFormulaSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = SchemePaymentFormula.objects.all()
        serializer = SchemePaymentFormulaSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerMultiSchemeListView(generics.ListCreateAPIView):
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer
    
    def post(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')

        if not customer_id:
            return Response({"error": "Customer ID is missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            customer = Customers.objects.get(id_customer=customer_id)
        except Customers.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        queryset = Scheme.objects.filter(status=1)
        serializer = SchemeSerializer(queryset, many=True)

        filtered_schemes = []
        for data in serializer.data:
            if data['allow_join_multi_acc'] == False:
                scheme_acc_obj = SchemeAccount.objects.filter(
                    acc_scheme_id=data['scheme_id'], 
                    id_customer=customer.pk
                )
                if scheme_acc_obj.exists():
                    continue  # Skip this scheme
        
            if PaymentSettings.objects.filter(scheme=data['scheme_id']).exists():
                minimum_payable = PaymentSettings.objects.filter(scheme=data['scheme_id']).first()
                if minimum_payable.min_formula == 1:
                    data.update({"minimum_amount": float(minimum_payable.min_parameter)})
                else:
                    data.update({"minimum_amount":0})

            data.update({
                "name": data['scheme_name'],
                "scheme_vis": int(data['scheme_vis'])
            })
            filtered_schemes.append(data)
        return Response({"data": filtered_schemes}, status=status.HTTP_200_OK)


class SchemeListView(generics.ListCreateAPIView):
    #permission_classes=[permissions.AllowAny]
    # permission_classes = [IsEmployee]
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer


    def validate_benefit_settings(self, installment_from, installment_to, scheme):
        overlaps = SchemeBenefitSettings.objects.filter(scheme=scheme).filter(Q(installment_from__lt=installment_to) & Q(installment_to__gt=installment_from))
        if overlaps.exists():
            raise ValidationError('The weight range overlaps with an existing range for the same product.')

    def get(self, request, *args, **kwargs):
        if((request.user.is_adminuser) | (request.user and request.user.is_customer)):
            print(request.query_params)
            if 'status' in request.query_params:
                queryset = Scheme.objects.filter(status=1)
                serializer = SchemeSerializer(queryset, many=True)
                for data in serializer.data:
                    if(PaymentSettings.objects.filter(scheme=data['scheme_id']).exists()):
                        minimum_payable = PaymentSettings.objects.filter(scheme=data['scheme_id']).first()
                        if minimum_payable.min_formula.pk == 1:
                            data.update({"minimum_amount": float(minimum_payable.min_parameter)})
                        else:
                            data.update({"minimum_amount":0})
                    data.update({"name":data['scheme_name'],"scheme_vis":int(data['scheme_vis'])})
                return Response({"data":serializer.data},status=status.HTTP_200_OK)

            paginator, page = pagination.paginate_queryset(self.queryset, request,None,SCHEME_COLUMN_LIST)
            columns = get_reports_columns_template(request.user.pk,SCHEME_COLUMN_LIST,request.query_params.get("path_name",''))
            serializer = self.serializer_class(page, many=True)
            SCHEME_ACTION_LIST = ACTION_LIST.copy()
            SCHEME_ACTION_LIST['is_edit_req'] = True
            for index,data in enumerate(serializer.data):
                data.update({"sno":index+1,"pk_id":data['scheme_id'],"is_active":data['status'], "name":data['scheme_name'],"scheme_type":'Amount' if data['scheme_type']==0 else 'Weight' })
            context={'columns':columns,'actions':SCHEME_ACTION_LIST,'page_count':paginator.count,'total_pages': paginator.num_pages,'current_page': page.number}
            return pagination.paginated_response(serializer.data,context) 
    
    def post(self, request, format=None):
        if(request.user.is_adminuser):
            try:
                with transaction.atomic():
                    payment_settings = request.data['payment_settings']
                    scheme_benefit_settings = request.data['scheme_benefit_settings']
                    digi_interest_settings = request.data['digi_interest']
                    gift_settings = request.data['gift_settings']
                    del request.data['payment_settings']
                    del request.data['scheme_benefit_settings']
                    del request.data['gift_settings']
                    request.data.update({"created_by": request.user.id})
                    if(request.data['scheme_type']==2):
                        request.data.update({"convert_to_weight": True})
                    if(request.data['scheme_type']==0):
                        request.data.update({"convert_to_weight": False})
                    serializer = SchemeSerializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    if(digi_interest_settings and int(request.data['scheme_type']) == 2):
                        for sett in digi_interest_settings:
                            sett.update({"from_day" : sett["from_days"],"to_day" : sett["to_days"],"scheme" : serializer.data['scheme_id']})
                            serializer_digi = SchemeDigiGoldInterestSettingsSerializer(data=sett)
                            serializer_digi.is_valid(raise_exception=True)
                            serializer_digi.save()
                    for data in payment_settings:
                        data.update({"scheme": serializer.data['scheme_id']})
                        psy_set_serializer = PaymentSettingsSerializer(data=data)
                        psy_set_serializer.is_valid(raise_exception=True)
                        psy_set_serializer.save()
                    for gift_set in gift_settings:
                        gift_set.update({"scheme": serializer.data['scheme_id']})
                        gift_set_serializer = SchemeGiftSettingsSerializer(data=gift_set)
                        gift_set_serializer.is_valid(raise_exception=True)
                        gift_set_serializer.save()
                    non_overlapping_data = []
                    for benefit_data in scheme_benefit_settings:
                        installment_from = float(benefit_data['installment_from'])
                        installment_to = float(benefit_data['installment_to'])
                        benefit_data.update({"scheme": serializer.data['scheme_id']})
                        overlapping_exists = SchemeBenefitSettings.objects.filter(
                                    Q(installment_from__lte=installment_to) & Q(installment_to__gte=installment_from),
                                    scheme=serializer.data['scheme_id']
                                    ).exclude(id=benefit_data.get('id')).exists()
                        if overlapping_exists:
                            continue
                        benefit_serializer = SchemeBenefitSettingsSerializer(data=benefit_data)
                        benefit_serializer.is_valid(raise_exception=True)
                        non_overlapping_data.append(benefit_serializer.save())
                        # try:
                        #     self.validate_benefit_settings(installment_from, installment_to, serializer.data['scheme_id'])
                        #     benefit_data.update({"scheme": serializer.data['scheme_id']})
                        #     serializer = SchemeBenefitSettingsSerializer(data=benefit_data)
                        #     serializer.is_valid(raise_exception=True)
                        #     serializer.save()
                        # except ValidationError as e:
                        #     del data
                    return Response({"scheme": serializer.data},status=status.HTTP_201_CREATED)
            except Exception as e:
                # Handle the exception
                raise(e)
                # return Response({f"An error occurred: {str(e)}"},status=status.HTTP_400_BAD_REQUEST)
    
class SchemeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer
    
    def validate_benefit_settings(self, installment_from, installment_to, scheme):
        overlaps = SchemeBenefitSettings.objects.filter(scheme=scheme).filter(Q(installment_from__lt=installment_to) & Q(installment_to__gt=installment_from))
        if overlaps.exists():
            raise ValidationError('The weight range overlaps with an existing range for the same product.')

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
            return Response({"Message": "Scheme status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = SchemeSerializer(obj)
        output = serializer.data
        pay_set = PaymentSettings.objects.filter(scheme=obj.scheme_id)
        payment_serializer = PaymentSettingsSerializer(pay_set, many=True)
        digi_intrest = SchemeDigiGoldInterestSettings.objects.filter(scheme=obj.scheme_id)
        digi_intrest_serializer = SchemeDigiGoldInterestSettingsSerializer(digi_intrest, many=True)
        benefit_set = SchemeBenefitSettings.objects.filter(scheme=obj.scheme_id)
        benefit_serializer = SchemeBenefitSettingsSerializer(benefit_set, many=True)
        payment_settings = []
        digi_intrest_settings = []
        for data in payment_serializer.data:
            instance = {}
            instance.update(data)
            
            scheme_payment_min_formula = SchemePaymentFormula.objects.get(id=data['min_formula'])
            scheme_payment_max_formula = SchemePaymentFormula.objects.get(id=data['min_formula'])
            instance.update({"min_formula_value":scheme_payment_min_formula.name}) 
            instance.update({"max_formula_value":scheme_payment_max_formula.name}) 
            
            for each_cond in condition:
                if each_cond['value'] == data['min_condition']:
                    instance.update({"min_condition_value":each_cond['label']})
                if each_cond['value'] == data['max_condition']:
                    instance.update({"max_condition_value":each_cond['label']})
                    
            for limit_by in limit_by_arr:
                if limit_by['value'] == data['limit_by']:
                    instance.update({"limit_by_value":limit_by['label']})
                    
            for each_denom_type in denom_type_arr:
                if each_denom_type['value'] == data['denom_type']:
                    instance.update({"denom_type_value":each_denom_type['label']})
                    
            for each_discount_type in discount_type_arr:
                if each_discount_type['value'] == data['discount_type']:
                    instance.update({"discount_type_value":each_discount_type['label']})
                    
            for payment_chance in payment_chance_type_arr:
                if payment_chance['value'] == data['payment_chance_type']:
                    instance.update({"payment_chance_type_value":payment_chance['label']})
                
                    
            if instance not in payment_settings:
                payment_settings.append(instance)
        
        for digi in digi_intrest_serializer.data:
            digi_instance = {}
            digi_instance.update({'from_days': digi['from_day'], 'to_days':digi['to_day'], 'interest_percentage':digi['interest_percentage']})
            
            if digi_instance not in digi_intrest_settings:
                digi_intrest_settings.append(digi_instance)
            
        if(SchemeGiftSettings.objects.filter(scheme=obj.scheme_id).exists()):
            gift_setting = SchemeGiftSettings.objects.filter(scheme=obj.scheme_id)
            gift_setting_serializer = SchemeGiftSettingsSerializer(gift_setting, many=True)
            output.update({"gift_settings":gift_setting_serializer.data})
        else:
            output.update({"gift_settings":[]})
        output.update({"created_by": obj.created_by.username,
                       "updated_by": obj.updated_by.username if obj.updated_by != None else None,
                       "payment_settings":payment_settings,
                       "digi_interest":digi_intrest_settings,
                       "scheme_benefit_settings":benefit_serializer.data})
        return Response(output, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            payment_settings = request.data['payment_settings']
            digi_interest_settings = request.data['digi_interest']
            scheme_benefit_settings = request.data['scheme_benefit_settings']
            gift_settings = request.data['gift_settings']
            del request.data['payment_settings']
            del request.data['scheme_benefit_settings']
            del request.data['gift_settings']
            queryset = self.get_object()
            request.data.update({"created_by": queryset.created_by.id})
            if(request.data['scheme_type']==2):
                request.data.update({"convert_to_weight": True})
            if(request.data['scheme_type']==0):
                request.data.update({"convert_to_weight": False})
            serializer = SchemeSerializer(queryset, data=request.data)
            serializer.is_valid(raise_exception=True)
            if PaymentSettings.objects.filter(scheme=queryset.scheme_id).exists():
                PaymentSettings.objects.filter(scheme=queryset.scheme_id).delete()
            if SchemeDigiGoldInterestSettings.objects.filter(scheme=queryset.scheme_id).exists():
                SchemeDigiGoldInterestSettings.objects.filter(scheme=queryset.scheme_id).delete()
            for data in payment_settings:
                data.update({"scheme": queryset.scheme_id})
                # if PaymentSettings.objects.filter(id=data['pay_id'], scheme=queryset.scheme_id).exists():
                #     psy_set = PaymentSettings.objects.filter(id=data['pay_id'], scheme=queryset.scheme_id).get()
                #     psy_settings_serializer = PaymentSettingsSerializer(psy_set, data=data)
                #     psy_settings_serializer.is_valid(raise_exception=True)
                #     psy_settings_serializer.save()
                # else:
                psy_settings_serializer = PaymentSettingsSerializer(data=data)
                psy_settings_serializer.is_valid(raise_exception=True)
                psy_settings_serializer.save()
            
            if(digi_interest_settings and int(request.data['scheme_type']) == 2):
                for sett in digi_interest_settings:
                    sett.update({"scheme": queryset.scheme_id})
                    sett.update({"from_day" : sett["from_days"],"to_day" : sett["to_days"]})
                    serializer_digi = SchemeDigiGoldInterestSettingsSerializer(data=sett)
                    serializer_digi.is_valid(raise_exception=True)
                    serializer_digi.save()
            
            non_overlapping_data = []
            if SchemeBenefitSettings.objects.filter(scheme=queryset.scheme_id).exists():
                SchemeBenefitSettings.objects.filter(scheme=queryset.scheme_id).delete()
            for benefit_data in scheme_benefit_settings:
                installment_from = float(benefit_data['installment_from'])
                installment_to = float(benefit_data['installment_to'])
                benefit_data.update({"scheme": queryset.scheme_id})

                overlapping_exists = SchemeBenefitSettings.objects.filter(
                        Q(installment_from__lte=installment_to) & Q(installment_to__gte=installment_from),
                        scheme=queryset.scheme_id
                ).exclude(id=benefit_data.get('id')).exists()

                if overlapping_exists:
                    continue

                # if SchemeBenefitSettings.objects.filter(id=benefit_data.get('id'), scheme=queryset.scheme_id).exists():
                #     benefit_set = SchemeBenefitSettings.objects.get(id=benefit_data['id'], scheme=queryset.scheme_id)
                #     benefit_serializer = SchemeBenefitSettingsSerializer(benefit_set, data=benefit_data)
                # else:
                benefit_serializer = SchemeBenefitSettingsSerializer(data=benefit_data)
                benefit_serializer.is_valid(raise_exception=True)
                non_overlapping_data.append(benefit_serializer.save())
            if SchemeGiftSettings.objects.filter(scheme=queryset.scheme_id).exists():
                SchemeGiftSettings.objects.filter(scheme=queryset.scheme_id).delete()
            for gift_set in gift_settings:
                gift_set.update({"scheme": queryset.scheme_id})
                gift_set_serializer = SchemeGiftSettingsSerializer(data=gift_set)
                gift_set_serializer.is_valid(raise_exception=True)
                gift_set_serializer.save()
            serializer.save(updated_by=self.request.user,
                            updated_on=datetime.now(tz=timezone.utc))
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_object()
        try:
            PaymentSettings.objects.filter(scheme=queryset.scheme_id).delete()
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Scheme instance can't be deleted, as it is already in relation"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)