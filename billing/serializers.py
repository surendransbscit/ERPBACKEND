from rest_framework import serializers
from django.utils.timezone import localtime
from .models import (
    ErpInvoice, BankSettlements,
    ErpInvoiceSalesDetails,
    ErpInvoiceOldMetalDetails,
    ErpInvoiceSalesReturn,
    ErpInvoiceStoneDetails,
    ErpInvoiceItemCharges,
    ErpInvoicePaymentModeDetail,
    ErpInvoiceSchemeAdjusted,
    ErpInvoiceCustomerAddress,
    ErpInvoiceOtherMetal,
    ErpIssueReceipt,
    ErpIssueReceiptPaymentDetails,
    ErpAdvanceAdj, ErpLiablityEntry, ErpLiablityEntryPament, ErpLiablityPaymentModeDetails, ErpLiablityPaymentEntryDetails,
    ErpReceiptCreditCollection,Branch,Metal,FinancialYear,ErpReceiptAdvanceAdj,ErpReceiptRefund,ErpCustomerSalesLog,
    ErpInvoiceDiscount,ErpInvoiceDiscountSalesDetails,ErpInvoiceDiscountOldMetalDetails,ErpInvoiceDiscountStoneDetails,ErpInvoiceDiscountOtherMetal,
    ErpInvoiceDiscountPaymentModeDetail,ErpInvoiceDiscountItemCharges, ErpItemDelivered, ErpItemDeliveredImages,ErpInvoiceGiftDetails
)
from inventory.serializers import validate_sale_item
from rest_framework.validators import UniqueTogetherValidator
from utilities.utils import format_date
from datetime import datetime ,timedelta

class ErpInvoiceSerializer(serializers.ModelSerializer):

    inv_no = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    created_date_time = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    class Meta:
        model = ErpInvoice
        fields = '__all__'

    def get_created_date_time(self, obj):
        return localtime(obj.created_on).strftime('%d-%m-%Y %I:%M %p')

    def get_time(self, obj):
        return localtime(obj.created_on).strftime('%I:%M %p')
    
    def get_date(self, obj):
        date = obj.invoice_date
        if date is not None and date != '':
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            return date.strftime('%d-%m-%y')
        return date
        
    def get_fields(self):
        fields = super().get_fields()
        fields['branch_name'] = serializers.CharField(source='id_branch.name', read_only=True)
        fields['counter_name'] = serializers.CharField(source='id_counter.counter_name', read_only=True)
        fields['created_by_emp'] = serializers.CharField(source='created_by.employee.firstname', read_only=True)
        fields['canceled_by_emp'] = serializers.CharField(source='canceled_by.employee.firstname', read_only=True)
        return fields
    
    def get_inv_no(self, obj):
        if self.context.get('invoice_no', False):
            inv_data = {
                'invoice_type': obj.invoice_type,
                'id_branch': obj.id_branch.id_branch,
                'fin_year': obj.fin_year.fin_id,
                'sales_invoice_no': obj.sales_invoice_no,
                'purchase_invoice_no': obj.purchase_invoice_no,
                'return_invoice_no': obj.return_invoice_no,
                'metal': obj.metal.id_metal if obj.metal else None,

            }
            if self.context.get('invoice_type', False):
                inv_data['invoice_type'] = self.context.get('invoice_type')

            invoice_info = get_invoice_no(inv_data)
            return invoice_info
        return None

