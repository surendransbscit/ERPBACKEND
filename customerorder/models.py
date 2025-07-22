from django.db import models
from datetime import datetime, date
from django.core.validators import MinValueValidator, MaxValueValidator
import os
import uuid
from  utilities.constants import (SHOW_IN_LWT_CHOICES)
from django.utils import timezone


accountUser = 'accounts.User'

def upload_order_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    order_type = "Customer Order"
    if(instance.order_detail.order.order_type == 1):
        order_type = "Customer Order"
    elif(instance.order_detail.order.order_type == 2):
        order_type = "Purchase Order"
    else:
        order_type = "Repair Order"
    unique_id = uuid.uuid4()
    return 'order_images/{type}/order_{order_id}/order_detail_{det_id}/{title}{ext}'.format(order_id=instance.order_detail.order.order_id, type=order_type,
                                                                                         det_id=instance.order_detail.detail_id, title=instance.name, ext=file_extension)
    
def upload_order_voice_note(instance, filename):
    """Function to generate file path for order voice notes."""
    _, file_extension = os.path.splitext(filename)
    name = 'order_voice_note'
    order_type = "Customer Order"
    if(instance.order.order_type == 1):
        order_type = "Customer Order"
    elif(instance.order.order_type == 2):
        order_type = "Purchase Order"
    else:
        order_type = "Repair Order"
    unique_id = uuid.uuid4()
    return f'order_voice_notes/{order_type}/order_{instance.order.order_id}/order_detail_{instance.detail_id}/{name}{file_extension}'


def upload_order_video(instance, filename):
    """
    Generate a unique file path for storing order-related video recordings.
    """
    _, file_extension = os.path.splitext(filename)

    order_type = "Customer Order"
    if (instance.order_detail.order.order_type == 1):
        order_type = "Customer Order"
    elif (instance.order_detail.order.order_type == 2):
        order_type = "Purchase Order"
    else:
        order_type = "Repair Order"

    unique_id = uuid.uuid4()

    return 'order_videos/{type}/order_{order_id}/order_detail_{det_id}/{title}_{uid}{ext}'.format(
        order_id=instance.order_detail.order.order_id,
        type=order_type,
        det_id=instance.order_detail.detail_id,
        title=instance.name,
        uid=unique_id,
        ext=file_extension
    )

# THis for Audio File
def upload_order_audio(instance, filename):
    """Generate a unique file path for storing order-related audio recordings."""
    _, file_extension = os.path.splitext(filename)
    order_type = "Customer Order"
    
    if instance.order_detail.order.order_type == 1:
        order_type = "Customer Order"
    elif instance.order_detail.order.order_type == 2:
        order_type = "Purchase Order"
    else:
        order_type = "Repair Order"
    
    unique_id = uuid.uuid4()
    return f'order_audios/{order_type}/order_{instance.order_detail.order.order_id}/order_detail_{instance.order_detail.detail_id}/{unique_id}{file_extension}'

class ERPOrder(models.Model):
    
    ORDER_TYPE_CHOICES = [
        (1, 'Customer Order'),
        (2, 'Purchase Order'),
        (3, 'Repair Order'),
        (4, 'Customized Order'),
    ]
    
    ADDED_THROUGH_CHOICES = [
        (1, 'Admin'),
        (2, 'Mobile App'),
    ]
    
    RATE_FIXED_TYPE_CHOICES = [
        (1, 'On billing date rate'),
        (2, 'On order date'),
    ]
    
    order_id = models.AutoField(primary_key=True)
    order_branch = models.ForeignKey('retailmasters.Branch', on_delete=models.PROTECT, related_name='order_branch_id')
    fin_year = models.ForeignKey('retailmasters.FinancialYear',on_delete=models.CASCADE, null=True, default=None)
    order_type = models.IntegerField(choices=ORDER_TYPE_CHOICES, verbose_name='Order type', default=1) 
    order_no = models.CharField(max_length=255)
    order_date = models.DateField()
    customer = models.ForeignKey('customers.Customers', on_delete=models.PROTECT, related_name='order_customer_id', null=True, default=None)
    supplier = models.ForeignKey('retailmasters.Supplier', on_delete=models.PROTECT, related_name='purchase_order_supplier', null=True, default=None)
    nick_name = models.CharField(max_length=255, null=True, default=None)
    is_rate_fixed_on_order = models.IntegerField(choices=RATE_FIXED_TYPE_CHOICES,default=2)
    added_through = models.IntegerField(choices=ADDED_THROUGH_CHOICES, default=1)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(accountUser, related_name='order_created_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(accountUser,related_name='order_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)
    id_counter = models.ForeignKey('retailmasters.Counter', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name="order_created_counter")
    
    def __str__(self) -> str:
        return 'ERP Order - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_order'
        
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    

