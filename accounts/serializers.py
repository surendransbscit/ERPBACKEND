from collections import OrderedDict
from dataclasses import field, fields
from datetime import datetime, timedelta
from pyexpat import model
from statistics import mode
from django.contrib.auth.models import Group
from pkg_resources import require
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import User

# serializer for LOGIN -- for Admin and Customers (All devices --one login/ authentication table is availabe in Django)
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        print("user", user)
        # if user.is_active == False:
        #     raise serializers.ValidationError('User is Inactive')
        if user:
            if user.is_active:
                return user
            raise serializers.ValidationError('User Account not active')
        raise serializers.ValidationError('Incorrect username/password')


# To view general data of users(both Admins and Customers)
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        # fields = ['id', 'username', 'email', 'is_customer', 'is_adminuser']
        fields = ['id', 'username', 'email', 'account_expiry', 'is_active']