class ErpInvoiceSalesDetailsSerializer(serializers.ModelSerializer):
    stone_details = serializers.SerializerMethodField()
    other_metal_details = serializers.SerializerMethodField()
    tag_code = serializers.SerializerMethodField()
    class Meta:
        model = ErpInvoiceSalesDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',{})
        stone_details = data.get('stone_details', [])
        other_metal_details = data.get('other_metal_detail', [])
        super().__init__(*args, **kwargs)
        self.stone_details = stone_details
        self.other_metal_details = other_metal_details

    def get_fields(self):
        fields = super().get_fields()
        fields['old_tag_code']  = serializers.CharField(source='tag_id.old_tag_code', read_only=True)
        fields['weight_show_in_print'] = serializers.CharField(source='id_product.weight_show_in_print', read_only=True)
        fields['weight_show_in_print_purity'] = serializers.CharField(source='id_purity.weight_show_in_print_purity', read_only=True)
        fields['metal_name'] = serializers.CharField(source='id_product.id_metal.metal_name', read_only=True)
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['product_code'] = serializers.CharField(source='id_product.short_code', read_only=True)
        fields['design_name'] = serializers.CharField(source='id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='id_sub_design.sub_design_name', read_only=True)
        fields['emp_name'] = serializers.CharField(source='ref_emp_id.firstname', read_only=True)
        return fields

    def get_stone_details(self, obj):
        if self.context.get('stone_details', False):
            stone_details = ErpInvoiceStoneDetails.objects.filter(invoice_sale_item_id=obj.invoice_sale_item_id)
            return ErpInvoiceStoneDetailsSerializer(stone_details, many=True).data
        return None
    def get_tag_code(self, obj):
        if obj.tag_id and obj.tag_id.tag_code:
            if obj.tag_id.old_tag_code:
                return obj.tag_id.old_tag_code
            return obj.tag_id.tag_code
        return None
    
    def get_other_metal_details(self, obj):
        queryset = ErpInvoiceOtherMetal.objects.filter(invoice_sale_item_id=obj.invoice_sale_item_id)
        other_metal_details= ErpInvoiceOtherMetalSerializer(queryset, many=True).data
        for detail, instance in zip(other_metal_details, queryset):
            cat_name = instance.id_category.cat_name
            detail.update({
                'cat_name': cat_name
            })
        return other_metal_details
    
    def validate(self, data):
        return validate_sale_item(self,data)

class ErpInvoiceOldMetalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceOldMetalDetails
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['old_metal_type_name'] = serializers.CharField(source='item_type.name', read_only=True)
        fields['stock_type'] = serializers.CharField(source='id_product.stock_type', read_only=True)
        fields['uom_id'] = serializers.CharField(source='id_product.uom_id.uom_id', read_only=True)
        fields['rate_deduction'] = serializers.CharField(source = 'item_type.rate_deduction',read_only=True)
        return fields

class ErpInvoiceSalesReturnSerializer(serializers.ModelSerializer):
    invoice_sale_item_details = ErpInvoiceSalesDetailsSerializer(source='invoice_sale_item_id', read_only=True)
    class Meta:
        model = ErpInvoiceSalesReturn
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='id_sub_design.sub_design_name', read_only=True)
        fields['tag_code'] = serializers.CharField(source='tag_id.tag_code', read_only=True)
        fields['stock_type'] = serializers.CharField(source='id_product.stock_type', read_only=True)
        fields['uom_id'] = serializers.CharField(source='id_product.uom_id.uom_id', read_only=True)
        return fields

class BankSettlementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankSettlements
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=BankSettlements.objects.all(),
                fields=(
                    'branch',
                    'invoice_date'),
                message='Bank settlement already exists')]
        
class ErpInvoiceStoneDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceStoneDetails
        fields = '__all__'
    def get_fields(self):
        fields = super().get_fields()
        fields['stone_type'] = serializers.CharField(source='id_stone.stone_type', read_only=True)
        return fields

class ErpInvoiceItemChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceItemCharges
        fields = '__all__'

class ErpInvoicePaymentModeDetailSerializer(serializers.ModelSerializer):
    pay_amt = serializers.SerializerMethodField()
    
    class Meta:
        model = ErpInvoicePaymentModeDetail
        fields = '__all__'

    def get_pay_amt(self, obj):
        if obj.payment_type == 1:
            return obj.payment_amount
        else:
            return -obj.payment_amount
        
    def get_fields(self):
        fields = super().get_fields()
        fields['mode_name'] = serializers.CharField(source='payment_mode.mode_name', read_only=True)
        fields['bank_name'] = serializers.CharField(source='id_bank.bank_name', read_only=True)
        fields['acc_number'] = serializers.CharField(source='id_bank.acc_number', read_only=True)
        return fields

class ErpInvoiceSchemeAdjustedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceSchemeAdjusted
        fields = '__all__'

class ErpInvoiceCustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceCustomerAddress
        fields = '__all__'

class ErpInvoiceOtherMetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceOtherMetal
        fields = '__all__'

class ErpItemDeliveredSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpItemDelivered
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='product.product_name', read_only=True)
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        fields['customer_name'] = serializers.CharField(source='customer.firstname', read_only=True)
        return fields
    
class ErpItemDeliveredImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpItemDeliveredImages
        fields = '__all__'
        
class ErpIssueReceiptSerializer(serializers.ModelSerializer):

    created_date_time = serializers.SerializerMethodField()
    class Meta:
        model = ErpIssueReceipt
        fields = '__all__'

    def get_created_date_time(self, obj):
        return localtime(obj.created_on).strftime('%d-%m-%Y %I:%M %p')
    
    def get_fields(self):
        fields = super().get_fields()
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        fields['employee_name'] = serializers.CharField(source='employee.firstname', read_only=True)
        fields['customer_name'] = serializers.CharField(source='customer.firstname', read_only=True)
        fields['customer_mobile'] = serializers.CharField(source='customer.mobile', read_only=True)
        fields['bank_name'] = serializers.CharField(source='id_bank.bank_name', read_only=True)
        return fields
        
class ErpIssueReceiptPaymentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpIssueReceiptPaymentDetails
        fields = '__all__'
    def get_fields(self):
        fields = super().get_fields()
        fields['mode_name'] = serializers.CharField(source='payment_mode.mode_name', read_only=True)
        fields['bank_name'] = serializers.CharField(source='bank.bank_name', read_only=True)
        fields['acc_number'] = serializers.CharField(source='bank.acc_number', read_only=True)
        return fields

class ErpReceiptCreditCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpReceiptCreditCollection
        fields = '__all__'

class ErpReceiptAdvanceAdjSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpReceiptAdvanceAdj
        fields = '__all__'

class ErpReceiptRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpReceiptRefund
        fields = '__all__'

def get_invoice_no(inv_data):

    inv_no_formatdata = [{
        "invoice_type" : 1,
        "invoice_format" : "SA-@metal_code@-@code@",
    },
    {
        "invoice_type" : 2,
        "invoice_format" : "PU-@metal_code@-@code@",
    },
    {
        "invoice_type" : 3,
        "invoice_format" : "SR-@metal_code@-@code@",
    },
    {
        "invoice_type" : 4,
        "invoice_format" : "SA-@metal_code@-@code@",
    },
    {
        "invoice_type" : 5,
        "invoice_format" : "SAR-@metal_code@-@@code@@",
    },
        {
        "invoice_type" : 6,
        "invoice_format" : "SA-@metal_code@-@code@",
    },
    ]

    invoice_type = inv_data['invoice_type']

    code = ''

    bra_code =Branch.objects.get(id_branch=inv_data['id_branch']).short_name

    fy_code = FinancialYear.objects.get(fin_id=inv_data['fin_year']).fin_year_code

    if(inv_data['metal']):

        metal_code = Metal.objects.get(id_metal=inv_data['metal']).metal_code
    
    else :

        metal_code=""


    sales_invoice_no = None
    purchase_invoice_no = None
    return_invoice_no = None
    invoice_no = None

    if(inv_data['sales_invoice_no']):
        code= inv_data['sales_invoice_no']
        filtered_data = [item for item in inv_no_formatdata if item['invoice_type'] == 1]
        invoice_format =  filtered_data[0]['invoice_format']
        sales_invoice_no = invoice_format.replace('@br_code@', bra_code).replace('@code@', code).replace('@fy_code@', fy_code).replace('@metal_code@', metal_code)
        
    if(inv_data['purchase_invoice_no']):
        code = inv_data['purchase_invoice_no']
        filtered_data = [item for item in inv_no_formatdata if item['invoice_type'] == 2]
        invoice_format =  filtered_data[0]['invoice_format']
        purchase_invoice_no = invoice_format.replace('@br_code@', bra_code).replace('@code@', code).replace('@fy_code@', fy_code).replace('@metal_code@', metal_code)

    if(inv_data['return_invoice_no']):
        code= inv_data['return_invoice_no']
        filtered_data = [item for item in inv_no_formatdata if item['invoice_type'] == 3]
        invoice_format =  filtered_data[0]['invoice_format']
        return_invoice_no = invoice_format.replace('@br_code@', bra_code).replace('@code@', code).replace('@fy_code@', fy_code).replace('@metal_code@', metal_code)

    if (invoice_type == 1 or invoice_type == 4 or invoice_type == 5 or invoice_type == 6):
        invoice_no = sales_invoice_no
    elif (invoice_type == 2):
        invoice_no = purchase_invoice_no
    elif (invoice_type == 3):
        invoice_no = return_invoice_no


    return {'invoice_no' : invoice_no,'sales_invoice_no' : sales_invoice_no,'purchase_invoice_no' : purchase_invoice_no,'return_invoice_no' : return_invoice_no}

def get_bill_no(id):
    obj = ErpInvoice.objects.filter(erp_invoice_id = id).first()
    inv_data = {
        'invoice_type': obj.invoice_type,
        'id_branch': obj.id_branch.id_branch,
        'fin_year': obj.fin_year.fin_id,
        'metal': obj.metal.id_metal if obj.metal else None,
        'sales_invoice_no': obj.sales_invoice_no,
        'purchase_invoice_no': obj.purchase_invoice_no,
        'return_invoice_no': obj.return_invoice_no
    }
    invoice_info = get_invoice_no(inv_data)
    return invoice_info['invoice_no']


