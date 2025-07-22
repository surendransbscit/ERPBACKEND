import os
import uuid
from datetime import datetime, timedelta
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from retailcataloguemasters.models import (
    Category, Product, Metal, Purity, Design, SubDesign, Stone, ProductCalculationType,Section,QualityCode
)
from retailmasters.models import (
    Supplier, Branch, Uom, Taxgroupitems, ErpStockStatusMaster, FinancialYear,OtherCharges,AttributeEntry,Size
)
from retailpurchase.models import ErpPurchaseEntryDetails,ErpPurchaseStoneDetails,ErpPurchaseOtherMetal,ErpAccountStockProcess
from customerorder.models import ERPOrderDetails
from common.models import BaseModel

from  utilities.constants import (  # Adjust the import path as needed
    LOT_TYPE_CHOICES,
    PURE_WT_CALC_TYPE_CHOICES,
    PURCHASE_MC_TYPE_CHOICES,
    PURCHASE_RATE_TYPE_CHOICES,
    PURCHASE_STN_CALC_TYPE_CHOICES,
    TAG_MC_TYPE_CHOICES,
    TAG_STN_CALC_TYPE_CHOICES,
    TAG_OTHER_METAL_MC_TYPE_CHOICES,
    TAG_OTHER_METAL_CALC_TYPE_CHOICES,
    TRANSACTION,
    SHOW_IN_LWT_CHOICES,
    PARTIAL_SALE_CHOICES,
    LOT_STATUS_CHOICES
)
accounts_user = 'accounts.User'

def upload_tag_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    unique_id = uuid.uuid4()
    return 'tag_images/tag_{tagid}/{pkid}{title}{ext}'.format(tagid=instance.erp_tag.tag_id, pkid=unique_id, title=datetime.now().strftime('%Y%m%d%H%M%S'), ext=file_extension)

# Models
class ErpLotInward(BaseModel):
    lot_no = models.AutoField(primary_key=True)
    lot_code = models.CharField(max_length=255,null=True,blank=False,default=None) 
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="lot_supplier")
    lot_date = models.DateField()
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    account_stock_process = models.ForeignKey(ErpAccountStockProcess,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="lot_branch", default=None)
    lot_type = models.IntegerField(choices=LOT_TYPE_CHOICES, default=1)
    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_closed_by', null=True, blank=True)
    closed_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_created_by')
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_updated_by', null=True, blank=True)
    
    class Meta:
        db_table = 'erp_lot_inward'

    def __str__(self):
        return f"Lot {self.lot_no}"


class ErpLotInwardDetails(models.Model):
    id_lot_inward_detail = models.AutoField(primary_key=True)
    item_code =  models.CharField(max_length=255,null=True,blank=False,default=None) 
    lot_no = models.ForeignKey(ErpLotInward, on_delete=models.CASCADE, related_name='lot_details')
    id_purity = models.ForeignKey(Purity, on_delete=models.CASCADE, related_name="lot_purity", null=True, default=None)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="lot_product", null=True, default=None)
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="lot_design", null=True, default=None)
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE, related_name="lot_sub_design", null=True, default=None)
    id_section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="lot_section", null=True, default=None)
    size   = models.ForeignKey(Size,on_delete=models.CASCADE,related_name="lot_size",null=True, default=None)
    pieces = models.PositiveIntegerField()
    uom_id = models.ForeignKey(Uom,on_delete=models.CASCADE, related_name="item_uom", null=True, default=None)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    tagged_pcs = models.PositiveIntegerField(default=0)
    tagged_gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    tagged_less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    tagged_net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    tagged_dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    tagged_stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    tagged_other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    sell_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)])
    purchase_touch = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_va = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_mc = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_mc_type = models.IntegerField(choices=PURCHASE_MC_TYPE_CHOICES, default=1)
    pure_wt_cal_type = models.IntegerField(choices=PURE_WT_CALC_TYPE_CHOICES, default=1)
    purchase_rate_type = models.IntegerField(choices=PURCHASE_RATE_TYPE_CHOICES, default=1)
    purchase_calculation = models.ForeignKey(ProductCalculationType, on_delete=models.CASCADE, null=True, default=None, related_name="lot_product_calculation_type")
    purchase_tax_group = models.ForeignKey(Taxgroupitems, on_delete=models.CASCADE, null=True, related_name='lot_tax_group', default=None)
    purchase_taxable_amt = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    pure_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    purchase_entry_detail = models.ForeignKey(ErpPurchaseEntryDetails, on_delete=models.CASCADE, related_name="purchase_detail", null=True, default=None)
    status = models.IntegerField(choices=LOT_STATUS_CHOICES, default=0)  # 0: Pending, 1: Completed
    closed_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_closed_product_by', null=True, blank=True)
    closed_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    class Meta:
        db_table = 'erp_lot_inward_details'
        indexes = [
            models.Index(fields=['id_product', 'id_design', 'id_sub_design']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['lot_no', 'id_product', 'id_design', 'id_sub_design'], name='unique_lot_details')
        ]

    def __str__(self):
        return f"Lot Detail {self.id_lot_inward_detail}"


