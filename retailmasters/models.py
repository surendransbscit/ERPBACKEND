from django.db import models
from datetime import datetime, date, timedelta
import os
import uuid
from retailcataloguemasters.models import (
    Product, Metal, Purity, Design, SubDesign)
from django.core.files.images import get_image_dimensions
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from schememaster.models import (Scheme)
from  utilities.model_utils import CommonFields

# from core.models import upload_to_gal

# Create your models here.
# function to manage branch image upload to corresponding folders


def upload_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/company/{id}{title}{ext}'.format(id=instance.company_name, title=datetime.now().strftime('%Y%m%d%H%M%S'), ext=file_extension)


def upload_to_gal(instance, filename):
    return 'images/retailmasters/branch/{filename}'.format(
        filename=filename)


def upload_pic(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/retailmasters/branch/{title}{ext}'.format(title=instance.name, ext=file_extension)

def upload_notification_img(instance, filename):
    unique_id = uuid.uuid4()
    _, file_extension = os.path.splitext(filename)
    return 'images/retailmasters/cus_notification/{id}_{title}{ext}'.format(title=instance.title, id=unique_id, ext=file_extension)

def upload_daily_status_img(instance, filename):
    unique_id = uuid.uuid4()
    _, file_extension = os.path.splitext(filename)
    return 'images/retailmasters/daily_status/{id}{ext}'.format(id=unique_id, ext=file_extension)


def upload_daily_status_audio(instance, filename):
    """Function to generate file path for order voice notes."""
    _, file_extension = os.path.splitext(filename)
    unique_id = uuid.uuid4()
    return 'audios/retailmasters/daily_status/{id}{ext}'.format(id=unique_id, ext=file_extension)


def upload_daily_status_video(instance, filename):
    """Function to generate file path for order voice notes."""
    _, file_extension = os.path.splitext(filename)
    unique_id = uuid.uuid4()
    return 'videos/retailmasters/daily_status/{id}{ext}'.format(id=unique_id, ext=file_extension)


def upload_supplier_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/retailmasters/supplier/{title}{ext}'.format(title=instance.short_code, ext=file_extension)


def upload_customer_aadhar_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/retailmasters/customerproof/{title}{ext}'.format(title=instance.aadhar_number, ext=file_extension)


def upload_customer_application_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/retailmasters/customerproof/{title}{ext}'.format(title=instance.aadhar_number, ext=file_extension)


def Banner_image_restriction(image):
    image_width, image_height = get_image_dimensions(image)
    if image_width != 640 or image_height != 320:
        raise ValidationError(
            'Image width needs to be 640px and height needs to be 320px ')


def upload_banner(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/retailmasters/banners/{title}{ext}'.format(
        title=instance.banner_name, ext=file_extension)


def upload_supplier_product_details_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'supplier_product/supplier_product_detail_{det_id}/{id}{ext}'.format(det_id=instance.supplier_product_details.id,
                                                                                id=instance.id, title=datetime.now().strftime('%Y%m%d%H%M%S'),
                                                                                ext=file_extension)


AMOUNTORPERCENT_TYPE_CHOICES = [
    (1, 'Amount'),
    (2, '%'),
]


class ERPOrderStatus(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.BooleanField(default=True)
    colour = models.CharField(max_length=255, null=True, default=None)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='order_status_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='order_status_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return 'Order Status - ' + str(self.pk)

    class Meta:
        db_table = 'erp_order_status'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    

class ERPInternalOrderStatus(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.BooleanField(default=True)
    colour = models.CharField(max_length=255, null=True, default=None)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='internal_order_status_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='internal_order_status_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return 'Internal Order Status - ' + str(self.pk)

    class Meta:
        db_table = 'erp_internal_order_status'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    


# model to store the multi-tenant architecture
class Tenant(models.Model):
    tenantid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='tenant_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='tenant_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'tenant'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


# model to store branches of a company:
class Branch(models.Model):
    id_branch = models.AutoField(primary_key=True)
    id_company = models.ForeignKey(
        'Company', on_delete=models.PROTECT, related_name='company_branches', )
    show_to_all = models.CharField(max_length=15,
                                   choices=(("0", "Own"), ("1", "All"),
                                            ("2", "All Cus Only"),
                                            ("3", "All Emp Only")),
                                   default="0")
    name = models.CharField(
        max_length=45,
        unique=True,
        error_messages={"unique": "Branch Name already Exists"})
    warehouse = models.CharField(max_length=45, blank=True, null=True)
    expo_warehouse = models.CharField(max_length=45, blank=True, null=True)
    active = models.BooleanField(default=1)
    short_name = models.CharField(
        max_length=10,
        unique=True,
        error_messages={"unique": "Branch Short Name is Unavailable"})
    email = models.EmailField(blank=True, null=True)
    address1 = models.CharField(max_length=45, blank=True, null=True)
    address2 = models.CharField(max_length=45, blank=True, null=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT)
    state = models.ForeignKey('State', on_delete=models.PROTECT)
    city = models.ForeignKey('City', on_delete=models.PROTECT)
    phone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    mob_code = models.CharField(max_length=15, default="+91")
    cusromercare = models.CharField(max_length=10, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    metal_rate_type = models.CharField(max_length=15,
                                       choices=(
                                           ("0", "Manual"),
                                           ("1", "Automatic"),
                                           ("2", "Partial"),
                                       ),
                                       default="0")
    logo = models.ImageField(upload_to=upload_pic, blank=True, null=True)
    map_url = models.TextField(blank=True, null=True)
    fb_link = models.TextField(blank=True, null=True)
    insta_link = models.TextField(blank=True, null=True)
    sort = models.IntegerField(blank=True, null=True)
    otp_verif_mobileno = models.CharField(max_length=45, blank=True, null=True)
    branch_type = models.CharField(max_length=15,
                                   choices=(
                                       (1, "Store"),
                                       (2, "Customer Service"),
                                   ),
                                   blank=True,
                                   null=True)
    is_ho = models.BooleanField(default=0)
    note = models.CharField(max_length=250, blank=True, null=True)
    gst_number = models.TextField(blank=True, null=True)

    class Meta:

        db_table = 'branch'


# model to store the countries data[pre-filled]
class Country(models.Model):
    id_country = models.AutoField(primary_key=True)
    shortname = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=150)
    currency_name = models.CharField(max_length=50)
    currency_code = models.CharField(max_length=4)
    mob_code = models.CharField(max_length=5)
    mob_no_len = models.PositiveIntegerField()
    date_upd = models.DateField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'accounts.User', related_name='country_by_user', on_delete=models.PROTECT, null=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='country_updated_by_user', null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'country'


# model to store the states data[pre-filled]
class State(models.Model):
    id_state = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    country = models.ForeignKey('Country', on_delete=models.PROTECT)
    is_default = models.BooleanField(default=False)
    state_code = models.CharField(blank=True, null=True,max_length=30)
    created_by = models.ForeignKey(
        'accounts.User', related_name='state_by_user', on_delete=models.PROTECT, null=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='state_updated_by_user', null=True, on_delete=models.SET_NULL)

    class Meta:
        # managed = False
        db_table = 'state'


class District(models.Model):
    id_district = models.AutoField(primary_key=True)
    district_name = models.CharField(max_length=50, unique=True)
    state = models.ForeignKey('State', on_delete=models.PROTECT)
    district_code = models.CharField(
        max_length=10, unique=True, null=True, blank=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='district_by_user', on_delete=models.PROTECT, null=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='district_updated_by_user', null=True, on_delete=models.SET_NULL)

    class Meta:
        # managed = False
        db_table = 'district'


# model to store the cities data[pre-filled]
class City(models.Model):
    id_city = models.AutoField(primary_key=True)
    state = models.ForeignKey('State', on_delete=models.PROTECT)
    name = models.CharField(max_length=30)
    # district = models.ForeignKey('District', on_delete=models.PROTECT)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'accounts.User', related_name='city_by_user', on_delete=models.PROTECT, null=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='city_updated_by_user', null=True, on_delete=models.SET_NULL)

    class Meta:
        # managed = False
        db_table = 'city'


class IndianPostal(models.Model):
    id_pincode = models.AutoField(primary_key=True)
    officename = models.CharField(max_length=128, blank=True, null=True)
    pincode = models.CharField(max_length=6, unique=True)
    taluk = models.CharField(max_length=30, blank=True, null=True)
    district = models.ForeignKey('District', on_delete=models.PROTECT)
    city = models.ForeignKey('City', on_delete=models.PROTECT)
    state = models.ForeignKey('State', on_delete=models.PROTECT)
    country = models.ForeignKey('Country', on_delete=models.PROTECT)

    class Meta:
        # managed = False
        db_table = 'indianpostal'


# model to store the company details or attributes
class Company(models.Model):
    id_company = models.AutoField(primary_key=True)
    id_tenant = models.ForeignKey(
        'Tenant', on_delete=models.PROTECT, related_name='tenant_company', blank=True, null=True)
    company_name = models.CharField(
        max_length=100,  unique=True, error_messages={"unique": "Company Name already Exists"})
    short_code = models.CharField(max_length=5, unique=True)
    comp_name_in_sms = models.CharField(max_length=45, unique=True)
    address1 = models.CharField(max_length=128, blank=True, null=True)
    address2 = models.CharField(max_length=128, blank=True, null=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT)
    state = models.ForeignKey('State', on_delete=models.PROTECT)
    city = models.ForeignKey('City', on_delete=models.PROTECT)
    pincode = models.CharField(max_length=12, blank=True, null=True)
    mob_code = models.CharField(max_length=15, default="+91")
    mobile = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    website = models.CharField(max_length=50, blank=True, null=True)
    bank_acc_number = models.CharField(max_length=45, blank=True, null=True)
    bank_name = models.CharField(max_length=120, blank=True, null=True)
    bank_acc_name = models.CharField(max_length=45, blank=True, null=True)
    bank_branch = models.CharField(max_length=100, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=45, blank=True, null=True)
    date_add = models.DateTimeField(auto_now_add=datetime.now)
    date_upd = models.DateTimeField(blank=True, null=True)
    phoneno = models.CharField(max_length=45, blank=True, null=True)
    mobileno = models.CharField(max_length=45, blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    cin_number = models.TextField(blank=True, null=True)
    whatsapp_no = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(upload_to=upload_image, null=True)

    class Meta:
        # managed = False
        db_table = 'company'

    LOGGING_IGNORE_FIELDS = ('date_upd', 'date_add')


# model to store various departments
class Department(models.Model):
    id_dept = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80)
    dept_code = models.CharField(max_length=10, unique=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='dept_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='dept_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    class Meta:
        # managed = False
        db_table = 'department'


# model to store various designations:
class Designation(models.Model):
    id_design = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='desg_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='desg_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    class Meta:
        # managed = False
        db_table = 'designation'

# Financial Year Model


class FinancialYear(models.Model):
    fin_id = models.AutoField(primary_key=True)
    fin_year_name = models.CharField(max_length=10, unique=True, error_messages={
                                     "unique": "Financial Year Name Already Exists"})
    fin_year_code = models.CharField(max_length=15, unique=True, error_messages={
                                     "unique": "Financial Year with this Code Already Exists"})
    fin_year_from = models.DateTimeField()
    fin_year_to = models.DateTimeField()
    fin_status = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='finyear_by_user', on_delete=models.PROTECT)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='finyear_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return 'Financial Year (ID %s) ' % (self.fin_id, )

    class Meta:
        # managed = False
        db_table = 'financial_year'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

# UOM model - Unit of measurement - Model


class Uom(models.Model):
    uom_id = models.AutoField(primary_key=True)
    uom_name = models.CharField(max_length=100, unique=True, error_messages={
                                'unique': "UOM name already exists"})
    uom_short_code = models.CharField(max_length=10, unique=True, error_messages={
                                      'unique': "UOM with short code already exists"})
    uom_status = models.BooleanField(default=True)
    divided_by_value = models.IntegerField(blank=True, null=True)
    is_default = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='uom_by_user', on_delete=models.PROTECT)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='uom_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return 'UOM (ID %s) ' % (self.uom_id, )

    class Meta:
        # managed = False
        db_table = 'uom'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


# Tax Master model - To save different kind of Taxes
class Taxmaster(models.Model):
    tax_id = models.AutoField(primary_key=True)
    tax_code = models.CharField(max_length=20, unique=True, error_messages={
        'unique': 'Tax with this code already exists'})
    tax_name = models.CharField(max_length=35, unique=True, error_messages={
        'unique': 'Tax with this name already exists'})
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, unique=True, error_messages={
                                         'unique': 'Tax with this percentage already exists'})
    tax_status = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='tax_by_user', on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    modified_by = models.ForeignKey(
        'accounts.User', related_name='tax_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    modified_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return 'Tax (ID %s) ' % (self.tax_id, )

    class Meta:
        # managed = False
        db_table = 'taxmaster'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'modified_time',
                             'modified_by')


# Tax Group model - To group different taxes to one
class Taxgroupmaster(models.Model):
    tgrp_id = models.AutoField(primary_key=True)
    tgrp_name = models.CharField(unique=True, max_length=35, error_messages={
                                 'unique': "Tax group with this name already exists"})
    tgrp_status = models.BooleanField(default=True)
    effective_date = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='taxgrp_by_user', on_delete=models.PROTECT)
    created_time = models.DateTimeField(auto_now_add=datetime.now())
    modified_by = models.ForeignKey(
        'accounts.User', related_name='taxgrp_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    modified_time = models.DateTimeField(blank=True, null=True)
    branch_code = models.CharField(max_length=35, blank=True, null=True)

    def __str__(self):
        return 'Tax Group (ID %s) ' % (self.tgrp_id, )

    class Meta:
        # managed = False
        db_table = 'ret_taxgroupmaster'

    LOGGING_IGNORE_FIELDS = ('created_time', 'created_by', 'modified_time',
                             'modified_by')


# Tax group items model - Sub model(/table) to store Items inside  each tax grp
class Taxgroupitems(models.Model):
    tgi_sno = models.AutoField(primary_key=True)
    tgi_tgrpcode = models.ForeignKey(
        Taxgroupmaster,
        on_delete=models.CASCADE,
    )
    tgi_taxcode = models.ForeignKey(
        Taxmaster,
        on_delete=models.PROTECT,
    )
    tgi_calculation = models.CharField(max_length=25,
                                       choices=(("1", 'base'), ("2",
                                                                'arrived')))
    tgi_type = models.CharField(max_length=25,
                                choices=(("1", 'add'), ("2", 'sub')))
    branch_code = models.CharField(max_length=35, blank=True, null=True)

    def __str__(self):
        return 'Tax Group Item (%s) of (%s) ' % (self.tgi_sno,
                                                 self.tgi_tgrpcode)

    class Meta:
        # managed = False
        db_table = 'taxgroupitems'


# Size model - assigned to products ( Produts and its different sizes )
class Size(models.Model):
    id_size = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)  # inch,MM,etc
    id_product = models.ForeignKey(
        Product, related_name='size_product', on_delete=models.PROTECT)
    value = models.CharField(max_length=20)  # 11.5 etc
    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='size_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='size_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    def __str__(self):
        return 'Size (ID %s) ' % (self.id_size, )

    class Meta:
        db_table = 'erp_size'
        unique_together = [[
            'value',
            'id_product',
            'name',
        ]]

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Currency(models.Model):
    id_currency = models.AutoField(primary_key=True, default=1)
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=5)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'currency'


