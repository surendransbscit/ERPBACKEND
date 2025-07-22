from pyexpat import model
from statistics import mode
from django.contrib.auth.models import Group
from rest_framework.validators import UniqueValidator
from django.db.models import  Sum,Q
from rest_framework import serializers
from django.db import connection
from .models import (ErpLotInwardDetails,ErpLotInward,ErpLotInwardStoneDetails, ErpTaggingContainerLogDetails,
                     ErpTagging,ErpTaggingStone,ErpTaggingLogDetails,ErpLotInwardNonTagLogDetails,ErpLotInwardOtherMetal,
                     ErpLotInwardNonTagLogStoneDetails,ErpTaggingImages,ErpTagCharges,ErpTagAttribute,ErpTagOtherMetal,
                     ErpTagScan,ErpTagScanDetails,ErpTagIssueReceipt,ErpTagIssueReceiptDetails,ErpLotNonTagInwardDetails,ErpLotNonTagInward,
                     #ErpTagIssueReceipt,ErpTagIssueReceiptDetails,
                     ErpLotIssueReceiptDetails,ErpLotIssueReceipt, ErpTagSetItems, ErpTagSet , ErpLotMerge , ErpLotMergeDetails)
from retailmasters.models import WeightRange  
from retailmasters.views import RetUomListView
from retailsettings.models import (RetailSettings)

        
class ErpTaggingContainerLogDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpTaggingContainerLogDetails
        fields = '__all__'
        
class ErpLotInwardSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpLotInward
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['supplier_name'] = serializers.CharField(source='id_supplier.supplier_name', read_only=True)
        return fields
        
class ErpTaggingImagesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpTaggingImages
        fields = '__all__'
    def get_fields(self):
        fields = super().get_fields()
        fields['name'] = serializers.CharField(source='erp_tag.tag_code', read_only=True)
        return fields
    

class ErpLotInwardDetailsSerializer(serializers.ModelSerializer):
    cat_id = serializers.SerializerMethodField()
    class Meta:
        model = ErpLotInwardDetails
        fields = '__all__'
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='id_sub_design.sub_design_name', read_only=True)
        fields['lot_code'] = serializers.CharField(source='lot_no.lot_code', read_only=True)
        fields['size_name'] = serializers.CharField(source='size.name', read_only=True)
        fields['lot_date'] = serializers.CharField(source='lot_no.lot_date', read_only=True)
        return fields
        
    def get_cat_id(self, obj):
        return obj.id_product.cat_id.id_category
    
    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',{})
        stone_details = data.get('stone_details', [])
        other_metal_details = data.get('other_metal_detail', [])
        super().__init__(*args, **kwargs)
        self.stone_details = stone_details
        self.other_metal_details = other_metal_details

    def validate(self, data):
        print(self.stone_details)
        return validate_sale_item(self,data)
class ErpLotInwardStoneDetailsSerializer(serializers.ModelSerializer):
    stone_type = serializers.CharField(source='id_stone.stone_type')
    class Meta:
        model = ErpLotInwardStoneDetails
        fields = '__all__'

class ErpLotInwardOtherMetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLotInwardOtherMetal
        fields = '__all__'