class ERPOrderDetails(models.Model):
    
    MC_TYPE_CHOICES = [
        (1, "Per Gram"),
        (2, "Per Piece")
        ]
    
    TAX_TYPE_CHOICES = [
        (1, 'Inclusive'),
        (2, 'Exclusive'),
    ]
    
    detail_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(ERPOrder, on_delete=models.PROTECT)
    purity = models.ForeignKey('retailcataloguemasters.Purity', on_delete=models.PROTECT, related_name="order_purity",default=None,null=True,blank=False,)
    uom = models.ForeignKey('retailmasters.Uom',on_delete=models.PROTECT, related_name="order_uom",default=None,null=True)
    erp_tag = models.ForeignKey('inventory.ErpTagging', on_delete=models.SET_NULL, null=True, default=None, related_name="order_tag")
    product = models.ForeignKey('retailcataloguemasters.Product', on_delete=models.PROTECT, related_name="order_product", null=True, default=None)
    design = models.ForeignKey('retailcataloguemasters.Design', on_delete=models.PROTECT, related_name="order_design",default=None,null=True,blank=False,)
    sub_design = models.ForeignKey('retailcataloguemasters.SubDesign', on_delete=models.PROTECT, related_name="order_sub_design",default=None,null=True,blank=False)
    size = models.ForeignKey('retailmasters.Size',on_delete=models.PROTECT,related_name="order_size", null=True,blank=False, default=None)
    repair_type = models.ForeignKey('retailcataloguemasters.RepairDamageMaster', on_delete=models.PROTECT, related_name="order_repair_type",default=None,null=True,blank=False,)
    order_repair_type = models.ManyToManyField('retailcataloguemasters.RepairDamageMaster', blank=True, related_name='order_repair_item_type')
    pieces = models.PositiveIntegerField(null=False, blank=False)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    diamond_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    calculation_type = models.ForeignKey('retailcataloguemasters.ProductCalculationType', on_delete=models.PROTECT, related_name="order_calculation_type",default=None,null=True,blank=False)
    wastage_percent = models.PositiveIntegerField(null=True, default=0, blank=False)
    wastage_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    mc_type = models.IntegerField(choices=MC_TYPE_CHOICES, default=1)
    mc_value = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    other_charges_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    other_metal_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    taxable_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, validators=[MinValueValidator(0.0)],default=0.0)
    tax_type = models.IntegerField(choices=TAX_TYPE_CHOICES, verbose_name='Tax type',null=True, default=None) 
    tax = models.ForeignKey('retailmasters.Taxmaster',related_name='order_tax',on_delete=models.PROTECT,null=True,default=None)
    tax_percent = models.PositiveIntegerField(null=True, default=None)
    tax_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    cgst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    sgst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    igst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    discount_amnt = models.DecimalField(max_digits=10, decimal_places=2, default = 0,validators=[MinValueValidator(0.00)])
    order_status = models.ForeignKey('retailmasters.ERPOrderStatus', on_delete=models.PROTECT, related_name='order_status')
    internal_order_process = models.ForeignKey('retailmasters.ERPInternalOrderStatus', on_delete=models.PROTECT, related_name='internal_order_status',default=None, null=True,blank=True)
    internal_order_process_status = models.IntegerField(choices=[(1, 'Issue'),(2, 'Completed')], default=1)
    linked_by = models.ForeignKey(accountUser,related_name='order_tag_linked_by_user', null=True, default=None, on_delete=models.PROTECT)
    linked_date = models.DateField(null=True, default=None)
    unlinked_by = models.ForeignKey(accountUser,related_name='order_tag_unlinked_by_user', null=True, default=None, on_delete=models.PROTECT)
    unlinked_date = models.DateField(null=True, default=None)
    unlinked_reason = models.TextField(null=True, default=None)
    customer_due_date = models.DateField(null=True, default=None)
    karigar_due_date = models.DateField(null=True, default=None)
    remarks = models.TextField(null=True,blank=True, default=None)
    cancel_reason = models.TextField(null=True, default=None)
    cancelled_by = models.ForeignKey(accountUser,related_name='order_detail_updated_by_user', null=True, default=None, on_delete=models.PROTECT)
    cancelled_date = models.DateField(null=True, default=None)
    updated_by = models.ForeignKey(accountUser,related_name='order_details_status_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(auto_now=datetime.now(tz=timezone.utc),null=True)
    delivered_on = models.DateField(null=True,default=None)
    karigar_charges = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    customer_charges = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    tax_charges = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    receipt = models.ForeignKey('billing.ErpIssueReceipt', on_delete=models.SET_NULL, related_name="delivery_receipt", null=True)
    is_reserved_item = models.BooleanField(default=False)
    voice_note = models.FileField(upload_to=upload_order_voice_note, null=True, default=None)
    nick_name = models.CharField(max_length=255, null=True, default=None)
    customized_ref_no = models.CharField(max_length=255, null=True, blank=True,default=None)
    customized_product_name = models.CharField(max_length=255, null=True, default=None, blank=True)
    customized_design_name = models.CharField(max_length=255, null=True, default=None, blank=True)
    dimension = models.CharField(max_length=255, null=True, default=None, blank=True)
    customized_stone_name = models.CharField(max_length=255, null=True, blank=True,default=None)
    customized_stone_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=True, default=0,validators=[MinValueValidator(0.0)])
    purchase_touch      = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_va         = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    repair_approx_amt   = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    order_accepted_by   = models.ForeignKey(accountUser,related_name='order_accepted_by_user', null=True, default=None, on_delete=models.PROTECT)
    order_accepted_on   = models.DateTimeField(null=True,default=None)
    ref_emp_id          = models.ForeignKey('employees.Employee', on_delete=models.CASCADE,default=None,null=True)
    flat_mc_value       = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    total_mc_value      = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    
    def __str__(self) -> str:
        return 'ERP Order Details - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_order_details'
        

