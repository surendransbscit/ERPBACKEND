from rest_framework import serializers
from .models import (ErpEstimation,ErpEstimationSalesDetails,ErpEstimationStoneDetails,ErpEstimationOldMetalDetails,ErpEstimationItemCharges,ErpEstimationSchemeAdjusted,ErpEstimationOtherMetal,
                     ErpEstimationSalesReturnDetails)
from inventory.serializers import (validate_sale_item)
from django.db import models
from django.db.models import F
from django.utils.timezone import localtime


class ErpEstimationSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    class Meta:
        model = ErpEstimation
        fields = '__all__'

    def get_time(self, obj):
        return localtime(obj.created_on).strftime('%I:%M %p')

    def get_tag_codes(self, obj):
        tag_codes = ErpEstimationSalesDetails.objects.filter(estimation_id=obj).values_list('tag_id__tag_code', flat=True)
        tag_codes= ','.join(map(str, tag_codes))
        return tag_codes

    def get_employee_names(self, obj):
        sales_items = ErpEstimationSalesDetails.objects.filter(estimation_id=obj)

        employee_set = set()

        for item in sales_items:
            if item.ref_emp_id and item.ref_emp_id.firstname:
                employee_set.add(item.ref_emp_id.firstname)
            if item.ref_emp_id_1 and item.ref_emp_id_1.firstname:
                employee_set.add(item.ref_emp_id_1.firstname)
            if item.ref_emp_id_2 and item.ref_emp_id_2.firstname:
                employee_set.add(item.ref_emp_id_2.firstname)

        return ', '.join(sorted(employee_set))


    
    def get_fields(self):
        fields = super().get_fields()
        fields['pk_id'] = serializers.IntegerField(source='pk', read_only=True)
        fields['branch_name'] = serializers.CharField(source='id_branch.name', read_only=True)
        fields['customer_name'] = serializers.CharField(source='id_customer.firstname', read_only=True)
        fields['customer_mobile'] = serializers.CharField(source='id_customer.mobile', read_only=True)
        fields['date'] = serializers.DateField(source='entry_date',format='%d-%m-%Y', read_only=True)
        fields['tag_codes'] = serializers.SerializerMethodField()
        fields['employee_names'] = serializers.SerializerMethodField()
        return fields

