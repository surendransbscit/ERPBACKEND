from django.db import models
from datetime import datetime, timedelta

from accounts.models import User
from retailmasters.models import Branch
from retailcataloguemasters.models import Section
import os



def upload_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/employees/{id}{title}{ext}'.format(id=instance.user.username, title=datetime.now().strftime('%Y%m%d%H%M%S'), ext=file_extension)

def upload_sign_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/employees/signature/{id}{title}{ext}'.format(id=instance.user.username, title=datetime.now().strftime('%Y%m%d%H%M%S'), ext=file_extension)

# employee type -> different categories of employees
class EmployeeType(models.Model):
    id_employee_type = models.AutoField(primary_key=True)
    employee_type = models.CharField(max_length=45)

    class Meta:
        db_table = 'erpemployee_type'


class Employee(models.Model):
    id_employee = models.AutoField(primary_key=True)
    user = models.OneToOneField(User,
                                limit_choices_to={'is_adminuser': True},
                                related_name="employee",
                                on_delete=models.CASCADE,
                                null=True)
    email = models.EmailField(unique=True, null=True,default=None, blank=False)
    email_verified = models.BooleanField(default=False)
    mob_code = models.CharField(max_length=15, default="+91")
    id_branch= models.IntegerField(blank=True, null=True)
    login_branches = models.ManyToManyField(Branch, blank=True, related_name='employees')
    lastname = models.CharField(max_length=32, blank=True, null=True)
    firstname = models.CharField(max_length=32)
    date_of_birth = models.DateField(blank=True, null=True)
    emp_code = models.CharField(max_length=20, blank=True, null=True)
    dept = models.ForeignKey("retailmasters.Department", on_delete=models.PROTECT, null = True)
    designation = models.ForeignKey("retailmasters.Designation", on_delete=models.PROTECT, blank=True,null = True)
    date_of_join = models.DateField(blank=True, null=True)
    mobile = models.CharField(max_length=20, null=True,default=None,blank=True)
    image = models.ImageField(upload_to=upload_image, null=True)
    signature = models.ImageField(upload_to=upload_sign_image, null=True)
    comments = models.CharField(max_length=200, blank=True, null=True)
    id_profile = models.ForeignKey('retailmasters.Profile',
                                 related_name="employee_profile",
                                 on_delete=models.PROTECT,
                                 null=True)
    is_developer = models.BooleanField(default=False, null=True)
    is_system_user = models.BooleanField(default=False)
    date_add = models.DateTimeField(auto_now_add=datetime.now)
    date_upd = models.DateTimeField(auto_now=datetime.now())
    emp_type = models.ForeignKey(EmployeeType,
                                 related_name="employee_emptype",
                                 on_delete=models.PROTECT, null=True, default=None)
    address1 = models.TextField(null=True,blank=True,default=None)
    address2 = models.TextField(null=True,blank=True,default=None)
    address3 = models.TextField(null=True,blank=True,default=None)
    pincode = models.CharField(max_length = 6,null=True,blank=True,default=None)
    country = models.ForeignKey('retailmasters.Country', on_delete=models.PROTECT, null=True)
    state=models.ForeignKey('retailmasters.State',on_delete=models.PROTECT, null=True)
    city=models.ForeignKey('retailmasters.City',on_delete=models.PROTECT, null=True)
    area = models.ForeignKey('retailmasters.Area', on_delete=models.PROTECT, null=True)
    section = models.ManyToManyField(Section, blank=True, related_name='employee_section')
    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    class Meta:
        # managed = False
        db_table = 'erpemployee'

    LOGGING_IGNORE_FIELDS = ('date_upd', )
    

class EmployeeFamilyDetails(models.Model):
    id_family_detail = models.BigAutoField(primary_key=True) 
    employee = models.ForeignKey(Employee, on_delete= models.PROTECT)
    relation_type = models.ForeignKey('retailmasters.RelationType', on_delete= models.PROTECT,default=None,null=True)
    profession = models.ForeignKey('retailmasters.Profession', on_delete=models.PROTECT,default=None,null=True)
    name = models.CharField(max_length=255)
    mobile = models.CharField(unique=True,max_length=20,null=True,verbose_name='relation_mobile')
    date_of_birth = models.DateField(null=True)
    date_of_wed = models.DateField(null=True)
    
    def __str__(self):
        return f"{self.name}, Relation of {self.employee.id_employee} - {self.employee.firstname}"
    
    class Meta:
        db_table = 'employee_family_details'
    
    
class EmployeeSettings(models.Model):
    id = models.AutoField(primary_key=True)
    id_employee = models.OneToOneField(Employee, on_delete=models.PROTECT)
    disc_limit_type =  models.CharField(max_length=45, choices=(("1", "Amount"), ("2", "Percent")))
    disc_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    allow_pur_det_add_in_pur_entry = models.BooleanField(default = False)
    allow_branch_transfer = models.BooleanField(default = False)
    allow_day_close = models.BooleanField(default = False)
    access_time_from = models.TimeField(null = True)
    access_time_to = models.TimeField(null = True)
    menu_style =  models.IntegerField(choices=((1, "Sidebar Menu"), (2, "Header Menu")), default=1)
    is_show_full_mobile = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='emp_settings_by_user', on_delete=models.PROTECT)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='emp_settings_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return 'Employee Settings (ID %s) ' % (self.id )

    class Meta:
        db_table = 'emp_settings'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')