class ERPOrderImages(models.Model):
    det_order_img_id = models.BigAutoField(primary_key=True)
    order_detail = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, default=None)
    image = models.ImageField(upload_to=upload_order_image)
    
    def __str__(self) -> str:
        return 'ERP Order Image - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_order_images'

class ErpOrderInternalProcessLog(models.Model):
    id = models.AutoField(primary_key=True)
    order_detail = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE)
    internal_order_process = models.ForeignKey('retailmasters.ERPInternalOrderStatus', on_delete=models.PROTECT, related_name='internal_order_status_log',default=None, null=True,blank=True)
    created_on = models.DateTimeField(auto_now=datetime.now(tz=timezone.utc),null=True)
    created_by = models.ForeignKey(accountUser, related_name='order_internal_process_created_by_user', on_delete=models.PROTECT)
    
    
    def __str__(self) -> str:
        return 'ERP Order Image - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_order_internal_process_log'


# Audio File
class ERPOrderAudios(models.Model):
    det_order_audio_id = models.BigAutoField(primary_key=True)
    order_detail = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, default=None)
    audio = models.FileField(upload_to=upload_order_audio)

    def __str__(self):
        return f'ERP Order Audio - {self.pk}'

    class Meta:
        db_table = 'erp_order_audios'


# Video File
class ERPOrderVideos(models.Model):
    det_order_vid_id = models.BigAutoField(primary_key=True)
    order_detail = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, default=None)
    video = models.FileField(upload_to=upload_order_video)

    def __str__(self):
        return f'ERP Order Video - {self.pk}'

    class Meta:
        db_table = 'erp_order_videos'
        

class ERPOrderStoneDetails(models.Model):
    
    CALC_TYPE_CHOICES = [
        (1, "By Pieces"),
        (2, "By Weight")
        ]
    
    order_stn_id = models.AutoField(primary_key=True)
    order_detail = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE)
    show_in_lwt = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    stone = models.ForeignKey('retailcataloguemasters.Stone', on_delete=models.PROTECT, related_name="order_detail_stone_id", null=True, default=None)
    uom_id = models.ForeignKey('retailmasters.Uom',on_delete=models.PROTECT, related_name="order_detail_stone_uom", null=True, default=None)
    pieces = models.PositiveIntegerField(null=True, default=None)
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    stone_calc_type = models.IntegerField(choices=CALC_TYPE_CHOICES, default=1)
    stone_rate = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    stone_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    
    def __str__(self) -> str:
        return 'ERP Order Stone Detail - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_order_stone_details'