class ErpInvoiceDiscountSerializer(serializers.ModelSerializer):

    inv_no = serializers.SerializerMethodField()
    class Meta:
        model = ErpInvoiceDiscount
        fields = '__all__'
        
    def get_fields(self):
        fields = super().get_fields()
        fields['branch_name'] = serializers.CharField(source='id_branch.name', read_only=True)
        return fields
    
    def get_inv_no(self, obj):
        if self.context.get('invoice_no', False):
            inv_data = {
                'invoice_type': obj.invoice_type,
                'id_branch': obj.id_branch.id_branch,
                'fin_year': obj.fin_year.fin_id,
                'metal':obj.metal.id_metal if obj.metal else None,
                'sales_invoice_no': obj.sales_invoice_no,
                'purchase_invoice_no': obj.purchase_invoice_no,
                'return_invoice_no': obj.return_invoice_no
            }
            if self.context.get('invoice_type', False):
                inv_data['invoice_type'] = self.context.get('invoice_type')

            invoice_info = get_invoice_no(inv_data)
            return invoice_info
        return None

class ErpInvoiceSalesDiscountDetailsSerializer(serializers.ModelSerializer):
    stone_details = serializers.SerializerMethodField()
    other_metal_details = serializers.SerializerMethodField()

    class Meta:
        model = ErpInvoiceDiscountSalesDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',{})
        stone_details = data.get('stone_details', [])
        other_metal_details = data.get('other_metal_detail', [])
        super().__init__(*args, **kwargs)
        self.stone_details = stone_details
        self.other_metal_details = other_metal_details

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='id_sub_design.sub_design_name', read_only=True)
        return fields

    def get_stone_details(self, obj):
        if self.context.get('stone_details', False):
            stone_details = ErpInvoiceDiscountStoneDetails.objects.filter(invoice_sale_item_id=obj.invoice_sale_item_id)
            return ErpInvoiceStoneDiscountDetailsSerializer(stone_details, many=True).data
        return None
    
    def get_other_metal_details(self, obj):
        queryset = ErpInvoiceDiscountOtherMetal.objects.filter(invoice_sale_item_id=obj.invoice_sale_item_id)
        other_metal_details= ErpInvoiceDiscountOtherMetalSerializer(queryset, many=True).data
        for detail, instance in zip(other_metal_details, queryset):
            cat_name = instance.id_category.cat_name
            detail.update({
                'cat_name': cat_name
            })
        return other_metal_details
    
    def validate(self, data):
        return validate_sale_item(self,data)

class ErpInvoiceDiscountOldMetalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceDiscountOldMetalDetails
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['stock_type'] = serializers.CharField(source='id_product.stock_type', read_only=True)
        fields['uom_id'] = serializers.CharField(source='id_product.uom_id.uom_id', read_only=True)
        return fields


class ErpInvoiceStoneDiscountDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceDiscountStoneDetails
        fields = '__all__'
    def get_fields(self):
        fields = super().get_fields()
        fields['stone_type'] = serializers.CharField(source='id_stone.stone_type', read_only=True)
        return fields

class ErpInvoiceDiscountPaymentModeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceDiscountPaymentModeDetail
        fields = '__all__'
    def get_fields(self):
        fields = super().get_fields()
        fields['mode_name'] = serializers.CharField(source='payment_mode.mode_name', read_only=True)
        return fields
class ErpInvoiceDiscountOtherMetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceDiscountOtherMetal
        fields = '__all__'

class ErpInvoiceDiscountItemChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceDiscountItemCharges
        fields = '__all__'

class ErpAdvanceAdjSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpAdvanceAdj
        fields = '__all__'

class ErpCustomerSalesLogSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='id_section.section_name', read_only=True)
    
    class Meta:
        model = ErpCustomerSalesLog
        fields = '__all__'
        
class ErpInvoiceGiftDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpInvoiceGiftDetails
        fields = '__all__'
        
class ErpLiablityEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLiablityEntry
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        fields['supplier_name'] = serializers.CharField(source='supplier.supplier_name', read_only=True)
        return fields
        
class ErpLiablityEntryPamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLiablityEntryPament
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        # fields['branch_name'] = serializers.CharField(source='supplier.branch.name', read_only=True)
        fields['supplier_name'] = serializers.CharField(source='supplier.supplier_name', read_only=True)
        return fields
        
class ErpLiablityPaymentModeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLiablityPaymentModeDetails
        fields = '__all__'
        
class ErpLiablityPaymentEntryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLiablityPaymentEntryDetails
        fields = '__all__'