class ErpTaggingSerializer(serializers.ModelSerializer):
    stone_details = serializers.SerializerMethodField()
    other_metal_details = serializers.SerializerMethodField()
    charges_details = serializers.SerializerMethodField()
    attribute_details = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField(read_only=True)
    cat_id = serializers.SerializerMethodField()
    tax_id = serializers.SerializerMethodField()
    weight_range = serializers.SerializerMethodField()
    stn_pcs = serializers.SerializerMethodField(read_only=True)
    purchase_date = serializers.SerializerMethodField(read_only=True)
    month_sup_code = serializers.SerializerMethodField(read_only=True)


    class Meta:
        model = ErpTagging
        fields = '__all__'

    def get_weight_range(self, obj):
        if self.context.get('weight_range', False):
            weight_range = WeightRange.objects.filter(from_weight__lt=obj.tag_gwt,to_weight__gt=obj.tag_gwt,id_product=obj.tag_product_id).first()
            print(weight_range,obj.tag_gwt,obj.tag_product_id)
            if(weight_range):
                return weight_range.weight_range_name
            return ''
        return None
    def get_stn_pcs(self, obj):
        if self.context.get('stone_pcs', False):
            stone_pcs = ErpTaggingStone.objects.filter(tag_id=obj.tag_id).aggregate(total=Sum('stone_pcs'))['total'] or 0
            return stone_pcs
        return None

    def get_date(self,obj):

        if obj.tag_date:
            return obj.tag_date.strftime("%Y-%m-%d")
        return None
    
    def get_month_sup_code(self, obj):
        if obj.tag_date:
            year = obj.tag_date.strftime("%y")  # Last two digits of the year
            month = obj.tag_date.strftime("%m")

            supplier_code = getattr(
                getattr(
                    getattr(obj.tag_lot_inward_details, 'lot_no', None),
                    'id_supplier', None
                ),
                'short_code', ''
            ) or ''

            return f"{month}{supplier_code}{year}"
        return ''


    def get_cat_id(self, obj):
        return obj.tag_product_id.cat_id.id_category

    def get_tax_id(self, obj):
        return obj.tag_product_id.tax_id.tax_id
    
    def get_purchase_date(self, obj):
        purchase_entry = (
            obj.tag_lot_inward_details
        )
        if purchase_entry and purchase_entry.purchase_entry_detail and  purchase_entry.purchase_entry_detail.purchase_entry.entry_date:
            return purchase_entry.purchase_entry_detail.purchase_entry.entry_date.strftime('%Y-%m-%d')
        return ''

    def get_fields(self):
        fields = super().get_fields()
        fields['container_name'] = serializers.CharField(source='container.container_name', read_only=True)
        fields['branch_name'] = serializers.CharField(source='tag_current_branch.name', read_only=True)
        fields['product_name'] = serializers.CharField(source='tag_product_id.product_name', read_only=True)
        fields['product_code'] = serializers.CharField(source='tag_product_id.short_code', read_only=True)
        fields['sales_mode'] = serializers.CharField(source='tag_product_id.sales_mode', read_only=True)
        fields['fixed_rate_type'] = serializers.CharField(source='tag_product_id.fixed_rate_type', read_only=True)
        fields['weight_show_in_print'] = serializers.CharField(source='tag_product_id.weight_show_in_print', read_only=True)
        fields['design_name'] = serializers.CharField(source='tag_design_id.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='tag_sub_design_id.sub_design_name', read_only=True)
        fields['section_name'] = serializers.CharField(source='tag_section_id.section_name', read_only=True)
        fields['size_name'] = serializers.CharField(source='size.name', read_only=True)
        fields['uom'] = serializers.CharField(source='tag_uom_id.uom_short_code', read_only=True)
        fields['tax_type'] = serializers.CharField(source='tag_product_id.tax_type', read_only=True)
        fields['supplier'] = serializers.CharField(source='tag_lot_inward_details.lot_no.id_supplier.id_supplier', read_only=True)
        fields['supplier_short_code'] = serializers.CharField(source='tag_lot_inward_details.lot_no.id_supplier.short_code', read_only=True)
        fields['supplier_name'] = serializers.CharField(source='id_supplier.supplier_name', read_only=True)
        fields['purity_name'] = serializers.CharField(source='tag_purity_id.description', read_only=True)
        fields['metal_name'] = serializers.CharField(source='tag_product_id.id_metal.metal_name', read_only=True)
        fields['metal'] = serializers.CharField(source='tag_product_id.id_metal.id_metal', read_only=True)


        return fields

    def get_stone_details(self, obj):
        query_set = ErpTaggingStone.objects.filter(tag_id=obj.tag_id)
        stone_details= ErpTagStoneSerializer(query_set, many=True).data
        for detail, instance in zip(stone_details, query_set):
            stone_name = instance.id_stone.stone_name
            if(detail['stone_calc_type']==1):
                detail.update({'stn_calc_type' : "Based on Pcs",})
            elif(detail['stone_calc_type']==2):
                detail.update({'stn_calc_type' : "Based on Gram",})
            detail.update({
                'piece': detail['stone_pcs'],
                'weight' : detail['stone_wt'],
                'amount': detail['stone_amount'],
                # 'stn_calc_type' : detail['stone_calc_type'],
                'stone_name': stone_name,
                'stone_type': instance.id_stone.stone_type,
                'uom_name': instance.uom_id.uom_name,
                'divided_by_value':instance.uom_id.divided_by_value,
                'quality_code':instance.id_quality_code.code if instance.id_quality_code!=None else None,
            })
        return stone_details
    
    def get_other_metal_details(self, obj):
        queryset = ErpTagOtherMetal.objects.filter(tag_id=obj.tag_id)
        other_metal_details= ErpTagOtherMetalSerializer(queryset, many=True).data
        for detail, instance in zip(other_metal_details, queryset):
            cat_name = instance.id_category.cat_name
            detail.update({
                'cat_name': cat_name
            })
        return other_metal_details
    
    def get_charges_details(self,obj):
        queryset = ErpTagCharges.objects.filter(tag_id=obj.tag_id)
        charges_details= ErpTagChargesSerializer(queryset, many=True).data
        return charges_details
    
    def get_attribute_details(self,obj):
        queryset = ErpTagAttribute.objects.filter(tag_id=obj.tag_id)
        attribute_details= ErpTagAttributeSerializer(queryset, many=True).data
        return attribute_details

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data',{})
        stone_details = data.get('stone_details', [])
        other_metal_details = data.get('other_metal_detail', [])
        super().__init__(*args, **kwargs)
        self.stone_details = stone_details
        self.other_metal_details = other_metal_details


    def validate(self, data):
    # Example: your existing logic
        if data.get('tag_huid'):
            if ErpTagging.objects.filter(
                Q(tag_huid2=data.get('tag_huid')) | Q(tag_huid=data.get('tag_huid'))
            ).filter(tag_status=1).exclude(pk=getattr(self.instance, 'pk', None)).exists():
                raise serializers.ValidationError("Tag HUID already exists.")

            if data.get('tag_huid') == data.get('tag_huid2'):
                raise serializers.ValidationError("Tag HUID and Tag HUID 2 cannot be the same.")

        if data.get('tag_huid2'):
            if ErpTagging.objects.filter(
                Q(tag_huid2=data.get('tag_huid2')) | Q(tag_huid=data.get('tag_huid2'))
            ).filter(tag_status=1).exclude(pk=getattr(self.instance, 'pk', None)).exists():
                raise serializers.ValidationError("Tag HUID 2 already exists.")

            if data.get('tag_huid') == data.get('tag_huid2'):
                raise serializers.ValidationError("Tag HUID and Tag HUID 2 cannot be the same.")
        return validate_sale_item(self,data,1)

class ErpTagStoneSerializer(serializers.ModelSerializer):
    stone_type = serializers.CharField(source='id_stone.stone_type')
    class Meta:
        model = ErpTaggingStone
        fields = '__all__'

def validate_sale_item(serializer_instance,data,validate_for=""):

    if (validate_for==1):
        net_weight      = float(data.get('tag_nwt', 0))
        gross_weight    = float(data.get('tag_gwt', 0))
        less_weight     = float(data.get('tag_lwt', 0))
        stone_wt        = float(data.get('tag_stn_wt', 0))
        dia_wt          =float(data.get('tag_dia_wt', 0))
        other_wt        =float(data.get('tag_other_metal_wt', 0))
    else:
        net_weight      = data.get('net_wt')
        gross_weight    = data.get('gross_wt')
        less_weight     = data.get('less_wt')
        stone_wt        = data.get('stone_wt')
        dia_wt          = data.get('dia_wt')
        other_wt        = data.get('other_metal_wt',0)
    
    if (gross_weight):
        net_wt          = format(gross_weight - less_weight - other_wt,'.3f')

        total_stone_weight = 0
        total_other_wt = 0
        #print(data)
        for stn in serializer_instance.stone_details:
            stone_weight = RetUomListView.carat_to_gram_conversion(serializer_instance,stn['stone_wt'],stn['uom_id'])
            print('stone_weight:',stone_weight)
            if(int(stn['show_in_lwt'])==1):   
                total_stone_weight +=float(stone_weight)
        total_stone_weight = format(total_stone_weight,'.3f')

        if hasattr(serializer_instance, 'other_metal_details') and serializer_instance.other_metal_details is not None:
            print(serializer_instance.other_metal_details)
            for other in serializer_instance.other_metal_details:
                total_other_wt +=float(other['weight'])

        if float(net_weight) > float(gross_weight):
                raise serializers.ValidationError("Net weight cannot be greater than gross weight.")
        if float(less_weight) > float(gross_weight):
                raise serializers.ValidationError("Less weight cannot be greater than gross weight.")
        if float(net_weight)!=float(net_wt):
                raise serializers.ValidationError(F"Net weight is Not Matching {net_weight}  {net_wt}")
        if(less_weight >0 and (stone_wt==0 and dia_wt==0)):
            raise serializers.ValidationError("Less Weight or Dia Weight is missing.")
        if(float(total_stone_weight)!=float(less_weight)):
                raise ValueError(F"Less weight is Not Matching {total_stone_weight}  {less_weight}")
        if(float(total_other_wt)!=float(other_wt)):
                raise serializers.ValidationError(F"Other Metal Wt is Not Matching {total_other_wt}  {other_wt}" )
    
    return data


class ErpLotInwardNonTagSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpLotInwardNonTagLogDetails
        fields = '__all__'

class ErpTaggingLogSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpTaggingLogDetails
        fields = '__all__'
    def get_fields(self):
        fields = super().get_fields()
        fields['from_branch_name'] = serializers.CharField(source='from_branch.name', read_only=True)
        fields['to_branch_name'] = serializers.CharField(source='to_branch.name', read_only=True)
        fields['stock_status_name'] = serializers.CharField(source='id_stock_status.name', read_only=True)
        return fields


class ErpLotInwardNonTagStoneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpLotInwardNonTagLogStoneDetails
        fields = '__all__'

class ErpTagAttributeSerializer(serializers.ModelSerializer):
    attribute_name = serializers.SerializerMethodField()

    class Meta:
        model = ErpTagAttribute
        fields = '__all__'
    
    def get_attribute_name(self,obj):
        return obj.id_attribute.attribute_name

class ErpTagChargesSerializer(serializers.ModelSerializer):
    charge_name = serializers.SerializerMethodField()
    class Meta:
        model = ErpTagCharges
        fields = '__all__'
    
    def get_charge_name(self,obj):
        return obj.id_charges.name

class ErpTagOtherMetalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpTagOtherMetal
        fields = '__all__'

        
class ErpTagScanSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpTagScan
        fields = '__all__'

class ErpTagScanDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpTagScanDetails
        fields = '__all__'

class ErpLotIssueReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLotIssueReceipt
        fields = '__all__'

class ErpLotIssueReceiptDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLotIssueReceiptDetails
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_lot_inward_detail.id_product.product_name', read_only=True)
        fields['lot_no'] = serializers.CharField(source='id_lot_inward_detail.lot_no.lot_code', read_only=True)
        return fields
class ErpTagIssueReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpTagIssueReceipt
        fields = '__all__'

class ErpTagIssueReceiptDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpTagIssueReceiptDetails
        fields = '__all__'

class ErpLotNonTagInwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLotNonTagInward
        fields = '__all__'

class ErpLotNonTagInwardDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLotNonTagInwardDetails
        fields = '__all__'
        
class ErpTagSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpTagSet
        fields = '__all__'
        
class ErpTagSetItemsSerializer(serializers.ModelSerializer):
    tag = ErpTaggingSerializer(read_only=True)
    class Meta:
        model = ErpTagSetItems
        fields = '__all__'


class ErpLotMergeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLotMerge
        fields = '__all__'

class ErpLotMergeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpLotMergeDetails
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_lot_inward_detail.id_product.product_name', read_only=True)
        fields['lot_no'] = serializers.CharField(source='id_lot_inward_detail.lot_no.lot_code', read_only=True)
        return fields