class ERPOrderCharges(models.Model):
    order_charges_id = models.AutoField(primary_key=True)
    order_detail = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE)
    charges = models.ForeignKey('retailmasters.OtherCharges', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    
    def __str__(self) -> str:
        return 'ERP Order Charges Detail - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_order_charges'
        
        
class ERPOrderAttribute(models.Model):
    order_attribut_id = models.AutoField(primary_key=True)
    order_detail = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE)
    attribute = models.ForeignKey('retailmasters.AttributeEntry', on_delete=models.PROTECT)
    value = models.CharField(max_length=255, null=True, default=None)
    
    def __str__(self) -> str:
        return 'ERP Order Attribute Detail - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_order_attributes'
        
class ErpOrderOtherMetal(models.Model):
    
    ORDER_OTHER_METAL_MC_TYPE_CHOICES = [
        (1, 'Per Gram'),
        (2, 'Per Pcs')
        ]
    
    order_other_metal_id  = models.AutoField(primary_key=True)
    order_detail        = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE)
    category            = models.ForeignKey('retailcataloguemasters.Category',on_delete=models.PROTECT,related_name="erp_order_other_metal_cat_id")
    purity              = models.ForeignKey('retailcataloguemasters.Purity',on_delete=models.PROTECT,related_name="erp_order_other_metal_purity_id")
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_type             = models.IntegerField(choices=ORDER_OTHER_METAL_MC_TYPE_CHOICES,default=1)
    mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    other_metal_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    rate_per_gram       = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])


    def __str__(self) -> str:
        return 'ERP Order Other metal - ' + str(self.pk)

    class Meta:
        db_table = 'erp_order_other_metal'



class ErpOrderRepairExtraMetal(models.Model):
    
    repair_extra_weight_metal_id  = models.AutoField(primary_key=True)
    order_detail        = models.ForeignKey(ERPOrderDetails, on_delete=models.PROTECT)
    id_metal            = models.ForeignKey('retailcataloguemasters.Metal',on_delete=models.PROTECT,related_name="erp_order_extra_weight_metal_id")
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    class Meta:
        db_table = 'erp_order_repair_extra_metal'

        
class ErpJobOrder(models.Model):
    
    JOB_ASSIGNED_TO_CHOICES = [
        (1, 'Karigar'),
        (2, 'Employee')
        ]
    
    id_job_order = models.AutoField(primary_key=True)
    fin_year = models.ForeignKey('retailmasters.FinancialYear',on_delete=models.PROTECT)
    assigned_to = models.IntegerField(choices=JOB_ASSIGNED_TO_CHOICES)
    supplier = models.ForeignKey('retailmasters.Supplier', on_delete=models.PROTECT, null=True, default=None)
    employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, default=None)
    ref_no = models.CharField(max_length=255)
    assigned_date = models.DateField()
    assigned_by = models.ForeignKey(accountUser, related_name='order_assigned_by_user', on_delete=models.PROTECT)
    
    def __str__(self) -> str:
        return 'Job Order - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_job_order'
        
    LOGGING_IGNORE_FIELDS = ('assigned_by')
    
