from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, date
# Create your models here.

account_user = 'accounts.User'
class PaymentStatus(models.Model):
    id      = models.AutoField(primary_key=True)
    name    = models.CharField(max_length=255)    
    color   = models.CharField(max_length=255)   
    
    def __str__(self) -> str:
        return 'Payment Status - ' + str(self.pk)
    
    class Meta:
        db_table = 'payment_status' 
    

class Payment(models.Model):
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
    id_scheme_account   = models.ForeignKey('managescheme.SchemeAccount', on_delete=models.PROTECT, related_name='payment_scheme_account_id',default=None,blank=True,null=True)
    id_scheme           = models.ForeignKey('schememaster.Scheme', on_delete=models.PROTECT, related_name='payment_scheme_id', null=True)
    date_payment        = models.DateField(blank=False, null=False)
    installment         = models.IntegerField(default = 0)
    id_branch           = models.ForeignKey('retailmasters.Branch', on_delete=models.PROTECT, related_name='payment_branch_id',null = True , default = None)
    id_payGateway       = models.ForeignKey('retailmasters.PaymentGateway', on_delete=models.PROTECT, related_name='payment_pg_id', null=True)
    trans_id            = models.CharField(max_length=75, null=True)
    trans_date          = models.DateField(blank=True, null=True)
    entry_date          = models.DateField(auto_now_add=date.today())
    payment_amount      = models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0.01)])
    net_amount          = models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0.01)])
    payment_charges     = models.DecimalField(max_digits=10, decimal_places=2)
    metal_rate          = models.DecimalField(max_digits=10, decimal_places=2)
    metal_weight        = models.DecimalField(max_digits=10, decimal_places=3,validators=[MinValueValidator(0.00)])
    bonus_metal_weight        = models.DecimalField(max_digits=10, decimal_places=3,validators=[MinValueValidator(0.00)], default=0)
    bonus_metal_amount        = models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0.00)], default=0)
    payment_status      = models.ForeignKey(PaymentStatus, on_delete=models.PROTECT, null=True, default=None,related_name='payment_status_id')
    remark              = models.CharField(max_length=75, blank=True)
    receipt_no          = models.CharField(max_length=75, blank=True)
    ref_trans_id        = models.CharField(max_length=75, null=True)
    discountAmt         = models.DecimalField(max_digits=10, decimal_places=2, default = 0,validators=[MinValueValidator(0.00)])
    tax_amount          = models.DecimalField(max_digits=10, decimal_places=2, default = 0,validators=[MinValueValidator(0.00)])
    tax_type            = models.IntegerField(choices=TAX_TYPE_CHOICES, null=True, default=None) 
    tax_id              = models.ForeignKey('retailmasters.Taxmaster',related_name='payment_tax',on_delete=models.PROTECT,null=True,default=None)
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
    is_free_installment = models.BooleanField(default=False)
    created_on          = models.DateTimeField(auto_now_add=datetime.now())
    created_by          = models.ForeignKey(account_user,related_name='pay_create_by_user', on_delete=models.PROTECT, null=True)
    updated_by          = models.ForeignKey(account_user,related_name='pay_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on          = models.DateTimeField(null=True)
    cancelled_by        = models.ForeignKey(account_user,related_name='pay_cancel_by_user', on_delete=models.PROTECT, null=True, default=None)
    cancelled_date      = models.DateField(null=True, default=None)
    cancel_reason       = models.TextField(null=True, default=None)
    account_name        = models.CharField(max_length=150,null=True, default=None)
    id_customer         = models.ForeignKey('customers.Customers', on_delete=models.PROTECT, related_name='payment_scheme_customerid',null=True, default=None)
    
    
    class Meta:
        db_table = 'payment'
        
    

class PaymentModeDetail(models.Model):
    CARD_TYPE_CHOICES = [
        (0, ''),
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    id_pay_mode_details     = models.AutoField(primary_key=True)
    id_pay                  = models.ForeignKey('Payment', on_delete=models.PROTECT, related_name='pay_det_pay_id', null=True)
    id_bank                 = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, default=None)
    payment_date            = models.DateTimeField(auto_now_add=datetime.now())
    payment_type            = models.CharField(max_length=25, null=True)
    payment_mode            = models.ForeignKey('retailmasters.PaymentMode', on_delete=models.PROTECT, null=True,related_name='payment_mode_id')
    payment_amount          = models.DecimalField(max_digits=10, decimal_places=2)
    card_no                 = models.CharField(max_length=15, null=True, default=None)
    card_holder             = models.CharField(max_length=75, null=True, default=None)
    payment_ref_number      = models.CharField(max_length=25, null=True, default=None)
    payment_status          = models.IntegerField(default = 0)
    card_type               = models.IntegerField(choices=CARD_TYPE_CHOICES, null=True, default=0)
    NB_type                 = models.IntegerField(default = 0, null=True) 
    net_banking_date        =  models.DateTimeField(null=True, default=None)
    remark                  = models.CharField(max_length=275, null=True)
    id_pay_device           = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='pay_det_device_id', null=True)
    created_on              = models.DateTimeField(auto_now_add=datetime.now())
    created_by              = models.ForeignKey(account_user, related_name='pay_det_create_by_user', on_delete=models.PROTECT, null=True)
    updated_by              = models.ForeignKey(account_user, related_name='pay_det_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on              = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'paymentmodedetails'