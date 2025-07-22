from rest_framework import serializers
from .models import (Employee, EmployeeType, EmployeeSettings,EmployeeFamilyDetails)
from django.contrib.auth import authenticate
from accounts.models import User
from retailmasters.models import Branch
from models_logging.models import Change
from datetime import datetime, timedelta

from rest_framework.validators import UniqueValidator

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        
class EmployeeFamilyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeFamilyDetails
        fields = '__all__'

class EmployeeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeType
        fields ='__all__'
        
        
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields ='__all__'
        
        
class EmployeeSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSettings
        fields ='__all__'
        
class ChangesLogAPISerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')

    class Meta:
        model = Change
        fields = '__all__'

# Create Employee Serializer at Settings by Admin:
class CreateEmployeeSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField()
    lastname = serializers.CharField(default=None,)
    mobile = serializers.CharField(max_length=20, validators=[
        UniqueValidator(queryset=Employee.objects.all(),
                        message=("Mobile Number Already exists"))
    ])

    emp_type = serializers.SlugRelatedField(
        queryset=EmployeeType.objects.all(), slug_field='id_employee_type',
        error_messages={
            'does_not_exist': 'Selected Employee Type does not exist.',
        }
    )
    login_branches = serializers.ListField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email',
                  'account_expiry', 'is_active', 'password', 'firstname', 'lastname', 'mobile', 'emp_type', 'login_branches']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def checkbranch(self, data):

        branches = []

        for each in data['login_branches']:
            try:
                branch = Branch.objects.get(id_branch=each)
                branches.append(branch)
            except Branch.DoesNotExist:
                pass

        data.update({"login_branches": branches})
        return data

    def save(self, data, **kwargs):
        user = User(
            username=self.validated_data['username'], email=self.validated_data['email'], is_active=self.validated_data['is_active'], account_expiry=self.validated_data['account_expiry'])
        user.is_adminuser = True
        user.set_password(self.validated_data['password'])
        user.save()

        emp = Employee(firstname=self.validated_data['firstname'], user=user,
                       lastname=self.validated_data.get('lastname'), mobile=self.validated_data.get('mobile'), emp_type=self.validated_data.get('emp_type'))

        emp.save()
        for each in self.validated_data['login_branches']:
            emp.login_branches.add(each)

        return user, emp

class EmployeeSignupSerializer(serializers.ModelSerializer):
    # password2 = serializers.CharField(style={"input_type": "password"},
    #                                   write_only=True)
    # admin_alert_before = serializers.CharField(
    #     source='adminuser.admin_alert_before', required=True)
    # admin_pay_alert = serializers.BooleanField(
    #     source='adminuser.admin_pay_alert', required=True)
    # admin_security_code = serializers.IntegerField(
    #     source='adminuser.admin_security_code', required=True)
    # groups = serializers.ListField(required=True)

    # id_branch = serializers.IntegerField(source='employee.id_branch')
    login_branches = serializers.ListField(allow_null=True)
    # login_companies = serializers.ListField(allow_null=True,)
    lastname = serializers.CharField(
        source='employee.lastname',
        max_length=32,
    )
    firstname = serializers.CharField(
        source='employee.firstname',
        max_length=32,
    )
    # date_of_birth = serializers.DateField(source='employee.date_of_birth')
    emp_code = serializers.CharField(
        source='employee.emp_code',
        max_length=20,
    )
    # dept = serializers.IntegerField(source='employee.dept')
    # designation = serializers.IntegerField(source='employee.designation')
    # date_of_join = serializers.DateField(source='employee.date_of_join')
    # email = serializers.EmailField(max_length=128, blank=True, null=True)
    mobile = serializers.CharField(max_length=20, source='employee.mobile')
    # phone = models.CharField(max_length=30, blank=True, null=True)
    # image = models.CharField(max_length=100, blank=True, null=True)
    # comments = models.CharField(max_length=200, blank=True, null=True)
    # username = models.CharField(max_length=30, blank=True, null=True)
    # passwd = models.CharField(max_length=32, blank=True, null=True)
    # id_profile = serializers.IntegerField(source='employee.id_profile')
    active = serializers.BooleanField(source='employee.active', required=False)
    # date_add = models.DateTimeField(blank=True, null=True)
    # date_upd = models.DateTimeField(blank=True, null=True)
    emp_type = serializers.IntegerField()

    # is_staff = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = '__all__'
        # fields = [
        #     'username', 'email', 'company_name', 'description', 'password',
        #     'password2'
        # ]
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }  # to be used for entry in DEFAULT AUTH USER MODEL

    def save(self, **kwargs):
        user = User(
            username=self.validated_data['username'],
            email=self.validated_data['email'],
            account_expiry=datetime.now() +
            timedelta(days=365),  # account expiry set[1 year]
            # is_staff=self.validated_data['is_staff']
        )

        password = self.validated_data['password']

        user.set_password(password)  # password is set for the user

        # user is set to be Employee ; since it is created via create/signup employee API
        user.is_adminuser = True
        # if (self.validated_data['is_staff']) :

        # # if (self.validated_data['password'] =! None) :
        #     user.is_staff=True

        user.save()  # user is saved

        admin_data = self.validated_data.pop(
            'employee')  # datas related to employee is popped out
        try:
            emp_type = EmployeeType.objects.get(
                id_employee_type=self.validated_data['emp_type'])
        except EmployeeType.DoesNotExist:
            emp_type = None

        adminuser = Employee.objects.create(
            user=user, emp_type=emp_type, **admin_data
        )  # employee is created with user -now created as a One-to-One relation and filled with the required fields for the employee table

        # adminuser.company_name=self.validated_data['company_name']
        # adminuser.description=self.validated_data['description']
        adminuser.login_companies.set(self.validated_data['login_companies'])
        adminuser.login_branches.set(self.validated_data['login_branches'])
        adminuser.save()
        return user
    
# serializer for Employee Login
class EmployeeLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    id_company = serializers.IntegerField()
    # id_branch = serializers.IntegerField()

    def validate(self, data):
        todays_date = datetime.today().date()
        user = authenticate(**data)
        #print("user", user)
        # if user.is_active == False:
        #     raise serializers.ValidationError('User is Inactive')
        if user:
            if todays_date <= user.account_expiry:
                if user.is_active:
                    if user.is_adminuser:
                        return user
                    raise serializers.ValidationError(
                        {"error_detail": 'Admin/Employee Not Found'})
                raise serializers.ValidationError(
                    {"error_detail": 'User Inactive'})
            raise serializers.ValidationError(
                {"error_detail": "Your Account has Expired. Please Contact Admin"})
        raise serializers.ValidationError(
            {"error_detail": 'Incorrect username/password'})


