from django.db import models
from datetime import datetime
from retailcataloguemasters.models import Category,Product, Metal, Purity,Design,SubDesign,Stone,ProductCalculationType,QualityCode,Section
from retailmasters.models import Supplier, Branch , Uom,Taxgroupitems , ErpStockStatusMaster , FinancialYear ,StockIssueType
from inventory.models import ErpTagging,ErpLotInwardDetails
from billing.models import  ErpInvoiceOldMetalDetails,ErpInvoiceSalesDetails
from django.core.validators import MinValueValidator,MaxValueValidator
from  utilities.constants import (  # Adjust the import path as needed
    PURCHASE_STN_CALC_TYPE_CHOICES,
    SHOW_IN_LWT_CHOICES,
    TAG_STN_CALC_TYPE_CHOICES,

)
from employees.models import Employee
from customers.models import Customers

# Create your models here.
accounts_user = 'accounts.User'
# Create your models here.

class ErpStockTransfer(models.Model):

    TRANSFER_TYPE_CHOICES = [
        (1, 'Tagged Item'),
        (2, 'Non Tag'),
        (3, 'Old Metal'),
        (4, 'Sales Return'),
        (5, 'Partly Sale')
    ]
    
    TRANSFER_STATUS_CHOICES = [
        (0, 'Initiated'),
        (1, 'Approved'),
        (2, 'Downloaded'),
        (3, 'Rejected')
    ]
    TRANS_TYPE_TO = [
        (1, 'Branch'),
        (2, 'Others'),
    ]
    ISSUE_TO = [
        (1, 'Employee'),
        (2, 'Customer'),
        (3, 'Karigar'),
        (4, 'Others')
    ]
    id_stock_transfer = models.AutoField(primary_key=True)
    fin_year           = models.ForeignKey(FinancialYear,on_delete=models.CASCADE,related_name="transfer_fin_year")
    trans_code         = models.CharField(max_length=255)
    trans_date         = models.DateField(null=True, blank=True)
    trans_to_type      = models.IntegerField(choices=TRANS_TYPE_TO, default=1)
    transfer_type      = models.IntegerField(choices=TRANSFER_TYPE_CHOICES, default=1)
    stock_issue_type   = models.ForeignKey(StockIssueType,on_delete=models.CASCADE,related_name="transfer_stock_issue_type",null=True, blank=True)
    supplier           = models.ForeignKey(Supplier,on_delete=models.CASCADE,related_name="transfer_supplier",null=True, blank=True)
    stock_issue_to     = models.IntegerField(choices=ISSUE_TO, default=1,null=True)
    id_employee        = models.ForeignKey(Employee, related_name='stock_issue_employee', on_delete=models.CASCADE,null=True, blank=True)
    id_customer        = models.ForeignKey(Customers, related_name='stock_issue_customer', on_delete=models.CASCADE,null=True, blank=True)
    transfer_from      = models.ForeignKey(Branch, related_name='transfers_from', on_delete=models.CASCADE)
    transfer_to        = models.ForeignKey(Branch, related_name='transfers_to', on_delete=models.CASCADE,null=True, blank=True)
    transfer_status    = models.IntegerField(choices=TRANSFER_STATUS_CHOICES, default=0)
    approved_date      = models.DateTimeField(null=True, blank=True)
    approved_by        = models.ForeignKey(accounts_user, related_name='approved_transfers', on_delete=models.CASCADE, null=True, blank=True)
    downloaded_date    = models.DateTimeField(null=True, blank=True)
    downloaded_by      = models.ForeignKey(accounts_user, related_name='downloaded_transfers', on_delete=models.CASCADE, null=True, blank=True)
    remarks            = models.TextField(null=True,blank=True, default=None)
    scale_weight       = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False,default=0)
    created_by         = models.ForeignKey(accounts_user, related_name='created_transfers', on_delete=models.CASCADE)
    created_on         = models.DateTimeField(auto_now_add=True)
    rejected_by        = models.ForeignKey(accounts_user, related_name='rejected_transfers', on_delete=models.CASCADE, null=True, blank=True)
    rejected_on        = models.DateTimeField(null=True, blank=True)
    reject_reason      = models.TextField(null=True, blank=True)
    updated_on         = models.DateTimeField(auto_now=True,null=True)
    updated_by         = models.ForeignKey(accounts_user, related_name='updated_transfers', on_delete=models.CASCADE, null=True, blank=True)
    class Meta:
        db_table = 'erp_stock_transfer'

class ErpTagTransfer(models.Model):
    STATUS_TYPE = [
        (1, 'Not Yet Download'),
        (2, 'Downloaded'),
        (3, 'Sold Out'),
    ]
    id_tag_transfer    = models.AutoField(primary_key=True)
    stock_transfer     = models.ForeignKey(ErpStockTransfer,on_delete=models.CASCADE,related_name="tag_stock_transfer_id",null=False)
    tag_id             = models.ForeignKey(ErpTagging,on_delete=models.CASCADE,related_name="transfer_tag_id")
    status             = models.IntegerField(choices=STATUS_TYPE, default=1)
    downloaded_date    = models.DateTimeField(null=True, blank=True)
    downloaded_by      = models.ForeignKey(accounts_user, related_name='tag_downloaded_transfers', on_delete=models.CASCADE, null=True, blank=True)
    class Meta:
        db_table = 'erp_transfer_tag_item'

