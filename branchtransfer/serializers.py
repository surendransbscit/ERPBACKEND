from rest_framework import serializers
from .models import *
from inventory.serializers import validate_sale_item

class ErpStockTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpStockTransfer
        fields = '__all__'

class ErpTagTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpTagTransfer
        fields = '__all__'


class ErpNonTagTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpNonTagTransfer
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True)
        fields['design_name'] = serializers.CharField(source='id_design.design_name', read_only=True)
        fields['sub_design_name'] = serializers.CharField(source='id_sub_design.sub_design_name', read_only=True)
        return fields

class ErpNonTagStoneTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpNonTagStoneTransfer
        fields = '__all__'

class ErpOldMetalTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpOldMetalTransfer
        fields = '__all__'

class ErpPartlySaleStnTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPartlySaleStnTransfer
        fields = '__all__'

class ErpPartlySaleTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpPartlySaleTransfer
        fields = '__all__'

class ErpSalesReturnTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpSalesReturnTransfer
        fields = '__all__'