class ErpLotInwardStoneDetails(models.Model):
    id_lot_inw_stn_detail = models.AutoField(primary_key=True)
    id_lot_inward_detail = models.ForeignKey(ErpLotInwardDetails, on_delete=models.CASCADE, related_name="lot_detail_id", null=True, default=None)
    show_in_lwt = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone = models.ForeignKey(Stone, on_delete=models.CASCADE, related_name="lot_stone_id", null=True, default=None)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="lot_id_quality_code", null=True, default=None)
    uom_id = models.ForeignKey(Uom, on_delete=models.CASCADE, related_name="lot_uom_id", null=True, default=None)
    stone_pcs = models.PositiveIntegerField(validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    pur_stn_cal_type = models.IntegerField(choices=PURCHASE_STN_CALC_TYPE_CHOICES, default=1)
    pur_st_rate     = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    pur_stn_cost     = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    purchase_stn_detail = models.ForeignKey(ErpPurchaseStoneDetails, on_delete=models.CASCADE, related_name="purchase_stn_detail", null=True, default=None)

    class Meta:
        db_table = 'erp_lot_inward_stone_details'
        indexes = [
            models.Index(fields=['id_stone', 'uom_id', 'id_lot_inward_detail']),
        ]


class ErpLotInwardOtherMetal(models.Model):
    
    id_lot_inw_other_metal  = models.AutoField(primary_key=True)
    id_lot_inward_detail = models.ForeignKey(ErpLotInwardDetails, on_delete=models.CASCADE, related_name="lot_other_detail", null=True, default=None)
    id_category         = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="lot_other_metal_cat_id", null=True, default=None)
    id_purity           = models.ForeignKey(Purity,on_delete=models.CASCADE,related_name="lot_other_metal_purity_id", null=True, default=None)
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_type             = models.IntegerField(choices=TAG_OTHER_METAL_MC_TYPE_CHOICES,default=1)
    calc_type             = models.IntegerField(choices=TAG_OTHER_METAL_CALC_TYPE_CHOICES,default=1)
    mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    rate_per_gram       = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    other_metal_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    purchase_other_metal = models.ForeignKey(ErpPurchaseOtherMetal, on_delete=models.CASCADE, related_name="pur_lot_other_detail", null=True, default=None)


    class Meta:
        db_table = 'erp_lot_inward_other_metal'