class RelationType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return 'Relation Type - ' + str(self.pk)

    class Meta:
        db_table = 'relation_type'


class ExchangeRate(models.Model):
    id_exchange = models.AutoField(primary_key=True, default=1)
    from_currency = models.ForeignKey(
        Currency, related_name='exchange_rates_from', on_delete=models.CASCADE)
    to_currency = models.ForeignKey(
        Currency, related_name='exchange_rates_to', on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=6)

    class Meta:
        unique_together = ['from_currency', 'to_currency']
        db_table = 'exchangerate'

    def __str__(self):
        return f"{self.from_currency.code} to {self.to_currency.code}: {self.rate}"


class metalRatePurityMaster(models.Model):
    id = models.AutoField(primary_key=True)
    rate_field = models.CharField(max_length=150)
    id_purity = models.ForeignKey(
        Purity, on_delete=models.PROTECT, related_name='rate_purity_master_id_purity', null=True)
    id_metal = models.ForeignKey(
        Metal, on_delete=models.PROTECT, related_name='rate_purity_master_id_metal', null=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='rate_purity_master_created_by', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='rate_purity_master_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'metal_rate_purity_master'


class ErpService(models.Model):
    id_service = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255,)
    short_code = models.CharField(max_length=200, unique=True)
    send_sms = models.BooleanField(default=False)
    send_email = models.BooleanField(default=False)
    send_whatsapp = models.BooleanField(default=False)
    send_notification = models.BooleanField(default=False)
    dlt_id = models.TextField()
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='service_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='service_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        # managed = False
        db_table = 'erp_service'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Bank(models.Model):
    id_bank = models.AutoField(primary_key=True)
    branch = models.ForeignKey('retailmasters.Branch', related_name='bank_branch',
                               on_delete=models.PROTECT, null=True, default=None)
    branch_name = models.CharField(max_length=35, null=True, default=None)
    bank_name = models.CharField(max_length=35, null=False, blank=False)
    short_code = models.CharField(max_length=10, null=True, default=None)
    acc_name = models.CharField(max_length=45, blank=True, null=True)
    acc_number = models.CharField(max_length=45, blank=True, null=True)
    bank_for = models.PositiveIntegerField(default=0)
    ifsc_code = models.CharField(max_length=45, blank=True, null=True)
    acc_type = models.CharField(max_length=2, choices=(
        ("1", "Savings"), ("2", "Current Account")))
    upi_id = models.CharField(max_length=45, blank=True, null=True)
    is_active = models.BooleanField(default=1)
    is_default = models.BooleanField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='bank_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='bank_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        # managed = False
        db_table = 'bank'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class PaymentMode(models.Model):
    id_mode = models.AutoField(primary_key=True)
    mode_name = models.CharField(max_length=50, unique=True)
    short_code = models.CharField(max_length=50, unique=True)
    sort_order = models.IntegerField(default=None,null=True)
    show_to_pay = models.BooleanField(default=1)
    is_active = models.BooleanField(default=1)
    card_name_visibility = models.BooleanField(default=0)
    card_name_mandatory = models.BooleanField(default=0)
    device_type_visibility = models.BooleanField(default=0)
    device_type_mandatory = models.BooleanField(default=0)
    card_no_visibility = models.BooleanField(default=0)
    card_no_mandatory = models.BooleanField(default=0)
    approval_no_visibility = models.BooleanField(default=0)
    approval_no_mandatory = models.BooleanField(default=0)
    bank_visibility = models.BooleanField(default=0)
    bank_mandatory = models.BooleanField(default=0)
    pay_date_visibility = models.BooleanField(default=0)
    pay_date_mandatory = models.BooleanField(default=0)
    nb_type_visibility = models.BooleanField(default=0)
    nb_type_mandatory = models.BooleanField(default=0)
    shortcut = models.CharField(max_length=100, default="ctrl+f1")
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='payment_mode_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='payment_mode_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'paymentmode'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Profile(models.Model):
    id_profile = models.AutoField(primary_key=True)
    profile_name = models.CharField(max_length=50, unique=True)
    allow_acc_closing = models.BooleanField(default=0)
    is_active = models.BooleanField(default=1)
    promotional_billing = models.BooleanField(default=0)
    purchase_edit_billing = models.BooleanField(default=False)
    retailer_billing = models.BooleanField(default=0)
    device_wise_login = models.BooleanField(default=False)
    est_bill_approval = models.BooleanField(default=False)
    est_bill_convert = models.BooleanField(default=False)
    allow_bill_date_change = models.BooleanField(default=False)
    isOTP_req_for_login = models.BooleanField(default=False)
    isOTP_req_for_bill_cancel = models.BooleanField(default=False)
    isOTP_req_for_multi_tag_print = models.BooleanField(default=False)
    isOTP_req_for_payment_cancel = models.BooleanField(default=False)
    isOTP_req_for_account_closing = models.BooleanField(default=False)
    isOTP_req_for_duplicate_bill = models.BooleanField(default=False)
    is_notify_for_est_approve = models.BooleanField(default=False)
    sales_return_limit = models.BooleanField(default=False)
    sales_return_limit_days = models.IntegerField(default=0)
    show_est_details = models.BooleanField(default=False)
    show_cus_visits = models.BooleanField(default=False)
    show_sales = models.BooleanField(default=False)
    show_karigar_order = models.BooleanField(default=False)
    show_cus_orders = models.BooleanField(default=False)
    show_sales_returns = models.BooleanField(default=False)
    show_credit_sales = models.BooleanField(default=False)
    show_old_metal_purchase = models.BooleanField(default=False)
    show_approvals = models.BooleanField(default=False)
    show_lots = models.BooleanField(default=False)
    show_cash_abstract = models.BooleanField(default=False)
    show_statistics = models.BooleanField(default=False)
    show_top_products = models.BooleanField(default=False)
    show_active_chits = models.BooleanField(default=False)
    show_matured_claimed = models.BooleanField(default=False)
    show_payment = models.BooleanField(default=False)
    show_users_joined_through = models.BooleanField(default=False)
    show_scheme_wise = models.BooleanField(default=False)
    show_branch_wise = models.BooleanField(default=False)
    show_collection_summary = models.BooleanField(default=False)
    show_inactive_chits = models.BooleanField(default=False)
    show_chit_closing_details = models.BooleanField(default=False)
    show_register_through_details = models.BooleanField(default=False)
    show_customer_details = models.BooleanField(default=False)
    show_customer_personal_landmark = models.BooleanField(default=False)
    show_branch_wise_collection_details = models.BooleanField(default=False)
    show_tagging_edit = models.BooleanField(default=False)
    can_edit_tag_va = models.BooleanField(default=False)
    can_edit_tag_mc = models.BooleanField(default=False)
    can_edit_tag_gwt = models.BooleanField(default=False)
    can_edit_tag_pcs = models.BooleanField(default=False)
    can_edit_tag_purity = models.BooleanField(default=False)
    can_edit_tag_mrp = models.BooleanField(default=False)
    can_edit_tag_huid = models.BooleanField(default=False)
    can_edit_tag_attr = models.BooleanField(default=False)
    can_edit_tag_pur_cost = models.BooleanField(default=False)
    can_edit_tag_dsgn_sub_desgn = models.BooleanField(default=False)
    can_edit_tag_img = models.BooleanField(default=False)
    can_print_tag = models.BooleanField(default=False)
    can_edit_account_join_date = models.BooleanField(default=False)
    allow_min_sales_amount = models.BooleanField(default=False)
    show_issue_pettycash_option = models.BooleanField(default=False)
    show_issue_credit_option = models.BooleanField(default=False)
    show_issue_refund_option = models.BooleanField(default=False)
    show_issue_bankdeposit_option = models.BooleanField(default=False)
    show_reciept_genadvnc_option = models.BooleanField(default=False)
    show_reciept_ordadvnc_option = models.BooleanField(default=False)
    show_reciept_credcoll_option = models.BooleanField(default=False)
    show_reciept_repord_delivery_option = models.BooleanField(default=False)
    show_reciept_openbal_option = models.BooleanField(default=False)
    show_reciept_chitdepo_option = models.BooleanField(default=False)
    show_reciept_others_option = models.BooleanField(default=True)
    allow_status_update = models.BooleanField(default=False)
    show_trans_code_search_in_billing = models.BooleanField(default=False)
    customer_type_show = models.BooleanField(default=False)
    is_show_min_sales_amount = models.BooleanField(default=False)
    show_unscanned_details = models.BooleanField(default=False)
    show_all_approval_estimations = models.BooleanField(default=False)
    is_otp_req_for_bill_delete = models.BooleanField(default=False)
    show_super_user_and_admin = models.BooleanField(default=False)
    
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='profile_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='profile_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'profile'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Area(models.Model):
    id_area = models.AutoField(primary_key=True)
    area_name = models.CharField(max_length=50)
    postal = models.CharField(max_length=50, null=True)
    taluk = models.CharField(max_length=50, null=True)
    pincode = models.IntegerField( null=True,default=None)
    region = models.ManyToManyField('Region', related_name='region_area')
    is_default = models.BooleanField(default=0)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='area_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='area_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'area'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Profession(models.Model):
    id_profession = models.AutoField(primary_key=True)
    profession_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='profession_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='profession_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'profession'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class MetalRates(models.Model):
    rate_id = models.AutoField(primary_key=True)
    gold_18ct = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    gold_20ct = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    gold_22ct = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    gold_24ct = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    gold_99_5ct = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    platinum = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    silver_G = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    silver_KG = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    silver_99_9 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    updatetime = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=1)
    send_notification = models.CharField(max_length = 60,  choices=(
        ("1", "Yes"), ("0", "No")), default=0)
    market_gold_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    market_silver_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='metal_rates_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='metal_rates_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return 'Metal Rates - ' + str(self.pk)

    class Meta:
        db_table = 'metal_rates'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class PaymentGateway(models.Model):
    API_TYPE_CHOICES = [
        (0, 'Demo - Demo URL'),
        (1, 'LIVE - LIVE url'),
    ]
    id_pg = models.AutoField(primary_key=True)
    pg_name = models.CharField(max_length=150)
    id_branch = models.ForeignKey(
        'Branch', on_delete=models.PROTECT, related_name='pg_branch_id', null=True)
    pg_code = models.CharField(max_length=15, null=True)
    param_1 = models.CharField(max_length=150, null=True)
    param_2 = models.CharField(max_length=150, null=True)
    param_3 = models.CharField(max_length=650, null=True)
    param_4 = models.CharField(max_length=650, null=True)
    api_url = models.CharField(max_length=150, null=True)
    api_type = models.IntegerField(choices=API_TYPE_CHOICES)
    is_default = models.BooleanField(default=1)
    pg_sort = models.IntegerField(default=0)
    pg_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='pg_create_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='pg_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'paymentgateway'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class PayDevice(models.Model):
    DEVICE_TYPE_CHOICES = [
        (1, 'Wallet'),
        (2, 'Bank'),
    ]
    id_device = models.AutoField(primary_key=True)
    device_name = models.CharField(max_length=30)
    device_type = models.IntegerField(choices=DEVICE_TYPE_CHOICES)
    device_status = models.BooleanField(default=True)
    device_sort = models.IntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='device_create_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='device_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'paydevice'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class NBType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    is_pay_device_req = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='nb_type_create_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='nb_type_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'nb_type'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Banner(models.Model):
    banner_id = models.BigAutoField(primary_key=True)
    banner_name = models.CharField(max_length=255, unique=True)
    banner_img = models.ImageField(
        validators=[Banner_image_restriction],
        upload_to=upload_banner)
    link = models.CharField(max_length=255, null=True, default=None)
    banner_status = models.BooleanField(default=True)
    banner_description = models.TextField(null=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='banner_created_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='banner_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return 'Banner - ' + str(self.pk)

    class Meta:
        db_table = 'banners'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class WeightRange(models.Model):
    id_weight_range = models.AutoField(primary_key=True)
    weight_range_name = models.CharField(max_length=20)
    id_product = models.ForeignKey(
        Product, related_name='weight_range_product', on_delete=models.PROTECT)
    from_weight = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    to_weight = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='weight_range_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='weight_range_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_weight_range'
        indexes = [
            models.Index(fields=['id_product']),  # Composite index
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['id_product', 'from_weight', 'to_weight'], name='product_weight_range')
        ]
        unique_together = [[
            'from_weight',
            'id_product',
            'to_weight',
        ]]

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class   Supplier(models.Model):
    id_supplier = models.AutoField(primary_key=True)
    is_vendor = models.IntegerField(choices=(
        (1, "Supplier"), (2, "Smith"), (3, "Manufacture"), (4, "Complementary Supplier"),(5, "Halmarking Center"),(6, "Local Vendor")), default=1)
    short_code = models.CharField(max_length=6,error_messages={"unique": "Product with this short code already exists"})
    supplier_name = models.CharField(max_length=75, unique=False)
    supplier_sign = models.CharField(max_length=45, blank=False, null=True, default=None)
    id_country = models.ForeignKey(
        'Country', related_name='supplier_id_country', on_delete=models.PROTECT,blank=True, null=True,default=None)
    id_state = models.ForeignKey('State', on_delete=models.PROTECT,blank=True, null=True,default=None)
    id_city = models.ForeignKey('City', on_delete=models.PROTECT,blank=True, null=True,default=None)
    id_metal = models.ManyToManyField(Metal,blank=True, null=True,default=None)
    address1 = models.CharField(max_length=20,blank=True, null=True,default=None)
    address2 = models.CharField(max_length=20, blank=True, null=True,default=None)
    address3 = models.CharField(max_length=20, blank=True, null=True,default=None)
    pincode = models.CharField(max_length=6, blank=True, null=True,default=None)
    gst_number = models.CharField(max_length=255, blank=True, null=True,default=None)
    pan_number = models.CharField(max_length=255, blank=True, null=True,default=None)
    phone_no = models.CharField(
        max_length=20, blank=True, null=True, default=None)
    mobile_no = models.CharField(max_length=20, blank=True,default=None,null=True)
    mob_code = models.CharField(max_length=15, default="+91")
    status = models.BooleanField(default=True)
    csh_op_blc = models.IntegerField(default=0)
    metal_op_blc = models.IntegerField(default=0)
    silver_op_blc = models.IntegerField(default=0)
    no_of_days_for_due = models.IntegerField(default=None, null=True)
    image = models.ImageField(
        upload_to=upload_supplier_image, null=True, default=None)
    created_by = models.ForeignKey(
        'accounts.User', related_name='supplier_added_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='supplier_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'erp_supplier'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class SupplierAccountDetails(models.Model):
    id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="supplier_account_detail")
    account_number = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    bank_name = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    account_branch = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    holder_name = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    upi = models.CharField(max_length=255, blank=True, null=True, default=None)
    acc_type = models.IntegerField(
        choices=((1, "Savings"), (2, "Current")), default=1)

    class Meta:
        db_table = 'erp_supplier_account_details'