class ErpEstimationSalesDetailsSerializer(serializers.ModelSerializer):
    stone_details = serializers.SerializerMethodField()
    charges_details = serializers.SerializerMethodField()
    other_metal_details = serializers.SerializerMethodField()
    cat_id = serializers.SerializerMethodField()
    tag_code = serializers.SerializerMethodField()
    old_tag_code = serializers.SerializerMethodField()
    stone_amount = serializers.SerializerMethodField()
    charges_amount = serializers.SerializerMethodField()
    other_metal_amt = serializers.SerializerMethodField()

    
    class Meta:
        model = ErpEstimationSalesDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',{})
        stone_details = data.get('stone_details', [])
        other_metal_details = data.get('other_metal_detail', [])
        super().__init__(*args, **kwargs)
        self.stone_details = stone_details
        self.other_metal_details = other_metal_details

    def validate(self, data):
        return validate_sale_item(self,data)
    
    def get_stone_details(self, obj):
        if self.context.get('stone_details', False):
            stone_details = ErpEstimationStoneDetails.objects.filter(est_item_id=obj.est_item_id)
            return ErpEstimationStoneDetailsSerializer(stone_details, many=True).data
        return None

    def get_charges_details(self, obj):
        if self.context.get('charges_details', False):
            charges_details = ErpEstimationItemCharges.objects.filter(est_item_id=obj.est_item_id)
            return ErpEstimationItemChargesSerializer(charges_details, many=True).data
        return None
    
    def get_other_metal_details(self, obj):
        queryset = ErpEstimationOtherMetal.objects.filter(est_item_id=obj.est_item_id)
        other_metal_details= ErpEstimationOtherMetalSerializer(queryset, many=True).data
        for detail, instance in zip(other_metal_details, queryset):
            cat_name = instance.id_category.cat_name
            detail.update({
                'cat_name': cat_name
            })
        return other_metal_details
    
    def get_cat_id(self, obj):
        return obj.id_product.cat_id.id_category
    
    def get_tag_code(self, obj):
        if obj.tag_id and obj.tag_id.tag_code:
            if obj.tag_id.old_tag_code:
                return obj.tag_id.old_tag_code
            return obj.tag_id.tag_code
        return None
    
    def get_old_tag_code(self, obj):
        if obj.tag_id:
            return obj.tag_id.old_tag_code
        return None
    
    def get_other_metal_amt(self, obj):
        return obj.erp_est_other_metal_est_item_id.aggregate(amount=models.Sum('other_metal_cost'))['amount'] or 0
    def get_charges_amount(self, obj):
        return obj.charge_est_item_id.aggregate(amount=models.Sum('charges_amount'))['amount'] or 0
    def get_stone_amount(self, obj):
        return obj.stn_est_item_id.aggregate(amount=models.Sum('stone_amount'))['amount'] or 0
    
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['product_code'] = serializers.CharField(source='id_product.short_code', read_only=True)
        fields['weight_show_in_print'] = serializers.CharField(source='id_product.weight_show_in_print', read_only=True)
        fields['weight_show_in_print_purity'] = serializers.CharField(source='id_purity.weight_show_in_print', read_only=True)
        fields['fixed_rate_type'] = serializers.CharField(source='id_product.fixed_rate_type', read_only=True)
        fields['sales_mode'] = serializers.CharField(source='id_product.sales_mode', read_only=True)
        fields['design_name'] = serializers.CharField(source='id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='id_sub_design.sub_design_name', read_only=True)  
        fields['emp_name'] = serializers.CharField(source='ref_emp_id.firstname', read_only=True)        
        fields['tagGrossWeight'] = serializers.CharField(source='tag_id.tag_gwt', read_only=True)        
        fields['maxGrossWeight'] = serializers.CharField(source='tag_id.tag_gwt', read_only=True)
        fields['supplier_name'] = serializers.CharField(source='tag_id.id_supplier.supplier_name', read_only=True)
        return fields


class ErpEstimationStoneDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpEstimationStoneDetails
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['stone_type'] = serializers.CharField(source='id_stone.stone_type', read_only=True)
        fields['stone_name'] = serializers.CharField(source='id_stone.stone_name', read_only=True)
        fields['uom_name'] = serializers.CharField(source='uom_id.uom_short_code', read_only=True)

        return fields
    

class ErpEstimationOldMetalDetailsSerializer(serializers.ModelSerializer):
    stone_details = serializers.SerializerMethodField()
    cat_id = serializers.SerializerMethodField()
    class Meta:
        model = ErpEstimationOldMetalDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        stone_details = kwargs.pop('stone_details', None)
        super().__init__(*args, **kwargs)
        self.stone_details = stone_details

    def get_stone_details(self, obj):
        if self.stone_details:
            stone_details = ErpEstimationStoneDetails.objects.filter(est_old_metal_item_id=obj.est_old_metal_item_id)
            return ErpEstimationStoneDetailsSerializer(stone_details, many=True).data
        return None

    def get_cat_id(self,obj):
         return obj.id_product.cat_id.id_category
    
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['old_metal_type_name'] = serializers.CharField(source = 'item_type.name',read_only=True)
        fields['old_metal_type_code'] = serializers.CharField(source = 'item_type.code',read_only=True)
        fields['rate_deduction'] = serializers.CharField(source = 'item_type.rate_deduction',read_only=True)
        return fields

class ErpEstimationItemChargesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpEstimationItemCharges
        fields = '__all__'

class ErpEstimationSchemeAdjustedSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpEstimationSchemeAdjusted
        fields = '__all__'

class ErpEstimationOtherMetalSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpEstimationOtherMetal
        fields = '__all__'
    

class ErpEstimationSalesReturnSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpEstimationSalesReturnDetails
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        return fields