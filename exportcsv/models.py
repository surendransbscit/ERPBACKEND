from django.db import models
from datetime import datetime, timedelta, date
# Create your models here.

class RawCustomerData(models.Model):
    id = models.AutoField(primary_key=True)
    lastname = models.CharField(max_length=32, null=True)
    firstname = models.CharField(max_length=32, null=True,verbose_name='Customer Name')
    email = models.CharField(max_length=128, blank=True,default=None,null=True)
    mobile = models.CharField(unique=True,max_length=255,null=True,verbose_name='Mobile')
    address1 = models.TextField(blank=True,default=None)
    address2 = models.TextField(null=True,blank=True,default=None)
    address3 = models.TextField(null=True,blank=True,default=None)
    pincode = models.CharField(max_length = 6,blank=True,default=None)
    is_imported = models.BooleanField(default=False)
    error_message = models.TextField(blank=True,default=None,null=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='cus_import_by_user', on_delete=models.PROTECT,null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='cus_import_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'customer_import'
        unique_together =( ('mobile'), )

class RawTagData(models.Model):
    id = models.AutoField(primary_key=True)
    tag_id                  = models.PositiveIntegerField(null=True,default=None)
    old_tag_code            = models.CharField(max_length=255)  # Adjust max_length as needed
    old_tag_id              = models.CharField(max_length=255,null=True, default=None)  # Adjust max_length as needed
    tag_date                = models.DateField(null=False,blank=False)
    tag_current_branch      = models.PositiveIntegerField(null=True, default=None)
    tag_product_id          = models.PositiveIntegerField(null=True, default=None)
    size_id                 = models.PositiveIntegerField(null=True, default=None)
    import_id               = models.PositiveIntegerField(null=True, default=None)
    tag_design_id           = models.PositiveIntegerField(null=True,default=None)
    tag_sub_design_id       = models.PositiveIntegerField(null=True,default=None)
    tag_section_id          = models.PositiveIntegerField(null=True,default=None)
    tag_purity_id           = models.PositiveIntegerField(null=True, default=None)
    tag_supplier_id           = models.PositiveIntegerField(null=True, default=None)
    tag_pcs                 = models.PositiveIntegerField(null=False, default=0)
    tag_uom_id              = models.PositiveIntegerField(null=True, default=None)
    tag_gwt                 = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0)
    tag_lwt                 = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0)
    tag_nwt                 = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0)
    tag_stn_wt              = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0)
    tag_dia_wt              = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0)
    tag_wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tag_wastage_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    tag_mc_type             = models.IntegerField(choices=[(1, 'Per Gram'),(2, 'Per Pcs')],default=1)
    tag_mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tag_buy_rate            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tag_sell_rate           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tag_tax_amount          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tag_item_cost           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tag_huid                = models.CharField(max_length=8,null=True,default=None, error_messages={"unique": "HUID already exists"})
    tag_huid2               = models.CharField(max_length=8,null=True,default=None, error_messages={"unique": "HUID already exists"})
    flat_mc_value           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    import_status           = models.IntegerField(choices=[(1, 'Excel Import Error'),(2, 'Imported'),(3, 'Tag Import Error'),(4, 'Tag Imported')],default=1)
    error_msg               = models.CharField(max_length=255)


    class Meta:
        db_table = 'tag_import'

class RawTagStoneData(models.Model):
    
    id                = models.AutoField(primary_key=True)
    ref_id            = models.PositiveIntegerField(null=True, default=None)
    show_in_lwt       = models.IntegerField(default=1)
    id_stone          = models.PositiveIntegerField(null=True, default=None)
    id_quality_code   = models.PositiveIntegerField(null=True, default=None)
    uom_id            = models.PositiveIntegerField(null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    stone_rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stone_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stone_calc_type   = models.IntegerField(default=1)
    import_status     = models.IntegerField(choices=[(1, 'Excel Import Error'),(2, 'Imported'),(3, 'Tag Import Error'),(4, 'Tag Imported')],default=1)
    error_msg         = models.CharField(max_length=255)
    class Meta:
        db_table = 'tag_import_stone'
    
    indexes = [
            models.Index(fields=['id_stone','uom_id']),
    ]

class RawTagStatusData(models.Model):
    
    id                = models.AutoField(primary_key=True)
    import_id               = models.PositiveIntegerField(null=True, default=None)
    tag_id            = models.PositiveIntegerField(null=True,default=None)
    old_tag_code      = models.CharField(max_length=255)  # Adjust max_length as needed
    tag_code          = models.CharField(max_length=255)  # Adjust max_length as needed
    tag_status        = models.IntegerField(default=1)
    tag_updated_status= models.IntegerField(default=1)
    log_id            = models.PositiveIntegerField(null=True,default=None)
    import_status     = models.IntegerField(choices=[(1, 'Excel Import Error'),(2, 'Imported'),(3, 'Tag Import Error'),(4, 'Tag Imported')],default=1)
    error_msg         = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='tag_status_import_by_user', on_delete=models.PROTECT,null=True)
    class Meta:
        db_table = 'tag_status_import'
    
class RawEmployee(models.Model):
    id = models.AutoField(primary_key=True)
    date_of_join = models.DateField(null=True,blank=False,default=None)
    lastname = models.CharField(max_length=32, null=True)
    firstname = models.CharField(max_length=32, null=True,verbose_name='Customer Name')
    emp_code = models.CharField(max_length=128, blank=True,default=None,null=True)
    mobile = models.CharField(max_length=255,null=True,verbose_name='Mobile',default=None)
    address1 = models.TextField(blank=True,default=None)
    address2 = models.TextField(null=True,blank=True,default=None)
    address3 = models.TextField(null=True,blank=True,default=None)
    is_imported = models.BooleanField(default=False)
    error_message = models.TextField(blank=True,default=None,null=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='emp_import_by_user', on_delete=models.PROTECT,null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='emp_import_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'employee_import'
        
class RawSchemeAccountData(models.Model):
    id = models.BigAutoField(primary_key=True)
    import_id = models.CharField(max_length=255)
    scheme_acc_no = models.CharField(max_length=255)
    cus_pk = models.IntegerField(null=True, default=None)
    scheme_pk = models.IntegerField(null=True, default=None)
    cus_name = models.CharField(max_length=255, null=True)
    cus_mobile = models.CharField(max_length=100, null=True)
    installment_paid = models.IntegerField(null=True, default=None)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    g_name = models.CharField(max_length=20, null=True)
    
    class Meta:
        db_table = 'scheme_account_import'