class ErpLotInwardNonTagLogDetails(models.Model):
    id_non_tag_log = models.AutoField(primary_key=True)
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="non_tag_from_branch", null=True, default=None)
    to_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="non_tag_to_branch", null=True, default=None)
    date = models.DateField()
    id_stock_status = models.ForeignKey(ErpStockStatusMaster, on_delete=models.CASCADE, related_name="non_tag_stock_status", null=True, default=None)
    lot_no = models.ForeignKey(ErpLotInward, on_delete=models.CASCADE, related_name='non_tag_lot_details',null=True, default=None)
    id_lot_inward_detail = models.ForeignKey(ErpLotInwardDetails, on_delete=models.CASCADE, related_name="non_tag_lot_detail_id", null=True, default=None)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="non_tag_product", null=True, default=None)
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="non_tag_design", null=True, default=None)
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE, related_name="non_tag_sub_design", null=True, default=None)
    id_section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="non_tag_section", null=True, default=None)
    pieces = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    transaction_type = models.IntegerField(choices=TRANSACTION,null=True,default=None)
    ref_id = models.IntegerField(null=True, blank=False,default=None)
    created_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='non_tag_created_by')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='non_tag_updated_by', null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'erp_lot_inward_non_tag_log_details'
        indexes = [
            models.Index(fields=['date','id_stock_status','id_product','id_design','id_sub_design','id_section']),
        ]

class ErpLotInwardNonTagLogStoneDetails(models.Model):
    id_log_stn_detail = models.AutoField(primary_key=True)
    id_non_tag_log = models.ForeignKey(ErpLotInwardNonTagLogDetails, on_delete=models.CASCADE, related_name="log_detail_id", null=True, default=None)
    show_in_lwt = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone = models.ForeignKey(Stone, on_delete=models.CASCADE, related_name="log_stone_id", null=True, default=None)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="non_tag_id_quality_code", null=True, default=None)
    uom_id = models.ForeignKey(Uom, on_delete=models.CASCADE, related_name="log_uom_id", null=True, default=None)
    stone_pcs = models.PositiveIntegerField(validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stn_cal_type = models.IntegerField(choices=PURCHASE_STN_CALC_TYPE_CHOICES, default=1)
    stn_rate     = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stn_cost     = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])


    class Meta:
        db_table = 'erp_lot_inward_non_tag_log_stone_details'
        indexes = [
            models.Index(fields=['id_stone', 'uom_id', 'id_non_tag_log']),
        ]