class SupplierStaffDetails(models.Model):
    id_staff_details = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="supplier_staff_detail")
    staff_name = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    staff_mobile = models.CharField(
        max_length=255, blank=True, null=True, default=None)

    class Meta:
        db_table = 'erp_supplier_staff_details'


class SupplierProducts(models.Model):
    id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="supplier_products")
    show_wastage_details = models.IntegerField(
        choices=((1, "Customer"), (2, "Admin"), (3, "Both")), default=1)
    show_macking_charge_details = models.IntegerField(
        choices=((1, "Customer"), (2, "Admin"), (3, "Both")), default=1)
    created_by = models.ForeignKey(
        'accounts.User', related_name='supplier_product_added_by_user', on_delete=models.PROTECT, null=True, default=None)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='supplier_product_updated_by_user', null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(null=True, auto_now_add=datetime.now())
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_supplier_products'

    def __str__(self) -> str:
        return 'Supplier Products - ' + str(self.pk)

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class SupplierProductDetails(models.Model):
    id = models.AutoField(primary_key=True)
    supplier_product = models.ForeignKey(
        SupplierProducts, on_delete=models.PROTECT, related_name="supplier_product_details")
    product = models.ForeignKey(
        Product, related_name='supplier_product_detail_product', on_delete=models.PROTECT)
    design = models.ManyToManyField(
        Design, related_name='supplier_product_detail_design')
    sub_design = models.ManyToManyField(
        SubDesign, related_name='supplier_product_detail_sub_design')
    purity = models.ManyToManyField('retailcataloguemasters.Purity', related_name="supplier_product_detail_purity")
    size = models.ManyToManyField(Size, related_name="supplier_product_detail_size")
    from_wastage = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    to_wastage = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    from_making_charge = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    to_making_charge = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    from_weight = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    to_weight = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    approx_delivery_date = models.PositiveIntegerField(null=True)

    class Meta:
        db_table = 'erp_supplier_product_details'

    def __str__(self) -> str:
        return 'Supplier Product Detail - ' + str(self.pk)


