from django.db import models
from datetime import datetime
import os
from retailcataloguemasters.models import Product, Metal, Purity
from django.core.files.images import get_image_dimensions
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator,MaxValueValidator

# Create your models here.

accountUser = 'accounts.User'
Scheme      = 'Scheme'

class SchemePaymentFormula(models.Model):
    id         = models.AutoField(primary_key=True)
    name       = models.CharField(max_length=150)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(accountUser, related_name='scheme_payment_formula_created_by', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(accountUser, related_name='scheme_payment_formula_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
      db_table = 'scheme_payment_formula'

class Scheme(models.Model):
    
    SCHEME_TYPE_CHOICES = [
        (0, 'Amount - Scheme based on amount'),
        (1, 'Weight - Scheme based on weight'),
        (2, 'DigiGold - Scheme based on Digital Gold'),

    ]
    TAX_TYPE_CHOICES = [
        (1, 'Inclusive'),
        (2, 'Exclusive'),
        (3, 'N/A'),
    ]

    scheme_vis_choices = [(1, 'All'), 
                (2, 'Admin'),
                (3, 'Mobile App'),
                (4, 'Collection App')]

    payment_restrict_choices = [(1, 'None'),
                                (2, 'All'),
                                (3, 'Admin'),
                                (4, 'Mobile App'),
                                (5, 'Collection App')]
    tax_type                = models.IntegerField(choices=TAX_TYPE_CHOICES, verbose_name='Tax type', null=True, default=None) 
    tax_id                  = models.ForeignKey('retailmasters.Taxmaster',related_name='scheme_tax',on_delete=models.PROTECT,null=True,default=None)
    scheme_id               = models.AutoField(primary_key=True)
    scheme_name             = models.CharField(max_length=150)
    scheme_code             = models.CharField(max_length=150)
    sch_id_metal            = models.ForeignKey(Metal, on_delete=models.PROTECT, related_name='scheme_metal_id', null=True)
    sch_classification      = models.ForeignKey('retailcataloguemasters.SchemeClassification', on_delete=models.PROTECT, related_name='scheme_classfication', null=True)
    sch_id_purity           = models.ForeignKey(Purity, on_delete=models.PROTECT, related_name='scheme_metal_id', null=True)
    scheme_type             = models.IntegerField(choices=SCHEME_TYPE_CHOICES, verbose_name='Scheme type')
    scheme_description      = models.TextField(null=True, blank=True)
    kyc_req                 = models.BooleanField(default=False)
    when_kyc_required       = models.CharField(choices=[(1, 'Scheme Joining'),(2, 'Scheme Closing'), (3, 'Particular Amount')], max_length = 10, blank = True, default = None)
    allow_advance           = models.BooleanField(default=False)
    number_of_advance       = models.PositiveIntegerField(null=True, default = None)
    allow_pending_due       = models.BooleanField(default=False)
    number_of_pending_due   = models.PositiveIntegerField(null=True, default = None)
    particular_amount       = models.PositiveIntegerField(null=True, default = None)
    convert_to_weight       = models.BooleanField(default=False)
    status                  = models.BooleanField(default=True)  
    allow_join              = models.BooleanField(default=False)  
    allow_join_multi_acc    = models.BooleanField(default=True)  
    unpaid_as_def           = models.BooleanField(default=False)  
    allow_due               = models.BooleanField(default=False)  
    total_instalment        = models.PositiveIntegerField(null = True)
    has_free_installment    = models.BooleanField(default=False)
    free_installment        = models.IntegerField(default = 0)
    digi_maturity_days      = models.PositiveIntegerField(null=True, default = None)
    digi_payment_chances    = models.PositiveIntegerField(null=True, default = None)
    digi_min_amount         = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=None)
    show_target             = models.BooleanField(default=False)
    pre_close_charges       = models.DecimalField(max_digits=10, decimal_places=2)
    scheme_vis              = models.CharField(choices=scheme_vis_choices,max_length = 10,default = '2')
    payment_restrict        = models.CharField(choices=payment_restrict_choices,max_length = 10,default = '1')
    payable_type            = models.CharField(choices=[(1, 'Fixed'),(2, 'Flexible')], max_length = 10, default = "1")
    created_on              = models.DateTimeField(auto_now_add=datetime.now())
    created_by              = models.ForeignKey(accountUser, related_name='scheme_create_by_user', on_delete=models.PROTECT)
    updated_by              = models.ForeignKey(accountUser,related_name='scheme_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on              = models.DateTimeField(null=True)
    
    
    class Meta:
        db_table = 'schemes'
        
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')



class SchemeBenefitSettings(models.Model):
    id                  = models.AutoField(primary_key=True)
    scheme              = models.ForeignKey(Scheme, on_delete=models.PROTECT)
    installment_from    = models.PositiveIntegerField()
    installment_to      = models.PositiveIntegerField()
    wastage_benefit     = models.PositiveIntegerField()
    mc_benefit          = models.PositiveIntegerField()
    
    
    def __str__(self) -> str:
        return 'Scheme Benefit Settings - ' + str(self.pk)
    
    class Meta:
        db_table = 'scheme_benefit_settings'
        

class PaymentSettings(models.Model):
    id                      = models.AutoField(primary_key=True)
    scheme                  = models.ForeignKey(Scheme, on_delete = models.DO_NOTHING, null = True, default = None)
    installment_from        = models.PositiveIntegerField()
    installment_to          = models.PositiveIntegerField()
    min_formula             = models.ForeignKey('SchemePaymentFormula', on_delete=models.PROTECT, related_name='min_formula', null=True, default=None)
    min_condition           = models.CharField(choices=[(1, 'N/A'),(2, 'Avg < Y1 ins payable means set Y1 as payable')], max_length = 10)
    min_condition_param     = models.CharField(max_length = 255, blank=True)
    min_parameter           = models.CharField(max_length = 255)
    max_formula             = models.ForeignKey('SchemePaymentFormula', on_delete=models.PROTECT, related_name='max_formula', null=True, default=None)
    max_condition           = models.CharField(choices=[(1, 'N/A'),(2, 'Avg < Y1 ins payable means set Y1 as payable')], max_length = 10)
    max_condition_param     = models.CharField(max_length = 255, blank=True)
    max_parameter           = models.CharField(max_length = 255)
    payment_type            = models.CharField(max_length = 255, null=True)
    limit_by                = models.CharField(choices=[(1, 'Amount'),(2, 'Weight')], max_length = 10)
    payment_min             = models.PositiveIntegerField(null = True)
    payment_max             = models.PositiveIntegerField(null = True)
    discount_type           = models.CharField(choices=[(1, 'Percent'),(2, 'Amount')], max_length = 10)
    discount_value          = models.CharField(max_length = 255)
    payment_chance_type     = models.CharField(choices=[(1, 'Daily'),(2, 'Monthly'), (3, 'Yearly')], max_length = 10)
    payment_chance_value    = models.PositiveIntegerField()
    denom_type              = models.CharField(choices=[(1, 'Multiples'),(2, 'Master'),(3, 'N/A'),
                                            (4, 'Grouping')], max_length = 10,blank=True)
    denom_value              = models.CharField(max_length = 255, blank=True)
    
    
    class Meta:
        db_table = 'scheme_payment_settings'
        


class Denomination(models.Model):
    id          = models.AutoField(primary_key=True)
    id_scheme =  models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='scheme_denomination', null=True)
    value       = models.CharField(max_length = 255)
    sort_order  = models.PositiveIntegerField()
    created_on  = models.DateTimeField(auto_now_add=datetime.now())
    created_by  = models.ForeignKey(accountUser,related_name='denomination_create_by_user', on_delete=models.PROTECT)
    updated_by  = models.ForeignKey(accountUser, related_name='denomination_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on  = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'denomination'
        
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class SchemeWeight(models.Model):
    id          = models.AutoField(primary_key=True)
    id_scheme =  models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='scheme_weight', null=True)
    value       = models.CharField(max_length = 255)
    sort_order  = models.PositiveIntegerField()
    created_on  = models.DateTimeField(auto_now_add=datetime.now())
    created_by  = models.ForeignKey(accountUser,related_name='scheme_weight_create_by_user', on_delete=models.PROTECT)
    updated_by  = models.ForeignKey(accountUser, related_name='scheme_weight_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on  = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'scheme_weight'
        
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class SchemePreCloseDiscountChart(models.Model):
    id_pc_dic       = models.AutoField(primary_key=True)
    id_pc_scheme    =  models.ForeignKey('Scheme', on_delete=models.CASCADE, related_name='scheme_pre_close_chart_id', null=True)
    paid_inc_from   = models.IntegerField(default = 0)
    paid_inc_to     = models.IntegerField(default = 0)
    deduction_type  = models.IntegerField(choices = [(1, 'Percent'),(2, 'Amount')])
    detection_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'scheme_pre_close_settings'
    
    
class SchemeDigiGoldInterestSettings(models.Model):
    id_interest_details  = models.AutoField(primary_key=True)
    scheme              = models.ForeignKey(Scheme, on_delete=models.PROTECT)
    from_day            = models.PositiveIntegerField()
    to_day              = models.PositiveIntegerField()
    interest_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0.000,validators=[MinValueValidator(0.0)])
    
    
    def __str__(self) -> str:
        return 'Scheme Digi Interest Settings - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_digi_gold_interest_details'
        

class SchemeGiftSettings(models.Model):
    id_gift_settings  = models.AutoField(primary_key=True)
    item = models.ForeignKey('otherinventory.OtherInventoryItem', on_delete=models.PROTECT, related_name="scheme_gift_other_inventory_item",null=True,default=None)
    scheme = models.ForeignKey(Scheme, on_delete=models.PROTECT)
    
    def __str__(self) -> str:
        return 'Scheme Gift Settings - ' + str(self.pk)
    
    class Meta:
        db_table = 'scheme_gift_settings'