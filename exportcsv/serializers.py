from pyexpat import model
from statistics import mode
from django.contrib.auth.models import Group
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from django.db import connection
from .models import (RawTagData, RawTagStoneData, RawTagStatusData, RawSchemeAccountData)

     
class RawTagDataSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RawTagData
        fields = '__all__'

class RawTagStatusDataSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RawTagStatusData
        fields = '__all__'

class RawTagStoneDataSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RawTagStoneData
        fields = '__all__'
        
class RawSchemeAccountDataSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RawSchemeAccountData
        fields = '__all__'

