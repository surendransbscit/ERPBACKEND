from rest_framework import serializers
from .models import (OtherInventoryCategory, OtherInventorySize, OtherInventoryItem, OtherInventoryPurchaseEntry,
                     OtherInventoryPurchaseEntryDetails, OtherInventoryItemIssue,
                     OtherInventoryPurchaseIssueLogs,OtherInventoryItemReOrder,ProductItemMapping)

class OtherInventoryCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherInventoryCategory
        fields = '__all__'
        
class OtherInventorySizeSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherInventorySize
        fields = '__all__'
        




class OtherInventoryItemReOrderSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = OtherInventoryItemReOrder
        fields = ['id', 'item', 'branch', 'branch_name', 'min_pcs']



class OtherInventoryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    reOrderSetting = serializers.SerializerMethodField()
    size_name = serializers.SerializerMethodField()

    class Meta:
        model = OtherInventoryItem
        fields = '__all__' 
        extra_fields = ['category_name', 'reOrderSetting', 'size_name']

    def get_reOrderSetting(self, obj):
        reorder_settings = obj.otherinventoryitemreorder_set.all() 
        return OtherInventoryItemReOrderSerializer(reorder_settings, many=True).data
    
    def get_size_name(self, obj):
        return [s.name for s in obj.size.all()]
     

        
class OtherInventoryPurchaseEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherInventoryPurchaseEntry
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['supplier_name'] = serializers.CharField(source='supplier.supplier_name', read_only=True)
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        return fields
        
class OtherInventoryPurchaseEntryDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherInventoryPurchaseEntryDetails
        fields = '__all__'
    def get_fields(self):
        fields = super().get_fields()
        fields['item_name'] = serializers.CharField(source='item.name', read_only=True)
        fields['size_name'] = serializers.CharField(source='size.name', read_only=True)
        return fields
                
class OtherInventoryItemIssueSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherInventoryItemIssue
        fields = '__all__'
    
    def get_fields(self):
        fields = super().get_fields()
        fields['item_name'] = serializers.CharField(source='item.name', read_only=True)
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        return fields
        
class OtherInventoryPurchaseLogsSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherInventoryPurchaseIssueLogs
        fields = '__all__'
    
class ProductItemMappingSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductItemMapping
        fields = '__all__'
        extra_kwargs = {
                    'id_product': {'error_messages': {'required': 'Product is required.'}},
                    'id_item': {'error_messages': {'required': 'item is required.'}}
                }
