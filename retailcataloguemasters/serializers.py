from rest_framework import serializers
from django.db import models
from .models import (Metal, Purity,SchemeClassification,QualityCode ,Stone,Clarity, Color, Shape, RetCut, Category, 
                     Product,SubDesign,Design, ProductMapping,SubDesignMapping,MakingAndWastageSettings,Section,
                     ProductCalculationType, DiamondCentRate,DiamondRateMaster,ProductSection,
                     ErpReorderSettings,CounterWiseTarget,CustomerMakingAndWastageSettings, CustomerEnquiry,
                     PurchaseDiamondRateMaster, PurchaseDiamondCentRate,RepairDamageMaster,CategoryPurityRate)

        
class CategoryPurityRateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryPurityRate
        fields = '__all__'
        
class MetalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Metal
        fields = '__all__'
        
        
class PuritySerializer(serializers.ModelSerializer):

    class Meta:
        model = Purity
        fields = '__all__'
        
class SchemeClassificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchemeClassification
        fields = '__all__'
        
        
class StoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Stone
        fields = '__all__'

class QualityCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = QualityCode
        fields = '__all__'


class DiamondRateSerializer(serializers.ModelSerializer):

    class Meta:
        model = DiamondRateMaster
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['quality_code_name'] = serializers.CharField(source='quality_code.code', read_only=True, allow_null=True)
        return fields
    

class PurchaseDiamondRateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseDiamondRateMaster
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['quality_code_name'] = serializers.CharField(source='quality_code.code', read_only=True, allow_null=True)
        return fields
        
class DiamondCentRateSerializer(serializers.ModelSerializer):

    class Meta:
        model = DiamondCentRate
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['quality_code'] = serializers.CharField(source='id_rate.quality_code.quality_id', read_only=True, allow_null=True)
        return fields
        
class PurchaseDiamondCentRateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseDiamondCentRate
        fields = '__all__'

class ClaritySerializer(serializers.ModelSerializer):

    class Meta:
        model = Clarity
        fields = '__all__'


class ColorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Color
        fields = '__all__'

class ShapeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shape
        fields = '__all__'
        
class ErpReorderSettingsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpReorderSettings
        fields = '__all__'
        extra_kwargs = {
                    'product': {'error_messages': {'required': 'Product is required.'}},
                    'branch': {'error_messages': {'required': 'Branch is required.'}},
                    'design': {'error_messages': {'required': 'Design is required.'}},
                    'sub_design': {'error_messages': {'required': 'Sub design is required.'}},
                    'size': {'error_messages': {'required': 'Size is required.'}},
                    'weight_range': {'error_messages': {'required': 'Weight range is required.'}},
                    'min_pcs': {'error_messages': {'required': 'Min pieces is required.'}},
                    'max_pcs': {'error_messages': {'required': 'Max pieces is required.'}},
                    
                }
        
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='product.product_name', read_only=True, allow_null=True)
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True, allow_null=True)
        fields['design_name'] = serializers.CharField(source='design.design_name', read_only=True, allow_null=True)
        fields['sub_design_name'] = serializers.CharField(source='sub_design.sub_design_name', read_only=True, allow_null=True)
        fields['weight_range_name'] = serializers.CharField(source='weight_range.weight_range_name', read_only=True, allow_null=True)
        fields['size_name'] = serializers.CharField(source='size.name', read_only=True, allow_null=True)
        return fields
        
        
class RetCutSerializer(serializers.ModelSerializer):

    class Meta:
        model = RetCut
        fields = '__all__'
        
class CategorySerializer(serializers.ModelSerializer):
    cat_type_name = serializers.CharField(source='get_cat_type_display', read_only=True)

    class Meta:
        model = Category
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['metal_name'] = serializers.CharField(source='id_metal.metal_name', read_only=True)
        return fields
        
class ProductSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()
    other_wt = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_sections(self, obj):
        sections = ProductSection.objects.filter(id_product=obj.pro_id).values_list('id_section', flat=True)
        return list(sections)
    def get_other_wt(self, obj):
        return obj.other_weight.aggregate(other_wt=models.Sum('weight'))['other_wt'] or 0
    def get_fields(self):
        fields = super().get_fields()
        fields['cat_type'] = serializers.CharField(source='cat_id.cat_type', read_only=True)
        return fields


class  QualityCodeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = QualityCode 
        fields = '__all__'
            
class  CounterWiseTargetSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CounterWiseTarget 
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        fields['section_name'] = serializers.CharField(source='section.section_name', read_only=True)
        return fields


class DesignSerializer(serializers.ModelSerializer):

    class Meta:
        model = Design
        fields = '__all__'
        design_name = serializers.CharField(
        required=True,
        error_messages={'required': 'Design Name is required.'})

class SubDesignSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubDesign
        fields = '__all__'
        sub_design_name = serializers.CharField(
        required=True,
        error_messages={'required': 'Sub Design Name is required.'})

class ProductMappingSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductMapping
        fields = '__all__'
        extra_kwargs = {
                    'id_product': {'error_messages': {'required': 'Product is required.'}},
                    'id_design': {'error_messages': {'required': 'Design is required.'}}
                }
        
class SubDesignMappingSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubDesignMapping
        fields = '__all__'
        extra_kwargs = {
                    'id_product': {'error_messages': {'required': 'Product is required.'}},
                    'id_design': {'error_messages': {'required': 'Design is required.'}},
                    'id_sub_design': {'error_messages': {'required': 'Sub Design is required.'}}
                }
        
class MakingAndWastageSettingsMappingSerializer(serializers.ModelSerializer):

    class Meta:
        model = MakingAndWastageSettings
        fields = '__all__'
        extra_kwargs = {
                    'id_product': {'error_messages': {'required': 'Product is required.'}},
                    'id_design': {'error_messages': {'required': 'Design is required.'}},
                    'id_sub_design': {'error_messages': {'required': 'Sub Design is required.'}},
                }
    
    def get_fields(self):
        fields = super().get_fields()
        fields['from_weight'] = serializers.CharField(source='id_weight_range.from_weight', read_only=True)
        fields['to_weight'] = serializers.CharField(source='id_weight_range.to_weight', read_only=True)
        return fields
    
    
class CustomerMakingAndWastageSettingsMappingSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerMakingAndWastageSettings
        fields = '__all__'
        extra_kwargs = {
                    'id_product': {'error_messages': {'required': 'Product is required.'}},
                    'id_design': {'error_messages': {'required': 'Design is required.'}},
                    'id_sub_design': {'error_messages': {'required': 'Sub Design is required.'}},
                }
    
    def get_fields(self):
        fields = super().get_fields()
        fields['from_weight'] = serializers.CharField(source='id_weight_range.from_weight', read_only=True)
        fields['to_weight'] = serializers.CharField(source='id_weight_range.to_weight', read_only=True)
        return fields
    

class SectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Section
        fields = '__all__'
        extra_kwargs = {
                    'section_name': {'error_messages': {'required': 'Section Name is required.'}},
                }
        

class ProductCalculationTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductCalculationType
        fields = '__all__'

class ProductSectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductSection
        fields = '__all__'

class RepairDamageMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = RepairDamageMaster
        fields = '__all__'        
class CustomerEnquirySerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerEnquiry
        fields = '__all__'