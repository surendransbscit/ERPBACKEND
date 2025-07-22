from django.db import models
from datetime import datetime
from utilities.constants import PURE_WT_CALC_TYPE_CHOICES
from customers.models import Customers

# Create your models here.

accounts_user = 'accounts.User'

# function to manage branch image upload to corresponding folders
def upload_to_gal(instance, filename):
    return 'images/retail_catalog/category/{filename}'.format(filename=filename)


def upload_to_schemeclass(instance, filename):
    return 'images/catalog_master/scheme_classify/{title}{filename}'.format(
        title=instance.classification_name, filename=filename)


def upload_prod_img(instance, filename):
    return 'images/retail_catalog/product/{filename}'.format(filename=filename)


from  utilities.constants import TAX_TYPE_CHOICES
from  utilities.model_utils import CommonFields


class Metal(models.Model):
    id_metal    = models.AutoField(primary_key=True)
    metal_name  = models.CharField(max_length=60,unique=True,error_messages={"unique" : "Same metal name already exists"})
    metal_code  = models.CharField(max_length=20,unique=True,error_messages={"unique" : "Same metal code already exists"}, null=True)
    created_on  = models.DateTimeField(auto_now_add=datetime.now())
    created_by  = models.ForeignKey(accounts_user, related_name='metals_by_user', on_delete=models.PROTECT)
    updated_on  = models.DateTimeField(blank=True, null=True)
    updated_by  = models.ForeignKey(accounts_user, related_name='metals_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    metal_status= models.BooleanField(default=True)

    def __str__(self):
        return 'Metal (ID %s) ' % (self.id_metal, )
    
    class Meta:
        db_table = 'metal'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    

class Purity(models.Model):
    id_purity   = models.AutoField(primary_key=True)
    purity      = models.DecimalField(max_digits=10, decimal_places=4, unique=True, error_messages={'unique': "Purity Value Already exists"})
    weight_show_in_print = models.IntegerField(choices=((0, "No"),(1, "Yes")),default=0)
    description = models.CharField(max_length=45, blank=True)
    status      = models.BooleanField(default=True)
    created_by  = models.ForeignKey(accounts_user, related_name='purity_by_user', on_delete=models.PROTECT)
    created_on  = models.DateTimeField(auto_now_add=datetime.now())
    updated_on  = models.DateTimeField(blank=True, null=True)
    updated_by  = models.ForeignKey(accounts_user, related_name='purity_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return 'Purity (ID %s) ' % (self.id_purity, )

    class Meta:
        db_table = 'erp_purity'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    
class SchemeClassification(models.Model):
    id_classification = models.AutoField(primary_key=True)
    classification_name = models.CharField(max_length=256)
    description = models.TextField()
    active = models.BooleanField(default = True)
    logo = models.ImageField(upload_to=upload_to_schemeclass, null=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='scheme_class_by_user', on_delete=models.PROTECT)
    updated_on = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='scheme_class_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return 'Scheme Classification (ID %s) ' % (self.id_classification)
    
    class Meta:
        db_table = 'scheme_classification'
    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class Category(models.Model):
    id_category     = models.AutoField(primary_key=True)
    id_metal        = models.ForeignKey(Metal,on_delete=models.PROTECT,related_name='category_metal')
    id_purity       = models.ManyToManyField(Purity, blank=True)
    sort            = models.IntegerField(unique=True, error_messages={"unique": "Category with this sort number already exists"},blank=True, null=True)
    cat_name        = models.CharField(max_length=65,unique=True,error_messages={"unique": "Category with this name already exists"})
    cat_type        = models.CharField(max_length=45,
                                choices=(("1", "Ornament"), ("2", "Bullion"),
                                         ("3", "Stone"), ("4", "Alloy"), ("5", "Old Metal")))
    cat_code        = models.CharField(max_length=10,unique=True,error_messages={"unique": "Category with this short code already exists"}, null=True)
    description     = models.TextField(blank=True)
    is_multimetal   = models.BooleanField(default=False)
    status          = models.BooleanField(default=True)
    image           = models.ImageField(upload_to=upload_to_gal, blank=True, null=True)
    show_in_metal_rate =  models.BooleanField(default=False)
    created_on      = models.DateTimeField(auto_now_add=datetime.now())
    created_by      = models.ForeignKey(accounts_user, related_name='category_by_user', on_delete=models.PROTECT)
    updated_on      = models.DateTimeField(blank=True, null=True)
    updated_by      = models.ForeignKey(accounts_user, related_name='category_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return 'Category (ID %s) ' % (self.id_category )

    class Meta:
        db_table = 'erp_category'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    

class CategoryPurityRate(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category,related_name='erp_cat_purity_rate_category',on_delete=models.PROTECT)
    purity = models.ForeignKey(Purity, on_delete=models.PROTECT,related_name='erp_cat_purity_rate_purity')
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=3)
    show_in_listing =  models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'accounts.User', related_name='erp_cat_purity_rate_added_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='erp_cat_purity_rate_updated_by_user', null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    updated_on = models.DateTimeField(null=True)

    class Meta:
        db_table = 'erp_category_purity_rate'
    
    def __str__(self) -> str:
        return 'Category Purity Rate - ' + str(self.pk)
    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class ProductCalculationType(models.Model):
    id_calculation_type = models.AutoField(primary_key=True)
    name                = models.CharField(max_length=20,unique=True,error_messages={"unique": "Name already exists"})
    created_by          = models.ForeignKey(accounts_user, related_name='calculation_type_by_user', on_delete=models.PROTECT)
    updated_by          = models.ForeignKey(accounts_user, related_name='calculation_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on          = models.DateTimeField(auto_now_add=datetime.now())
    updated_on          = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'erp_product_calculation_type'

class Product(models.Model):
    pro_id              = models.AutoField(primary_key=True)
    id_metal            = models.ForeignKey(Metal,on_delete=models.PROTECT,related_name='product_metal')
    cat_id              = models.ForeignKey(Category,related_name='product_category',on_delete=models.PROTECT)
    hsn_code            = models.CharField(max_length=45, blank=True)
    stock_type          = models.CharField(max_length=2,choices=(("0", "Tagged"), ("1", "Non-Tagged")))
    tax_type            = models.IntegerField(choices=TAX_TYPE_CHOICES, default=2)
    sales_mode          = models.CharField(max_length=2,choices=(("0", "Fixed Rate"),("1", "Flexible Rate")))
    short_code          = models.CharField(max_length=3,unique=True,error_messages={"unique": "Product with this short code already exists"}, null=True)
    product_name        = models.CharField(max_length=75,unique=True,error_messages={"unique": "Product with this name already exists"})
    has_size            = models.CharField(max_length=2,choices=(("0", "No"),("1", "Yes")),default=0)
    has_weight_range    = models.CharField(max_length=2,choices=(("0", "No"),("1", "Yes")),default=0)
    calculation_based_on = models.ForeignKey(ProductCalculationType,related_name='product_calculation_type',on_delete=models.PROTECT, null=True, default=None)
    tax_id              = models.ForeignKey('retailmasters.Taxmaster',related_name='product_tax',on_delete=models.PROTECT,null=True,default=None)
    uom_id              = models.ForeignKey('retailmasters.Uom',related_name='product_uom_id',on_delete=models.PROTECT,null=True,default=None,blank=True)
    status              = models.BooleanField(default=True)
    image               = models.ImageField(upload_to=upload_prod_img, blank=True, null=True)
    reorder_based_on    = models.IntegerField(choices=((1, "Weight Range"),(2, "Size"),(3,"Both")), null=True, default=None)
    wastage_calc_type   = models.IntegerField(choices=((1, "Gross Weight"),(2, "Net Weight")), default=1)
    mc_calc_type        = models.IntegerField(choices=((1, "Gross Weight"),(2, "Net Weight")), default=1)
    fixed_rate_type     = models.IntegerField(choices=((1, "Based on Weight"),(2, "Based on Rate")), default=2)
    report_based_on_weight_range= models.IntegerField(choices=((0, "No"),(1, "Yes")),default=1)
    report_based_on_design= models.IntegerField(choices=((0, "No"),(1, "Yes")),default=1)
    weight_show_in_print= models.IntegerField(choices=((0, "No"),(1, "Yes")),default=0)
    other_weight        = models.ManyToManyField('retailmasters.OtherWeight', blank=True, related_name='other_weights')
    description         = models.CharField(max_length=45, null=True,default=None)
    min_touch           = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    max_touch           = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    created_by          = models.ForeignKey(accounts_user, related_name='product_by_user', on_delete=models.PROTECT)
    updated_by          = models.ForeignKey(accounts_user, related_name='product_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on          = models.DateTimeField(auto_now_add=datetime.now())
    updated_on          = models.DateTimeField(blank=True, null=True)
    add_lot_excess_weight= models.IntegerField(choices=((0, "No"),(1, "Yes")),default=0)
    show_in_enquiry_form              = models.BooleanField(default=False)

    def __str__(self):
        return 'Product (ID %s) ' % (self.pro_id, )

    class Meta:
        db_table = 'erp_product'

    LOGGING_IGNORE_FIELDS = ('created_time', 'created_by', 'updated_time',
                             'updated_by')

class ErpReorderSettings(models.Model):
    
    id_reorder_setting   = models.AutoField(primary_key=True)
    branch = models.ForeignKey('retailmasters.Branch',related_name='reorder_setting_branch',on_delete=models.PROTECT)
    product = models.ForeignKey(Product,related_name='reorder_setting_product', on_delete=models.PROTECT)
    design = models.ForeignKey('retailcataloguemasters.Design',on_delete=models.PROTECT,related_name='reorder_setting_design_id')
    sub_design = models.ForeignKey('retailcataloguemasters.SubDesign',on_delete=models.PROTECT,related_name='reorder_setting_sub_design_id',null=True, default=None)
    size = models.ForeignKey('retailmasters.Size',on_delete=models.PROTECT,related_name="reorder_setting_size",null=True, default=None)
    weight_range = models.ForeignKey('retailmasters.WeightRange',on_delete=models.PROTECT,related_name="reorder_setting_weight_range",null=True, default=None)
    min_pcs = models.PositiveIntegerField()
    max_pcs = models.PositiveIntegerField()
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey('accounts.User', related_name='reorder_setting_user', on_delete=models.PROTECT,default=None,null=True)

    def __str__(self):
        return 'Reorder setting (ID %s) ' % (self.id_reorder_setting )
    class Meta:
        db_table = 'erp_reorder_settings'
    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by')

class Design(models.Model):
    id_design    = models.AutoField(primary_key=True)
    design_name  = models.CharField(max_length=75,unique=True,error_messages={"unique": "Design name already exists"})
    design_code  = models.CharField(max_length=20,unique=True,error_messages={"unique" : "Same Design code already exists"}, null=True)
    status       = models.BooleanField(default=True)
    show_in_enquiry_form              = models.BooleanField(default=False)
    created_by   = models.ForeignKey(accounts_user, related_name='design_by_user', on_delete=models.PROTECT)
    updated_by   = models.ForeignKey(accounts_user, related_name='design_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on   = models.DateTimeField(auto_now_add=datetime.now())
    updated_on   = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'erp_design'


class SubDesign(models.Model):
    id_sub_design    = models.AutoField(primary_key=True)
    sub_design_name  = models.CharField(max_length=75,unique=True,error_messages={"unique": "Sub Design name already exists"})
    status           = models.BooleanField(default=True)
    created_by       = models.ForeignKey(accounts_user, related_name='sub_design_by_user', on_delete=models.PROTECT)
    updated_by       = models.ForeignKey(accounts_user, related_name='sub_design_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on       = models.DateTimeField(auto_now_add=datetime.now())
    updated_on       = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'erp_sub_design'

class ProductMapping(models.Model):
    id_product_mapping  = models.AutoField(primary_key=True)
    id_product          = models.ForeignKey(Product,on_delete=models.PROTECT,related_name='product_id')
    id_design           = models.ForeignKey(Design,on_delete=models.PROTECT,related_name='design_id')
    created_by          = models.ForeignKey(accounts_user, related_name='created_by_user', on_delete=models.PROTECT)
    created_on          = models.DateTimeField(auto_now_add=datetime.now())
    class Meta:
        db_table = 'erp_design_mapping'
        indexes = [
            models.Index(fields=['id_product', 'id_design']),  # Composite index
        ]
        constraints = [
            models.UniqueConstraint(fields=['id_product', 'id_design'], name='unique_product_design')
        ]

class SubDesignMapping(models.Model):
    id_product_mapping  = models.AutoField(primary_key=True)
    id_product          = models.ForeignKey(Product,on_delete=models.PROTECT,related_name='mapping_product_id')
    id_design           = models.ForeignKey(Design,on_delete=models.PROTECT,related_name='mapping_design_id')
    id_sub_design       = models.ForeignKey(SubDesign,on_delete=models.PROTECT,related_name='mapping_sub_design_id')
    created_by          = models.ForeignKey(accounts_user, related_name='sub_design_mapped_by_user', on_delete=models.PROTECT)
    created_on          = models.DateTimeField(auto_now_add=datetime.now())
    class Meta:
        db_table = 'erp_sub_design_mapping'
        indexes = [
            models.Index(fields=['id_product', 'id_design' , 'id_sub_design']),  # Composite index
        ]
        constraints = [
            models.UniqueConstraint(fields=['id_product', 'id_design' , 'id_sub_design'], name='unique_product_design_sub_design')
        ]

class MakingAndWastageSettings(models.Model):
    id_mc_wast_settings  = models.AutoField(primary_key=True)
    id_product           = models.ForeignKey(Product,related_name='mc_wast_product', on_delete=models.PROTECT)
    id_design            = models.ForeignKey(Design,related_name='mc_wast_design', on_delete=models.PROTECT)
    id_sub_design        = models.ForeignKey(SubDesign,related_name='mc_wast_sub_design', on_delete=models.PROTECT, null=True, default=None)
    id_weight_range      = models.ForeignKey('retailmasters.WeightRange',related_name='mc_wast_weight_range', on_delete=models.PROTECT, null=True,default=None)
    supplier = models.ManyToManyField('retailmasters.Supplier',related_name="mc_va_suppliers")
    purity               = models.ForeignKey(Purity, on_delete=models.PROTECT, null=True, default=None,related_name='mc_wast_purity')
    purchase_touch       = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    pure_wt_type   = models.IntegerField(choices=((1, 'Net weight * Purchase Touch'),
                                                  (2, '(Purchase Touch + Purchase Wastage%) * Net Weight'),
                                                  (3, '(Net weight * Purchase Touch) * Purchase Wastage%')), default=2)
    purchase_mc_type      = models.IntegerField(choices=((1, "Gross weight"), (2, "Net weight")),default=1)
    purchase_mc             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    purchase_va_type      = models.IntegerField(choices=((1, "Gross weight"), (2, "Net weight")),default=1)
    purchase_va             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    purchase_flat_mc   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    purchase_sales_rate   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00, null=True)
    retail_touch       = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    retail_mc_type      = models.IntegerField(choices=((1, "Gross weight"), (2, "Net weight")),default=1)
    retail_mc             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    retail_va_type      = models.IntegerField(choices=((1, "Gross weight"), (2, "Net weight")),default=1)
    retail_va             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    retail_flat_mc   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    vip_retail_touch       = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    vip_retail_mc_type      = models.IntegerField(choices=((1, "Gross weight"), (2, "Net weight")),default=1)
    vip_retail_mc             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    vip_retail_va_type      = models.IntegerField(choices=((1, "Gross weight"), (2, "Net weight")),default=1)
    vip_retail_va             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    vip_retail_flat_mc   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    
    # mc_type              = models.CharField(max_length=2,choices=(("1", "Per Gram"), ("2", "Per Piece")),default=1)
    # min_mc_value             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # max_mc_value             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # wastage_type              = models.IntegerField(choices=((1, "Percent"), (2, "Weight")),default=1)
    # min_wastage_percentage   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # max_wastage_percentage   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # plt_mc_type              = models.CharField(max_length=2,choices=(("1", "Per Gram"), ("2", "Per Piece")),default=1)
    # plt_min_mc_value             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # plt_max_mc_value             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # plt_wastage_type              = models.IntegerField(choices=((1, "Percent"), (2, "Weight")),default=1)
    # plt_min_wastage_percentage   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # plt_max_wastage_percentage   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # dia_mc_type              = models.CharField(max_length=2,choices=(("1", "Per Gram"), ("2", "Per Piece")),default=1)
    # dia_min_mc_value             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # dia_max_mc_value             = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # dia_wastage_type              = models.IntegerField(choices=((1, "Percent"), (2, "Weight")),default=1)
    # dia_min_wastage_percentage   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    # dia_max_wastage_percentage   = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    created_on           = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by           = models.ForeignKey('accounts.User', related_name='mc_wastage_settings_created_by_user', on_delete=models.PROTECT, null=True)
    

    class Meta:
        db_table = 'erp_mc_wast_settings'
        indexes = [
            models.Index(fields=['id_product','id_design','id_sub_design','id_weight_range']),  # Composite index
        ]
        constraints = [
            models.UniqueConstraint(fields=['id_product','id_design','id_sub_design','id_weight_range'], name='mc_wast_settings_constraint')
        ]
    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by')
    

class CustomerMakingAndWastageSettings(models.Model):
    id_mc_wast_settings  = models.AutoField(primary_key=True)
    id_product           = models.ForeignKey(Product,related_name='customer_mc_wast_product', on_delete=models.PROTECT)
    id_design            = models.ForeignKey(Design,related_name='customer_mc_wast_design', on_delete=models.PROTECT)
    id_sub_design        = models.ForeignKey(SubDesign,related_name='cuatomer_mc_wast_sub_design', on_delete=models.PROTECT, null=True, default=None)
    purity               = models.ForeignKey(Purity, on_delete=models.PROTECT, null=True, default=None,related_name='customer_mc_wast_purity')
    id_weight_range      = models.ForeignKey('retailmasters.WeightRange',related_name='customer_mc_wast_weight_range', on_delete=models.PROTECT, null=True,default=None)
    mc_type              = models.IntegerField(choices=((1, "Gross weight"), (2, "Net weight")),default=1)
    min_mc_value         = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    max_mc_value         = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    flat_mc_min          = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    flat_mc_max          = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    sales_rate           = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00, null=True)
    sales_rate_type      = models.IntegerField(choices=((1, "Amount"), (2, "Percentage")),default=1,null=True)
    va_type              = models.IntegerField(choices=((1, "Gross weight"), (2, "Net weight")),default=1)
    min_va_value         = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    max_va_value         = models.DecimalField(max_length=10,max_digits=10,decimal_places=2,default=0.00)
    created_on           = models.DateTimeField(auto_now_add=datetime.now(), null=True)
    created_by           = models.ForeignKey('accounts.User', related_name='customer_mc_wastage_settings_created_by_user', on_delete=models.PROTECT, null=True)
    

    class Meta:
        
        db_table = 'erp_customer_mc_wast_settings'
        indexes = [
            models.Index(fields=['id_product','id_design','id_sub_design','id_weight_range']),  # Composite index
        ]
        constraints = [
            models.UniqueConstraint(fields=['id_product','id_design','id_sub_design','id_weight_range'], name='customer_mc_wast_settings_constraint')
        ]
    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by')
        

class Clarity(models.Model):
    id_clarity = models.AutoField(primary_key=True)
    clarity = models.CharField(max_length=45, unique=True, error_messages={
                               'unique': "Clarity Already exists"})
    status = models.BooleanField(default=True)
    description = models.CharField(max_length=45, blank=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='retclarity_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='retclarity_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return 'Clarity (ID %s) ' % (self.pk, )

    class Meta:
        # managed = False
        db_table = 'clarity'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


# Not used -- Diamond color
class Color(models.Model):
    id_color = models.AutoField(primary_key=True)
    color = models.CharField(max_length=45, unique=True, error_messages={
        'unique': "Color Already exists"})
    status = models.BooleanField(default=True)
    description = models.CharField(max_length=45, blank=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='retcolor_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='retcolor_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return 'Color (ID %s) ' % (self.pk, )

    class Meta:
        # managed = False
        db_table = 'color'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


# Not used -- Diamond cut
class RetCut(models.Model):
    id_cut = models.AutoField(primary_key=True)
    cut = models.CharField(max_length=45, unique=True, error_messages={
        'unique': "Cut Already exists"})
    description = models.CharField(max_length=45, blank=True, null=True)
    status = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='retcut_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='retcut_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return 'Cut (ID %s) ' % (self.pk, )

    class Meta:
        # managed = False
        db_table = 'cut'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class Shape(models.Model):
    id_ret_shape = models.AutoField(primary_key=True)
    shape = models.CharField(max_length=45, unique=True, error_messages={
                             'unique': "Shape already exist"})
    description = models.CharField(max_length=45, blank=True, null=True)
    status = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='retshapes_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='retshapes_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'shape'

    def __str__(self) -> str:
        return 'Shape (ID %s) ' % (self.pk, )

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class QualityCode(models.Model):
    quality_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=12, unique=True, error_messages={
                            'unique': "Quality Code already exist"})
    status = models.BooleanField(default=True)
    color = models.ForeignKey(
        'Color', related_name='quality_bycolor', on_delete=models.PROTECT)
    clarity = models.ForeignKey(
        'Clarity', related_name='quality_byclarity', on_delete=models.PROTECT)
    cut = models.ForeignKey(
        'RetCut', related_name='quality_bycut', on_delete=models.PROTECT)
    shape = models.ForeignKey(
        'Shape', related_name='quality_byshape', on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='retquality_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='retquality_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'quality_code'
        unique_together = [[
            'color',
            'cut',
            'shape',
            'clarity'
        ]]

    def __str__(self) -> str:
        return 'Quality Code (ID %s) ' % (self.pk, )

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')



class DiamondRateMaster(models.Model):
    rate_id = models.AutoField(primary_key=True)
    quality_code = models.OneToOneField(
        'QualityCode', on_delete=models.PROTECT, related_name='diamond_rates')
    effective_date = models.DateField()
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='ret_diamondrate_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='ret_diamondrate_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ret_diamond_rate'

    def __str__(self) -> str:
        return 'Diamond Rate Master (ID %s) ' % (self.pk, )

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    
    
class PurchaseDiamondRateMaster(models.Model):
    rate_id = models.AutoField(primary_key=True)
    quality_code = models.OneToOneField(
        'QualityCode', on_delete=models.PROTECT, related_name='purchase_diamond_rates')
    supplier = models.ManyToManyField('retailmasters.Supplier',related_name="purchase_diamond_rate_suppliers")
    effective_date = models.DateField()
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(
        'accounts.User', related_name='ret_purchase_diamondrate_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='ret_purchase_diamondrate_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ret_purchase_diamond_rate_master'

    def __str__(self) -> str:
        return 'Purchase Diamond Rate Master - (%s) ' % (self.pk, )

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class DiamondCentRate(models.Model):
    id_cents_rate = models.AutoField(primary_key=True)
    id_rate = models.ForeignKey(
        'DiamondRateMaster', related_name='diamond_cent_rates', on_delete=models.CASCADE)
    from_cent = models.DecimalField(max_digits=12, decimal_places=3)
    to_cent = models.DecimalField(max_digits=12, decimal_places=3)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='diamond_cent_rates_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ret_diamond_cent_rates'

    def __str__(self) -> str:
        return 'Diamond Cent Rate (ID %s) ' % (self.pk, )

    LOGGING_IGNORE_FIELDS = ('updated_on',
                             'updated_by')
    

class PurchaseDiamondCentRate(models.Model):
    id_cent_rate = models.AutoField(primary_key=True)
    id_rate = models.ForeignKey(
        'PurchaseDiamondRateMaster', related_name='purchase_diamond_cent_rates', on_delete=models.CASCADE)
    from_cent = models.DecimalField(max_digits=12, decimal_places=3)
    to_cent = models.DecimalField(max_digits=12, decimal_places=3)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    updated_by = models.ForeignKey(
        'accounts.User', related_name='purchase_diamond_cent_rates_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ret_purchase_diamond_cent_rates'

    def __str__(self) -> str:
        return 'Purchase Diamond Cent Rate (ID %s) ' % (self.pk, )

    LOGGING_IGNORE_FIELDS = ('updated_on',
                             'updated_by')


# Stone - Model - Stone details with UOM associated
class Stone(models.Model):
    stone_id            = models.AutoField(primary_key=True)
    stone_name          = models.CharField(max_length=100, unique=True, error_messages={"unique": "Stone with this name already exists"})
    stone_code          = models.CharField(max_length=100)
    stone_type          = models.IntegerField(choices=((1, "Diamond"), (2, "Gem Stones"),(3, "Others")))
    uom_id              = models.ForeignKey('retailmasters.Uom',on_delete=models.PROTECT,related_name='stone_uom')
    is_certificate_req  = models.BooleanField(default=False)
    show_less_wt        = models.BooleanField(default=False)
    is_4c_req           = models.BooleanField(default=False)
    stone_status        = models.BooleanField(default=True)
    created_on          = models.DateTimeField(auto_now_add=datetime.now())
    created_by          = models.ForeignKey(accounts_user,related_name='stone_by_user', on_delete=models.PROTECT)
    updated_on          = models.DateTimeField(blank=True, null=True)
    updated_by          = models.ForeignKey(accounts_user, related_name='stone_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return 'Stone (ID %s) ' % (self.stone_id, )

    class Meta:
        # managed = False
        db_table = 'erp_stone'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class Section(models.Model):
    id_section       = models.AutoField(primary_key=True)
    section_name     = models.CharField(max_length=20,unique=True,error_messages={"unique": "Section name already exists"})
    status           = models.BooleanField(default=True)
    created_by       = models.ForeignKey(accounts_user, related_name='section_by_user', on_delete=models.PROTECT)
    updated_by       = models.ForeignKey(accounts_user, related_name='section_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on       = models.DateTimeField(auto_now_add=datetime.now())
    updated_on       = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'erp_section'

class TagStatusMaster(models.Model):
    id_tag_status = models.AutoField(primary_key=True)
    status_name   = models.CharField(max_length=20,unique=True,error_messages={"unique": "Status Name already exists"})
    created_by    = models.ForeignKey(accounts_user, related_name='tag_status_by_user', on_delete=models.PROTECT)
    updated_by    = models.ForeignKey(accounts_user, related_name='tag_status_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on    = models.DateTimeField(auto_now_add=datetime.now())
    updated_on    = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'erp_tag_status_master'


class ProductSection(models.Model):
    id_pro_section = models.AutoField(primary_key=True)
    id_product     = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='section_product_id')
    id_section     = models.ForeignKey(Section,on_delete=models.PROTECT,related_name='section_id')
    created_by     = models.ForeignKey(accounts_user, related_name='product_section_by_user', on_delete=models.PROTECT)
    created_on     = models.DateTimeField(auto_now_add=datetime.now())
    class Meta:
        db_table = 'erp_product_section'


class CounterWiseTarget(models.Model):
    id_counter_target = models.AutoField(primary_key=True)
    branch = models.ForeignKey('retailmasters.Branch',related_name='counter_target_branch',on_delete=models.PROTECT)
    section = models.ForeignKey(Section,on_delete=models.PROTECT,related_name='counter_target_section')
    product = models.ForeignKey(Product,on_delete=models.PROTECT,related_name='counter_target_product', null=True, default=None)
    target_pieces = models.PositiveIntegerField(default=0)
    target_weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    from_date = models.DateField()
    to_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True,default=0)

    pcs_target_value = models.DecimalField(max_length=10,max_digits=10,decimal_places=2, null=True, blank=True)
    wt_target_value = models.DecimalField(max_length=10,max_digits=10,decimal_places=2, null=True, blank=True)
    amt_target_value = models.DecimalField(max_length=10,max_digits=10,decimal_places=2, null=True, blank=True)

    pcs_target_type = models.IntegerField(choices=((1, "Per Piece"),(2, "Flat")), default=1, blank=True)
    wt_target_type = models.IntegerField(choices=((1, "Per Percentage"),(2, "Flat")), default=1, blank=True)  
    amt_target_type = models.IntegerField(choices=((1, "Per Gram"),(2, "Flat")), default=1, blank=True)

    
    class Meta:
        db_table = 'counter_wise_target'

    def __str__(self) -> str:
        return 'Counter Target (ID %s) ' % (self.pk, )
    

class RepairDamageMaster(models.Model):
    TAX_TYPE_CHOICES = [(1, 'Inclusive'),(2, 'Exclusive')]

    id_repair        = models.AutoField(primary_key=True)
    name             = models.CharField(max_length=75,unique=True,error_messages={"unique": "Repair Damage Master name already exists"})
    tax_id           = models.ForeignKey('retailmasters.Taxmaster', on_delete=models.CASCADE,null=True,default=None)
    tax_type         = models.IntegerField(choices=TAX_TYPE_CHOICES, default=2)
    status           = models.BooleanField(default=True)
    created_by       = models.ForeignKey(accounts_user, related_name='repairdamage_by_user', on_delete=models.PROTECT)
    updated_by       = models.ForeignKey(accounts_user, related_name='repairdamage_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on       = models.DateTimeField(auto_now_add=datetime.now())
    updated_on       = models.DateTimeField(blank=True, null=True)
    class Meta:
        db_table = 'erp_repair_damage_master'

class CustomerEnquiry(models.Model):
    TYPE_CHOICES = [(1, 'InStock'),(2, 'OutStock')]

    id_enquiry = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customers,related_name='customer_enquiry',on_delete=models.PROTECT)
    product = models.ForeignKey(Product,on_delete=models.PROTECT,related_name='customer_enquiry_product', null=True, default=None)
    design = models.ForeignKey(Design,on_delete=models.PROTECT,related_name='customer_enquiry_design', null=True, default=None)
    sub_design = models.ForeignKey(SubDesign,on_delete=models.PROTECT,related_name='customer_enquiry_sub_design', null=True, default=None)
    weight_range = models.CharField(max_length=240)
    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    type = models.IntegerField(choices=TYPE_CHOICES, default=1)
    enquiry = models.CharField(max_length=240)
    tag_id = models.ForeignKey("inventory.ErpTagging", on_delete=models.CASCADE,null=True,related_name="customer_enquiry_tag_id", default=None)
    created_by       = models.ForeignKey(accounts_user, related_name='customer_enquiry_by_user', on_delete=models.PROTECT)
    updated_by       = models.ForeignKey(accounts_user, related_name='customer_enquiry_updated_by_user', blank=True, null=True, on_delete=models.SET_NULL)
    created_on       = models.DateTimeField(auto_now_add=datetime.now())
    updated_on       = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'erp_customer_enquiry'

    def __str__(self) -> str:
        return 'Customer Enquiry (ID %s) ' % (self.pk, )