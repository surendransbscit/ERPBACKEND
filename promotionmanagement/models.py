from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime
accounts_user = 'accounts.User'
from retailmasters.models import (Branch, Supplier)
from employees.models import (Employee)
from customers.models import (Customers)
from retailcataloguemasters.models import Product
# Discount

class Discount(models.Model):
    
    DISCOUNT_TYPE_CHOICES = [
        (1, ' Wastage %'),
        (2,  'Wastage Value'),
        (3,  'Making Charges % '),
        (4,  'Making Charges Value'),
        (5,  'Gold Rate Discount'),
        (6,  'Diamond Value Discount'),
        (7,  'Flat Bill % Discount'),
        (8,  'Flat Bill ₹ Discount'),
        (9,  'Category Discount'),
        (10,  'Product Discount'),
        (11,  'Customer Type Discount '),        
        ]
    
    discount_id = models.AutoField(primary_key=True)
    discount_name = models.CharField(max_length=255)
    discount_type = models.IntegerField(choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.CharField(max_length=255)
    apply_on = models.CharField(max_length = 60,  choices=(
        ("1", "All"), ("2", "Product")), default=1)
    apply_on_value = models.CharField(max_length=255)
    start_date = models.DateField(default=None)
    end_date = models.DateField(default=None)
    branches = models.ManyToManyField(Branch, related_name='discount_branches')
    product = models.ManyToManyField(Product, related_name='discount_products')
    terms_and_conditions  = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=1)
    max_discount_allowed = models.CharField(max_length=255)
    conditions = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_discount', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_discount', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Discount - ' + str(self.pk)

    class Meta:
        db_table = 'discount'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


#coupon master

class Coupon(models.Model):
   
    coupon_id = models.AutoField(primary_key=True)
    coupon_code = models.CharField(max_length=15, unique=True,
                                  error_messages={'unique': "Coupon Code Already exists"})
    discount_type = models.CharField(max_length = 60,  choices=(
        ("1", "Percentage"), ("2", "Value")), default=1)
    discount_value = models.CharField(max_length=255)
    min_cart_value = models.CharField(max_length=255)
    usage_limit = models.CharField(max_length=255)
    branches = models.ManyToManyField(Branch, related_name='coupon_branches')
    is_active = models.BooleanField(default=1)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_coupon', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_coupon', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Coupon - ' + str(self.pk)

    class Meta:
        db_table = 'coupon'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    

class GiftVoucher(models.Model):
       
    voucher_id = models.AutoField(primary_key=True)
    voucher_name = models.CharField(max_length=255)
    voucher_code = models.CharField(max_length = 60,  choices=(
        ("1", "Auto"), ("2", "Manual")), default=1)
    shortcode = models.CharField(max_length=15, unique=True,null=True, default=None,
                                  error_messages={'unique': "Short Code Already exists"})
    voucher_amount = models.CharField(max_length=255)
    validity_from  = models.DateField(default=None)
    validity_to = models.DateField(default=None)
    redemable_on = models.CharField(max_length = 60,  choices=(
        ("1", "Only Sales"), ("2", "Only Saving Scheme"),("3","Both")), default=1)
    usage_limit = models.CharField(max_length=255)
    voucher_type = models.CharField(max_length = 60,  choices=(
        ("1", "Free "), ("2", "Paid Voucher")), default=1)
    issued_to = models.CharField(max_length = 60,  choices=(
        ("1", "Customer "), ("2", "Employee "),("3","Vendors"),("4","Others")), default=1)
    conditions = models.CharField(max_length=255,null=True, blank=True)
    terms_and_conditions  = models.TextField(null=True, blank=True)
    apply_on = models.CharField(max_length = 60,  choices=(
        ("1", "All"), ("2", "Product")), default=1)
    product = models.ManyToManyField(Product, related_name='gift_voucher_products')
    is_active = models.BooleanField(default=1)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_gift_voucher', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_gift_voucher', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Gift Voucher - ' + str(self.pk)

    class Meta:
        db_table = 'gift_voucher'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    
class GiftVoucherIssue(models.Model):
    issue_id = models.AutoField(primary_key=True)
    voucher = models.ForeignKey(GiftVoucher, on_delete=models.PROTECT)
    voucher_code = models.CharField(max_length=255, unique=True, error_messages={"unique": "Voucher code already exists"})
    customer = models.ForeignKey(Customers, on_delete=models.PROTECT, null=True, default=None)    
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, default=None)    
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, default=None)
    notes = models.TextField()    
    amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    status = models.IntegerField(choices=[(1, 'Pending'), (2, 'Redeemed'), (3, 'Cancelled')], default=1)
    ref_no = models.ForeignKey('billing.ErpInvoice', on_delete=models.PROTECT, null=True, default=None)
    issued_date = models.DateField(null=True, default=None)
    cancelled_by = models.ForeignKey(
        accounts_user, related_name='cancelled_gift_voucher_issue', on_delete=models.CASCADE, null=True)
    cancelled_on = models.DateTimeField(default=None, null=True)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_gift_voucher_issue', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_gift_voucher_issue', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Gift Voucher Issue - ' + str(self.pk)

    class Meta:
        db_table = 'gift_voucher_issue'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    

class GiftVoucherIssuePaymentDetail(models.Model):
    CARD_TYPE_CHOICES = [
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    PAYMENT_TYPE_CHOICES = [
        (1,'Credit'),
        (2,'Debit'),
    ]
    issue_pay_id     = models.AutoField(primary_key=True)
    voucher_issue    = models.ForeignKey(GiftVoucherIssue, on_delete=models.PROTECT, related_name='voucher_issue_payment', null=True)
    id_bank                 = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, blank=True,default=None)
    payment_date            = models.DateTimeField(auto_now_add=datetime.now())
    payment_type            = models.IntegerField(choices=PAYMENT_TYPE_CHOICES,default=1)
    payment_mode            = models.ForeignKey('retailmasters.PaymentMode', on_delete=models.PROTECT, null=True)
    payment_amount          = models.DecimalField(max_digits=10, decimal_places=2)
    card_no                 = models.CharField(max_length=15, null=True,blank=True, default=None)
    card_holder             = models.CharField(max_length=75, null=True,blank=True,default=None)
    payment_ref_number      = models.CharField(max_length=25, null=True, blank=True,default=None)
    payment_status          = models.IntegerField(default = 0)
    card_type               = models.IntegerField(choices=CARD_TYPE_CHOICES, null=True, default=0)
    NB_type                 = models.IntegerField(default = 0, null=True,blank=True,) 
    net_banking_date        =  models.DateTimeField(null=True, default=None)
    remark                  = models.CharField(max_length=275, null=True)
    id_pay_device           = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='voucher_issue_pay_device', null=True)
       
    class Meta:
        db_table = 'voucher_issue_payment_details'