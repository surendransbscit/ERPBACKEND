from django.shortcuts import render
from django.http import HttpResponse, request, Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import datetime, timedelta, date
from django.db import transaction , IntegrityError,DatabaseError,OperationalError
from django.db.models import  Sum, F, ExpressionWrapper, DecimalField,PositiveIntegerField,Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from utilities.utils import format_date,format_with_decimal
from utilities.constants import FILTERS
from utilities.pagination_mixin import PaginationMixin
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
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee,isSuperuser,IsSuperuserOrEmployee
from collections import defaultdict
from core.views  import get_reports_columns_template

#view

from retailmasters.views import BranchEntryDate
from inventory.views import generate_lot_code,insert_lot_details
from retaildashboard.views import execute_raw_query
from reports.views import get_supplier_openning_details
from utilities.utils import generate_query_result

# model
from .models import (ErpPurchaseEntry,ErpPurchaseEntryDetails,ErpPurchaseStoneDetails,ErpPurchaseOtherMetal,ErpSupplierPayment,ErpAccountStockProcess,ErpSupplierRateCut,ErpCustomerRateCut,ErpSupplierRateCutAndMetalIssue,ErpSupplierPaymentDetails,ErpSupplierPaymentModeDetail,
                     ErpPurchaseIssueReceipt,ErpPurchaseIssueReceiptDetails,ErpPurchaseIssueReceiptOtherMetal,ErpPurchaseIssueReceiptStoneDetails,ErpSupplierMetalIssue,ErpCustomerPayment,ErpCustomerPaymentDetails,ErpCustomerPaymentModeDetail,
                     ErpSupplierMetalIssueDetails, ErpPurchaseReturnStoneDetails, ErpPurchaseReturnDetails, ErpPurchaseReturn,ErpPurchaseEntryChargesDetails)
from employees.models import (Employee)
from retailmasters.models import (Branch,FinancialYear,Uom,Company)
from retailcataloguemasters.models import (Product,Design,SubDesign)
from retailsettings.models import (RetailSettings)
from billing.models import ErpInvoiceSalesDetails,ErpInvoiceOldMetalDetails,ErpInvoiceStoneDetails,ErpInvoiceSalesReturn,ErpInvoice,ErpInvoiceOtherMetal
from inventory.models import ErpTaggingStone,ErpTagOtherMetal,ErpTagging
#serializers

from .serializers import (ErpPurchaseEntrySerializer,ErpPurchaseEntryDetailsSerializer,ErpPurchaseStoneDetailsSerializer,ErpInvoiceItemChargesSerializer,ErpSupplierPaymentDetailsSerializer,
                          ErpCustomerPaymentSerializer,ErpCustomerPaymentDetailsSerializer,ErpCustomerPaymentModeDetailSerializer,ErpSupplierRateCutAndMetalIssueSerializer,
                          ErpPurchaseOtherMetalSerializer,ErpPurchaseIssueReceiptOtherMetalSerializer,ErpSupplierPaymentSerializer,ErpSupplierPaymentModeDetailSerializer,
                          ErpPurchaseIssueReceiptStoneDetailsSerializer,ErpPurchaseIssueReceiptSerializer,ErpPurchaseIssueReceiptDetailsSerializer,ErpSupplierMetalIssueDetailsSerializer,
                          ErpSupplierMetalIssueSerializer,ErpSupplierRateCutSerializer,ErpAccountStockProcessSerializer,ErpAccountStockProcessDetailsSerializer,ErpSupplierAdvanceAdjSerializer,
                          ErpPurchaseReturnStoneDetailsSerializer, ErpPurchaseReturnDetailsSerializer, ErpPurchaseReturnSerializer,ErpSupplierAdvanceSerializer,
                          ErpCustomerRateCutSerializer,ErpPurchaseEntryChargesSerializer)

from inventory.serializers import ErpTaggingSerializer,ErpLotInwardSerializer,ErpLotInwardNonTagStoneSerializer,ErpLotInwardNonTagSerializer,ErpTagStoneSerializer,ErpTagOtherMetalSerializer,ErpTaggingLogSerializer
from billing.serializers import ErpInvoiceStoneDetailsSerializer,ErpInvoiceSerializer,ErpInvoiceOtherMetalSerializer,ErpInvoiceOldMetalDetailsSerializer,ErpInvoiceSalesDetailsSerializer


#constant
from .constants import (ACTION_LIST,PURCHASE_ENTRY_COLUMN_LIST,PURCHASE_ISSUE_COLUMN_LIST,SUPPLIER_PAYMENT_ACTION_LIST,SUPPLIER_PAYMENT_COLUMN_LIST,
                        PURCHASE_ISSUE_ACTION_LIST,METAL_ISSUE_ACTION_LIST,METAL_ISSUE_COLUMN_LIST,
                        PURCHASE_RETURN_COLUMN_LIST)

ISSUE_STATUS_COLOUR = [
    {"status": 0, "status_color": "primary"},
    {"status": 1, "status_color": "success"},
    {"status": 2, "status_color": "danger"},
]

def get_status_color(status):
    color = next((item['status_color'] for item in ISSUE_STATUS_COLOUR if item['status'] == status), None)
    return color

class ErpPurchaseEntryCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def generate_ref_code(self, data,branch_code,fy,setting_bill_type):
        code = ''
        code_settings = RetailSettings.objects.get(name='purchase_entry_code_settings').value
        code_format = RetailSettings.objects.get(name='purchase_entry_code_format').value
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_code=None
        if code_settings == '0':#GENERATE CODE
            last_code=ErpPurchaseEntry.objects.filter(setting_bill_type=setting_bill_type).order_by('-id_purchase_entry').first()
        elif code_settings == '1':#GENERATE CODE WITH FY AND BRANCH
            last_code=ErpPurchaseEntry.objects.filter(setting_bill_type=setting_bill_type,id_branch=data['id_branch'],fin_year=fin_id).order_by('-id_purchase_entry').first()
        elif code_settings == '2':#GENERATE CODE WITH BRANCH
            last_code=ErpPurchaseEntry.objects.filter(setting_bill_type=setting_bill_type,id_branch=data['id_branch']).order_by('-id_purchase_entry').first()
        elif code_settings == '3':#GENERATE CODE WITH FY
            last_code=ErpPurchaseEntry.objects.filter(setting_bill_type=setting_bill_type,fin_year=fin_id).order_by('-id_purchase_entry').first()
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
        
        #code=code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code)

        return code
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                purchase_data = request.data
                purchase_details = request.data.get('item_details')
                charges_details = request.data.get('charges_details')
                is_qc_required = RetailSettings.objects.get(name='is_qc_required').value
                bill_setting_type = int(request.data.get('setting_bill_type',1))
                generate_lot = int(request.data.get('lot_generate',1))

                if not purchase_data:
                    return Response({"error": "Purchase data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if len(purchase_details)==0 and len(charges_details)==0:
                    return Response({"error": "Purchase Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(purchase_data['id_branch'])
                branch=Branch.objects.get(id_branch=purchase_data['id_branch'])
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                ref_no = self.generate_ref_code(purchase_data,branch.short_name,fy,bill_setting_type)
                purchase_data.update({"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": request.user.id,"auto_lot_generate":0 if int(is_qc_required)==1 else 1 })
                purchase_serializer = ErpPurchaseEntrySerializer(data = purchase_data)
                if purchase_serializer.is_valid(raise_exception=True):
                    purchase_serializer.save()
                    if len(purchase_details) > 0 :
                        purchase_item_details = self.insert_purchase_details(purchase_details,purchase_serializer.data['id_purchase_entry'])
                        if int(generate_lot) ==1:
                            lot_data = lot_generate({"id_branch":purchase_data['id_branch'],"id_supplier":purchase_data['id_supplier'],'setting_bill_type':bill_setting_type},request)
                            for itm in purchase_item_details:
                                itm.update({
                                    "purchase_entry_detail":itm['id_purchase_entry_detail']
                                })
                                if len(itm['stone_details']) > 0:
                                    for stn in itm['stone_details']:
                                        stn.update({
                                            "purchase_stn_detail":stn['id_purchase_stn_detail']
                                        })

                            insert_lot_details(purchase_item_details,lot_data['lot_date'],lot_data['lot_no'],lot_data['id_branch'],request)
                    
                    if purchase_data['is_rate_fixed']==1:
                        rate_cut = ErpPurchasePaymentCreateAPIView()
                        rate_cut_details = []
                        for itm_details in purchase_item_details:
                            rate_cut_data = {}
                            product_details = Product.objects.filter(pro_id=itm_details['id_product']).get()
                            rate_cut_data.update({
                                "rate_per_gram":itm_details['purchase_rate'],
                                "id_metal":product_details.id_metal.pk,
                                "amount":format(float(itm_details['pure_wt'])*float(itm_details['purchase_rate']),'.2f'),
                                "pure_wt":itm_details['pure_wt'],
                                "purchase_entry":purchase_serializer.data['id_purchase_entry'],
                                'setting_bill_type':bill_setting_type
                            })
                        rate_cut_details.append(rate_cut_data)
                        rate_cut.insert_rate_cut_details(rate_cut_details,purchase_data['id_supplier'],entry_date,fin_id,request.user.id)
                    
                    if len(charges_details) > 0:
                        for charge in charges_details:
                            charge.update({
                                'id_charges' : charge['selectedCharge'],
                                'charges_amount' : charge['amount'],
                                "id_purchase_entry": purchase_serializer.data['id_purchase_entry']
                            })
                            charge_serializer = ErpPurchaseEntryChargesSerializer(data=charge)
                            if(charge_serializer.is_valid(raise_exception=True)):
                                charge_serializer.save()
                            else:
                                return Response({"message":charge_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                    est_url = self.generate_print(purchase_serializer.data['id_purchase_entry'],request)
                    return Response({"message":"Purchase Entry Created Successfully.",'pdf_url': est_url['pdf_url'],"id_purchase_entry":purchase_serializer.data['id_purchase_entry'],"pdf_path":"purchase/purchase_entry/print",
                                     "print_data":est_url['response_data']}, status=status.HTTP_201_CREATED)
                return Response({"message":ErpPurchaseEntrySerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": f"A database error occurred:{e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self, request, *args, **kwargs):
        id_purchase_entry = self.kwargs.get('pk')
        est_url = self.generate_print(id_purchase_entry,request)
        # response_data = { 'pdf_url': est_url}
        response_data = { 'pdf_url': est_url['pdf_url'],
                         'response_data':est_url['response_data']}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
        
    def generate_print(self, id_purchase_entry,request):
        instance = ErpPurchaseEntry.objects.get(id_purchase_entry=id_purchase_entry)
        serializer = ErpPurchaseEntrySerializer(instance)
        data = serializer.data
        item_details = ErpPurchaseEntryDetails.objects.filter(purchase_entry=id_purchase_entry)
        item_details_serializer = ErpPurchaseEntryDetailsSerializer(item_details, many=True)
        charges_details = ErpPurchaseEntryChargesDetails.objects.filter(id_purchase_entry=id_purchase_entry)
        charges_details_serializer = ErpPurchaseEntryChargesSerializer(charges_details, many=True)
        comp = Company.objects.latest("id_company")
        total_charges_amount,total_dia_wt,total_stn_wt,total_net_wt,total_gross_wt,purchase_amount,total_pcs,total_less_wt,total_pure_wt = 0,0,0,0,0,0,0,0,0
        
        for item in item_details_serializer.data:
            stone_details = ErpPurchaseStoneDetails.objects.filter(purchase_entry_detail=item['id_purchase_entry_detail'])
            stone_details_serializer = ErpPurchaseStoneDetailsSerializer(stone_details, many=True)
            product_details = Product.objects.get(pro_id=item['id_product'])
            total_pcs += int(item['pieces'])
            total_gross_wt += float(item['gross_wt'])
            total_net_wt += float(item['net_wt'])
            total_pure_wt += float(item['pure_wt'])
            total_stn_wt += float(item['stone_wt'])
            total_dia_wt += float(item['dia_wt'])
            total_less_wt += float(item['less_wt'])
            purchase_amount += float(item['purchase_cost'])
            item.update({
                "stock_type":'Tagged' if product_details.stock_type==0 else 'Non Tag',
                "id_category":product_details.cat_id.id_category,
                "stone_details":stone_details_serializer.data,
            })
        for charges in charges_details_serializer.data:
           total_charges_amount += float(charges['charges_amount'])
        data['total_pcs'] = format(total_pcs, '.0f')
        data['total_gross_wt'] = format(total_gross_wt, '.3f')
        data['total_net_wt'] = format(total_net_wt, '.3f')
        data['total_pure_wt'] = format(total_pure_wt, '.3f')
        data['total_less_wt'] = format(total_less_wt, '.3f')
        data['total_stn_wt'] = format(total_stn_wt, '.3f')
        data['total_dia_wt'] = format(total_dia_wt, '.3f')
        data['total_pure_wt'] = format(total_pure_wt, '.3f')
        data['purchase_amount'] = format(purchase_amount, '.2f')
        data['charges_amount'] = format(total_charges_amount, '.2f')
        data['charges_details'] = charges_details_serializer.data
        data.update({
            "supplier_name":instance.id_supplier.supplier_name,
            "branch":instance.id_branch.name,
            "item_details": item_details_serializer.data if len(item_details_serializer.data) > 0 else [],
                    #  'company_detail': comp
                    'company_name':comp.company_name
                     })

        # save_dir = os.path.join(settings.MEDIA_ROOT, 'purchase_entry')
        # save_dir = os.path.join(save_dir, f'{id_purchase_entry}')
        # if not os.path.exists(save_dir):
        #     os.makedirs(save_dir)
        # template = get_template('purchase_entry_print.html')
        # html = template.render(data)
        # result = io.BytesIO()
        # pisa.pisaDocument(io.StringIO(html), result)
        # pdf_path = os.path.join(save_dir, 'purchase_entry.pdf')
        # with open(pdf_path, 'wb') as f:
        #     f.write(result.getvalue())
        # pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'purchase_entry/{id_purchase_entry}/purchase_entry.pdf')
        pdf_path = ''
        return {"response_data":data,
                "pdf_url":pdf_path}
        # return pdf_path

    def insert_purchase_details(self,purchase_details,purchase_entry):
        return_data =[]
        for purchase_item in purchase_details:
            purchase_item.update({"purchase_entry":purchase_entry})
            print(purchase_item)
            if (purchase_item['tax_id'])=="":
                purchase_item.update({"tax_id" : None, "tax_type" : 2})
            purchase_detail_serializer = ErpPurchaseEntryDetailsSerializer(data=purchase_item)
            if(purchase_detail_serializer.is_valid(raise_exception=True)):
                purchase_detail_serializer.save()
                stone_details=insert_other_details(purchase_item['stone_details'],ErpPurchaseStoneDetailsSerializer,{"purchase_entry_detail":purchase_detail_serializer.data['id_purchase_entry_detail']})
                other_metal_details=insert_other_details(purchase_item['other_metal_details'],ErpPurchaseOtherMetalSerializer,{"purchase_entry_detail":purchase_detail_serializer.data['id_purchase_entry_detail']})
                for charge in purchase_item['charges_details']:
                    charge.update({'id_charges' : charge['selectedCharge'],'charges_amount' : charge['amount'],"purchase_entry_detail": purchase_detail_serializer.data['id_purchase_entry_detail']})
                    charge_serializer = ErpInvoiceItemChargesSerializer(data=charge)
                    charge_serializer.is_valid(raise_exception=True)
                    charge_serializer.save()
                return_data.append({**purchase_item,**purchase_detail_serializer.data,'stone_details':stone_details,'other_metal_details':other_metal_details})
            else:
                tb = traceback.format_exc()
                return Response({"error":ErpPurchaseEntryDetailsSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            
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

class PurchaseEntryListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        try:
            po_no = request.query_params.get('po_no')
            fin_id = request.query_params.get('fin_id')
            issue_type = int(request.query_params.get('issue_type'))
            id_branch = request.query_params.get('id_branch')
            bill_setting_type = int(request.query_params.get('bill_setting_type',1))


            if( (not issue_type) or (not fin_id) or (not po_no) or (not id_branch) ):
                return Response({"error": "po_no,fin_id,issue_type,id_branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = ErpPurchaseEntry.objects.filter(setting_bill_type =bill_setting_type,fin_year=fin_id,ref_no=po_no,is_cancelled=False,id_branch = id_branch,is_approved = True,auto_lot_generate = False).get()
            serializer = ErpPurchaseEntrySerializer(queryset)
            if issue_type==1:
                detail = ErpPurchaseEntryDetails.objects.filter(purchase_entry=serializer.data['id_purchase_entry'])
            else:
                detail = ErpPurchaseEntryDetails.objects.filter(purchase_entry=serializer.data['id_purchase_entry'],is_halmarked=False)
            detail_serializer = ErpPurchaseEntryDetailsSerializer(detail,many=True)
            detail_data = detail_serializer.data
            item_details = []
            for item, instance in zip(detail_data,detail):
                print(item)
                gross_wt = float(item["gross_wt"])
                less_wt = float(item["less_wt"])
                net_wt = float(item["net_wt"])
                dia_wt = float(item["dia_wt"])
                stn_wt = float(item["stone_wt"])
                other_metal_wt = float(item["other_metal_wt"])
                pieces = float(item["pieces"])
                pure_wt = float(item["pure_wt"])
                stone=[]
                other_metal=[]


                stone_details_instance = ErpPurchaseStoneDetails.objects.filter(purchase_entry_detail=item['id_purchase_entry_detail'])
                stone_details = ErpPurchaseStoneDetailsSerializer(stone_details_instance, many=True).data

                for stn, stn_instance in zip(stone_details,stone_details_instance):
                    issued_stn_data = stn_instance.issue_receipt_stone.filter(issue_receipt_detail__issue_receipt__issue_type=issue_type,issue_receipt_detail__issue_receipt__status__in = [0,1])
                    stone_pcs = float(stn["stone_pcs"])
                    stone_wt = float(stn["stone_wt"])
                    pur_st_rate = float(stn["pur_st_rate"])
                    for stn_data in issued_stn_data:
                        stone_pcs -= float(stn_data.stone_pcs or 0)
                        stone_wt -= float(stn_data.stone_wt or 0)
                    stn.update({
                        "avail_piece": format(stone_pcs, '.3f'),
                        "avail_wt": format(stone_wt, '.3f'),
                        "piece": format(stone_pcs, '.3f'),
                        "weight": format(stone_wt, '.3f'),
                        "stone_rate": format(pur_st_rate, '.2f'),
                        "stone_amount": format(stone_wt, '.2f'),
                        "stone_name": stn_instance.id_stone.stone_name,
                    })
                    if(stone_pcs > 0 or stone_wt > 0):
                        stone.append(stn)

                other_metal_details_instance = ErpPurchaseOtherMetal.objects.filter(purchase_entry_detail=item['id_purchase_entry_detail'])
                other_metal_details = ErpPurchaseOtherMetalSerializer(other_metal_details_instance, many=True).data

                for other, other_instance in zip(other_metal_details,other_metal_details_instance):
                    issued_other_data = other_instance.issue_receipt_other_metal.filter(issue_receipt_detail__issue_receipt__issue_type=issue_type,issue_receipt_detail__issue_receipt__status__in = [0,1])
                    piece = float(other["piece"])
                    weight = float(other["weight"])
                    wastage_weight = float(other["wastage_weight"])
                    for metal_data in issued_other_data:
                        piece -= float(metal_data.piece or 0)
                        weight -= float(metal_data.weight or 0)
                    other.update({
                        "avail_piece": format(piece, '.3f'),
                        "avail_wt": format(weight, '.3f'),
                        "selectedCategory": other_instance.id_category.id_category,
                        "selectedPurity":other_instance.id_purity.id_purity,
                        'piece': (piece),
                        'ratePerGram': (other_instance.rate_per_gram),
                        'weight': (weight),
                        'amount': (other_instance.other_metal_cost),
                        'wastagePercentage':(other_instance.wastage_percentage),
                        'wastageWeight':(wastage_weight),
                        'mcValue':(other_instance.mc_value),
                        'mcType':other_instance.mc_type,
                        'cat_name':other_instance.id_category.cat_name,

                    })
                    if(piece > 0 or weight > 0):
                        other_metal.append(other)


                issued_data = instance.purchase_issue_detail.filter(issue_receipt__issue_type=issue_type,issue_receipt__status__in = [0,1])

                for data in issued_data:
                    gross_wt -= float(data.gross_wt or 0)
                    less_wt -= float(data.less_wt or 0)
                    net_wt -= float(data.net_wt or 0)
                    dia_wt -= float(data.dia_wt or 0)
                    stn_wt -= float(data.stone_wt or 0)
                    other_metal_wt -= float(data.other_metal_wt or 0)
                    pieces -= float(data.pieces or 0)
                    pure_wt -= float(data.pure_wt or 0)



                item.update({
                    "stone_details":stone,
                    "other_metal_details":other_metal,
                    "avail_stone_details":stone,
                    "avail_other_metal_details":other_metal,
                    "avail_gross_wt": format(gross_wt, '.3f'),
                    "avail_piece": format(pieces, '.0f'),
                    "avail_less_wt": format(less_wt, '.3f'),
                    "avail_net_wt": format(net_wt, '.3f'),
                    "avail_dia_wt": format(dia_wt, '.3f'),
                    "avail_stone_wt": format(stn_wt, '.3f'),
                    "avail_other_metal_wt": format(other_metal_wt, '.3f'),
                    "avail_pure_wt": format(pure_wt, '.3f'),
                    "gross_wt": format(gross_wt, '.3f'),
                    "pieces": format(pieces, '.0f'),
                    "less_wt": format(less_wt, '.3f'),
                    "net_wt": format(net_wt, '.3f'),
                    "dia_wt": format(dia_wt, '.3f'),
                    "stone_wt": format(stn_wt, '.3f'),
                    "other_metal_wt": format(other_metal_wt, '.3f'),
                    "pure_wt": format(pure_wt, '.3f'),
                    "purchase_entry_detail":item["id_purchase_entry_detail"],
                    "isChecked":True,
                })

                if(gross_wt > 0 or pieces > 0):
                    item_details.append(item)
            if(item_details):
                return Response(item_details)
            return Response({"message": "No Records Found"}, status=status.HTTP_400_BAD_REQUEST)
            
        except ErpPurchaseEntry.DoesNotExist:
            return Response({"message": "Po Details Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_branch = request.data.get('branch')
        id_branch = (id_branch) if id_branch != '' else 0
        bill_setting_type = int(request.data.get('bill_setting_type',2))

        code_format = RetailSettings.objects.get(name='purchase_entry_code_format').value

        lists = ErpPurchaseEntry.objects.annotate(
            total_gross_wt=Sum('purchase_details__gross_wt', filter=Q(purchase_details__gross_wt__isnull=False)),
            total_net_wt=Sum('purchase_details__net_wt', filter=Q(purchase_details__net_wt__isnull=False)),
            total_stn_wt=Sum('purchase_details__stone_wt', filter=Q(purchase_details__stone_wt__isnull=False)),
            total_dia_wt=Sum('purchase_details__dia_wt', filter=Q(purchase_details__dia_wt__isnull=False))
        ).values(
            'id_purchase_entry',
            'ref_no', 
            'id_branch__short_name',
            'fin_year__fin_year_code',
            'id_purchase_entry',
            'total_gross_wt', 
            'total_net_wt',
            'total_stn_wt',
            'total_dia_wt',
            'is_approved', 
            'entry_date',
            'id_supplier__supplier_name',
            'id_branch__name',
            'is_cancelled'
        ).order_by('-id_purchase_entry')
        if from_date and to_date:
            lists = lists.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            lists = lists.filter(id_branch__in=id_branch)
        if bill_setting_type == 0 or bill_setting_type == 1:
            lists = lists.filter(setting_bill_type=bill_setting_type)
        
        paginator, page = pagination.paginate_queryset(lists, request,None,PURCHASE_ENTRY_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,PURCHASE_ENTRY_COLUMN_LIST,request.data.get('path_name',''))
        
        for index,purchase in enumerate(page):
            code = (code_format
                    .replace('@branch_code@',  purchase['id_branch__short_name'])
                    .replace('@code@', purchase['ref_no'])
                    .replace('@fy_code@', purchase['fin_year__fin_year_code']))
            purchase['sno'] = index+1
            purchase['pk_id'] = purchase['id_purchase_entry']
            purchase['is_active'] = purchase['is_approved']
            purchase['ref_code'] = code
            purchase['status_name'] = ('UnApproved' if purchase['is_approved']==0 else 'Approved') if purchase['is_cancelled']==False else 'Cancelled'
            purchase['is_editable'] = (1 if purchase['is_approved']==0 else 0) if purchase['is_cancelled']==False else 0
            purchase['entry_date'] = format_date(purchase['entry_date'])
            purchase['total_gross_wt'] = format(purchase.get('total_gross_wt') or 0.0, '.3f')
            purchase['total_net_wt'] = format(purchase.get('total_net_wt') or 0.0, '.3f')
            purchase['total_stn_wt'] = format(purchase.get('total_stn_wt') or 0.0, '.3f')
            purchase['total_dia_wt'] = format(purchase.get('total_dia_wt') or 0.0, '.3f')
            purchase['is_cancelable'] = (True if purchase['is_approved']==0 else False)  if purchase['is_cancelled']==False else False


        
        print(paginator)
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        ACTION_LIST['is_edit_req'] = True
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

class PurchaseEntryEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = ErpPurchaseEntry.objects.all()
    serializer_class = ErpPurchaseEntrySerializer
    def get(self, request, *args, **kwargs):
        if ('approve' in request.query_params):
            obj = self.get_object()
            if(obj.is_approved == False and obj.is_cancelled == False):
                obj.is_approved = True
                obj.approved_by = self.request.user
                obj.approved_on =  datetime.now(tz=timezone.utc)
                obj.save()
                return Response({"message": "Purchase Entry Approved Successfully."}, status=status.HTTP_202_ACCEPTED)
            return Response({"message": "Purchase Entry Cannot Be Undo."}, status=status.HTTP_400_BAD_REQUEST)
        
        if ('touchUpdate' in request.query_params):
            ref_no = request.query_params.get('ref_no')
            fin_id = request.query_params.get('fin_id')
            id_branch = request.query_params.get('id_branch')
            bill_setting_type = request.query_params.get('bill_setting_type')
            if( (not fin_id) or (not ref_no) or (not id_branch) or (not bill_setting_type) ):
                return Response({"error": "ref_no,fin_id,id_branch,settings is missing."}, status=status.HTTP_400_BAD_REQUEST)
            obj = ErpPurchaseEntry.objects.filter(fin_year=fin_id,ref_no=ref_no,id_branch = id_branch,setting_bill_type = bill_setting_type).get()
        else :
            obj = self.get_object()
        serializer = ErpPurchaseEntrySerializer(obj)
        data = serializer.data
        item_details = ErpPurchaseEntryDetails.objects.filter(purchase_entry=data['id_purchase_entry'])
        item_details_serializer = ErpPurchaseEntryDetailsSerializer(item_details, many=True)
        for item in item_details_serializer.data:
            product_details = Product.objects.get(pro_id=item['id_product'])
            stone_details = ErpPurchaseStoneDetails.objects.filter(purchase_entry_detail=item['id_purchase_entry_detail'])
            stone_details = ErpPurchaseStoneDetailsSerializer(stone_details, many=True).data
            other_details = ErpPurchaseOtherMetal.objects.filter(purchase_entry_detail=item['id_purchase_entry_detail'])
            other_details = ErpPurchaseOtherMetalSerializer(other_details, many=True).data
            item.update({
                "stock_type":'Tagged' if int(product_details.stock_type)==0 else 'Non Tag',
                "product_name":Product.objects.get(pro_id=item['id_product']).product_name,
                "design_name":None if item['id_design']==None else Design.objects.get(id_design=item['id_design']).design_name,
                "sub_design_name":None if item['id_sub_design']==None else SubDesign.objects.get(id_sub_design=item['id_sub_design']).sub_design_name,
                "id_category":product_details.cat_id.id_category,
                "stone_details":stone_details,
                "other_metal_details":other_details
            })
        data.update({"item_details": item_details_serializer.data})
        return Response(data, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                purchase_entry = kwargs.get('pk')
                purchase_data = request.data
                item_details = request.data.get('item_details')
                is_delete_req =  int(request.data.get('is_delete_req',1))
                if not purchase_entry:
                    return Response({"error": "Purchase ID is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not purchase_data:
                    return Response({"error": "Purchase data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not item_details:
                    return Response({"error": "Purchase Details data is missing."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    purchase_instance = ErpPurchaseEntry.objects.get(pk=purchase_entry)
                except ErpPurchaseEntry.DoesNotExist:
                    return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)
                purchase_data.update({"updated_by": request.user.id,'updated_on': datetime.now(tz=timezone.utc)})
                serializer = ErpPurchaseEntrySerializer(purchase_instance, data=purchase_data, partial=True)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

                    if item_details:
                        if (is_delete_req == 1):
                            self.update_deleted_details(item_details, purchase_entry)

                        self.update_purchase_details(item_details, purchase_entry,serializer.data,request)

                    return Response({"message": "Purchase updated successfully."}, status=status.HTTP_200_OK)
                tb = traceback.format_exc()
                return Response({"error": serializer.errors,"traceback": tb }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": f"A database error occurred:{e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}", "traceback": tb }, status=status.HTTP_400_BAD_REQUEST)

    def update_deleted_details(self, item_details, purchase_entry):
        existing_items = ErpPurchaseEntryDetails.objects.filter(purchase_entry=purchase_entry)
        existing_item_map = {item.pk: item for item in existing_items}
        ids_to_delete = set(existing_item_map.keys())
        print(ids_to_delete)
        for detail in item_details:
            item_id = detail.get('id_purchase_entry_detail')
            if item_id:
                ids_to_delete.discard(item_id)
        if ids_to_delete:
            print('delete')
            print(ids_to_delete)
            ErpPurchaseEntryDetails.objects.filter(pk__in=ids_to_delete).delete()  

    def update_purchase_details(self, item_details,purchase_entry,lot_data,request):        
        for detail in item_details:
            item_id = detail.get('id_purchase_entry_detail')
            if item_id:
                try:
                    item_instance = ErpPurchaseEntryDetails.objects.get(pk=item_id)
                    serializer = ErpPurchaseEntryDetailsSerializer(item_instance, data=detail, partial=True)
                    print('insert')
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        update_other_details(detail.get('stone_details',[]),serializer.data['id_purchase_entry_detail'],ErpPurchaseStoneDetailsSerializer,'purchase_entry_detail','id_purchase_stn_detail')
                        update_other_details(detail.get('other_metal_details',[]),serializer.data['id_purchase_entry_detail'],ErpPurchaseOtherMetalSerializer,'purchase_entry_detail','id_purchase_other_metal')

                except ErpPurchaseEntryDetails.DoesNotExist:
                    print('update')
                    self.insert_purchase_details(detail,purchase_entry,lot_data,request)
            else:
                print('update')
                self.insert_purchase_details(detail,purchase_entry,lot_data,request)


    def insert_purchase_details(self,purchase_item,item_id,lot_data,request):
        purchase_item.update({"purchase_entry":item_id})
        purchase_detail_serializer = ErpPurchaseEntryDetailsSerializer(data=purchase_item)
        if(purchase_detail_serializer.is_valid(raise_exception=True)):
            purchase_detail_serializer.save()
            for stn in purchase_item['stone_details']:
                stn.update({"id_purchase_entry_detail":purchase_detail_serializer.data['id_purchase_entry_detail']})
                purchase_stone_serializer = ErpPurchaseStoneDetailsSerializer(data=stn)
                purchase_stone_serializer.is_valid(raise_exception=True)
                purchase_stone_serializer.save()
            other_metal_details=insert_other_details(purchase_item['other_metal_details'],ErpPurchaseOtherMetalSerializer,{"purchase_entry_detail":purchase_detail_serializer.data['id_purchase_entry_detail']})
            
    def post(self, request, *args, **kwargs):
        queryset = ErpPurchaseEntry.objects.get(id_purchase_entry= request.data['pk_id'])
        if(queryset.is_approved == False and queryset.is_cancelled == False):
            queryset.is_cancelled = True
            queryset.cancelled_by = self.request.user
            queryset.cancelled_on =  datetime.now(tz=timezone.utc)
            queryset.cancelled_reason =  request.data['cancel_reason']
            queryset.save()
            return Response({"message": "Purchase Entry Cancelled Successfully."}, status=status.HTTP_202_ACCEPTED)
        return Response({"message": "Purchase Entry Cannot Be Cancelled."}, status=status.HTTP_400_BAD_REQUEST)
def update_other_details(details, parent_id, serializer_class, parent_field,id,delete_req=True):

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

    if ids_to_delete and delete_req:
        serializer_class.Meta.model.objects.filter(pk__in=ids_to_delete).delete()


class PurchaseEntryItemDeleteView(generics.GenericAPIView):
    queryset = ErpPurchaseEntryDetails.objects.all()

    def delete(self, request, *args, **kwargs):
        id_purchase_entry_detail = request.query_params.get('id_purchase_entry_detail')

        if not id_purchase_entry_detail:
            return Response({"message": "Purchase Entry Detail ID is missing."},status=status.HTTP_400_BAD_REQUEST)

        try:
            purchase_entry_detail = self.queryset.filter(id_purchase_entry_detail=id_purchase_entry_detail).first()
            if not purchase_entry_detail:
                return Response({"message": "Purchase Entry Detail not found."},status=status.HTTP_404_NOT_FOUND)

            # Delete related records in sub-tables
            ErpPurchaseStoneDetails.objects.filter(purchase_entry_detail=id_purchase_entry_detail).delete()
            ErpPurchaseOtherMetal.objects.filter(purchase_entry_detail=id_purchase_entry_detail).delete()

            # Delete the main record
            purchase_entry_detail.delete()

            return Response(
                {"message": "Item and related entries deleted successfully."},
                status=status.HTTP_200_OK
            )
        except ProtectedError:
            return Response(
                {
                    "error_detail": [
                        "Purchase Entry Detail can't be deleted as it is in use."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ErpPurchaseIssueReceiptCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def generate_issue_no(self):
        code = ''
        last_code=ErpPurchaseIssueReceipt.objects.order_by('-id_issue_receipt').first()
        if last_code:
            last_code = last_code.issue_no
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
                purchase_data = request.data
                purchase_details = request.data.get('item_details')
                if not purchase_data:
                    return Response({"error": "Purchase Issue data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not purchase_details:
                    return Response({"error": "Purchase Issue Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                branch=Branch.objects.get(is_ho=1)
                purchase_data['id_branch'] = branch.id_branch
                entry_date = branch_date.get_entry_date(purchase_data['id_branch'])
                issue_no = self.generate_issue_no()
                purchase_data.update({"issue_date":entry_date,"issue_no":issue_no,"created_by": request.user.id})
                
                purchase_serializer = ErpPurchaseIssueReceiptSerializer(data = purchase_data)
                if purchase_serializer.is_valid(raise_exception=True):
                    purchase_serializer.save()
                    purchase_details = self.insert_purchase_issue_details(purchase_details,purchase_serializer.data['id_issue_receipt'])
                    est_url = self.generate_print(purchase_serializer.data['id_issue_receipt'],request)
                    return Response({"message":"Purchase Issue Receipt Created Successfully.","issue_no":purchase_serializer.data['issue_no'],'pdf_url': est_url['pdf_url'],"id_issue_receipt":purchase_serializer.data['id_issue_receipt'],"pdf_path":'purchase/qu_issue_receipt/print',
                                    "print_data":est_url['response_data']}, status=status.HTTP_201_CREATED)
                return Response({"message":ErpPurchaseEntrySerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self, request, *args, **kwargs):
        id_issue_receipt = self.kwargs.get('pk')
        est_url = self.generate_print(id_issue_receipt,request)
        # response_data = { 'pdf_url': est_url}
        response_data = {
                         'response_data':est_url['response_data']}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
        
        
    def generate_print(self,id_issue_receipt,request):
        instance = ErpPurchaseIssueReceipt.objects.get(id_issue_receipt = id_issue_receipt)
        Serializer = ErpPurchaseIssueReceiptSerializer(instance)
        data = Serializer.data
        item_details = ErpPurchaseIssueReceiptDetails.objects.filter(issue_receipt=id_issue_receipt)
        item_details_serializer = ErpPurchaseIssueReceiptDetailsSerializer(item_details, many=True)
        comp = Company.objects.latest("id_company")

        total_gross_wt = 0
        total_net_wt = 0

        total_gross_wt += float(data.get('gross_wt', 0) or 0)
        total_net_wt += float(data.get('net_wt', 0) or 0)

        for item in item_details_serializer.data:
            total_gross_wt += float(item.get('gross_wt', 0) or 0)
            total_net_wt += float(item.get('net_wt', 0) or 0)

        item_details_data = item_details_serializer.data + [{
        "is_summary": True,
        "total_gross_wt": format(total_gross_wt, '.3f'),
        "total_net_wt": format(total_net_wt, '.3f')
        }]
        
        # data.update({"branch":instance.id_branch.name,"employee":instance.issue_to_emp.firstname,
        #             "issue_no":instance.issue_no,"issue_date":format_date(instance.issue_date),'company_name':comp.company_name})
        
        custom_response_data = {
        "company_name": comp.company_name,
        "branch": instance.id_branch.name,
        "issue_no": instance.issue_no,
        "issue_date": format_date(instance.issue_date),
        "supplier_name": instance.issue_to_supplier.supplier_name if instance.issue_to_supplier else None,
        "emp_name": instance.issue_to_emp.firstname,
        "item_details": item_details_data
    }
        
        pdf_path = ''
        return {"response_data":custom_response_data,
                "pdf_url":pdf_path}

    def insert_purchase_issue_details(self,purchase_details,issue_receipt):
        return_data =[]
        for purchase_item in purchase_details:
            purchase_item.update({"issue_receipt":issue_receipt})
            # print(purchase_item,'purchase_item')
            purchase_detail_serializer = ErpPurchaseIssueReceiptDetailsSerializer(data=purchase_item)
            if(purchase_detail_serializer.is_valid(raise_exception=True)):
                purchase_detail_serializer.save()
                stone_details=insert_other_details(purchase_item['stone_details'],ErpPurchaseIssueReceiptStoneDetailsSerializer,{"issue_receipt_detail":purchase_detail_serializer.data['id_issue_receipt_detail']})
                other_metal_details=insert_other_details(purchase_item['other_metal_details'],ErpPurchaseIssueReceiptOtherMetalSerializer,{"issue_receipt_detail":purchase_detail_serializer.data['id_issue_receipt_detail']})
                return_data.append({**purchase_item,**purchase_detail_serializer.data,'stone_details':stone_details,'other_metal_details':other_metal_details})
            else:
                tb = traceback.format_exc()
                return Response({"error":ErpPurchaseIssueReceiptDetailsSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            
        return return_data



class ErpPurchaseIssueReceiptEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    queryset = ErpPurchaseIssueReceipt.objects.all()
    serializer_class = ErpPurchaseIssueReceiptSerializer
    def get(self, request, *args, **kwargs):
        obj = self.get_object()    
        serializer = ErpPurchaseIssueReceiptSerializer(obj)
        data = serializer.data
        item_details = ErpPurchaseIssueReceiptDetails.objects.filter(issue_receipt=data['id_issue_receipt'])
        item_details_serializer = ErpPurchaseIssueReceiptDetailsSerializer(item_details, many=True)
        for item in item_details_serializer.data:
            stone_details = ErpPurchaseIssueReceiptStoneDetails.objects.filter(issue_receipt_detail=item['id_issue_receipt_detail'])
            stone_details = ErpPurchaseIssueReceiptStoneDetailsSerializer(stone_details, many=True).data
            other_details = ErpPurchaseIssueReceiptOtherMetal.objects.filter(issue_receipt_detail=item['id_issue_receipt_detail'])
            other_details = ErpPurchaseIssueReceiptOtherMetalSerializer(other_details, many=True).data
            item.update({
                "stone_details":stone_details,
                "other_metal_details":other_details
            })
        data.update({"item_details": item_details_serializer.data})
        return Response(data, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                id_issue_receipt = kwargs.get('pk')
                purchase_data = request.data
                item_details = request.data.get('item_details')
                if not id_issue_receipt:
                    return Response({"error": "Purchase Issue Receipt ID is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not purchase_data:
                    return Response({"error": "Purchase Issue Receipt data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not item_details:
                    return Response({"error": "Purchase Issue Receipt Details is missing."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    purchase_instance = ErpPurchaseIssueReceipt.objects.get(pk=id_issue_receipt)
                except ErpPurchaseIssueReceipt.DoesNotExist:
                    return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)
                update_data={"status":1,"updated_by": request.user.id,'updated_on': datetime.now(tz=timezone.utc)}
                serializer = ErpPurchaseIssueReceiptSerializer(purchase_instance, data=update_data, partial=True)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

                    if item_details:
                        self.update_purchase_issue_details(item_details, id_issue_receipt,serializer.data,request)

                    return Response({"message": "Purchase Issue Receipt updated successfully."}, status=status.HTTP_200_OK)
                tb = traceback.format_exc()
                return Response({"error": serializer.errors,"traceback": tb }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}", "traceback": tb }, status=status.HTTP_400_BAD_REQUEST)
        except ErpPurchaseIssueReceipt.DoesNotExist:
            tb = traceback.format_exc()
            return Response({"error": "Invalid Data", "traceback": tb }, status=status.HTTP_400_BAD_REQUEST)

    def update_purchase_issue_details(self, item_details,purchase_entry,lot_data,request):        
        for detail in item_details:
            item_id = detail.get('id_issue_receipt_detail')
            if item_id:
                try:
                    update_detail = {  'recd_pieces': detail["pieces"],
                                        'recd_gross_wt':detail["gross_wt"],
                                        'recd_less_wt': detail["less_wt"],
                                        'recd_net_wt': detail["net_wt"],
                                        'recd_dia_wt': detail["dia_wt"],
                                        'recd_stone_wt': detail["stone_wt"],
                                        'recd_other_metal_wt': detail["other_metal_wt"],
                                        'recd_pure_wt': detail["pure_wt"],
                                        'recd_purchase_cost': detail["purchase_cost"],

                                          }
                    item_instance = ErpPurchaseIssueReceiptDetails.objects.get(pk=item_id)
                    serializer = ErpPurchaseIssueReceiptDetailsSerializer(item_instance, data=update_detail, partial=True)
                    print('insert')
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        update_other_details(detail.get('stone_details',[]),serializer.data['id_issue_receipt_detail'],ErpPurchaseIssueReceiptStoneDetailsSerializer,'issue_receipt_detail','id_issue_stn_detail',False)
                        update_other_details(detail.get('other_metal_details',[]),serializer.data['id_issue_receipt_detail'],ErpPurchaseIssueReceiptOtherMetalSerializer,'issue_receipt_detail','id_issue_other_metal',False)

                except ErpPurchaseIssueReceiptDetails.DoesNotExist:
                    raise(ErpPurchaseIssueReceiptDetails.DoesNotExist)
                
    def post(self, request, *args, **kwargs):
        queryset = ErpPurchaseIssueReceipt.objects.get(id_issue_receipt= request.data['pk_id'])
        if(queryset.status == 0 ):
            queryset.status = 2
            queryset.cancelled_by = self.request.user
            queryset.cancelled_on =  datetime.now(tz=timezone.utc)
            queryset.cancelled_reason =  request.data['cancel_reason']
            queryset.save()
            return Response({"message": "Purchase Issue Receipt Cancelled Successfully."}, status=status.HTTP_202_ACCEPTED)
        return Response({"message": "Purchase Issue Receipt Cannot Be Cancelled."}, status=status.HTTP_400_BAD_REQUEST)

    


class PurchaseIssueReceiptListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        try:
            issue_no = request.query_params.get('issue_no')
            queryset = ErpPurchaseIssueReceipt.objects.filter(issue_no=issue_no,status=0).get()
            issuereceipt = ErpPurchaseIssueReceiptSerializer(queryset).data

            detail = ErpPurchaseIssueReceiptDetails.objects.filter(issue_receipt=issuereceipt['id_issue_receipt'])
            detail_serializer = ErpPurchaseIssueReceiptDetailsSerializer(detail,many=True)
            for data in detail_serializer.data:
                gross_wt = float(data["gross_wt"])
                less_wt = float(data["less_wt"])
                net_wt = float(data["net_wt"])
                dia_wt = float(data["dia_wt"])
                stn_wt = float(data["stone_wt"])
                other_metal_wt = float(data["other_metal_wt"])
                pieces = float(data["pieces"])
                pure_wt = float(data["pure_wt"])
                stone_details_instance = ErpPurchaseIssueReceiptStoneDetails.objects.filter(issue_receipt_detail=data['id_issue_receipt_detail'])
                stone_details = ErpPurchaseIssueReceiptStoneDetailsSerializer(stone_details_instance, many=True).data
                other_metal_details_instance = ErpPurchaseIssueReceiptOtherMetal.objects.filter(issue_receipt_detail=data['id_issue_receipt_detail'])
                other_metal_details = ErpPurchaseIssueReceiptOtherMetalSerializer(other_metal_details_instance, many=True).data
                for other, other_instance in zip(other_metal_details,other_metal_details_instance):
                    piece = float(other["piece"])
                    weight = float(other["weight"])
                    wastage_weight = float(other["wastage_weight"])
                    other.update({
                        "avail_piece": format(piece, '.3f'),
                        "avail_wt": format(weight, '.3f'),
                        "selectedCategory": other_instance.id_category.id_category,
                        "selectedPurity":other_instance.id_purity.id_purity,
                        'piece': (piece),
                        'ratePerGram': (0),
                        'weight': (weight),
                        'amount': (other_instance.other_metal_cost),
                        'wastagePercentage':(other_instance.wastage_percentage),
                        'wastageWeight':(wastage_weight),
                        'mcValue':(other_instance.mc_value),
                        'mcType':other_instance.mc_type,
                        'cat_name':other_instance.id_category.cat_name,
                    })
                for stn, stn_instance in zip(stone_details,stone_details_instance):
                    stone_pcs = float(stn["stone_pcs"])
                    stone_wt = float(stn["stone_wt"])
                    stn.update({
                        "avail_piece": format(stone_pcs, '.3f'),
                        "avail_wt": format(stone_wt, '.3f'),
                        "piece": format(stone_pcs, '.3f'),
                        "weight": format(stone_wt, '.3f'),
                        "stone_rate": format(stn_instance.pur_st_rate, '.2f'),
                        "stone_amount": format(stn_instance.pur_stn_cost, '.2f'),
                        "stone_name": stn_instance.id_stone.stone_name,
                    })

                data.update({
                    "avail_stone_details":stone_details,
                    "avail_other_metal_details":other_metal_details,
                    "avail_gross_wt": format(gross_wt, '.3f'),
                    "avail_piece": format(pieces, '.0f'),
                    "avail_less_wt": format(less_wt, '.3f'),
                    "avail_net_wt": format(net_wt, '.3f'),
                    "avail_dia_wt": format(dia_wt, '.3f'),
                    "avail_stone_wt": format(stn_wt, '.3f'),
                    "avail_other_metal_wt": format(other_metal_wt, '.3f'),
                    "avail_pure_wt": format(pure_wt, '.3f'),
                    "stone_details":stone_details,
                    "other_metal_details":other_metal_details,
                    "purchase_cost":data["purchase_costs"]
                })
            issuereceipt.update({"item_details":detail_serializer.data})
            return Response(issuereceipt)
        except ErpPurchaseIssueReceipt.DoesNotExist:
                return Response({"message": "Issue Details Does Not Exist" }, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_branch = request.data.get('branch')
        id_branch = (id_branch) if id_branch != '' else 0
        print(id_branch,'branch',from_date,to_date)

        lists = ErpPurchaseIssueReceipt.objects.annotate(
            total_gross_wt=Sum('purchase_issues__gross_wt'),
            total_net_wt=Sum('purchase_issues__net_wt'),
            total_stn_wt=Sum('purchase_issues__stone_wt'),
            total_dia_wt=Sum('purchase_issues__dia_wt'),
            total_recd_gross_wt=Sum('purchase_issues__recd_gross_wt'),
            total_recd_net_wt=Sum('purchase_issues__recd_net_wt'),
            total_recd_stn_wt=Sum('purchase_issues__recd_stone_wt'),
            total_recd_dia_wt=Sum('purchase_issues__recd_dia_wt'),
        ).values(
            'id_issue_receipt',
            'issue_no', 
            'issue_type',
            'issue_to_emp__firstname',
            'total_gross_wt', 
            'total_net_wt',
            'total_stn_wt',
            'total_dia_wt',
            'total_recd_gross_wt', 
            'total_recd_net_wt',
            'total_recd_stn_wt',
            'total_recd_dia_wt',
            'issue_date',
            'status'
        ).order_by('-id_issue_receipt')
        if from_date and to_date:
            lists = lists.filter(issue_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            lists = lists.filter(id_branch__in=id_branch)


        for purchase in lists:
            print(dict(ErpPurchaseIssueReceipt.ISSUE_STATUS).get(purchase['status'], ''),get_status_color(purchase['status']))
            purchase['pk_id'] = purchase['id_issue_receipt']
            purchase['issue_type'] = 'Qc' if purchase['issue_type']==1 else 'Halmarking'
            purchase['issue_date'] = format_date(purchase['issue_date'])
            purchase['total_gross_wt'] = format(purchase['total_gross_wt'], '.3f')
            purchase['total_net_wt'] = format(purchase['total_net_wt'], '.3f')
            purchase['total_stn_wt'] = format(purchase['total_stn_wt'], '.3f')
            purchase['total_dia_wt'] = format(purchase['total_dia_wt'], '.3f')
            purchase['total_recd_gross_wt'] = format(purchase['total_recd_gross_wt'], '.3f')
            purchase['total_recd_net_wt'] = format(purchase['total_recd_net_wt'], '.3f')
            purchase['total_recd_stn_wt'] = format(purchase['total_recd_stn_wt'], '.3f')
            purchase['total_recd_dia_wt'] = format(purchase['total_recd_dia_wt'], '.3f')
            purchase['is_cancelable'] = (True if purchase['status']==0 else False)
            purchase['status_color'] = get_status_color(purchase['status'])
            purchase['status'] = dict(ErpPurchaseIssueReceipt.ISSUE_STATUS).get(purchase['status'], '')
        paginator, page = pagination.paginate_queryset(lists, request,None,PURCHASE_ISSUE_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,PURCHASE_ISSUE_COLUMN_LIST,request.data.get('path_name',''))
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        PURCHASE_ISSUE_ACTION_LIST ['is_print_req'] = True

        context={
            'columns':columns,
            'actions':PURCHASE_ISSUE_ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(lists,context) 


class PurchaseLotGenerateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        try:
            po_no = request.query_params.get('po_no')
            fin_id = request.query_params.get('fin_id')
            id_branch = request.query_params.get('id_branch')
            bill_setting_type = int(request.data.get('bill_setting_type',1))
            issue_type =1
            if((not fin_id) or (not po_no) or (not id_branch) ):
                return Response({"error": "po_no,fin_id,id_branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = ErpPurchaseEntry.objects.filter(is_approved=True,fin_year=fin_id,ref_no=po_no,is_cancelled=False,id_branch = id_branch,setting_bill_type=bill_setting_type).get()
            serializer = ErpPurchaseEntrySerializer(queryset)
            detail = ErpPurchaseEntryDetails.objects.filter(purchase_entry = queryset.id_purchase_entry)
            detail_serializer = ErpPurchaseEntryDetailsSerializer(detail,many=True)
            detail_data = detail_serializer.data
            item_details = []
            for item, instance in zip(detail_data,detail):
                gross_wt =0
                less_wt = 0
                net_wt = 0
                dia_wt = 0
                stn_wt = 0
                other_metal_wt = 0
                pieces = 0
                stone=[]
                other_metal=[]


                stone_details_instance = ErpPurchaseStoneDetails.objects.filter(purchase_entry_detail=item['id_purchase_entry_detail'])
                stone_details = ErpPurchaseStoneDetailsSerializer(stone_details_instance, many=True).data

                for stn, stn_instance in zip(stone_details,stone_details_instance):
                    issued_stn_data = stn_instance.issue_receipt_stone.filter(issue_receipt_detail__issue_receipt__issue_type=issue_type,issue_receipt_detail__issue_receipt__status__in = [0,1])
                    lot_stn_data = stn_instance.purchase_stn_detail.all()

                    stone_pcs = 0
                    stone_wt = 0
                    for stn_data in issued_stn_data:
                        stone_pcs += float(stn_data.recd_pcs or 0)
                        stone_wt += float(stn_data.recd_wt or 0)
                    for stn_data in lot_stn_data:
                        stone_pcs -= float(stn_data.stone_pcs or 0)
                        stone_wt -= float(stn_data.stone_wt or 0)
                    stn.update({
                        "avail_piece": format(stone_pcs, '.3f'),
                        "avail_wt": format(stone_wt, '.3f'),
                        "piece": format(stone_pcs, '.3f'),
                        "weight": format(stone_wt, '.3f'),
                        "stone_rate": format(stn_instance.pur_st_rate, '.2f'),
                        "stone_amount": format(stn_instance.pur_stn_cost, '.2f'),
                        "stone_name": stn_instance.id_stone.stone_name,
                    })
                    if(stone_pcs > 0 or stone_wt > 0):
                        stone.append(stn)

                other_metal_details_instance = ErpPurchaseOtherMetal.objects.filter(purchase_entry_detail=item['id_purchase_entry_detail'])
                other_metal_details = ErpPurchaseOtherMetalSerializer(other_metal_details_instance, many=True).data

                for other, other_instance in zip(other_metal_details,other_metal_details_instance):
                    issued_other_data = other_instance.issue_receipt_other_metal.filter(issue_receipt_detail__issue_receipt__issue_type=issue_type,issue_receipt_detail__issue_receipt__status__in = [0,1])
                    lot_other_detail = other_instance.pur_lot_other_detail.all()

                    piece = 0
                    weight = 0
                    wastage_weight = float(other["wastage_weight"])
                    for metal_data in issued_other_data:
                        piece += float(metal_data.recd_pcs or 0)
                        weight += float(metal_data.recd_wt or 0)
                    for metal_data in lot_other_detail:
                        piece -= float(metal_data.piece or 0)
                        weight -= float(metal_data.weight or 0)
                    other.update({
                        "avail_piece": format(piece, '.3f'),
                        "avail_wt": format(weight, '.3f'),
                        "selectedCategory": other_instance.id_category.id_category,
                        "selectedPurity":other_instance.id_purity.id_purity,
                        'piece': (piece),
                        'ratePerGram': (other_instance.rate_per_gram),
                        'weight': (weight),
                        'amount': (other_instance.other_metal_cost),
                        'wastagePercentage':(other_instance.wastage_percentage),
                        'wastageWeight':(wastage_weight),
                        'mcValue':(other_instance.mc_value),
                        'mcType':other_instance.mc_type,
                        'cat_name':other_instance.id_category.cat_name,

                    })
                    if(piece > 0 or weight > 0):
                        other_metal.append(other)


                issued_data = instance.purchase_issue_detail.filter(issue_receipt__issue_type=issue_type,issue_receipt__status__in = [0,1])
                for data in issued_data:
                    print(data.recd_gross_wt,'recd_gross_wt')
                    gross_wt += float(data.recd_gross_wt or 0)
                    less_wt += float(data.recd_less_wt or 0)
                    net_wt += float(data.recd_net_wt or 0)
                    dia_wt += float(data.recd_dia_wt or 0)
                    stn_wt += float(data.recd_stone_wt or 0)
                    other_metal_wt += float(data.recd_other_metal_wt or 0)
                    pieces += float(data.recd_pieces or 0)

                lot_data = instance.purchase_detail.all()
                print(lot_data,'lot_data')

                for data in lot_data:
                    gross_wt -= float(data.gross_wt or 0)
                    less_wt -= float(data.less_wt or 0)
                    net_wt -= float(data.net_wt or 0)
                    dia_wt -= float(data.dia_wt or 0)
                    stn_wt -= float(data.stone_wt or 0)
                    other_metal_wt -= float(data.other_metal_wt or 0)
                    pieces -= float(data.pieces or 0)


                item.update({
                    "stone_details":stone,
                    "other_metal_details":other_metal,
                    "avail_stone_details":stone,
                    "avail_other_metal_details":other_metal,
                    "avail_gross_wt": format(gross_wt, '.3f'),
                    "avail_piece": format(pieces, '.0f'),
                    "avail_less_wt": format(less_wt, '.3f'),
                    "avail_net_wt": format(net_wt, '.3f'),
                    "avail_dia_wt": format(dia_wt, '.3f'),
                    "avail_stone_wt": format(stn_wt, '.3f'),
                    "avail_other_metal_wt": format(other_metal_wt, '.3f'),
                    "gross_wt": format(gross_wt, '.3f'),
                    "pieces": format(pieces, '.0f'),
                    "less_wt": format(less_wt, '.3f'),
                    "net_wt": format(net_wt, '.3f'),
                    "dia_wt": format(dia_wt, '.3f'),
                    "stone_wt": format(stn_wt, '.3f'),
                    "other_metal_wt": format(other_metal_wt, '.3f'),
                    "purchase_entry_detail":item["id_purchase_entry_detail"],
                    "isChecked":True,
                })

                if(gross_wt > 0 or pieces > 0):
                    item_details.append(item)


            if(item_details):
                output = serializer.data
                output.update({
                    "item_details":item_details
                })
                return Response(output)
            return Response({"message": "Po Details Does Not Have Balance Wt","detail_data":detail_data }, status=status.HTTP_400_BAD_REQUEST)
            
        except ErpPurchaseEntry.DoesNotExist:
            return Response({"message": "Po Details Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                lot_data = request.data
                lot_details = request.data.get('item_details')
                if not lot_data:
                    return Response({"error": "Lot data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not lot_details:
                    return Response({"error": "Lot Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                lot_data = lot_generate(lot_data,request)
                print(lot_data)
                insert_lot_details(lot_details,lot_data['lot_date'],lot_data['lot_no'],lot_data['id_branch'],request)
                return Response({"message":"Lot Created Successfully.","lot_no":lot_data['lot_no'],"pdf_path":"inventory/lot/print"}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"message": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)


def lot_generate(lot_data,request):
    branch_date = BranchEntryDate()
    entry_date = branch_date.get_entry_date(lot_data['id_branch'])
    branch=Branch.objects.get(id_branch=lot_data['id_branch'])
    fy=FinancialYear.objects.get(fin_status=True)
    fin_id = fy.fin_id
    lot_code = generate_lot_code(lot_data,branch.short_name,fy)
    lot_data.update({"lot_date":entry_date,"lot_code":lot_code,"fin_year":fin_id,"created_by": request.user.id})
    lot_serializer = ErpLotInwardSerializer(data = lot_data)
    if lot_serializer.is_valid(raise_exception=True):
        lot_serializer.save()
        return lot_serializer.data
    raise ValueError(lot_serializer.errors)



class ErpCustomerRateCutCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        id_customer = request.query_params.get('id_customer')
        id_metal = request.query_params.get('id_metal')
        if(not id_customer):
            return Response({"error": "id_supplier is missing...."}, status=status.HTTP_400_BAD_REQUEST)
        elif(not id_metal):
            return Response({"error": "id_metal is missing...."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            rate_cut_details = self.customer_rate_cut_details(id_customer,id_metal)

            return Response(rate_cut_details)

    def customer_rate_cut_details(self,id_customer,id_metal):
        sql = F"""
                select i.erp_invoice_id,c.firstname as cus_name,date_format(i.invoice_date,'%d-%m-%Y') as payment_date,
                COALESCE(pur.total_pcs,0) as pieces,coalesce(pur.pure_weight,0) as pure_wt,
                (coalesce(pur.pure_weight,0) - coalesce(rc.pure_wt,0)-coalesce(oldMetal.pure_weight,0)) as balance_weight,i.sales_invoice_no as ref_no,
                '0' as mc_and_other_charges,'0' as total_amount,(coalesce(oldMetal.pure_weight,0)+coalesce(rc.pure_wt,0)) as paid_weight,
                '0' as paid_amount,'true' as isChecked
                from erp_invoice i
                left join customers c on c.id_customer = i.id_customer_id
                left join (select d.invoice_bill_id_id,COALESCE(sum(d.pieces),0) as total_pcs,
                    coalesce(sum(d.pure_weight),0) as pure_weight
                    from erp_invoice_sales_details d
                    left join erp_product p on p.pro_id = d.id_product_id
                    where p.id_metal_id = {id_metal}
                    group by d.invoice_bill_id_id) as pur ON pur.invoice_bill_id_id = i.erp_invoice_id
                left join (select s.invoice_bill_id_id,coalesce(sum(s.pure_weight),0) as pure_weight
                    from erp_invoice_old_metal_details s
                    group by s.invoice_bill_id_id) as oldMetal on oldMetal.invoice_bill_id_id = i.erp_invoice_id
                left join (select coalesce(sum(c.pure_wt),0) as pure_wt,c.erp_invoice_id_id
                    from erp_customer_rate_cut c
                    where c.id_customer_id = {id_customer} and c.id_metal_id = {id_metal}
                    group by c.erp_invoice_id_id) as rc on rc.erp_invoice_id_id = i.erp_invoice_id
                where i.invoice_status = 1 and i.id_customer_id = {id_customer}
                having pure_wt > 0
                """
        result = execute_raw_query(sql)
        return result
            
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                payment_data = request.data
                rate_cut_details = request.data['rate_cut_details']
                metal_issue_details = request.data['metal_issue_details']
                metal_varavu_details = request.data['metal_varavu_details']

                if not payment_data:
                    return Response({"error": "Purchase Payment data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if (not rate_cut_details) and (not metal_issue_details) and (not metal_varavu_details):
                    return Response({"error": "Purchase Payment Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch=Branch.objects.get(is_ho=1)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(branch.id_branch)
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                if(rate_cut_details):
                    for item in rate_cut_details:
                        ref_no = self.generate_ref_code(fin_id)
                        item.update({"id_customer":payment_data['id_customer'],"id_metal":payment_data['id_metal'],"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": request.user.id})
                        rate_cut_serializer = ErpCustomerRateCutSerializer(data = item)
                        if rate_cut_serializer.is_valid(raise_exception=True):
                            rate_cut_serializer.save()
                if  metal_varavu_details :
                        metal_varavu_details=insert_other_details(metal_varavu_details,ErpSupplierAdvanceAdjSerializer,{})

                if(metal_issue_details):
                    payment_data['id_branch'] = branch.id_branch
                    instance = ErpMetalIssueCreateAPIView()
                    stock_details = instance.insert_metal_issue_details(payment_data, metal_issue_details,request)
                    for item in stock_details:
                        if item["type"] == 3:
                            product_details = Product.objects.filter(pro_id=item['id_product']).get()
                            data = {
                                "type" : 2,
                                "ref_id" : item["id_metal_issue"],
                                "id_supplier" : payment_data['id_supplier'],
                                "id_metal" : product_details.id_metal.pk,
                                "ref_id" : item["id_metal_issue"],
                                "weight" : item["pure_wt"],
                            }
                            serial= ErpSupplierAdvanceSerializer(data=data)
                            if(serial.is_valid(raise_exception=True)):
                                serial.save()

                    
                return Response({"message":"Purchase Payment Created Successfully.",'pdf_url': ""}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_ref_code(self,fin_id):
        code = ''
        code_settings = RetailSettings.objects.get(name='purchase_entry_code_settings').value
        last_code=None
        if code_settings == '0':#GENERATE CODE
            last_code=ErpCustomerRateCut.objects.order_by('-id_cus_rate_cut').first()
        elif code_settings == '1':#GENERATE CODE WITH FY
            last_code=ErpCustomerRateCut.objects.filter(fin_year=fin_id).order_by('-id_cus_rate_cut').first()
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


class ErpCustomerPaymentCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
            id_customer = request.query_params.get('id_customer')
            id_metal = request.query_params.get('id_metal')
            
            if(not id_customer):
                return Response({"message": "id_customer is missing...."}, status=status.HTTP_400_BAD_REQUEST)
            elif(not id_metal):
                return Response({"message": "id_metal is missing...."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                sql = F"""
                select i.erp_invoice_id,c.firstname as cus_name,date_format(i.invoice_date,'%d-%m-%Y') as payment_date,
                COALESCE(pur.total_pcs,0) as pieces,coalesce(pur.pure_weight,0) as pure_wt,
                (coalesce(pur.pure_weight,0) - coalesce(rc.pure_wt,0)-coalesce(oldMetal.pure_weight,0)) as balance_weight,i.sales_invoice_no as ref_no,
                '0' as mc_and_other_charges,coalesce(rc.amount,0) as total_amount,(coalesce(oldMetal.pure_weight,0)+coalesce(rc.pure_wt,0)) as paid_weight,
                coalesce(pay.paid_amount,0) as paid_amount,'true' as isChecked,coalesce(coalesce(rc.amount,0) - coalesce(pay.paid_amount,0),0) as balance_amount
                from erp_invoice i
                left join customers c on c.id_customer = i.id_customer_id
                left join (select d.invoice_bill_id_id,COALESCE(sum(d.pieces),0) as total_pcs,
                    coalesce(sum(d.pure_weight),0) as pure_weight
                    from erp_invoice_sales_details d
                    left join erp_product p on p.pro_id = d.id_product_id
                    where p.id_metal_id = {id_metal}
                    group by d.invoice_bill_id_id) as pur ON pur.invoice_bill_id_id = i.erp_invoice_id
                left join (select s.invoice_bill_id_id,coalesce(sum(s.pure_weight),0) as pure_weight
                    from erp_invoice_old_metal_details s
                    group by s.invoice_bill_id_id) as oldMetal on oldMetal.invoice_bill_id_id = i.erp_invoice_id
                left join (select coalesce(sum(c.pure_wt),0) as pure_wt,c.erp_invoice_id_id,
                    coalesce(sum(c.amount),0) as amount
                    from erp_customer_rate_cut c
                    where c.id_customer_id = {id_customer} and c.id_metal_id = {id_metal}
                    group by c.erp_invoice_id_id) as rc on rc.erp_invoice_id_id = i.erp_invoice_id
                left join (select coalesce(sum(pay.paid_amount),0) as paid_amount,pay.ref_id
                    from erp_customer_purchase_payment_details pay
                    LEFT JOIN erp_customer_purchase_payment p on p.id =pay.customer_payment_id
                    where p.id_customer_id = {id_customer} and p.metal_id = {id_metal}
                    group by pay.ref_id ) as pay on pay.ref_id = i.erp_invoice_id
                where i.invoice_status = 1 and i.id_customer_id = {id_customer}
                having pure_wt > 0
                """ 
                results = execute_raw_query(sql)

                
            output = []
            for res in  results :
                if(res["balance_amount"] > 0 ):
                    output.append(res)
            return Response(output)

    def generate_ref_code(self, data,branch_code,fy):
        code = ''
        code_settings = RetailSettings.objects.get(name='purchase_entry_code_settings').value
        fin_id = fy.fin_id
        last_code=None
        if code_settings == '0':#GENERATE CODE
            last_code=ErpCustomerPayment.objects.order_by('-pk').first()
        elif code_settings == '1':#GENERATE CODE WITH FY
            last_code=ErpCustomerPayment.objects.filter(fin_year=fin_id).order_by('-pk').first()
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
                payment_data = request.data
                payment_details = request.data.get('payment_details')
                payment_mode_details = request.data.get('payment_mode_details')

                if not payment_data:
                    return Response({"error": "Purchase Payment data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if int(payment_data['type']) == 1 and (not payment_details) and (not payment_mode_details):
                    return Response({"error": "Purchase Payment Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch=Branch.objects.get(is_ho=1)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(branch.id_branch)
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                ref_no = self.generate_ref_code(payment_data,branch.short_name,fy)
                payment_data.update({"ref_no":ref_no,"entry_date":entry_date,"fin_year":fin_id,"cash_from_branch": branch.id_branch,"id_branch":branch.id_branch,"created_by": request.user.id})
                payment_serializer = ErpCustomerPaymentSerializer(data = payment_data)
                if payment_serializer.is_valid(raise_exception=True):
                    payment_serializer.save()
                    payment_details=insert_other_details(payment_details,ErpCustomerPaymentDetailsSerializer,{"customer_payment":payment_serializer.data['id']})
                    payment_mode_details=insert_other_details(payment_mode_details,ErpCustomerPaymentModeDetailSerializer,{"payment_type":2,"customer_payment":payment_serializer.data['id']})
                return Response({"message":"Purchase Payment Created Successfully.",'pdf_url': ""}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
class ErpPurchasePaymentCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
            id_supplier = request.query_params.get('id_supplier')
            id_metal = request.query_params.get('id_metal')
            bill_setting_type = int(request.query_params.get('bill_setting_type',1))
            if(not id_supplier and not id_metal):
                return Response({"error": "id_supplier,id_metal is missing...."}, status=status.HTTP_400_BAD_REQUEST)
            rate_cut_and_pay_type = RetailSettings.objects.get(name='rate_cut_and_pay_type').value
            print("rate_cut_and_pay_type",rate_cut_and_pay_type)
            if int(rate_cut_and_pay_type)==2:
                rate_cut_details = self.supplier_rate_cut_details(id_supplier,id_metal,bill_setting_type)
            else:
                rate_cut_details = self.supplier_purchase_rate_cut_details(id_supplier,id_metal,bill_setting_type)
                   
            results = execute_raw_query(rate_cut_details)
            if int(rate_cut_and_pay_type)==2:
                opening = F"""SELECT
                            pur.id_metal_id,
                            NULL as purchase_entry_id,
                            2 as type ,
                            false as isChecked,
                            m.metal_name as metal_name,
                            "Openning" as ref_no,
                            "-" as payment_date,
                            0 as pieces,
                            COALESCE(SUM(pur.weight), 0) as pure_wt,
                            0 as mc_and_other_charges,
                            COALESCE(SUM(pur.amount), 0) as total_amount,
                            COALESCE(SUM(metal_issue.paid_weight), 0) + COALESCE(SUM(rate_cut.paid_weight), 0) as paid_weight,
                            COALESCE(SUM(payment.paid_amount), 0) as paid_amount,
                            COALESCE(COALESCE(SUM(pur.weight), 0) - COALESCE(SUM(metal_issue.paid_weight), 0) - COALESCE(SUM(rate_cut.paid_weight), 0) , 0) as balance_weight,
                            COALESCE( COALESCE(SUM(pur.amount), 0)  - COALESCE(SUM(payment.paid_amount), 0), 0) as balance_amount
                        FROM
                            erp_purchase_supplier_opening pur
                        LEFT JOIN metal m ON m.id_metal = pur.id_metal_id
                        LEFT JOIN (
                                SELECT
                                    pro.id_metal_id,
                                    COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                                    COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                                FROM erp_supplier_metal_issue_details mi
                                LEFT JOIN erp_product pro ON pro.pro_id = mi.id_product_id
                                LEFT JOIN erp_supplier_metal_issue d ON d.id_issue = mi.issue_id
                                WHERE mi.type = 4 and d.id_supplier_id = {id_supplier}
                                GROUP BY pro.id_metal_id
                              ) metal_issue ON metal_issue.id_metal_id = pur.id_metal_id
                        LEFT JOIN (
                            SELECT rc.id_metal_id,
                                rc.purchase_entry_id,
                                COALESCE(SUM(rc.amount), 0) AS paid_amount,
                                COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
                            FROM erp_rate_cut rc
                            where rc.id_supplier_id = {id_supplier} and rc.type = 2
                            GROUP BY rc.id_metal_id
                              ) rate_cut ON rate_cut.id_metal_id = pur.id_metal_id
                        LEFT JOIN (
                            SELECT sp.metal_id,sp.ref_id,COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                                    FROM erp_supplier_payment_details sp
                                    WHERE sp.type = 4 and sp.id_supplier_id = {id_supplier}
                                    GROUP BY sp.metal_id
                              ) payment ON payment.metal_id = pur.id_metal_id
                        WHERE                   
                            pur.id_supplier_id = {id_supplier}
                        GROUP BY
                            pur.id_metal_id"""
                results1 = execute_raw_query(opening)
                print(results1,opening)
                if results1:
                    results = results1 + results 
                
                
            output = []
            print(results)
            for res in  results :
                if(float(res["balance_weight"]) > 0 ):
                    output.append(res)
            return Response(output)

    def supplier_rate_cut_details(self,id_supplier,id_metal,bill_setting_type):
        sql = (F"""SELECT
                            NULL as purchase_entry_id,
                            "-" as ref_no,
                            ent.entry_date,
                            ent.payment_date,
                            DATE_FORMAT(ent.payment_date, '%d-%m-%Y') AS payment_date,
                            pro.id_metal_id,
                            false as isChecked,
                            m.metal_name,s.value as is_qc_required,
                            COALESCE(if(s.value=0,pur_itm.pieces,recv.pieces), 0) AS pieces,
                            COALESCE(if(s.value=0,pur_itm.pure_wt,recv.pure_wt), 0) AS pure_wt,
                            COALESCE(recv.purchase_cost, 0) AS purchase_cost,
                            COALESCE(rate_cut.paid_amount, 0) + COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0) AS total_amount,
                            (COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) )  AS paid_weight,
                            COALESCE(payment.paid_amount, 0) AS paid_amount,
                            COALESCE(if(s.value=0,pur_itm.pure_wt,recv.pure_wt) - (COALESCE(rate_cut.paid_weight, 0)+ COALESCE(metal_issue.paid_weight, 0) + COALESCE(adj.adjusted_weight, 0) ), 0) AS balance_weight,
                            COALESCE(COALESCE(rate_cut.paid_amount, 0) - COALESCE(payment.paid_amount, 0) - COALESCE(adj.adjusted_weight, 0) + COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0), 0) AS balance_amount,
                            COALESCE(charges.charges_amount, 0) AS charges_amount,
                            COALESCE(other_metal.other_metal_cost, 0) AS other_metal_cost,
                            COALESCE(stn.stone_amount, 0) AS stone_amount,
                            COALESCE(SUM(pur.total_mc_value), 0) AS mc_amount,
                            (COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0)) as mc_and_other_charges
                   
                        FROM
                            erp_purchase_item_details pur 
                        LEFT JOIN erp_product pro ON  pro.pro_id = pur.id_product_id
                        LEFT JOIN metal m ON m.id_metal = pro.id_metal_id
                        LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = pur.purchase_entry_id
                        LEFT JOIN(
                        SELECT
                            adj.id_supplier_id,
                            adj.id_metal_id,
                            COALESCE(SUM(adj.weight),
                            0) AS adjusted_weight,
                            COALESCE(SUM(adj.amount),
                            0) AS adjusted_amount
                        FROM
                            erp_purchase_supplier_advance_adj adj
                        WHERE
                            adj.is_adjusted = 1 and adj.adj_type = 1
                            and adj.id_supplier_id = {id_supplier}
                            and adj.id_metal_id = {id_metal} 
                            and adj.setting_bill_type = {bill_setting_type} 
                        GROUP BY
                            adj.id_metal_id
                    ) adj
                    ON
                        adj.id_metal_id = pro.id_metal_id
                   
                        LEFT JOIN(
                            SELECT COALESCE(SUM(pur.pieces), 0) AS pieces,
                                COALESCE(SUM(pur.pure_wt), 0) AS pure_wt,
                                0 AS purchase_cost,
                                pur.purchase_entry_id,
                                pro.id_metal_id
                            FROM erp_purchase_item_details pur
                            LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                            LEFT JOIN erp_purchase_entry p on p.id_purchase_entry = pur.purchase_entry_id
                            WHERE pur.purchase_entry_id is not null 
                            and p.setting_bill_type = {bill_setting_type} 
                            and p.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal} 
                            GROUP BY pro.id_metal_id
                        ) pur_itm ON pur_itm.id_metal_id = pro.id_metal_id
                   
                        LEFT JOIN(
                            SELECT COALESCE(SUM(rec.recd_pieces), 0) AS pieces,
                                COALESCE(SUM(rec.recd_pure_wt), 0) AS pure_wt,
                                COALESCE(SUM(rec.recd_purchase_cost), 0) AS purchase_cost,
                                pur.purchase_entry_id,
                                pro.id_metal_id
                            FROM erp_purchase_item_issue_receipt_details rec
                            LEFT JOIN erp_purchase_item_issue_receipt iss ON iss.id_issue_receipt = rec.issue_receipt_id
                            LEFT JOIN erp_purchase_item_details pur ON pur.id_purchase_entry_detail = rec.purchase_entry_detail_id
                            LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                            LEFT JOIN erp_purchase_entry p on p.id_purchase_entry = pur.purchase_entry_id
                            WHERE iss.issue_type = 1 AND iss.status = 1 and p.id_supplier_id = {id_supplier} and pro.id_metal_id = {id_metal} 
                            and p.setting_bill_type = {bill_setting_type} 
                            GROUP BY pro.id_metal_id
                        ) recv ON recv.id_metal_id = pro.id_metal_id
                        
                        LEFT JOIN( SELECT
                                    sp.metal_id,
                                    sp.ref_id,
                                    COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                                FROM erp_supplier_payment_details sp
                                LEFT JOIN erp_supplier_payment p ON p.id_purchase_payment = sp.purchase_payment_id
                                WHERE sp.type = 1 and sp.id_supplier_id = {id_supplier}
                                and sp.metal_id = {id_metal} 
                                and p.setting_bill_type = {bill_setting_type} 
                                GROUP BY sp.metal_id
                        ) payment ON payment.metal_id = pro.id_metal_id
                        
                        LEFT JOIN(
                            SELECT rc.id_metal_id,
                                rc.purchase_entry_id,
                                COALESCE(SUM(rc.amount), 0) AS paid_amount,
                                COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
                            FROM erp_rate_cut rc
                            where rc.id_supplier_id = {id_supplier}
                            and rc.type != 3 and rc.type != 2
                            and rc.id_metal_id = {id_metal} 
                            and rc.setting_bill_type = {bill_setting_type} 
                            GROUP BY rc.id_metal_id
                        ) rate_cut ON rate_cut.id_metal_id = pro.id_metal_id
                        
                        LEFT JOIN(
                                SELECT
                                    pro.id_metal_id,
                                    mi.purchase_entry_id,
                                    COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                                    COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                                FROM erp_supplier_metal_issue_details mi
                                LEFT JOIN erp_product pro ON pro.pro_id = mi.id_product_id
                                LEFT JOIN erp_supplier_metal_issue d ON d.id_issue = mi.issue_id
                                WHERE d.status = 1 and d.id_supplier_id = {id_supplier}
                                and pro.id_metal_id = {id_metal} and mi.type = 1
                                and d.setting_bill_type = {bill_setting_type} 
                                GROUP BY pro.id_metal_id
                        ) metal_issue ON metal_issue.id_metal_id = pro.id_metal_id
                   
                        LEFT JOIN(
                                SELECT
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(charges.charges_amount), 0) AS charges_amount
                                FROM erp_purchase_item_charges_details charges
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = charges.purchase_entry_detail_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                LEFT JOIN erp_purchase_entry p on p.id_purchase_entry = item.purchase_entry_id
                                where p.is_approved = 1 and p.id_supplier_id = {id_supplier}
                                and pro.id_metal_id = {id_metal} 
                                and p.setting_bill_type = {bill_setting_type} 
                                GROUP BY pro.id_metal_id
                        ) charges ON charges.id_metal_id = pro.id_metal_id
                        
                        LEFT JOIN(
                                SELECT
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(stn.pur_stn_cost), 0) AS stone_amount
                                FROM erp_purchase_stone_details stn
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = stn.purchase_entry_detail_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                LEFT JOIN erp_purchase_entry p on p.id_purchase_entry = item.purchase_entry_id
                                where p.is_approved = 1 and p.id_supplier_id = {id_supplier}
                                and pro.id_metal_id = {id_metal} 
                                and p.setting_bill_type = {bill_setting_type} 
                                GROUP BY pro.id_metal_id
                        ) stn ON stn.id_metal_id = pro.id_metal_id
                        
                        LEFT JOIN(
                                SELECT
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(other_metal.other_metal_cost), 0) AS other_metal_cost
                                FROM erp_purchase_other_metal other_metal
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = other_metal.purchase_entry_detail_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                LEFT JOIN erp_purchase_entry p on p.id_purchase_entry = item.purchase_entry_id
                                where p.is_approved = 1 and p.id_supplier_id = {id_supplier}
                                and p.setting_bill_type = {bill_setting_type} 
                                and pro.id_metal_id = {id_metal} 
                                GROUP BY pro.id_metal_id
                        ) other_metal ON other_metal.id_metal_id = pro.id_metal_id
                        join settings s on s.name = 'is_qc_required'
                        WHERE ent.is_approved = 1 and ent.id_supplier_id = {id_supplier}
                        and pro.id_metal_id = {id_metal} 
                        GROUP BY pro.id_metal_id;
                        HAVING 
                        balance_weight > 0 ; 
                    """)
        return sql


    def supplier_purchase_rate_cut_details(self,id_supplier,id_metal,bill_setting_type):
        sql = (F"""SELECT
                            1 as type ,
                            pur.purchase_entry_id,
                            ent.ref_no,
                            ent.entry_date,
                            ent.payment_date,
                            DATE_FORMAT(ent.payment_date, '%d-%m-%Y') AS payment_date,
                            pro.id_metal_id,
                            false as isChecked,
                            m.metal_name,s.value as is_qc_required,
                            COALESCE(if(s.value=0,pur_itm.pieces,recv.pieces), 0) AS pieces,
                            COALESCE(if(s.value=0,pur_itm.pure_wt,recv.pure_wt), 0) AS pure_wt,
                            COALESCE(recv.purchase_cost, 0) AS purchase_cost,
                            COALESCE(rate_cut.paid_amount, 0) + COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0) AS total_amount,
                            (COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) )  AS paid_weight,
                            COALESCE(payment.paid_amount, 0) AS paid_amount,
                            COALESCE(if(s.value=0,pur_itm.pure_wt,recv.pure_wt) - (COALESCE(rate_cut.paid_weight, 0)+ COALESCE(metal_issue.paid_weight, 0)  + COALESCE(adj.adjusted_weight, 0)), 0) AS balance_weight,
                            COALESCE(COALESCE(rate_cut.paid_amount, 0) - COALESCE(payment.paid_amount, 0) + COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0), 0) AS balance_amount,
                            COALESCE(charges.charges_amount, 0) AS charges_amount,
                            COALESCE(other_metal.other_metal_cost, 0) AS other_metal_cost,
                            COALESCE(stn.stone_amount, 0) AS stone_amount,
                            COALESCE(SUM(pur.total_mc_value), 0) AS mc_amount,
                            COALESCE(adj.ref_id, 0) as adjusted_weight,
                            (COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0)) as mc_and_other_charges
                   
                        FROM
                            erp_purchase_item_details pur 
                        LEFT JOIN erp_product pro ON  pro.pro_id = pur.id_product_id
                        LEFT JOIN metal m ON m.id_metal = pro.id_metal_id
                        LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = pur.purchase_entry_id
                        LEFT JOIN(
                            SELECT
                                adj.ref_id,
                                adj.id_supplier_id,
                                adj.id_metal_id,
                                COALESCE(SUM(adj.weight),
                                0) AS adjusted_weight,
                                COALESCE(SUM(adj.amount),
                                0) AS adjusted_amount
                            FROM
                                erp_purchase_supplier_advance_adj adj
                            WHERE
                                adj.is_adjusted = 1 and adj.adj_type = 1
                                and adj.id_supplier_id = {id_supplier} 
                                and adj.setting_bill_type = {bill_setting_type} 
                            GROUP BY
                                  adj.ref_id,adj.id_metal_id
                        ) adj
                        ON
                            adj.id_metal_id = pro.id_metal_id AND adj.ref_id = pur.purchase_entry_id
                        LEFT JOIN(
                            SELECT COALESCE(SUM(pur.pieces), 0) AS pieces,
                                COALESCE(SUM(pur.pure_wt), 0) AS pure_wt,
                                0 AS purchase_cost,
                                pur.purchase_entry_id,
                                pro.id_metal_id
                            FROM erp_purchase_item_details pur
                            LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = pur.purchase_entry_id
                            LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                            WHERE pur.purchase_entry_id is not null and ent.setting_bill_type = {bill_setting_type} 
                            GROUP BY pur.purchase_entry_id,pro.id_metal_id
                        ) pur_itm ON pur_itm.purchase_entry_id = pur.purchase_entry_id AND pur_itm.id_metal_id = pro.id_metal_id
                   
                        LEFT JOIN(
                            SELECT COALESCE(SUM(rec.recd_pieces), 0) AS pieces,
                                COALESCE(SUM(rec.recd_pure_wt), 0) AS pure_wt,
                                COALESCE(SUM(rec.recd_purchase_cost), 0) AS purchase_cost,
                                pur.purchase_entry_id,
                                pro.id_metal_id
                            FROM erp_purchase_item_issue_receipt_details rec
                            LEFT JOIN erp_purchase_item_issue_receipt iss ON iss.id_issue_receipt = rec.issue_receipt_id
                            LEFT JOIN erp_purchase_item_details pur ON pur.id_purchase_entry_detail = rec.purchase_entry_detail_id
                            LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                            LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = pur.purchase_entry_id
                            WHERE iss.issue_type = 1 AND iss.status = 1
                            and ent.setting_bill_type = {bill_setting_type} 
                            GROUP BY pur.purchase_entry_id,pro.id_metal_id
                        ) recv ON recv.purchase_entry_id = pur.purchase_entry_id AND recv.id_metal_id = pro.id_metal_id
                        
                        LEFT JOIN( SELECT
                                    sp.metal_id,
                                    sp.ref_id,
                                    COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                                FROM erp_supplier_payment_details sp
                                LEFT JOIN erp_supplier_payment p ON p.id_purchase_payment = sp.purchase_payment_id
                                WHERE sp.type = 1 and p.setting_bill_type = {bill_setting_type} 
                                GROUP BY sp.ref_id,sp.metal_id
                        ) payment ON payment.ref_id = pur.purchase_entry_id AND payment.metal_id = pro.id_metal_id
                        
                        LEFT JOIN(
                            SELECT rc.id_metal_id,
                                rc.purchase_entry_id,
                                COALESCE(SUM(rc.amount), 0) AS paid_amount,
                                COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
                            FROM erp_rate_cut rc
                            where  rc.type = 1 and rc.setting_bill_type = {bill_setting_type} 
                            GROUP BY rc.purchase_entry_id,rc.id_metal_id
                        ) rate_cut ON rate_cut.purchase_entry_id = pur.purchase_entry_id AND rate_cut.id_metal_id = pro.id_metal_id
                        
                        LEFT JOIN(
                                SELECT
                                    pro.id_metal_id,
                                    mi.purchase_entry_id,
                                    COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                                    COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                                FROM erp_supplier_metal_issue_details mi
                                LEFT JOIN erp_product pro ON pro.pro_id = mi.id_product_id
                                LEFT JOIN erp_supplier_metal_issue d ON d.id_issue = mi.issue_id
                                WHERE d.type = 1 and d.setting_bill_type = {bill_setting_type} 
                                GROUP BY pro.id_metal_id,mi.purchase_entry_id
                        ) metal_issue ON metal_issue.purchase_entry_id = pur.purchase_entry_id AND metal_issue.id_metal_id = pro.id_metal_id
                   
                        LEFT JOIN(
                                SELECT
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(charges.charges_amount), 0) AS charges_amount
                                FROM erp_purchase_item_charges_details charges
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = charges.purchase_entry_detail_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                GROUP BY pro.id_metal_id,item.purchase_entry_id
                        ) charges ON charges.purchase_entry_id = pur.purchase_entry_id AND charges.id_metal_id = pro.id_metal_id
                        
                        LEFT JOIN(
                                SELECT
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(stn.pur_stn_cost), 0) AS stone_amount
                                FROM erp_purchase_stone_details stn
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = stn.purchase_entry_detail_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                GROUP BY pro.id_metal_id,item.purchase_entry_id
                        ) stn ON stn.purchase_entry_id = pur.purchase_entry_id AND stn.id_metal_id = pro.id_metal_id
                        
                        LEFT JOIN(
                                SELECT
                                    pro.id_metal_id,
                                    item.purchase_entry_id,
                                    COALESCE(SUM(other_metal.other_metal_cost), 0) AS other_metal_cost
                                FROM erp_purchase_other_metal other_metal
                                LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = other_metal.purchase_entry_detail_id
                                LEFT JOIN erp_product pro ON pro.pro_id = item.id_product_id
                                GROUP BY pro.id_metal_id,item.purchase_entry_id
                        ) other_metal ON other_metal.purchase_entry_id = pur.purchase_entry_id AND other_metal.id_metal_id = pro.id_metal_id
                        join settings s on s.name = 'is_qc_required'
                        WHERE ent.is_approved = 1 and ent.id_supplier_id = {id_supplier}
                        and pro.id_metal_id = {id_metal}
                        and ent.setting_bill_type = {bill_setting_type}
                        GROUP BY pur.purchase_entry_id,pro.id_metal_id;
                        HAVING 
                        balance_weight > 0 ; 
                    """) 
        return sql

    def generate_ref_code(self,fin_id,setting_bill_type):
        code = ''
        code_settings = RetailSettings.objects.get(name='purchase_entry_code_settings').value
        last_code=None
        if code_settings == '0':#GENERATE CODE
            last_code=ErpSupplierRateCut.objects.filter(setting_bill_type=setting_bill_type).order_by('-id_rate_cut').first()
        elif code_settings == '1':#GENERATE CODE WITH FY
            last_code=ErpSupplierRateCut.objects.filter(setting_bill_type=setting_bill_type,fin_year=fin_id).order_by('-id_rate_cut').first()
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
    
    def generate_code(self,fin_id,setting_bill_type):
        code = ''
        code_settings = RetailSettings.objects.get(name='purchase_entry_code_settings').value
        last_code=None
        if code_settings == '0':#GENERATE CODE
            last_code=ErpSupplierRateCutAndMetalIssue.objects.filter(setting_bill_type=setting_bill_type).order_by('-pk').first()
        elif code_settings == '1':#GENERATE CODE WITH FY
            last_code=ErpSupplierRateCutAndMetalIssue.objects.filter(setting_bill_type=setting_bill_type,fin_year=fin_id).order_by('-pk').first()
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
                payment_data = request.data
                rate_cut_details = request.data['rate_cut_details']
                metal_issue_details = request.data['metal_issue_details']
                metal_varavu_details = request.data['metal_varavu_details']
                bill_setting_type = int(request.data.get('bill_setting_type',1))
                if not payment_data:
                    return Response({"error": "Purchase Payment data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if (not rate_cut_details) and (not metal_issue_details) and (not metal_varavu_details):
                    return Response({"error": "Purchase Payment Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch=Branch.objects.get(is_ho=1)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(branch.id_branch)
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                ref_no = self.generate_code(fin_id,bill_setting_type)
                insert_data = {
                    "id_supplier": payment_data['id_supplier'],
                    "ref_no": ref_no,
                    "entry_date": entry_date,
                    "id_branch": branch.id_branch,
                    "fin_year": fin_id,
                    "created_by": request.user.id,
                    "remarks": payment_data.get('remarks'),
                    "setting_bill_type": bill_setting_type,
                }
                serializer = ErpSupplierRateCutAndMetalIssueSerializer(data=insert_data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    id = serializer.data['id']
                    payment_data['parent'] = id
                    if(rate_cut_details):
                        rate_cut_details =self.insert_rate_cut_details(rate_cut_details,payment_data['id_supplier'],entry_date,fin_id,request.user.id,id)
                    if  metal_varavu_details :
                            metal_varavu_details=insert_other_details(metal_varavu_details,ErpSupplierAdvanceAdjSerializer,{"parent":id})

                    if(metal_issue_details):
                        payment_data['id_branch'] = branch.id_branch
                        instance = ErpMetalIssueCreateAPIView()
                        stock_details = instance.insert_metal_issue_details(payment_data, metal_issue_details,request)
                        for item in stock_details:
                            if item["type"] == 3:
                                product_details = Product.objects.filter(pro_id=item['id_product']).get()
                                data = {
                                    "type" : 2,
                                    "ref_id" : item["id_metal_issue"],
                                    "id_supplier" : payment_data['id_supplier'],
                                    "parent":id,
                                    "id_metal" : product_details.id_metal.pk,
                                    "weight" : item["pure_wt"],
                                    "setting_bill_type":bill_setting_type,
                                }
                                serial= ErpSupplierAdvanceSerializer(data=data)
                                if(serial.is_valid(raise_exception=True)):
                                    serial.save()
                    return Response({"message":"Purchase Payment Created Successfully.",'pdf_url': ""}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    
    def insert_rate_cut_details(self,rate_cut_details,id_supplier,entry_date,fin_id,user_id,id=None):
        for item in rate_cut_details:
            ref_no = self.generate_ref_code(fin_id,item['setting_bill_type'])
            item.update({"id_supplier":id_supplier,"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": user_id,"parent":id})
            rate_cut_serializer = ErpSupplierRateCutSerializer(data = item)
            if rate_cut_serializer.is_valid(raise_exception=True):
                rate_cut_serializer.save()
                item.update(rate_cut_serializer.data)
                if item["type"] == 3:
                    data = {
                        "type" : 3,
                        "ref_id" : item["id_rate_cut"],
                        "id_supplier" : item['id_supplier'],
                        "id_metal" : item['id_metal'],
                        "weight" : item["pure_wt"],
                        "parent":id,
                        "setting_bill_type":item["setting_bill_type"],
                    }
                    serial= ErpSupplierAdvanceSerializer(data=data)
                    if(serial.is_valid(raise_exception=True)):
                        serial.save()
        return rate_cut_details

class GetPurchaseStockDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        try:
            result_data = []
            from_date = request.data.get('from_date')
            to_date = request.data.get('to_date')
            id_branch = request.data.get('id_branch')
            id_metal = request.data.get('id_metal')
            stock_type = request.data.get('stock_type')
            if not from_date:
                    return Response({"error": "From Date is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not to_date:
                    return Response({"error": "To Date is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not id_branch:
                    return Response({"error": "Branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if not stock_type:
                    return Response({"error": "Stock Type is missing."}, status=status.HTTP_400_BAD_REQUEST)
            if stock_type=='1':
                  result_data = self.get_sales_return_stock(from_date,to_date,id_branch,id_metal)
            if stock_type=='2':
                  result_data = self.get_partly_sales_stock(from_date,to_date,id_branch,id_metal)
            if stock_type=='3':
                  result_data = self.get_old_metal_stock(from_date,to_date,id_branch,id_metal)
            return Response({"message": "Data Retrieved Successfully","result":result_data}, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


    def get_old_metal_stock(self,from_date,to_date,from_branch,id_metal):
        return_data =[]
        metal_filter = ''
        if(id_metal):
            metal_filter = F"AND P.id_metal_id={id_metal} "
        
        old_metal_list = ErpInvoiceOldMetalDetails.objects.raw(
            F"""
             SELECT 
                E.invoice_old_metal_item_id,
                E.invoice_bill_id_id,
                P.product_name AS product_name,
                P.stock_type AS stock_type,
                P.uom_id_id AS uom_id,
                E.touch,
                E.id_product_id,
                E.gross_wt,
                E.pieces,
                E.less_wt,
                E.net_wt,
                E.dia_wt,
                E.stone_wt,
                E.dust_wt,
                E.wastage_weight
            FROM 
                erp_invoice_old_metal_details AS E
            JOIN 
                erp_invoice AS I ON I.erp_invoice_id = E.invoice_bill_id_id
            LEFT JOIN 
                erp_pocket_details AS PO ON E.invoice_old_metal_item_id = PO.invoice_old_metal_item_id_id
            LEFT JOIN (
            SELECT  ASP.id_account_stock_process,ASD.invoice_old_metal_item_id_id 
            FROM erp_account_stock_process_details ASD
            LEFT JOIN erp_account_stock_process AS ASP ON ASP.id_account_stock_process = ASD.account_stock_id
            WHERE  ASP.status = 1
            GROUP BY  ASD.invoice_old_metal_item_id_id 
            ) as ASP ON  ASP.invoice_old_metal_item_id_id = E.invoice_old_metal_item_id
            JOIN 
                erp_product AS P ON E.id_product_id = P.pro_id
            WHERE 
                I.invoice_status = 1
                AND I.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                AND I.id_branch_id = '{from_branch}'
                AND PO.id_pocket_detail IS NULL
                AND ASP.id_account_stock_process IS NULL
                {metal_filter}
            """
        )
        old_metal_list = ErpInvoiceOldMetalDetailsSerializer(old_metal_list,many=True).data
        
        if len(old_metal_list) > 0:
            for item in old_metal_list:
                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = item["invoice_bill_id"])
                inv_data = ErpInvoiceSerializer(inv_queryset,context={"invoice_no":True,'invoice_type':2}).data
                stone_details = []
                try:
                    stone_query_set = ErpInvoiceStoneDetails.objects.filter(invoice_old_metal_item_id=item['invoice_old_metal_item_id']).all()
                    stone_serializer = ErpInvoiceStoneDetailsSerializer(stone_query_set,many = True)
                    stone_details = stone_serializer.data
                except ErpInvoiceStoneDetails.DoesNotExist:
                       continue
                return_data.append({
                        "invoice_old_metal_item_id":item['invoice_old_metal_item_id'],
                        "pk_id":item['invoice_old_metal_item_id'],
                        "type": "OLD METAL",
                        "product_name":item['product_name'],
                        "stock_type":item['stock_type'],
                        "stock_type_name": ("Non-Tagged" if item['stock_type'] == "1" else "Tagged"),
                        "id_product":item['id_product'],
                        "id_design": '',
                        "id_sub_design": '',
                        "id_section": '',
                        "id_purity": '',
                        "uom_id": item['uom_id'],
                        "touch": item['touch'],
                        "pieces":item['pieces'],
                        "gross_wt": item['gross_wt'],
                        "less_wt":item['less_wt'],
                        "net_wt":format_with_decimal((float(item['net_wt']) + float(item['dust_wt']) + float(item['wastage_weight'])),3),
                        "dia_wt":item['dia_wt'],
                        "stone_wt":item['stone_wt'],
                        "other_metal_wt":0,
                        "stone_details":stone_details,
                        "other_metal_details":[],
                        "invoice_no" : inv_data['inv_no']['invoice_no'],
                        "customer_name" : inv_data['customer_name'],
                        "customer_mobile" : inv_data['customer_mobile'],
                  })
        return return_data
    
    def get_sales_return_stock(self,from_date,to_date,from_branch,id_metal):
        return_data =[]
        metal_filter = ''
        if(id_metal):
            metal_filter = F"AND P.id_metal_id={id_metal} "
        sales_return_list = ErpInvoiceSalesReturn.objects.raw(
            F"""
             SELECT 
                E.invoice_return_id,
                E.invoice_bill_id_id,
                P.product_name AS product_name,
                P.stock_type AS stock_type,
                P.uom_id_id AS uom_id_id,
                E.id_product_id,
                E.id_design_id,
                E.id_sub_design_id,
                E.id_purity_id,
                E.gross_wt,
                E.pieces,
                E.less_wt,
                E.net_wt,
                E.dia_wt,
                E.stone_wt,
                P.stock_type as item_type,
                E.tag_id_id
            FROM 
                erp_invoice_sales_return_details AS E
            JOIN 
                erp_invoice AS I ON I.erp_invoice_id = E.invoice_bill_id_id
            LEFT JOIN (
            SELECT  ASP.id_account_stock_process,ASD.invoice_return_id_id 
            FROM erp_account_stock_process_details ASD
            LEFT JOIN erp_account_stock_process AS ASP ON ASP.id_account_stock_process = ASD.account_stock_id
            WHERE  ASP.status = 1
            GROUP BY  ASD.invoice_return_id_id 
            ) as ASP ON  ASP.invoice_return_id_id = E.invoice_return_id
            JOIN 
                erp_product AS P ON E.id_product_id = P.pro_id
            WHERE 
                I.invoice_status = 1
                AND I.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                AND I.id_branch_id = '{from_branch}'
                AND ASP.id_account_stock_process IS NULL
                {metal_filter}
            """
        )
        for item in sales_return_list:
            inv_queryset = ErpInvoice.objects.get(erp_invoice_id = item.invoice_bill_id.erp_invoice_id)
            inv_data = ErpInvoiceSerializer(inv_queryset,context={"invoice_no":True,'invoice_type':3}).data
            stone_details = []
            # queryset = ErpInvoiceOtherMetal.objects.filter(invoice_sale_item_id=item.invoice_sale_item_id.invoice_sale_item_id)
            # other_metal_details= ErpInvoiceOtherMetalSerializer(queryset, many=True).data
            # try:
            #     stone_query_set = ErpInvoiceStoneDetails.objects.filter(invoice_sale_item_id=item.invoice_sale_item_id.invoice_sale_item_id).all()
            #     stone_serializer = ErpInvoiceStoneDetailsSerializer(stone_query_set,many = True)
            #     stone_details = stone_serializer.data
            # except ErpInvoiceStoneDetails.DoesNotExist:
            #         continue
            return_data.append({
                    "invoice_return_id": item.invoice_return_id,
                    "pk_id": item.invoice_return_id,
                    "type": "SALES RETURN",
                    "stock_type":item.stock_type,
                    "stock_type_name": ("Non-Tagged" if item.stock_type == "1" else "Tagged"),
                    "product_name": item.product_name,
                    "id_product":item.id_product_id,
                    "id_design": item.id_design_id,
                    "id_sub_design": item.id_sub_design_id,
                    "id_purity": item.id_purity_id,
                    "tag_id": item.tag_id_id,
                    "id_section": '',
                    "uom_id": item.uom_id_id,
                    "pieces":item.pieces,
                    "gross_wt":item.gross_wt,
                    "less_wt":item.less_wt,
                    "net_wt":item.net_wt,
                    "dia_wt":item.dia_wt,
                    "stone_wt":item.stone_wt,
                    "other_metal_wt": 0,
                    "stone_details":stone_details,
                    "other_metal_details":[],
                    "invoice_no" : inv_data['inv_no']['invoice_no'],
                    "customer_name" : inv_data['customer_name'],
                    "customer_mobile" : inv_data['customer_mobile'],
                })
        return return_data
    def get_partly_sales_stock(self,from_date,to_date,from_branch,id_metal):
        return_data =[]
        metal_filter = ''
        if(id_metal):
            metal_filter = F"AND P.id_metal_id={id_metal} "
        partly_sales_list = ErpInvoiceSalesDetails.objects.raw(
            F"""
             SELECT 
                E.invoice_sale_item_id,
                E.invoice_bill_id_id,
                P.product_name AS product_name,
                P.stock_type AS stock_type,
                P.uom_id_id,
                E.id_product_id,
                E.id_design_id,
                E.id_sub_design_id,
                E.id_purity_id,
                TAG.tag_gwt,
                TAG.tag_pcs,
                TAG.tag_lwt,
                TAG.tag_nwt,
                TAG.tag_dia_wt,
                TAG.tag_stn_wt,
                TAG.tag_other_metal_wt,
                E.item_type,
                TAG.tag_id as tag
            FROM 
                erp_invoice_sales_details AS E
            JOIN 
                erp_invoice AS I ON I.erp_invoice_id = E.invoice_bill_id_id
            JOIN 
                erp_tagging AS TAG ON TAG.tag_id = E.tag_id_id
            LEFT JOIN (
            SELECT  ASP.id_account_stock_process,ASD.invoice_sale_item_id_id 
            FROM erp_account_stock_process_details ASD
            LEFT JOIN erp_account_stock_process AS ASP ON ASP.id_account_stock_process = ASD.account_stock_id
            WHERE  ASP.status = 1
            GROUP BY  ASD.invoice_sale_item_id_id 
            ) as ASP ON  ASP.invoice_sale_item_id_id = E.invoice_sale_item_id
            JOIN 
                erp_product AS P ON E.id_product_id = P.pro_id
            WHERE 
                I.invoice_status = 1
                AND I.invoice_date BETWEEN '{from_date}' AND '{to_date}'
                AND I.id_branch_id = '{from_branch}'
                AND E.item_type = 0
                AND E.is_partial_sale = 1
                AND ASP.id_account_stock_process IS NULL
                {metal_filter}
            """
        )
        for item in partly_sales_list:
            inv_queryset = ErpInvoice.objects.get(erp_invoice_id = item.invoice_bill_id.erp_invoice_id)
            inv_data = ErpInvoiceSerializer(inv_queryset,context={"invoice_no":True}).data
            sold_pcs = sold_grosswt = sold_netwt = sold_leswt = sold_diawt = sold_stnwt = sold_otherwt=0
            sold_details = ErpInvoiceSalesDetails.objects.filter(tag_id=item.tag,invoice_bill_id__invoice_status = 1)
            sold_data = ErpInvoiceSalesDetailsSerializer(sold_details,many=True,context={"stone_details":True}).data
            query_set = ErpTaggingStone.objects.filter(tag_id=item.tag)
            tag_stone_details= ErpTagStoneSerializer(query_set, many=True).data
            queryset = ErpTagOtherMetal.objects.filter(tag_id=item.tag)
            tag_other_details= ErpTagOtherMetalSerializer(queryset, many=True).data
            tag = ErpTagging.objects.get(tag_id=item.tag)


            balance_stone_detail=[]
            balance_other_detail=[]
            for items, sold in zip(sold_data, sold_details):
                sold_pcs += float(sold.pieces)
                sold_grosswt += float(sold.gross_wt)
                sold_netwt += float(sold.net_wt)
                sold_leswt += float(sold.less_wt)
                sold_diawt += float(sold.dia_wt)
                sold_stnwt += float(sold.stone_wt)
                sold_otherwt += float(sold.other_metal_wt)
                for tag_stn in tag_stone_details: # Need To Recheck This Condition ############
                    for stn in items["stone_details"]:
                        if(tag_stn["id_stone"] == stn['id_stone']):# Need To Recheck This Condition
                            tag_stn["stone_pcs"] = int(float(tag_stn["stone_pcs"]) - float(stn["stone_pcs"]))
                            tag_stn["stone_wt"] = format_with_decimal(float(tag_stn["stone_wt"]) - float(stn["stone_wt"]),3)
                    if(tag_stn["stone_pcs"] > 0 or tag_stn["stone_wt"] > 0):
                        balance_stone_detail.append(tag_stn)
                for tag_metal in tag_other_details: # Need To Recheck This Condition ############
                    for metal in items["other_metal_details"]:
                        if(tag_metal["id_category"] == metal['id_category']):# Need To Recheck This Condition
                            tag_metal["piece"] = int(float(tag_metal["piece"]) - float(metal["piece"]))
                            tag_metal["weight"] = format_with_decimal(float(tag_metal["weight"]) - float(metal["weight"]),3)
                    if(tag_metal["piece"] > 0 or tag_metal["weight"] > 0):
                        balance_other_detail.append(tag_metal)

            balance_wt = float(item.tag_gwt) - float(sold_grosswt)
            if(balance_wt > 0):
                balance_pcs = float(item.tag_pcs) - int(sold_pcs)
                return_data.append({
                    "invoice_sale_item_id":item.invoice_sale_item_id,
                    "pk_id":item.invoice_sale_item_id,
                    "product_name": item.product_name,
                    "id_product":item.id_product_id,
                    "id_design": item.id_design_id,
                    "id_sub_design": item.id_sub_design_id,
                    "id_purity": item.id_purity_id,
                    "tag_id": item.tag,
                    "supplier_name": tag.id_supplier.supplier_name if tag.id_supplier else '',
                    "id_supplier": tag.id_supplier.pk,
                    "id_section": '',
                     "uom_id": item.uom_id_id,
                    "pieces": ( int(balance_pcs) if (balance_pcs > 0) else 1 )  ,
                    "type": "PARTLY SOLD",
                    "stock_type":'1',
                    "invoice_no" : inv_data['inv_no']['invoice_no'],
                    "customer_name" : inv_data['customer_name'],
                    "customer_mobile" : inv_data['customer_mobile'],
                    "gross_wt" : format_with_decimal(float(item.tag_gwt) - float(sold_grosswt),3),
                    "net_wt" : format_with_decimal(float(item.tag_nwt) - float(sold_netwt),3),
                    "less_wt" : format_with_decimal(float(item.tag_lwt) - float(sold_leswt),3),
                    "dia_wt" : format_with_decimal(float(item.tag_dia_wt) - float(sold_diawt),3),
                    "stone_wt" : format_with_decimal(float(item.tag_stn_wt) - float(sold_stnwt),3),
                    "other_metal_wt" : format_with_decimal(float(item.tag_other_metal_wt) - float(sold_otherwt),3),
                    "stone_details" : balance_stone_detail,
                    "other_metal_details":balance_other_detail,
                })
        return return_data
    
class ErpAccountStockProcessCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def generate_ref_code(self, data,branch_code,fy):
        code = ''
        # code_settings = RetailSettings.objects.get(name='purchase_entry_code_settings').value
        # code_format = RetailSettings.objects.get(name='purchase_entry_code_format').value
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_code=None
        # if code_settings == '0':#GENERATE CODE
        last_code=ErpAccountStockProcess.objects.order_by('-id_account_stock_process').first()
        # elif code_settings == '2':#GENERATE CODE WITH FY
        #     last_code=ErpAccountStockProcess.objects.filter(fin_year=fin_id).order_by('-id_account_stock_process').first()
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
        
        #code=code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code)

        return code
    
    def post(self, request, *args, **kwargs):
        item_details  = []
        try:
            with transaction.atomic():
                stock_data = request.data
                stock_details = request.data.get('stock_details')
                is_sub_design_req = RetailSettings.objects.get(name='is_sub_design_req').value
                is_section_required = RetailSettings.objects.get(name='is_section_required').value
                sales_return_lot_supplier_id = RetailSettings.objects.get(name='sales_return_lot_supplier_id').value

                if not stock_data:
                    return Response({"error": "Stock data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if (not stock_details):
                    return Response({"error": "Stock Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch=Branch.objects.get(id_branch = stock_data['id_branch'])
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(stock_data['id_branch'])
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                ref_no = self.generate_ref_code(stock_data,branch.short_name,fy)
                stock_data.update({"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": request.user.id})
                stock_data_serializer = ErpAccountStockProcessSerializer(data = stock_data)
                if stock_data_serializer.is_valid(raise_exception=True):
                    stock_data_serializer.save()
                    stock_details=insert_other_details(stock_details,ErpAccountStockProcessDetailsSerializer,{"account_stock":stock_data_serializer.data['id_account_stock_process']})
                    if(stock_data["process_type"]== '2'):
                            item_details = self.prepare_data_for_lot(stock_details,is_sub_design_req,is_section_required)
                            stock_data['id_supplier'] = sales_return_lot_supplier_id
                            if int(stock_data['stock_type']) == 2:
                                stock_data['id_supplier'] = stock_details[0].get('id_supplier') if stock_details else sales_return_lot_supplier_id
                            stock_data['account_stock_process'] = stock_data_serializer.data['id_account_stock_process']
                            lot_data = lot_generate(stock_data,request)
                            insert_lot_details(item_details,lot_data['lot_date'],lot_data['lot_no'],lot_data['id_branch'],request)
                    if(stock_data["process_type"]== '3'):
                            item_details = self.prepare_data_for_lot(stock_details,is_sub_design_req,is_section_required)
                            insert_non_tag_details(item_details,entry_date,4,stock_data_serializer.data['id_account_stock_process'],stock_data['id_branch'],request)



                return Response({"message":"Account Process Created Successfully.",'pdf_url': ""}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"message": f"Missing key: {e}",'tb':tb}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"message": str(e),'data':item_details}, status=status.HTTP_400_BAD_REQUEST)
            
    def prepare_data_for_lot(self,stock_details,is_sub_design_req,is_section_required):
        items = defaultdict(lambda: {"pieces": 0,"gross_wt": 0.000,"net_wt": 0.000,"less_wt": 0.000,"dia_wt": 0.000,"stone_wt": 0.000,"other_metal_wt":0.000,"stone_details":[],"other_metal_details":[]})
        for lot_item in stock_details:
            if(is_sub_design_req == '1' and is_section_required == '1'):
                key = (lot_item["id_product"], lot_item["id_design"],lot_item["id_sub_design"],lot_item["id_section"])
                items[key]["id_sub_design"] = lot_item["id_sub_design"]
                items[key]["id_section"] = lot_item["id_section"]
            elif(is_section_required == '1'):
                key = (lot_item["id_product"], lot_item["id_design"],lot_item["id_sub_design"])
                items[key]["id_sub_design"] = lot_item["id_sub_design"]
                items[key]["id_section"] = lot_item["id_section"]
            elif(is_sub_design_req == '1'):
                key = (lot_item["id_product"], lot_item["id_design"],lot_item["id_section"])
                items[key]["id_sub_design"] = lot_item["id_sub_design"]
            else:
                key = (lot_item["id_product"], lot_item["id_design"])
            print(key,"key")
            items[key]["id_product"] = lot_item["id_product"]
            items[key]["id_design"] = lot_item["id_design"]
            items[key]["id_purity"] = lot_item.get("id_purity")
            items[key]["uom_id"] = lot_item["uom_id"]
            items[key]["sell_rate"] = 0
            items[key]["pieces"] += int(lot_item["pieces"])
            items[key]["gross_wt"] += float(lot_item["gross_wt"])
            items[key]["net_wt"] += float(lot_item["net_wt"])
            items[key]["less_wt"] += float(lot_item["less_wt"])
            items[key]["stone_wt"] += float(lot_item["stone_wt"])
            items[key]["other_metal_wt"] += float(lot_item["other_metal_wt"])
            items[key]["dia_wt"] += float(lot_item["dia_wt"])
            items[key]["stone_details"] = self.prepare_data_for_stone_details(items[key]["stone_details"],lot_item["stone_details"])
            items[key]["other_metal_detail"] = self.prepare_data_for_other_details(items[key]["other_metal_details"],lot_item["other_metal_details"])

        result = list(items.values())
        for lotitem in result:
            lotitem["pieces"] = int(lotitem["pieces"])
            lotitem["gross_wt"] = format_with_decimal(lotitem["gross_wt"],3)
            lotitem["net_wt"] = format_with_decimal(lotitem["net_wt"],3)
            lotitem["less_wt"] = format_with_decimal(lotitem["less_wt"],3)
            lotitem["stone_wt"] = format_with_decimal(lotitem["stone_wt"],3)
            lotitem["other_metal_wt"] = format_with_decimal(lotitem["other_metal_wt"],3)
            lotitem["dia_wt"] = format_with_decimal(lotitem["dia_wt"],3)


        return result
    
    def prepare_data_for_stone_details(self,grouped_details,item_stone_details):
        stone_details = grouped_details + item_stone_details
        items = defaultdict(lambda: {"stone_pcs": 0,"stone_wt": 0,"pur_st_rate": 0,"pur_stn_cost": 0})
        for stone in stone_details:
            print(stone["stone_wt"],"stone_wt")
            key = (stone["id_stone"])
            items[key]["id_stone"] = stone["id_stone"]
            items[key]["show_in_lwt"] = stone["show_in_lwt"]
            items[key]["stone_wt"] += float(stone["stone_wt"])
            items[key]["stone_pcs"] += int(stone["stone_pcs"])
            items[key]["uom_id"] = stone["uom_id"]
            items[key]["stone_type"] = stone["stone_type"]
            items[key]["pur_stn_cost"] += float(stone["pur_stn_cost"])
            items[key]["pur_st_rate"] += float(stone["pur_st_rate"])
            items[key]["pur_stn_cal_type"] = stone["pur_stn_cal_type"]
        result = list(items.values())
        return result

    def prepare_data_for_other_details(self,grouped_details,item_details):
        details = grouped_details + item_details
        items = defaultdict(lambda: {"piece": 0,"weight": 0,"wastage_weight": 0,"mc_value": 0,"rate_per_gram": 0,"other_metal_cost": 0})
        for item in details:
            key = (item["id_category"],item["id_purity"])
            items[key]["id_category"] = item["id_category"]
            items[key]["id_purity"] = item["id_purity"]
            items[key]["other_metal_cost"] += float(item["other_metal_cost"])
            items[key]["rate_per_gram"] += float(item["rate_per_gram"])
            items[key]["mc_type"] = item["mc_type"]
            items[key]["mc_value"] += float(item["mc_value"])
            items[key]["wastage_weight"] += float(item["wastage_weight"])
            items[key]["weight"] += float(item["weight"])
            items[key]["piece"] += float(item["piece"])
        result = list(items.values())
        return result

def insert_non_tag_details(item_details,entry_date,type,id,id_branch,request):
    for item in item_details:
            log_details=item
            log_details.update({"ref_id": id,"transaction_type": type,"to_branch": id_branch,"date" : entry_date,"id_stock_status": 1,"created_by": request.user.id})
            non_tag_serializer = ErpLotInwardNonTagSerializer(data=log_details)
            non_tag_serializer.is_valid(raise_exception=True)
            non_tag_serializer.save()
            for stn in item['stone_details']:
                log_stn_details=stn
                log_stn_details.update({ "id_non_tag_log": non_tag_serializer.data['id_non_tag_log'],"stn_cal_type": stn['pur_stn_cal_type'],"stn_rate" : stn['pur_st_rate'],"stn_cost": stn['pur_stn_cost']})
                non_tag_stn_serializer = ErpLotInwardNonTagStoneSerializer(data=log_stn_details)
                non_tag_stn_serializer.is_valid(raise_exception=True)
                non_tag_stn_serializer.save()


class ErpMetalIssueCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def generate_ref_code(self, data,branch_code,fy):
        code = ''
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_code=ErpSupplierMetalIssue.objects.order_by('-id_issue').first()
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
        item_details  = []
        try:
            with transaction.atomic():
                stock_data = request.data
                stock_details = request.data.get('stock_details')
                is_sub_design_req = RetailSettings.objects.get(name='is_sub_design_req').value
                is_section_required = RetailSettings.objects.get(name='is_section_required').value

                if not stock_data:
                    return Response({"error": "Stock data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if (not stock_details):
                    return Response({"error": "Stock Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                self.insert_metal_issue_details(stock_data,stock_details,request)
                return Response({"message":"Metal Issue Created Successfully.",'pdf_url': ""}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"message": f"Missing key: {e}",'tb':tb}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"message": str(e),'data':item_details}, status=status.HTTP_400_BAD_REQUEST)
        
    def insert_non_tag_details(self,details,updated_data):
        for item in details:
            non_log_details=item
            non_log_details.update({"from_branch": updated_data['id_branch'],"date" : updated_data['entry_date'],"id_stock_status": 2,'transaction_type': 5,'ref_id': updated_data['id_issue'],"created_by": updated_data['created_by']})
            non_tag_serializer = ErpLotInwardNonTagSerializer(data=non_log_details)
            non_tag_serializer.is_valid(raise_exception=True)
            non_tag_serializer.save()
            insert_other_details(item['stone_details'],ErpLotInwardNonTagStoneSerializer,{"id_non_tag_log":non_tag_serializer.data['id_non_tag_log']})

    def insert_metal_issue_details(self,stock_data,stock_details,request):
        branch=Branch.objects.get(id_branch = stock_data['id_branch'])
        branch_date = BranchEntryDate()
        entry_date = branch_date.get_entry_date(stock_data['id_branch'])
        fy=FinancialYear.objects.get(fin_status=True)
        fin_id = fy.fin_id
        ref_no = self.generate_ref_code(stock_data,branch.short_name,fy)
        stock_data.update({"entry_date":entry_date,"ref_no":ref_no,"fin_year":fin_id,"created_by": request.user.id})
        stock_data_serializer = ErpSupplierMetalIssueSerializer(data = stock_data)
        if stock_data_serializer.is_valid(raise_exception=True):
            stock_data_serializer.save()
            stock_details=insert_other_details(stock_details,ErpSupplierMetalIssueDetailsSerializer,{"issue":stock_data_serializer.data['id_issue']})
            self.insert_non_tag_details(stock_details,stock_data_serializer.data)
            return stock_details




class ErpMetalIssueListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_branch = request.data.get('branch')
        id_branch = (id_branch) if id_branch != '' else 0

        lists = ErpSupplierMetalIssue.objects.annotate(
            pure_wt=Sum('po_metal_issue_details__pure_wt'),
            issue_weight=Sum('po_metal_issue_details__issue_weight'),
        ).values(
            'id_issue',
            'ref_no', 
            'type',
            'id_supplier__supplier_name',
            'entry_date', 
            'id_branch__name',
            'status',
            'fin_year',
            'pure_wt', 
            'issue_weight',
        )
        if from_date and to_date:
            lists = lists.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            lists = lists.filter(id_branch__in=id_branch)


        for purchase in lists:
            purchase['pk_id'] = purchase['id_issue']
            purchase['issue_type'] = 'Purchase Payment' if purchase['type']==1 else 'Metal Issue'
            purchase['issue_date'] = format_date(purchase['entry_date'])
            purchase['pure_wt'] = format(purchase['pure_wt'], '.3f')
            purchase['issue_weight'] = format(purchase['issue_weight'], '.3f')
            purchase['supplier_name'] = purchase['id_supplier__supplier_name']
            purchase['branch_name'] = purchase['id_branch__name']
            purchase['is_cancelable'] = (True if purchase['status']==0 else False)
            purchase['status_color'] = get_status_color(purchase['status'])
            purchase['status'] = dict(ErpSupplierMetalIssue.STATUS_CHOICES).get(purchase['status'], '')
        paginator, page = pagination.paginate_queryset(lists, request,None,METAL_ISSUE_COLUMN_LIST)
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        context={
            'columns':METAL_ISSUE_COLUMN_LIST,
            'actions':METAL_ISSUE_ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(lists,context) 



class ErpSupplierPaymentCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
            id_supplier = request.query_params.get('id_supplier')
            id_metal = request.query_params.get('id_metal')
            bill_setting_type = request.query_params.get('bill_setting_type')
            
            if(not id_supplier and not id_metal and not bill_setting_type):
                return Response({"error": "id_supplier,id_metal is missing...."}, status=status.HTTP_400_BAD_REQUEST)
            
            output = self.get_payment_details(id_supplier, id_metal, bill_setting_type)
            return Response(output)
    
    def get_payment_details(self, id_supplier, id_metal, bill_setting_type):
        rate_cut_and_pay_type = RetailSettings.objects.get(name='rate_cut_and_pay_type').value
        if int(rate_cut_and_pay_type)==1:
            sql = (F"""SELECT
                            1 as type,
                            pur.purchase_entry_id,
                            pur.purchase_entry_id as ref_id,
                            ent.ref_no,
                            ent.entry_date,
                            ent.payment_date,
                            DATE_FORMAT(ent.payment_date, '%d-%m-%Y') AS payment_date,
                            pro.id_metal_id,
                            false as isChecked,
                            m.metal_name,
                            COALESCE(if(s.value=0,pur_itm.pieces,recv.pieces), 0) AS pieces,
                            COALESCE(if(s.value=0,pur_itm.pure_wt,rate_cut.paid_weight), 0) AS pure_wt,
                            COALESCE(if(ent.is_rate_fixed=1,pur_itm.purchase_cost,rate_cut.paid_amount), 0) AS purchase_cost,
                            COALESCE(if(ent.is_rate_fixed=1,pur_itm.purchase_cost,rate_cut.paid_amount), 0) + COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0) AS total_amount,
                            (COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) )  AS paid_weight,
                                COALESCE(payment.paid_amount, 0) AS paid_amount,
                                COALESCE(recv.pure_wt - (COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) ), 0) AS balance_weight,
                                COALESCE(COALESCE(if(ent.is_rate_fixed=1,pur_itm.purchase_cost,rate_cut.paid_amount), 0) - COALESCE(payment.paid_amount, 0) + COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0) , 0) AS balance_amount,
                                COALESCE(charges.charges_amount, 0) AS charges_amount,
                                COALESCE(other_metal.other_metal_cost, 0) AS other_metal_cost,
                                COALESCE(stn.stone_amount, 0) AS stone_amount,
                                COALESCE(SUM(pur.total_mc_value), 0) AS mc_amount,
                                (COALESCE(SUM(pur.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0)) as mc_and_other_charges
                    
                            FROM erp_purchase_entry ent
                            LEFT JOIN erp_purchase_item_details pur ON ent.id_purchase_entry = pur.purchase_entry_id 
                            LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                            LEFT JOIN metal m ON m.id_metal = pro.id_metal_id                   
                            LEFT JOIN(
                                SELECT COALESCE(SUM(pur.pieces), 0) AS pieces,
                                    COALESCE(SUM(pur.pure_wt), 0) AS pure_wt,
                                    COALESCE(SUM(pur.purchase_cost), 0) AS purchase_cost,
                                    pur.purchase_entry_id,
                                    pro.id_metal_id
                                FROM erp_purchase_item_details pur
                                LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                                WHERE pur.purchase_entry_id is not null
                                GROUP BY pur.purchase_entry_id,pro.id_metal_id
                            ) pur_itm ON pur_itm.purchase_entry_id = pur.purchase_entry_id AND pur_itm.id_metal_id = pro.id_metal_id
                    
                            LEFT JOIN(
                                SELECT COALESCE(SUM(rec.recd_pieces), 0) AS pieces,
                                    COALESCE(SUM(rec.recd_pure_wt), 0) AS pure_wt,
                                    COALESCE(SUM(rec.recd_purchase_cost), 0) AS purchase_cost,
                                    pur.purchase_entry_id,
                                    pro.id_metal_id
                                FROM erp_purchase_item_issue_receipt_details rec
                                LEFT JOIN erp_purchase_item_issue_receipt iss ON iss.id_issue_receipt = rec.issue_receipt_id
                                LEFT JOIN erp_purchase_item_details pur ON pur.id_purchase_entry_detail = rec.purchase_entry_detail_id
                                LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                                WHERE iss.issue_type = 1 AND iss.status = 1
                                GROUP BY pur.purchase_entry_id,pro.id_metal_id
                            ) recv ON recv.purchase_entry_id = pur.purchase_entry_id AND recv.id_metal_id = pro.id_metal_id
                            
                            LEFT JOIN(SELECT sp.metal_id,sp.ref_id,COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                                    FROM erp_supplier_payment_details sp
                                    WHERE sp.type = 1
                                    GROUP BY sp.ref_id,sp.metal_id
                            ) payment ON payment.ref_id = pur.purchase_entry_id AND payment.metal_id = pro.id_metal_id
                            
                            LEFT JOIN(
                                SELECT rc.id_metal_id,
                                    rc.purchase_entry_id,
                                    COALESCE(SUM(rc.amount), 0) AS paid_amount,
                                    COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
                                FROM
                                    erp_rate_cut rc
                                where rc.type = 1
                                GROUP BY
                                    rc.purchase_entry_id,
                                    rc.id_metal_id
                            ) rate_cut
                            ON
                                rate_cut.purchase_entry_id = pur.purchase_entry_id AND rate_cut.id_metal_id = pro.id_metal_id
                            
                            LEFT JOIN(
                                    SELECT
                                        pro.id_metal_id,
                                        mi.purchase_entry_id,
                                        COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                                        COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                                    FROM
                                        erp_supplier_metal_issue_details mi
                                    LEFT JOIN erp_product pro ON
                                        pro.pro_id = mi.id_product_id
                                    LEFT JOIN erp_supplier_metal_issue d ON
                                        d.id_issue = mi.issue_id
                                    WHERE
                                        d.type = 1
                                    GROUP BY
                                        pro.id_metal_id,
                                        mi.purchase_entry_id
                            ) metal_issue
                            ON
                                metal_issue.purchase_entry_id = pur.purchase_entry_id AND metal_issue.id_metal_id = pro.id_metal_id
                    
                            LEFT JOIN(
                                    SELECT
                                        pro.id_metal_id,
                                        item.purchase_entry_id,
                                        COALESCE(SUM(charges.charges_amount), 0) AS charges_amount
                                    FROM
                                        erp_purchase_item_charges_details charges
                                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = charges.purchase_entry_detail_id
                                    LEFT JOIN erp_product pro ON
                                        pro.pro_id = item.id_product_id
                                    GROUP BY
                                        pro.id_metal_id,
                                        item.purchase_entry_id
                            ) charges
                            ON
                                charges.purchase_entry_id = pur.purchase_entry_id AND charges.id_metal_id = pro.id_metal_id
                            
                            LEFT JOIN(
                                    SELECT
                                        pro.id_metal_id,
                                        item.purchase_entry_id,
                                        COALESCE(SUM(stn.pur_stn_cost), 0) AS stone_amount
                                    FROM
                                        erp_purchase_stone_details stn
                                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = stn.purchase_entry_detail_id
                                    LEFT JOIN erp_product pro ON
                                        pro.pro_id = item.id_product_id
                                    GROUP BY
                                        pro.id_metal_id,
                                        item.purchase_entry_id
                            ) stn
                            ON
                                stn.purchase_entry_id = pur.purchase_entry_id AND stn.id_metal_id = pro.id_metal_id
                            
                            LEFT JOIN(
                                    SELECT
                                        pro.id_metal_id,
                                        item.purchase_entry_id,
                                        COALESCE(SUM(other_metal.other_metal_cost), 0) AS other_metal_cost
                                    FROM
                                        erp_purchase_other_metal other_metal
                                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = other_metal.purchase_entry_detail_id
                                    LEFT JOIN erp_product pro ON
                                        pro.pro_id = item.id_product_id
                                    GROUP BY
                                        pro.id_metal_id,
                                        item.purchase_entry_id
                            ) other_metal
                            ON
                                other_metal.purchase_entry_id = pur.purchase_entry_id AND other_metal.id_metal_id = pro.id_metal_id
                            join settings s on s.name = 'is_qc_required'
                            WHERE
                                ent.is_approved = 1 and ent.id_supplier_id = {id_supplier}
                                and pro.id_metal_id = {id_metal}
                                and ent.setting_bill_type = {bill_setting_type}
                            GROUP BY
                                pur.purchase_entry_id,
                                pro.id_metal_id;  
                                """)        
            results = execute_raw_query(sql)

        else :
            sql = (F"""SELECT
                                1 as type,
                                NULL as purchase_entry_id,
                                NULL as ref_id,
                                " " as ref_no,
                                m.id_metal,
                                false as isChecked,
                                m.metal_name,
                                COALESCE(if(s.value=0,pur_itm.pieces,recv.pieces), 0) AS pieces,
                                COALESCE(if(s.value=0,pur_itm.pure_wt,rate_cut.paid_weight), 0) AS pure_wt,
                                COALESCE(rate_cut.paid_amount, 0) AS purchase_cost,
                                COALESCE(rate_cut.paid_amount, 0) + COALESCE(SUM(pur_itm.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0) AS total_amount,
                                (COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) )  AS paid_weight,
                                COALESCE(payment.paid_amount, 0) AS paid_amount,
                                COALESCE(recv.pure_wt - (COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) ), 0) AS balance_weight,
                                COALESCE(COALESCE(rate_cut.paid_amount, 0)  - COALESCE(payment.paid_amount, 0)  - COALESCE(payment.deduction_amount, 0) + COALESCE(SUM(pur_itm.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0), 0) AS balance_amount,
                                COALESCE(charges.charges_amount, 0) AS charges_amount,
                                COALESCE(other_metal.other_metal_cost, 0) AS other_metal_cost,
                                COALESCE(stn.stone_amount, 0) AS stone_amount,
                                COALESCE(SUM(pur_itm.total_mc_value), 0) AS mc_amount,
                                (COALESCE(SUM(pur_itm.total_mc_value), 0) + COALESCE(stn.stone_amount, 0) + COALESCE(other_metal.other_metal_cost, 0)  + COALESCE(charges.charges_amount, 0)) as mc_and_other_charges
                    
                            FROM  metal m 
                            LEFT JOIN(
                                SELECT
                                    adj.id_supplier_id,
                                    adj.id_metal_id,
                                    COALESCE(SUM(adj.weight),
                                    0) AS adjusted_weight,
                                    COALESCE(SUM(adj.amount),
                                    0) AS adjusted_amount
                                FROM
                                    erp_purchase_supplier_advance_adj adj
                                WHERE
                                    adj.is_adjusted = 1
                                    and adj.id_supplier_id = {id_supplier} 
                                    and adj.setting_bill_type = {bill_setting_type}
                                GROUP BY
                                    adj.id_metal_id
                            ) adj
                            ON
                                adj.id_metal_id = m.id_metal
                    
                            LEFT JOIN(
                                SELECT COALESCE(SUM(pur.pieces), 0) AS pieces,
                                    COALESCE(SUM(pur.pure_wt), 0) AS pure_wt,
                                    COALESCE(SUM(pur.total_mc_value), 0) AS total_mc_value,
                                    COALESCE(SUM(pur.pure_wt*pur.purchase_rate), 0) AS purchase_cost,
                                    pro.id_metal_id
                                FROM erp_purchase_item_details pur
                                LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = pur.purchase_entry_id
                                LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                                WHERE ent.is_approved = 1 and ent.id_supplier_id = {id_supplier}
                                and ent.setting_bill_type = {bill_setting_type}
                                GROUP BY pro.id_metal_id
                            ) pur_itm ON  pur_itm.id_metal_id = m.id_metal
                    
                            LEFT JOIN(
                                SELECT COALESCE(SUM(rec.recd_pieces), 0) AS pieces,
                                    COALESCE(SUM(rec.recd_pure_wt), 0) AS pure_wt,
                                    COALESCE(SUM(rec.recd_purchase_cost), 0) AS purchase_cost,
                                    pur.purchase_entry_id,
                                    pro.id_metal_id
                                FROM erp_purchase_item_issue_receipt_details rec
                                LEFT JOIN erp_purchase_item_issue_receipt iss ON iss.id_issue_receipt = rec.issue_receipt_id
                                LEFT JOIN erp_purchase_item_details pur ON pur.id_purchase_entry_detail = rec.purchase_entry_detail_id
                                LEFT JOIN erp_product pro ON pro.pro_id = pur.id_product_id
                                LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = pur.purchase_entry_id
                                WHERE iss.issue_type = 1 AND iss.status = 1 and  ent.is_approved = 1 and ent.id_supplier_id = {id_supplier}
                                and ent.setting_bill_type = {bill_setting_type}
                                GROUP BY  pro.id_metal_id
                            ) recv ON  recv.id_metal_id = m.id_metal
                            
                            LEFT JOIN(SELECT sp.metal_id,sp.ref_id,COALESCE(SUM(sp.paid_amount), 0) AS paid_amount,
                            COALESCE(SUM(p.deduction_amount), 0) AS deduction_amount
                                    FROM erp_supplier_payment_details sp
                                    LEFT JOIN erp_supplier_payment p ON p.id_purchase_payment = sp.purchase_payment_id
                                    WHERE  sp.id_supplier_id = {id_supplier}
                                    and p.setting_bill_type = {bill_setting_type}
                                    GROUP BY sp.metal_id
                            ) payment ON  payment.metal_id = m.id_metal
                            
                            LEFT JOIN(
                                SELECT rc.id_metal_id,
                                    rc.purchase_entry_id,
                                    COALESCE(SUM(rc.amount), 0) AS paid_amount,
                                    COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
                                FROM
                                    erp_rate_cut rc
                                where  rc.id_supplier_id = {id_supplier} and rc.setting_bill_type = {bill_setting_type}
                                GROUP BY
                                    rc.id_metal_id
                            ) rate_cut
                            ON
                                rate_cut.id_metal_id = m.id_metal
                            
                            LEFT JOIN(
                                    SELECT
                                        pro.id_metal_id,
                                        mi.purchase_entry_id,
                                        COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                                        COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                                    FROM
                                        erp_supplier_metal_issue_details mi
                                    LEFT JOIN erp_product pro ON
                                        pro.pro_id = mi.id_product_id
                                    LEFT JOIN erp_supplier_metal_issue d ON
                                        d.id_issue = mi.issue_id
                                    LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = mi.purchase_entry_id

                                    WHERE
                                         ent.is_approved = 1 and ent.id_supplier_id = {id_supplier}
                                         and ent.setting_bill_type = {bill_setting_type}
                                    GROUP BY
                                        pro.id_metal_id
                                        
                            ) metal_issue
                            ON
                                metal_issue.id_metal_id = m.id_metal
                    
                            LEFT JOIN(
                                    SELECT
                                        pro.id_metal_id,
                                        item.purchase_entry_id,
                                        COALESCE(SUM(charges.charges_amount), 0) AS charges_amount
                                    FROM
                                        erp_purchase_item_charges_details charges
                                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = charges.purchase_entry_detail_id
                                    LEFT JOIN erp_product pro ON
                                        pro.pro_id = item.id_product_id
                                    LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                    WHERE ent.is_approved = 1 and ent.id_supplier_id = {id_supplier} and ent.setting_bill_type = {bill_setting_type}
                                    GROUP BY
                                        pro.id_metal_id
                            ) charges
                            ON
                                charges.id_metal_id = m.id_metal
                            
                            LEFT JOIN(
                                    SELECT
                                        pro.id_metal_id,
                                        item.purchase_entry_id,
                                        COALESCE(SUM(stn.pur_stn_cost), 0) AS stone_amount
                                    FROM
                                        erp_purchase_stone_details stn
                                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = stn.purchase_entry_detail_id
                                    LEFT JOIN erp_product pro ON
                                        pro.pro_id = item.id_product_id
                                    LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                    WHERE ent.is_approved = 1 and ent.id_supplier_id = {id_supplier}
                                    and ent.setting_bill_type = {bill_setting_type}
                                    GROUP BY
                                        pro.id_metal_id
                            ) stn
                            ON
                              stn.id_metal_id = m.id_metal
                            
                            LEFT JOIN(
                                    SELECT
                                        pro.id_metal_id,
                                        item.purchase_entry_id,
                                        COALESCE(SUM(other_metal.other_metal_cost), 0) AS other_metal_cost
                                    FROM
                                        erp_purchase_other_metal other_metal
                                    LEFT JOIN erp_purchase_item_details item ON item.id_purchase_entry_detail = other_metal.purchase_entry_detail_id
                                    LEFT JOIN erp_product pro ON
                                        pro.pro_id = item.id_product_id
                                    LEFT JOIN erp_purchase_entry ent ON ent.id_purchase_entry = item.purchase_entry_id
                                    WHERE ent.is_approved = 1 and ent.id_supplier_id = {id_supplier}
                                    and ent.setting_bill_type = {bill_setting_type}
                                    GROUP BY
                                        pro.id_metal_id
                            ) other_metal
                            ON
                              other_metal.id_metal_id = m.id_metal
                            join settings s on s.name = 'is_qc_required'
                            WHERE
                                 m.id_metal = {id_metal}
                            GROUP BY
                                m.id_metal;
                                """)        
            results = execute_raw_query(sql)
        
        
        opening_balance_query = F""" SELECT
                        pur.id_metal_id,
                        NULL as purchase_entry_id,
                        4 as type ,
                        false as isChecked,
                        m.metal_name as metal_name,
                        "Openning" as ref_no,
                        "-" as payment_date,
                        0 as pieces,
                        COALESCE(SUM(pur.weight), 0) as pure_wt,
                        0 as mc_and_other_charges,
                        COALESCE(SUM(pur.amount), 0) as total_amount,
                        COALESCE(SUM(metal_issue.paid_weight), 0) + COALESCE(SUM(rate_cut.paid_weight), 0) as paid_weight,
                        COALESCE(SUM(payment.paid_amount), 0) as paid_amount,
                        COALESCE( COALESCE(SUM(pur.amount), 0)  - COALESCE(SUM(payment.paid_amount), 0), 0) as balance_amount,
                        COALESCE(COALESCE(SUM(pur.weight), 0) - COALESCE(SUM(metal_issue.paid_weight), 0) - COALESCE(SUM(rate_cut.paid_weight), 0) , 0) as balance_weight

                    FROM
                        erp_purchase_supplier_opening pur
                    LEFT JOIN metal m ON m.id_metal = pur.id_metal_id
                    LEFT JOIN (
                            SELECT
                                pro.id_metal_id,
                                COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                                COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                            FROM erp_supplier_metal_issue_details mi
                            LEFT JOIN erp_product pro ON pro.pro_id = mi.id_product_id
                            LEFT JOIN erp_supplier_metal_issue d ON d.id_issue = mi.issue_id
                            WHERE mi.type = 4 and d.id_supplier_id = {id_supplier}
                            GROUP BY pro.id_metal_id
                          ) metal_issue ON metal_issue.id_metal_id = pur.id_metal_id
                    LEFT JOIN (
                        SELECT rc.id_metal_id,
                            rc.purchase_entry_id,
                            COALESCE(SUM(rc.amount), 0) AS paid_amount,
                            COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
                        FROM erp_rate_cut rc
                        where rc.id_supplier_id = {id_supplier} and rc.type = 2
                        GROUP BY rc.id_metal_id
                          ) rate_cut ON rate_cut.id_metal_id = pur.id_metal_id
                    LEFT JOIN (
                        SELECT sp.metal_id,sp.ref_id,COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                                FROM erp_supplier_payment_details sp
                                WHERE sp.type = 4 and sp.id_supplier_id = {id_supplier}
                                GROUP BY sp.metal_id
                          ) payment ON payment.metal_id = pur.id_metal_id
                    WHERE                   
                        pur.id_supplier_id = {id_supplier}
                        and pur.id_metal_id = {id_metal}
                    GROUP BY
                        pur.id_metal_id  """
        opening_balance = execute_raw_query(opening_balance_query)
        
        advance_rate_cut_query = F"""SELECT rc.id_metal_id,
                            NULL as purchase_entry_id,
                            5 as type ,
                            false as isChecked,
                            m.metal_name as metal_name,
                            "Advance Rate Cut" as ref_no,
                            "-" as payment_date,
                            0 as pieces,
                            COALESCE(SUM(rc.pure_wt), 0) as pure_wt,
                            0 as mc_and_other_charges,
                        COALESCE(SUM(rc.amount), 0) as total_amount,
                        COALESCE(SUM(rc.pure_wt), 0) as paid_weight,
                        COALESCE(SUM(payment.paid_amount), 0) as paid_amount,
                        COALESCE( COALESCE(SUM(rc.amount), 0)  - COALESCE(SUM(payment.paid_amount), 0), 0) as balance_amount,
                        COALESCE(SUM(rc.pure_wt), 0) as balance_weight
                        FROM erp_rate_cut rc
                        LEFT JOIN metal m ON m.id_metal = rc.id_metal_id
                        LEFT JOIN (
                                SELECT sp.metal_id,sp.ref_id,COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                                FROM erp_supplier_payment_details sp
                                WHERE sp.type = 5 and sp.id_supplier_id = {id_supplier}
                                GROUP BY sp.metal_id
                        ) payment ON payment.metal_id = rc.id_metal_id
                        where rc.id_supplier_id = {id_supplier} and rc.type = 3
                        and rc.id_metal_id = {id_metal}
                        GROUP BY rc.id_metal_id """
        advance_rate_cut = execute_raw_query(advance_rate_cut_query)
        
    
        job_order_payment_query = (F""" 
                SELECT COALESCE(SUM(ord_det.karigar_charges), 0) - COALESCE((pay.paid_amount), 0) as balance_amount,0 as balance_weight,COALESCE(SUM(ord_det.karigar_charges), 0) as total_amount,
                COALESCE(SUM(ord_det.karigar_charges), 0) as mc_and_other_charges,ord_det.delivered_on as entry_date,0 as isChecked,0 as paid_weight,0 as pure_wt,ord_det.detail_id as ref_id,
                COALESCE((pay.paid_amount), 0) as paid_amount,0 as pieces, CONCAT("RE-",ord.order_no) as ref_no,3 as type,ord_det.detail_id,DATE_FORMAT(ord_det.delivered_on, '%d-%m-%Y') AS payment_date
                FROM erp_job_order_details job
                LEFT JOIN erp_job_order job_ord ON job_ord.id_job_order = job.job_order_id
                LEFT JOIN erp_order_details ord_det  ON ord_det.detail_id  = job.order_detail_id
                LEFT JOIN erp_order ord ON ord.order_id = ord_det.order_id
                LEFT JOIN ( 
                        SELECT
                                sp.ref_id,
                                COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                            FROM
                                erp_supplier_payment_details sp
                            WHERE
                                sp.type = 3
                            GROUP BY
                                sp.ref_id
                    ) as pay ON pay.ref_id = ord_det.detail_id
                WHere 
                    ord.order_type = 3 and ord_det.order_status_id = 5 and job.status_id = 5
                    and job_ord.supplier_id = {id_supplier}
                GROUP BY ord_det.detail_id
                """)
        job_order_payment = execute_raw_query(job_order_payment_query)
        

        other_charges_payment = []
        other_charges_payment_query = F"""
                SELECT 
                    s.id_purchase_entry_id AS purchase_entry_id,
                    s.id_purchase_entry_id AS ref_id,
                    FALSE AS isChecked,
                    6 AS type,
                    p.ref_no AS ref_no,
                    group_concat(c.name) AS metal_name,
                    0 AS pieces,
                    0 AS pure_wt,
                    0 AS mc_and_other_charges,
                    COALESCE(SUM(s.charges_amount), 0) AS total_amount,
                    0 AS paid_weight,
                    COALESCE(payment.paid_amount,0) AS paid_amount,
                    0 AS balance_weight,
                    DATE_FORMAT(p.payment_date, '%d-%m-%Y') AS payment_date,
                    (COALESCE(SUM(s.charges_amount), 0)-COALESCE(payment.paid_amount,0)) AS balance_amount
                FROM erp_purchase_entry_charges_details s
                LEFT JOIN erp_purchase_entry p 
                    ON p.id_purchase_entry = s.id_purchase_entry_id
                left join other_charges c on c.id_other_charge = s.id_charges_id
                LEFT JOIN (
                    SELECT 
                        sp.metal_id,
                        sp.ref_id,
                        COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                    FROM erp_supplier_payment_details sp
                    WHERE sp.type = 6
                    GROUP BY sp.ref_id
                ) payment 
                    ON payment.ref_id = s.id_purchase_entry_id

                WHERE p.is_approved = 1
                and p.id_supplier_id = {id_supplier} and p.setting_bill_type = {bill_setting_type}
                GROUP BY s.id_purchase_entry_id
            """


        other_charges_payment = execute_raw_query(other_charges_payment_query)

            



        output = []
        for res in  results +   job_order_payment + other_charges_payment + advance_rate_cut + opening_balance:
            if(float(res["balance_amount"]) > 0 ):
                output.append(res)
        return (output)



    def generate_ref_code(self, data,branch_code,fy):
        code = ''
        code_settings = RetailSettings.objects.get(name='purchase_entry_code_settings').value
        code_format = RetailSettings.objects.get(name='purchase_entry_code_format').value
        fy_code = fy.fin_year_code
        fin_id = fy.fin_id
        last_code=None
        if code_settings == '0':#GENERATE CODE
            last_code=ErpSupplierPayment.objects.order_by('-id_purchase_payment').first()
        elif code_settings == '1':#GENERATE CODE WITH FY
            last_code=ErpSupplierPayment.objects.filter(fin_year=fin_id).order_by('-id_purchase_payment').first()
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
                payment_data = request.data
                payment_details = request.data.get('payment_details')
                payment_mode_details = request.data.get('payment_mode_details')
                cash_varavu = float(request.data.get('cashVaravu',0))

                if not payment_data:
                    return Response({"error": "Purchase Payment data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if int(payment_data['type']) == 1 and ((not payment_details) or  (not payment_mode_details)):
                    return Response({"error": "Purchase Payment Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch=Branch.objects.get(is_ho=1)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(branch.id_branch)
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                ref_no = self.generate_ref_code(payment_data,branch.short_name,fy)
                payment_data.update({"ref_no":ref_no,"entry_date":entry_date,"fin_year":fin_id,"cash_from_branch": branch.id_branch,"id_branch":branch.id_branch,"created_by": request.user.id})
                payment_serializer = ErpSupplierPaymentSerializer(data = payment_data)
                if payment_serializer.is_valid(raise_exception=True):
                    payment_serializer.save()
                    if int(payment_data['type']) == 5 :
                        data = {
                            "type" : 1,
                            "id_metal":payment_data['metal'],
                            "ref_id" : payment_serializer.data['id_purchase_payment'],
                            "id_supplier" : payment_data['id_supplier'],
                            "amount" : payment_data["paid_amount"],
                        }

                        serial= ErpSupplierAdvanceSerializer(data=data)
                        if(serial.is_valid(raise_exception=True)):
                            serial.save()
                            payment_details = [{
                            "type" : 5,
                            "purchase_payment" : payment_serializer.data['id_purchase_payment'],
                            "ref_id" : serial.data['id'],
                            "id_supplier" : payment_data['id_supplier'],
                            "metal":payment_data['metal'],
                            "net_amount" : payment_data["paid_amount"],
                            "paid_amount" : payment_data["paid_amount"],
                            "discount_amount" : 0,
                            }]
                    if  cash_varavu > 0 :
                        cash_varavu_details = {
                            "ref_id" : payment_serializer.data['id_purchase_payment'],
                            "type" : 1,
                            "id_supplier" : payment_data['id_supplier'],
                            "id_metal" : payment_data['metal'],
                            "adj_type" : 2,
                            "weight":0.000,
                            "amount" : cash_varavu,
                        }
                        cash_varavu_details=insert_other_details([cash_varavu_details],ErpSupplierAdvanceAdjSerializer,{})
                    payment_details=insert_other_details(payment_details,ErpSupplierPaymentDetailsSerializer,{"purchase_payment":payment_serializer.data['id_purchase_payment']})
                    payment_mode_details=insert_other_details(payment_mode_details,ErpSupplierPaymentModeDetailSerializer,{"payment_type":2,"purchase_payment":payment_serializer.data['id_purchase_payment']})
                return Response({"message":"Purchase Payment Created Successfully.",'pdf_url': ""}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
      

class ErpSupplierPaymentPrintAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        id = self.kwargs.get('pk')
        if not id:
            return Response({"error": "ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payment_queryset = ErpSupplierPayment.objects.get(id_purchase_payment=id)
            payment_details_queryset = ErpSupplierPaymentDetails.objects.filter(purchase_payment=payment_queryset)
            payment_mode_details_queryset = ErpSupplierPaymentModeDetail.objects.filter(purchase_payment=payment_queryset)
            payment_details = ErpSupplierPaymentDetailsSerializer(payment_details_queryset, many=True).data
            payment_mode_details = ErpSupplierPaymentModeDetailSerializer(payment_mode_details_queryset, many=True).data
            payment_data = {
                "id": payment_queryset.id_purchase_payment,
                "ref_no": payment_queryset.ref_no,
                "entry_date": format_date(payment_queryset.entry_date),
                "supplier_name": payment_queryset.id_supplier.supplier_name,
                "branch_name": payment_queryset.id_branch.name,
                "amount": payment_queryset.paid_amount,
                "remarks": payment_queryset.remarks,
                "payment_details": payment_details,
                "payment_mode_details": payment_mode_details,
            }
            return Response({"response_data": payment_data}, status=status.HTTP_200_OK)
        except ErpSupplierPayment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_branch = request.data.get('branch')
        lists = ErpSupplierPayment.objects.values(
            'id_purchase_payment',
            'ref_no', 
            'id_supplier__supplier_name',
            'entry_date', 
            'id_branch__name',
            'fin_year',
            'paid_amount',
        )
        if from_date and to_date:
            lists = lists.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            lists = lists.filter(id_branch__in=id_branch)


        for purchase in lists:
            purchase['pk_id'] = purchase['id_purchase_payment']
            purchase['entry_date'] = format_date(purchase['entry_date'])
            purchase['paid_amount'] = format(purchase['paid_amount'], '.2f')
            purchase['supplier_name'] = purchase['id_supplier__supplier_name']
            purchase['branch_name'] = purchase['id_branch__name']
            # purchase['is_cancelable'] = (True if purchase['status']==0 else False)
            # purchase['status_color'] = get_status_color(purchase['status'])
            # purchase['status'] = dict(ErpSupplierPayment.STATUS_CHOICES).get(purchase['status'], '')
        paginator, page = pagination.paginate_queryset(lists, request,None,METAL_ISSUE_COLUMN_LIST)
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        context={
            'columns':SUPPLIER_PAYMENT_COLUMN_LIST,
            'actions':SUPPLIER_PAYMENT_ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(lists,context) 
class ErpPurchaseReturnListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):

        from_date = request.data.get('fromDate')
        to_date = request.data.get('toDate')
        id_branch = request.data.get('branch')
        id_branch = (id_branch) if id_branch != '' else 0

        lists = ErpPurchaseReturn.objects.select_related('supplier', 'branch').annotate(
            total_gross_wt=Sum('purchase_return_details__gross_wt'),
            total_net_wt=Sum('purchase_return_details__net_wt'),
            total_pure_wt=Sum('purchase_return_details__pure_wt'),
        ).values(
            'id_purchase_return',
            'branch__short_name',
            'total_gross_wt', 
            'total_net_wt',
            'total_pure_wt',
            'entry_date',
            'supplier__supplier_name',
            'branch__name',
            'status'
        )
        if from_date and to_date:
            lists = lists.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            lists = lists.filter(branch__in=id_branch)
        
        paginator, page = pagination.paginate_queryset(lists, request,None,PURCHASE_RETURN_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,PURCHASE_RETURN_COLUMN_LIST,request.data.get('path_name',''))
        for index,purchase in enumerate(page):
            purchase['is_cancelable'] = True if (purchase['status']==1) else False
            purchase['status_color'] ='success' if (purchase['status']==1) else 'danger',
            purchase['status'] = 'Success' if (purchase['status']==1) else 'Cancel',
            purchase['sno'] = index+1
            purchase['pk_id'] = purchase['id_purchase_return']
            purchase['branch_name'] = purchase['branch__name']
            purchase['supplier_name'] = purchase['supplier__supplier_name']
            purchase['entry_date'] = format_date(purchase['entry_date'])
            purchase['total_gross_wt'] = format(purchase['total_gross_wt'], '.3f')
            purchase['total_net_wt'] = format(purchase['total_net_wt'], '.3f')
            purchase['total_pure_wt'] = format(purchase['total_pure_wt'], '.3f')

        FILTERS['isDateFilterReq'] = False
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        ACTION_LIST['is_edit_req'] = True
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
    
class ErpPurchaseReturnCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def generate_ref_code(self, data,fy):
        code = ''
        fin_id = fy.fin_id
        last_code=ErpPurchaseReturn.objects.filter(branch=data['id_branch'],fin_year=fin_id).order_by('-id_purchase_return').first()
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
        
        #code=code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code)

        return code
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                branch_date = BranchEntryDate()
                fy=FinancialYear.objects.get(fin_status=True)
                fin_id = fy.fin_id
                ref_no = self.generate_ref_code(request.data,fy)
                entry_date = branch_date.get_entry_date(request.data['id_branch'])
                request.data.update({"ref_no":ref_no,"entry_date":entry_date, "created_by":request.user.pk, "branch":request.data['id_branch'],
                                    "supplier":request.data['id_supplier']})
                item_details = request.data['item_details']
                del request.data['item_details']
                serializer = ErpPurchaseReturnSerializer(data=request.data)
                serializer.is_valid(raise_exception = True)
                serializer.save()
                for data in item_details:
                    stone_details = data['stone_details']
                    del data['stone_details']
                    data.update({"purchase_return":serializer.data['id_purchase_return']})
                    detail_serializer = ErpPurchaseReturnDetailsSerializer(data=data)
                    detail_serializer.is_valid(raise_exception = True)
                    detail_serializer.save()
                    for stone_data in stone_details:
                        stone_data.update({'stone_wt':stone_data['weight'],'stone_pcs':stone_data['piece'],'stone':stone_data['id_stone'],"purchase_return_detail":detail_serializer.data['id_purchase_return_det']})
                        stone_detail_serializer = ErpPurchaseReturnStoneDetailsSerializer(data=stone_data)
                        stone_detail_serializer.is_valid(raise_exception = True)
                        stone_detail_serializer.save()
                    self.update_stock_details({**detail_serializer.data,"stone_details":stone_details},serializer.data)
                    
                return Response({"status":True,"message":"Return Entry Created Successfully.."}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({"message": F"A database error occurred. {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"message": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def update_stock_details(self,data,purchase_return):
        item_type = data["type"]
        if int(item_type) == 2:

            tag_instance = ErpTagging.objects.get(pk=data['tag_id'])
            
            tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":purchase_return['created_by'],"tag_status":6}, partial=True)
            tag_serializer.is_valid(raise_exception=True)
            tag_serializer.save()

            log_details={
                'from_branch': purchase_return['branch'],
                'date': purchase_return['entry_date'],
                'id_stock_status': 6,
                'tag_id': data['tag_id'],
                'transaction_type': 7,
                'ref_id': data['id_purchase_return_det'],
                "created_by": purchase_return['created_by'],
            }
            log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
            log_tag_serializer.is_valid(raise_exception=True)
            log_tag_serializer.save()

        if int(item_type) == 3:
            non_log_details=data
            non_log_details.update({"pieces":data['piece'],"stone_wt":0,"dia_wt":0,"from_branch": purchase_return['branch'],"date" : purchase_return['entry_date'],"id_stock_status": 6,'transaction_type': 7,'ref_id': data['id_purchase_return_det'],"created_by": purchase_return['created_by']})
            non_tag_serializer = ErpLotInwardNonTagSerializer(data=non_log_details)
            non_tag_serializer.is_valid(raise_exception=True)
            non_tag_serializer.save()
            insert_other_details(data['stone_details'],ErpLotInwardNonTagStoneSerializer,{"id_non_tag_log":non_tag_serializer.data['id_non_tag_log']})
        
class ErpPurchaseReturnRetrieveUpdateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpPurchaseReturn.objects.all()
    serializer_class = ErpPurchaseReturnSerializer
    
    def get(self, request, pk, format=None):
        queryset = self.get_object()
        if ('changestatus' in request.query_params):
            if (queryset.status == 1):
                queryset.status = 2
            else:
                queryset.status = 1
            queryset.updated_by = self.request.user
            queryset.updated_on = datetime.now(tz=timezone.utc)
            queryset.save()
            return Response({"Message": "Purchase return status changed successfully."}, status=status.HTTP_202_ACCEPTED)
        serializer = ErpPurchaseReturnSerializer(queryset)
        output = serializer.data
        return_items = ErpPurchaseReturnDetails.objects.filter(purchase_return=queryset.id_purchase_return)
        return_items_serializer = ErpPurchaseReturnDetailsSerializer(return_items, many=True)
        for data in return_items_serializer.data:
            stone_details = ErpPurchaseReturnStoneDetails.objects.filter(purchase_return_detail=data['id_purchase_return_det'])
            stone_details_serializer = ErpPurchaseReturnStoneDetailsSerializer(stone_details, many=True)
            data.update({
                "stone_details":stone_details_serializer.data,
            })
        output.update({"item_details": return_items_serializer.data})
        return Response(output, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            queryset = self.get_object()
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(request.data['id_branch'])
            
            return_item_details = ErpPurchaseReturnDetails.objects.filter(purchase_return=queryset.id_purchase_return)
            return_item_details_serializer = ErpPurchaseReturnDetailsSerializer(return_item_details, many=True)    
            for item_data in return_item_details_serializer.data:
                if(ErpPurchaseReturnStoneDetails.objects.filter(purchase_return_detail=item_data['id_purchase_return_det']).exists()):
                    ErpPurchaseReturnStoneDetails.objects.filter(purchase_return_detail=item_data['id_purchase_return_det']).delete()
            ErpPurchaseReturnDetails.objects.filter(purchase_return=queryset.id_purchase_return).delete()
            
            request.data.update({"entry_date":entry_date, "created_by":queryset.created_by.pk, "branch":request.data['id_branch'],
                                 "supplier":request.data['id_supplier']})
            
            item_details = request.data['item_details']
            del request.data['item_details']
            
            serializer = ErpPurchaseReturnSerializer(queryset, data=request.data)
            serializer.is_valid(raise_exception = True)
            serializer.save(updated_by=self.request.user,
                            updated_on=datetime.now(tz=timezone.utc))
                  
                    
            for data in item_details:
                stone_details = data['stone_details']
                del data['stone_details']
                data.update({"purchase_return":queryset.id_purchase_return})
                detail_serializer = ErpPurchaseReturnDetailsSerializer(data=data)
                detail_serializer.is_valid(raise_exception = True)
                detail_serializer.save()
                for stone_data in stone_details:
                    stone_data.update({"purchase_return_detail":detail_serializer.data['id_purchase_return_det']})
                    stone_detail_serializer = ErpPurchaseReturnStoneDetailsSerializer(data=stone_data)
                    stone_detail_serializer.is_valid(raise_exception = True)
                    stone_detail_serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        
class ErpPurchaseReturnCancelView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        try:
            id = request.data['pk_id']
            queryset = ErpPurchaseReturn.objects.get(id_purchase_return = id)
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(queryset.branch)
            entry_datetime = datetime.combine(entry_date, datetime.now(tz=timezone.utc).time())
            update_data ={ 'canceled_reason' : request.data['cancel_reason'] ,'canceled_by' : request.user.id,'canceled_on' : entry_datetime,'status' : 2}
            serializer = ErpPurchaseReturnSerializer(queryset,update_data,partial=True)
            if serializer.is_valid(raise_exception=True):
                    serializer.save()
            purchase = ErpPurchaseReturnDetails.objects.filter(purchase_return=id)
            purchase_serializer = ErpPurchaseReturnDetailsSerializer(purchase, many=True,context={'stone_details': True, 'charges_details': True})
            response_data = serializer.data
            purchase_details = purchase_serializer.data
            for detail in purchase_details:
                item_type =detail['type']
                print(item_type)
                if int(item_type) == 2:
                    tag_instance = ErpTagging.objects.get(pk=detail['tag_id'])
                    tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by": request.user.id,"tag_status":1 }, partial=True)
                    tag_serializer.is_valid(raise_exception=True)
                    tag_serializer.save()
                    log_details={
                        'to_branch': response_data['branch'],
                        'date': entry_date,
                        'id_stock_status': 5,
                        'tag_id': detail['tag_id'],
                        'transaction_type': 7,
                        'ref_id': detail['id_purchase_return_det'],
                        "created_by": request.user.id,
                    }
                    log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                    log_tag_serializer.is_valid(raise_exception=True)
                    log_tag_serializer.save()
                if int(item_type) == 3:
                    non_log_details=detail
                    non_log_details.update({"pieces":detail['piece'],"stone_wt":0,"dia_wt":0,"to_branch": response_data['branch'],"date" : entry_date,"id_stock_status": 5,'transaction_type': 7,'ref_id': detail['id_purchase_return_det'],"created_by": request.user.id})
                    non_tag_serializer = ErpLotInwardNonTagSerializer(data=non_log_details)
                    non_tag_serializer.is_valid(raise_exception=True)
                    non_tag_serializer.save()
                    insert_other_details(detail['stone_details'],ErpLotInwardNonTagStoneSerializer,{"id_non_tag_log":non_tag_serializer.data['id_non_tag_log']})

            return Response({"message":"Purchase Return Canceled Successfully."}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)

class ErpPurchaseReturnPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def generate_print(self, id_purchase_return,request):
        instance = ErpPurchaseReturn.objects.get(id_purchase_return=id_purchase_return)
        serializer = ErpPurchaseReturnSerializer(instance)
        data = serializer.data
        item_details = ErpPurchaseReturnDetails.objects.filter(purchase_return=id_purchase_return)
        item_details_serializer = ErpPurchaseReturnDetailsSerializer(item_details, many=True)
        comp = Company.objects.latest("id_company")
        total_pure_wt,total_touch_wt,total_net_wt,total_gross_wt,purchase_amount,total_pcs,total_less_wt = 0,0,0,0,0,0,0
        for item in item_details_serializer.data:
            product_details = Product.objects.get(pro_id=item['id_product'])
            total_pcs += int(item['piece'])
            total_gross_wt += float(item['gross_wt'])
            total_net_wt += float(item['net_wt'])
            total_touch_wt += float(item['touch'])
            total_pure_wt += float(item['pure_wt'])
            total_less_wt += float(item['less_wt'])
            purchase_amount += float(item['item_cost'])
            item.update({
                "stock_type":'Tagged' if product_details.stock_type==0 else 'Non Tag',
                "id_category":product_details.cat_id.id_category
            })
        data['total_pcs'] = format(total_pcs, '.0f')
        data['total_gross_wt'] = format(total_gross_wt, '.3f')
        data['total_net_wt'] = format(total_net_wt, '.3f')
        data['total_less_wt'] = format(total_less_wt, '.3f')
        data['total_touch_wt'] = format(total_touch_wt, '.3f')
        data['total_pure_wt'] = format(total_pure_wt, '.3f')
        data['purchase_amount'] = format(purchase_amount, '.3f')
        data.update({"supplier_name":instance.supplier.supplier_name,"branch":instance.branch.name,"item_details": item_details_serializer.data,'company_detail': comp})

        save_dir = os.path.join(settings.MEDIA_ROOT, 'purchase_return')
        save_dir = os.path.join(save_dir, f'{id_purchase_return}')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        template = get_template('purchase_return_print.html')
        html = template.render(data)
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        pdf_path = os.path.join(save_dir, 'purchase_return.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'purchase_return/{id_purchase_return}/purchase_return.pdf')
        return pdf_path
    
    def get(self, request, *args, **kwargs):
        id_purchase_return = self.kwargs.get('pk')
        est_url = self.generate_print(id_purchase_return,request)
        response_data = { 'pdf_url': est_url}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
    
class ErpSupplierOpeningDetailsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_supplier = request.data.get('id_supplier')
        id_metal = request.data.get('id_metal')
        id_branch = request.data.get('id_branch')
        if(not id_supplier):
            return Response({"error": "id_supplier is missing."}, status=status.HTTP_400_BAD_REQUEST)
        if(not id_metal):
            return Response({"error": "id_metal is missing."}, status=status.HTTP_400_BAD_REQUEST)
        if(not id_branch):
            return Response({"error": "id_branch is missing."}, status=status.HTTP_400_BAD_REQUEST)
        branch_date = BranchEntryDate()
        entry_date = branch_date.get_entry_date(id_branch)
        results = get_supplier_openning_details(entry_date,id_metal,id_supplier)

        results.update({
            "balance_amount": (results['balance_amount']),
            "balance_weight": (results['balance_weight']),
            "amount": f"{abs(results['balance_amount'])} {'DR' if float(results['balance_amount']) > 0 else 'CR'}",
            "weight": f"{abs(results['balance_weight'])} {'DR' if float(results['balance_weight']) > 0 else 'CR'}",
        })
        if results:
            return Response(results)
        else:
            return Response({"error": "Invalid Details"}, status=status.HTTP_400_BAD_REQUEST) 
        
class ErpSupplierAdvanceDetailsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_supplier = request.data.get('id_supplier')
        id_metal = request.data.get('id_metal')
        if(not id_supplier):
            return Response({"error": "id_supplier is missing."}, status=status.HTTP_400_BAD_REQUEST)
        if(not id_metal):
            return Response({"error": "id_metal is missing."}, status=status.HTTP_400_BAD_REQUEST)
        query = F""" 
                    SELECT
                        adv.id_metal_id AS id_metal,
                        COALESCE(SUM(adv.weight),
                        0) AS advance_weight,
                        COALESCE(SUM(adv.amount),
                        0) AS advance_amount,
                        COALESCE((adj.adjusted_amount),
                        0) AS adjusted_amount,
                        COALESCE((adj.adjusted_weight),
                        0) AS adjusted_weight,
                        COALESCE(
                            COALESCE(SUM(adv.weight),
                            0) - COALESCE((adj.adjusted_weight),
                            0),
                            0
                        ) AS balance_wt,
                        COALESCE(
                            COALESCE(SUM(adv.amount),
                            0) - COALESCE((adj.adjusted_amount),
                            0),
                            0
                        ) AS balance_amt
                    FROM
                        erp_purchase_supplier_advance adv
                    LEFT JOIN(
                        SELECT
                            adj.id_supplier_id,
                            adj.id_metal_id,
                            COALESCE(SUM(adj.weight),
                            0) AS adjusted_weight,
                            COALESCE(SUM(adj.amount),
                            0) AS adjusted_amount
                        FROM
                            erp_purchase_supplier_advance_adj adj
                        WHERE
                            adj.is_adjusted = 1
                            and adj.id_supplier_id = {id_supplier} 
                            AND adj.id_metal_id = {id_metal} 
                        GROUP BY
                            adj.id_supplier_id,
                            adj.id_metal_id
                    ) adj
                    ON
                        adj.id_metal_id = adv.id_metal_id AND adj.id_supplier_id = adv.id_supplier_id
                    WHERE
                        adv.id_supplier_id = {id_supplier} AND adv.id_metal_id = {id_metal} 
                    GROUP BY
                        adv.id_metal_id,
                        adv.id_supplier_id;
                """
        result = generate_query_result(query)
        if result:
            return Response(result[0])
        else:
            return Response({"balance_wt": 0,"balance_amt" : 0})
        

class ErpSupplierCashVaravuAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_supplier = request.data.get('id_supplier')
        id_metal = request.data.get('id_metal')
        if(not id_supplier):
            return Response({"error": "id_supplier is missing."}, status=status.HTTP_400_BAD_REQUEST)

        query = F""" 
                    SELECT
                        COALESCE(SUM(adv.amount),
                        0) AS advance_amount,
                        COALESCE((adj.adjusted_amount),
                        0) AS adjusted_amount,
                        COALESCE(
                            COALESCE(SUM(adv.amount),
                            0) - COALESCE((adj.adjusted_amount),
                            0),
                            0
                        ) AS balance_amt
                    FROM
                        erp_purchase_supplier_advance adv
                    LEFT JOIN(
                        SELECT
                            adj.id_supplier_id,
                            COALESCE(SUM(adj.amount),
                            0) AS adjusted_amount
                        FROM
                            erp_purchase_supplier_advance_adj adj
                        WHERE
                            adj.is_adjusted = 1
                            and adj.id_supplier_id = {id_supplier} 
                            and adj.id_metal_id = {id_metal} 
                        GROUP BY
                            adj.id_supplier_id
                    ) adj
                    ON
                        adj.id_supplier_id = adv.id_supplier_id
                    WHERE
                        adv.id_supplier_id = {id_supplier} and adv.id_metal_id = {id_metal} 
                    GROUP BY
                        adv.id_supplier_id;
                """
        result = generate_query_result(query)
        if result:
            return Response(result[0])
        else:
            return Response({"balance_amt" : 0})