class SupplierProductImageDetails(models.Model):
    id = models.AutoField(primary_key=True)
    supplier_product_details = models.ForeignKey(
        SupplierProductDetails, on_delete=models.PROTECT, related_name="supplier_product_details_image")
    image = models.ImageField(upload_to=upload_supplier_product_details_image)
    image_name = models.CharField(max_length=255, null=True, default=None)

    class Meta:
        db_table = 'erp_supplier_product_image_details'

    def __str__(self) -> str:
        return 'Supplier Product Detail Image - ' + str(self.pk)


class ErpDayClosed(models.Model):
    entry_date_id = models.AutoField(primary_key=True)
    id_branch = models.ForeignKey(
        Branch, related_name='day_close_branch', on_delete=models.PROTECT)
    is_day_closed = models.BooleanField(default=False)
    entry_date = models.DateField(default=None)
    updated_on = models.DateField(null=True, default=None)

    class Meta:
        db_table = 'erp_day_closing'
        constraints = [
            models.UniqueConstraint(
                fields=['id_branch'], name='branch_entry_date_constraint')
        ]


class ErpDayClosedLog(models.Model):

    CLOSE_TYPE_CHOICES = [
        (1, 'Manual'),
        (2, 'Automatic')
    ]

    id_day_closed_log = models.AutoField(primary_key=True)
    id_branch = models.ForeignKey(
        Branch, related_name='day_close_log_branch', on_delete=models.PROTECT)
    day_close_type = models.IntegerField(choices=CLOSE_TYPE_CHOICES, default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='day_closed_user', on_delete=models.PROTECT, default=None, null=True)

    class Meta:
        db_table = 'erp_day_closing_log'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by')


