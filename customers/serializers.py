from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.validators import UniqueValidator
from datetime import datetime, timedelta

from accounts.models import User
from retailsettings.models import (RetailSettings)
from .models import (Customers, CustomerLoginPin, CustomerAddress, CustomerFamilyDetails, CustomerDeviceIdMaster,
                     CustomerNominee,TempCustomers, CustomerEnquiry)

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customers
        fields = '__all__'
        
class TempCustomersSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempCustomers
        fields = '__all__'
        
class CustomerFamilyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFamilyDetails
        fields = '__all__'
        
class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = '__all__'
        
class CustomerLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        todays_date = datetime.today().date()
        user = authenticate(**data)
        #print("user", user)
        # if user.is_active == False:
        #     raise serializers.ValidationError('User is Inactive')
        if user:
            
            if todays_date <= user.account_expiry:
                if user.is_active:
                    if user.is_customer:
                        return user
                    raise serializers.ValidationError(
                        {"message": 'Customer Not Found'})
                raise serializers.ValidationError(
                    {"message": 'User Inactive'})
            raise serializers.ValidationError(
                {"message": "Your Account has Expired. Please Contact Admin"})
        raise serializers.ValidationError(
            {"message": 'Incorrect username/password'})
        
class CustomerLoginPinSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerLoginPin
        fields = '__all__'
        
class CustomerDeviceIdMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDeviceIdMaster
        fields = '__all__'
        
class CustomerNomineeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerNominee
        fields = '__all__'

class CustomerEnquirySerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerEnquiry
        fields = '__all__'