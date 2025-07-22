from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import transaction , IntegrityError,connection
from django.utils.timezone import now
from django.db.models import  Sum, F, ExpressionWrapper, DecimalField, When, Case , Count
from utilities.pagination_mixin import PaginationMixin
pagination = PaginationMixin()  # Apply pagination
from common.permissions import IsEmployee
from utilities.utils import format_date,date_format_with_time,generate_query_result,format_wt
from django.utils.timezone import localtime,make_aware,is_naive
from random import randint
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta, date, time
import base64
from PIL import Image
from django.core.files.images import ImageFile
from django.db.models import Q
import copy
from num2words import num2words
from core.views  import get_reports_columns_template
from branchtransfer.models import (ErpStockTransfer,ErpTagTransfer)
from branchtransfer.serializers import ( ErpStockTransferSerializer)
from .models import (
    ErpInvoice,
    BankSettlements,
    ErpInvoiceOtherMetal,
    ErpInvoiceSalesDetails,
    ErpInvoiceOldMetalDetails,
    ErpInvoiceSalesReturn,
    ErpInvoiceStoneDetails,
    ErpInvoiceItemCharges,
    ErpInvoicePaymentModeDetail,
    ErpInvoiceSchemeAdjusted,
    ErpInvoiceCustomerAddress,
    ErpIssueReceipt,
    ErpIssueReceiptPaymentDetails,
    ErpReceiptCreditCollection,
    ErpReceiptRefund,
    ErpReceiptAdvanceAdj,
    ErpInvoiceDiscount,
    ErpInvoiceDiscountOldMetalDetails,
    ErpInvoiceDiscountSalesDetails,
    ErpInvoiceDiscountPaymentModeDetail,
    ErpAdvanceAdj,
    ErpCustomerSalesLog, ErpItemDelivered, ErpItemDeliveredImages,ErpInvoiceGiftDetails,
    ErpLiablityEntry, ErpLiablityEntryPament, ErpLiablityPaymentModeDetails, ErpLiablityPaymentEntryDetails,
)
from .serializers import (
    ErpInvoiceSerializer,
    BankSettlementsSerializer,
    ErpInvoiceSalesDetailsSerializer,
    ErpInvoiceOldMetalDetailsSerializer,
    ErpInvoiceSalesReturnSerializer,
    ErpInvoiceStoneDetailsSerializer,
    ErpInvoiceItemChargesSerializer,
    ErpInvoicePaymentModeDetailSerializer,
    ErpInvoiceSchemeAdjustedSerializer,
    ErpInvoiceCustomerAddressSerializer,
    ErpInvoiceOtherMetalSerializer,
    ErpIssueReceiptSerializer,
    ErpIssueReceiptPaymentDetailsSerializer,
    ErpReceiptCreditCollectionSerializer,
    ErpReceiptAdvanceAdjSerializer,
    ErpReceiptRefundSerializer,
    ErpInvoiceDiscountSerializer,
    ErpInvoiceSalesDiscountDetailsSerializer,
    ErpInvoiceStoneDiscountDetailsSerializer,
    ErpInvoiceDiscountItemChargesSerializer,
    ErpInvoiceDiscountOtherMetalSerializer,
    ErpInvoiceDiscountOldMetalDetailsSerializer,
    ErpInvoiceDiscountPaymentModeDetailSerializer,
    ErpAdvanceAdjSerializer,
    ErpCustomerSalesLogSerializer, ErpItemDeliveredSerializer, ErpItemDeliveredImagesSerializer,ErpInvoiceGiftDetailsSerializer,
    get_invoice_no, ErpLiablityEntrySerializer, ErpLiablityEntryPamentSerializer, ErpLiablityPaymentModeDetailsSerializer, ErpLiablityPaymentEntryDetailsSerializer,
)
from estimations.models import ErpEstimation,ErpEstimationSalesDetails,ErpEstimationOldMetalDetails
from estimations.serializers import ErpEstimationSalesDetailsSerializer,ErpEstimationOldMetalDetailsSerializer
from retailmasters.views import BranchEntryDate

from retailcataloguemasters.models import (Product, CounterWiseTarget, CategoryPurityRate, Category, Purity, Section)
from retailcataloguemasters.serializers import (CategoryPurityRateSerializer)

from retailmasters.serializers import (MetalRatesSerializer,IncentiveSettingsSerializer,IncentiveTransactionsSerializer,CustomerDepositSerializer,
                                       CompanySerializer)
from retailmasters.models import (FinancialYear,MetalRates,City,State,Country,Area,Branch, ErpDayClosed, PaymentMode,IncentiveSettings,IncentiveTransactions,
                                  ERPOrderStatus, Profile,CustomerDeposit, Company, DepositMaster,State, Purity)
from employees.models import (Employee)
from accounts.models import (User)
from core.models import (EmployeeOTP)
from retailsettings.models import (RetailSettings)
from customers.models import CustomerAddress,Customers
from customers.serializers import CustomerAddressSerializer
from customerorder.models import (ERPOrder,ERPOrderDetails)
from inventory.views import convert_to_code_word
from customerorder.serializers import (ErpOrdersSerializer, ErpOrdersDetailSerializer)
from inventory.models import (ErpTagging,ErpTaggingStone, ErpTaggingContainerLogDetails,ErpTaggingLogDetails,ErpTagOtherMetal,ErpTagCharges,ErpTagAttribute)
from inventory.serializers import ErpTaggingLogSerializer,ErpLotInwardNonTagSerializer,ErpLotInwardNonTagStoneSerializer,ErpTaggingSerializer
from managescheme.models import SchemeAccount
from managescheme.serializers import SchemeAccountSerializer
from schememaster.models import SchemeBenefitSettings
from utilities.constants import FILTERS,ITEM_TYPE_CHOICES
from utilities.utils import format_currency,format_date
from .constants import (ACTION_LIST,INVOICE_COLUMN_LIST, ISSUE_RECEIPT_COLUMN_LIST,SETTLEMENT_COLUMN_LIST,BILLWISE_TRANSACTION_REPORT,
                        ISSUERECIEPTWISE_TRANSACTION_REPORT, JEWEL_NOT_DELIVERED_COLUMN_LIST, LIABLITY_ENTRY_COLUMNS, LIABLITY_ENTRY_ACTION_LIST,
                        LIABLITY_PAYMENT_ENTRY_COLUMNS, LIABLITY_PAYMENT_ENTRY_ACTION_LIST,ERP_CUSTOMER_SALES_LOG_ACTION_LIST,ERP_CUSTOMER_SALES_LOG_COLUMNS)
