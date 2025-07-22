from rest_framework import serializers
from .models import (ErpPocket,ErpPocketDetails,ErpPocketStoneDetails,ErpMeltingIssueDetails,
                     ErpMetalProcess,ErpMeltingReceiptDetails,ErpTestingIssueDetails,
                     ErpRefining,ErpRefiningDetails,ErpRefiningReceiptDetails)
from inventory.serializers import validate_sale_item

        
class ErpPocketSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpPocket
        fields = '__all__'


class ErpPocketDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpPocketDetails
        fields = '__all__'

    
class ErpPocketDetailStoneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpPocketStoneDetails
        fields = '__all__'


class ErpMetalProcessSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpMetalProcess
        fields = '__all__'

class ErpMeltingIssueDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpMeltingIssueDetails
        fields = '__all__'

class ErpMeltingReceiptDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpMeltingReceiptDetails
        fields = '__all__'

class ErpPocketMeltingIssueSerializer(serializers.ModelSerializer):

    balance_pcs = serializers.FloatField()
    balance_gwt = serializers.FloatField()
    balance_lwt = serializers.FloatField()
    balance_nwt = serializers.FloatField()
    product_name = serializers.CharField()
    id_product = serializers.IntegerField()
    
    class Meta:
        model = ErpPocket
        fields = ['id_pocket', 'pocket_no','product_name','id_product',
                  'balance_pcs', 'balance_gwt', 'balance_lwt', 'balance_nwt']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Formatting balance fields to 3 decimal places
        representation['balance_pcs'] = format(representation['balance_pcs'], '.0f')
        representation['balance_gwt'] = format(representation['balance_gwt'], '.3f')
        representation['balance_lwt'] = format(representation['balance_lwt'], '.3f')
        representation['balance_nwt'] = format(representation['balance_nwt'], '.3f')
        return representation


class ErpTestingIssueDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpTestingIssueDetails
        fields = '__all__'


class ErpRefiningSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpRefining
        fields = '__all__'


class ErpRefiningDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpRefiningDetails
        fields = '__all__'


class ErpRefiningReceiptDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpRefiningReceiptDetails
        fields = '__all__'