class ErpJobOrderDetails(models.Model):
    id_job_order_detail = models.AutoField(primary_key=True)
    job_order = models.ForeignKey(ErpJobOrder, on_delete=models.PROTECT)
    order_detail = models.ForeignKey(ERPOrderDetails, on_delete=models.PROTECT)
    due_date = models.DateField(null=True,default=None)
    delivery_date = models.DateField(null=True,default=None)
    status = models.ForeignKey('retailmasters.ERPOrderStatus', on_delete=models.PROTECT, related_name='job_order_status')
    remarks = models.TextField(null=True, default=None)
    cancel_reason = models.TextField(null=True, default=None)
    cancelled_by = models.ForeignKey(accountUser,related_name='job_order_cancelled_by_user', null=True, default=None, on_delete=models.SET_NULL)
    cancelled_date = models.DateField(null=True, default=None)
    updated_by = models.ForeignKey(accountUser,related_name='job_order_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)
    
    def __str__(self) -> str:
        return 'Job Order Detail - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_job_order_details'
        

class CustomerCart(models.Model):
    
    CART_TYPE_CHOICES = [
        (1, "Customer Cart"),
        (2, "Purchase Cart")
        ]
    
    MC_TYPE_CHOICES = [
        (1, "Per Gram"),
        (2, "Per Piece")
        ]
    
    TAX_TYPE_CHOICES = [
        (1, 'Inclusive'),
        (2, 'Exclusive'),
    ]
    
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey('customers.Customers', on_delete=models.PROTECT, null=True)
    cart_type = models.IntegerField(choices=CART_TYPE_CHOICES, default=1)
    weight_range = models.ForeignKey('retailmasters.WeightRange',related_name='customer_cart_weight_range', on_delete=models.PROTECT, null=True,default=None)
    purity = models.ForeignKey('retailcataloguemasters.Purity', on_delete=models.PROTECT, related_name="customer_cart_purity",default=None,null=True,blank=False,)
    uom = models.ForeignKey('retailmasters.Uom',on_delete=models.PROTECT, related_name="customer_cart_uom", null=True, default=None)
    erp_tag = models.ForeignKey('inventory.ErpTagging', on_delete=models.SET_NULL, null=True, default=None, related_name="customer_cart_tag")
    product = models.ForeignKey('retailcataloguemasters.Product', on_delete=models.PROTECT, related_name="customer_cart_product")
    design = models.ForeignKey('retailcataloguemasters.Design', on_delete=models.PROTECT, related_name="customer_cart_design",default=None,null=True,blank=False,)
    sub_design = models.ForeignKey('retailcataloguemasters.SubDesign', on_delete=models.PROTECT, related_name="customer_cart_sub_design",default=None,null=True,blank=False)
    size = models.ForeignKey('retailmasters.Size',on_delete=models.PROTECT,related_name="customer_cart_size", null=True,blank=False, default=None)
    pieces = models.PositiveIntegerField(null=False, blank=False)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=0,validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=0,validators=[MinValueValidator(0.0)])
    diamond_wt = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=0,validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    customer_due_date = models.DateField(null=True, default=None)
    remarks = models.TextField(null=True,blank=True, default=None)
    added_on = models.DateTimeField(auto_now_add=datetime.now())
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    taxable_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, validators=[MinValueValidator(0.0)],default=0.0)
    tax_type = models.IntegerField(choices=TAX_TYPE_CHOICES, verbose_name='Tax type',null=True, default=None) 
    tax_percent = models.PositiveIntegerField(null=True, default=None)
    tax_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    cgst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    sgst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    igst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    
    def __str__(self) -> str:
        return 'Customer Cart - ' + str(self.pk)
    
    class Meta:
        db_table = 'customer_cart'
        
    LOGGING_IGNORE_FIELDS = ('added_on')
    

class CustomerWishlist(models.Model):
    
    MC_TYPE_CHOICES = [
        (1, "Per Gram"),
        (2, "Per Piece")
        ]
    
    TAX_TYPE_CHOICES = [
        (1, 'Inclusive'),
        (2, 'Exclusive'),
    ]
    
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey('customers.Customers', on_delete=models.PROTECT)
    purity = models.ForeignKey('retailcataloguemasters.Purity', on_delete=models.PROTECT, related_name="customer_wishlist_purity",default=None,null=True,blank=False,)
    uom = models.ForeignKey('retailmasters.Uom',on_delete=models.PROTECT, related_name="customer_wishlist_uom",default=None,null=True,blank=True)
    erp_tag = models.ForeignKey('inventory.ErpTagging', on_delete=models.SET_NULL, null=True, default=None, related_name="customer_wishlist_tag")
    product = models.ForeignKey('retailcataloguemasters.Product', on_delete=models.PROTECT, related_name="customer_wishlist_product")
    design = models.ForeignKey('retailcataloguemasters.Design', on_delete=models.PROTECT, related_name="customer_wishlist_design",default=None,null=True,blank=False,)
    sub_design = models.ForeignKey('retailcataloguemasters.SubDesign', on_delete=models.PROTECT, related_name="customer_wishlist_sub_design",default=None,null=True,blank=False)
    size = models.ForeignKey('retailmasters.Size',on_delete=models.PROTECT,related_name="customer_wishlist_size", null=True,blank=False, default=None)
    pieces = models.PositiveIntegerField(null=False, blank=False)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False, default=0,validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=0,validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=0,validators=[MinValueValidator(0.0)])
    diamond_wt = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=0,validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=0, validators=[MinValueValidator(0.0)])
    customer_due_date = models.DateField(null=True, default=None)
    remarks = models.TextField(null=True,blank=True, default=None)
    added_on = models.DateTimeField(auto_now_add=datetime.now())
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    taxable_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(0.0)],default=0.0)
    tax_type = models.IntegerField(choices=TAX_TYPE_CHOICES, verbose_name='Tax type',null=True, default=None) 
    tax_percent = models.PositiveIntegerField(null=True, default=None)
    tax_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    cgst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    sgst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    igst_amnt = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    
    def __str__(self) -> str:
        return 'Customer Wishlist - ' + str(self.pk)
    
    class Meta:
        db_table = 'customer_wishlist'
        
    LOGGING_IGNORE_FIELDS = ('added_on')