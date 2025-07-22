from pyexpat import model
from statistics import mode
from django.contrib.auth.models import Group
from rest_framework.validators import UniqueValidator
from rest_framework import serializers

from .models import (Scheme,PaymentSettings,SchemePaymentFormula,Denomination,SchemeWeight, 
                     SchemeBenefitSettings,SchemeDigiGoldInterestSettings, SchemeGiftSettings)

class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = '__all__'
        
        
class PaymentSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSettings
        fields = '__all__'
        
class SchemeGiftSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeGiftSettings
        fields = '__all__'
        
class SchemeBenefitSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeBenefitSettings
        fields = '__all__'

class SchemePaymentFormulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemePaymentFormula
        fields = '__all__'

class SchemeAmountDenomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Denomination
        fields = '__all__'


class SchemeWeightDenomSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeWeight
        fields = '__all__'

class SchemeDigiGoldInterestSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeDigiGoldInterestSettings
        fields = '__all__'