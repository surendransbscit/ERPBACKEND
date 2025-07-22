from rest_framework import generics,status
from rest_framework.response import Response
from django.db import transaction , IntegrityError
from utilities.pagination_mixin import PaginationMixin
pagination = PaginationMixin()  # Apply pagination
from common.permissions import IsEmployee,IsSuperuserOrEmployee,IsCustomerUser
from .models import (ErpEstimation,ErpEstimationSalesDetails,ErpEstimationOldMetalDetails,ErpEstimationSchemeAdjusted,ErpEstimationSalesReturnDetails)
from retailmasters.views import BranchEntryDate,MetalRates
from retailmasters.serializers import MetalRatesSerializer
from customers.models import CustomerAddress
from .serializers import ( ErpEstimationSerializer,ErpEstimationSalesDetailsSerializer,ErpEstimationStoneDetailsSerializer,ErpEstimationOldMetalDetailsSerializer,
                          ErpEstimationSchemeAdjustedSerializer,ErpEstimationItemChargesSerializer,ErpEstimationOtherMetalSerializer,
                          ErpEstimationSalesReturnSerializer)
from utilities.constants import FILTERS
from .constants import ACTION_LIST,EST_COLUMN_LIST
from datetime import datetime
from django.utils import timezone
from django.template.loader import get_template
import os
from xhtml2pdf import pisa
import io
import qrcode
from django.conf import settings
from django.db.models import Q
from billing.models import ErpInvoice,ErpInvoiceSalesDetails
from billing.serializers import ErpInvoiceSerializer,ErpInvoiceSalesDetailsSerializer
from billing.views import get_invoice_no
from collections import defaultdict
from core.views  import get_reports_columns_template

from inventory.models import ErpTagAttribute,ErpTaggingImages,ErpTagging
from inventory.views import convert_to_code_word
from inventory.serializers import ErpTagAttributeSerializer,ErpTaggingImagesSerializer,ErpTaggingSerializer
from retailsettings.models import (RetailSettings)
from retailmasters.models import (Company,Size,metalRatePurityMaster)
from retailcataloguemasters.models import Product,CategoryPurityRate,CustomerMakingAndWastageSettings
from retailcataloguemasters.serializers import CustomerMakingAndWastageSettingsMappingSerializer
from employees.models import (Employee)
from employees.serializers import (EmployeeSerializer)
from utilities.utils import generate_query_result,delete_file_after_delay,convert_tag_to_formated_data
import random


# At the top of your views.py or a utilities module
import socketio
sio = socketio.Client()

class ErpEstimationCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpEstimation.objects.all()
    serializer_class = ErpEstimationSerializer
    
    def get(self, request, *args, **kwargs):
        estimation_id = self.kwargs.get('pk')
        est_url = self.genertate_estimation_print(estimation_id,request)
        response_data = { "response_data" : est_url['response_data'], }
        return Response(response_data, status=status.HTTP_200_OK)
 

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                est_data = request.data.get('estimation')
                sales_details = request.data.get('sales_details')
                purchase_details = request.data.get('purchase_details')
                return_details = request.data.get('return_details')
                scheme_details = request.data.get('scheme_details')
                if not est_data:
                    return Response({"error": "Estimation data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if (not sales_details and not purchase_details and not return_details):
                    return Response({"error": "Estimation Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(request.data['estimation']['id_branch'])
                est_no = self.generate_estimation_no(request.data['estimation']['id_branch'],entry_date)
                est_data.update({"est_no":est_no,"entry_date":entry_date,"created_by": request.user.id})
                est_serializer = ErpEstimationSerializer(data = est_data)
               
                if est_serializer.is_valid(raise_exception=True):
                    est_serializer.save()
                    estimation_id = est_serializer.data['estimation_id']
                    
                    if sales_details:

                        self.insert_sales_details(sales_details,estimation_id)
                    
                    if purchase_details:
                        self.insert_purchase_details(purchase_details,estimation_id)

                    if return_details:
                        self.insert_sales_return_details(return_details,estimation_id)

                    if scheme_details:
                        self.insert_scheme_details(scheme_details,estimation_id)
                    


                    try:
                        # Create a client socket to emit the event
                        sio = socketio.Client()
                        sio.connect('http://127.0.0.1:8001')  # Socket.IO server

                        data = {
                            "estimation_id": estimation_id,
                            "est_no": est_no,
                            "created_by": request.user.id,
                        }

                        # Emit the event to notify frontend clients
                        sio.emit('new_estimation_created', data)
                        sio.emit('update_notification')
                        print("Emitted new_estimation_created event to socket server!")

                        # sio.disconnect()
                    except Exception as e:
                        print(f"Failed to emit socket event: {e}")

                    est_url = self.genertate_estimation_print(estimation_id,request)

                    return Response({"message":"Estmation Created Successfully.",**est_url}, status=status.HTTP_201_CREATED)
                return Response({"error":ErpEstimationSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"error": F"A database error occurred.  {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                estimation_id = kwargs.get('pk')
                est_data = request.data.get('estimation')
                sales_details = request.data.get('sales_details')
                purchase_details = request.data.get('purchase_details')
                return_details = request.data.get('return_details')
                scheme_details = request.data.get('scheme_details')

                print("dfghj")
                if not estimation_id:
                    return Response({"error": "Estimation ID is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not est_data:
                    return Response({"error": "Estimation data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not (sales_details or purchase_details or return_details):
                    return Response({"error": "Estimation Details are missing."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    estimation_instance = ErpEstimation.objects.get(pk=estimation_id)
                except ErpEstimation.DoesNotExist:
                    return Response({"error": "Estimation not found."}, status=status.HTTP_404_NOT_FOUND)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(estimation_instance.id_branch.pk)
                est_date = estimation_instance.entry_date
                print(entry_date,est_date)
                if entry_date != est_date:
                    print(entry_date,est_date)
                    if(ErpEstimation.objects.filter(entry_date= entry_date,est_no =estimation_instance.est_no).exists()):
                        print(entry_date,est_date)
                        est_no = self.generate_estimation_no(estimation_instance.id_branch.pk,entry_date)
                        ErpEstimation.objects.filter(pk=estimation_instance.pk).update(created_on=datetime.now(tz=timezone.utc))
                        est_data.update({"est_no": est_no,"entry_date":entry_date})
                    else:
                        ErpEstimation.objects.filter(pk=estimation_instance.pk).update(created_on=datetime.now(tz=timezone.utc))
                        est_data.update({"entry_date":entry_date})
                    estimation_instance.refresh_from_db()
                    #return Response({"message": "Estimation Date  Updated successfully.",**est_url}, status=status.HTTP_200_OK)

                est_data.update({"updated_by": request.user.id,'updated_on': datetime.now(tz=timezone.utc)})
                est_serializer = ErpEstimationSerializer(estimation_instance, data=est_data, partial=True)
                if est_serializer.is_valid(raise_exception=True):
                    est_serializer.save()
                    print("2dfghj")

                    if sales_details:
                        self.update_sales_details(sales_details, estimation_id)
                    print("dfghjdddcxz")

                    if purchase_details:
                        self.update_purchase_details(purchase_details, estimation_id)

                    if return_details:
                        self.update_return_details(return_details, estimation_id)

                    if scheme_details:
                        self.update_scheme_details(scheme_details, estimation_id)

                    est_url = self.genertate_estimation_print(estimation_id,request)
                    

                    return Response({"message": "Estimation updated successfully.",**est_url}, status=status.HTTP_200_OK)
                return Response({"error": est_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    def update_sales_details(self, sales_details, estimation_id):

        existing_items = ErpEstimationSalesDetails.objects.filter(estimation_id=estimation_id)
        existing_item_map = {item.pk: item for item in existing_items}
        ids_to_delete = set(existing_item_map.keys())

        for detail in sales_details:
            sales_id = detail.get('est_item_id')
            if sales_id:
                ids_to_delete.discard(sales_id)
                try:
                    sales_instance = ErpEstimationSalesDetails.objects.get(pk=sales_id,estimation_id = estimation_id)
                    stone_details =detail.get('stone_details',[])
                    charges_details =detail.get('charges_details', [])
                    detail['status'] = 0
                    serializer = ErpEstimationSalesDetailsSerializer(sales_instance, data=detail, partial=True)

                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        self.update_other_details(stone_details,serializer.data['est_item_id'],ErpEstimationStoneDetailsSerializer,'est_item_id','est_stn_id')
                        self.update_other_details(charges_details,serializer.data['est_item_id'],ErpEstimationItemChargesSerializer,'est_item_id','charges_est_item_id')

                except ErpEstimationSalesDetails.DoesNotExist:
                    self.insert_sales_details([detail],estimation_id)
            else:
                self.insert_sales_details([detail],estimation_id)

        if ids_to_delete:
            ErpEstimationSalesDetails.objects.filter(pk__in=ids_to_delete).delete()

    def update_purchase_details(self, purchase_details, estimation_id):
        existing_items = ErpEstimationOldMetalDetails.objects.filter(estimation_id=estimation_id)
        existing_item_map = {item.pk: item for item in existing_items}
        ids_to_delete = set(existing_item_map.keys())

        for detail in purchase_details:
            purchase_id = detail.get('est_old_metal_item_id')
            if purchase_id:
                ids_to_delete.discard(purchase_id)
                try:
                    purchase_instance = ErpEstimationOldMetalDetails.objects.get(pk=purchase_id, estimation_id=estimation_id)
                    serializer = ErpEstimationOldMetalDetailsSerializer(purchase_instance, data=detail, partial=True)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        self.update_other_details(detail.get('stone_details', []),serializer.data['est_old_metal_item_id'],ErpEstimationStoneDetailsSerializer,'est_old_metal_item_id','est_stn_id')

                except ErpEstimationOldMetalDetails.DoesNotExist:                     
                        self.insert_purchase_details([detail],estimation_id)
            else:
                self.insert_purchase_details([detail],estimation_id)

        if ids_to_delete:
            ErpEstimationOldMetalDetails.objects.filter(pk__in=ids_to_delete).delete()

    def update_return_details(self, return_details, estimation_id):
        existing_items = ErpEstimationSalesReturnDetails.objects.filter(estimation_id=estimation_id)
        existing_item_map = {item.pk: item for item in existing_items}
        ids_to_delete = set(existing_item_map.keys())

        for detail in return_details:
            return_id = detail.get('est_return_item_id')
            if return_id:
                ids_to_delete.discard(return_id)
                try:
                    return_instance = ErpEstimationSalesReturnDetails.objects.get(pk=return_id, estimation_id=estimation_id)
                    serializer = ErpEstimationSalesReturnSerializer(return_instance, data=detail, partial=True)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        self.update_other_details(detail.get('stone_details', []),serializer.data['est_return_item_id'],ErpEstimationStoneDetailsSerializer,'est_return_item_id','est_stn_id')

                except ErpEstimationSalesReturnDetails.DoesNotExist:                     
                        self.insert_sales_return_details([detail],estimation_id)
            else:
                self.insert_sales_return_details([detail],estimation_id)

        if ids_to_delete:
            ErpEstimationSalesReturnDetails.objects.filter(pk__in=ids_to_delete).delete()

    def update_other_details(self, details, parent_id, serializer_class, parent_field,id):

        existing_details = serializer_class.Meta.model.objects.filter(**{parent_field: parent_id})
        existing_detail_map = {detail.pk: detail for detail in existing_details}
        ids_to_delete = set(existing_detail_map.keys())

        for detail in details:
            detail_id = detail.get(id)

            if detail_id:

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

    def update_scheme_details(self, scheme_details, estimation_id):
        existing_schemes = ErpEstimationSchemeAdjusted.objects.filter(estimation_id=estimation_id)
        existing_schemes_map = {item.pk: item for item in existing_schemes}
        ids_to_delete = set(existing_schemes_map.keys())

        for scheme in scheme_details:
            scheme_id = scheme.get('est_scheme_adj_id')
            scheme.update({"estimation_id": estimation_id})

            if scheme_id:
                ids_to_delete.discard(scheme_id)
                scheme_instance = ErpEstimationSchemeAdjusted.objects.get(est_scheme_adj_id=scheme_id)
                scheme_serializer = ErpEstimationSchemeAdjustedSerializer(instance=scheme_instance, data=scheme)
                if scheme_serializer.is_valid(raise_exception=True):
                    scheme_serializer.save()
            else:
                scheme_serializer = ErpEstimationSchemeAdjustedSerializer(data=scheme)
                if scheme_serializer.is_valid(raise_exception=True):
                    scheme_serializer.save()

        if ids_to_delete:
            ErpEstimationSchemeAdjusted.objects.filter(pk__in=ids_to_delete).delete()

    def generate_estimation_no(self,id_branch,entry_date):
        is_generate_random_est = RetailSettings.objects.get(name='is_generate_random_est').value
        if int(is_generate_random_est)==0:
            last_est=ErpEstimation.objects.filter(id_branch=id_branch,entry_date =entry_date ).order_by('-estimation_id').first()
            if last_est:
                code= int(last_est.est_no) + 1
            else:
                code = '1'
        elif int(is_generate_random_est)==1:
            attempts = 0
            max_attempts = 1000

            while attempts < max_attempts:
                code = str(random.randint(10000, 99999))  # 5-digit random number
                if not ErpEstimation.objects.filter(est_no=code, id_branch=id_branch,entry_date =entry_date).exists():
                    return code
                attempts += 1
            
        return code
    
    def insert_sales_details(self,sales_details,estimation_id):

        for sales_item in sales_details:
            
            sales_item.update({"estimation_id":estimation_id,'status': 0})
            stone_details = sales_item['stone_details']
            charges_details=sales_item['charges_details']
            other_metal_detail=sales_item['other_metal_detail']

            est_detail_serializer = ErpEstimationSalesDetailsSerializer(data=sales_item)
            if(est_detail_serializer.is_valid(raise_exception=True)):
                est_detail_serializer.save()
                    
                for stn in stone_details:
                    stn.update({"est_item_id":est_detail_serializer.data['est_item_id']})
                    stone_serializer = ErpEstimationStoneDetailsSerializer(data=stn)
                    stone_serializer.is_valid(raise_exception=True)
                    stone_serializer.save()

                for charge in charges_details:

                    charge.update({'id_charges' : charge['selectedCharge'],'charges_amount' : charge['amount'],"est_item_id":est_detail_serializer.data['est_item_id']})
                    charge_serializer = ErpEstimationItemChargesSerializer(data=charge)
                    charge_serializer.is_valid(raise_exception=True)
                    charge_serializer.save()

                for other_metal in other_metal_detail:

                    other_metal.update({"est_item_id":est_detail_serializer.data['est_item_id']})
                    other_metal_serializer = ErpEstimationOtherMetalSerializer(data=other_metal)
                    other_metal_serializer.is_valid(raise_exception=True)
                    other_metal_serializer.save()
                
            else:
                return Response({"error":ErpEstimationSalesDetails.errors}, status=status.HTTP_400_BAD_REQUEST)
            
    def insert_purchase_details(self,purchase_details,estimation_id):
        for purchase_item in purchase_details:
            purchase_item.update({"estimation_id":estimation_id})
            purchase_detail_serializer = ErpEstimationOldMetalDetailsSerializer(data=purchase_item,stone_details = purchase_item['stone_details'])
            if(purchase_detail_serializer.is_valid(raise_exception=True)):
                purchase_detail_serializer.save()
                    
                for stn in purchase_item['stone_details']:
                    stn.update({"est_old_metal_item_id":purchase_detail_serializer.data['est_old_metal_item_id']})
                    stone_serializer = ErpEstimationStoneDetailsSerializer(data=stn)
                    stone_serializer.is_valid(raise_exception=True)
                    stone_serializer.save()
            else:
                return Response({"error":ErpEstimationOldMetalDetailsSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def insert_sales_return_details(self,return_details,estimation_id):
        for return_item in return_details:
            return_item.update({"estimation_id":estimation_id})
            purchase_detail_serializer = ErpEstimationSalesReturnSerializer(data=return_item)
            if(purchase_detail_serializer.is_valid(raise_exception=True)):
                purchase_detail_serializer.save()
                    
                for stn in return_item['stone_details']:
                    stn.update({"est_return_item_id":purchase_detail_serializer.data['est_return_item_id']})
                    stone_serializer = ErpEstimationStoneDetailsSerializer(data=stn)
                    stone_serializer.is_valid(raise_exception=True)
                    stone_serializer.save()
            else:
                return Response({"error":ErpEstimationSalesReturnSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
    def insert_scheme_details(self,scheme_details,estimation_id):
        for scheme in scheme_details:
            scheme.update({"estimation_id":estimation_id, "closing_weight":scheme.closing_weight,
                           "wastage":scheme.va, "mc":scheme.mc, "closing_amount":scheme.amount, "rate_per_gram":scheme.rate_per_gram})
            scheme_serializer = ErpEstimationSchemeAdjustedSerializer(data=scheme)
            if(scheme_serializer.is_valid(raise_exception=True)):
                scheme_serializer.save()
            else:
                return Response({"error":ErpEstimationSchemeAdjustedSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
    def genertate_estimation_print (self,estimation_id,request):
        obj = ErpEstimation.objects.get(estimation_id=estimation_id)
        est_serializer = ErpEstimationSerializer(obj)
        est_sales_details = ErpEstimationSalesDetails.objects.filter(estimation_id=obj).order_by('pk')
        est_sale_serializer = ErpEstimationSalesDetailsSerializer(est_sales_details, many=True,context={'stone_details': True, 'charges_details': True})
        
        est_purchase_details = ErpEstimationOldMetalDetails.objects.filter(estimation_id=obj).order_by('pk')
        est_purchase_serializer = ErpEstimationOldMetalDetailsSerializer(est_purchase_details, many=True)
        
        est_return_details = ErpEstimationSalesReturnDetails.objects.filter(estimation_id=obj).order_by('pk')
        est_return_serializer = ErpEstimationSalesReturnSerializer(est_return_details, many=True)
        
        est_scheme_adjusted = ErpEstimationSchemeAdjusted.objects.filter(estimation_id=obj)
        est_scheme_adjusted_serializer = ErpEstimationSchemeAdjustedSerializer(est_scheme_adjusted, many=True)
        metalrates = MetalRates.objects.all().latest('rate_id')
        metalrates_serializer = MetalRatesSerializer(metalrates)
        

        response_data = est_serializer.data
        sales_details = est_sale_serializer.data
        purchase_details = est_purchase_serializer.data
        return_details = est_return_serializer.data
        template_type = int(RetailSettings.objects.get(name='estimation_print_template').value)
        comp = Company.objects.get(id_company=1)
        emp_name =''
        emp_name_query  =  generate_query_result(f"""SELECT GROUP_CONCAT(DISTINCT emp.firstname) as emp_name FROM erp_estimation_sales_details sa  
                                                LEFT JOIN erpemployee emp ON emp.id_employee = sa.ref_emp_id_id
                                                Where sa.estimation_id_id = {estimation_id} GROUP BY sa.estimation_id_id; """)
        if emp_name_query :
            emp_name = emp_name_query[0]['emp_name']

        if emp_name != None and emp_name == '':
            emp_name = obj.id_employee.firstname

        if(CustomerAddress.objects.filter(customer=response_data['id_customer']).exists()):
            cus_address = CustomerAddress.objects.filter(customer=response_data['id_customer']).first()
            if cus_address.line1!=None and cus_address.line1!='':
                response_data.update({"address":cus_address.line1})
            if cus_address.city!=None and cus_address.city!='':
                response_data.update({"city":cus_address.city.name})
            if cus_address.pincode!=None and cus_address.pincode!='':
                response_data.update({"pin_code":cus_address.pincode})
        else:
            response_data.update({"address":"",
                                  "city":"",
                                  "pin_code":""})

        sgst_cost =0
        cgst_cost =0
        igst_cost =0
        tax_per=0
        total_taxable =0
        avg_rate =0
        total_nwt =0
        total_gwt =0
        total_vawt =0
        total_pur_nwt =0
        total_pur_pure_wt = 0
        total_pur_gwt =0
        rate =metalrates.gold_22ct
        total_stone_amt =0
        total_charges_amt =0
        total_other_amt =0
        total_mc_value =0
        total_tax_amount = 0
        total_pur_wnt = 0
        total_item_mc_value = 0
        total_rate_per_gram = 0
        dash= "-------------------------------------------------------------------------"
        partly_sales_details = ErpEstimationSalesDetails.objects.filter(estimation_id=obj,is_partial_sale = 1)
        partly_sales_details = ErpEstimationSalesDetailsSerializer(partly_sales_details, many=True).data
        partly_sold_pcs = partly_sold_grosswt = partly_sold_netwt = partly_sold_leswt = partly_sold_diawt = partly_sold_stnwt = partly_sold_otherwt=0
        group_data = {}
        purchase_group_data = {}
        for partly in partly_sales_details:
            queryset = ErpTagging.objects.filter(tag_id=partly["tag_id"]).get()
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

            partly.update({
                "tag_gwt":format(float(queryset.tag_gwt),'.3f'),
                "sold_gwt":format(float(partly['gross_wt']),'.3f'),
                "balance_gross_wt" : format(float(queryset.tag_gwt) - float(partly['gross_wt']),'.3f'),
                "balance_net_wt" : float(queryset.tag_nwt) - float(sold_netwt) - float(partly["net_wt"]),
                "balance_less_wt" : float(queryset.tag_lwt) - float(sold_leswt) - float(partly["less_wt"]),
                "balance_dia_wt" : float(queryset.tag_dia_wt) - float(sold_diawt) - float(partly["dia_wt"]),
                "balance_stn_wt" : float(queryset.tag_stn_wt) - float(sold_stnwt) - float(partly["stone_wt"]),
                "balance_other_metal_wt" : float(queryset.tag_other_metal_wt) - float(sold_otherwt) - float(partly["other_metal_wt"]),
            })
            partly_sold_pcs += float(partly["balance_gross_wt"])
            partly_sold_grosswt += float(partly["balance_gross_wt"])
            partly_sold_netwt += float(partly["balance_net_wt"])
            partly_sold_leswt += float(partly["balance_less_wt"])
            partly_sold_diawt += float(partly["balance_dia_wt"])
            partly_sold_stnwt += float(partly["balance_stn_wt"])
            partly_sold_otherwt += float(partly["balance_other_metal_wt"])
                # "stone_details" : balance_stone_detail,
                # "other_metal_details":balance_other_detail,
        if (partly_sales_details):
            response_data['partly_sold_otherwt'] = format(partly_sold_otherwt, '.3f')
            response_data['partly_sold_grosswt'] = format(partly_sold_grosswt, '.3f')
            response_data['partly_sold_netwt'] = format(partly_sold_netwt, '.3f')
            response_data['partly_sold_leswt'] = format(partly_sold_leswt, '.3f')
            response_data['partly_sold_diawt'] = format(partly_sold_diawt, '.3f')
            response_data['partly_sold_stnwt'] = format(partly_sold_stnwt, '.3f')
        sales_stone = []
        mrp_item_cost = 0
        mpr_item_count = 0
        total_tax_discount = 0

        for index,item in enumerate(sales_details):
            if (int(item.get('weight_show_in_print', 1)) == 0 and int(template_type) == 1):
                if (int(item.get('weight_show_in_print_purity', 1)) != 0):
                    print("weight_show_in_print_purity :",item.get('weight_show_in_print_purity', 1))
                    item['weight_show_in_print'] = 1
            wt_code=0
            mrp_flexible_amt = 0
            tot_mc_amt =  item['total_mc_value']
            tot_va_amt = float(item['wastage_weight']) * float(item.get('rate_per_gram', 0))
            tax_discount = float(item['discount_amount']) - float(tot_mc_amt) - float(tot_va_amt)
            if tax_discount > 0:
                total_tax_discount += tax_discount
            total_rate_per_gram = item.get('rate_per_gram', 0)
            item.update({"sno": index+1})
            if(float(item['mc_discount_amount']) > 0) :
                item_mc = float(item['total_mc_value']) - float(item['mc_discount_amount'])
                if float(item_mc) < 0:
                    item['total_mc_value'] = 0
                else:
                    item['total_mc_value'] = format(item_mc,'.2f')
            if(float(item['wastage_discount']) > 0) :
                item['wastage_percentage'] = (item['wastage_percentage_after_disc'])
                item['wastage_weight'] = format(((float(item['wastage_percentage'])*float(item['net_wt']))/100),'.3f')

            if (int(item.get('weight_show_in_print', 1)) == 0 and template_type == 1):
                wt_code = convert_to_code_word(float(item.get('net_wt', 0)))
                tot_va_amt = float(item['wastage_weight']) * float(item.get('rate_per_gram', 0))
                mrp_flexible_amt = float(item.get('taxable_amount', 0))
            else:
                total_gwt += float(item.get('gross_wt', 0))
                total_nwt += float(item.get('net_wt', 0))
                total_vawt += float(item.get('wastage_weight', 0))
                total_mc_value+= float(item.get('total_mc_value', 0))

            sgst_cost += float(item.get('sgst_cost', 0))
            cgst_cost += float(item.get('cgst_cost', 0))
            igst_cost += float(item.get('igst_cost', 0))
            total_taxable += float(item.get('taxable_amount', 0))
            tax_per = float(item.get('tax_percentage', 0))
            total_stone_amt += float(item.get('stone_amount', 0))
            total_charges_amt += float(item.get('charges_amount', 0))
            total_other_amt+= float(item.get('other_metal_amt', 0))
            avg_rate += float(item.get('rate_per_gram', 0) if float(item.get('sales_mode', 0))==1 else 0)
            # total_mc_value+= float(item.get('flat_mc_value', 0))
            total_tax_amount += float(item.get('tax_amount', 0))
            item_mc_value = format((float(item.get('total_mc_value', 0))*float(tax_per)/100) + float(item.get('total_mc_value', 0)),'.2f')
            total_item_mc_value += float(item_mc_value)
            rate_per_gram = (item.get('rate_per_gram', 0) if float(item.get('sales_mode', 0))==1 else  item.get('sell_rate', 0))
            item.update({"wt_code":wt_code,"item_mc_value": item_mc_value,tax_discount:tax_discount})
            if(float(item.get('sales_mode', 0)) == 0):
                mrp_item_cost += float(item.get('item_cost', 0))  + float(item.get('discount_amount', 0))
                total_nwt -= float(item.get('net_wt', 0))
                total_gwt -= float(item.get('gross_wt', 0))
                #tax_per -= float(item.get('tax_percentage', 0))
                total_stone_amt -= float(item.get('stone_amount', 0))
                total_charges_amt -= float(item.get('charges_amount', 0))
                total_other_amt-= float(item.get('other_metal_amt', 0))
                mpr_item_count += 1
            
            # print(mrp_item_cost,"mrp_item_cost",mpr_item_count,avg_rate)
            group_data.setdefault(rate_per_gram, []).append({
                "rate_per_gram": rate_per_gram,
                "sales_mode":item.get('sales_mode', 0),
                "cat_id": item.get('cat_id', 0),
                "gross_wt": item.get('gross_wt', 0),
                "net_wt": item.get('net_wt', 0),
                "pieces": item.get('pieces', 0),
                "sell_rate": item.get('sell_rate', 0),
                "wastage_weight": item.get('wastage_weight', 0),
                "weight_show_in_print":int(item.get('weight_show_in_print', 1)),
                "mrp_flexible_amt":mrp_flexible_amt

            })
            sales_stone.extend(item['stone_details'])

        rate_grouped = []
        total_amt_wt =0
        for key,item in group_data.items():
            wt = 0
            rate = 0
            is_weight_item = True
            for item2 in item:
              if item2['weight_show_in_print'] == 0 and template_type == 1:
                  total_amt_wt += item2['mrp_flexible_amt']
                  
              elif(float(item2.get('sales_mode', 0)) == 1 or (float(item2.get('net_wt', 0)) >0 ) ):
                wt += float(item2.get('net_wt', 0)) + float(item2.get('wastage_weight', 0))
                if float(item2.get('net_wt', 0)) >0:
                    rate = float(item2.get('rate_per_gram', 0))
              else:
                wt+= item2.get('pieces', 0)
                is_weight_item = False
                rate = float(item2.get('rate_per_gram', 0))

            total_amt_wt += float(wt) * float(rate)
            if(is_weight_item):
                rate_grouped.append({"wt": format(wt, '.3f'),"rate_per_gram": rate,})
            else:
                rate_grouped.append({"wt": f'{wt} Pcs',"rate_per_gram": rate,})
            
        est_print_old_metal_rate_show = RetailSettings.objects.get(name='est_print_old_metal_rate_show').value
        
        for item in purchase_details:
            if int(est_print_old_metal_rate_show) == 1:
                rate_per_gram = item.get('rate_per_gram', 0)
            else:
                rate_per_gram = item.get('customer_rate', 0)
            custom_less_weight = float(float(item.get('gross_wt', 0)) - float(item.get('pure_weight', 0)))
            item.update({"custom_less_weight" : format(float(custom_less_weight) , '.3f'),
                "rate_per_gram":rate_per_gram
                })
            total_pur_gwt += float(item.get('gross_wt', 0))
            total_pur_nwt += float(item.get('net_wt', 0))
            total_pur_pure_wt += float(item.get('pure_weight', 0))
            total_pur_wnt += float(item.get('wastage_weight', 0))
            purchase_group_data.setdefault(rate_per_gram, []).append({
                "rate_per_gram": rate_per_gram,
                "gross_wt": item.get('gross_wt', 0),
                "net_wt": item.get('net_wt', 0),
                "dust_wt": item.get('dust_wt', 0),
            })
        
        pur_rate_grouped = []
        total_pur_amt_wt =0
        for key,item in purchase_group_data.items():
            wt = 0
            rate = 0
            for item2 in item:
                wt += float(item2.get('net_wt', 0))
                rate = float(item2.get('rate_per_gram', 0))
            total_pur_amt_wt += float(wt) * float(rate)
            pur_rate_grouped.append({"wt": format(wt, '.3f'),"rate_per_gram": rate,})
         
        # print(pur_rate_grouped)   
            


        total_amount =0
        if sales_details:
            total_wt = format((float(total_nwt) + float(total_vawt)), '.3f')
            gold_22ct = metalrates_serializer.data['gold_22ct']
            gold_22ct_plus_tax = 0
            if(int(template_type) == 1):#ssm
                if(avg_rate):
                    avg_rate = round(avg_rate / (len(sales_details) - mpr_item_count),2)
                rate = avg_rate
                #tax_per= tax_per / (len(sales_details))
                tax_rate = format((float(rate) * float(round(tax_per, 2) / 100)), '.2f')
                total_rate = round((float(rate) + float(tax_rate)),2)
                charges_amt = float(total_charges_amt)
                other_amt = float(total_other_amt )
                stone_amt = float(total_stone_amt)
                mrp_item_cost =0
                total_amount = total_amt_wt + stone_amt + other_amt + charges_amt + total_tax_amount + total_mc_value + mrp_item_cost - total_tax_discount
                print(total_wt,rate,stone_amt,other_amt,charges_amt,total_tax_amount,total_mc_value,mrp_item_cost,total_tax_discount,total_amount,"TOTAL AMOUNT")
            else:
                if(avg_rate):
                    avg_rate = round(avg_rate / (len(sales_details) - mpr_item_count),2)
                rate = avg_rate
                tax_rate = format((float(avg_rate) * float(round(tax_per, 2) / 100)), '.2f')
                total_rate = round((float(avg_rate) + float(tax_rate)),2)
                total_charges_amt = float(total_charges_amt + (float(total_charges_amt) * float(round(tax_per, 2) / 100)))
                total_other_amt = float(total_other_amt + (float(total_other_amt) * float(round(tax_per, 2) / 100)))
                total_stone_amt = float(total_stone_amt + (float(total_stone_amt) * float(round(tax_per, 2) / 100)) )
                total_amount = float(total_wt) * float(total_rate) + total_stone_amt + total_other_amt + total_charges_amt + total_mc_value + mrp_item_cost
                gold_22ct_plus_tax = float(gold_22ct) + (float(gold_22ct) * float(tax_per / 100))

            response_data['gold_22ct_plus_tax'] = format(gold_22ct_plus_tax, '.2f')
            response_data['gold_22ct'] = gold_22ct
            response_data['rate_tax_percentage'] = tax_per
            response_data['rate_tax_value'] = float(gold_22ct) * float(tax_per / 100)
            response_data['total_rate_per_gram'] = total_rate_per_gram
            
            response_data['mrp_item_cost'] = format(mrp_item_cost, '.2f')
            response_data['total_gwt'] = format(total_gwt, '.3f')
            response_data['total_nwt'] = format(total_nwt, '.3f')
            response_data['total_vawt'] = format(total_vawt, '.3f')
            response_data['total_wt'] = format((float(total_nwt) + float(total_vawt)), '.3f')
            response_data['total_amount'] = format(total_amount, '.2f')
            response_data['total_mc_value'] = format(total_mc_value, '.2f')
            response_data['total_mc_value'] = format(total_mc_value, '.2f')
            response_data['total_amt_wt'] = format(total_amt_wt, '.2f')
            response_data['total_rate'] = total_rate
            response_data['tax_rate'] = tax_rate
            response_data['sales_stone'] = sales_stone
            response_data['total_tax_amount'] = total_tax_amount
            response_data['rate_grouped'] = rate_grouped
            response_data['rate'] = round(rate,2)
            response_data['total_charges_amt'] = format(total_charges_amt, '.2f')
            response_data['total_other_amt'] = format(total_other_amt, '.2f')
            response_data['total_stone_amt'] = format(total_stone_amt, '.2f')
            response_data['total_taxable'] = format(total_taxable,'.2f')
            response_data['sgst_cost'] = format(sgst_cost, '.3f')
            response_data['cgst_cost'] = format(cgst_cost, '.3f')
            response_data['igst_cost'] = format(igst_cost, '.3f')
            response_data['tax_per'] = round(tax_per, 2)
            response_data['igst_per'] = round(tax_per, 2) 
            response_data['cgst_per'] = round(tax_per / 2, 2)
            response_data['sgst_per'] = round(tax_per / 2, 2)
            response_data['emp_name'] = emp_name

        response_data['emp_name'] = emp_name
        response_data['sales_stone'] = sales_stone
        response_data['total_pur_nwt'] = format(total_pur_nwt,'.3f')
        response_data['total_tax_discount'] = format(total_tax_discount,'.2f')
        response_data['total_pur_pure_wt'] = format(total_pur_pure_wt,'.3f')
        response_data['total_pur_gwt'] = format(total_pur_gwt,'.3f')
        response_data['total_pur_wnt'] = format(total_pur_wnt,'.3f')
        response_data['total_item_mc_value'] = format(total_item_mc_value,'.2f')
        response_data['pur_rate_grouped'] = pur_rate_grouped
        response_data['company_name'] = comp.short_code
        response_data['sales_details'] = sales_details
        response_data['partly_sales_details'] = partly_sales_details
        response_data['dash'] = dash
        response_data['purchase_details'] = purchase_details
        response_data['return_details'] = return_details
        response_data['scheme_details'] = est_scheme_adjusted_serializer.data
        response_data['metal_rates'] = metalrates_serializer.data

        # save_dir = os.path.join(settings.MEDIA_ROOT, f'estimation/{estimation_id}')

        # if not os.path.exists(save_dir):
        #     os.makedirs(save_dir)
        
        # qr = qrcode.QRCode(
        #     version=1,
        #     error_correction=qrcode.constants.ERROR_CORRECT_L,
        #     box_size=10,
        #     border=4,
        # )
        # qr.add_data(estimation_id)
        # qr.make(fit=True)
        # qr_img = qr.make_image(fill_color="black", back_color="white")
        # qr_path = os.path.join(save_dir, 'qrcode.png')
        # qr_img.save(qr_path)

        # response_data['qr_path'] = qr_path
        # if int(template_type) == 1:
        #     template = get_template('estimation_print_template1.html')
        # elif int(template_type) == 2:
        #     template = get_template('estimation_print_template2.html')
        # else:
        #     template = get_template('estimation_print_template3.html')

            
        # html = template.render(response_data)
        # result = io.BytesIO()
        # pisa.pisaDocument(io.StringIO(html), result)
        # pdf_path = os.path.join(save_dir, 'est_print.pdf')
        # with open(pdf_path, 'wb') as f:
        #     f.write(result.getvalue())

        # pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'estimation/{estimation_id}/est_print.pdf')

        # delete_file_after_delay(pdf_path, delay=5)

        return {"response_data":response_data}
            


            
class ErpEstimationListAPIView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    queryset = ErpEstimation.objects.all()
    serializer_class = ErpEstimationSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        est_serializer = ErpEstimationSerializer(obj)
        est_sales_details = ErpEstimationSalesDetails.objects.filter(estimation_id=obj)
        est_sale_serializer = ErpEstimationSalesDetailsSerializer(est_sales_details, many=True,context={'stone_details': True, 'charges_details': True})
        est_purchase_details = ErpEstimationOldMetalDetails.objects.filter(estimation_id=obj)
        est_purchase_serializer = ErpEstimationOldMetalDetailsSerializer(est_purchase_details, many=True,stone_details=True)
        est_return_details = ErpEstimationSalesReturnDetails.objects.filter(estimation_id=obj)
        est_return_serializer = ErpEstimationSalesReturnSerializer(est_return_details, many=True)
        
        est_scheme_adjusted = ErpEstimationSchemeAdjusted.objects.filter(estimation_id=obj)
        est_scheme_adjusted_serializer = ErpEstimationSchemeAdjustedSerializer(est_scheme_adjusted, many=True)
        response_data = est_serializer.data
        response_data['sales_details'] = est_sale_serializer.data
        response_data['purchase_details'] = est_purchase_serializer.data
        response_data['return_details'] = est_return_serializer.data
        response_data['scheme_details'] = est_scheme_adjusted_serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
 
    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        id_branch = (id_branch) if id_branch != '' else 0
        queryset = ErpEstimation.objects.all().order_by('-created_on')
        if from_date and to_date:
                queryset = queryset.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(id_branch__in=id_branch)
        else:
            queryset = queryset.filter(id_branch=id_branch)

        paginator, page = pagination.paginate_queryset(queryset, request,None, EST_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,EST_COLUMN_LIST,request.data.get('path_name',''))
        serializer = ErpEstimationSerializer(page, many=True)

        for data in serializer.data:
            data['is_editable'] = 1
            invoice_no = []
            queryset_sales = ErpInvoice.objects.filter(erp_invoice_id=data['invoice_id'],invoice_status=1,setting_bill_type = 1 ).order_by('-erp_invoice_id')

            if(queryset_sales):
                inv_data = ErpInvoiceSerializer(queryset_sales,many=True,context={'invoice_no': True}).data
                for dat in inv_data:
                    if dat['inv_no'] :
                        data['is_editable'] = 0
                        erp_invoice_id = dat['erp_invoice_id']
                        invoice_no.append(dat['inv_no']['invoice_no'])
            if invoice_no:
                data['erp_invoice_id'] = erp_invoice_id
                data['invoice_no'] = ", ".join(set(invoice_no))

            data['date'] = f"{data['date']} {data['time']}"
            
            sales = float(data.get('sales_amount') or 0)
            purchase = float(data.get('purchase_amount') or 0)
            ret = float(data.get('return_amount') or 0)

            if sales and not purchase and not ret:
                data['type'] = "Sales"
            elif purchase and not sales and not ret:
                data['type'] = "Purchase"
            elif ret and not sales and not purchase:
                data['type'] = "Return"
            elif sales and purchase and not ret:
                data['type'] = "Sales & Purchase"
            elif (purchase or ret) and not sales:
                data['type'] = "Purchase & Return"
            elif sales and ret and not purchase:
                data['type'] = "Sales & Return"
            elif sales and purchase and ret:
                data['type'] = "All"
            else:
                data['type'] = "Unknown"

            


        FILTERS['isDateFilterReq'] = False
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
        return pagination.paginated_response(serializer.data,context)



class ErpEstimationAPIView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    queryset = ErpEstimation.objects.all()
    serializer_class = ErpEstimationSerializer

    def post(self, request, *args, **kwargs):
        try:
            est_no = request.data.get('est_no')
            id_branch = request.data.get('id_branch')
            is_est_approval_req = int(RetailSettings.objects.get(name='is_est_approval_req').value)
            if not est_no:
                return Response({"error": "Estimation No is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not id_branch:
                return Response({"error": "Estimation Branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(id_branch)
            obj = ErpEstimation.objects.filter(est_no = est_no ,id_branch = id_branch,entry_date = entry_date).get()
            if is_est_approval_req == 1 and obj.send_to_approval == 1 and obj.is_approved == 0 :
                return Response({"message": "Estimation is Waiting For Approval"}, status=status.HTTP_400_BAD_REQUEST)
            elif is_est_approval_req == 1 and obj.send_to_approval == 1 and obj.is_approved == 2 :
                return Response({"message": "Estimation is Rejected"}, status=status.HTTP_400_BAD_REQUEST)
            est_serializer = ErpEstimationSerializer(obj)
            est_sales_details = ErpEstimationSalesDetails.objects.filter(Q(item_type=0, tag_id__tag_status_id=1) | Q(item_type__gt=0, status=0),estimation_id=obj)
            est_sale_serializer = ErpEstimationSalesDetailsSerializer(est_sales_details, many=True,context={'stone_details': True, 'charges_details': True})
            est_purchase_details = ErpEstimationOldMetalDetails.objects.filter(estimation_id=obj,status = 0)
            est_purchase_serializer = ErpEstimationOldMetalDetailsSerializer(est_purchase_details, many=True,stone_details=True)
            est_scheme_adjusted = ErpEstimationSchemeAdjusted.objects.filter(estimation_id=obj)
            est_scheme_adjusted_serializer = ErpEstimationSchemeAdjustedSerializer(est_scheme_adjusted, many=True)
            est_return_details = ErpEstimationSalesReturnDetails.objects.filter(estimation_id=obj)
            est_return_serializer = ErpEstimationSalesReturnSerializer(est_return_details, many=True)
            response_data = est_serializer.data
            response_data['sales_details'] = est_sale_serializer.data
            response_data['purchase_details'] = est_purchase_serializer.data
            response_data['return_details'] = est_return_serializer.data
            response_data['scheme_details'] = est_scheme_adjusted_serializer.data
            print(response_data['sales_details'])
            if(response_data['purchase_details'] or response_data['sales_details'] or response_data['return_details']):
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Estimation Details Not Available"}, status=status.HTTP_400_BAD_REQUEST)

        except ErpEstimation.DoesNotExist:
            return Response({"message": "Invalid Estimation No"}, status=status.HTTP_400_BAD_REQUEST)
        


class ErpEstimationApproveAPIView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    queryset = ErpEstimation.objects.all()
    serializer_class = ErpEstimationSerializer

    def post(self, request, *args, **kwargs):
        try:
            employee_obj = Employee.objects.get(user=request.user)
            result = []
            id_branch = request.data.get('id_branch')
            if not id_branch:
                return Response({"error": "Estimation Branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(id_branch)
            obj = ErpEstimation.objects.filter(id_branch = id_branch,entry_date = entry_date,is_approved__in = [0,1],
                                               send_to_approval=True)
            if(employee_obj.id_profile.show_all_approval_estimations != True):
                obj = obj.filter(id_employee = employee_obj.pk)
            if('est_code' in request.data):
                obj = obj.filter(est_no=request.data['est_code'])
            est_serializer = ErpEstimationSerializer(obj,many=True)
            for data in est_serializer.data:
                
                est_sales_details = ErpEstimationSalesDetails.objects.filter(Q(item_type=0, tag_id__tag_status_id=1) | Q(item_type__gt=0, status=0),estimation_id=data['estimation_id'])
                est_sale_serializer = ErpEstimationSalesDetailsSerializer(est_sales_details, many=True,context={'stone_details': True, 'charges_details': True})
                est_purchase_details = ErpEstimationOldMetalDetails.objects.filter(estimation_id=data['estimation_id'],status = 0)
                est_purchase_serializer = ErpEstimationOldMetalDetailsSerializer(est_purchase_details, many=True,stone_details=True)
                est_scheme_adjusted = ErpEstimationSchemeAdjusted.objects.filter(estimation_id=data['estimation_id'])
                est_scheme_adjusted_serializer = ErpEstimationSchemeAdjustedSerializer(est_scheme_adjusted, many=True)
                if(est_sale_serializer.data or est_purchase_serializer.data):
                    data.update({"active_tab":str(data['estimation_id'])+"_1", "purchase_tab":str(data['estimation_id'])+"_2", "paymentModeData":[],
                                "sales_tab":str(data['estimation_id'])+"_1","partlysale_tab":str(data['estimation_id'])+"_3","payment_tab":str(data['estimation_id'])+"_4",
                                "totalAmountReceived":data['net_amount'],"isCredit":False,"discountAmount":data['total_discount_amount'],"balanceAmount":data['net_amount'],"id_employee":''})

                    data['sales_details'] = est_sale_serializer.data
                    data['purchase_details'] = est_purchase_serializer.data
                    data['scheme_details'] = est_scheme_adjusted_serializer.data
                    data['partlysale_details'] = self.get_partly_sale_details(data)
                    # if(data['sales_details']):
                    #     data.update({"emp_name":  data['sales_details'][0]['emp_name'],"id_employee":  data['sales_details'][0]['ref_emp_id']})
                    # response_data = est_serializer.data
                    if(data not in result):
                        result.append(data)
            return Response({"message": "Data Fetched successfully..","data":result}, status=status.HTTP_200_OK)
    
        except ErpEstimation.DoesNotExist:
            return Response({"message": "Invalid Estimation No"}, status=status.HTTP_400_BAD_REQUEST)
        
    def get_partly_sale_details(self,obj):
        response_data  = []
        partly_sales_details = ErpEstimationSalesDetails.objects.filter(estimation_id=obj['estimation_id'],is_partial_sale = 1)
        partly_sales_details = ErpEstimationSalesDetailsSerializer(partly_sales_details, many=True).data
        partly_sold_pcs = partly_sold_grosswt = partly_sold_netwt = partly_sold_leswt = partly_sold_diawt = partly_sold_stnwt = partly_sold_otherwt=0
        for partly in partly_sales_details:
            queryset = ErpTagging.objects.filter(tag_id=partly["tag_id"]).get()
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

            balance_wt = float(queryset.tag_gwt) - float(sold_grosswt) - float(partly["gross_wt"])
            # if(balance_wt > 0):
            #     output=serializer.data
            partly.update({
                "balance_gross_wt" : float(queryset.tag_gwt) - float(sold_grosswt) - float(partly["gross_wt"]),
                "balance_net_wt" : float(queryset.tag_nwt) - float(sold_netwt) - float(partly["net_wt"]),
                "balance_less_wt" : float(queryset.tag_lwt) - float(sold_leswt) - float(partly["less_wt"]),
                "balance_dia_wt" : float(queryset.tag_dia_wt) - float(sold_diawt) - float(partly["dia_wt"]),
                "balance_stn_wt" : float(queryset.tag_stn_wt) - float(sold_stnwt) - float(partly["stone_wt"]),
                "balance_other_metal_wt" : float(queryset.tag_other_metal_wt) - float(sold_otherwt) - float(partly["other_metal_wt"]),
                "tag_gross_wt" : float(queryset.tag_gwt),
                "tag_net_wt" : float(queryset.tag_nwt),
                "tag_less_wt" : float(queryset.tag_lwt),
                "tag_dia_wt" : float(queryset.tag_dia_wt),
                "tag_stn_wt" : float(queryset.tag_stn_wt),
                "tag_other_metal_wt" : float(queryset.tag_other_metal_wt),
            })
            partly_sold_pcs += float(partly["balance_gross_wt"])
            partly_sold_grosswt += float(partly["balance_gross_wt"])
            partly_sold_netwt += float(partly["balance_net_wt"])
            partly_sold_leswt += float(partly["balance_less_wt"])
            partly_sold_diawt += float(partly["balance_dia_wt"])
            partly_sold_stnwt += float(partly["balance_stn_wt"])
            partly_sold_otherwt += float(partly["balance_other_metal_wt"])
                # "stone_details" : balance_stone_detail,
                # "other_metal_details":balance_other_detail,
            if (balance_wt):
                response_data.append(partly)
            # response_data['partly_sold_otherwt'] = format(partly_sold_otherwt, '.3f')
            # response_data['partly_sold_grosswt'] = format(partly_sold_grosswt, '.3f')
            # response_data['partly_sold_netwt'] = format(partly_sold_netwt, '.3f')
            # response_data['partly_sold_leswt'] = format(partly_sold_leswt, '.3f')
            # response_data['partly_sold_diawt'] = format(partly_sold_diawt, '.3f')
            # response_data['partly_sold_stnwt'] = format(partly_sold_stnwt, '.3f')
        
        return response_data
    
class ErpEstimationApprovalView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    queryset = ErpEstimation.objects.all()
    serializer_class = ErpEstimationSerializer
    
    
    def post(self, request, *args, **kwargs):
        est_id = request.data.get('est_id')
        is_approved = request.data.get('is_approved')
        estDetails = request.data.get('estDetails')
        sales_details = request.data.get('sales_details')

        if not est_id:
            return Response({"message": "Estimation id is missing."}, status=status.HTTP_400_BAD_REQUEST)
        if(is_approved == 1):
            obj = ErpEstimation.objects.filter(estimation_id = est_id).update(is_approved=is_approved,round_off = estDetails['round_off'],net_amount = estDetails['net_amount'],
                                                                              total_discount_amount = estDetails['total_discount_amount'],sales_amount = estDetails['sales_amount'],
                                                                              approved_by=request.user.pk,
                                                                              approved_on=datetime.now(tz=timezone.utc))
            for item in sales_details:
                sales_instance = ErpEstimationSalesDetails.objects.get(pk=item['est_item_id'])
                serializer = ErpEstimationSalesDetailsSerializer(sales_instance, data=item, partial=True)
                if serializer.is_valid(raise_exception=True):
                   serializer.save()
            # sio.emit('estimation_approved')
            # sio.emit('update_notification')
            print("Emitted estimation_approved event to socket server!")
        else:
            obj = ErpEstimation.objects.filter(estimation_id = est_id).update(is_approved=is_approved)
            # sio.emit('estimation_approved')
            # sio.emit('update_notification')
            print("Emitted estimation_approved event to socket server!")

        # est_serializer = ErpEstimationSerializer(obj)
        return Response({"message":f"Estimation {'Approved' if is_approved == 1 else 'Rejected'} successfully."},status=status.HTTP_200_OK)


class ErpEstimationApprovalPrint(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpEstimation.objects.all()
    serializer_class = ErpEstimationSerializer
    
    def generate_approval_print(self, net_amount, est_no, est_id, sign_image,firstname, request):
        print_obj = {}
        totals = defaultdict(float)
        
        # code = (str(lot_code) + "-" +str(data['id_lot_inward_detail']))
        # id = data['id_lot_inward_detail']
        save_dir = os.path.join(settings.MEDIA_ROOT, f'estimation/qr/{est_id}')
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(est_no)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        qr_path = os.path.join(save_dir, 'qrcode.png')
        qr_img.save(qr_path)
        sign_image_path = None
        if sign_image!=None:
            sign_image_name = os.path.basename(sign_image)  # Extract file name from original path
            sign_image_path = os.path.join(settings.MEDIA_ROOT, f'images/employees/signature', sign_image_name)
        # print(qr_path)
        # print(sign_image_path)
        
        print_obj.update({
            "estimation_no":est_no,
            "final_amount": f"{net_amount:.2f}",
            "employee_signature":sign_image_path,
            "qr_path":qr_path,
            "firstname":firstname,
        })
        template = get_template('estimation_approval_temp.html')
        html = template.render({'data': print_obj})
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        save_pdf_dir = os.path.join(settings.MEDIA_ROOT, f'estimation_approval/{est_id}')
        if not os.path.exists(save_pdf_dir):
            os.makedirs(save_pdf_dir)
        pdf_path = os.path.join(save_pdf_dir, 'estimation.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        pdf_path = request.build_absolute_uri(settings.MEDIA_URL +f'estimation_approval/{est_id}/estimation.pdf')
        return pdf_path
    
    def get(self, request, *args, **kwargs):
        est_id = kwargs.get('pk')
        print(est_id)
        print_obj = ErpEstimation.objects.filter(estimation_id=est_id).first()
        employee_query = Employee.objects.filter(user = print_obj.approved_by.pk).first()
        employee_seri = EmployeeSerializer(employee_query)
        # print(employee_seri.data)
        pdf_path = self.generate_approval_print(print_obj.net_amount,print_obj.est_no,
                                                print_obj.pk,
                                                employee_seri.data['signature'],
                                                employee_seri.data['firstname'], 
                                                request)
        return Response({"pdf_url":pdf_path}, status=status.HTTP_200_OK)

class ErpEstimationStockTransferAPIView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    queryset = ErpEstimation.objects.all()
    serializer_class = ErpEstimationSerializer

    def post(self, request, *args, **kwargs):
        try:
            est_no = request.data.get('est_no')
            id_branch = request.data.get('id_branch')
            if not est_no:
                return Response({"error": "Estimation No is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not id_branch:
                return Response({"error": "Estimation Branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(id_branch)
            queryset = ErpTagging.objects.raw(F"""SELECT tag.* FROM erp_estimation est
                        LEFT JOIN erp_estimation_sales_details d ON d.estimation_id_id = est.estimation_id
                        LEFT JOIN erp_tagging tag ON tag.tag_id = d.tag_id_id
                        Where tag.tag_status_id = 1 and tag.tag_id is NOT NULL and est.entry_date = "{entry_date}" and est.est_no = {est_no}  and est.id_branch_id = {id_branch} and tag.tag_current_branch_id = {id_branch} """)
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
            if(serializer.data):
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid Estimation No"}, status=status.HTTP_400_BAD_REQUEST)

        except ErpTagging.DoesNotExist:
            return Response({"message": "Invalid Estimation No"}, status=status.HTTP_400_BAD_REQUEST)


class ErpEstimationTagSearch(generics.GenericAPIView):

    permission_classes = [IsSuperuserOrEmployee | IsCustomerUser]
    serializer_class = ErpTaggingSerializer

    def get(self, request, *args, **kwargs):
        tag_code = request.query_params.get('tag_code')
        id_branch = request.query_params.get('id_branch')
        if (not tag_code):
            return Response({"message": "Tag code is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not id_branch:
            return Response({"message": "Branch is required"}, status=status.HTTP_400_BAD_REQUEST)
        is_sub_design_req = RetailSettings.objects.get(name='is_sub_design_req').value
        
        try: 
            queryset = ErpTagging.objects.filter(tag_code=tag_code)
            queryset = queryset.filter(tag_current_branch=id_branch,tag_status=1,order_tag__detail_id__isnull=True).get()
            serializer = ErpTaggingSerializer(queryset)
            mc_va_settings_queryset = CustomerMakingAndWastageSettings.objects.filter(id_product = queryset.tag_product_id.pro_id,id_design = queryset.tag_design_id.id_design,purity = queryset.tag_purity_id.id_purity)
            if int(is_sub_design_req) == 1:
                mc_va_settings_queryset = mc_va_settings_queryset.filter(sub_design_id = queryset.tag_sub_design_id.id_sub_design)
            settings = mc_va_settings_queryset.first()
            size_name = ''
            if settings and settings.id_weight_range:
                mc_va_settings_queryset = mc_va_settings_queryset.filter(
                    id_weight_range__from_weight__lte=queryset.tag_gwt,
                    id_weight_range__to_weight__gte=queryset.tag_gwt
                ).first()
            mc_va_settings_serializer = CustomerMakingAndWastageSettingsMappingSerializer(
            mc_va_settings_queryset, many=True)
            mc_va_settings = mc_va_settings_serializer.data
            stone_amount = other_metal_amount = other_charges_amount = 0
            formatted_data = convert_tag_to_formated_data(serializer.data)
            for stones in serializer.data['stone_details']:
                stone_amount += float(stones.get("stone_amount",0))
            for other in serializer.data['other_metal_details']:
                other_metal_amount += float(other.get("other_metal_cost",0))
            for charge in serializer.data['charges_details']:
                other_charges_amount += float(charge.get("charges_amount",0))


            product_details = Product.objects.get(pro_id = serializer.data['tag_product_id'])
            if serializer.data['size']!=None:
                size = Size.objects.get(id_size=serializer.data['size'])
                size_name = size.name
            cat_id = product_details.cat_id
            metal_rate_type = RetailSettings.objects.get(name='metal_rate_type').value
            rate_per_gram = 0
            if int(metal_rate_type)==1:
                cat_pur_rate = CategoryPurityRate.objects.filter(category = cat_id, purity = serializer.data['tag_purity_id']).first()
                rate_per_gram =cat_pur_rate.rate_per_gram if cat_pur_rate else 0
            else:
                cat_pur_rate = metalRatePurityMaster.objects.filter(id_metal = queryset.tag_product_id.id_metal.pk,id_purity = serializer.data['tag_purity_id']).first()
                metal_rate = MetalRates.objects.latest('rate_id')
                field_name = MetalRates._meta.get_field(cat_pur_rate.rate_field)
                rate_value = field_name.value_from_object(metal_rate)
                rate_per_gram = rate_value
            mc_calc_type = product_details.mc_calc_type
            wastage_calc_type = product_details.wastage_calc_type
            min_mc_value = 0
            min_va_value = 0
            if mc_va_settings:
                mc_calc_type = mc_va_settings.mc_type
                wastage_calc_type = mc_va_settings.va_type
                min_mc_value = mc_va_settings.min_mc_value
                min_va_value = mc_va_settings.min_va_value
                if float(formatted_data['mc_value']) < float(mc_va_settings.min_mc_value):
                    formatted_data['mc_value'] = mc_va_settings.max_mc_value
                if float(formatted_data['wastage_percentage']) < float(mc_va_settings.min_va_value):
                    formatted_data['wastage_value'] = mc_va_settings.max_va_value

            formatted_data.update({
                "discount_amount": 0,
                "invoice_type" : 1,
                "settings_billling_type":0,
                "tax_type" : product_details.tax_type,
                "tax_percentage": product_details.tax_id.tax_percentage,
                "mc_calc_type": mc_calc_type,
                "wastage_calc_type": wastage_calc_type,
                "sales_mode": product_details.sales_mode,
                "fixwd_rate_type": product_details.fixed_rate_type,
                "productDetails":[],
                "stone_details": serializer.data['stone_details'],
                "other_metal_details": serializer.data['other_metal_details'],
                "charges_details":serializer.data['charges_details'],
                "pure_wt" : formatted_data['pure_wt'],
                "purchase_va" : formatted_data['purchase_va'],
                "other_charges_amount" : other_charges_amount,
                "other_metal_amount" : other_metal_amount,
                "stone_amount" : stone_amount,
                "rate_per_gram": rate_per_gram ,
                "id_size":serializer.data['size'],
                "size_name":size_name,
                "min_mc_value": min_mc_value,
                "min_va_value": min_va_value,
            })
            

            item_cost = calculate_sales_itemcost(formatted_data)
            formatted_data.update({
                "item_cost": item_cost['item_cost'],
                "taxable_amount": item_cost['taxable_amount'],
                "cgst": item_cost['cgst'],
                "sgst": item_cost['sgst'],
                "igst": item_cost['igst'],
                "total_mc_value": item_cost['total_mc_value'],
                "discount_amount": item_cost['discount_amount'],
                "wastage_wt": item_cost['wastage_wt'],
            })

            return Response({"data":formatted_data,"status":True}, status=status.HTTP_200_OK)
        
        except ErpTagging.DoesNotExist:
            try:
                if tag_code :
                   queryset = ErpTagging.objects.filter(tag_code=tag_code).get()
               
                if queryset.tag_status == 1:
                    if queryset.order_tag:
                       return Response({"message": "Tag Reserved For Order","status":False}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                       return Response({"message": "Tag not found in this branch","status":False}, status=status.HTTP_400_BAD_REQUEST)
                
                elif queryset.tag_status == 2:
                    return Response({"message": "Tag is Sold Out","status":False}, status=status.HTTP_400_BAD_REQUEST)
                elif queryset.tag_current_branch != id_branch:
                    return Response({"message": "Tag not found in this branch","status":False}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": f"Tag is {queryset.tag_status.name}","status":False}, status=status.HTTP_400_BAD_REQUEST)

                
            except ErpTagging.DoesNotExist:
                return Response({"message": "Invalid Tag"}, status=status.HTTP_400_BAD_REQUEST)
            
    def post(self, request, *args, **kwargs):
        tag_details = request.data.get('tag_details')
        is_sub_design_req = RetailSettings.objects.get(name='is_sub_design_req').value
        if (not tag_details):
            return Response({"message": "Tag Details is required"}, status=status.HTTP_400_BAD_REQUEST)
        for tag in tag_details:
            product_details = Product.objects.get(pro_id = tag['id_product'])
            mc_va_settings_queryset = CustomerMakingAndWastageSettings.objects.filter(id_product = tag['id_product'],id_design = tag['id_design'],purity = tag['id_purity'])
            if int(is_sub_design_req) == 1:
                mc_va_settings_queryset = mc_va_settings_queryset.filter(sub_design_id = tag['id_sub_design'])
            settings = mc_va_settings_queryset.first()
            if settings and settings.id_weight_range:
                mc_va_settings_queryset = mc_va_settings_queryset.filter(
                    id_weight_range__from_weight__lte= tag['gross_wt'],
                    id_weight_range__to_weight__gte= tag['gross_wt']
                ).first()
            mc_va_settings_serializer = CustomerMakingAndWastageSettingsMappingSerializer(
            mc_va_settings_queryset, many=True)
            mc_va_settings = mc_va_settings_serializer.data
            stone_amount = other_metal_amount = other_charges_amount = 0
            for stones in tag['stone_details']:
                stone_amount += float(stones.get("stone_amount",0))
            for other in tag['other_metal_details']:
                other_metal_amount += float(other.get("other_metal_cost",0))
            for charge in tag['charges_details']:
                other_charges_amount += float(charge.get("charges_amount",0))
            cat_id = product_details.cat_id
            metal_rate_type = RetailSettings.objects.get(name='metal_rate_type').value
            rate_per_gram = 0
            if int(metal_rate_type)==1:
                cat_pur_rate = CategoryPurityRate.objects.filter(category = cat_id, purity = tag['id_purity']).first()
                rate_per_gram =cat_pur_rate.rate_per_gram if cat_pur_rate else 0
            else:
                cat_pur_rate = metalRatePurityMaster.objects.filter(id_metal = product_details.id_metal.pk,id_purity = tag['id_purity']).first()
                metal_rate = MetalRates.objects.latest('rate_id')
                field_name = MetalRates._meta.get_field(cat_pur_rate.rate_field)
                rate_value = field_name.value_from_object(metal_rate)
                rate_per_gram = rate_value
            mc_calc_type = product_details.mc_calc_type
            wastage_calc_type = product_details.wastage_calc_type
            min_mc_value = 0
            min_va_value = 0
            if settings:
                mc_calc_type = settings.mc_type
                wastage_calc_type = settings.va_type
                min_mc_value = settings.min_mc_value
                min_va_value = settings.min_va_value
                if float(tag['mc_value']) < float(settings.min_mc_value):
                    tag['mc_value'] = settings.max_mc_value
                if float(tag['wastage_percentage']) < float(settings.min_va_value):
                    tag['wastage_value'] = settings.max_va_value
            tag.update({
                "discount_amount": 0,
                "invoice_type" : 1,
                "settings_billling_type":0,
                "tax_type" : product_details.tax_type,
                "tax_percentage": product_details.tax_id.tax_percentage,
                "mc_calc_type": mc_calc_type,
                "wastage_calc_type": wastage_calc_type,
                "sales_mode": product_details.sales_mode,
                "fixwd_rate_type": product_details.fixed_rate_type,
                "productDetails":[],
                "other_charges_amount" : other_charges_amount,
                "other_metal_amount" : other_metal_amount,
                "stone_amount" : stone_amount,
                "rate_per_gram": rate_per_gram ,
                "min_mc_value": min_mc_value,
                "min_va_value": min_va_value,
            })
            item_cost = calculate_sales_itemcost(tag)
            tag.update({
                "item_cost": item_cost['item_cost'],
                "taxable_amount": item_cost['taxable_amount'],
                "cgst": item_cost['cgst'],
                "sgst": item_cost['sgst'],
                "igst": item_cost['igst'],
                "total_mc_value": item_cost['total_mc_value'],
                "discount_amount": item_cost['discount_amount'],
                "wastage_wt": item_cost['wastage_wt'],
            })
        return Response({"data":tag_details}, status=status.HTTP_200_OK)
        

def calculate_sales_itemcost(data):
    item_cost = 0
    total_mc_value = 0
    taxAmount = 0
    cgst = 0
    sgst = 0
    igst = 0
    item_rate = 0
    pieces = data['pieces']
    gross_wt = data['gross_wt']
    net_wt = data['net_wt']
    pure_wt = data['pure_wt']
    wastage_wt = data['wastage_wt']
    wastage_percentage = data['wastage_percentage']
    mc_type = data['mc_type']
    mc_value = data['mc_value']
    total_mc_value = data['total_mc_value']
    flat_mc_value = data['flat_mc_value']
    rate_per_gram = data['rate_per_gram']
    tax_percentage = data['tax_percentage']
    tax_type = data['tax_type']
    stone_amount = data['stone_amount']
    other_metal_amount = data['other_metal_amount']
    other_charges_amount = data['other_charges_amount']
    discount_amount = data['discount_amount']
    sell_rate = data['sell_rate']
    mc_calc_type = data['mc_calc_type']
    wastage_calc_type = data['wastage_calc_type']
    sales_mode = data['sales_mode']
    fixwd_rate_type = data['fixwd_rate_type']
    invoice_type = data['invoice_type']
    delivery_location = data.get("delivery_location",1)
    if(wastage_calc_type ==1):
        wastage_wt = float(float(float(gross_wt)*float(wastage_percentage))/100); #Based on Gross weight
    else:
        wastage_wt = float(float(float(net_wt)*float(wastage_percentage))/100); # Based on net weight
    
    if(mc_calc_type==1):
        total_mc_value = float( float(gross_wt)*float(mc_value) if mc_type==1  else float(pieces)*float(mc_value))
    else:
        total_mc_value = float(float(net_wt)*float(mc_value) if mc_type==1 else float(pieces)*float(mc_value))
    item_rate = 0
    if(int(sales_mode) == 1):
        if(int(invoice_type)==2):
            
            item_rate = (float(float(pure_wt))*float(rate_per_gram))
        else:
            item_rate = (float(float(net_wt)+float(wastage_wt))*float(rate_per_gram))
        
    else:
        if(int(fixwd_rate_type)==2):
            item_rate = sell_rate
        else:
            item_rate = float(float(sell_rate)*float(net_wt))
  
    if(float(flat_mc_value)>0):
        total_mc_value = float(flat_mc_value)+float(total_mc_value)
    
    taxable_amount = float(float(item_rate)+float(total_mc_value)+float(other_metal_amount)+float(stone_amount)+float(other_charges_amount)-float(discount_amount))

    if(tax_type!='' and tax_type!=0 and tax_percentage>0):
        if(tax_type==1): #Inclusive of Tax
            taxAmount = calculate_inclusive_tax(taxable_amount,tax_percentage)
            item_cost = float(taxable_amount)
            taxable_amount = float(float(taxable_amount)-float(taxAmount))
        else: #Exclusive of tax
            taxAmount = calculate_exclusive_tax (taxable_amount,tax_percentage)
            item_cost = float(float(taxAmount)+float(taxable_amount))
        
        if(taxAmount>0):
            cgst = float(taxAmount/2)
            sgst = float(taxAmount/2)
            
            
        
    else:
        item_cost = taxable_amount
    
    return {
        "wastage_wt":format(wastage_wt,'.3f'),
        "item_cost": format(item_cost,'.2f'),
        "taxAmount":format(taxAmount,'.2f'),
        "taxable_amount":format(taxable_amount,'.2f'),
        "cgst":format(cgst,'.2f'),
        "sgst":format(sgst,'.2f'),
        "igst":format(igst,'.2f'),
        "total_mc_value":format(total_mc_value,'.2f'),
        "discount_amount":format(discount_amount,'.2f'),
    }


def  calculate_inclusive_tax(taxable_amount,taxPercentage):
    amt_without_gst = (float(taxable_amount)*100)/(100+float(taxPercentage))
    inclusiveTaxAmount = float(float(taxable_amount)- float(amt_without_gst))
    return inclusiveTaxAmount

def  calculate_exclusive_tax(taxable_amount,taxPercentage):
    exclusiveTaxAmount = float(float(float(taxable_amount)*float(taxPercentage))/100)
    return exclusiveTaxAmount


class ErpCalculateOldMetalView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        
        item_details = request.data.get('purchase_details')
        updated_items = []
        if not item_details:
            return Response({"message": "Item details are required"}, status=status.HTTP_400_BAD_REQUEST)
        for item in item_details:
            item_cost = 0
            gross_weight = item['gross_wt']
            net_weight = item['net_wt']
            rate_per_gram = item['rate_per_gram']
            touch = item['touch']

            try:
                pure_weight = round(float(net_weight) * float(touch) / 100, 3)
            except (ValueError, TypeError):
                pure_weight = 0.0

            calculation_type = RetailSettings.objects.get(name='old_metal_calculation').value

            try:
                if calculation_type == 3:
                    item_cost = round(float(gross_weight) * float(rate_per_gram), 2)
                elif calculation_type == 2:
                    item_cost = round(float(pure_weight) * float(rate_per_gram), 2)
                else:
                    item_cost = round(float(net_weight) * float(rate_per_gram), 2)
            except (ValueError, TypeError):
                item_cost = 0.0

            item['item_cost'] = item_cost
            item['pure_weight'] = pure_weight
            updated_items.append(item)
        return Response({"data": updated_items}, status=status.HTTP_200_OK)
    
class ErpEstimationSearchAPIView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    queryset = ErpEstimation.objects.all()
    serializer_class = ErpEstimationSerializer

    def post(self, request, *args, **kwargs):
        try:
            est_no = request.data.get('est_no')
            id_branch = request.data.get('id_branch')
            est_date = request.data.get('est_date')
            if not est_no:
                return Response({"error": "Estimation No is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not id_branch:
                return Response({"error": "Estimation Branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not est_date:
                return Response({"error": "Estimation Date is missing."}, status=status.HTTP_400_BAD_REQUEST)

            obj = ErpEstimation.objects.filter(est_no = est_no ,id_branch = id_branch,entry_date = est_date).get()
            est_serializer = ErpEstimationSerializer(obj)
            data = est_serializer.data
            data['is_editable'] = 1
            invoice_no = []
            queryset_sales = ErpInvoice.objects.filter(erp_invoice_id=data['invoice_id'],invoice_status=1,setting_bill_type = 1 ).order_by('-erp_invoice_id')

            if(queryset_sales):
                inv_data = ErpInvoiceSerializer(queryset_sales,many=True,context={'invoice_no': True}).data
                for dat in inv_data:
                    if dat['inv_no'] :
                        data['is_editable'] = 0
                        erp_invoice_id = dat['erp_invoice_id']
                        invoice_no.append(dat['inv_no']['invoice_no'])
            if invoice_no:
                data['erp_invoice_id'] = erp_invoice_id
                data['invoice_no'] = ", ".join(set(invoice_no))
            return Response([data], status=status.HTTP_200_OK)


        except ErpEstimation.DoesNotExist:
            return Response({"message": "Invalid Estimation No"}, status=status.HTTP_400_BAD_REQUEST)