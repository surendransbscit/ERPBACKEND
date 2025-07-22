from django.db import models
from employees.models import EmployeeType, Employee 
from django.utils import timezone
# Create your models here.

# function to manage branch image upload to corresponding folders
def upload_to_gal(instance, filename):
    return 'images/retail_catalog/category/{filename}'.format(
        filename=filename)


def upload_prod_img(instance, filename):
    return 'images/retail_catalog/product/{filename}'.format(filename=filename)


def upload_subdesignmapping_img(instance, filename):
    return 'images/retail_catalog/subdesignmapping/{filename}'.format(
        filename=filename)



# menu model is used to store the menu - side menus -- with permisssions set to users/ categories to view w.r.t to their login
class Menu(models.Model):
    text = models.CharField(max_length=45)
    link = models.CharField(max_length=75, null=True, blank=True, default="#")
    icon = models.CharField(max_length=85, null=True, blank=True)
    # ownership = models.ManyToManyField(EmployeeType, through='MenuAccess')
    parent = models.ForeignKey(
        'Menu', null=True, blank=True, default=None, on_delete=models.SET_NULL)
    order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    sub = models.BooleanField(default=False)
    title = models.CharField(max_length=125, null=True)
    save_value_by = models.CharField(max_length = 60,  choices=(
        ("1", "First letter as caps"), ("2", "All letters as caps")), default=1)

    # grp = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "menu"


# give access to particular menu listing/ and add,delete,edit accesses, for Employee Types / Groups
# class MenuAccess(models.Model):
#     id_menu_access = models.AutoField(primary_key=True)
#     emp_type = models.ForeignKey(EmployeeType,
#                                  on_delete=models.CASCADE,
#                                  related_name="access_emptype")
#     menu = models.ForeignKey(Menu,
#                              on_delete=models.CASCADE,
#                              related_name="access_menu_item")
#     view = models.BooleanField(default=False)
#     add = models.BooleanField(default=False)
#     edit = models.BooleanField(default=False)
#     delete = models.BooleanField(default=False)

#     class Meta:
#         db_table = "menu_group_access"


class EmpMenuAccess(models.Model):
    id_menu_emp_access = models.AutoField(primary_key=True)
    # emp = models.ForeignKey(Employee,
    #                         on_delete=models.CASCADE,
    #                         related_name="menu_access", null=True, default=None)
    profile = models.ForeignKey('retailmasters.Profile',
                            on_delete=models.CASCADE,
                            related_name="profile_menu_access", null=True, default=None)
    menu = models.ForeignKey('Menu',
                             on_delete=models.CASCADE,
                             related_name="access_emp")
    view = models.BooleanField(default=False)
    add = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    print = models.BooleanField(default=False)
    export = models.BooleanField(default=False)

    class Meta:
        db_table = "menu_emp_access"
        
        

# Admin OTP model is used to store Email OTPs of user
class EmployeeOTP(models.Model):

    OTP_FOR = (
        ("0", "Password Reset OTP"),
        ("1", "Profile Email Change OTP"),
        ("2", "Email Verify OTP"),
        ("3", "Login OTP"),
        ("4", "Bill Cancel OTP"),
        ("5", "Multi-Tag Print OTP"),
        ("6", "Payment Cancel OTP"),
        ("7", "Account Closing OTP"),
    )

    id_otp = models.BigAutoField(primary_key=True)
    employee = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE, related_name='otp_set')
    email_id = models.EmailField()
    otp_code = models.CharField(
        max_length=6)
    creation_time = models.DateTimeField(default=timezone.now)
    expiry = models.DateTimeField()
    otp_for = models.CharField(choices=OTP_FOR, max_length=1)

    def __str__(self) -> str:
        return 'Admin User OTP - ' + str(self.pk)

    class Meta:
        db_table = 'employee_otp'
    # LOG IGNORE THIS MODEL
    
class TempCustomerOtp(models.Model):

    OTP_FOR = (
        (1, "Registration OTP"),
    )

    id_otp = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(
        'customers.TempCustomers', on_delete=models.CASCADE, related_name='temp_customer_otp')
    email_id = models.EmailField(null=True)
    otp_code = models.CharField(max_length=6)
    creation_time = models.DateTimeField(default=timezone.now)
    expiry = models.DateTimeField()
    otp_for = models.IntegerField(choices=OTP_FOR)

    def __str__(self) -> str:
        return 'Customer User OTP - ' + str(self.pk)

    class Meta:
        db_table = 'temp_customer_otp'
        
class CustomerOTP(models.Model):

    OTP_FOR = (
        (1, "Forgot Password OTP"),
        (2, "Profile Email Change OTP"),
        (3, "Email Verify OTP"),
    )

    id_otp = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(
        'customers.Customers', on_delete=models.CASCADE, related_name='customer_otp')
    email_id = models.EmailField()
    otp_code = models.CharField(max_length=6)
    creation_time = models.DateTimeField(default=timezone.now)
    expiry = models.DateTimeField()
    otp_for = models.IntegerField(choices=OTP_FOR)

    def __str__(self) -> str:
        return 'Customer User OTP - ' + str(self.pk)

    class Meta:
        db_table = 'customer_otp'


class LoginDetails(models.Model):
    detail_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('accounts.User',
                             on_delete=models.CASCADE)
    is_mobile = models.BooleanField(default=False)
    is_tablet = models.BooleanField(default=False)
    is_touch_capable = models.BooleanField(default=False)
    is_pc = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)
    browser_fam = models.CharField(max_length=50)
    browser_ver = models.CharField(max_length=50)
    os_fam = models.CharField(max_length=50)
    os_ver = models.CharField(max_length=50)
    device_fam = models.CharField(max_length=50)
    device_brand = models.CharField(max_length=50, null=True)
    ip_address = models.CharField(max_length=50)
    signin_time = models.DateTimeField()

    def __str__(self) -> str:
        return 'Login Device Details - ' + str(self.pk)

    class Meta:
        db_table = "login_details"

class ReportColumnsTemplates(models.Model):
    id_menu_col = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='user_col', null=True, default=None)
    columns = models.TextField()
    menu = models.ForeignKey(Menu,
                             on_delete=models.CASCADE,
                             related_name="menu_col")
    class Meta:
        db_table = "report_columns_templates"