class ErpTagging(models.Model):
   
    tag_id                  = models.AutoField(primary_key=True)
    fin_year                = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    tag_code                = models.CharField(max_length=255,unique=True, error_messages={"unique": "Tag Code already exists"})
    tag_date                = models.DateField(null=False,blank=False)
    id_branch              = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="tagged_id_branch", null=True, default=None)
    tag_branch              = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="tagged_branch_id", null=True, default=None)
    tag_current_branch      = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="tag_current_branch_id", null=True, default=None)
    tag_lot_inward_details  = models.ForeignKey(ErpLotInwardDetails,on_delete=models.CASCADE,related_name="lot_inward_detail_id", null=True, default=None)
    tag_product_id          = models.ForeignKey(Product, on_delete=models.CASCADE,related_name="tag_product_id",null=True, default=None)
    tag_design_id           = models.ForeignKey(Design, on_delete=models.CASCADE,related_name="tag_design_id",null=True, default=None)
    tag_sub_design_id       = models.ForeignKey(SubDesign, on_delete=models.CASCADE,related_name="tag_sub_design_id",null=True, default=None)
    tag_section_id          = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="tag_section", null=True, default=None)
    tag_order_det           = models.ForeignKey(ERPOrderDetails, on_delete=models.CASCADE, related_name="tag_order_detail_id", null=True, default=None)
    tag_purity_id           = models.ForeignKey(Purity, on_delete=models.CASCADE,related_name="tag_purity_id",null=True, default=None)
    tag_pcs                 = models.PositiveIntegerField(null=False, blank=False)
    tag_uom_id              = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="tag_uom_id",null=False, blank=False)
    tag_gwt                 = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0,validators=[MinValueValidator(0.0)])
    tag_lwt                 = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0,validators=[MinValueValidator(0.0)])
    tag_nwt                 = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0,validators=[MinValueValidator(0.0)])
    tag_stn_wt              = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0,validators=[MinValueValidator(0.0)])
    tag_dia_wt              = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0,validators=[MinValueValidator(0.0)])
    tag_other_metal_wt      = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False,default=0,validators=[MinValueValidator(0.0)])
    tag_calculation_type    = models.ForeignKey(ProductCalculationType,on_delete=models.CASCADE,related_name="tag_calculation_type_master_id",null=True, default=None)
    tag_wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    tag_wastage_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    tag_mc_type             = models.IntegerField(choices=TAG_MC_TYPE_CHOICES,default=1)
    tag_mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    tag_buy_rate            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    tag_sell_rate           = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    tag_mrp_margin_amount   = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    tag_tax_grp_id          = models.ForeignKey(Taxgroupitems,on_delete=models.CASCADE,related_name="tag_tax_group_items",null=True, default=None)
    tag_tax_amount          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tag_item_cost           = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    tag_purchase_touch      = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    tag_purchase_va         = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    tag_purchase_mc         = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    tag_purchase_mc_type    = models.IntegerField(choices=TAG_MC_TYPE_CHOICES,default=1)
    tag_purchase_calc_type   = models.IntegerField(choices=PURE_WT_CALC_TYPE_CHOICES, default=1)
    tag_pure_wt             = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    tag_purchase_rate       = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    tag_purchase_rate_calc_type = models.IntegerField(choices=PURCHASE_RATE_TYPE_CHOICES, default=1)
    tag_huid                = models.CharField(max_length=8,null=True,default=None)
    tag_huid2               = models.CharField(max_length=8,null=True,default=None)
    tag_purchase_cost       = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    size                     = models.ForeignKey(Size,on_delete=models.CASCADE,related_name="tag_size",null=True, default=None)
    is_partial_sale         = models.IntegerField(choices=PARTIAL_SALE_CHOICES, default=0)
    container = models.ForeignKey('retailmasters.Container', on_delete=models.CASCADE, related_name="tag_container_id", null=True, default=None)
    is_special_discount_applied =  models.BooleanField(default=False) #for EDA
    flat_mc_value           = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    total_mc_value          = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    old_tag_code            = models.CharField(max_length=255,null=True,default=None)  # Adjust max_length as needed
    old_tag_id              = models.CharField(max_length=255,null=True, default=None)
    tag_status              = models.ForeignKey(ErpStockStatusMaster,on_delete=models.CASCADE,related_name="tag_stock_status_master",null=True, default=None)
    is_imported             = models.BooleanField(default=False)
    is_issued_to_counter    = models.BooleanField(default=0)
    id_supplier             = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="tag_supplier",default=None, null=True)
    created_by              = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_created_by', null=True, default=None)
    created_on              = models.DateTimeField(auto_now_add=True)
    updated_by              = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_updated_by', null=True, blank=True)
    updated_on              = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'erp_tagging'
    
    indexes = [
            models.Index(fields=['tag_status','id_product', 'id_design','id_sub_design','uom_id','tag_calculation_type','tag_tax_grp_id','created_by','updated_by']),
    ]

class ErpTaggingImages(models.Model):
    id = models.AutoField(primary_key=True)
    erp_tag = models.ForeignKey(ErpTagging, on_delete=models.CASCADE, related_name="erptaggingimages")
    tag_image = models.ImageField(upload_to=upload_tag_image)
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.id} - Image for Tag {self.erp_tag}"

    class Meta:
        db_table = 'erp_tagging_images'


class ErpTaggingStone(models.Model):
    
    id_tag_stn_detail = models.AutoField(primary_key=True)
    tag_id            = models.ForeignKey(ErpTagging,on_delete=models.CASCADE,related_name="erp_tag_id",null=True, default=None)
    show_in_lwt       = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone          = models.ForeignKey(Stone, on_delete=models.CASCADE,related_name="tag_stn_stone_id",null=True, default=None)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="tag_id_quality_code", null=True, default=None)
    uom_id            = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="tag_stn_uom_id",null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    stone_rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_calc_type   = models.IntegerField(choices=TAG_STN_CALC_TYPE_CHOICES,default=1)
    class Meta:
        db_table = 'erp_tag_stone'
    
    indexes = [
            models.Index(fields=['id_stone','tag_id','uom_id']),
    ]

