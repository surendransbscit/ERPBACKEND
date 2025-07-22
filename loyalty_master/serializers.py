from rest_framework import serializers
from .models import (LoyaltyTier,LoyaltySettings,LoyaltyCustomer,LoyaltyTransaction)



class LoyaltyTierSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LoyaltyTier
        fields = '__all__'
        
        

class LoyaltySettingsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LoyaltySettings
        fields = '__all__'
        
        
class LoyaltyCustomerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LoyaltyCustomer
        fields = '__all__'
        
        
        
class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LoyaltyTransaction
        fields = '__all__'