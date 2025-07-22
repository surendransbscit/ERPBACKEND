from django.db import models
from datetime import datetime, date

# Create your models here.

class SchemeAccount(models.Model):
    
    SCHEME_CREATED_THROUGH_CHOICES = [
        (0, 'Admin App'),
        (1, 'Mobile App'),
        (2, 'Web App'),
        (3, 'Collection app')
    ]
    
    UTILIZED_TYPE_CHOICES = [
        (1, 'Cash Refund'),
        (2, 'Against Purchase')
    ]
    
    id_scheme_account       = models.AutoField(primary_key=True)
    acc_scheme_id           = models.ForeignKey('schememaster.Scheme', on_delete=models.PROTECT, related_name='scheme_account_scheme_id')
    id_customer             = models.ForeignKey('customers.Customers', on_delete=models.PROTECT, related_name='scheme_customerid')
    id_branch               = models.ForeignKey('retailmasters.Branch', on_delete=models.PROTECT, related_name='scheme_branch_id')
    scheme_acc_number       = models.CharField(max_length=15, null=True, blank=True, default=None)
    total_paid_ins          = models.IntegerField(default = 0)
    display_ac_no           = models.CharField(max_length=150,blank=True)
    account_name            = models.CharField(max_length=150)
    ref_no                  = models.CharField(max_length=150,blank=True)
    start_date              = models.DateField(auto_now_add=date.today())
    approved_employee       = models.IntegerField(default = 0)
    #old details
    old_scheme_acc_number   = models.CharField(max_length=150,null=True, default=None)
    opening_balance_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    opening_balance_weight  = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    old_paid_ins            = models.IntegerField(default = 0)
    #old details
    closing_balance         = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    closing_amount          = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    closing_weight          = models.DecimalField(max_digits=10, decimal_places=3,null=True)
    target_weight           = models.DecimalField(max_digits=10, decimal_places=3,null=True, default=None)
    closing_date            = models.DateField(blank=True, null=True)
    closed_employee         = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, related_name='closed_employee')
    is_closed               = models.BooleanField(default = False)
    added_by                = models.IntegerField(choices=SCHEME_CREATED_THROUGH_CHOICES, verbose_name='Scheme Joint Through',null=True)
    additional_benefits     = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    closing_add_charges     = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    closing_deductions      = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    closing_benefits        = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    is_utilized             = models.BooleanField(default = False)
    utilized_type           = models.IntegerField(choices=UTILIZED_TYPE_CHOICES, verbose_name='Utilized Type',null=True)
    closing_id_branch       = models.ForeignKey('retailmasters.Branch', on_delete=models.PROTECT, related_name='scheme_closing_branch_id', null=True)
    fin_year                = models.ForeignKey('retailmasters.FinancialYear', on_delete=models.PROTECT, related_name='financial_year_id', null=True)
    created_on              = models.DateTimeField(auto_now_add=datetime.now())
    updated_on              = models.DateTimeField(null=True)
    close_reverted_by       = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, default=None, related_name='close_reverted_employee')
    
    class Meta:
        db_table = 'schemeaccount'
   