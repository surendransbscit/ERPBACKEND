from django.db import models
from datetime import datetime, timedelta, date
import os

from accounts.models import User
# Create your models here.


# model to store the customer{Customer} [+ acts as a sub table of the DEFAULT AUTH USER MODEL w.th relation specified to it]
class CustomerAddress(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.OneToOneField('Customers', on_delete= models.PROTECT)
    line1 = models.TextField(blank=True,default=None)
    line2 = models.TextField(null=True,blank=True,default=None)
    line3 = models.TextField(null=True,blank=True,default=None)
    pincode = models.CharField(max_length = 6,blank=True,null=True,default=None)
    country = models.ForeignKey('retailmasters.Country', on_delete=models.PROTECT, null=True)
    state=models.ForeignKey('retailmasters.State',on_delete=models.PROTECT, null=True)
    city=models.ForeignKey('retailmasters.City',on_delete=models.PROTECT, null=True)
    area = models.ForeignKey('retailmasters.Area', on_delete=models.PROTECT, null=True)
    
    
    class Meta:
        # managed = False
        db_table = 'customer_address'
        
def upload_pic(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/customers/{id}{title}{ext}'.format(id=instance.mobile, title=datetime.now().strftime('%Y%m%d%H%M%S'), ext=file_extension)


class TempCustomers(models.Model):
    id_customer = models.AutoField(primary_key=True)
    # user = models.OneToOneField(User,
    #                             related_name="temp_customer",
    #                             on_delete=models.CASCADE,
    #                             null=True)
    confirm_password = models.CharField(max_length=155, null=True, default=None)
    email = models.EmailField(blank=True,null=True)
    mob_code = models.CharField(max_length=15, default="+91")
    title = models.CharField(max_length=5, null=True)
    lastname = models.CharField(max_length=32, null=True)
    firstname = models.CharField(max_length=32, null=True,verbose_name='Customer Name')
    company_name = models.CharField(max_length=32, default=None,blank=True,null=True,verbose_name='Company Name')
    date_of_birth = models.DateField(null=True)
    date_of_wed = models.DateField(null=True)
    gender = models.CharField(choices=[(1, 'Male'),(2, 'Female'), (3, 'Other')], max_length = 10, null=True)
    mobile = models.CharField(unique=True,max_length=255,null=True,verbose_name='Mobile')
    gst_number = models.CharField(max_length=255, null=True,blank=True)
    pan_number = models.CharField(max_length=255, null=True,blank=True)
    aadhar_number = models.CharField(max_length=255, null=True)
    registered_through = models.CharField(choices=[(1, 'Admin'),(2, 'Mobile App'),
                                           (3, 'Collection App')], max_length = 10, default = '1')
    approved_through = models.IntegerField(choices=[(1, 'Admin'),(2, 'Mobile App')], default = 1)
    cus_type = models.CharField(max_length = 60,  choices=(
        ("1", "Individual"), ("2", "Company")), default=1)
    class Meta:
        # managed = False
        db_table = 'temp_customers'
        unique_together = (('id_customer', 'firstname', 'lastname',
                            'mobile'), )

class Customers(models.Model):
    id_customer = models.AutoField(primary_key=True)
    user = models.OneToOneField(User,
                                related_name="customer",
                                on_delete=models.CASCADE,
                                null=True)
    email = models.EmailField(unique=True, blank=True,null=True)
    mob_code = models.CharField(max_length=15, default="+91")
    reference_no = models.CharField(unique=True, max_length=100, null=True)
    id_branch = models.IntegerField(null=True)
    id_area = models.IntegerField(null=True)
    title = models.CharField(max_length=5, null=True)
    lastname = models.CharField(max_length=32, null=True)
    firstname = models.CharField(max_length=32, null=True,verbose_name='Customer Name')
    company_name = models.CharField(max_length=32, default=None,blank=True,null=True,verbose_name='Company Name')
    date_of_birth = models.DateField(null=True)
    date_of_wed = models.DateField(null=True)
    gender = models.CharField(choices=[(1, 'Male'),(2, 'Female'), (3, 'Other')], max_length = 10, null=True)
    # address = models.ForeignKey(CustomerAddress, on_delete = models.PROTECT, null = True)
    # email = models.CharField(max_length=128, blank=True, null=True)  ##??
    mobile = models.CharField(unique=True,max_length=255,null=True,verbose_name='Mobile')
    phone_no = models.CharField(
        max_length=20, blank=True, null=True, default=None)
    cus_img = models.ImageField(upload_to=upload_pic, null=True)
    profession = models.ForeignKey('retailmasters.Profession', on_delete=models.PROTECT,null=True, default=None)
    comments = models.CharField(max_length=200, null=True)
    profile_complete = models.IntegerField(null=True)
    active = models.BooleanField(default=True)
    # is_approved = models.BooleanField(default=True)
    approved_status = models.IntegerField(choices=[(1, 'Pending'),(2, 'Approved'), (3, 'Rejected')], default = 1)
    date_add = models.DateTimeField( null=True)
    custom_entry_date = models.DateField(auto_now_add=date.today(), null=True)
    date_upd = models.DateTimeField(null=True)
    notification = models.BooleanField(default=True)
    gst_number = models.CharField(max_length=255, null=True,blank=True)
    pan_number = models.CharField(max_length=255, null=True,blank=True)
    aadhar_number = models.CharField(max_length=255, null=True)
    cus_ref_code = models.CharField(max_length=45, null=True)
    is_refbenefit_crt_cus = models.BooleanField(default=False, null=True)
    emp_ref_code = models.CharField(max_length=45, null=True)
    is_refbenefit_crt_emp = models.BooleanField(default=False, null=True)
    religion = models.IntegerField(null=True)
    kyc_status = models.BooleanField(default=False,null=True)
    is_cus_synced = models.BooleanField(default=False)  # ???
    last_sync_time = models.DateTimeField(null=True)
    last_payment_on = models.DateTimeField(null=True)
    is_vip = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    debit_balance = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    registered_through = models.CharField(choices=[(1, 'Admin'),(2, 'Mobile App'),
                                           (3, 'Collection App')], max_length = 10, default = '1')
    approved_through = models.IntegerField(choices=[(1, 'Admin'),(2, 'Mobile App')], default = 1)
    catalogue_req_status = models.IntegerField(choices=[(0,'dont show catalogue'),(1, 'Pending'),(2, 'Approved'), (3, 'Rejected')], default = 2)
    cus_type = models.CharField(max_length = 60,  choices=(
        ("1", "Individual"), ("2", "Company")), default=1)
    send_promo_sms = models.BooleanField(default=False)
    is_retailer = models.CharField(max_length = 60,  choices=(
        ("1", "Yes"), ("0", "No")), default=0)
    retailer_type = models.CharField(max_length = 60,  choices=(
        ("1", "Retail "), ("0", "Vip Retail")), default=0)
    profile_type = models.CharField(max_length = 60,  choices=(
         ("0", "None"),("1", "Retail"), ("2", "Vip Retail")), default=0)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='cus_by_user', on_delete=models.PROTECT,null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='cus_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)
    catalogue_visible_type = models.IntegerField(choices=[(0, 'Life Time'),(1, 'Limited')], default = 0)
    show_catalogue_date = models.DateTimeField(null=True,default=None,blank=True)
    class Meta:
        # managed = False
        db_table = 'customers'
        unique_together = (('id_customer', 'firstname', 'lastname',
                            'mobile'), )
        indexes = [
            models.Index(fields=['mobile', 'id_customer']),  # Composite index
        ]

    LOGGING_IGNORE_FIELDS=('created_on','created_by',"updated_on","updated_by")   
    
class CustomerFamilyDetails(models.Model):
    id_family_detail = models.BigAutoField(primary_key=True) 
    customer = models.ForeignKey('Customers', on_delete= models.PROTECT)
    relation_type = models.ForeignKey('retailmasters.RelationType', on_delete= models.PROTECT,default=None,null=True)
    profession = models.ForeignKey('retailmasters.Profession', on_delete=models.PROTECT,default=None,null=True)
    name = models.CharField(max_length=255)
    mobile = models.CharField(unique=True,max_length=20,null=True,verbose_name='relation_mobile')
    date_of_birth = models.DateField(null=True)
    date_of_wed = models.DateField(null=True)
    
    def __str__(self):
        return f"{self.name}, Relation of {self.customer.id_customer} - {self.customer.firstname}"
    
    class Meta:
        db_table = 'customer_family_details'

class CustomerKYC(models.Model):
    id_cus_kyc = models.AutoField(primary_key=True)
    id_cus_kyc_cusid = models.ForeignKey('Customers',
                             on_delete=models.CASCADE,
                             related_name="cus_kyc_cusid")
    kyc_pro_type = models.IntegerField(blank=True, null=True)
    kyc_pro_id = models.CharField(max_length=50, blank=True, null=True)
    kyc_proof_img = models.CharField(max_length=50, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='cus_kyc_by_user', on_delete=models.PROTECT,null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='cus_kyc_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)
    class Meta:
        db_table = 'customerkyc'
        
    LOGGING_IGNORE_FIELDS=('created_on','created_by',"updated_on","updated_by") 

class CustomerNominee(models.Model):
    id_cus_nominee = models.AutoField(primary_key=True)
    id_nominee_cusid = models.OneToOneField('Customers',
                             on_delete=models.CASCADE,
                             related_name="cus_nominee_cusid")
    nominee_name = models.CharField(max_length=50, blank=True, null=True)
    nominee_relationship = models.CharField(max_length=32,
                                            blank=True,
                                            null=True)
    nominee_date_of_birth = models.DateField(blank=True, null=True)
    nominee_date_of_wed = models.DateField(blank=True, null=True)
    nominee_mobile = models.CharField(max_length=20, blank=True, null=True)
    # created_on = models.DateTimeField(auto_now_add=datetime.now())
    # created_by = models.ForeignKey(
    #     'accounts.User', related_name='cus_nominee_by_user', on_delete=models.PROTECT,null=True)
    # updated_by = models.ForeignKey(
    #     'accounts.User', related_name='cus_nominee_updated_by_user', null=True, on_delete=models.SET_NULL)
    # updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'customernominee'
        
    LOGGING_IGNORE_FIELDS=('created_on','created_by',"updated_on","updated_by") 

class CustomerNomineeProof(models.Model):
    id_cus_nom_prof = models.AutoField(primary_key=True)
    id_cus_nom_id   = models.ForeignKey('CustomerNominee',
                             on_delete=models.CASCADE,
                             related_name="cus_nominee_cusid")
    nom_pro_type = models.IntegerField(blank=True, null=True)
    nom_pro_id = models.CharField(max_length=50, blank=True, null=True)
    proof_img = models.CharField(max_length=50, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='cus_nominee_proof_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='cus_nominee_proof_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)
    class Meta:
        db_table = 'customernomineeproof'
        
    LOGGING_IGNORE_FIELDS=('created_on','created_by',"updated_on","updated_by") 
    
class CustomerLoginPin(models.Model):
    id = models.AutoField(primary_key=True)
    pin = models.CharField(max_length=4)
    user = models.OneToOneField(
        'accounts.User', on_delete=models.PROTECT, limit_choices_to={'is_customer': True}, related_name='cus_pin')
    customer = models.OneToOneField('Customers', on_delete=models.PROTECT)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'cus_login_pin'
        
class CustomerDeviceIdMaster(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    deviceID = models.CharField(max_length=255)
    subscription_id = models.TextField(blank=True,default=None)
    is_active = models.BooleanField()
    
    def __str__(self):
        return f"Notification of {self.deviceID} with {self.customer.firstname}"
    
    class Meta:
        db_table = 'customer_deviceid_master'
        

class CustomerEnquiry(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey('customers.Customers', on_delete=models.CASCADE, related_name='enquiry_customer')
    enquiry_date = models.DateField()
    metal = models.IntegerField(choices=[(1, 'Gold'), (2, 'Silver')])
    product = models.ForeignKey('retailcataloguemasters.Product', on_delete=models.CASCADE, null=True, default=None)
    design = models.ForeignKey('retailcataloguemasters.Design', on_delete=models.CASCADE, null=True, default=None)
    weight_range = models.ForeignKey('retailmasters.WeightRange', on_delete=models.CASCADE, null=True, default=None)
    size = models.ForeignKey('retailmasters.Size', on_delete=models.CASCADE, null=True, default=None)
    gender = models.IntegerField(choices=[(1, 'Male'),(2, 'Female'), (3, 'Transgender')], null=True)
    # weight_range_from = models.DecimalField(max_digits=10, decimal_places=3, default=0.00)
    # weight_range_to = models.DecimalField(max_digits=10, decimal_places=3, default=0.00)
    replied_by = models.ForeignKey('accounts.User', related_name='enquiry_replied_by', null=True, on_delete=models.SET_NULL, default=None)
    status = models.IntegerField(choices=[(1, 'Open'), (2, 'Replied')], default=1)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'customer_enquiry'