class ErpTagOtherMetal(models.Model):
    
    id_tag_other_metal  = models.AutoField(primary_key=True)
    tag_id              = models.ForeignKey(ErpTagging,on_delete=models.CASCADE, related_name="erp_other_metal_tag_id", null=True, default=None)
    id_category         = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="erp_other_metal_cat_id", null=True, default=None)
    id_purity           = models.ForeignKey(Purity,on_delete=models.CASCADE,related_name="erp_other_metal_purity_id", null=True, default=None)
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_type             = models.IntegerField(choices=TAG_OTHER_METAL_MC_TYPE_CHOICES,default=1)
    calc_type             = models.IntegerField(choices=TAG_OTHER_METAL_CALC_TYPE_CHOICES,default=1)
    mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    rate_per_gram       = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    other_metal_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_tag_other_metal'



class ErpTaggingLogDetails(models.Model):
    id_tag_log = models.AutoField(primary_key=True)
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="tag_from_branch", null=True, default=None)
    to_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="tag_to_branch", null=True, default=None)
    date = models.DateField()
    id_stock_status = models.ForeignKey(ErpStockStatusMaster, on_delete=models.CASCADE, related_name="tag_stock_status", null=True, default=None)
    tag_id = models.ForeignKey(ErpTagging, on_delete=models.CASCADE, related_name="log_tag_id", null=True, default=None)
    transaction_type = models.IntegerField(choices=TRANSACTION,null=True,default=None)
    ref_id = models.IntegerField(null=True, blank=False,default=None)
    created_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_log_created_by')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_log_updated_by', null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'erp_tag_log_details'
        indexes = [
            models.Index(fields=['from_branch', 'to_branch', 'date','id_stock_status','tag_id']),
        ]

class ErpTaggingContainerLogDetails(models.Model):
    id = models.AutoField(primary_key=True)
    tag = models.ForeignKey(ErpTagging,on_delete=models.CASCADE, related_name="tag_container_log_tag_id")
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="tag_container_log_from_branch", null=True, default=None)
    to_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="tag_container_log_to_branch", null=True, default=None)
    from_container = models.ForeignKey('retailmasters.Container', on_delete=models.CASCADE, related_name="tag_container_log_from_container", null=True, default=None)
    to_container = models.ForeignKey('retailmasters.Container', on_delete=models.CASCADE, related_name="tag_container_log_to_container", null=True, default=None)
    transaction_type = models.IntegerField(choices=TRANSACTION,null=True)
    status = models.ForeignKey(ErpStockStatusMaster, on_delete=models.SET_NULL, related_name="tag_container_log_status", null=True, default=None)
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_container_log_updated_by', null=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'erp_tag_container_log_details'
        

class ErpTagCharges(models.Model):

    tag_charges_id = models.AutoField(primary_key=True)
    tag_id         = models.ForeignKey(ErpTagging,on_delete=models.CASCADE,null=False,blank=False)
    id_charges     = models.ForeignKey(OtherCharges,on_delete=models.CASCADE,null=False,blank=False,default=None)
    charges_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_tag_charges_details'

class ErpTagAttribute(models.Model):

    tag_attribute_id = models.AutoField(primary_key=True)
    tag_id           = models.ForeignKey(ErpTagging,on_delete=models.CASCADE,null=False,blank=False)
    id_attribute     = models.ForeignKey(AttributeEntry,on_delete=models.CASCADE,null=False,blank=False)
    value            = models.CharField(max_length=255,default=None,blank=True)

    class Meta:
        db_table = 'erp_attribute_details'