from datetime import datetime
from django.utils import timezone
from django.template.loader import get_template
from collections import defaultdict
import os
import re
from xhtml2pdf import pisa
import io
import qrcode
import pytz
from django.conf import settings
import traceback
import json
class ErpInvoiceCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpInvoice.objects.all()
    serializer_class = ErpInvoiceSerializer
    
    def get(self, request, *args, **kwargs):
        erp_invoice_id = self.kwargs.get('pk')
        response_data = self.get_invoice_data(erp_invoice_id, request)
        response_ = {"response_data": response_data}
        return Response(response_, status=status.HTTP_200_OK)

    def get_invoice_data(self,erp_invoice_id, request):
        template_type = RetailSettings.objects.get(name='bill_print_template').value
        metal_rate_type = int(RetailSettings.objects.get(name='metal_rate_type').value)
        metalrates = MetalRates.objects.all().latest('rate_id')
        metalrates_serializer = MetalRatesSerializer(metalrates)
        category_rates_data = {}
        category_rates = CategoryPurityRate.objects.filter(show_in_listing=True)
        category_rates_serializer = CategoryPurityRateSerializer(category_rates, many=True)
        inv = ErpInvoice.objects.get(erp_invoice_id=erp_invoice_id)
        inv_serializer = ErpInvoiceSerializer(inv)
        sales_details = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id=inv)
        sale_serializer = ErpInvoiceSalesDetailsSerializer(sales_details, many=True,context={'stone_details': True, 'charges_details': True})
        purchase_details = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id=inv)
        purchase_serializer = ErpInvoiceOldMetalDetailsSerializer(purchase_details, many=True)
        scheme_adjusted = ErpInvoiceSchemeAdjusted.objects.filter(invoice_bill_id=inv)
        gift_adjusted = ErpInvoiceGiftDetails.objects.filter(invoice_bill_id=inv)
        scheme_adjusted_serializer = ErpInvoiceSchemeAdjustedSerializer(scheme_adjusted, many=True)
        gift_adjusted_serializer = ErpInvoiceGiftDetailsSerializer(gift_adjusted, many=True)
        
        inv_payment_details = ErpInvoicePaymentModeDetail.objects.filter(invoice_bill_id=inv)
        payment_details_serializer = ErpInvoicePaymentModeDetailSerializer(inv_payment_details, many=True)
        return_details = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id=inv)
        return_details_serializer = ErpInvoiceSalesReturnSerializer(return_details,many=True)
        jewel_not_deliver = ErpItemDelivered.objects.filter(bill=inv)
        jewel_not_deliver_serializer = ErpItemDeliveredSerializer(jewel_not_deliver,many=True)
        company = Company.objects.latest("id_company")
        company_serializer = CompanySerializer(company, context={'request':request})
        state = State.objects.latest("id_state")
        emp = Employee.objects.filter(pk = inv.id_employee.pk).get()
        # emp_name = inv_serializer.data['created_by_emp']
        emp_name = emp.firstname
        emp_code = emp.emp_code
        emp_name_query  =  generate_query_result(f"""SELECT GROUP_CONCAT(DISTINCT concat(emp.firstname)) as emp_name FROM erp_invoice_sales_details sa  
                                                LEFT JOIN erpemployee emp ON emp.id_employee = sa.ref_emp_id_id
                                                Where sa.invoice_bill_id_id = {inv.pk} GROUP BY sa.invoice_bill_id_id; """)
        if emp_name_query :
            emp_name = emp_name_query[0]['emp_name']

        # partly sale
        partly_sold_details = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id=inv,is_partial_sale = 1)
        partly_sold_details_serializer = ErpInvoiceSalesDetailsSerializer(partly_sold_details, many=True)
        for partly in partly_sold_details_serializer.data:
            queryset = ErpTagging.objects.filter(tag_id=partly["tag_id"]).get()
            sold_pcs = sold_grosswt = 0
            sold_details = ErpInvoiceSalesDetails.objects.filter(tag_id=queryset.tag_id,invoice_bill_id__invoice_status = 1)
            sold_data = ErpInvoiceSalesDetailsSerializer(sold_details,many=True,context={"stone_details":True}).data
            for item, sold in zip(sold_data, sold_details):
                sold_pcs += float(sold.pieces)
                sold_grosswt += float(sold.gross_wt)           
            partly.update({
                "tag_gwt":format(float(queryset.tag_gwt),'.3f'),
                "sold_gwt":format(sold_grosswt,'.3f'),
                "blc_gwt":format(float(queryset.tag_gwt) - float(sold_grosswt),'.3f'),
            })
        
        for cat_rate_item in category_rates_serializer.data:
            category_obj = Category.objects.filter(id_category=cat_rate_item['category']).first()
            if category_obj.cat_code == 'GO':
                category_rates_data.update({
                    "gold_rate":cat_rate_item['rate_per_gram']
                })
            if category_obj.cat_code == 'SO':
                category_rates_data.update({
                    "silver_rate":cat_rate_item['rate_per_gram']
                })
            if category_obj.cat_code == 'GC':
                category_rates_data.update({
                    "gold_coin":cat_rate_item['rate_per_gram']
                })
            if category_obj.cat_code == 'SC':
                category_rates_data.update({
                    "silver_coin":cat_rate_item['rate_per_gram']
                })
        # partly sale

        response_data = inv_serializer.data
        sales_details = sale_serializer.data
        purchase_details = purchase_serializer.data
        return_details = return_details_serializer.data
        payment_details = payment_details_serializer.data
        scheme_details = scheme_adjusted_serializer.data
        gift_details = gift_adjusted_serializer.data
        metal_rate_data = metalrates_serializer.data
        jewel_not_deliver_details = jewel_not_deliver_serializer.data
        sgst_cost =0
        cgst_cost =0
        igst_cost =0
        tax_per=0
        total_taxable =0
        total_nwt =0
        total_gwt =0
        total_mc_value =0
        total_wastage_weight = 0
        total_pur_nwt =0
        total_pur_lwt =0
        total_pur_gwt =0
        total_pur_pure_wt = 0
        total_itm_cost =0
        deposit_bill  = None if inv.due_amount > 0 else inv.deposit_bill.first()
        advance_adj_bill  =inv.advance_adj_invoices.all()
        deposit_amount = 0
        sr_sgst_cost =0
        sr_cgst_cost =0
        sr_igst_cost =0
        sr_tax_per=0
        sr_total_taxable =0
        sr_total_nwt =0
        sr_total_gwt =0
        sr_total_pcs =0
        advance_adj_amount = 0
        total_chit_amount = 0
        gift_amount = 0
        total_jnd_wt = 0
        total_jnd_piece = 0
        rate_per_gram = 0
        total_amt = 0
        total_dis_amt = 0

        if(advance_adj_bill):
            for adj_bill in advance_adj_bill:
                advance_adj_amount += float(adj_bill.adj_amount)
        if(deposit_bill):
            deposit_amount = format(deposit_bill.amount, '.2f')

        metal_rate_data.update({
            "silver_coin_rate": Decimal(Decimal(metalrates.silver_G) + Decimal(5))
        })
        cus_address = CustomerAddress.objects.filter(customer=response_data['id_customer']).first()
        
        company_strip_address = None
        if cus_address != None :
            
            address1 = cus_address.line1 if (cus_address.line1 and cus_address.line1 != None and cus_address.line1 != '') else ''
            address2 = cus_address.line2 if (cus_address.line2 and cus_address.line2 != None and cus_address.line2 != '') else ''
            address3 = cus_address.line3 if (cus_address.line3 and cus_address.line3 != None and cus_address.line3 != '') else ''
            company_strip_address = (
            f"{address1} {address2} {address3}, {cus_address.city.name}, {cus_address.state.name}. {cus_address.pincode}".strip()
            )
            if cus_address.line1!=None and cus_address.line1!='':
                response_data.update({"address":cus_address.line1})
                response_data.update({"cus_address1":cus_address.line1})
            if cus_address.line2!=None and cus_address.line2!='':
                response_data.update({"cus_address2":cus_address.line2})
            if cus_address.line3!=None and cus_address.line2!='':
                response_data.update({"cus_address3":cus_address.line3})
            if cus_address.city!=None and cus_address.city!='':
                response_data.update({"city":cus_address.city.name})
            if cus_address.pincode!=None and cus_address.pincode!='':
                response_data.update({"pin_code":cus_address.pincode})
            if cus_address.area!=None and cus_address.area!='':
                response_data.update({"area":cus_address.area.area_name})
            response_data.update({"company_strip_address":company_strip_address})

        stone_amount = 0
        for item in sales_details:
            if (int(item.get('weight_show_in_print', 1)) == 0 and int(template_type) == 1):
                if (int(item.get('weight_show_in_print_purity', 1)) != 0):
                    item['weight_show_in_print'] = 1
                
            wt_code = ''
            print(float(item.get('taxable_amount', 0)) + float(item.get('discount_amount', 0)),item.get('taxable_amount', 0))
            item['total_mc'] = item['total_mc_value']
            item['va'] = item['wastage_percentage']
            item['va_wt'] = item['wastage_weight']
            amount = float(item.get('taxable_amount', 0)) + float(item.get('discount_amount', 0))
            item['amount'] = format(amount, '.2f')  # keep this as string if needed for display
            total_amt += amount
            total_dis_amt += float(item.get('discount_amount', 0))
            if len(item['stone_details']) > 0:
                for stn_itm in item['stone_details']:
                    stone_amount += float(stn_itm['stone_amount'])
            if(float(item['mc_discount_amount']) > 0) :
                item_mc = float(item['total_mc_value']) - float(item['mc_discount_amount'])
                if float(item_mc) < 0:
                    item['total_mc_value'] = 0
                else:
                    item['total_mc_value'] = format(item_mc,'.2f')
            if(float(item['wastage_discount']) > 0) :
                item['wastage_percentage'] = (item['wastage_percentage_after_disc'])
                item['wastage_weight'] = format(((float(item['wastage_percentage'])*float(item['net_wt']))/100),'.3f')
            if (int(item.get('weight_show_in_print', 1)) == 0):
                wt_code = convert_to_code_word(float(item.get('net_wt', 0)))
            else:
                total_nwt += float(item.get('net_wt', 0))
            product_obj = Product.objects.filter(pro_id=item['id_product']).first()
            purity_obj = Purity.objects.filter(id_purity=item['id_purity']).first()
            item.update({"wt_code":wt_code,"stone_amount":format(stone_amount,'.2f'),
                         "hsn_code":product_obj.hsn_code, "purity_name":purity_obj.purity})

            total_gwt += float(item.get('gross_wt', 0))
            total_wastage_weight += float(item.get('wastage_weight', 0))
            sgst_cost += float(item.get('sgst_cost', 0))
            cgst_cost += float(item.get('cgst_cost', 0))
            igst_cost += float(item.get('igst_cost', 0))
            total_taxable += float(item.get('taxable_amount', 0))
            tax_per += float(item.get('tax_percentage', 0))
            total_itm_cost += float(item.get('item_cost', 0))
            total_mc_value += float(item.get('total_mc_value', 0))
            rate_per_gram = float(item.get('rate_per_gram', 0))

        for item in jewel_not_deliver_details:
            total_jnd_wt += float(item.get('weight', 0))
            total_jnd_piece += float(item.get('piece', 0))


        for item in purchase_details:
            custom_less_weight = float(float(item.get('gross_wt', 0)) - float(item.get('pure_weight', 0)))
            item.update({"custom_less_weight" : format(float(custom_less_weight) , '.3f')})
            total_pur_gwt += float(item.get('gross_wt', 0))
            total_pur_lwt += float(custom_less_weight)
            total_pur_nwt += float(item.get('net_wt', 0))
            total_pur_pure_wt += float(item.get('pure_weight', 0))
        
        for item in return_details:
            print(item['invoice_sale_item_details'])
            # item.update(item['invoice_sale_item_details'])
            sr_total_pcs += float(item.get('pieces', 0))
            sr_total_gwt += float(item.get('gross_wt', 0))
            sr_total_nwt += float(item.get('net_wt', 0))
            sr_sgst_cost += float(item.get('sgst_cost', 0))
            sr_cgst_cost += float(item.get('cgst_cost', 0))
            sr_igst_cost += float(item.get('igst_cost', 0))
            sr_total_taxable += float(item.get('taxable_amount', 0))
            sr_tax_per += float(item.get('tax_percentage', 0))
        cash =0 
        for item, instance in zip(payment_details, inv_payment_details):
            mode_name = instance.payment_mode.mode_name
            if(int(template_type) == 2 and instance.payment_mode.pk == 1 ):
                cash += float(item["payment_amount"])
            else:   
                item.update({
                    "mode_name":mode_name
                })
        chit_number = ''
        for item, instance in zip(scheme_details, scheme_adjusted):
           
            # item.update({
            #     "closing_amount":instance.id_scheme_account.closing_amount
            # })
            chit_number = item['scheme_acc_number']
            total_chit_amount += float(item['closing_amount'])
            
        for item, instance in zip(gift_details, gift_adjusted):
               
            # item.update({
            #     "closing_amount":instance.id_scheme_account.closing_amount
            # })
            gift_amount += float(item['amount'])

        credit_bill  = inv.deposit_bill.first() if inv.due_amount > 0 else None
        credit_no =''
        if credit_bill:
            credit_no = credit_bill.bill_no
        
        if sales_details:
            tax_per= tax_per / len(sales_details)
            response_data['total_gwt'] = format(total_gwt, '.3f')
            response_data['total_nwt'] = format(total_nwt, '.3f')
            response_data['total_wastage_weight'] = format(total_wastage_weight, '.3f')
            response_data['total_mc_value'] = format(total_mc_value,'.2f')
            response_data['total_taxable'] = format(total_taxable,'.2f')
            response_data['total_itm_cost'] = format(total_itm_cost,'.2f')
            response_data['sgst_cost'] = format(sgst_cost, '.3f')
            response_data['cgst_cost'] = format(cgst_cost, '.3f')
            response_data['igst_cost'] = format(igst_cost, '.3f')
            response_data['tax_per'] = round(tax_per, 2)
            response_data['igst_per'] = round(tax_per, 2) 
            response_data['cgst_per'] = round(tax_per / 2, 2)
            response_data['sgst_per'] = round(tax_per / 2, 2)

        if return_details:
            tax_per= tax_per / len(return_details)
            response_data['sr_total_pcs'] = sr_total_pcs
            response_data['sr_total_gwt'] = format(sr_total_gwt, '.3f')
            response_data['sr_total_nwt'] = format(sr_total_nwt, '.3f')
            response_data['sr_total_taxable'] = format(sr_total_taxable,'.2f')
            response_data['sr_sgst_cost'] = format(sr_sgst_cost, '.3f')
            response_data['sr_cgst_cost'] = format(sr_cgst_cost, '.3f')
            response_data['sr_igst_cost'] = format(sr_igst_cost, '.3f')
            response_data['sr_tax_per'] = round(sr_tax_per, 2)
            response_data['sr_igst_per'] = round(sr_tax_per, 2) 
            response_data['sr_cgst_per'] = round(sr_tax_per / 2, 2)
            response_data['sr_sgst_per'] = round(sr_tax_per / 2, 2)

        if jewel_not_deliver_details:
            response_data['total_jnd_piece'] = format(total_jnd_piece,'.3f')
            response_data['total_jnd_wt'] = format(total_jnd_wt,'.3f')

        response_data['total_pur_nwt'] = format(total_pur_nwt,'.3f')
        response_data['total_pur_gwt'] = format(total_pur_gwt,'.3f')
        response_data['total_pur_lwt'] = format(total_pur_lwt,'.3f')
        response_data['total_pur_pure_wt'] = format(total_pur_pure_wt,'.3f')
        response_data['total_amt'] = format(total_amt,'.2f')
        response_data['total_dis_amt'] = format(total_dis_amt,'.2f')

        response_data['sales_details'] = sales_details
        response_data['jewel_not_deliver_details'] = jewel_not_deliver_details
        response_data['purchase_details'] = purchase_details
        response_data['scheme_details'] = scheme_details
        response_data['gift_details'] = gift_details
        response_data['emp_name'] = emp_name
        response_data['emp_code'] = emp_code
        response_data['payment_details'] = payment_details
        response_data['return_details'] = return_details
        response_data['metal_rates'] = metal_rate_data
        response_data['metal_rate_type'] = metal_rate_type
        response_data['category_rates_data'] = category_rates_data
        response_data['advance_adj_amount'] = advance_adj_amount
        response_data['total_chit_amount'] = total_chit_amount
        response_data['gift_amount'] = gift_amount
        response_data['rate_per_gram'] = rate_per_gram 
        response_data['cash'] = cash 
        response_data['chit_number'] = chit_number 
        response_data['balance_amount'] = float(response_data['net_amount']) - float(response_data['received_amount']) - float(response_data['due_amount']) - float(total_chit_amount)
        response_data['amount_in_words'] = num2words(response_data['net_amount'], lang='en_IN') + " Only"
        if  float(response_data['balance_amount']) > 0 :

            response_data['show_balance_amount'] =  True
        else :

            response_data['show_balance_amount'] =  False

        if  response_data['balance_amount'] > 0 :

            response_data['balance_amount'] =  format_currency(response_data['balance_amount'])
        else :
            response_data['balance_amount'] = 'NIL'



        response_data['company_name'] =   company.company_name
        response_data['company_strip_address'] =   company_strip_address
        response_data['counter_name'] =   inv.id_counter.counter_name
        response_data['address1'] =   company.address1
        response_data['address2'] =   company.address2
        response_data['pincode'] =   company.pincode
        response_data['gst_number'] =   company.gst_number
        response_data['mobile'] =   company.mobile
        response_data['company_logo'] =   company_serializer.data['image']
        response_data['state_code'] =   state.state_code
        
        
        
        
        
        
        
        response_data['deposit_amount'] =  deposit_amount 
        response_data['credit_no'] =  credit_no 
        response_data['invoice_data'] = get_invoice_no(inv_serializer.data)
        response_data['partly_sold_details'] = partly_sold_details_serializer.data
        print(response_data)
        # pdf_url = self.genertate_invoice_print(erp_invoice_id,request,response_data)
        return response_data        
 

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                invoice_data = request.data.get('invoice')
                id_emp = request.data.get('invoice')["id_employee"]
                return_cash_amount = float(request.data.get('invoice').get('return_cash_amount',0))
                sales_details = request.data.get('sales_details')
                purchase_details = request.data.get('purchase_details')
                return_details = request.data.get('return_details',[])
                scheme_details = request.data.get('scheme_details',[])
                gift_details = request.data.get('gift_details',[])
                payment_details=request.data.get('payment_details')
                advance_details=request.data.get('advance_adjusted_details',[])
                customer_deposit_details=request.data.get('deposit_details',[])
                item_delivered_details=request.data.get('item_delivered_details',[])
                allow_bill_date_change=request.data.get('allow_bill_date_change')
                isDateChangeded=request.data.get('isDateChangeded')
                entryDate=request.data.get('entryDate')
                counter = request.data.get('invoice')["id_counter"]
                print("counter",counter)

                if not invoice_data:
                    return Response({"error": "Invoice data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if (not sales_details and not purchase_details and not return_details):
                    return Response({"error": "Invoice Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                fy=FinancialYear.objects.get(fin_status=True)
                address ={}
                if  invoice_data['id_customer']:
                    customer = Customers.objects.get(id_customer=invoice_data['id_customer'])
                    # customer_name =  customer.firstname
                    customer_mobile =  customer.mobile   

                    address = CustomerAddress.objects.filter(customer=invoice_data['id_customer']).first()
                    if address:
                        address = CustomerAddressSerializer(address).data
                        area    = Area.objects.filter(id_area=address['area']).get()
                        country = Country.objects.filter(id_country=address['country']).get()
                        state   = State.objects.filter(id_state=address['state']).get()
                        city    = City.objects.filter(id_city=address['city']).get()
                        address.update({"area_name":area.area_name,"country_name":country.name,"state_name":state.name,"city_name":city.name})
                        print(address)
                invoice_date = branch_date.get_entry_date(invoice_data['id_branch'])
                if(allow_bill_date_change and isDateChangeded and entryDate):
                    invoice_date = entryDate
                invoice = self.generate_invoice_no(invoice_data['id_branch'],fy,request,invoice_data['setting_bill_type'],invoice_date)
                invoice.update({"customer_mobile":customer_mobile,"invoice_date":invoice_date,"created_by": request.user.id})
                invoice_data.update(invoice)
                invoice_data.update({"id_employee":id_emp, "created_by":request.user.id})
                inv_serializer = ErpInvoiceSerializer(data = invoice_data,context={"invoice_no":True})
                if inv_serializer.is_valid(raise_exception=True):
                    inv_serializer.save()
                    erp_invoice_id = inv_serializer.data['erp_invoice_id']
                    invoice_data.update(inv_serializer.data)
                    # print("yyyyyyyyyyyyyyyyyyyy","invoice_data",invoice_data, "erp_invoice_id",erp_invoice_id, "salses_details",sales_details )
                    if sales_details:
                        print("hjkl")
                        sales_details = self.insert_sales_details(sales_details,erp_invoice_id,invoice_data)
                        print("hjkl")
                    
                    if purchase_details:

                        purchase_details = self.insert_purchase_details(purchase_details,erp_invoice_id,invoice_data)

                    if scheme_details:

                        scheme_details = self.insert_scheme_details(scheme_details,erp_invoice_id)
                        
                    if gift_details:
    
                        gift_details = self.insert_gift_details(gift_details,erp_invoice_id)
                        
                    if return_details:
                       
                       for ret_item in return_details:
                           if ret_item['invoice_sale_item_id']!=None:
                            invoice_sale_item_id = ret_item['invoice_sale_item_id']
                            query_set = ErpInvoiceSalesDetails.objects.get(invoice_sale_item_id =invoice_sale_item_id)
                            query_set.status = 2
                            query_set.save()

                            if int(ret_item['tax_id'])==0:
                                ret_item.update({"tax_id" : None, "tax_type" : 2})


                       return_details = insert_other_details(return_details,ErpInvoiceSalesReturnSerializer,{"invoice_bill_id":erp_invoice_id})

                    if payment_details:
                       
                        for payment in payment_details:
                            payment.update({'payment_mode' : payment['id_mode']})

                        payment_details = insert_other_details(payment_details,ErpInvoicePaymentModeDetailSerializer,{"invoice_bill_id":erp_invoice_id})

                    if return_cash_amount > 0:

                        return_cash_amount_details = {
                            "payment_type": 2,
                            "payment_mode": 1,
                            "payment_amount": return_cash_amount,
                        }
                        return_cash_amount_details = insert_other_details([return_cash_amount_details],ErpInvoicePaymentModeDetailSerializer,{"invoice_bill_id":erp_invoice_id})
                        print("payement Details Updated")

                    advance_adj_amount = 0
                    if advance_details:
                       
                        for adv in advance_details:
                            advance_adj_amount+=float(adv['utilized_amount'])
                            adv.update({'receipt' : adv['id_issue_receipt'],
                            'adj_amount' : adv['utilized_amount'],
                            'id_customer':invoice_data['id_customer'],
                            })

                        advance_details = insert_other_details(advance_details,ErpReceiptAdvanceAdjSerializer,{"invoice_bill_id":erp_invoice_id})

                    if invoice_data.get('deposit_amount'): 

                        branch = Branch.objects.get(id_branch=invoice_data['id_branch'])

                        bill_no = generate_issue_receipt_billno({'branch':invoice_data['id_branch'],'type':2,'setting_bill_type':invoice_data['setting_bill_type']}, branch.short_name, fy, 1)

                        deposit_details = { 'issue_type':None,'type':2,'receipt_type':3,'fin_year':fy.fin_id,'bill_date':invoice_date,'branch':invoice_data['id_branch'],'bill_no':bill_no,'customer':invoice_data['id_customer'],'setting_bill_type': invoice_data['setting_bill_type'],'remarks': f"Against Invoice : {invoice_data['inv_no']['invoice_no']}",
                                           'id_counter': inv_serializer.data['id_counter'],'deposit_bill':erp_invoice_id,'amount':invoice_data.get('deposit_amount'),'weight':0,"created_by": request.user.id,"employee": id_emp}

                        deposit_details = insert_other_details([deposit_details],ErpIssueReceiptSerializer,{"invoice_bill_id":erp_invoice_id})

                    if int(invoice_data['is_credit']) == 1 and float(invoice_data.get('due_amount',0)) > 0 : 

                        branch = Branch.objects.get(id_branch=invoice_data['id_branch'])

                        bill_no = generate_issue_receipt_billno({'branch':invoice_data['id_branch'],'type':1,'setting_bill_type':invoice_data['setting_bill_type']}, branch.short_name, fy, 1)

                        deposit_details = { 'type':1,'issue_type':1,'receipt_type':None,'fin_year':fy.fin_id,'bill_date':invoice_date,'branch':invoice_data['id_branch'],'bill_no':bill_no,'customer':invoice_data['id_customer'],
                                            'id_counter': inv_serializer.data['id_counter'],'deposit_bill':erp_invoice_id,'amount':invoice_data.get('due_amount'),'weight':0,"created_by": request.user.id,"employee": id_emp,'remarks': f"Against Invoice : {invoice_data['inv_no']['invoice_no']}",'ref_id':erp_invoice_id,'setting_bill_type': invoice_data['setting_bill_type']}

                        deposit_details = insert_other_details([deposit_details],ErpIssueReceiptSerializer,{"invoice_bill_id":erp_invoice_id})

                    
                    invoice_no = get_invoice_no(inv_serializer.data)
                    if len(customer_deposit_details) > 0:
                        for cus_depo_detail in customer_deposit_details:
                            # print(cus_depo_detail)
                            CustomerDeposit.objects.filter(id=cus_depo_detail['id']).update(bill=erp_invoice_id)
                            
                    if len(item_delivered_details) > 0:
                        branch = Branch.objects.get(id_branch=invoice_data['id_branch'])
                        for item_del in item_delivered_details:
                            item_del.update({"customer":customer.pk, "entry_date":invoice_date,
                                             "bill":inv_serializer.data['erp_invoice_id'], "branch":branch.pk})
                            item_deli_serializer = ErpItemDeliveredSerializer(data=item_del)
                            item_deli_serializer.is_valid(raise_exception=True)
                            item_deli_serializer.save()
                            if(len(item_del['images'])>0):
                                for item_del_index, item_del_images in enumerate(item_del['images']):
                                    b = ((base64.b64decode(item_del_images['preview']
                                                [item_del_images['preview'].find(",") + 1:])))
                                    img = Image.open(io.BytesIO(b))
                                    filename = 'item_delivered_image.jpeg'
                                    img_object = ImageFile(io.BytesIO(
                                            img.fp.getvalue()), name=filename)
                                    item_del_images.update({"item_delivered_image": img_object, "name":str(item_del_index + 1) + "_" +str(datetime.now().strftime('%Y%m%d%H%M%S'))}) 
                                    item_del_images.update({"erp_item_delivered":item_deli_serializer.data['id_item_delivered']})
                                    item_deli_images_serializer = ErpItemDeliveredImagesSerializer(data=item_del_images)
                                    item_deli_images_serializer.is_valid(raise_exception=True)
                                    item_deli_images_serializer.save()  


                 #   pdf_url = self.genertate_invoice_print(erp_invoice_id,request,data)

                    data = self.get_invoice_data(erp_invoice_id, request)

                    return Response({"message":"Invoice Created Successfully.","response_data": data,"invoice_id":erp_invoice_id,"pdf_path":"billing/print"}, status=status.HTTP_201_CREATED)
                return Response({"error":ErpInvoiceSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        
    def generate_invoice_no(self,id_branch,fy,request,setting_bill_type,invoice_date):
        metal = request.data.get("invoice").get("metal")
        sales_details = request.data.get('sales_details')
        purchase_details = request.data.get('purchase_details')
        return_details = request.data.get('return_details')
        invoice_type = None
        sales_invoice_no = None
        purchase_invoice_no = None
        return_invoice_no = None
        fin_id = fy.fin_id

        if(sales_details):
            invoice_type = 1
            sales_invoice_no = self.generate_ref_no(id_branch,fin_id,invoice_type,setting_bill_type,metal,invoice_date)
        if(purchase_details):
            invoice_type = 2
            purchase_invoice_no = self.generate_ref_no(id_branch,fin_id,invoice_type,setting_bill_type,metal,invoice_date)
            if(sales_details):
                invoice_type = 4
        if(return_details):
            invoice_type = 3
            return_invoice_no = self.generate_ref_no(id_branch,fin_id,invoice_type,setting_bill_type,metal,invoice_date)
            if(sales_details):
                invoice_type = 5
                if(purchase_details):
                    invoice_type = 6

        return {'invoice_type':invoice_type,'sales_invoice_no':sales_invoice_no,'purchase_invoice_no':purchase_invoice_no,'return_invoice_no':return_invoice_no,'fin_year':fin_id }
        
            

    def generate_ref_no(self,id_branch,fin_id,bill_type,setting_bill_type,metal,invoice_date):
        print('setting_bill_type',setting_bill_type,invoice_date)
        is_metal_wise_billing = int(RetailSettings.objects.get(name='is_metal_wise_billing').value)
        is_metal_wise_billing_purchase = int(RetailSettings.objects.get(name='is_metal_wise_billing_purchase').value)
        bill_no_generation_type = int(RetailSettings.objects.get(name='bill_no_generation_type').value) # 1 ->  Normal 2-> based Entry Date
        code =''
        if(bill_type==1):
            last_inv=ErpInvoice.objects.select_for_update().filter(id_branch=id_branch,fin_year =fin_id, sales_invoice_no__isnull=False,setting_bill_type=setting_bill_type)
            if(is_metal_wise_billing == 1):
                last_inv = last_inv.select_for_update().filter(metal = metal)
        if(bill_type==2):
            last_inv=ErpInvoice.objects.select_for_update().filter(id_branch=id_branch,fin_year =fin_id, purchase_invoice_no__isnull=False,setting_bill_type=setting_bill_type)
            if(is_metal_wise_billing_purchase == 1):
                last_inv = last_inv.select_for_update().filter(metal = metal)
        if(bill_type==3):
            if(is_metal_wise_billing_purchase == 1):
                last_inv = last_inv.select_for_update().filter(metal = metal)
            last_inv=ErpInvoice.objects.select_for_update().filter(id_branch=id_branch,fin_year =fin_id, return_invoice_no__isnull=False,setting_bill_type=setting_bill_type)

        if(bill_no_generation_type == 2):
            last_inv = last_inv.select_for_update().filter(invoice_date = invoice_date)
        last_inv = last_inv.order_by('-erp_invoice_id').first()
        print('last_inv',last_inv.purchase_invoice_no,last_inv.sales_invoice_no,last_inv.return_invoice_no)
        if last_inv:
           if(bill_type==1):
                code= int(last_inv.sales_invoice_no)
                code = str(code + 1).zfill(5)
           if(bill_type==2):
                code= int(last_inv.purchase_invoice_no)
                code = str(code + 1).zfill(5)
           if(bill_type==3):
                code= int(last_inv.return_invoice_no)
                code = str(code + 1).zfill(5)
        else:
           code = '00001'
        return code

    
    def insert_sales_details(self,sales_details,erp_invoice_id,invoice_data):
        return_data =[]

        for sales_item in sales_details:
            
            sales_item.update({"invoice_bill_id":erp_invoice_id})
            item_type =sales_item['item_type']

            if(item_type==0):
                tag_id = sales_item['tag_id']
                tagObj = ErpTagging.objects.filter(tag_id=tag_id).get()
                if(tagObj.container != None):
                    ErpTaggingContainerLogDetails.objects.create(tag=tagObj, from_branch=tagObj.id_branch,
                                                             from_container=tagObj.container,
                                                             to_branch=None, to_container=None, transaction_type=2)
            elif(item_type==1):
                sales_item['tag_id'] = None
            elif(item_type==2):
                tag_id = sales_item['tag_id']


            stone_details = sales_item['stone_details']
            charges_details=sales_item['charges_details']
            other_metal_details=sales_item['other_metal_detail']
            inv_detail_serializer = ErpInvoiceSalesDetailsSerializer(data=sales_item)
            if(inv_detail_serializer.is_valid(raise_exception=True)):
                inv_detail_serializer.save()
                item_type =inv_detail_serializer.data['item_type']

                self.insert_customer_log(inv_detail_serializer.data,invoice_data)

                stone_details=insert_other_details(stone_details,ErpInvoiceStoneDetailsSerializer,{"invoice_sale_item_id":inv_detail_serializer.data['invoice_sale_item_id']})

                for charge in charges_details:
                    charge.update({'id_charges' : charge['selectedCharge'],'charges_amount' : charge['amount'],"invoice_sale_item_id":inv_detail_serializer.data['invoice_sale_item_id']})
                    charge_serializer = ErpInvoiceItemChargesSerializer(data=charge)
                    charge_serializer.is_valid(raise_exception=True)
                    charge_serializer.save()

                other_metal_details=insert_other_details(other_metal_details,ErpInvoiceOtherMetalSerializer,{"invoice_sale_item_id":inv_detail_serializer.data['invoice_sale_item_id']})

                
                return_data.append({**sales_item,**inv_detail_serializer.data,'stone_details':stone_details,'charges_details':charges_details,'other_metal_details':other_metal_details})

                insert_incentive_details(inv_detail_serializer.data,invoice_data['id_branch'],invoice_data['invoice_date'])

            
                if item_type == 0:
                    if invoice_data['setting_bill_type'] == 1:
                        tag_instance = ErpTagging.objects.get(pk=sales_item['tag_id'])
                        tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by":invoice_data['created_by'],"tag_status":2,"is_partial_sale":sales_item['is_partial_sale'] }, partial=True)
                        tag_serializer.is_valid(raise_exception=True)
                        tag_serializer.save()
                    else:
                        tag_instance = ErpTagging.objects.get(pk=sales_item['tag_id'])
                        tag_serializer = ErpTaggingSerializer(tag_instance, data={"is_special_discount_applied":True,"updated_on":datetime.now(tz=timezone.utc),"updated_by":invoice_data['created_by'],"tag_status":2,"is_partial_sale":sales_item['is_partial_sale'] }, partial=True)
                        tag_serializer.is_valid(raise_exception=True)
                        tag_serializer.save()

                    log_details={
                        'from_branch': invoice_data['id_branch'],
                        'date': invoice_data['invoice_date'],
                        'id_stock_status': 2,
                        'tag_id': sales_item['tag_id'],
                        'transaction_type': 2,
                        'ref_id': inv_detail_serializer.data['invoice_sale_item_id'],
                        "created_by": invoice_data['created_by'],
                    }
                    log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                    log_tag_serializer.is_valid(raise_exception=True)
                    log_tag_serializer.save()

                if item_type == 1:
                    non_log_details=sales_item
                    non_log_details.update({"from_branch": invoice_data['id_branch'],"date" : invoice_data['invoice_date'],"id_stock_status": 2,'transaction_type': 2,'ref_id': inv_detail_serializer.data['invoice_sale_item_id'],"created_by": invoice_data['created_by']})
                    non_tag_serializer = ErpLotInwardNonTagSerializer(data=non_log_details)
                    non_tag_serializer.is_valid(raise_exception=True)
                    non_tag_serializer.save()
                    insert_other_details(stone_details,ErpLotInwardNonTagStoneSerializer,{"id_non_tag_log":non_tag_serializer.data['id_non_tag_log']})
                if sales_item['est_item_id']:

                    self.update_estimation(sales_item,inv_detail_serializer);

                if sales_item.get("id_tag_transfer"):

                    self.update_stock_issue(sales_item,invoice_data);            

                if sales_item['order_detail']:

                    self.update_order_status(sales_item,invoice_data['invoice_date']);         
            else:
                return Response({"message":ErpInvoiceSalesDetailsSerializer.errors,"message":"From Sales Details"}, status=status.HTTP_400_BAD_REQUEST)
            
        return return_data

    def update_estimation(self,sales_item,inv_detail_serializer):
        queryset = ErpEstimationSalesDetails.objects.get(est_item_id=sales_item['est_item_id'])
        queryset.invoice_sale_item_id = inv_detail_serializer.instance
        queryset.status = 1
        queryset.save()
        est_queryset = ErpEstimation.objects.filter(estimation_id=queryset.estimation_id.pk).get()
        est_queryset.invoice_id = inv_detail_serializer.instance.invoice_bill_id
        est_queryset.save()
    
    def update_stock_issue(self,sales_item,invoice_data):
        queryset = ErpTagTransfer.objects.get(id_tag_transfer=sales_item['id_tag_transfer'])
        queryset.status = 3
        queryset.save()

        stock=ErpTagTransfer.objects.filter(stock_transfer =queryset.stock_transfer.pk)
        total_stock = stock.count()
        downloded_stock =stock.filter(status__in = [2,3]).count()
        print(total_stock)
        print(downloded_stock)
        if total_stock == downloded_stock:
            print('DOWNLOADED')
            transfer_instance= ErpStockTransfer.objects.get(pk=queryset.stock_transfer.pk)
            approval_data = {"transfer_status":2,"downloaded_date":invoice_data['invoice_date'],"downloaded_by": invoice_data['created_by'],"updated_by": invoice_data['created_by'], "updated_on":datetime.now(tz=timezone.utc)}
            transfer_serializer = ErpStockTransferSerializer(transfer_instance,data = approval_data, partial=True)
            transfer_serializer.is_valid(raise_exception=True)
            transfer_serializer.save()
            return True

    def insert_customer_log(self, sales_item, inv_detail): 


        try:
            counter_target = CounterWiseTarget.objects.get(id_counter_target=inv_detail['id_counter'])
        except CounterWiseTarget.DoesNotExist:
            print("No CounterWiseTarget found for id:", inv_detail['id_counter'])
            return 

        incentive_amount = 0
        net_weight = float(sales_item.get('net_wt', 0))
        wt_target_value = float(counter_target.wt_target_value or 0)

        if counter_target.wt_target_type == 1:  # Per Percentage
            incentive_amount = net_weight * wt_target_value
        elif counter_target.wt_target_type == 2:  # Flat
            incentive_amount = wt_target_value


        data = {
            **sales_item,
            **inv_detail,
            'invoice_sale_item': sales_item['invoice_sale_item_id'],
            'ref_id': inv_detail['erp_invoice_id'],
            'incentive_amount': round(incentive_amount, 2),
        }
        serializer = ErpCustomerSalesLogSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()


    def update_order_status(self,sales_item,invoice_date):
        queryset = ERPOrderDetails.objects.get(detail_id=sales_item['order_detail'])
        queryset.order_status = ERPOrderStatus.objects.get(id=5)
        queryset.delivered_on = invoice_date
        queryset.save()

            
    def insert_purchase_details(self,purchase_details,erp_invoice_id,invoice_data):
        return_data =[]
        for purchase_item in purchase_details:
            purchase_item.update({"invoice_bill_id":erp_invoice_id,"current_branch":invoice_data['id_branch']})
            purchase_detail_serializer = ErpInvoiceOldMetalDetailsSerializer(data=purchase_item)
            if(purchase_detail_serializer.is_valid(raise_exception=True)):
                purchase_detail_serializer.save()

                stone_details=insert_other_details(purchase_item['stone_details'],ErpInvoiceStoneDetailsSerializer,{"invoice_old_metal_item_id":purchase_detail_serializer.data['invoice_old_metal_item_id']})

                if purchase_item['est_old_metal_item_id']:
                    queryset = ErpEstimationOldMetalDetails.objects.get(est_old_metal_item_id = purchase_item['est_old_metal_item_id'])
                    detail = { 'invoice_old_metal_item_id': purchase_detail_serializer.data['invoice_old_metal_item_id'],'status':1}
                    serializer = ErpEstimationOldMetalDetailsSerializer(queryset, data=detail, partial=True)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                
                return_data.append({**purchase_item,**purchase_detail_serializer.data,'stone_details':stone_details})

            else:
                tb = traceback.format_exc()
                return Response({"error":ErpInvoiceOldMetalDetailsSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            
        return return_data
            
    def insert_scheme_details(self,scheme_details,erp_invoice_id):
        for scheme in scheme_details:
            scheme.update({
                "invoice_bill_id":erp_invoice_id, 
                "closing_weight":scheme['closing_weight'],
                "scheme_acc_number":scheme['scheme_acc_number'],
                "wastage":scheme['va'], 
                "mc":scheme['mc'], 
                "closing_amount":scheme['amount'], 
                "rate_per_gram":scheme['rate_per_gram']
            })
            scheme_serializer = ErpInvoiceSchemeAdjustedSerializer(data=scheme)

            if(scheme_serializer.is_valid(raise_exception=True)):
                scheme_instance = scheme_serializer.save()
                if "id_scheme_account" in scheme:
                    scheme_account = scheme_instance.id_scheme_account  # Get the related SchemeAccount
                    scheme_account.is_utilized = True
                    scheme_account.utilized_type = 2
                    scheme_account.save()
            else:
                return Response({"error":ErpInvoiceSchemeAdjustedSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def insert_gift_details(self,gift_details,erp_invoice_id):
        for gift in gift_details:
            gift.update({"invoice_bill_id":erp_invoice_id})
            gift_serializer = ErpInvoiceGiftDetailsSerializer(data=gift)
            invoice_obj = ErpInvoice.objects.filter(erp_invoice_id=erp_invoice_id).first()
            if(gift_serializer.is_valid(raise_exception=True)):
                gift_instance = gift_serializer.save()
                voucher = gift_instance.issue_id  # Get the related SchemeAccount
                voucher.status = 2
                voucher.ref_no = invoice_obj
                voucher.save()
            else:
                return Response({"error":ErpInvoiceGiftDetailsSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def genertate_invoice_print (self,erp_invoice_id,request,data):
        metalrates = MetalRates.objects.all().latest('rate_id')
        metalrates_serializer = MetalRatesSerializer(metalrates)
        template_type = RetailSettings.objects.get(name='bill_print_template').value
        customer_address = CustomerAddress.objects.filter(customer = data['id_customer']).first()
        if customer_address:
            customer_address_serializer = CustomerAddressSerializer(customer_address)
            address = customer_address_serializer.data
        response_data = data
        sales_details = data['sales_details']
        purchase_details = data['purchase_details']
        return_details = data['return_details']
        payment_details = data['payment_details']
        scheme_details = data['scheme_details']
        sgst_cost =0
        cgst_cost =0
        igst_cost =0
        tax_per=0
        total_taxable =0
        total_pcs =0
        total_nwt =0
        total_gwt =0
        total_wwt = 0
        total_pur_nwt =0
        total_pur_gwt =0
        total_pur_wnt =0
        sr_sgst_cost =0
        sr_cgst_cost =0
        sr_igst_cost =0
        sr_tax_per=0
        sr_total_taxable =0
        sr_total_nwt =0
        sr_total_gwt =0
        dash= "------------------------------------------------------------------------"
        for item in sales_details:
            total_pcs += float(item.get('pieces', 0))
            total_gwt += float(item.get('gross_wt', 0))
            total_nwt += float(item.get('net_wt', 0))
            total_wwt += float(item.get('wastage_weight', 0))
            sgst_cost += float(item.get('sgst_cost', 0))
            cgst_cost += float(item.get('cgst_cost', 0))
            igst_cost += float(item.get('igst_cost', 0))
            total_taxable += float(item.get('taxable_amount', 0))
            tax_per += float(item.get('tax_percentage', 0))

        for item in purchase_details:
            total_pur_gwt += float(item.get('gross_wt', 0))
            total_pur_nwt += float(item.get('net_wt', 0))
            total_pur_wnt += float(item.get('wastage_weight', 0))
            

        for item in return_details:
            print(item['invoice_sale_item_details'])
            # item.update(item['invoice_sale_item_details'])
            sr_total_gwt += float(item.get('gross_wt', 0))
            sr_total_nwt += float(item.get('net_wt', 0))
            sr_sgst_cost += float(item.get('sgst_cost', 0))
            sr_cgst_cost += float(item.get('cgst_cost', 0))
            sr_igst_cost += float(item.get('igst_cost', 0))
            sr_total_taxable += float(item.get('taxable_amount', 0))
            sr_tax_per += float(item.get('tax_percentage', 0))

        if return_details:
            tax_per= tax_per / len(return_details)
            response_data['sr_total_gwt'] = format(sr_total_gwt, '.3f')
            response_data['sr_total_nwt'] = format(sr_total_nwt, '.3f')
            response_data['sr_total_taxable'] = format(sr_total_taxable,'.2f')
            response_data['sr_sgst_cost'] = format(sr_sgst_cost, '.3f')
            response_data['sr_cgst_cost'] = format(sr_cgst_cost, '.3f')
            response_data['sr_igst_cost'] = format(sr_igst_cost, '.3f')
            response_data['sr_tax_per'] = round(sr_tax_per, 2)
            response_data['sr_igst_per'] = round(sr_tax_per, 2) 
            response_data['sr_cgst_per'] = round(sr_tax_per / 2, 2)
            response_data['sr_sgst_per'] = round(sr_tax_per / 2, 2)


        if sales_details:
            tax_per= tax_per / len(sales_details)
            response_data['total_pcs'] = int(total_pcs)
            response_data['total_gwt'] = format(total_gwt, '.3f')
            response_data['total_nwt'] = format(total_nwt, '.3f')
            response_data['total_wwt'] = format(total_wwt, '.3f')
            response_data['total_taxable'] = format(total_taxable,'.2f')
            response_data['sgst_cost'] = format(sgst_cost, '.3f')
            response_data['cgst_cost'] = format(cgst_cost, '.3f')
            response_data['igst_cost'] = format(igst_cost, '.3f')
            response_data['tax_per'] = round(tax_per, 2)
            response_data['igst_per'] = round(tax_per, 2) 
            response_data['cgst_per'] = round(tax_per / 2, 2)
            response_data['sgst_per'] = round(tax_per / 2, 2)

        response_data['total_pur_nwt'] = format(total_pur_nwt,'.3f')
        response_data['total_pur_gwt'] = format(total_pur_gwt,'.3f')
        response_data['total_pur_wnt'] = format(total_pur_wnt,'.3f')


        response_data['sales_details'] = sales_details
        response_data['purchase_details'] = purchase_details
        response_data['scheme_details'] = scheme_details
        response_data['payment_details'] = payment_details
        response_data['return_details'] = return_details
        response_data['metal_rates'] = metalrates_serializer.data
        response_data['dash'] = dash

        response_data['balance_amount'] = float(response_data['net_amount']) - float(response_data['received_amount']) - float(response_data['due_amount']) - float(response_data['total_chit_amount'])

        if  response_data['balance_amount'] > 0 :

            response_data['balance_amount'] =  format_currency(response_data['balance_amount'])
        else :
            response_data['balance_amount'] = 'NIL'

        if  float(response_data['due_amount']) > 0 :

            response_data['show_balance_amount'] =  False
        else :

            response_data['show_balance_amount'] =  True

        print('value')
        print(response_data['due_amount'])
        if (response_data['invoice_type'] == 1 or response_data['invoice_type'] == 4 or response_data['invoice_type'] == 5 or response_data['invoice_type'] == 6):
            invoice_name = "SALES INVOICE"
        elif (response_data['invoice_type'] == 2):
            invoice_name = "PURCHASE INVOICE"
        elif (response_data['invoice_type'] == 3):
            invoice_name = "SALES RETURN INVOICE"
        response_data['invoice_type'] = invoice_name
        save_dir = os.path.join(settings.MEDIA_ROOT, f'billing/{erp_invoice_id}')

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(erp_invoice_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(save_dir, 'qrcode.png')
        qr_img.save(qr_path)

        response_data['qr_path'] = qr_path
        if(int(template_type) == 1):
           template = get_template('billing_template_1.html')
        elif(int(template_type) == 2):
           template = get_template('billing_template_2.html')

        html = template.render(response_data)
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        pdf_path = os.path.join(save_dir, 'bill_print.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())

        pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'billing/{erp_invoice_id}/bill_print.pdf')

        return pdf_path
            

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





class ErpIssueCreditsListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        branch = request.data['branch']
        customer = request.data['customer']
        
        queryset = ErpIssueReceipt.objects.filter(type=1, issue_type=1, branch=branch, customer=customer)
        serializer = ErpIssueReceiptSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ErpInvoiceListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        id_metal = request.data['id_metal']
        status = request.data.get('bill_status')
        bill_type = request.data.get('bill_type')
        bill_setting_type = 1
        if "bill_setting_type" in request.data:
            bill_setting_type =  request.data['bill_setting_type']
        id_branch = (id_branch) if id_branch != '' else 1
        
        queryset = ErpInvoice.objects.filter(setting_bill_type=bill_setting_type).order_by('-pk')

        if from_date and to_date:
            queryset = queryset.filter(invoice_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(id_branch__in=id_branch)
        else:
            queryset = queryset.filter(id_branch=id_branch)
        if id_metal:
            queryset = queryset.filter(metal=id_metal)
        if status:
            queryset = queryset.filter(invoice_status=status)
        if bill_type:
            queryset = queryset.filter(invoice_type=bill_type)
        paginator, page = pagination.paginate_queryset(queryset, request,None, INVOICE_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,INVOICE_COLUMN_LIST,request.data.get('path_name',''))
        serializer = ErpInvoiceSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            round_offed_sales_amount = round(float(data['sales_amount']))
            inv_data = get_invoice_no(data)

            data.update({"sales_amount":round_offed_sales_amount,"pk_id":data['erp_invoice_id'], "sno":index+1,"invoice_no":inv_data['invoice_no'],'status_color': 'success' if (data['invoice_status']==1) else 'danger',"invoice_date":format_date(data['invoice_date']),'status': 'Success' if (data['invoice_status']==1) else 'Cancel','invoice_status_name': 'Success' if (data['invoice_status']==1) else 'Cancel','is_cancelable': True if (data['invoice_status']==1) else False})
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isSchemeFilterReq'] = False
        filters_copy['isMetalFilterReq'] = True
        filters_copy['isBillStatusFilterReq'] = True
        filters_copy['isBillTypeFilterReq'] = True

        context={
            'columns':columns,
            'actions':ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':filters_copy
            }
        return pagination.paginated_response(serializer.data,context)

    
def cancel_bill(request):
        with transaction.atomic():    
            erp_invoice_id = request.data['pk_id']
            queryset = ErpInvoice.objects.get(erp_invoice_id = erp_invoice_id)
            branch_date = BranchEntryDate()
            entry_date = branch_date.get_entry_date(queryset.id_branch)
            entry_datetime = datetime.combine(entry_date, datetime.now(tz=timezone.utc).time())
            update_data ={ 'canceled_reason' : request.data['cancel_reason'] ,'canceled_by' : request.user.id,'canceled_on' : entry_datetime,'invoice_status' : 2}
            inv_serializer = ErpInvoiceSerializer(queryset,update_data,partial=True)
            if inv_serializer.is_valid(raise_exception=True):
                    inv_serializer.save()
            advance_details = ErpReceiptAdvanceAdj.objects.filter(invoice_bill_id=erp_invoice_id)
            sales_details = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id=erp_invoice_id)
            sale_serializer = ErpInvoiceSalesDetailsSerializer(sales_details, many=True,context={'stone_details': True, 'charges_details': True})
            purchase_details = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id=erp_invoice_id)
            purchase_serializer = ErpInvoiceOldMetalDetailsSerializer(purchase_details, many=True)
            return_details = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id=erp_invoice_id)
            return_details_serializer = ErpInvoiceSalesReturnSerializer(return_details,many=True)
            scheme_adjusted = ErpInvoiceSchemeAdjusted.objects.filter(invoice_bill_id=erp_invoice_id)
            response_data = inv_serializer.data
            sales_details = sale_serializer.data
            purchase_details = purchase_serializer.data
            return_details = return_details_serializer.data
            deposit = queryset.deposit_bill.first()
            if deposit:
                deposit.bill_status = 2
                deposit.save()
            for detail in sales_details:
                item_type =detail['item_type']
                print(item_type)
                logs_to_delete = ErpCustomerSalesLog.objects.filter(invoice_sale_item = detail['invoice_sale_item_id'])
                if logs_to_delete.exists():
                    logs_to_delete.delete()
                if item_type == 0:
                    tag_instance = ErpTagging.objects.get(pk=detail['tag_id'])
                    tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by": request.user.id,"tag_status":1 }, partial=True)
                    tag_serializer.is_valid(raise_exception=True)
                    tag_serializer.save()
                    log_details={
                        'to_branch': response_data['id_branch'],
                        'date': response_data['invoice_date'],
                        'id_stock_status': 5,
                        'tag_id': detail['tag_id'],
                        'transaction_type': 2,
                        'ref_id': detail['invoice_sale_item_id'],
                        "created_by": request.user.id,
                    }
                    log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                    log_tag_serializer.is_valid(raise_exception=True)
                    log_tag_serializer.save()
                if item_type == 1:
                    non_log_details=detail
                    non_log_details.update({"to_branch": response_data['id_branch'],"date" : response_data['invoice_date'],"id_stock_status": 5,'transaction_type': 2,'ref_id': detail['invoice_sale_item_id'],"created_by": request.user.id})
                    non_tag_serializer = ErpLotInwardNonTagSerializer(data=non_log_details)
                    non_tag_serializer.is_valid(raise_exception=True)
                    non_tag_serializer.save()
                    insert_other_details(detail['stone_details'],ErpLotInwardNonTagStoneSerializer,{"id_non_tag_log":non_tag_serializer.data['id_non_tag_log']})
                estqueryset = ErpEstimationSalesDetails.objects.filter(invoice_sale_item_id = detail['invoice_sale_item_id'])
                if estqueryset.exists():
                    estqueryset = estqueryset.get()
                    estqueryset.invoice_sale_item_id = None
                    estqueryset.status = 0
                    estqueryset.save()
                if detail['order_detail']:
                    ord_queryset = ERPOrderDetails.objects.get(detail_id=detail['order_detail'])
                    ord_queryset.order_status = ERPOrderStatus.objects.get(id=4)
                    ord_queryset.save()
                if detail['id_tag_transfer']:
                    tranc_queryset = ErpTagTransfer.objects.get(id_tag_transfer=detail['id_tag_transfer'])
                    tranc_queryset.status = 1
                    tranc_queryset.save()
                    transfer_instance= ErpStockTransfer.objects.get(pk=tranc_queryset.stock_transfer.pk)
                    transfer_instance.downloaded_date = None
                    transfer_instance.downloaded_by = None
                    transfer_instance.transfer_status = 2
                    transfer_instance.updated_by = request.user
                    transfer_instance.updated_on = datetime.now(tz=timezone.utc)
                    transfer_instance.save()
                    tag_instance = ErpTagging.objects.get(pk=detail['tag_id'])
                    tag_serializer = ErpTaggingSerializer(tag_instance, data={ "updated_on":datetime.now(tz=timezone.utc),"updated_by": request.user.id,"tag_status":8 }, partial=True)
                    tag_serializer.is_valid(raise_exception=True)
                    tag_serializer.save()
            for detail in purchase_details:
                    if ErpEstimationOldMetalDetails.objects.filter(invoice_old_metal_item_id = detail['invoice_old_metal_item_id']).exists():
                        queryset = ErpEstimationOldMetalDetails.objects.get(invoice_old_metal_item_id = detail['invoice_old_metal_item_id'])
                        detail = { 'invoice_old_metal_item_id': None,'status':0}
                        serializer = ErpEstimationOldMetalDetailsSerializer(queryset, data=detail, partial=True)
                        if serializer.is_valid(raise_exception=True):
                            serializer.save()
            for detail in return_details:
                if  detail['invoice_sale_item_id']:
                    queryset = ErpInvoiceSalesDetails.objects.get(invoice_sale_item_id = detail['invoice_sale_item_id'])
                    queryset.status = 1
                    queryset.save()
            for detail in scheme_adjusted:
                if detail.id_scheme_account:
                    detail.id_scheme_account.is_utilized = False
                    detail.id_scheme_account.utilized_type = None
                    detail.save()
            for detail in advance_details:
                detail.is_adjusted = False
                detail.save()

        

class ErpInvoiceCancelView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.user.pk).get()
        emp = Employee.objects.filter(user_id = request.user.pk).get()
        emp_profile = Profile.objects.get(id_profile=emp.id_profile.pk)
        if(emp_profile.isOTP_req_for_bill_cancel == True):
            OTP_code = randint(100000, 999999)
            expiry_time = timezone.now() + timedelta(minutes=5)
            if (EmployeeOTP.objects.filter(employee=emp.pk, otp_for="4", expiry__gt=timezone.now()).exists()):
                return Response({"message": "A bill cancel OTP already exists. Please use it / wait till its expire"}, status=status.HTTP_400_BAD_REQUEST)
            EmployeeOTP.objects.create(employee=emp, otp_for="4", email_id=user.email,
                                    otp_code=OTP_code, expiry=timezone.now()+timedelta(minutes=5))
            return Response({
                "message": "Enter OTP sent to your mobile number to proceed further.",
            })
        else:
            try:
                cancel_bill(request)
                return Response({"message":"Invoice Canceled Successfully."}, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                tb = traceback.format_exc()
                return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            except KeyError as e:
                tb = traceback.format_exc()
                return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)


class ErpInvoiceDetailsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpInvoice.objects.all()
    serializer_class = ErpInvoiceSerializer
    
    def post(self, request, *args, **kwargs):
        erp_invoice_id = request.data.get('erp_invoice_id')
        if (not erp_invoice_id):
            return Response({"error": "Invoice Id Is Missing"}, status=status.HTTP_400_BAD_REQUEST)
        metalrates = MetalRates.objects.all().latest('rate_id')
        metalrates_serializer = MetalRatesSerializer(metalrates)
        inv = ErpInvoice.objects.get(erp_invoice_id=erp_invoice_id)
        inv_serializer = ErpInvoiceSerializer(inv)
        sales_details = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id=inv)
        sale_serializer = ErpInvoiceSalesDetailsSerializer(sales_details, many=True,context={'stone_details': True, 'charges_details': True})
        purchase_details = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id=inv)
        purchase_serializer = ErpInvoiceOldMetalDetailsSerializer(purchase_details, many=True)
        scheme_adjusted = ErpInvoiceSchemeAdjusted.objects.filter(invoice_bill_id=inv)
        gift_adjusted = ErpInvoiceGiftDetails.objects.filter(invoice_bill_id=inv)
        gift_adjusted_serializer = ErpInvoiceGiftDetailsSerializer(gift_adjusted, many=True)
        scheme_adjusted_serializer = ErpInvoiceSchemeAdjustedSerializer(scheme_adjusted, many=True)
        inv_payment_details = ErpInvoicePaymentModeDetail.objects.filter(invoice_bill_id=inv)
        payment_details_serializer = ErpInvoicePaymentModeDetailSerializer(inv_payment_details, many=True)
        return_details = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id=inv)
        return_details_serializer = ErpInvoiceSalesReturnSerializer(return_details,many=True)
        response_data = inv_serializer.data
        sales_details = sale_serializer.data
        purchase_details = purchase_serializer.data
        return_details = return_details_serializer.data
        payment_details = payment_details_serializer.data
        scheme_details = scheme_adjusted_serializer.data
        gift_details = gift_adjusted_serializer.data
        
        sgst_cost =0
        cgst_cost =0
        igst_cost =0
        tax_per=0
        total_taxable =0
        total_nwt =0
        total_gwt =0
        total_pur_nwt =0
        total_pur_gwt =0
        deposit_bill  = None if inv.due_amount > 0 else inv.deposit_bill.first()
        advance_adj_bill  =inv.advance_adj_invoices.all()
        deposit_amount = 0
        sr_sgst_cost =0
        sr_cgst_cost =0
        sr_igst_cost =0
        sr_tax_per=0
        sr_total_taxable =0
        sr_total_nwt =0
        sr_total_gwt =0
        advance_adj_amount = 0
        total_chit_amount = 0
        gift_amount = 0
        
        if(advance_adj_bill):
            for adj_bill in advance_adj_bill:
                advance_adj_amount += float(adj_bill.adj_amount)
        if(deposit_bill):
            deposit_amount = format(deposit_bill.amount, '.2f')


        for item in sales_details:
            total_gwt += float(item.get('gross_wt', 0))
            total_nwt += float(item.get('net_wt', 0))
            sgst_cost += float(item.get('sgst_cost', 0))
            cgst_cost += float(item.get('cgst_cost', 0))
            igst_cost += float(item.get('igst_cost', 0))
            total_taxable += float(item.get('taxable_amount', 0))
            tax_per += float(item.get('tax_percentage', 0))

        for item in purchase_details:
            total_pur_gwt += float(item.get('gross_wt', 0))
            total_pur_nwt += float(item.get('net_wt', 0))
        
        for item in return_details:
            print(item['invoice_sale_item_details'])
            #item.update(item['invoice_sale_item_details'])
            sr_total_gwt += float(item.get('gross_wt', 0))
            sr_total_nwt += float(item.get('net_wt', 0))
            sr_sgst_cost += float(item.get('sgst_cost', 0))
            sr_cgst_cost += float(item.get('cgst_cost', 0))
            sr_igst_cost += float(item.get('igst_cost', 0))
            sr_total_taxable += float(item.get('taxable_amount', 0))
            sr_tax_per += float(item.get('tax_percentage', 0))

        for item, instance in zip(payment_details, inv_payment_details):
            mode_name = instance.payment_mode.mode_name
            item.update({
                "mode_name":mode_name
            })

        for item, instance in zip(scheme_details, scheme_adjusted):
           
            item.update({
                "closing_amount":instance.id_scheme_account.closing_amount
            })
            total_chit_amount += float(item['closing_amount'])
            
        for item, instance in zip(gift_details, gift_adjusted):
               
            # item.update({
            #     "closing_amount":instance.id_scheme_account.closing_amount
            # })
            gift_amount += float(item['amount'])

        if sales_details:
            tax_per= tax_per / len(sales_details)
            response_data['total_gwt'] = format(total_gwt, '.3f')
            response_data['total_nwt'] = format(total_nwt, '.3f')
            response_data['total_taxable'] = format(total_taxable,'.2f')
            response_data['sgst_cost'] = format(sgst_cost, '.3f')
            response_data['cgst_cost'] = format(cgst_cost, '.3f')
            response_data['igst_cost'] = format(igst_cost, '.3f')
            response_data['tax_per'] = round(tax_per, 2)
            response_data['igst_per'] = round(tax_per, 2) 
            response_data['cgst_per'] = round(tax_per / 2, 2)
            response_data['sgst_per'] = round(tax_per / 2, 2)

        if return_details:
            tax_per= tax_per / len(return_details)
            response_data['sr_total_gwt'] = format(sr_total_gwt, '.3f')
            response_data['sr_total_nwt'] = format(sr_total_nwt, '.3f')
            response_data['sr_total_taxable'] = format(sr_total_taxable,'.2f')
            response_data['sr_sgst_cost'] = format(sr_sgst_cost, '.3f')
            response_data['sr_cgst_cost'] = format(sr_cgst_cost, '.3f')
            response_data['sr_igst_cost'] = format(sr_igst_cost, '.3f')
            response_data['sr_tax_per'] = round(sr_tax_per, 2)
            response_data['sr_igst_per'] = round(sr_tax_per, 2) 
            response_data['sr_cgst_per'] = round(sr_tax_per / 2, 2)
            response_data['sr_sgst_per'] = round(sr_tax_per / 2, 2)

        response_data['total_pur_nwt'] = format(total_pur_nwt,'.3f')
        response_data['total_pur_gwt'] = format(total_pur_gwt,'.3f')

        response_data['sales_details'] = sales_details
        response_data['purchase_details'] = purchase_details
        response_data['scheme_details'] = scheme_details
        response_data['gift_details'] = gift_details
        
        response_data['payment_details'] = payment_details
        response_data['return_details'] = return_details
        response_data['metal_rates'] = metalrates_serializer.data
        response_data['advance_adj_amount'] = advance_adj_amount
        response_data['total_chit_amount'] = total_chit_amount
        response_data['gift_amount'] = gift_amount
        
        response_data['balance_amount'] = float(response_data['net_amount']) - float(response_data['received_amount']) - float(response_data['due_amount']) - float(total_chit_amount)

        if  response_data['balance_amount'] > 0 :

            response_data['balance_amount'] =  format_currency(response_data['balance_amount'])
        else :
            response_data['balance_amount'] = 'NIL'

        if  float(response_data['due_amount']) > 0 :

            response_data['show_balance_amount'] =  False
        else :

            response_data['show_balance_amount'] =  True


        response_data['deposit_amount'] =  deposit_amount 
        response_data['invoice_data'] = get_invoice_no(inv_serializer.data)
        print(response_data)
        instance = ErpInvoiceCreateAPIView()
        # pdf_url = instance.genertate_invoice_print(erp_invoice_id,request,response_data)
        # response_data['pdf_url'] = pdf_url
        response_data.update({'status_color': 'success' if (response_data['invoice_status']==1) else 'danger',"invoice_date":format_date(response_data['invoice_date']),'status': 'Success' if (response_data['invoice_status']==1) else 'Cancel','invoice_status_name': 'Success' if (response_data['invoice_status']==1) else 'Cancel',})
        return Response(response_data, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                erp_invoice_id = kwargs.get('pk')
                inv_data = request.data
                purchase_details = request.data.get('purchase_details')
                payment_details = request.data.get('payment_details')
                if not erp_invoice_id:
                    return Response({"error": "Invoice ID is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not inv_data:
                    return Response({"error": "Invoice data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if not (purchase_details or payment_details):
                    return Response({"error": "Invoice Details are missing."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    instance = ErpInvoice.objects.get(pk=erp_invoice_id)
                except ErpInvoice.DoesNotExist:
                    return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

                inv_data.update({"updated_by": request.user.id,'updated_on': datetime.now(tz=timezone.utc)})
                inv_serializer = ErpInvoiceSerializer(instance, data=inv_data, partial=True)
                if inv_serializer.is_valid(raise_exception=True):
                    inv_serializer.save()

                    if purchase_details:
                        for purchase_item in purchase_details:
                            purchase_item.update({"invoice_bill_id":erp_invoice_id})
                            purchase_detail_serializer = ErpInvoiceOldMetalDetailsSerializer(data=purchase_item)
                            if(purchase_detail_serializer.is_valid(raise_exception=True)):
                                purchase_detail_serializer.save()
                    if payment_details:
                       self.update_payment_details(payment_details, erp_invoice_id)
                    return Response({"message": "Invoice Updated Successfully."}, status=status.HTTP_200_OK)
                return Response({"error": inv_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"error": "A database error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def update_payment_details(self, payment_details, erp_invoice_id):

        existing_items = ErpInvoicePaymentModeDetail.objects.filter(invoice_bill_id=erp_invoice_id)
        existing_item_map = {item.pk: item for item in existing_items}
        ids_to_delete = set(existing_item_map.keys())

        for detail in payment_details:
            id = detail.get('invoice_pay_id')
            if id:
                ids_to_delete.discard(id)
                try:
                    instance = ErpInvoicePaymentModeDetail.objects.get(pk=id)
                    serializer = ErpInvoicePaymentModeDetailSerializer(instance, data=detail, partial=True)

                    if serializer.is_valid(raise_exception=True):
                        serializer.save()

                except ErpInvoicePaymentModeDetail.DoesNotExist:
                    detail.update({"invoice_bill_id":erp_invoice_id})
                    serializer = ErpInvoicePaymentModeDetailSerializer(data=detail)
                    if(serializer.is_valid(raise_exception=True)):
                        serializer.save()
            else:
                detail.update({"invoice_bill_id":erp_invoice_id})
                serializer = ErpInvoicePaymentModeDetailSerializer(data=detail)
                if(serializer.is_valid(raise_exception=True)):
                    serializer.save()

        if ids_to_delete:
            ErpInvoicePaymentModeDetail.objects.filter(pk__in=ids_to_delete).delete()
        


class ErpIssueReceiptListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        bill_setting_type = request.data.get('bill_setting_type',1)
        id_branch = (id_branch) if id_branch != '' else 1

        queryset = ErpIssueReceipt.objects.filter(setting_bill_type=bill_setting_type)
        if from_date and to_date:
                queryset = queryset.filter(bill_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(branch__in=id_branch)
        else:
            queryset = queryset.filter(branch=id_branch)

        output = []
        paginator, page = pagination.paginate_queryset(queryset, request,None,ISSUE_RECEIPT_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,ISSUE_RECEIPT_COLUMN_LIST,request.data.get('path_name',''))
        serializer = ErpIssueReceiptSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({"pk_id":data['id'], "sno":index+1, "bill_date":format_date(data['bill_date']),
                         "amount":format_currency(data['amount'])})
            # if  data['type'] == 1:
            #     data.update({"type":"Issue"})
            # else:
            #     data.update({"type":"Receipt"})
            if (data['receipt_type'] == 1 and data['type'] == 2):
                trans_name = "GENRAL ADVANCE RECEIPT"
            elif (data['receipt_type'] == 2  and data['type'] == 2):
                trans_name = "ORDER ADVANCE RECEIPT"
            elif (data['receipt_type'] == 3  and data['type'] == 2):
                trans_name = "ADVANCE DEPOSIT RECEIPT"
            elif (data['receipt_type'] == 4  and data['type'] == 2):
                trans_name = "IMPORTED RECEIPT"
            elif (data['receipt_type'] == 5  and data['type'] == 2):
                trans_name = "CREDIT COLLECTION RECEIPT"
            elif (data['receipt_type'] == 6  and data['type'] == 2):
                trans_name = "REPAIR ORDER DELIVERY RECEIPT"
            elif (data['receipt_type'] == 7  and data['type'] == 2):
                trans_name = "OPENING BALANCE"
            elif (data['issue_type'] == 1  and data['type'] == 1):
                trans_name = "CREDIT ISSUE"
            elif (data['issue_type'] == 2  and data['type'] == 1):
                trans_name = "REFUND ISSUE"
            elif (data['issue_type'] == 3  and data['type'] == 1):
                trans_name =  "PETTY CASH ISSUE"
            elif (data['issue_type'] == 5  and data['type'] == 1):
                trans_name =  "BANK DEPOSIT"
            data.update({"type":trans_name})
            if data['bill_status'] == 1:
                data.update({"bill_status":"Success", "is_cancelable":True})
            else:
                data.update({"bill_status":"Cancelled", "is_cancelable":False})
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

class ErpIssueReceiptCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
        

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                payment_details = request.data['payment_details']
                credit_details = request.data['credit_details']
                refund_details = request.data.get('refund_details',[])
                repair_details = request.data.get('repair_details',[])
                del request.data['payment_details']
                del request.data['credit_details']

                branch = Branch.objects.get(id_branch=request.data['branch'])
                fy=FinancialYear.objects.get(fin_status=True)
                
                if(request.data['type'] == 2 and request.data['receipt_type'] == 5):
                    if(len(credit_details) == 0):
                        return Response({"message":"Credit details required."}, status=status.HTTP_400_BAD_REQUEST)
                if( int(request.data['type']) == 1 and int(request.data['issue_type']) == 2):
                    if(len(refund_details) == 0):
                        return Response({"message":"Refund details required."}, status=status.HTTP_400_BAD_REQUEST)
                    
                bill_no = generate_issue_receipt_billno(request.data, branch.short_name, fy, request.data['type'])
                print(bill_no,"bill_no")
                request.data.update({"bill_date":ErpDayClosed.objects.get(id_branch=request.data['branch']).entry_date,
                                    "created_by":request.user.pk, "fin_year":fy.pk, "bill_no":bill_no})
                serializer = ErpIssueReceiptSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                # if(request.data['type'] == "1" and request.data['issue_type'] == 1):
                #     credit_collection_data = {"issue":serializer.data['id'], "discount_amount":0, "received_amount":request.data['amount']}
                #     credit_collection_serializer = ErpReceiptCreditCollectionSerializer(data=credit_collection_data)
                #     credit_collection_serializer.is_valid(raise_exception=True)
                #     credit_collection_serializer.save()
                if(request.data['type'] == 2 and request.data['receipt_type'] == 5):
                    if(request.data['credit_type']==1):
                        if(len(credit_details) > 0):
                            for credits in credit_details:
                                credit_collection_data = {"issue":credits['issue_id'], "receipt":serializer.data['id'], "discount_amount": credits['discount_amount'], "received_amount":credits['received_amount']}
                                credit_collection_serializer = ErpReceiptCreditCollectionSerializer(data=credit_collection_data)
                                credit_collection_serializer.is_valid(raise_exception=True)
                                credit_collection_serializer.save()
                    if(request.data['credit_type']==2):
                        if(len(credit_details) > 0):
                            for credits in credit_details:
                                credit_collection_data = {"invoice_bill_id":credits['invoice_bill_id'], "receipt":serializer.data['id'], "discount_amount": credits['discount_amount'], "received_amount":credits['received_amount']}
                                credit_collection_serializer = ErpReceiptCreditCollectionSerializer(data=credit_collection_data)
                                credit_collection_serializer.is_valid(raise_exception=True)
                                credit_collection_serializer.save()
                                collected_amount = 0
                                col = ErpReceiptCreditCollection.objects.filter(invoice_bill_id = credits["invoice_bill_id"] ,receipt__bill_status= 1)
                                col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
                                for collection in col_data:
                                    collected_amount += (float(collection['received_amount']) + float(collection['discount_amount']))
                                inv = ErpInvoice.objects.get(erp_invoice_id = credits["invoice_bill_id"] )
                                due_amount = float(inv.due_amount)
                                balance_amount = float(due_amount) - float(collected_amount)
                                if(balance_amount == 0):
                                    inv.credit_status = 1
                                    inv.save()
                if(request.data['type'] == 2 and request.data['receipt_type'] == 6):
                    for sales_item in repair_details:
                        ERPOrderDetails.objects.filter(detail_id=sales_item['detail_id']).update(receipt=serializer.data['id'],order_status=5,updated_by= request.user.pk,updated_on = datetime.now(tz=timezone.utc)  )

                if(int(request.data['type']) == 1 and int(request.data['issue_type']) == 2):
                    if(len(refund_details) > 0):
                        for refund in refund_details:
                            refund_data = {"issue":serializer.data['id'], "receipt":refund['id_issue_receipt'],"refund_amount":refund['amount']}
                            refund_serializer = ErpReceiptRefundSerializer(data=refund_data)
                            refund_serializer.is_valid(raise_exception=True)
                            refund_serializer.save()
                for data in payment_details:
                    data.update({"issue_receipt":serializer.data['id'],"type": 1 if int(request.data['type']) == 2 else 2 })
                    payment_detail_serializer = ErpIssueReceiptPaymentDetailsSerializer(data=data)
                    payment_detail_serializer.is_valid(raise_exception=True)
                    payment_detail_serializer.save()
                print_details = ErpIssueReceiptPrintDetailsView()
                response_data = print_details.get_invoice_data(serializer.data['id'], request)
                return Response({"status":True,"response_data" : response_data}, status=status.HTTP_201_CREATED)
            except Exception as e:
                tb = traceback.format_exc()
                return Response({"message": f"An unexpected error occurred: {e}","bill_no" :bill_no,"traceback": tb}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ErpIssueReceiptDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpIssueReceipt.objects.all()
    serializer_class = ErpIssueReceiptSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = self.get_serializer(queryset)
        output = serializer.data
        output.update({"created_by": queryset.created_by.username,
                       "updated_by": queryset.updated_by.username if queryset.updated_by != None else None})
        payment_detail_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt=queryset.id)
        payment_detail_serializer = ErpIssueReceiptPaymentDetailsSerializer(payment_detail_queryset, many=True)
        output.update({"payment_details":payment_detail_serializer.data})
        return Response(output, status=status.HTTP_200_OK)
    
    # def put(self, request, *args, **kwargs):
    #     with transaction.atomic():
    #         queryset = self.get_object()
    #         serializer = self.get_serializer(queryset)
            
    #         payment_details = request.data['payment_details']
    #         del request.data['payment_details']
    #         return Response(status=status.HTTP_202_ACCEPTED)


def generate_issue_receipt_billno(data, branch_code, fy, issue_type):

    code = ''
    issue_receipt_code_settings = RetailSettings.objects.get(name='issue_receipt_code_settings').value
    issue_receipt_code_format = RetailSettings.objects.get(name='issue_receipt_code_format').value
    fy_code = fy.fin_year_code
    fin_id = fy.fin_id
    last_issue_receipt_code = None
    if int(issue_receipt_code_settings) == 1:#GENERATE CODE WITH FY, TYPE AND BRANCH
        last_issue_receipt_code=ErpIssueReceipt.objects.filter(branch=data['branch'],fin_year=fin_id,type=data['type'],setting_bill_type=data['setting_bill_type']).order_by('-id').first()
    # elif order_code_settings == '2':#GENERATE CODE WITH PRODUCT
    #     last_ordercode=ERPOrder.objects.filter(tag_product_id=data['tag_product_id']).order_by('-order_id').first()
    # elif order_code_settings == '3':#GENERATE CODE WITH FY
    #     last_ordercode=ERPOrder.objects.filter(fin_year=fin_id).order_by('-order_id').first()
    if last_issue_receipt_code:
        last_issue_receipt_code = last_issue_receipt_code.bill_no
        match = re.search(r'(\d{5})$', last_issue_receipt_code)
        if match:
            code = match.group(1)
            code = str(int(code) + 1).zfill(5)
        else:
            code = '00001'
    else:
        code = '00001'
    
    issue_receipt_code = issue_receipt_code_format.replace('@branch_code@', branch_code).replace('@code@', code).replace('@fy_code@', fy_code).replace('@type@', str(issue_type))

    return issue_receipt_code

class ErpIssueReceiptCancelView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():    
                issue_receipt_id = request.data['pk_id']
                queryset = ErpIssueReceipt.objects.get(id = issue_receipt_id)
                branch_date = BranchEntryDate()
                entry_date = branch_date.get_entry_date(queryset.branch.pk)
                entry_datetime = datetime.combine(entry_date, datetime.now(tz=timezone.utc).time())
                update_data ={ 'cancel_reason' : request.data['cancel_reason'] ,'cancelled_by' : request.user.id,'cancelled_date' : entry_date,'bill_status' : 2}
                serializer = ErpIssueReceiptSerializer(queryset,update_data,partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                if(CustomerDeposit.objects.filter(bill=issue_receipt_id).exists()):
                    cus_deposit_details = CustomerDeposit.objects.filter(bill=issue_receipt_id).update(bill=None)
                return Response({"message":"Issue / Receipt Canceled Successfully."}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)

class ErpIssueReceiptPrintDetailsView(generics.GenericAPIView):

    permission_classes = [IsEmployee]
    queryset = ErpIssueReceipt.objects.all()
    serializer_class = ErpIssueReceiptSerializer

    def get_out_standing_details(self , id_customer):
            with connection.cursor() as cursor:
                sql = F""" 
                    SELECT 
                    r.customer_id,
                    r.total_credit_amount,
                    COALESCE(recd.paid_amount, 0) AS paid_amount
                    FROM (
                        SELECT 
                        customer_id,
                        SUM(amount) AS total_credit_amount
                        FROM erp_issue_receipt 
                        WHERE issue_type = 1 AND customer_id IS NOT NULL and customer_id = {id_customer}
                        GROUP BY customer_id
                    ) r
                    LEFT JOIN (
                        SELECT 
                        recpt.customer_id,
                        SUM(rcc.received_amount) AS paid_amount
                        FROM erp_receipt_credit_collection rcc
                        LEFT JOIN erp_issue_receipt recpt ON recpt.id = rcc.receipt_id
                        where recpt.bill_status = 1 and recpt.customer_id = {id_customer}
                        GROUP BY recpt.customer_id
                    ) recd ON recd.customer_id = r.customer_id;
                    """
                cursor.execute(sql)
                response_data = None
                if cursor.description:
                    result = cursor.fetchall()
                    field_names = [desc[0] for desc in cursor.description]
                    report_data = {}
                    for row in result:
                        field_value = dict(zip(field_names, row))
                        report_data.update(field_value)
                    response_data = report_data
                return response_data
    
    def get(self, request, *args, **kwargs):
        id_issue_receipt = self.kwargs.get('pk')
        response_data = self.get_invoice_data(id_issue_receipt, request)
        response_ = {"response_data": response_data}
        return Response(response_, status=status.HTTP_200_OK)

    def get_invoice_data(self, id_issue_receipt, request):
        queryset = ErpIssueReceipt.objects.get(id = id_issue_receipt)
        serializer = ErpIssueReceiptSerializer(queryset)
        output = serializer.data
        output.update({
            'type_id':queryset.type
        })
        company = Company.objects.latest("id_company")
        company_serializer = CompanySerializer(company, context={'request':request})
        state = State.objects.latest("id_state")
        emp_name = ''
        emp_code = ''
        if(queryset.employee != None):
            emp = Employee.objects.filter(pk =serializer.data['employee']).first()
            emp_name = emp.firstname
            emp_code = emp.emp_code
        if(queryset.type == 1):
            output.update({"type":"Issue"})
            if(queryset.issue_to == 1):
                output.update({"name":queryset.customer.firstname, "mobile":queryset.customer.mobile})
            else:
                output.update({"name":queryset.employee.firstname, "mobile":queryset.employee.mobile})
            if(queryset.issue_type == 1):
                output.update({"sub_type":"Credit Payment"})
            elif(queryset.issue_type == 2):
                output.update({"sub_type":"Refund Payment"})
            elif(queryset.issue_type == 3):
                output.update({"sub_type":"Payment"})
            else:
                output.update({"sub_type":None})
        if(queryset.type == 2):
            output.update({"type":"Receipt"})
            
            if(queryset.receipt_type == 1):
                output.update({"sub_type":"General Advance Receipt"})
            elif(queryset.receipt_type == 2):
                output.update({"sub_type":"Order Advance Receipt"})
            elif(queryset.receipt_type == 3):
                output.update({"sub_type":"Advance Deposit Receipt"})
            elif(queryset.receipt_type == 4):
                output.update({"sub_type":"Import"})
            elif(queryset.receipt_type == 5):
                customer_out_standing = self.get_out_standing_details(queryset.customer.pk)
                output.update({
                    "sub_type":"Credit Collection Receipt",
                    "total_credit_amount" : customer_out_standing['total_credit_amount'],
                    "paid_amount" : customer_out_standing['paid_amount'],
                    "balance_amount" : format(float(customer_out_standing['total_credit_amount']) - float(customer_out_standing['paid_amount']),'.2f')
                })

            elif(queryset.receipt_type == 8):
                output.update({"sub_type":"Chit Collection Receipt"})
            elif(queryset.receipt_type == 9):
                output.update({"sub_type":"Cash Receipt"})
            else:
                output.update({"sub_type":None})
        if (queryset.customer!=None and CustomerAddress.objects.filter(customer = queryset.customer.pk).exists()):
            customer_address = CustomerAddress.objects.get(customer = queryset.customer.pk)
            customer_address_serializer = CustomerAddressSerializer(customer_address)
            address = customer_address_serializer.data
            # address.update({"state_name":State.objects.get(id_state=customer_address_serializer.data['state']).name})
            
            if customer_address != None :
            
                address1 = customer_address.line1 if (customer_address.line1 and customer_address.line1 != None and customer_address.line1 != '') else ''
                address2 = customer_address.line2 if (customer_address.line2 and customer_address.line2 != None and customer_address.line2 != '') else ''
                address3 = customer_address.line3 if (customer_address.line3 and customer_address.line3 != None and customer_address.line3 != '') else ''
                company_strip_address = (
                f"{address1} {address2} {address3}, {customer_address.city.name}, {customer_address.state.name}. {customer_address.pincode}".strip()
                )
                if customer_address.line1!=None and customer_address.line1!='':
                    output.update({"cus_address1":customer_address.line1})
                if customer_address.line2!=None and customer_address.line2!='':
                    output.update({"cus_address2":customer_address.line2})
                if customer_address.line3!=None and customer_address.line2!='':
                    output.update({"cus_address3":customer_address.line3})
                if customer_address.city!=None and customer_address.city!='':
                    output.update({"city":customer_address.city.name})
                if customer_address.pincode!=None and customer_address.pincode!='':
                    output.update({"pin_code":customer_address.pincode})
                if customer_address.area!=None and customer_address.area!='':
                    output.update({"area":customer_address.area.area_name})
            output.update({"name":queryset.customer.firstname, "mobile":queryset.customer.mobile,"address":address, "strip_address":company_strip_address})
        else:
            output.update({"address":None})
        output.update({"bill_date" : format_date(queryset.bill_date) })
        payment_details = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt=queryset.id)
        payment_detail_serializer = ErpIssueReceiptPaymentDetailsSerializer(payment_details, many=True)
        pay_details = []
        for data in payment_detail_serializer.data:
            mode = PaymentMode.objects.get(id_mode=data['payment_mode']).mode_name
            data.update({"payment_mode":mode})
            if data not in pay_details:
                pay_details.append(data)
        output.update({
            "payment_details":pay_details,
            'company_name' :   company.company_name,
            'company_strip_address' :   company_strip_address,
            'gst_number' :   company.gst_number,
            'company_mobile' :   company.mobile,
            'company_logo' :   company_serializer.data['image'],
            'emp_name' : emp_name,
            'emp_code' : emp_code,
            'account_head_name':queryset.account_head.name if(queryset.account_head is not None) else None,
            'amount_in_words' : num2words(queryset.amount, lang='en_IN') + " Only",
            'counter_name' :   queryset.id_counter.counter_name if(queryset.id_counter is not None) else None
            })
        return output


class ErpIssueReceiptPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpIssueReceipt.objects.all()
    serializer_class = ErpIssueReceiptSerializer
    
    def genertate_issue_receipt_print(self,erp_issue_receipt_id,request,data):
        metalrates = MetalRates.objects.all().latest('rate_id')
        metalrates_serializer = MetalRatesSerializer(metalrates)
        response_data = data

        save_dir = os.path.join(settings.MEDIA_ROOT, f'issue_receipt\{erp_issue_receipt_id}')

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        template = get_template('issue_receipt_print.html')
        html = template.render(response_data)
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        pdf_path = os.path.join(save_dir, 'issue_receipt_print.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())

        pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'issue_receipt\{erp_issue_receipt_id}\\issue_receipt_print.pdf')

        return pdf_path
    
    def generate_order_print(self, queryset, serializer, output, issue_code, request):
        order_details_qs = ERPOrderDetails.objects.filter(order=queryset.order_id)
        order_details_serialized = ErpOrdersDetailSerializer(order_details_qs, many=True).data

        branch = Branch.objects.filter(id_branch=serializer.data['order_branch']).first()
        customer = Customers.objects.filter(id_customer=serializer.data['customer']).first()
        company = Company.objects.latest("id_company")

        customer_address = CustomerAddress.objects.filter(customer=customer.pk).first()
        address = (
            f"{customer_address.line1 or ''} {customer_address.line2 or ''} {customer_address.line3 or ''}".strip()
            if customer_address else None
        )
        output.update({"address": address})

        order_type_labels = {1: "Customer Order", 2: "Purchase Order", 3: "Repair Order"}
        output.update({"order_type_label": order_type_labels.get(serializer.data['order_type'], "Unknown Order")})

        totals = defaultdict(float)
        order_details = []

        for details in order_details_serialized:

            totals["total_pcs"] += int(details['pieces'])
            totals["total_gross_wt"] += float(details['gross_wt'])
            totals["total_net_wt"] += float(details['net_wt'])
            totals["total_less_wt"] += float(details['less_wt'])
            totals["total_mc"] += float(details['mc_value'])
            totals["total_item_cost"] += float(details['item_cost'])

            order_details.append(details)
        balance_amount = float(totals["total_item_cost"]) - float(output['amount'])
        output.update({
            "order_details": order_details,
            "total_pcs": f"{totals['total_pcs']:.0f}",
            "total_gross_wt": f"{totals['total_gross_wt']:.3f}",
            "total_net_wt": f"{totals['total_net_wt']:.3f}",
            "total_less_wt": f"{totals['total_less_wt']:.3f}",
            "total_item_cost": f"{totals['total_item_cost']:.2f}",
            "balance_amount": f"{balance_amount:.2f}",
            "total_mc": f"{totals['total_mc']:.2f}",
            "branch_name": branch.name,
            "cus_name": customer.firstname,
            "mobile": customer.mobile,
            'company_detail': company,
        })
        
        # print(output)

        order_folder = "erp_reciept_repair_order" if serializer.data['order_type'] == 3 else "erp_receipt_order"
        save_dir = os.path.join(settings.MEDIA_ROOT, order_folder, str(issue_code))
        os.makedirs(save_dir, exist_ok=True)

        template = get_template('order_issue_reciept_print.html')
        html = template.render(output)

        pdf_path = os.path.join(save_dir, f"{order_folder}.pdf")
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)

        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())

        return request.build_absolute_uri(f"{settings.MEDIA_URL}{order_folder}/{issue_code}/{order_folder}.pdf")
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = ErpIssueReceiptSerializer(queryset)
        output = serializer.data
        if(queryset.type == 1):
            output.update({"type":"Issue"})
            if(queryset.issue_to == 1):
                output.update({"name":queryset.customer.firstname, "mobile":queryset.customer.mobile})
            else:
                output.update({"name":queryset.employee.firstname, "mobile":queryset.employee.mobile})
            if(queryset.issue_type == 1):
                output.update({"sub_type":"Credit"})
            elif(queryset.issue_type == 2):
                output.update({"sub_type":"Refund"})
            elif(queryset.issue_type == 3):
                output.update({"sub_type":"Petty Cash"})
            else:
                output.update({"sub_type":None})
        if(queryset.type == 2):
            output.update({"type":"Receipt"})
            output.update({"name":queryset.customer.firstname, "mobile":queryset.customer.mobile})
            if(queryset.receipt_type == 1):
                output.update({"sub_type":"General Advance"})
            elif(queryset.receipt_type == 2):
                output.update({"sub_type":"Order Advance"})
            elif(queryset.receipt_type == 3):
                output.update({"sub_type":"Advance Deposit"})
            elif(queryset.receipt_type == 4):
                output.update({"sub_type":"Import"})
            elif(queryset.receipt_type == 5):
                output.update({"sub_type":"Credit Collection"})
            else:
                output.update({"sub_type":None})
        if (CustomerAddress.objects.filter(customer = queryset.customer.pk).exists()):
            customer_address = CustomerAddress.objects.get(customer = queryset.customer.pk)
            customer_address_serializer = CustomerAddressSerializer(customer_address)
            address = customer_address_serializer.data
            address.update({"state_name":State.objects.get(id_state=customer_address_serializer.data['state']).name})
            output.update({"address":address})
        else:
            output.update({"address":None})
        payment_details = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt=queryset.id)
        payment_detail_serializer = ErpIssueReceiptPaymentDetailsSerializer(payment_details, many=True)
        pay_details = []
        for data in payment_detail_serializer.data:
            mode = PaymentMode.objects.get(id_mode=data['payment_mode']).mode_name
            data.update({"payment_mode":mode})
            if data not in pay_details:
                pay_details.append(data)
        output.update({"payment_details":pay_details})
        
        # if(queryset.receipt_type==2):
        #     order_detail = ERPOrder.objects.get(order_id=queryset.order.pk)
        #     order_detail_serializer = ErpOrdersSerializer(order_detail)
        #     order_data = order_detail_serializer.data
        #     if(order_detail.order_type==1):
        #         order_data.update({"order_type":"Customer Order"})
        #     elif(order_detail.order_type==2):
        #         order_data.update({"order_type":"Purchase Order"})
        #     else:
        #         order_data.update({"order_type":"Repair Order"})
        #     output.update({"order_details":order_data})
        if(queryset.receipt_type==2):
            order_queryset = ERPOrder.objects.filter(order_id=queryset.order.pk).first()
            order_serializer = ErpOrdersSerializer(order_queryset)
            output.update({"order":order_serializer.data})
            order_pdf_path = self.generate_order_print(order_queryset, order_serializer, output, queryset.bill_no, request)
            response_data = { 'pdf_url': order_pdf_path}
            return Response(response_data, status=status.HTTP_202_ACCEPTED)
        else:
            pdf_url = self.genertate_issue_receipt_print(queryset.id,request,output)
            response_ = { 'pdf_url': pdf_url}
            return Response(response_, status=status.HTTP_200_OK)
        # return Response(output, status=status.HTTP_200_OK)

class ErpInvoiceReturnDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():    
                fin_year = request.data['fin_year_id']
                bill_no = request.data['bill_no']
                id_branch = request.data['id_branch']
                id_customer = request.data['id_customer']
                queryset = ErpInvoice.objects.filter(fin_year = fin_year,sales_invoice_no=bill_no,id_branch=id_branch,id_customer=id_customer,invoice_status = 1).get()
                inv_serializer = ErpInvoiceSerializer(queryset,many=False)
                invoice_data = inv_serializer.data
                invoice_data.update({"days_difference":(datetime.now() - datetime.strptime(invoice_data['invoice_date'], "%Y-%m-%d") ).days})
                sales_details = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id=invoice_data['erp_invoice_id'],status=1)
                sale_serializer = ErpInvoiceSalesDetailsSerializer(sales_details, many=True,context={'stone_details': True, 'charges_details': True})
                sales_details = sale_serializer.data
                return_data = {
                    "invoice_data" : invoice_data,
                    "sales_details" : sales_details
                }
            return Response({"message":"Invoice Canceled Successfully.","data":return_data}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"message": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"message": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except ErpInvoice.DoesNotExist:
             return Response({"message":"No Record Found"}, status=status.HTTP_400_BAD_REQUEST)

        



class ErpInvoiceCreditDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        type = request.data['type'] # 1 isssueRecipt Credit 2 Invoice Credit
        id_customer = request.data['id_customer']
        settings_bill_type = request.data['settings_bill_type']
        if(type == 1):
            queryset = ErpIssueReceipt.objects.filter(customer = id_customer,issue_type=1,bill_status=1,setting_bill_type= settings_bill_type)
            serializered_data = ErpIssueReceiptSerializer(queryset,many=True).data
            response_data = []
            for data in serializered_data:
                received_amount = 0
                issued_amount = float(data['amount'])
                balance_amount =0
                col = ErpReceiptCreditCollection.objects.filter(issue = data['id'],receipt__bill_status= 1)
                col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
                for collection in col_data:
                    received_amount += float(collection['received_amount']) + float(collection['discount_amount'])
                balance_amount = issued_amount - received_amount
                if(balance_amount > 0):
                    data.update({'issued_amount':issued_amount,'balance_amount':balance_amount,'received_amount':received_amount,'discount':0,'amount':0, })
                    response_data.append(data)
        elif(type == 2):
            queryset = ErpInvoice.objects.filter(id_customer = id_customer,is_credit=1,invoice_status=1,credit_status=0)
            serializered_data = ErpInvoiceSerializer(queryset,many=True).data
            response_data = []
            for data in serializered_data:
                received_amount = 0
                issued_amount = float(data['due_amount'])
                balance_amount =0
                col = ErpReceiptCreditCollection.objects.filter(invoice_bill_id = data['erp_invoice_id'],receipt__bill_status= 1)
                col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
                for collection in col_data:
                    received_amount += (float(collection['received_amount']) + float(collection['discount_amount']))
                balance_amount = issued_amount - received_amount
                if(balance_amount > 0):
                    invoice_no = get_invoice_no(data)
                    data.update({'bill_no':invoice_no['invoice_no'],'issued_amount':issued_amount,'balance_amount':balance_amount,'received_amount':received_amount,'discount':0,'amount':0, })
                    response_data.append(data)

        if(response_data):
            return Response({"message":"Data Retived Successfully.","data":response_data}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message":"No Data Credit Data Available for this Customer","data":[]}, status=status.HTTP_201_CREATED)




class ErpInvoiceAdvanceDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_customer = request.data['id_customer']
        settings_bill_type = request.data['settings_bill_type']
        queryset = ErpIssueReceipt.objects.filter(customer = id_customer,receipt_type__in=[1,2,3,4],bill_status=1,setting_bill_type = settings_bill_type)
        serializered_data = ErpIssueReceiptSerializer(queryset,many=True).data
        response_data = []
        for data in serializered_data:
            refunded_amount = 0
            adjusted_amount = 0
            advance_amount = float(data['amount'])
            balance_amount =0
            refund = ErpReceiptRefund.objects.filter(receipt = data['id'],issue__bill_status= 1)
            refund_data = ErpReceiptRefundSerializer(refund,many=True).data
            for ref in refund_data:
                refunded_amount += float(ref['refund_amount'])
            adjusted = ErpReceiptAdvanceAdj.objects.filter(receipt = data['id'],invoice_bill_id__invoice_status =1,is_adjusted = True)
            adjusted_data = ErpReceiptAdvanceAdjSerializer(adjusted,many=True).data
            for adj in adjusted_data:
                adjusted_amount += float(adj['adj_amount'])
            twod_adjusted = ErpAdvanceAdj.objects.filter(receipt = data['id'],invoice_bill_id__invoice_status =1)
            twod_adjusted_data = ErpAdvanceAdjSerializer(twod_adjusted,many=True).data
            for adj in twod_adjusted_data:
                adjusted_amount += float(adj['adj_amount'])
            balance_amount = advance_amount - refunded_amount - adjusted_amount
            if(balance_amount > 0):
                new_data = {'bill_no':data['bill_no'],'id_issue_receipt':data['id'],'advance_amount':advance_amount,'balance_amount':balance_amount,'refunded_amount':refunded_amount,'adjusted_amount':adjusted_amount,'discount':0,'amount':0, }
                response_data.append(new_data)
        if(response_data):
            return Response({"message":"Data Retived Successfully.","data":response_data}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message":"No Data Credit Data Available for this Customer","data":[]}, status=status.HTTP_201_CREATED)



       

class ErpInvoiceChitsDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        # id_customer = request.data['id_customer']
        id_sch_account = request.data.get('id_sch_account', None)
        id_customer = request.data.get('id_customer', None)
        if(id_customer):
            queryset = SchemeAccount.objects.filter(id_customer = id_customer,is_closed=True,is_utilized=False)
            response_data = SchemeAccountSerializer(queryset,many=True).data
            for item, instance in zip(response_data, queryset):
                if(instance.closing_weight > 0.000):
                    benefit_settings = SchemeBenefitSettings.objects.filter(
                        scheme=instance.acc_scheme_id,
                        installment_from__lte=instance.total_paid_ins,
                        installment_to__gte=instance.total_paid_ins
                        ).first()
                    if benefit_settings:
                        item.update({
                            "id_metal":instance.acc_scheme_id.sch_id_metal.pk,
                            "id_purity":instance.acc_scheme_id.sch_id_purity.pk,
                            "wastage_benefit": benefit_settings.wastage_benefit,
                            "mc_benefit": benefit_settings.mc_benefit
                        })
                item.update({
                    "scheme_name":instance.acc_scheme_id.scheme_name,
                })
            if(response_data):
                return Response({"message":"Data Retived Successfully.","data":response_data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message":"No Data Credit Data Available for this Customer","data":[]}, status=status.HTTP_201_CREATED)
            
        if(id_sch_account):
            queryset = SchemeAccount.objects.filter(id_scheme_account = id_sch_account,is_closed=True,is_utilized=False)
            response_data = SchemeAccountSerializer(queryset,many=True).data
            for item, instance in zip(response_data, queryset):
                if(instance.closing_weight > 0.000):
                    benefit_settings = SchemeBenefitSettings.objects.filter(
                        scheme=instance.acc_scheme_id,
                        installment_from__lte=instance.total_paid_ins,
                        installment_to__gte=instance.total_paid_ins
                        ).first()
                    if benefit_settings:
                        item.update({
                            "id_metal":instance.acc_scheme_id.sch_id_metal.pk,
                            "id_purity":instance.acc_scheme_id.sch_id_purity.pk,
                            "wastage_benefit": benefit_settings.wastage_benefit,
                            "mc_benefit": benefit_settings.mc_benefit
                        })
                item.update({
                    "scheme_name":instance.acc_scheme_id.scheme_name,
                })
            if(response_data):
                return Response({"message":"Data Retived Successfully.","data":response_data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message":"No Data Credit Data Available for this Account","data":[]}, status=status.HTTP_201_CREATED)


class BankSettlementListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']

        queryset = BankSettlements.objects.all()
        if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date]).order_by('-id_settlement')

        paginator, page = pagination.paginate_queryset(queryset, request,None,SETTLEMENT_COLUMN_LIST)
        columns = get_reports_columns_template(request.user.pk,SETTLEMENT_COLUMN_LIST,request.data.get('path_name',''))
        serializer = BankSettlementsSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update({
                "card_difference_amount":format((float(data['card_payment_amount'])-float(data['card_received_amount'])),'.2f'),
                "net_banking_difference_amount":format((float(data['net_banking_payment_amount'])-float(data['net_banking_received_amount'])),'.2f'),
                "upi_difference_amount":format((float(data['upi_payment_amount'])-float(data['upi_received_amount'])),'.2f'),
            })
        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = False
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

class BankSettlementsListCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = BankSettlements.objects.all()
    serializer_class = BankSettlementsSerializer
    
    def post(self, request, *args, **kwargs):
        for data in request.data['bank_settlement_data']:
            if(BankSettlements.objects.filter(invoice_date=data['invoice_date']).exists()):
                BankSettlements.objects.filter(invoice_date=data['invoice_date']).update(
                    card_payment_amount=data['card_payment_amount'],
                    card_received_amount=data['card_received_amount'],
                    net_banking_payment_amount=data['net_banking_payment_amount'],
                    net_banking_received_amount=data['net_banking_received_amount'],
                    upi_payment_amount=data['upi_payment_amount'],
                    upi_received_amount=data['upi_received_amount'],
                    updated_by=request.user,
                    updated_on=datetime.now(tz=timezone.utc)
                )
            else:
                data.update({"created_by": request.user.id})
                serializer = BankSettlementsSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        return Response({"message":"Bank Settlement created successfully."},status=status.HTTP_200_OK)
    

class InvoiceOnlinePaymentDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        id_bank = request.data.get('id_bank')
        if not from_date  :
            return Response({"message": "From date is missing."}, status=status.HTTP_400_BAD_REQUEST)
        if not to_date  :
            return Response({"message": "To date is missing."}, status=status.HTTP_400_BAD_REQUEST)
        if not id_bank:
            return Response({"message": "Bank ID is missing."}, status=status.HTTP_400_BAD_REQUEST)

        query = f"""
        select i.invoice_date,
        (SELECT IFNULL(SUM(d.payment_amount), 0) AS payment_amount
            FROM erp_invoice_payment_details d 
            left JOIN paymentmode p ON p.id_mode = d.payment_mode_id
            left join erp_invoice e on e.erp_invoice_id = d.invoice_bill_id_id
            WHERE p.short_code = 'CC' and e.invoice_status = 1 and e.invoice_date = i.invoice_date
            AND DATE_FORMAT(e.invoice_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
            AND d.id_bank_id = {id_bank}
        ) as card_payment,
        (SELECT IFNULL(SUM(d.payment_amount), 0) AS payment_amount
            FROM erp_invoice_payment_details d 
            left JOIN paymentmode p ON p.id_mode = d.payment_mode_id
            left join erp_invoice e on e.erp_invoice_id = d.invoice_bill_id_id
            WHERE p.short_code = 'NB' and e.invoice_status = 1 and e.invoice_date = i.invoice_date
            AND DATE_FORMAT(e.invoice_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
            AND d.id_bank_id = {id_bank}
        ) as net_banking_payment,
        (SELECT IFNULL(SUM(d.payment_amount), 0) AS payment_amount
            FROM erp_invoice_payment_details d 
            left JOIN paymentmode p ON p.id_mode = d.payment_mode_id
            left join erp_invoice e on e.erp_invoice_id = d.invoice_bill_id_id
            WHERE p.short_code = 'UPI' and e.invoice_status = 1 and e.invoice_date = i.invoice_date
            AND DATE_FORMAT(e.invoice_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
            AND d.id_bank_id = {id_bank}
        ) as upi_payment
        from erp_invoice i
        where i.invoice_status = 1
        AND DATE_FORMAT(i.invoice_date, '%Y-%m-%d') BETWEEN '{from_date}' AND '{to_date}'
        group by i.invoice_date
        having card_payment > 0 or net_banking_payment > 0 or upi_payment > 0
        """
        result = generate_query_result(query)
        return Response({"message":"Data Retrieved Successfully.","data":result}, status=status.HTTP_201_CREATED)
    
class JewelNotDeliveredAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        id_customer = request.data.get('customer')
        bill_setting_type = request.data['bill_setting_type']
        try:
            queryset = ErpItemDelivered.objects.filter(bill__invoice_status = 1)
            if id_branch and id_customer:
                queryset = queryset.filter(branch=id_branch, customer=id_customer)
            elif id_branch:
                queryset = queryset.filter(branch=id_branch)
            elif id_customer:
                queryset = queryset.filter(customer=id_customer)

            data = ErpItemDeliveredSerializer(queryset,many=True).data

            response_data=[]
            for item, instance in zip(data, queryset):
                inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.bill.erp_invoice_id,
                                                      setting_bill_type=bill_setting_type)
                inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                inv_data = get_invoice_no(inv_serializer)
                if(instance.is_delivered == 2):
                    item.update({"show_checkbox":True, "isChecked":False, "status":"Not Delivered", "colour":"danger"})
                else:
                    item.update({"show_checkbox":False, "status":"Delivered", "colour":"success"})
                item.update({"bill_no":inv_data['invoice_no'], "customer_name":instance.customer.firstname,
                             "branch_name":instance.branch.name, "customer_mobile":instance.customer.mobile,
                             "bill_date":format_date(item['entry_date']), "product_name":instance.product.product_name})
                if(item['delivered_by'] != None):
                    item.update({"delivered_by":instance.delivered_by.first_name,
                                 "delivered_on":date_format_with_time(item['delivered_on'])})
                else:
                    item.update({"delivered_by":None, "delivered_on":None})
                if item not in response_data:
                    response_data.append(item)
            return Response({"message":"Data Retived Successfully.","data":response_data}, status=status.HTTP_201_CREATED)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                deliver_details = request.data.get('deliver_details')
                for ret_item in deliver_details:
                    id_item_delivered = ret_item['id_item_delivered']
                    query_set = ErpItemDelivered.objects.get(id_item_delivered =id_item_delivered)
                    query_set.is_delivered = 1
                    query_set.delivered_by = self.request.user
                    query_set.delivered_on = datetime.now(tz=timezone.utc)
                    query_set.save()

                return Response({"message":"Delivered Successfully.",}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)

class JewelNotDeliveredRevertAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                deliver_details = request.data.get('deliver_details')
                for ret_item in deliver_details:
                    id_item_delivered = ret_item['id_item_delivered']
                    query_set = ErpItemDelivered.objects.get(id_item_delivered =id_item_delivered)
                    query_set.is_delivered = 2
                    # query_set.delivered_by = self.request.user
                    # query_set.delivered_on = datetime.now(tz=timezone.utc)
                    query_set.save()

                return Response({"message":"Delivered Successfully.",}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)

class JewelNotDeliveredProductWiseAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def post(self, request, *args, **kwargs):
        id_customer = request.data.get('customer')

        try:
            # Query for undelivered items
            queryset = ErpItemDelivered.objects.filter(is_delivered=2)
            if id_customer:
                queryset = queryset.filter(customer=id_customer)

            # Dictionary to store aggregated data per customer
            customer_data = defaultdict(lambda: {"products": set(), "total_weight": 0, "total_pieces": 0})

            for item in queryset:
                customer_id = item.customer.id_customer  # Group by customer
                customer_data[customer_id]["products"].add(item.product.product_name)  # Store unique product names
                customer_data[customer_id]["total_weight"] += float(item.weight)  # Sum weight
                customer_data[customer_id]["total_pieces"] += item.piece  # Sum pieces
                
                credit_queryset = ErpIssueReceipt.objects.filter(customer=item.customer.id_customer, issue_type=1, bill_status=1)
                credit_serializer = ErpIssueReceiptSerializer(credit_queryset, many=True).data
        
                outstanding_amount = 0
                for credits in credit_serializer:
                    received_amount = 0
                    issued_amount = float(credits['amount'])
                    balance_amount = 0
                    col = ErpReceiptCreditCollection.objects.filter(issue=credits['id'], receipt__bill_status=1)
                    col_data = ErpReceiptCreditCollectionSerializer(col, many=True).data
                    for collection in col_data:
                        received_amount += float(collection['received_amount']) + float(collection['discount_amount'])
                    balance_amount = issued_amount - received_amount
                    if balance_amount > 0:
                        outstanding_amount += balance_amount 
                customer_data[customer_id]["outstanding_amount"] = outstanding_amount

            # Prepare response data
            response_data = [
                {
                    "customer": Customers.objects.get(id_customer=customer_id).firstname,
                    "mobile": Customers.objects.get(id_customer=customer_id).mobile,
                    "products": ",".join(sorted(customer_data[customer_id]["products"])),  # Concatenated product names
                    "weight": customer_data[customer_id]["total_weight"],
                    "pieces": customer_data[customer_id]["total_pieces"],
                    "outstanding_amount": customer_data[customer_id]["outstanding_amount"],
                }
                for customer_id in customer_data
            ]

            # return Response({"message": "Data Retrieved Successfully.", "data": response_data}, status=status.HTTP_200_OK)
            paginator, page = pagination.paginate_queryset(response_data, request,None,JEWEL_NOT_DELIVERED_COLUMN_LIST)
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = False
            filters_copy['isBranchFilterReq'] = False
            filters_copy['isSchemeFilterReq'] = False
            filters_copy['isCustomerFilterReq'] = True
            
            actions_copy = ACTION_LIST.copy()
            actions_copy['is_add_req'] = False
            actions_copy['is_cancel_req'] = False
            context = {
                'columns': JEWEL_NOT_DELIVERED_COLUMN_LIST,
                'actions': actions_copy,
                'page_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page.number,
                'is_filter_req': True,
                'filters': filters_copy
            }
    
            return pagination.paginated_response(response_data, context)

        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class ErpInvoiceDiscountCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpInvoiceDiscount.objects.all()
    serializer_class = ErpInvoiceSerializer
    
    def get(self, request, *args, **kwargs):
        erp_invoice_id = self.kwargs.get('pk')
        metalrates = MetalRates.objects.all().latest('rate_id')
        metalrates_serializer = MetalRatesSerializer(metalrates)
        inv = ErpInvoiceDiscount.objects.get(erp_invoice_id=erp_invoice_id)
        inv_serializer = ErpInvoiceDiscountSerializer(inv)
        sales_details = ErpInvoiceDiscountSalesDetails.objects.filter(invoice_bill_id=inv)
        sale_serializer = ErpInvoiceSalesDiscountDetailsSerializer(sales_details, many=True,context={'stone_details': True, 'charges_details': True})
        purchase_details = ErpInvoiceDiscountOldMetalDetails.objects.filter(invoice_bill_id=inv)
        purchase_serializer = ErpInvoiceDiscountOldMetalDetailsSerializer(purchase_details, many=True)
        # scheme_adjusted = ErpInvoiceSchemeAdjusted.objects.filter(invoice_bill_id=inv)
        # scheme_adjusted_serializer = ErpInvoiceSchemeAdjustedSerializer(scheme_adjusted, many=True)
        inv_payment_details = ErpInvoiceDiscountPaymentModeDetail.objects.filter(invoice_bill_id=inv)
        payment_details_serializer = ErpInvoiceDiscountPaymentModeDetailSerializer(inv_payment_details, many=True)
        # return_details = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id=inv)
        # return_details_serializer = ErpInvoiceSalesReturnSerializer(return_details,many=True)
        response_data = inv_serializer.data
        sales_details = sale_serializer.data
        purchase_details = purchase_serializer.data
        return_details = []  #return_details_serializer.data
        payment_details = payment_details_serializer.data
        scheme_details = [] #scheme_adjusted_serializer.data
        sgst_cost =0
        cgst_cost =0
        igst_cost =0
        tax_per=0
        total_taxable =0
        total_nwt =0
        total_gwt =0
        total_pur_nwt =0
        total_pur_gwt =0
        deposit_bill  = None #inv.deposit_bill.first()
        advance_adj_bill  = inv.advance_adj_inv.all()
        deposit_amount = 0
        sr_sgst_cost =0
        sr_cgst_cost =0
        sr_igst_cost =0
        sr_tax_per=0
        sr_total_taxable =0
        sr_total_nwt =0
        sr_total_gwt =0
        advance_adj_amount = 0
        total_chit_amount = 0
        if(advance_adj_bill):
            for adj_bill in advance_adj_bill:
                advance_adj_amount += float(adj_bill.adj_amount)
        if(deposit_bill):
            deposit_amount = format(deposit_bill.amount, '.2f')


        for item in sales_details:
            total_gwt += float(item.get('gross_wt', 0))
            total_nwt += float(item.get('net_wt', 0))
            sgst_cost += float(item.get('sgst_cost', 0))
            cgst_cost += float(item.get('cgst_cost', 0))
            igst_cost += float(item.get('igst_cost', 0))
            total_taxable += float(item.get('taxable_amount', 0))
            tax_per += float(item.get('tax_percentage', 0))

        for item in purchase_details:
            total_pur_gwt += float(item.get('gross_wt', 0))
            total_pur_nwt += float(item.get('net_wt', 0))
        
        for item in return_details:
            print(item['invoice_sale_item_details'])
            item.update(item['invoice_sale_item_details'])
            sr_total_gwt += float(item.get('gross_wt', 0))
            sr_total_nwt += float(item.get('net_wt', 0))
            sr_sgst_cost += float(item.get('sgst_cost', 0))
            sr_cgst_cost += float(item.get('cgst_cost', 0))
            sr_igst_cost += float(item.get('igst_cost', 0))
            sr_total_taxable += float(item.get('taxable_amount', 0))
            sr_tax_per += float(item.get('tax_percentage', 0))

        for item, instance in zip(payment_details, inv_payment_details):
            mode_name = instance.payment_mode.mode_name
            item.update({
                "mode_name":mode_name
            })

        # for item, instance in zip(scheme_details, scheme_adjusted):
           
        #     item.update({
        #         "closing_amount":instance.id_scheme_account.closing_amount
        #     })
        #     total_chit_amount += float(item['closing_amount'])


        if sales_details:
            tax_per= tax_per / len(sales_details)
            response_data['total_gwt'] = format(total_gwt, '.3f')
            response_data['total_nwt'] = format(total_nwt, '.3f')
            response_data['total_taxable'] = format(total_taxable,'.2f')
            response_data['sgst_cost'] = format(sgst_cost, '.3f')
            response_data['cgst_cost'] = format(cgst_cost, '.3f')
            response_data['igst_cost'] = format(igst_cost, '.3f')
            response_data['tax_per'] = round(tax_per, 2)
            response_data['igst_per'] = round(tax_per, 2) 
            response_data['cgst_per'] = round(tax_per / 2, 2)
            response_data['sgst_per'] = round(tax_per / 2, 2)

        if return_details:
            tax_per= tax_per / len(return_details)
            response_data['sr_total_gwt'] = format(sr_total_gwt, '.3f')
            response_data['sr_total_nwt'] = format(sr_total_nwt, '.3f')
            response_data['sr_total_taxable'] = format(sr_total_taxable,'.2f')
            response_data['sr_sgst_cost'] = format(sr_sgst_cost, '.3f')
            response_data['sr_cgst_cost'] = format(sr_cgst_cost, '.3f')
            response_data['sr_igst_cost'] = format(sr_igst_cost, '.3f')
            response_data['sr_tax_per'] = round(sr_tax_per, 2)
            response_data['sr_igst_per'] = round(sr_tax_per, 2) 
            response_data['sr_cgst_per'] = round(sr_tax_per / 2, 2)
            response_data['sr_sgst_per'] = round(sr_tax_per / 2, 2)

        response_data['total_pur_nwt'] = format(total_pur_nwt,'.3f')
        response_data['total_pur_gwt'] = format(total_pur_gwt,'.3f')

        response_data['sales_details'] = sales_details
        response_data['purchase_details'] = purchase_details
        response_data['scheme_details'] = scheme_details
        response_data['payment_details'] = payment_details
        response_data['return_details'] = return_details
        response_data['metal_rates'] = metalrates_serializer.data
        response_data['advance_adj_amount'] = advance_adj_amount
        response_data['total_chit_amount'] = total_chit_amount
        response_data['balance_amount'] = float(response_data['net_amount']) - float(response_data['received_amount']) - float(response_data['due_amount']) - float(total_chit_amount)

        if  response_data['balance_amount'] > 0 :

            response_data['balance_amount'] =  format_currency(response_data['balance_amount'])
        else :
            response_data['balance_amount'] = 'NIL'

        if  float(response_data['due_amount']) > 0 :

            response_data['show_balance_amount'] =  False
        else :

            response_data['show_balance_amount'] =  True


        response_data['deposit_amount'] =  deposit_amount 
        response_data['invoice_data'] = get_invoice_no(inv_serializer.data)
        print(response_data)
        pdf_url = self.genertate_invoice_print(erp_invoice_id,request,response_data)
        response_ = { 'pdf_url': pdf_url}
        return Response(response_, status=status.HTTP_200_OK)
 

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                invoice_data = request.data.get('invoice')
                sales_details = request.data.get('sales_details')
                purchase_details = request.data.get('purchase_details')
                return_details = request.data.get('return_details',[])
                scheme_details = request.data.get('scheme_details',[])
                payment_details=request.data.get('payment_details')
                advance_details=request.data.get('advance_adjusted_details',[])
                if not invoice_data:
                    return Response({"error": "Invoice data is missing."}, status=status.HTTP_400_BAD_REQUEST)
                if (not sales_details and not purchase_details and not return_details):
                    return Response({"error": "Invoice Details is missing."}, status=status.HTTP_400_BAD_REQUEST)
                branch_date = BranchEntryDate()
                fy=FinancialYear.objects.get(fin_status=True)
                address ={}
                if  invoice_data['id_customer']:
                    customer = Customers.objects.get(id_customer=invoice_data['id_customer'])
                    customer_name =  customer.firstname
                    customer_mobile =  customer.mobile   

                    address = CustomerAddress.objects.get(customer=invoice_data['id_customer'])
                    address = CustomerAddressSerializer(address).data
                    area    = Area.objects.filter(id_area=address['area']).get()
                    country = Country.objects.filter(id_country=address['country']).get()
                    state   = State.objects.filter(id_state=address['state']).get()
                    city    = City.objects.filter(id_city=address['city']).get()
                    address.update({"area_name":area.area_name,"country_name":country.name,"state_name":state.name,"city_name":city.name})
                    print(address)
                invoice_date = branch_date.get_entry_date(invoice_data['id_branch'])
                invoice = self.generate_invoice_no(invoice_data['id_branch'],fy,request)
                invoice.update({"customer_mobile":customer_mobile,"customer_name":customer_name,"invoice_date":invoice_date,"created_by": request.user.id})
                invoice_data.update(invoice)
                inv_serializer = ErpInvoiceDiscountSerializer(data = invoice_data)
                if inv_serializer.is_valid(raise_exception=True):
                    inv_serializer.save()
                    erp_invoice_id = inv_serializer.data['erp_invoice_id']
                    invoice_data.update(inv_serializer.data)
                    if sales_details:

                        sales_details = self.insert_sales_details(sales_details,erp_invoice_id,invoice_data)
                    
                    if purchase_details:

                        purchase_details = self.insert_purchase_details(purchase_details,erp_invoice_id)

                    if scheme_details:

                        scheme_details = self.insert_scheme_details(scheme_details,erp_invoice_id)

                    # if return_details:
                       
                    #    for ret_item in return_details:
                    #        invoice_sale_item_id = ret_item['invoice_sale_item_id']
                    #        query_set = ErpInvoiceSalesDetails.objects.get(invoice_sale_item_id =invoice_sale_item_id)
                    #        query_set.status = 2
                    #        query_set.save()


                    #    return_details = insert_other_details(return_details,ErpInvoiceSalesReturnSerializer,{"invoice_bill_id":erp_invoice_id})

                    if payment_details:
                       
                        for payment in payment_details:
                            payment.update({'payment_mode' : payment['id_mode']})

                        payment_details = insert_other_details(payment_details,ErpInvoiceDiscountPaymentModeDetailSerializer,{"invoice_bill_id":erp_invoice_id})

                    advance_adj_amount = 0
                    if advance_details:
                       
                        for adv in advance_details:
                            advance_adj_amount+=float(adv['utilized_amount'])
                            adv.update({'receipt' : adv['id_issue_receipt'],
                            'adj_amount' : adv['utilized_amount'],
                            })

                        advance_details = insert_other_details(advance_details,ErpAdvanceAdjSerializer,{"invoice_bill_id":erp_invoice_id})

                    if invoice_data.get('deposit_amount'): 

                        branch = Branch.objects.get(id_branch=invoice_data['id_branch'])

                        bill_no = generate_issue_receipt_billno({'branch':invoice_data['id_branch'],'type':1}, branch.short_name, fy, 1)

                        deposit_details = { 'type':1,'receipt_type':3,'fin_year':fy.fin_id,'bill_date':invoice_date,'branch':invoice_data['id_branch'],'bill_no':bill_no,'customer':invoice_data['id_customer'],
                                            'deposit_bill':erp_invoice_id,'amount':invoice_data.get('deposit_amount'),'weight':0,"created_by": request.user.id,"employee": invoice_data['id_employee']}

                        deposit_details = insert_other_details([deposit_details],ErpIssueReceiptSerializer,{"invoice_bill_id":erp_invoice_id})

                    
                    invoice_no = get_invoice_no(inv_serializer.data)
                     
                    data = {
                        **invoice_data,
                        "invoice_data":invoice_no,
                        'sales_details' : sales_details,
                        'purchase_details' : purchase_details,
                        'return_details' : return_details,
                        'payment_details' : payment_details,
                        'scheme_details' : scheme_details,
                        'address' : address,
                        'advance_adj_amount' : advance_adj_amount,
                    }

                    pdf_url = self.genertate_invoice_print(erp_invoice_id,request,data)

                    return Response({"message":"Invoice Created Successfully.","pdf_url": pdf_url,"invoice_id":erp_invoice_id,"pdf_path":"billing/discount_print"}, status=status.HTTP_201_CREATED)
                return Response({"error":ErpInvoiceSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            tb = traceback.format_exc()
            return Response({"error": f"Missing key: {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        
    def generate_invoice_no(self,id_branch,fy,request):

        sales_details = request.data.get('sales_details')
        purchase_details = request.data.get('purchase_details')
        return_details = request.data.get('return_details')
        invoice_type = None
        sales_invoice_no = None
        purchase_invoice_no = None
        return_invoice_no = None
        fin_id = fy.fin_id

        if(sales_details):
            invoice_type = 1
            sales_invoice_no = self.generate_ref_no(id_branch,fin_id,invoice_type)
        if(purchase_details):
            invoice_type = 2
            purchase_invoice_no = self.generate_ref_no(id_branch,fin_id,invoice_type)
            if(sales_details):
                invoice_type = 4
        if(return_details):
            invoice_type = 3
            return_invoice_no = self.generate_ref_no(id_branch,fin_id,invoice_type)
            if(sales_details):
                invoice_type = 5
                if(purchase_details):
                    invoice_type = 6

        return {'invoice_type':invoice_type,'sales_invoice_no':sales_invoice_no,'purchase_invoice_no':purchase_invoice_no,'return_invoice_no':return_invoice_no,'fin_year':fin_id }
        
            

    def generate_ref_no(self,id_branch,fin_id,bill_type):
        code =''
        if(bill_type==1):
            last_inv=ErpInvoiceDiscount.objects.filter(id_branch=id_branch,fin_year =fin_id, sales_invoice_no__isnull=False).order_by('-erp_invoice_id').first()
        if(bill_type==2):
            last_inv=ErpInvoiceDiscount.objects.filter(id_branch=id_branch,fin_year =fin_id, purchase_invoice_no__isnull=False).order_by('-erp_invoice_id').first()
        if(bill_type==3):
            last_inv=ErpInvoiceDiscount.objects.filter(id_branch=id_branch,fin_year =fin_id, return_invoice_no__isnull=False).order_by('-erp_invoice_id').first()
        if last_inv:
           if(bill_type==1):
                code= int(last_inv.sales_invoice_no)
                code = str(code + 1).zfill(5)
           if(bill_type==2):
                code= int(last_inv.purchase_invoice_no)
                code = str(code + 1).zfill(5)
           if(bill_type==3):
                code= int(last_inv.return_invoice_no)
                code = str(code + 1).zfill(5)
        else:
           code = '00001'
        return code

    
    def insert_sales_details(self,sales_details,erp_invoice_id,invoice_data):
        return_data =[]

        for sales_item in sales_details:
            
            sales_item.update({"invoice_bill_id":erp_invoice_id})
            item_type =sales_item['item_type']

            if(item_type==0):
                tag_id = sales_item['tag_id']
                tagObj = ErpTagging.objects.filter(tag_id=tag_id).get()
                if(tagObj.container != None):
                    ErpTaggingContainerLogDetails.objects.create(tag=tagObj, from_branch=tagObj.tag_current_branch,
                                                             from_container=tagObj.container,
                                                             to_branch=None, to_container=None, transaction_type=2)
            elif(item_type==1):
                sales_item['tag_id'] = None
            elif(item_type==2):
                tag_id = sales_item['tag_id']


            stone_details = sales_item['stone_details']
            charges_details=sales_item['charges_details']
            other_metal_details=sales_item['other_metal_detail']
            inv_detail_serializer = ErpInvoiceSalesDiscountDetailsSerializer(data=sales_item)
            if(inv_detail_serializer.is_valid(raise_exception=True)):
                inv_detail_serializer.save()
                item_type =inv_detail_serializer.data['item_type']

                stone_details=insert_other_details(stone_details,ErpInvoiceStoneDiscountDetailsSerializer,{"invoice_sale_item_id":inv_detail_serializer.data['invoice_sale_item_id']})

                for charge in charges_details:
                    charge.update({'id_charges' : charge['selectedCharge'],'charges_amount' : charge['amount'],"invoice_sale_item_id":inv_detail_serializer.data['invoice_sale_item_id']})
                    charge_serializer = ErpInvoiceDiscountItemChargesSerializer(data=charge)
                    charge_serializer.is_valid(raise_exception=True)
                    charge_serializer.save()

                other_metal_details=insert_other_details(other_metal_details,ErpInvoiceDiscountOtherMetalSerializer,{"invoice_sale_item_id":inv_detail_serializer.data['invoice_sale_item_id']})

                return_data.append({**sales_item,**inv_detail_serializer.data,'stone_details':stone_details,'charges_details':charges_details,'other_metal_details':other_metal_details})

            
                if item_type == 0:

                    tag_instance = ErpTagging.objects.get(pk=sales_item['tag_id'])
                    
                    tag_serializer = ErpTaggingSerializer(tag_instance, data={"is_special_discount_applied":True,"updated_on":datetime.now(tz=timezone.utc),"updated_by":invoice_data['created_by'],"tag_status":2,"is_partial_sale":sales_item['is_partial_sale'] }, partial=True)
                    tag_serializer.is_valid(raise_exception=True)
                    tag_serializer.save()

                    log_details={
                        'from_branch': invoice_data['id_branch'],
                        'date': invoice_data['invoice_date'],
                        'id_stock_status': 2,
                        'tag_id': sales_item['tag_id'],
                        'transaction_type': 6,
                        'ref_id': inv_detail_serializer.data['invoice_sale_item_id'],
                        "created_by": invoice_data['created_by'],
                    }
                    log_tag_serializer = ErpTaggingLogSerializer(data=log_details)
                    log_tag_serializer.is_valid(raise_exception=True)
                    log_tag_serializer.save()

                if item_type == 1:
                    non_log_details=sales_item
                    non_log_details.update({"from_branch": invoice_data['id_branch'],"date" : invoice_data['invoice_date'],"id_stock_status": 2,'transaction_type': 6,'ref_id': inv_detail_serializer.data['invoice_sale_item_id'],"created_by": invoice_data['created_by']})
                    non_tag_serializer = ErpLotInwardNonTagSerializer(data=non_log_details)
                    non_tag_serializer.is_valid(raise_exception=True)
                    non_tag_serializer.save()
                    insert_other_details(stone_details,ErpLotInwardNonTagStoneSerializer,{"id_non_tag_log":non_tag_serializer.data['id_non_tag_log']})
                if sales_item['est_item_id']:

                    self.update_estimation(sales_item,inv_detail_serializer);         

                if sales_item['order_detail']:

                    self.update_order_status(sales_item,invoice_data['invoice_date']);         
            else:
                return Response({"message":ErpInvoiceSalesDetailsSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        return return_data

    def update_estimation(self,sales_item,inv_detail_serializer):
        queryset = ErpEstimationSalesDetails.objects.get(est_item_id=sales_item['est_item_id'])
        queryset.invoice_sale_item_id = inv_detail_serializer.instance
        queryset.status = 1
        queryset.save()

    def update_order_status(self,sales_item,invoice_date):
        queryset = ERPOrderDetails.objects.get(detail_id=sales_item['order_detail'])
        queryset.order_status = ERPOrderStatus.objects.get(id=5)
        queryset.delivered_on = invoice_date
        queryset.save()

            
    def insert_purchase_details(self,purchase_details,erp_invoice_id):
        return_data =[]
        for purchase_item in purchase_details:
            purchase_item.update({"invoice_bill_id":erp_invoice_id})
            purchase_detail_serializer = ErpInvoiceDiscountOldMetalDetailsSerializer(data=purchase_item)
            if(purchase_detail_serializer.is_valid(raise_exception=True)):
                purchase_detail_serializer.save()

                stone_details=insert_other_details(purchase_item['stone_details'],ErpInvoiceStoneDiscountDetailsSerializer,{"invoice_old_metal_item_id":purchase_detail_serializer.data['invoice_old_metal_item_id']})

                if purchase_item['est_old_metal_item_id']:
                    queryset = ErpEstimationOldMetalDetails.objects.get(est_old_metal_item_id = purchase_item['est_old_metal_item_id'])
                    detail = { 'invoice_old_metal_item_id': purchase_detail_serializer.data['invoice_old_metal_item_id'],'status':1}
                    serializer = ErpEstimationOldMetalDetailsSerializer(queryset, data=detail, partial=True)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                
                return_data.append({**purchase_item,**purchase_detail_serializer.data,'stone_details':stone_details})

            else:
                tb = traceback.format_exc()
                return Response({"error":ErpInvoiceOldMetalDetailsSerializer.errors,'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
            
        return return_data
            
    def insert_scheme_details(self,scheme_details,erp_invoice_id):
        for scheme in scheme_details:
            scheme.update({"invoice_bill_id":erp_invoice_id, "closing_weight":scheme.closing_weight,
                           "wastage":scheme.va, "mc":scheme.mc, "closing_amount":scheme.amount, "rate_per_gram":scheme.rate_per_gram})
            scheme_serializer = ErpInvoiceSchemeAdjustedSerializer(data=scheme)

            if(scheme_serializer.is_valid(raise_exception=True)):
                scheme_instance = scheme_serializer.save()
                scheme_account = scheme_instance.id_scheme_account  # Get the related SchemeAccount
                scheme_account.is_utilized = True
                scheme_account.utilized_type = 2
                scheme_account.save()
            else:
                return Response({"error":ErpInvoiceSchemeAdjustedSerializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
    
    
    
    def genertate_invoice_print (self,erp_invoice_id,request,data):
        metalrates = MetalRates.objects.all().latest('rate_id')
        metalrates_serializer = MetalRatesSerializer(metalrates)
        response_data = data
        sales_details = data['sales_details']
        purchase_details = data['purchase_details']
        return_details = data['return_details']
        payment_details = data['payment_details']
        scheme_details = data['scheme_details']
        sgst_cost =0
        cgst_cost =0
        igst_cost =0
        tax_per=0
        total_taxable =0
        total_nwt =0
        total_gwt =0
        total_pur_nwt =0
        total_pur_gwt =0
        sr_sgst_cost =0
        sr_cgst_cost =0
        sr_igst_cost =0
        sr_tax_per=0
        sr_total_taxable =0
        sr_total_nwt =0
        sr_total_gwt =0

        for item in sales_details:
            total_gwt += float(item.get('gross_wt', 0))
            total_nwt += float(item.get('net_wt', 0))
            sgst_cost += float(item.get('sgst_cost', 0))
            cgst_cost += float(item.get('cgst_cost', 0))
            igst_cost += float(item.get('igst_cost', 0))
            total_taxable += float(item.get('taxable_amount', 0))
            tax_per += float(item.get('tax_percentage', 0))

        for item in purchase_details:
            total_pur_gwt += float(item.get('gross_wt', 0))
            total_pur_nwt += float(item.get('net_wt', 0))

        for item in return_details:
            print(item['invoice_sale_item_details'])
            item.update(item['invoice_sale_item_details'])
            sr_total_gwt += float(item.get('gross_wt', 0))
            sr_total_nwt += float(item.get('net_wt', 0))
            sr_sgst_cost += float(item.get('sgst_cost', 0))
            sr_cgst_cost += float(item.get('cgst_cost', 0))
            sr_igst_cost += float(item.get('igst_cost', 0))
            sr_total_taxable += float(item.get('taxable_amount', 0))
            sr_tax_per += float(item.get('tax_percentage', 0))

        if return_details:
            tax_per= tax_per / len(return_details)
            response_data['sr_total_gwt'] = format(sr_total_gwt, '.3f')
            response_data['sr_total_nwt'] = format(sr_total_nwt, '.3f')
            response_data['sr_total_taxable'] = format(sr_total_taxable,'.2f')
            response_data['sr_sgst_cost'] = format(sr_sgst_cost, '.3f')
            response_data['sr_cgst_cost'] = format(sr_cgst_cost, '.3f')
            response_data['sr_igst_cost'] = format(sr_igst_cost, '.3f')
            response_data['sr_tax_per'] = round(sr_tax_per, 2)
            response_data['sr_igst_per'] = round(sr_tax_per, 2) 
            response_data['sr_cgst_per'] = round(sr_tax_per / 2, 2)
            response_data['sr_sgst_per'] = round(sr_tax_per / 2, 2)


        if sales_details:
            tax_per= tax_per / len(sales_details)
            response_data['total_gwt'] = format(total_gwt, '.3f')
            response_data['total_nwt'] = format(total_nwt, '.3f')
            response_data['total_taxable'] = format(total_taxable,'.2f')
            response_data['sgst_cost'] = format(sgst_cost, '.3f')
            response_data['cgst_cost'] = format(cgst_cost, '.3f')
            response_data['igst_cost'] = format(igst_cost, '.3f')
            response_data['tax_per'] = round(tax_per, 2)
            response_data['igst_per'] = round(tax_per, 2) 
            response_data['cgst_per'] = round(tax_per / 2, 2)
            response_data['sgst_per'] = round(tax_per / 2, 2)

        response_data['total_pur_nwt'] = format(total_pur_nwt,'.3f')
        response_data['total_pur_gwt'] = format(total_pur_gwt,'.3f')

        response_data['sales_details'] = sales_details
        response_data['purchase_details'] = purchase_details
        response_data['scheme_details'] = scheme_details
        response_data['payment_details'] = payment_details
        response_data['return_details'] = return_details
        response_data['metal_rates'] = metalrates_serializer.data
        print('value')
        print(response_data['due_amount'])

        save_dir = os.path.join(settings.MEDIA_ROOT, f'discount_billing/{erp_invoice_id}')

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(erp_invoice_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(save_dir, 'qrcode.png')
        qr_img.save(qr_path)

        response_data['qr_path'] = qr_path

        template = get_template('bill_discount_print.html')
        html = template.render(response_data)
        result = io.BytesIO()
        pisa.pisaDocument(io.StringIO(html), result)
        pdf_path = os.path.join(save_dir, 'bill_print.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())

        pdf_path = request.build_absolute_uri(settings.MEDIA_URL + f'discount_billing/{erp_invoice_id}/bill_print.pdf')

        return pdf_path
            

def insert_other_details(details,serializer_name,updated_data):
    return_data =[]
    for item in details:
        if(updated_data != None):
            item.update(updated_data)
        serializer = serializer_name(data=item)
        if(serializer.is_valid(raise_exception=True)):
            serializer.save()
            return_data.append({**item,**serializer.data})
        else:
            return Response({"error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    return return_data

class ErpInvoiceDiscountListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        id_branch = (id_branch) if id_branch != '' else 1

        queryset = ErpInvoiceDiscount.objects.all()
        if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])
        if isinstance(id_branch, list):
            queryset = queryset.filter(id_branch__in=id_branch)
        else:
            queryset = queryset.filter(id_branch=id_branch)

        paginator, page = pagination.paginate_queryset(queryset, request,None,INVOICE_COLUMN_LIST)
        serializer = ErpInvoiceSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            inv_data = get_invoice_no(data)

            data.update({"pk_id":data['erp_invoice_id'], "sno":index+1,"invoice_no":inv_data['invoice_no'],'status_color': 'success' if (data['invoice_status']==1) else 'danger',"invoice_date":format_date(data['invoice_date']),'status': 'Success' if (data['invoice_status']==1) else 'Cancel','invoice_status_name': 'Success' if (data['invoice_status']==1) else 'Cancel','is_cancelable': True if (data['invoice_status']==1) else False})

        FILTERS['isDateFilterReq'] = True
        FILTERS['isBranchFilterReq'] = True
        FILTERS['isSchemeFilterReq'] = False
        context={
            'columns':INVOICE_COLUMN_LIST,
            'actions':ACTION_LIST,
            'page_count':paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req':True,
            'filters':FILTERS
            }
        return pagination.paginated_response(serializer.data,context)


    
def insert_incentive_details(details,id_branch,date):
    return_data =[]
    settings = IncentiveSettings.objects.filter(branch=id_branch, start_date__lte=date, end_date__gte=date)
    print(IncentiveSettings.objects.all(),"has Settings")
    if(settings):
        print(settings,"has Settings")
        for inst in settings:

            if inst.employee_roles:
                employee_roles = json.loads(inst.employee_roles)
            else:
                employee_roles = [0,0,0]
            
            if inst.weight_ranges:
                weight_ranges = json.loads(inst.weight_ranges)
            else:
                weight_ranges = []
            
            products = json.loads(inst.applicable_products)
            filtered = [item for item in products if item["value"] == details["id_product"]]
            incentive_amount = 0 
            if filtered:
                print(filtered,"has product")
                if int(inst.calculation_method) == 1:
                    incentive_amount = inst.value
                
                elif int(inst.calculation_method) == 2:
                    incentive_amount = float(details["taxable_amount"]) * (float(inst.value)/100)

                elif int(inst.calculation_method) == 3:
                    incentive_amount =  float(details["net_wt"]) * float(inst.value)
            
                elif int(inst.calculation_method) == 4:
                    filtered_wt_range = [item for item in weight_ranges if float(item["from_weight"]) <= float(details["net_wt"]) and float(item["to_weight"]) >= float(details["net_wt"]) ]
                    if filtered_wt_range:
                        filtered_wt_range = filtered_wt_range[0]
                        incentive_amount = filtered_wt_range["value"]

                emp1 =  details['ref_emp_id']
                emp2 =  details.get('ref_emp_id_1')
                emp3 =  details.get('ref_emp_id_2')
                if( incentive_amount != 0):
                    data = {
                        "transaction_date" : date,
                        "sale_item":details["invoice_sale_item_id"],
                        "incentive":inst.pk,
                        "product":details["id_product"],
                        "quantity":details["pieces"],
                        "weight":details["net_wt"],
                        "sale_value":details["taxable_amount"],
                    }
                    insert_data = {}

                    if(emp1):

                        emp1_amt = float(incentive_amount) * (float(employee_roles[0])/100)
                        insert_data = {
                        **data,
                        "employee":emp1,
                        "incentive_amount":emp1_amt,
                        "employee_role":0,
                        }
                        print(insert_data,"has Emp")

                        serializer = IncentiveTransactionsSerializer(data=insert_data)
                        if(serializer.is_valid(raise_exception=True)):
                            serializer.save()
                    if(emp2):
                        emp2_amt = float(incentive_amount) * (float(employee_roles[1])/100)
                        insert_data = {
                        **data,
                        "employee":emp2,
                        "incentive_amount":emp2_amt,
                        "employee_role":1,
                        }
                        serializer = IncentiveTransactionsSerializer(data=insert_data)
                        if(serializer.is_valid(raise_exception=True)):
                            serializer.save()
                    if(emp3):
                        emp3_amt = float(incentive_amount) * (float(employee_roles[2])/100)
                        insert_data = {
                        **data,
                        "employee":emp3,
                        "incentive_amount":emp3_amt,
                        "employee_role":2,
                        }
                        serializer = IncentiveTransactionsSerializer(data=insert_data)
                        if(serializer.is_valid(raise_exception=True)):
                            serializer.save()
                    break


class ErpInvoiceDepositDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_customer = request.data['id_customer']
        today = now().date()
        queryset = CustomerDeposit.objects.filter(
            customer=id_customer,
            bill=None,
            closing_date__lte=today)
        serializered_data = CustomerDepositSerializer(queryset,many=True).data
        for data in serializered_data:
            depo_master_obj = DepositMaster.objects.get(id_deposit_master=data['deposit'])
            data.update({"deposit_type":depo_master_obj.type})
        return Response({"message":"Data Retived Successfully.","data":serializered_data}, status=status.HTTP_200_OK)


class ErpInvoiceDeleteDetailsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpInvoice.objects.all()
    serializer_class = ErpInvoiceSerializer
    
    def post(self, request, *args, **kwargs):
        erp_invoice_ids = request.data.get('erp_invoice_ids')
        if (not erp_invoice_ids):
            return Response({"error": "Invoice Id Is Missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                save_dir = os.path.join(settings.MEDIA_ROOT, f'sql_export')
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                now = datetime.now()
                timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
                filename = f"db_{timestamp}.sql"
                save_dir = os.path.join(save_dir, filename)
                delete_bills(erp_invoice_ids,save_dir)
                return Response({"message":"Data Retived Successfully."}, status=status.HTTP_200_OK)


        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)    

def delete_bills(erp_invoice_ids,save_dir):
    for erp_invoice_id in erp_invoice_ids:
        inv = ErpInvoice.objects.get(erp_invoice_id=erp_invoice_id)
        export_sql(save_dir,[inv],ErpInvoice)
        sales_details = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id=inv)
        purchase_details = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id=inv)
        inv_payment_details = ErpInvoicePaymentModeDetail.objects.filter(invoice_bill_id=inv)
        return_details = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id=inv)
        delivery_details = ErpItemDelivered.objects.filter(bill=inv)

        export_sql(save_dir,inv_payment_details,ErpInvoicePaymentModeDetail)
        export_sql(save_dir,return_details,ErpInvoiceSalesReturn)
        export_sql(save_dir,delivery_details,ErpItemDelivered)

        return_details.delete()
        inv_payment_details.delete()
        for item in sales_details:
            export_sql(save_dir,[item],ErpInvoiceSalesDetails)
            stn = ErpInvoiceStoneDetails.objects.filter(invoice_sale_item_id=item)
            charges = ErpInvoiceItemCharges.objects.filter(invoice_sale_item_id=item)
            other_metal = ErpInvoiceOtherMetal.objects.filter(invoice_sale_item_id=item)
            sales_return = ErpInvoiceSalesReturn.objects.filter(invoice_sale_item_id=item)
            export_sql(save_dir,stn,ErpInvoiceStoneDetails)
            export_sql(save_dir,charges,ErpInvoiceItemCharges)
            export_sql(save_dir,other_metal,ErpInvoiceOtherMetal)
            export_sql(save_dir,sales_return,ErpInvoiceSalesReturn)
            stn.delete()
            charges.delete()
            other_metal.delete()
            sales_return.delete()
            if(item.item_type == 0 and item.tag_id):
                tag=ErpTagging.objects.get(tag_id = item.tag_id.pk)
                tag_stone =ErpTaggingStone.objects.filter(tag_id  = item.tag_id.pk)
                tag_attr =ErpTagAttribute.objects.filter(tag_id  = item.tag_id.pk)
                tag_charges =ErpTagCharges.objects.filter(tag_id  = item.tag_id.pk)
                tag_metal =ErpTagOtherMetal.objects.filter(tag_id  = item.tag_id.pk)
                tag_container_log =ErpTaggingContainerLogDetails.objects.filter(tag_id  = item.tag_id.pk)
                tag_log =ErpTaggingLogDetails.objects.filter(tag_id  = item.tag_id.pk)
                export_sql(save_dir,[tag],ErpTagging)
                export_sql(save_dir,tag_stone,ErpTaggingStone)
                export_sql(save_dir,tag_attr,ErpTagAttribute)
                export_sql(save_dir,tag_charges,ErpTagCharges)
                export_sql(save_dir,tag_metal,ErpTagOtherMetal)
                export_sql(save_dir,tag_container_log,ErpTaggingContainerLogDetails)
                export_sql(save_dir,tag_log,ErpTaggingLogDetails)
                tag_stone.delete()
                tag_attr.delete()
                tag_charges.delete()
                tag_metal.delete()
                tag_log.delete()
                tag_container_log.delete()
                tag.delete()




        for item in purchase_details:
            export_sql(save_dir,[item],ErpInvoiceOldMetalDetails)
            stn = ErpInvoiceStoneDetails.objects.filter(invoice_old_metal_item_id=item)
            export_sql(save_dir,stn,ErpInvoiceStoneDetails)
            stn.delete()

        purchase_details.delete()
        sales_details.delete()
        delivery_details.delete()
        inv.delete()

class ErpInvoiceConvertsToNumberOneAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpInvoice.objects.all()
    serializer_class = ErpInvoiceSerializer
    
    def post(self, request, *args, **kwargs):
        erp_invoice_ids = request.data.get('erp_invoice_ids')
        save_dir = os.path.join(settings.MEDIA_ROOT, f'sql_export')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
        filename = f"db_{timestamp}.sql"
        save_dir = os.path.join(save_dir, filename)
        delete_bill =  []
        if (not erp_invoice_ids):
            return Response({"error": "Invoice Id Is Missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                for erp_invoice_id in erp_invoice_ids:
                    inv = ErpInvoice.objects.get(erp_invoice_id=erp_invoice_id)
                    paymentMode=ErpInvoicePaymentModeDetail.objects.filter(invoice_bill_id =erp_invoice_id).exclude(payment_mode = 1)
                    if paymentMode:
                        delete_bill.append(erp_invoice_id)
                        instance = ErpInvoiceCreateAPIView()
                        serializer = ErpInvoiceSerializer(inv)
                        payment_mode_details = ErpInvoicePaymentModeDetailSerializer(paymentMode,many=True).data
                        print(payment_mode_details)
                        sales_instance = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id = erp_invoice_id).first()
                        sales_details = ErpInvoiceSalesDetailsSerializer(sales_instance).data
                        if(sales_details):
                            invoice_data = serializer.data
                            #CREATE INVOICE 
                            invoice_type = inv.invoice_type
                            sales_invoice_no = None
                            purchase_invoice_no = None
                            return_invoice_no = None
                            net_amount = 0
                            fin_id = inv.fin_year.fin_id
                            metal = inv.metal.pk if inv.metal else None
                            sales_invoice_no = instance.generate_ref_no(inv.id_branch.pk,fin_id,1,1,metal)
                            for item in paymentMode:
                                net_amount += float(item.payment_amount)
                            invoice_data.update({
                                "sales_invoice_no":sales_invoice_no,
                                "setting_bill_type":1,
                                "return_invoice_no":None,
                                "purchase_invoice_no":None,
                                "due_amount":0,
                                "due_date":None,
                                "credit_status":0,
                                "is_credit":0,
                                "sales_amount":net_amount,
                                "purchase_amount":0,
                                "net_amount":net_amount,
                                "total_discount_amount":0,
                                "received_amount":net_amount,
                                "return_amount":0,
                                "round_off":0,
                            })
                            inv_serializer = ErpInvoiceSerializer(data = invoice_data,context={"invoice_no":True})
                            if inv_serializer.is_valid(raise_exception=True):
                                inv_serializer.save()
                                erp_invoice_id = inv_serializer.data['erp_invoice_id']
                            for item in payment_mode_details:
                                item.update({
                                "invoice_bill_id":erp_invoice_id
                                })
                            gross_wt = format_wt(float(net_amount)/float(sales_instance.rate_per_gram))
                            base_price =float(net_amount) /(1+(float(sales_instance.tax_percentage)/100))
                            tax_amount = format(float(net_amount) - float(base_price),'.2f')
                            gst_cost=format((float(tax_amount) / float(2)),'.2f')
                            
                            print(gst_cost)
                            
                            sales_details.update({
                                "invoice_bill_id":erp_invoice_id,
                                "tag_id" : None,
                                "pieces": 1,
                                "gross_wt":gross_wt,
                                "net_wt":gross_wt,
                                "less_wt":0,
                                "dia_wt":0,
                                "stone_wt":0,
                                "other_metal_wt":0,
                                "wastage_percentage":0,
                                "wastage_weight":0,
                                "other_metal_wt":0,
                                "total_mc_value":0,
                                "mc_value":0,
                                "other_charges_amount":0,
                                "other_metal_amount":0,
                                "tax_type":1,
                                "tax_amount":tax_amount,
                                "igst_cost":0,
                                "sgst_cost":gst_cost,
                                "cgst_cost":gst_cost,
                                "wastage_percentage_after_disc":0,
                                "mc_discount_amount":0,
                                "wastage_discount":0,
                                "discount_amount":0,
                                "taxable_amount":format(base_price,'.2f'),
                                "item_cost":net_amount,
                                "stone_details":[]
                            })
                            print(sales_details)
                            inv_detail_serializer = ErpInvoiceSalesDetailsSerializer(data=sales_details)
                            if(inv_detail_serializer.is_valid(raise_exception=True)):
                                inv_detail_serializer.save()
                                for payment in payment_mode_details:
                                    payment_mode_details_serializer = ErpInvoicePaymentModeDetailSerializer(data=payment)  
                                    if(payment_mode_details_serializer.is_valid(raise_exception=True)):
                                        payment_mode_details_serializer.save()
                    else:
                        instance = ErpInvoiceCreateAPIView()
                        #CREATE INVOICE 
                        invoice_type = inv.invoice_type
                        sales_invoice_no = None
                        purchase_invoice_no = None
                        return_invoice_no = None
                        fin_id = inv.fin_year.fin_id
                        metal = inv.metal.pk if inv.metal else None
                        if(inv.sales_invoice_no):
                            sales_invoice_no = instance.generate_ref_no(inv.id_branch.pk,fin_id,1,1,metal)
                        if(inv.purchase_invoice_no):
                            purchase_invoice_no = instance.generate_ref_no(inv.id_branch.pk,fin_id,2,1,metal)
                        if(inv.return_invoice_no):
                            return_invoice_no = instance.generate_ref_no(inv.id_branch.pk,fin_id,3,1,metal)

                        inv.sales_invoice_no = sales_invoice_no
                        inv.return_invoice_no = return_invoice_no
                        inv.purchase_invoice_no = purchase_invoice_no
                        inv.setting_bill_type = 1
                        inv.is_converted_bill = 1
                        inv.save()

                if delete_bill:
                    delete_bills(delete_bill,save_dir)


                return Response({"message":"Data Retived Successfully."}, status=status.HTTP_200_OK)


        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)
        
def export_sql(file_name,model_data,model):
    table_name = model._meta.db_table
    fields = [field.column for field in model._meta.fields]
    with open(file_name, "a") as f:
        for obj in model_data:
            values = []
            for field in fields:
                value = getattr(obj, field)
                if isinstance(value, str):
                    value = f"""'{value.replace("'", "''")}'"""  # Escape single quotes
                elif isinstance(value, datetime) or isinstance(value, date):
                    value = f"'{value}'"
                elif value is None:
                    value = "NULL"
                values.append(str(value))
            sql_insert = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({', '.join(values)});\n"
            # print(sql_insert)
            f.write(sql_insert)


class ErpInvoiceDeleteListAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_branch = request.data.get('branch')
        filter_type = request.data.get('filter_type')
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        report_col = copy.deepcopy(BILLWISE_TRANSACTION_REPORT)
        queryset = ErpDayClosed.objects.get(id_branch=id_branch)
        
        if queryset.is_day_closed == 0:
            return Response({"message": "Please Day close and Try it"}, status=status.HTTP_400_BAD_REQUEST)
        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            sql = F"""
                    select e.erp_invoice_id,c.firstname as customer_name,c.mobile,c.id_customer,
                    coalesce(csh.payment_amount,0) as csh_payment,coalesce(card.payment_amount,0) as card_payment,
                    coalesce(upi.payment_amount,0) as upi_payment,coalesce(net_banking.payment_amount,0) as net_banking_payment,
                    coalesce(sch.closing_amount,0) as chit_closing_amount,e.received_amount
                    from erp_invoice e 
                    left join customers c on c.id_customer = e.id_customer_id
                    left join(select p.invoice_bill_id_id,coalesce(sum(p.payment_amount),0) as payment_amount
                    from erp_invoice_payment_details p 
                    left join paymentmode m on m.id_mode = p.payment_mode_id
                    where p.payment_mode_id = 1
                    group by p.invoice_bill_id_id) as csh on csh.invoice_bill_id_id = e.erp_invoice_id

                    left join(select p.invoice_bill_id_id,coalesce(sum(p.payment_amount),0) as payment_amount
                    from erp_invoice_payment_details p 
                    left join paymentmode m on m.id_mode = p.payment_mode_id
                    where p.payment_mode_id = 2
                    group by p.invoice_bill_id_id) as card on card.invoice_bill_id_id = e.erp_invoice_id

                    left join(select p.invoice_bill_id_id,coalesce(sum(p.payment_amount),0) as payment_amount
                    from erp_invoice_payment_details p 
                    left join paymentmode m on m.id_mode = p.payment_mode_id
                    where p.payment_mode_id = 3
                    group by p.invoice_bill_id_id) as upi on upi.invoice_bill_id_id = e.erp_invoice_id

                    left join(select p.invoice_bill_id_id,coalesce(sum(p.payment_amount),0) as payment_amount
                    from erp_invoice_payment_details p 
                    left join paymentmode m on m.id_mode = p.payment_mode_id
                    where p.payment_mode_id = 3
                    group by p.invoice_bill_id_id) as net_banking on net_banking.invoice_bill_id_id = e.erp_invoice_id

                    left join (select chit.invoice_bill_id_id,coalesce(sum(chit.closing_amount),0) as closing_amount
                    from erp_invoice_scheme_adjusted_details chit
                    group by chit.invoice_bill_id_id) as sch on sch.invoice_bill_id_id = e.erp_invoice_id

                    where (e.invoice_date) between '{from_date}' and '{to_date}' and e.invoice_status = 1 and e.setting_bill_type = 0
                    
                    having chit_closing_amount = 0

            """
            response_data = generate_query_result(sql)
            result = []
            for item in response_data:
                invoice_details = ErpInvoice.objects.get(erp_invoice_id=item['erp_invoice_id'])
                serializer = ErpInvoiceSerializer(invoice_details)
                inv_data = get_invoice_no(serializer.data)
                item.update({
                    "invoice_no":inv_data['invoice_no'],
                    "pk_id":item['erp_invoice_id'],
                    "status_color": 'success' if (serializer.data['invoice_status']==1) else 'danger',
                    "invoice_date":format_date(serializer.data['invoice_date']),
                    'status': 'Success' if (serializer.data['invoice_status']==1) else 'Cancel','invoice_status_name': 'Success' if (serializer.data['invoice_status']==1) else 'Cancel',
                    })
                if int(filter_type)==1:
                    if (float(item['received_amount']) == 0 or (float(item['csh_payment']) > 0 and (float(item['card_payment']) == 0 and float(item['upi_payment']) == 0 and float(item['net_banking_payment']) == 0))):
                        output = {**item}
                        if output not in result:
                            result.append(output)
                if int(filter_type)==2:
                    if float(item['received_amount']) > 0 and (float(item['csh_payment']) > 0 or float(item['card_payment']) > 0 or float(item['upi_payment']) > 0 or float(item['net_banking_payment']) > 0):
                        output = {**item}
                        if output not in result:
                            result.append(output)
            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':report_col,
                'actions':ACTION_LIST,
                'is_filter_req':True,
                'filters':filters_copy,
                'rows':result,
                }
            
            return Response(context, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class ErpIssueRecieptDeleteListAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        id_branch = [request.data.get('branch')]
        cashGreaterThan = request.data.get('cashGreaterThan',None)
        issue_type = request.data.get('issue_type',None)
        receipt_type = request.data.get('receipt_type',None)
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        report_col = copy.deepcopy(ISSUERECIEPTWISE_TRANSACTION_REPORT)

        if not from_date or not to_date:
            return Response({"message": "From date and To date is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpIssueReceipt.objects.filter(bill_status = 1,setting_bill_type = 0)

            if(id_branch):
                queryset  = queryset.filter(branch__in = id_branch)
                
            if(issue_type):
                queryset  = queryset.filter(issue_type = issue_type)

            if(receipt_type):
                queryset  = queryset.filter(receipt_type = receipt_type)

            if not (receipt_type and issue_type):
                queryset  = queryset.filter(Q(receipt_type = 6) | Q(issue_type__in = [3,5]))

            if from_date and to_date:
                queryset = queryset.filter(bill_date__range=[from_date, to_date])

            data = ErpIssueReceiptSerializer(queryset,many=True).data

            payment_modes = PaymentMode.objects.filter(is_active=True).values('id_mode', 'mode_name', 'short_code')

            for mode in payment_modes:
                report_col.append({'accessor': mode["short_code"], 'Header': mode["mode_name"],'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True})
            report_col.append({'accessor': 'amount', 'Header': 'Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},)

            
            response_data = []

            for item, instance in zip(data, queryset):
                paymentmodewise = {}
                inv_payment_queryset = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt= item["id"]).values('payment_mode').annotate(
                    total_amount=Sum(
                        Case(
                            When(type=1, then=F('payment_amount')),
                            default=-F('payment_amount'),
                        )
                    ),
                    payment_type=F('type'),
                    mode_name=F('payment_mode__short_code'),
                    mode=F('payment_mode')
                )
                cash = inv_payment_queryset.filter(payment_mode = 1)

                if(cashGreaterThan):

                    if (cash and float(cash.get()['total_amount']) < float(cashGreaterThan)):
                        cash = cash
                    else:
                        continue
                inv_payment_data = list(inv_payment_queryset)

                for pay in inv_payment_data:
                    paymentmodewise.update({
                      pay["mode_name"] :pay["total_amount"] 
                    })

                # deposit_data  = instance.deposit_bill.first()

                # if(deposit_data):
                #     deposit_amt = deposit_data.amount
                

                response_data.append({
                    **item,
                    'isChecked':True,
                    "emp_name" : instance.created_by.employee.firstname,
                    "invoice_no" : item['bill_no'],
                    **paymentmodewise
                })

            filters_copy = FILTERS.copy()
            filters_copy['isDateFilterReq'] = True
            filters_copy['isBranchFilterReq'] = True
            filters_copy['isSchemeFilterReq'] = False
            context={
                'columns':report_col,
                'actions':ACTION_LIST,
                'is_filter_req':True,
                'filters':filters_copy,
                'rows':response_data,
                }
            
            return Response(context, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({"error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
class ErpIssueRecieptDeleteAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        erp_receipt_ids = request.data.get('erp_receipt_ids')
        if (not erp_receipt_ids):
            return Response({"error": "Receipt Id Is Missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                save_dir = os.path.join(settings.MEDIA_ROOT, f'sql_export')
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                now = datetime.now()
                timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
                filename = f"db_{timestamp}.sql"
                save_dir = os.path.join(save_dir, filename)
                for erp_receipt_id in erp_receipt_ids:
                    issue_rec = ErpIssueReceipt.objects.get(id=erp_receipt_id)
                    export_sql(save_dir,[issue_rec],ErpIssueReceipt)
                    
                    issue_rec_payment_details = ErpIssueReceiptPaymentDetails.objects.filter(issue_receipt=issue_rec)
                    issue_rec_cred_collec_issue = ErpReceiptCreditCollection.objects.filter(issue=issue_rec)
                    issue_rec_cred_collec_rec = ErpReceiptCreditCollection.objects.filter(receipt=issue_rec)
                    issue_rec_refund_rec = ErpReceiptRefund.objects.filter(receipt=issue_rec)
                    issue_rec_refund_issue = ErpReceiptRefund.objects.filter(issue=issue_rec)
                    issue_rec_adj = ErpReceiptAdvanceAdj.objects.filter(receipt=issue_rec)
                    
                    export_sql(save_dir,issue_rec_payment_details,ErpIssueReceiptPaymentDetails)
                    export_sql(save_dir,issue_rec_cred_collec_issue,ErpReceiptCreditCollection)
                    export_sql(save_dir,issue_rec_cred_collec_rec,ErpReceiptCreditCollection)
                    export_sql(save_dir,issue_rec_refund_rec,ErpReceiptRefund)
                    export_sql(save_dir,issue_rec_refund_issue,ErpReceiptRefund)
                    export_sql(save_dir,issue_rec_adj,ErpReceiptAdvanceAdj)
                    
                    issue_rec_payment_details.delete()
                    issue_rec_cred_collec_issue.delete()
                    issue_rec_cred_collec_rec.delete()
                    issue_rec_refund_rec.delete()
                    issue_rec_refund_issue.delete()
                    issue_rec_adj.delete()
                    issue_rec.delete()

                return Response({"message":"Data deleted Successfully."}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)      
        except Exception as e:
            tb = traceback.format_exc()
            return Response({"error": F"Error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)  
        
class ErpDeleteTransactionsAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        transaction_type = int(request.data.get('transaction_type',0))
        try:
            save_dir = os.path.join(settings.MEDIA_ROOT, f'sql_export')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            now = datetime.now()
            timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
            filename = f"db_{timestamp}.sql"
            save_dir = os.path.join(save_dir, filename)
            with transaction.atomic():
                if transaction_type == 1:
                    erp_invoice_ids = list(ErpInvoice.objects.values_list('pk', flat=True))
                    if (not erp_invoice_ids):
                        return Response({"error": "Invoice Details Is Missing"}, status=status.HTTP_400_BAD_REQUEST)
                    delete_bills(erp_invoice_ids,save_dir)
                    with connection.cursor() as cursor:
                        cursor.execute("ALTER TABLE erp_invoice AUTO_INCREMENT = 1;")
                    return Response({"message":"Data Deleted Successfully."}, status=status.HTTP_200_OK)
                elif transaction_type == 2:
                    issue_receipt_queryset = ErpIssueReceipt.objects.exclude(issue_type=1)
                    export_sql(save_dir,issue_receipt_queryset,ErpIssueReceipt)
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM erp_issue_receipt WHERE issue_type != 1 ")
                    return Response({"message":"Data Deleted Successfully."}, status=status.HTTP_200_OK)

                    
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"error": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)      
        except Exception as e:
            tb = traceback.format_exc()
            return Response({"error": F"Error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)

class ErpInvoiceSearchAPIView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpInvoice.objects.all()
    serializer_class = ErpInvoiceSerializer
    
    def post(self, request, *args, **kwargs):
        invoice_type = int(request.data.get('invoice_type'))
        invoice_no = request.data.get('invoice_no')
        fin_year = request.data.get('fin_year')
        id_branch = request.data.get('id_branch')
        id_metal = request.data.get('id_metal')
        entry_date = request.data.get('entry_date')
        if (not invoice_type or not invoice_no or not fin_year or not id_branch ):
            return Response({"error": "Filter Data Is Missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = ErpInvoice.objects.filter(id_branch = id_branch,fin_year= fin_year,invoice_date = entry_date)
            ref_no = invoice_no[-5:]
            if invoice_type == 1 or  invoice_type == 4 or invoice_type == 5 or invoice_type == 6:
                queryset = queryset.filter(sales_invoice_no = ref_no,metal = id_metal).get()
            elif invoice_type == 2:
                queryset = queryset.filter(invoice_type=invoice_type,purchase_invoice_no = ref_no).get()
            elif invoice_type == 3 or invoice_type == 7:
                queryset = queryset.filter(invoice_type=3,return_invoice_no = ref_no).get()
            inv_serializer = ErpInvoiceSerializer(queryset)
            data = inv_serializer.data
            round_offed_sales_amount = round(float(data['sales_amount']))
            inv_data = get_invoice_no(data)
            data.update({"sales_amount":round_offed_sales_amount,"pk_id":data['erp_invoice_id'], "sno":1,"invoice_no":inv_data['invoice_no'],'status_color': 'success' if (data['invoice_status']==1) else 'danger',"invoice_date":format_date(data['invoice_date']),'status': 'Success' if (data['invoice_status']==1) else 'Cancel','invoice_status_name': 'Success' if (data['invoice_status']==1) else 'Cancel','is_cancelable': True if (data['invoice_status']==1) else False})
            return Response([data], status=status.HTTP_200_OK) 
        except ErpInvoice.DoesNotExist:
            return Response({"message": "Invoice not found."}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            tb = traceback.format_exc()
            return Response({"message": F"A database error occurred.  {e}",'traceback':tb}, status=status.HTTP_400_BAD_REQUEST)       
class ErpLiablityEntryListCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def generate_ref_no(self,id_branch,fin_id):
        code =''
        last_entry=ErpLiablityEntry.objects.filter(branch=id_branch,fin_year=fin_id)
        last_entry = last_entry.order_by('-id').first()
        if last_entry:
            code= int(last_entry.bill_no)
            code = str(code + 1).zfill(5)
        else:
           code = '00001'
        return code
    
    
    def get(self, request, *args, **kwargs):
        queryset = ErpLiablityEntry.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None, LIABLITY_ENTRY_COLUMNS)
        columns = get_reports_columns_template(request.user.pk,LIABLITY_ENTRY_COLUMNS,request.query_params.get("path_name",''))
        serializer = ErpLiablityEntrySerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {"pk_id": data['id'], "sno": index+1, "entry_date":format_date(data['entry_date'])})
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        context = {
            'columns': columns,
            'actions': LIABLITY_ENTRY_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)
    
    
    def post(self, request, *args, **kwargs):
        fy = FinancialYear.objects.get(fin_status=True)
        bill_no = self.generate_ref_no(request.data['branch'], fy.pk)
        request.data.update({'fin_year':fy.pk, 'bill_no':bill_no, 'entry_date':date.today()})
        serializer = ErpLiablityEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        print_class = ErpLiablityEntryPrintView()
        print_data = print_class.generate_print(serializer.data['id'])
        return Response({'data':serializer.data, 'print_data':print_data}, status=status.HTTP_201_CREATED)
    
class ErpLiablityEntryPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpLiablityEntry.objects.all()
    serializer_class = ErpLiablityEntrySerializer
    
    def generate_print(self, id):
        company = Company.objects.latest("id_company")
        liablity_obj = ErpLiablityEntry.objects.get(id=id)
        output = {
            'company': company.company_name,
            'supplier_name': liablity_obj.supplier.supplier_name,
            'mobile': liablity_obj.supplier.mobile_no,
            'branch': liablity_obj.branch.name,
            'bill_no': liablity_obj.bill_no,
            'amount': liablity_obj.amount,
            'ref_bill_no': liablity_obj.ref_bill_no if(liablity_obj.ref_bill_no != None) else None,
            'remarks': liablity_obj.remarks if(liablity_obj.remarks != None) else None,
            'entry_date':format_date(liablity_obj.entry_date),
        }
        return output
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        print_data = self.generate_print(queryset.id)
        return Response({'response_data':print_data}, status=status.HTTP_200_OK)
    
class ErpLiablityEntryPayableListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        id_supplier = request.query_params.get('id_supplier')
        # bill_setting_type = request.query_params.get('bill_setting_type')
        
        if(not id_supplier):
            return Response({"error": "Supplier id is missing...."}, status=status.HTTP_400_BAD_REQUEST)
        
        output = []
        queryset = ErpLiablityEntry.objects.filter(
            supplier=id_supplier,
            paid_amount__lt=F('amount')
        )
        serializer = ErpLiablityEntrySerializer(queryset, many=True)
        for data in serializer.data:
            paid_amount = Decimal(data.get('paid_amount', 0))
            total_amount = Decimal(data.get('amount', 0))
            balance_amount = total_amount - paid_amount

            data.update({
                "isChecked": False,
                "date": format_date(data['entry_date']),
                "balance_amount": balance_amount
            })
            if data not in output:
                output.append(data)
        return Response(output, status=status.HTTP_200_OK)
    
class ErpLiablityPaymentListCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def generate_receipt_no(self,id_supplier,fin_id):
        code =''
        last_entry=ErpLiablityEntryPament.objects.filter(supplier=id_supplier,fin_year=fin_id)
        last_entry = last_entry.order_by('-id').first()
        if last_entry:
            code= int(last_entry.receipt_no)
            code = str(code + 1).zfill(5)
        else:
           code = '00001'
        return code
    
    def get(self, request, *args, **kwargs):
        queryset = ErpLiablityEntryPament.objects.all()
        paginator, page = pagination.paginate_queryset(queryset, request,None, LIABLITY_PAYMENT_ENTRY_COLUMNS)
        columns = get_reports_columns_template(request.user.pk,LIABLITY_PAYMENT_ENTRY_COLUMNS,request.query_params.get("path_name",''))
        serializer = ErpLiablityEntryPamentSerializer(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {"pk_id": data['id'], "sno": index+1, "payment_date":format_date(data['payment_date'])})
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        context = {
            'columns': columns,
            'actions': LIABLITY_PAYMENT_ENTRY_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            fy = FinancialYear.objects.get(fin_status=True)
            payment_details = request.data['payment_details']
            payment_mode_details = request.data['payment_mode_details']
            del request.data['payment_mode_details']
            del request.data['payment_details']
            receipt_no = self.generate_receipt_no(request.data['id_supplier'], fy.pk)
            request.data.update({
                "supplier":request.data['id_supplier'],
                "payment_amount":request.data['paid_amount'],
                "receipt_no":receipt_no,
                "payment_date":date.today(),
                "fin_year":fy.pk,
                "remarks": request.data['remarks'] if('remarks' in request.data) else None,
            })
            serializer = ErpLiablityEntryPamentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            for payment_data in payment_details:
                payment_data.update({
                    "liablity_entry_payment":serializer.data['id'],
                    "liablity_entry":payment_data['ref_id'],
                    "payment_amount":payment_data['paid_amount'],
                    "payment_date":date.today(),
                    "remarks": request.data['remarks'] if('remarks' in request.data) else None
                    })
                payment_serializer = ErpLiablityPaymentEntryDetailsSerializer(data=payment_data)
                payment_serializer.is_valid(raise_exception=True)
                payment_serializer.save()
                liablity_obj = ErpLiablityEntry.objects.get(id=payment_data['ref_id'])
                liablity_paid_amount = Decimal(liablity_obj.paid_amount)
                calc_liablity_paid_amount = liablity_paid_amount + Decimal(payment_data['paid_amount'])
                liablity_obj.paid_amount = calc_liablity_paid_amount
                liablity_obj.save()
            for payment_mode_data in payment_mode_details:
                payment_mode_data.update({
                    "liablity_payment":serializer.data['id']
                })
                payment_mode_serializer = ErpLiablityPaymentModeDetailsSerializer(data=payment_mode_data)
                payment_mode_serializer.is_valid(raise_exception=True)
                payment_mode_serializer.save()
            print_class = ErpLiablityPaymentPrintView()
            print_data = print_class.generate_print(serializer.data['id'])
            return Response({'data':serializer.data, 'print_data':print_data}, status=status.HTTP_201_CREATED)
        

class ErpLiablityPaymentPrintView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = ErpLiablityEntryPament.objects.all()
    serializer_class = ErpLiablityEntryPamentSerializer
    
    def generate_print(self, id):
        company = Company.objects.latest("id_company")
        payment_details = []
        liablity_payment_obj = ErpLiablityEntryPament.objects.get(id=id)
        liablity_payment_details_query = ErpLiablityPaymentEntryDetails.objects.filter(liablity_entry_payment=liablity_payment_obj.pk)
        liablity_payment_details_serializer = ErpLiablityPaymentEntryDetailsSerializer(liablity_payment_details_query, many=True)
        total_balance_amount = Decimal(0.00)
        total_entry_amount = Decimal(0.00)
        for data in liablity_payment_details_serializer.data:
            instance = {}
            liablity_entry_obj = ErpLiablityEntry.objects.get(id=data['liablity_entry'])
            paid_amount = Decimal(liablity_entry_obj.paid_amount)
            total_amount = Decimal(liablity_entry_obj.amount)
            balance_amount = total_amount - paid_amount
            total_balance_amount += balance_amount
            total_entry_amount += total_amount
            instance.update({
                "remarks":data['remarks'],
                "payment_amount":data['payment_amount'],
                "bill_no":liablity_entry_obj.bill_no,
                "amount":liablity_entry_obj.amount,
                "balance_amount":balance_amount,
            })
            if instance not in payment_details:
                payment_details.append(instance)
        output = {
            'company': company.company_name,
            'supplier_name': liablity_payment_obj.supplier.supplier_name,
            'mobile': liablity_payment_obj.supplier.mobile_no,
            'receipt_no': liablity_payment_obj.receipt_no,
            'payment_amount': liablity_payment_obj.payment_amount,
            'remarks': liablity_payment_obj.remarks if(liablity_payment_obj.remarks != None) else None,
            'payment_date':format_date(liablity_payment_obj.payment_date),
            'payment_details': payment_details,
            "balance_amount":balance_amount,
            "entry_amount":total_entry_amount,
        }
        return output
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        print_data = self.generate_print(queryset.id)
        return Response({'response_data':print_data}, status=status.HTTP_200_OK)

class ErpInvoiceSqlListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def post(self, request, *args, **kwargs):
        from_date = request.data['fromDate']
        to_date = request.data['toDate']
        id_branch = request.data['branch']
        id_metal = request.data['id_metal']
        status = request.data.get('bill_status')
        bill_type = request.data.get('bill_type')
        bill_setting_type = 1
        if "bill_setting_type" in request.data:
            bill_setting_type =  request.data['bill_setting_type']
        id_branch = (id_branch) if id_branch != '' else 1
        filter_data = ''
        if from_date and to_date:
            filter_data += f' and i.invoice_date BETWEEN "{from_date}" AND "{to_date}" '
        if isinstance(id_branch, list):
            branch_ids = ', '.join(str(b) for b in id_branch)
            filter_data += f' and i.id_branch_id  in ({branch_ids})'
        else:
            filter_data += f' and i.id_branch_id =  {id_branch} '
        if id_metal:
            filter_data += f' and i.metal_id =  {id_metal} '
        if status:
            filter_data += f' and i.invoice_status =  {status} '
        if bill_type:
             filter_data += f' and i.invoice_type =  {bill_type} '

        filter_data += f' and i.setting_bill_type =  {bill_setting_type} '
        page = int(request.data.get("page", 1))
        records_per_page = int(request.data.get("records", 50))  # default to 50 if not passed

        count_sql = f"""
                SELECT   COUNT(*) as total FROM erp_invoice i
                Where 1
                {filter_data}
                """
        print(count_sql)
        count_result = generate_query_result(count_sql)
        total_records = count_result[0]['total']
        total_pages = (total_records + records_per_page - 1) // records_per_page 
        if total_pages < page:
           page = 1
        offset = (page - 1) * records_per_page
        sql = f"""
                SELECT  i.*,i.fin_year_id as fin_year,b.name as branch_name,i.id_branch_id as id_branch,i.metal_id as metal,COALESCE(SUM(sa.net_wt),0) as sale_wt
                FROM erp_invoice i
                LEFT JOIN branch b ON b.id_branch = i.id_branch_id
                LEFT JOIN erp_invoice_sales_details sa ON sa.invoice_bill_id_id = i.erp_invoice_id
                Where 1
                {filter_data}
                GROUP BY i.erp_invoice_id
                ORDER BY i.erp_invoice_id DESC
                LIMIT {records_per_page} OFFSET {offset}
                """
        result = generate_query_result(sql)
        columns = get_reports_columns_template(request.user.pk,INVOICE_COLUMN_LIST,request.data.get('path_name',''))
        responce_data = []
        for index, data in enumerate(result):
            round_offed_sales_amount = round(float(data['sales_amount']))
            inv_data = get_invoice_no(data)
            created_on = data['created_on']
            if created_on.tzinfo is None:
                created_on = created_on.replace(tzinfo=pytz.utc)
            time = localtime(created_on).strftime('%I:%M %p')
            invoice_date = format_date(data['invoice_date'])
            datetime_str = f"{invoice_date} {time}"
            responce_data.append({"sales_amount":round_offed_sales_amount,
                         "pk_id":data['erp_invoice_id'], 
                         "sno":index+1,
                         "invoice_no":inv_data['invoice_no'],
                         'status_color': 'success' if (data['invoice_status']==1) else 'danger',
                         "invoice_date":datetime_str,
                         'status': 'Success' if (data['invoice_status']==1) else 'Cancel',
                         'invoice_status_name': 'Success' if (data['invoice_status']==1) else 'Cancel',
                         'is_cancelable': True if (data['invoice_status']==1) else False,
                         "sale_wt": data['sale_wt'],
                         "branch_name": data['branch_name'],
                         "customer_name": data['customer_name'],
                         "customer_mobile": data['customer_mobile'],
                         "purchase_amount": data['purchase_amount'],
                         "net_amount": data['net_amount'],
                         "received_amount": data['received_amount'],
                         "sale_wt": data['sale_wt'],
                         "erp_invoice_id":data['erp_invoice_id'], 
                         })
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        filters_copy['isBranchFilterReq'] = True
        filters_copy['isSchemeFilterReq'] = False
        filters_copy['isMetalFilterReq'] = True
        filters_copy['isBillStatusFilterReq'] = True
        filters_copy['isBillTypeFilterReq'] = True

        context={
            'columns':columns,
            'actions':ACTION_LIST,
            'page_count':total_records,
            'total_pages': total_pages,
            'current_page': page,
            'is_filter_req':True,
            'filters':filters_copy
            }
        return pagination.paginated_response(responce_data,context)
    
class ErpCustomerSalesLogDetails(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    queryset = ErpCustomerSalesLog.objects.all().order_by('-id')
    serializer_class = ErpCustomerSalesLogSerializer

    def post(self, request):
        if 'active' in request.query_params:
            queryset = ErpCustomerSalesLog.objects.all()
            serializer = ErpCustomerSalesLogSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = self.get_queryset()
        paginator, page = pagination.paginate_queryset(queryset, request, None, ERP_CUSTOMER_SALES_LOG_COLUMNS)
        serializer = self.get_serializer(page, many=True)
        enhanced_data = []
        for index, data in enumerate(serializer.data):
            data.update({
                "pk_id": data.get("id", data.get("id")),
                "sno": index + 1,
                "section_name": data.get("section_name", "")
            })
            enhanced_data.append(data)
        filters_copy = FILTERS.copy()
        print("enhanced_data",enhanced_data)
        context = {
            "columns": ERP_CUSTOMER_SALES_LOG_COLUMNS,
            "actions": ERP_CUSTOMER_SALES_LOG_ACTION_LIST,
            "page_count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "is_filter_req": False,
            "filters": filters_copy,
        }
        
        return pagination.paginated_response(enhanced_data, context)

    
