from rest_framework import serializers
from .models import (ERPOrder, ERPOrderDetails, ERPOrderStoneDetails, ERPOrderAttribute, ERPOrderCharges,
                     ERPOrderImages,ERPOrderVideos,ERPOrderAudios, ErpOrderOtherMetal, ErpJobOrder, ErpJobOrderDetails, CustomerCart, CustomerWishlist,
                     ErpOrderRepairExtraMetal,ErpOrderInternalProcessLog)
from rest_framework.validators import UniqueTogetherValidator
from inventory.serializers import validate_sale_item
from utilities.utils import format_date
class ErpOrderStoneSerializer(serializers.ModelSerializer):
    stone_type = serializers.CharField(source='stone.stone_type')
    stone_name = serializers.SerializerMethodField()
    uom_name = serializers.SerializerMethodField()
    divided_by_value = serializers.SerializerMethodField()
    class Meta:
        model = ERPOrderStoneDetails
        fields = '__all__'

    def get_stone_name(self, obj):
        return obj.stone.stone_name
    
    def get_divided_by_value(self, obj):
        return obj.uom_id.divided_by_value

    def get_uom_name(self, obj):
        return obj.uom_id.uom_name
        
class ErpOrderOtherMetalSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpOrderOtherMetal
        fields = '__all__'
        

class ErpOrdersSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ERPOrder
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ERPOrder.objects.all(),
                fields=(
                    'order_branch',
                    'fin_year',
                    'order_type',
                    'order_no'),
                message='Order number already exists')]
        
    def get_date(self,obj):
        if obj.order_date:
            return obj.order_date.strftime("%d-%m-%Y")
        return None
    
    def get_fields(self):
        fields = super().get_fields()
        fields['branch_name'] = serializers.CharField(source='order_branch.name', read_only=True)
        fields['customer_name'] = serializers.CharField(source='customer.firstname',read_only=True)
        fields['customer_mobile'] = serializers.CharField(source='customer.mobile',read_only=True)
        fields['employee_name'] = serializers.CharField(source='created_by.username',read_only=True)

        return fields
    
class ErpOrdersDetailSerializer(serializers.ModelSerializer):
    stone_details = serializers.SerializerMethodField()
    internal_process_details = serializers.SerializerMethodField()
    class Meta:
        model = ERPOrderDetails
        fields = '__all__'

    def get_due_date(self,obj):
        if obj.customer_due_date:
            return obj.customer_due_date.strftime("%d-%m-%Y")
        return None
    
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='sub_design.sub_design_name', read_only=True)
        fields['uom_name'] = serializers.CharField(source='uom.uom_short_code', read_only=True)
        fields['purity_name'] = serializers.CharField(source='purity.description', read_only=True)
        fields['size_name'] = serializers.CharField(source='size.name', read_only=True)
        fields['order_status_name'] = serializers.CharField(source='order_status.name', read_only=True)
        fields['colour'] = serializers.CharField(source='order_status.colour', read_only=True)
        fields['repair_tax'] = serializers.CharField(source='repair_type.tax_id.tax_percentage', read_only=True)
        fields['repair_tax_type'] = serializers.CharField(source='repair_type.tax_id.tax_type', read_only=True)
        fields['order_no'] = serializers.CharField(source='order.order_no', read_only=True)
        fields['tag_code'] = serializers.CharField(source='erp_tag.old_tag_code', read_only=True)


        return fields
    
    def get_stone_details(self, obj):
        if self.context.get('stone_details', False):
            query_set = ERPOrderStoneDetails.objects.filter(tag_id=obj.tag_id)
            stone_details= ErpOrderStoneSerializer(query_set, many=True).data
            for detail, instance in zip(stone_details, query_set):
                stone_name = instance.stone.stone_name
                detail.update({
                    'pieces': detail['stone_pcs'],
                    'weight' : detail['stone_wt'],
                    'stone_amnt': detail['stone_amount'],
                    'calc_type' : detail['stone_calc_type'],
                    'stone_name': stone_name,
                    # 'stone_type': instance.stone.stone_type,
                })
            return stone_details
        return None


    def get_internal_process_details(self, obj):
        query_set = ErpOrderInternalProcessLog.objects.filter(order_detail=obj)
        internal_process_details= ErpOrderInternalProcessLogSerializer(query_set, many=True).data
        for detail, instance in zip(internal_process_details, query_set):
            detail.update({
                'process_name': instance.internal_order_process.name,
                'process_date': format_date(instance.created_on),
            })
        return internal_process_details

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',{})
        stone_details = data.get('stone_details', [])
        other_metal_details = data.get('other_metal_details', [])
        super().__init__(*args, **kwargs)
        self.stone_details = stone_details
        self.other_metal_details = other_metal_details

    
    def validate(self, data):
        return validate_sale_item(self,data)
    
    
class ErpOrderAttributeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ERPOrderAttribute
        fields = '__all__'

class ErpOrderChargesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ERPOrderCharges
        fields = '__all__'
        
class ErpOrderImagesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ERPOrderImages
        fields = '__all__'
        
        

class ErpJobOrderSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpJobOrder
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ErpJobOrder.objects.all(),
                fields=(
                    'assigned_to',
                    'fin_year',
                    'ref_no'),
                message='Job Order number already exists')]
        
    def get_fields(self):
        fields = super().get_fields()
        fields['karigar_name'] = serializers.CharField(source='supplier.supplier_name', read_only=True, allow_null=True)
        fields['karigar_mobile'] = serializers.CharField(source='supplier.mobile_no', read_only=True, allow_null=True)
        return fields
        
class ErpJobOrderDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpJobOrderDetails
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['supplier_name'] = serializers.CharField(source='job_order.supplier.supplier_name',read_only=True)
        fields['supplier_mobile'] = serializers.CharField(source='job_order.supplier.mobile_no',read_only=True)
        return fields
        
class CustomerCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerCart
        fields = '__all__'
        
    def get_fields(self):
        fields = super().get_fields()
        fields['customer_name'] = serializers.CharField(source='customer.firstname',read_only=True)
        fields['customer_mobile'] = serializers.CharField(source='customer.mobile',read_only=True)
        fields['metal_name'] = serializers.CharField(source='product.id_metal.metal_name', read_only=True)
        fields['product_name'] = serializers.CharField(source='product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='sub_design.sub_design_name', read_only=True, allow_null=True)
        fields['uom_name'] = serializers.CharField(source='uom.uom_short_code', read_only=True, allow_null=True)
        fields['tag_code'] = serializers.CharField(source='erp_tag.tag_code', read_only=True, allow_null=True)
        return fields
        
class CustomerWishlistSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerWishlist
        fields = '__all__'
    
class ERPOrderAudiosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERPOrderAudios
        fields = ['det_order_audio_id', 'order_detail', 'name', 'audio']


class ERPOrderVideosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERPOrderVideos
        fields = ['det_order_vid_id', 'order_detail', 'name', 'video']


class ErpOrderRepairExtraMetalSerializer(serializers.ModelSerializer):

    class Meta:
        model = ErpOrderRepairExtraMetal
        fields = '__all__'

class ErpOrderInternalProcessLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = ErpOrderInternalProcessLog
        fields = '__all__'