class ErpTagScan(models.Model):

    id_tag_scan      = models.AutoField(primary_key=True)
    id_branch        = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="scan_branch")
    id_section       = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="scan_section",null=True, default=None)
    id_product       = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="scan_product",null=True, default=None)
    start_date       = models.DateField(null=False,blank=False)
    closed_by        = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_scan_closed_by', null=True, default=None)
    closed_date      = models.DateField(null=True, blank=True)
    status           = models.IntegerField(choices=[(0, 'Open'),(1, 'Closed')],default=0)
    created_by       = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_scan_created_by', null=True, default=None)
    created_on       = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_by       = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_scan_updated_by', null=True, blank=True)
    updated_on       = models.DateTimeField(auto_now=True, null=True, blank=True)


    class Meta:
        db_table = 'erp_tag_scan'


class ErpTagScanDetails(models.Model):

    id_tag_scan_detail      = models.AutoField(primary_key=True)
    id_tag_scan             = models.ForeignKey(ErpTagScan, on_delete=models.CASCADE,related_name="scan_branch")
    tag_id                  = models.ForeignKey(ErpTagging,on_delete=models.CASCADE,null=False,blank=False)
    is_wt_scanned           = models.BooleanField(default=False)            
    scale_wt                = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    created_by              = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_scan_details_created_by', null=True, default=None)
    created_on              = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'erp_tag_scan_details'


class ErpLotIssueReceipt(BaseModel):
    id = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None)
    status = models.IntegerField(choices=[(1, 'Issue'),(2,'Receipt')],null=True,default=1) 
    entry_date = models.DateField()
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    issue_employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, default=None,related_name='lot_issue_employee',)
    receipt_employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, default=None,related_name='lot_receipt_employee',)
    receipt_entry_date = models.DateField(null=True,default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="lot_issue_branch", default=None)
    issue_remarks = models.TextField(null=True, default=None)
    receipt_remarks = models.TextField(null=True, default=None)
    created_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_issue_created_by')
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_issue_updated_by', null=True, blank=True)
    
    class Meta:
        db_table = 'erp_lot_issue_receipt'

    def __str__(self):
        return f"Lot {self.id}"


class ErpLotIssueReceiptDetails(models.Model):
    id_detail = models.AutoField(primary_key=True)
    detail = models.ForeignKey(ErpLotIssueReceipt, on_delete=models.CASCADE, related_name='issue_details')
    id_lot_inward_detail = models.ForeignKey(ErpLotInwardDetails, on_delete=models.CASCADE, related_name='lot_details')
    pieces = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    receipt_pieces = models.PositiveIntegerField(default=0)
    receipt_gross_wt = models.DecimalField(default=0,max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    receipt_less_wt = models.DecimalField(default=0,max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    receipt_net_wt = models.DecimalField(default=0,max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    receipt_dia_wt = models.DecimalField(default=0,max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    receipt_stone_wt = models.DecimalField(default=0,max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_lot_issue_receipt_details'
        
    def __str__(self):
        return f"Lot Detail {self.id_detail}"
    


class ErpTagIssueReceipt(BaseModel):
    id = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    status = models.IntegerField(choices=[(1, 'Issue'),(2,'Receipt')],null=True,default=1)
    entry_date = models.DateField()
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="tag_issue_branch", default=None)
    issue_employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, default=None,related_name='tag_issue_employee',)
    receipt_employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, default=None,related_name='tag_receipt_employee',)
    receipt_entry_date = models.DateField(null=True,default=None)
    issue_remarks = models.TextField(null=True, default=None)
    receipt_remarks = models.TextField(null=True, default=None)
    created_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_issue_created_by')
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_issue_updated_by', null=True, blank=True)
    
    class Meta:
        db_table = 'erp_tag_issue_receipt'

    def __str__(self):
        return f"Tag {self.id}"


class ErpTagIssueReceiptDetails(models.Model):
    id_detail = models.AutoField(primary_key=True)
    detail = models.ForeignKey(ErpTagIssueReceipt, on_delete=models.CASCADE, related_name='tag_issue_details')
    tag = models.ForeignKey(ErpTagging, on_delete=models.CASCADE, related_name='tag_details')
    status = models.IntegerField(choices=[(1, 'Issued'),(2,'Receipted')],null=True,default=None)

    class Meta:
        db_table = 'erp_tag_issue_receipt_details'
        
    def __str__(self):
        return f"Tag Detail {self.id_detail}"
    
class ErpLotNonTagInward(BaseModel):
    id = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None)
    status = models.IntegerField(choices=[(1, 'Issue'),(2,'Receipt')],null=True,default=1) 
    entry_date = models.DateField()
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    issue_employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, default=None,related_name='lot_inward_issue_employee',)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="lot_non_tag_inward_branch", default=None)
    issue_remarks = models.TextField(null=True, default=None)
    created_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_non_tag_inward_created_by')
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_non_tag_inward_updated_by', null=True, blank=True)
    
    class Meta:
        db_table = 'erp_lot_non_tag_inward'

    def __str__(self):
        return f"Lot {self.id}"


