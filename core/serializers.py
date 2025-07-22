from rest_framework import serializers
from django.contrib.auth import authenticate
from models_logging.models import Change
from django.core.validators import EmailValidator
from rest_framework.validators import UniqueTogetherValidator

from accounts.models import User
from .models import Menu, EmpMenuAccess, Employee,LoginDetails,ReportColumnsTemplates


# serializer for Admin sign in validation
class EmployeeSignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        email_validation = EmailValidator()
        # check username is a Email Address
        try:
            email_validation(data['username'])
            # Find username using the Email address provided
            try:
                username = User.objects.get(email=data['username']).username
                data.update({"username": username})
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"error_detail": [
                        "Incorrect username/password"]}
                )
        except:
            pass

        user = authenticate(**data)
        if user:
            if user.is_active:
                if user.is_adminuser:
                    return user
                raise serializers.ValidationError(
                    {"error_detail": [
                        "Incorrect username/password for Admin"]})
            raise serializers.ValidationError(
                {"error_detail": [
                    "Inactive Account"]})
        raise serializers.ValidationError(
            {"error_detail": [
                "Incorrect username/password"]}
        )


# serializer for AdminMenu model
class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'
        

class EmpMenuAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpMenuAccess
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=EmpMenuAccess.objects.all(),
                fields=(
                    'profile',
                    'menu',),
                message='Menu access already given to this profile')]


# serializer for Admin model
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'


# serializer for logs - changes
class ChangesLogAPISerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')

    class Meta:
        model = Change
        fields = '__all__'


class LoginDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginDetails
        fields = '__all__'

class ReportColumnsTemplatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportColumnsTemplates
        fields = '__all__'