class ErpStockStatusMaster(models.Model):
    id_stock_status = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, unique=True, error_messages={
                            "unique": "Name already exists"})

    class Meta:
        db_table = 'erp_stock_status_master'


class ErpCharges(models.Model):
    id_charge = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, unique=True, error_messages={
                            "unique": "Name already exists"})
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='charges_user', on_delete=models.PROTECT, null=True, default=None)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='charges_updated_by_user', null=True, default=None, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_charges'


class AttributeEntry(models.Model):
    id_attribute = models.AutoField(primary_key=True)
    attribute_name = models.CharField(max_length=50)
    value = models.IntegerField(null=True)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='attribute_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='attribute_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'attribute'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class OtherCharges(models.Model):
    id_other_charge = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    amount = models.IntegerField()
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='other_charges_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='other_charges_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'other_charges'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class StockIssueType(models.Model):
    id_stock_issue_type = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    reduce_in_stock = models.BooleanField(default=0)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='stock_issue_type_create_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='stock_issue_type_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_stock_issue_type'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Floor(models.Model):
    id_floor = models.AutoField(primary_key=True)
    id_branch = models.ForeignKey(
        'Branch', on_delete=models.PROTECT, related_name='floor_branch_id', null=True)
    floor_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='floor_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='floor_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'erp_floor_master'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Counter(models.Model):
    id_counter = models.AutoField(primary_key=True)
    id_floor = models.ForeignKey(
        'Floor', on_delete=models.PROTECT, related_name='counter_floor_id', null=True)
    counter_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='counter_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='counter_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'erp_counter_master'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class RegisteredDevices(models.Model):
    id_registered_device = models.AutoField(primary_key=True)
    id_counter = models.ForeignKey(
        'Counter', on_delete=models.PROTECT, related_name='registered_counter_id', null=True)
    name = models.CharField(max_length=100)
    ref_no = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='registered_device_by_user', on_delete=models.PROTECT, null=True)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='registered_device_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'registered_devices'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Container(models.Model):
    id_container = models.AutoField(primary_key=True)
    branch = models.ForeignKey('retailmasters.Branch', related_name='container_branch',
                               on_delete=models.PROTECT, null=True, default=None)
    container_name = models.CharField(max_length=50)
    sku_id = models.CharField(max_length=50)
    description = models.TextField(null=True)
    weight = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='container_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='container_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'container'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class OldMetalItemType(models.Model):
    id_item_type = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    id_metal = models.ForeignKey(
        Metal, on_delete=models.PROTECT, related_name='old_metal_item_id_metal', null=True)
    code = models.CharField(max_length=50)
    touch = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    rate_deduction = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='old_metal_item_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='old_metal_item_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'old_metal_item'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class OtherWeight(models.Model):
    id_other_weight_master = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    weight = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00)
    description = models.TextField(null=True)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='other_weight_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='other_weight_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'erp_other_weight'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class CashOpeningBalance(models.Model):
    id_opening_balance = models.AutoField(primary_key=True)
    entry_date = models.DateField(blank=True, null=True)
    branch = models.ForeignKey('retailmasters.Branch', related_name='csh_opening_balance',
                               on_delete=models.PROTECT, null=True, default=None)
    amount = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='csh_opening_balance_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='csh_opening_balance_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'erp_branch_csh_opening_balance'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class AccountHead(models.Model):
    TYPE_CHOICES = [
        (1, 'Issue'),
        (2, 'Receipt')
    ]
    id_account_head = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=1)
    type = models.IntegerField(choices=TYPE_CHOICES, default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='account_head_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='account_head_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'erp_account_head'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class CustomerProof(models.Model):
    id_proof_identity = models.AutoField(primary_key=True)
    id_customer = models.ForeignKey(
        'customers.Customers', on_delete=models.PROTECT, related_name='customer_proof_customerid')
    aadhar_number = models.CharField(max_length=255, null=True)
    aadhar_img_page = models.ImageField(
        upload_to=upload_customer_aadhar_image, null=True, default=None)
    application_img_path = models.ImageField(
        upload_to=upload_customer_aadhar_image, null=True, default=None)
    remarks = models.CharField(max_length=75, blank=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='customer_proof_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='customer_proof_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'erp_customer_proof'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class BankDeposit(models.Model):
    id_bank_deposit = models.AutoField(primary_key=True)
    entry_date = models.DateField(blank=True, null=True)
    branch = models.ForeignKey('retailmasters.Branch', related_name='bank_deposit_branch',
                               on_delete=models.PROTECT, null=True, default=None)
    bank = models.ForeignKey('retailmasters.Bank', related_name='bank_deposit_bank',
                             null=True, default=None, on_delete=models.PROTECT)
    amount = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='bank_deposit_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='bank_deposit_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_bank_deposit'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class DepositMaster(models.Model):
    id_deposit_master = models.AutoField(primary_key=True)
    scheme = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=50, unique=True)
    maturity_in_days = models.PositiveIntegerField()
    type = models.IntegerField(choices=(
        (1, "Amount"), (2, "Weight"), (3, "Both")))
    payable_type = models.IntegerField( choices=((1, "Fixed"), (2, "Flexible")))
    interest  = models.IntegerField( choices=((1, "Yes"), (2, "No")))
    interest_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    interest_type  = models.IntegerField( choices=(
        (1, "Fixed"), (2, "Time period")))
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='erp_deposit_master_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='erp_deposit_master_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_deposit_master'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    
class DepositMasterInterest(models.Model):
    id_deposit_master_settings = models.AutoField(primary_key=True)
    deposit_master = models.ForeignKey(DepositMaster,on_delete=models.PROTECT)
    from_days= models.PositiveIntegerField()
    to_days = models.PositiveIntegerField()
    interest_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    
    def _str_(self) -> str:
        return 'Deposit Master Interest Settings - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_deposit_master_interest'

class CustomerDeposit(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey('customers.Customers', on_delete=models.PROTECT, related_name='cus_deposit_customerid')
    deposit = models.ForeignKey(DepositMaster, on_delete=models.PROTECT)
    branch = models.ForeignKey('retailmasters.Branch', related_name='cus_deposit_branch',
                               on_delete=models.PROTECT,)
    bill = models.ForeignKey('billing.ErpInvoice', on_delete=models.PROTECT, 
                             related_name='cus_deposit_bill', null=True, default=None)
    ref_no = models.CharField(max_length=50, null=True, default=None)
    entry_date = models.DateField(default=None)
    start_date = models.DateField(default=None)
    closing_date = models.DateField(default=None)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    deposit_weight = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    
    def _str_(self) -> str:
        return 'Customer Deposit Master - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_customer_deposit'
    
class CustomerDepositItems(models.Model):
    id = models.AutoField(primary_key=True)
    est_old_metal_item_id = models.ForeignKey('estimations.ErpEstimationOldMetalDetails',on_delete=models.SET_NULL,related_name="old_metal_item_deposit",null=True,default=None)
    cus_deposit = models.ForeignKey(CustomerDeposit, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=False, blank=False, related_name="cus_deposit_product")
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def _str_(self) -> str:
        return 'Customer Deposit Items - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_customer_deposit_items'
        
class CustomerDepositPayment(models.Model):
    PAID_THROUGH_CHOICES = [
        (1, 'Admin'),
        (2, 'Mobile App'),
        (3, 'Collection App')
    ]
    TAX_TYPE_CHOICES = [
        (1, 'Inclusive'),
        (2, 'Exclusive'),
        (3, 'N/A'),
    ]
    id_payment          = models.AutoField(primary_key=True)
    date_payment        = models.DateField(blank=False, null=False)
    cus_deposit         = models.ForeignKey(CustomerDeposit, on_delete=models.PROTECT)
    id_branch           = models.ForeignKey('retailmasters.Branch', on_delete=models.PROTECT, related_name='cus_deposit_payment_branch_id')
    id_payGateway       = models.ForeignKey('retailmasters.PaymentGateway', on_delete=models.PROTECT, related_name='cus_deposit_payment_pg_id', null=True)
    trans_id            = models.CharField(max_length=75, null=True)
    trans_date          = models.DateField(blank=True, null=True)
    entry_date          = models.DateField(auto_now_add=date.today())
    payment_amount      = models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0.01)])
    net_amount          = models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0.01)])
    payment_charges     = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status      = models.ForeignKey('schemepayment.PaymentStatus', on_delete=models.PROTECT, null=True, default=None,related_name='cus_deposit_payment_status_id')
    remark              = models.CharField(max_length=75, blank=True)
    receipt_no          = models.CharField(max_length=75, blank=True)
    ref_trans_id        = models.CharField(max_length=75, null=True)
    discountAmt         = models.DecimalField(max_digits=10, decimal_places=2, default = 0,validators=[MinValueValidator(0.00)])
    tax_amount          = models.DecimalField(max_digits=10, decimal_places=2, default = 0,validators=[MinValueValidator(0.00)])
    tax_type            = models.IntegerField(choices=TAX_TYPE_CHOICES, null=True, default=None) 
    tax_id              = models.ForeignKey('retailmasters.Taxmaster',related_name='cus_deposit_payment_tax',on_delete=models.PROTECT,null=True,default=None)
    actual_trans_amt    = models.DecimalField(max_digits=10, decimal_places=2, default = 0,validators=[MinValueValidator(0.00)])
    is_offline          = models.IntegerField(default = 0)
    approval_date       = models.DateTimeField(blank=True, null=True)
    gst                 = models.DecimalField(max_digits=10, decimal_places=2, default = 0)
    gst_type            = models.IntegerField(default = 0)
    gst_amount          = models.DecimalField(max_digits=10, decimal_places=2, default = 0)
    paid_through        = models.IntegerField(choices=PAID_THROUGH_CHOICES, null=True)
    due_type            = models.CharField(max_length=2, default="ND")
    order_id            = models.TextField(default=None,blank=True,null=True)
    payment_session_id  = models.TextField(default=None,blank=True,null=True)
    created_on          = models.DateTimeField(auto_now_add=datetime.now())
    created_by          = models.ForeignKey('accounts.User',related_name='cus_deposit_pay_create_by_user', on_delete=models.PROTECT, null=True)
    updated_by          = models.ForeignKey('accounts.User',related_name='cus_deposit_pay_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on          = models.DateTimeField(null=True)
    cancelled_by        = models.ForeignKey('accounts.User',related_name='cus_deposit_pay_cancel_by_user', on_delete=models.PROTECT, null=True, default=None)
    cancelled_date      = models.DateField(null=True, default=None)
    cancel_reason       = models.TextField(null=True, default=None)
    
    
    class Meta:
        db_table = 'erp_customer_deposit_payment'
        
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
        
class CustomerDepositPaymentDetail(models.Model):
    CARD_TYPE_CHOICES = [
        (0, ''),
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    id_pay_mode_details     = models.AutoField(primary_key=True)
    id_pay                  = models.ForeignKey(CustomerDepositPayment, on_delete=models.PROTECT, related_name='cus_deposit_pay_det_pay_id', null=True)
    id_bank                 = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, default=None)
    payment_date            = models.DateTimeField(auto_now_add=datetime.now())
    payment_type            = models.CharField(max_length=25, null=True)
    payment_mode            = models.ForeignKey('retailmasters.PaymentMode', on_delete=models.PROTECT, null=True,related_name='cus_deposit_payment_mode_id')
    payment_amount          = models.DecimalField(max_digits=10, decimal_places=2)
    card_no                 = models.CharField(max_length=15, null=True, default=None)
    card_holder             = models.CharField(max_length=75, null=True, default=None)
    payment_ref_number      = models.CharField(max_length=25, null=True, default=None)
    payment_status          = models.IntegerField(default = 0)
    card_type               = models.IntegerField(choices=CARD_TYPE_CHOICES, null=True, default=0)
    NB_type                 = models.IntegerField(default = 0, null=True) 
    net_banking_date        =  models.DateTimeField(null=True, default=None)
    remark                  = models.CharField(max_length=275, null=True)
    id_pay_device           = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='cus_deposit_pay_det_device_id', null=True)
    created_on              = models.DateTimeField(auto_now_add=datetime.now())
    created_by              = models.ForeignKey('accounts.User', related_name='cus_deposit_pay_det_create_by_user', on_delete=models.PROTECT, null=True)
    updated_by              = models.ForeignKey('accounts.User', related_name='cus_deposit_pay_det_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on              = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'erp_customer_deposit_paymentdetails'
        
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    


    
class IncentiveSettings(models.Model):
    TYPE_CHOICES =[("0", "MRP Item"), ("1", "Weight Based Item")]
    CALCULATION_METHOD_CHOICES =[("1", "Flat"), ("2", "Percentage"),("3", "Per Gram"),("4", "Weight-Range")]

    incentive_id = models.AutoField(primary_key=True)
    start_date = models.DateField()
    end_date = models.DateField()
    branch = models.ForeignKey('retailmasters.Branch', related_name='incentive_settings_branch',
                               on_delete=models.PROTECT, null=True, default=None)
    incentive_type = models.CharField(max_length=15, choices=TYPE_CHOICES,default="0")
    calculation_method = models.CharField(max_length=15, choices=CALCULATION_METHOD_CHOICES,default="0")
    value = models.IntegerField()
    weight_ranges = models.CharField(max_length=255,null=True,default=None)
    employee_roles = models.CharField(max_length=255,null=True,default=None)
    applicable_products = models.CharField(max_length=255,null=True,default=None)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='incentive_settings_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='incentive_settings_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_incentive_settings'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class IncentiveTransactions (models.Model):
    EMP_ROLES_CHOICES =[("0", "Main"), ("1", "Support"),("2", "Support 2")]

    incentive_transaction_id = models.AutoField(primary_key=True)
    transaction_date = models.DateField()
    sale_item = models.ForeignKey('billing.ErpInvoiceSalesDetails', related_name='incentive_sale_item',on_delete=models.SET_NULL,null=True)
    employee = models.ForeignKey('employees.Employee', related_name='incentive_emp',on_delete=models.PROTECT)
    incentive = models.ForeignKey(IncentiveSettings, related_name='incentive_settings',on_delete=models.PROTECT)
    product = models.ForeignKey(Product, related_name='incentive_product',on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(null=False,blank=False,default=0)
    weight  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    sale_value  = models.DecimalField(max_digits=10, decimal_places=2, default=0.000,validators=[MinValueValidator(0.0)])
    incentive_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0.000,validators=[MinValueValidator(0.0)])
    employee_role = models.CharField(max_length=15, choices=EMP_ROLES_CHOICES,default="0")
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='incentive_transaction_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='incentive_transaction_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_incentive_transaction'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Religion(models.Model):
    id_religion = models.AutoField(primary_key=True)     
    name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='religion_create_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='religion_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_religion'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class CustomerNotificationMaster(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    active = models.BooleanField()
    image = models.ImageField(upload_to=upload_notification_img, null=True)
    # send_to_customers = models.ManyToManyField('customers.Customers', related_name='customer_notification')
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='customer_notification_create_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='customer_notification_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'customer_notification_master'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class CustomerNotifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    notification = models.ForeignKey(CustomerNotificationMaster, on_delete=models.PROTECT)
    customers = models.ForeignKey('customers.Customers', related_name='customers_notification', on_delete=models.PROTECT)
    status = models.IntegerField(choices=[(1, 'Not yet seen'), (2, 'Seen')], default=1)
    
    class Meta:
        db_table = 'customer_notifications'



        

class DailyStatusMaster(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.IntegerField(choices=[(1, 'Image'), (2, 'Audio'),
                                         (3, 'Video'), (4, 'Text',)])
    image_file = models.ImageField(upload_to=upload_daily_status_img, null=True, default=None)
    audio_file = models.FileField(upload_to=upload_daily_status_audio, null=True, default=None)
    video_file = models.FileField(upload_to=upload_daily_status_video, null=True, default=None)
    text = models.TextField(null=True, default=None)
    status = models.BooleanField(default=True)
    valid_upto = models.DateTimeField()
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='daily_status_create_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='daily_status_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'daily_status_master'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    


class Region(models.Model):
    id_region = models.AutoField(primary_key=True)
    region_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=1)
    created_on = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='region_by_user', on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='region_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        # managed = False
        db_table = 'region'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')