class ErpLotNonTagInwardDetails(models.Model):
    id_detail = models.AutoField(primary_key=True)
    detail = models.ForeignKey(ErpLotNonTagInward, on_delete=models.CASCADE, related_name='non_tag_issue_details')
    id_lot_inward_detail = models.ForeignKey(ErpLotInwardDetails, on_delete=models.CASCADE, related_name='non_tag_lot_details')
    pieces = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    class Meta:
        db_table = 'erp_lot_non_tag_inward_details'
        
    def __str__(self):
        return f"Lot Detail {self.id_detail}"
    
class ErpTagSet(models.Model):
    id = models.BigAutoField(primary_key=True)
    tag = models.OneToOneField(ErpTagging, on_delete=models.CASCADE, related_name='tag_set_tag_id')
    set_no = models.CharField(max_length=255, null=True, default=None)
    set_name = models.CharField(max_length=255, null=True, default=None)
    date = models.DateField()
    created_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_set_created_by')
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='tag_set_updated_by', null=True, default=None)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_on = models.DateTimeField(null=True, default=None)
    
    def __str__(self):
        return f"Tag Set {self.id}"
    
    class Meta:
        db_table = 'erp_tag_set'
        
class ErpTagSetItems(models.Model):
    id = models.BigAutoField(primary_key=True)
    tag_set = models.ForeignKey(ErpTagSet, on_delete=models.CASCADE, related_name='tag_set_item_set_id')
    tag = models.OneToOneField(ErpTagging, on_delete=models.CASCADE, related_name='tag_set_item_tag_id',
                               error_messages={
        'unique': "This tag is already associated in a set.",
        'null': "Tag cannot be null.",
        'invalid': "Invalid tag selected.",
    })
    
    def __str__(self):
        return f"Tag Set Item{self.id}"
    
    class Meta:
        db_table = 'erp_tag_set_items'
    


class ErpLotMerge(BaseModel):
    id = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None)
    entry_date = models.DateField()
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="lot_merge_branch", default=None)
    issue_remarks = models.TextField(null=True, default=None)
    created_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_merge_created_by')
    updated_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE, related_name='lot_merge_updated_by', null=True, blank=True)
    id_purity = models.ForeignKey(Purity, on_delete=models.CASCADE, related_name="lot_merge_purity", null=True, default=None)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="lot_merge_product", null=True, default=None)
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="lot_merge_design", null=True, default=None)
    class Meta:
        db_table = 'erp_lot_merge'

    def __str__(self):
        return f"Lot {self.id}"


class ErpLotMergeDetails(models.Model):
    id_detail = models.AutoField(primary_key=True)
    lot_merge = models.ForeignKey(ErpLotMerge, on_delete=models.CASCADE, related_name='lot_merge_id')
    id_lot_inward_detail = models.ForeignKey(ErpLotInwardDetails, on_delete=models.CASCADE, related_name='lot_merge_item_details')
    pieces = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    
    class Meta:
        db_table = 'erp_lot_merge_item_details'
        
    def __str__(self):
        return f"Lot Detail {self.id_detail}"
    
