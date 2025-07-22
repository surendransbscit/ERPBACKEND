from rest_framework import serializers
from .models import (ErpPurchaseEntry,ErpPurchaseEntryDetails,ErpPurchaseStoneDetails,ErpPurchaseOtherMetal,ErpPurchaseIssueReceiptOtherMetal,ErpPurchaseEntryCharges,ErpSupplierRateCutAndMetalIssue,
                     ErpPurchaseIssueReceiptStoneDetails,ErpPurchaseIssueReceipt,ErpSupplierMetalIssue,ErpSupplierRateCut,ErpCustomerRateCut,ErpAccountStockProcessDetails,ErpAccountStockProcess,
                     ErpPurchaseIssueReceiptDetails,ErpSupplierPayment,ErpSupplierPaymentModeDetail,ErpSupplierMetalIssueDetails,ErpSupplierPaymentDetails,ErpCustomerPayment,ErpCustomerPaymentDetails,ErpCustomerPaymentModeDetail,
                     ErpPurchaseReturnStoneDetails, ErpPurchaseReturnDetails, ErpPurchaseReturn,ErpSupplierAdvance,ErpSupplierAdvanceAdj,ErpPurchaseEntryChargesDetails)
from inventory.serializers import validate_sale_item
from retailsettings.models import (RetailSettings)

        
class ErpPurchaseEntrySerializer(serializers.ModelSerializer):
    ref_code = serializers.SerializerMethodField()
    
    class Meta:
        model = ErpPurchaseEntry
        fields = '__all__'

    def get_ref_code(self, obj):
        code_format = RetailSettings.objects.get(name='purchase_entry_code_format').value
        # Handling missing or None values gracefully
        branch_code = obj.id_branch.short_name if obj.id_branch and obj.id_branch.short_name else 'N/A'
        ref_no = obj.ref_no if obj.ref_no else 'N/A'
        fy_code = obj.fin_year.fin_year_code if obj.fin_year and obj.fin_year.fin_year_code else 'N/A'

        # Replace placeholders with actual values
        code = (code_format
                .replace('@branch_code@', branch_code)
                .replace('@code@', ref_no)
                .replace('@fy_code@', fy_code))

        return code

        

class ErpPurchaseEntryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPurchaseEntryDetails
        fields = '__all__'
            
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',{})
        stone_details = data.get('stone_details', [])
        other_metal_details = data.get('other_metal_details', [])
        super().__init__(*args, **kwargs)
        self.other_metal_details = other_metal_details
        self.stone_details = stone_details

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='id_sub_design.sub_design_name', read_only=True)
        fields['tax_percentage'] = serializers.CharField(source='tax_id.tax_percentage', read_only=True)
        return fields

   

    def validate(self, data):
        return validate_sale_item(self,data)
    
    
class ErpPurchaseStoneDetailsSerializer(serializers.ModelSerializer):
    stone_type = serializers.CharField(source='id_stone.stone_type')
    stone_name = serializers.SerializerMethodField()
    uom_name = serializers.SerializerMethodField()
    divided_by_value = serializers.SerializerMethodField()

    def get_stone_name(self, obj):
        return obj.id_stone.stone_name
    
    def get_divided_by_value(self, obj):
        return obj.uom_id.divided_by_value

    def get_uom_name(self, obj):
        return obj.uom_id.uom_name
    
    class Meta:
        model = ErpPurchaseStoneDetails
        fields = '__all__'

class ErpPurchaseOtherMetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPurchaseOtherMetal
        fields = '__all__'
        
class ErpPurchaseIssueReceiptStoneDetailsSerializer(serializers.ModelSerializer):
    stone_type = serializers.CharField(source='id_stone.stone_type')
    class Meta:
        model = ErpPurchaseIssueReceiptStoneDetails
        fields = '__all__'

class ErpPurchaseIssueReceiptOtherMetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPurchaseIssueReceiptOtherMetal
        fields = '__all__'

class ErpPurchaseIssueReceiptDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPurchaseIssueReceiptDetails
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='purchase_entry_detail.id_product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='purchase_entry_detail.id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='purchase_entry_detail.id_sub_design.sub_design_name', read_only=True)
        fields['purchase_va'] = serializers.CharField(source='purchase_entry_detail.purchase_va', read_only=True)
        fields['purchase_touch'] = serializers.CharField(source='purchase_entry_detail.purchase_touch', read_only=True)
        fields['pure_wt_cal_type'] = serializers.CharField(source='purchase_entry_detail.pure_wt_cal_type', read_only=True)
        fields['purchase_mc'] = serializers.CharField(source='purchase_entry_detail.purchase_mc', read_only=True)
        fields['purchase_mc_type'] = serializers.CharField(source='purchase_entry_detail.purchase_mc_type', read_only=True)
        fields['purchase_rate_type'] = serializers.CharField(source='purchase_entry_detail.purchase_rate_type', read_only=True)
        fields['purchase_rate'] = serializers.CharField(source='purchase_entry_detail.purchase_rate', read_only=True)
        fields['tax_type'] = serializers.CharField(source='purchase_entry_detail.tax_type', read_only=True)
        fields['tax_percentage'] = serializers.CharField(source='purchase_entry_detail.tax_id.tax_percentage', read_only=True)
        fields['purchase_costs'] = serializers.CharField(source='purchase_entry_detail.purchase_cost', read_only=True)

        return fields

class ErpPurchaseIssueReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPurchaseIssueReceipt
        fields = '__all__'

class ErpSupplierPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierPayment
        fields = '__all__'

class ErpSupplierPaymentModeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierPaymentModeDetail
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['mode_name'] = serializers.CharField(source='payment_mode.mode_name', read_only=True)
        fields['bank_name'] = serializers.CharField(source='id_bank.bank_name', read_only=True)
        fields['acc_number'] = serializers.CharField(source='id_bank.acc_number', read_only=True)
        return fields
        
class ErpSupplierPaymentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierPaymentDetails
        fields = '__all__'

class ErpSupplierMetalIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierMetalIssue
        fields = '__all__'

class ErpSupplierRateCutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierRateCut
        fields = '__all__'

class ErpAccountStockProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpAccountStockProcess
        fields = '__all__'

class ErpAccountStockProcessDetailsSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='id_sub_design.sub_design_name', read_only=True)
        fields['stock_type'] = serializers.CharField(source='id_product.stock_type', read_only=True)
        fields['id_metal'] = serializers.CharField(source='id_product.id_metal', read_only=True)

        return fields
    class Meta:
        model = ErpAccountStockProcessDetails
        fields = '__all__'
class ErpSupplierMetalIssueDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierMetalIssueDetails
        fields = '__all__'

class ErpInvoiceItemChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPurchaseEntryCharges
        fields = '__all__'

class ErpPurchaseEntryChargesSerializer(serializers.ModelSerializer):
    charge_name = serializers.SerializerMethodField()

    class Meta:
        model = ErpPurchaseEntryChargesDetails
        fields = '__all__'

    def get_charge_name(self, obj):
        return obj.id_charges.name if obj.id_charges else None

    
        
class ErpPurchaseReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPurchaseReturn
        fields = '__all__'
        
    def get_fields(self):
        fields = super().get_fields()
        fields['supplier_name'] = serializers.CharField(source='supplier.supplier_name', read_only=True)
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        return fields
        
class ErpPurchaseReturnDetailsSerializer(serializers.ModelSerializer):
    stone_details = serializers.SerializerMethodField()

    class Meta:
        model = ErpPurchaseReturnDetails
        fields = '__all__'
        

    def get_stone_details(self, obj):
        query_set = ErpPurchaseReturnStoneDetails.objects.filter(purchase_return_detail=obj.id_purchase_return_det)
        stone_details= ErpPurchaseReturnStoneDetailsSerializer(query_set, many=True).data
        for detail, instance in zip(stone_details, query_set):
            stone_name = instance.stone.stone_name
            detail.update({
                'piece': detail['stone_pcs'],
                'weight' : detail['stone_wt'],
                'amount': detail['stone_amount'],
                'stn_calc_type' : detail['stone_calc_type'],
                'stone_name': stone_name,
                'id_stone':detail['stone'],
                'stone_type': instance.stone.stone_type,
            })
        return stone_details

class ErpPurchaseReturnStoneDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPurchaseReturnStoneDetails
        fields = '__all__'

class ErpSupplierAdvanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierAdvance
        fields = '__all__'

class ErpSupplierAdvanceAdjSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierAdvanceAdj
        fields = '__all__'

class ErpCustomerRateCutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpCustomerRateCut
        fields = '__all__'

class ErpCustomerPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpCustomerPayment
        fields = '__all__'

class ErpCustomerPaymentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpCustomerPaymentDetails
        fields = '__all__'

class ErpCustomerPaymentModeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpCustomerPaymentModeDetail
        fields = '__all__'


class ErpPurchaseEntryDetailsListSerializer(serializers.ModelSerializer):
    metal_name = serializers.SerializerMethodField()

    class Meta:
        model = ErpPurchaseEntryDetails
        fields = [
            'id_purchase_entry_detail',
            'gross_wt',
            'pure_wt',
            'metal_name',
        ]

    def get_metal_name(self, obj):
        if obj.id_product and obj.id_product.id_metal:
            return obj.id_product.id_metal.metal_name
        return None
    
class ErpPurchaseSupplierSerializer(serializers.ModelSerializer):
    id_purchase_entry = serializers.IntegerField()
    gross_wt_sum = serializers.DecimalField(max_digits=10, decimal_places=3)
    pure_wt_sum = serializers.DecimalField(max_digits=10, decimal_places=3)
    metal_name = serializers.CharField()
    supplier_name = serializers.CharField()
    entry_date = serializers.DateField() 

class ErpSupplierRateCutAndMetalIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSupplierRateCutAndMetalIssue
        fields = '__all__'