class ErpNonTagTransfer(models.Model):
    id_non_tag_transfer = models.AutoField(primary_key=True)
    stock_transfer  = models.ForeignKey(ErpStockTransfer,on_delete=models.CASCADE,related_name="non_tag_stock_transfer_id",null=False)
    id_lot_inward_detail = models.ForeignKey(ErpLotInwardDetails, on_delete=models.CASCADE, related_name="non_tag_branch_lot_detail_id", null=True, default=None)
    id_section           = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="non_tag_branch_section", null=True, default=None)
    id_product           = models.ForeignKey(Product, on_delete=models.CASCADE,related_name="non_tag_transfer_product_id")
    id_design            = models.ForeignKey(Design, on_delete=models.CASCADE,related_name="non_tag_transfer_design_id")
    id_sub_design        = models.ForeignKey(SubDesign, on_delete=models.CASCADE,related_name="non_tag_transfer_sub_design_id",null=True, default=None)
    pieces               = models.PositiveIntegerField()
    gross_wt             = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    less_wt              = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    net_wt               = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    dia_wt               = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    stone_wt             = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    
    class Meta:
        db_table = 'erp_transfer_non_tag_item'


class ErpNonTagStoneTransfer(models.Model):
    id_non_tag_stn_transfer = models.AutoField(primary_key=True)
    id_non_tag_transfer  = models.ForeignKey(ErpNonTagTransfer,on_delete=models.CASCADE,related_name="non_tag_stock_transfer_id")
    show_in_lwt = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone = models.ForeignKey(Stone, on_delete=models.CASCADE, related_name="non_tag_stock_transfer_stone_id", null=True, default=None)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="non_tag_stock_transfer_quality_code", null=True, default=None)
    uom_id = models.ForeignKey(Uom, on_delete=models.CASCADE, related_name="non_tag_stock_transfer_uom_id", null=True, default=None)
    stone_pcs = models.PositiveIntegerField(validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stn_cal_type = models.IntegerField(choices=PURCHASE_STN_CALC_TYPE_CHOICES, default=1)
    stn_rate     = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stn_cost     = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    
    class Meta:
        db_table = 'erp_transfer_non_tag_stn_item'


class ErpOldMetalTransfer(models.Model):
    id_old_metal_transfer   = models.AutoField(primary_key=True)
    stock_transfer      = models.ForeignKey(ErpStockTransfer,on_delete=models.CASCADE,related_name="old_metal_stock_transfer_id",null=False)
    old_metal_sale_id       = models.ForeignKey(ErpInvoiceOldMetalDetails,on_delete=models.SET_NULL,related_name="transfer_old_metal_id",null=True)
    class Meta:
        db_table = 'erp_transfer_old_metal_item'


class ErpSalesReturnTransfer(models.Model):
    RETURN_TYPE = [(1,'Tagged Itm'),(2,'Non Tagged Item')]
    id_sales_return_transfer   = models.AutoField(primary_key=True)
    stock_transfer             = models.ForeignKey(ErpStockTransfer,on_delete=models.CASCADE,related_name="sales_return_stock_transfer_id",null=False)
    bill_detail_id             = models.ForeignKey(ErpInvoiceSalesDetails,on_delete=models.CASCADE,related_name="transfer_sale_detail_id")
    sales_ret_type             = models.IntegerField(choices=RETURN_TYPE,default=1)
    class Meta:
        db_table = 'erp_transfer_sales_return_item'


class ErpPartlySaleTransfer(models.Model):
    id_partly_sale_transfer = models.AutoField(primary_key=True)
    stock_transfer          = models.ForeignKey(ErpStockTransfer,on_delete=models.CASCADE,related_name="partly_sale_stock_transfer_id",null=False)
    tag_id                  = models.ForeignKey(ErpTagging,on_delete=models.CASCADE,related_name="partly_sale_transfer_tag_id")
    pieces                  = models.PositiveIntegerField()
    gross_wt                = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    less_wt                 = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    net_wt                  = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    dia_wt                  = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    stone_wt                = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],blank=False)
    
    class Meta:
        db_table = 'erp_transfer_partly_sale_item'

class ErpPartlySaleStnTransfer(models.Model):
    id_partly_stn_transfer = models.AutoField(primary_key=True)
    id_partly_sale_transfer = models.ForeignKey(ErpPartlySaleTransfer,on_delete=models.CASCADE,related_name="partly_sale_branch_stone_transfer_id")
    show_in_lwt       = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone          = models.ForeignKey(Stone, on_delete=models.CASCADE,related_name="partly_sale_branch_stn_stone_id",null=True, default=None)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="partly_sale_branch_id_quality_code", null=True, default=None)
    uom_id            = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="partly_sale_branch_stn_uom_id",null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    stone_rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_calc_type   = models.IntegerField(choices=TAG_STN_CALC_TYPE_CHOICES,default=1)
     
    class Meta:
        db_table = 'erp_transfer_partly_sale_stone'