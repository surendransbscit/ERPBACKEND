from django.db import models

from django.core.validators import MinValueValidator, MaxValueValidator
from retailcataloguemasters.models import (Category, Product, Metal, Purity, Design, SubDesign, Stone, ProductCalculationType,Section,QualityCode)
from retailmasters.models import (Supplier, Branch, Uom, Taxgroupitems, FinancialYear,Taxmaster)
from accounts.models import User
from employees.models import Employee
from billing.models import ErpInvoiceSalesDetails,ErpInvoiceOldMetalDetails,ErpInvoiceSalesReturn
from inventory.models import ErpTagging
##Constants

from utilities.constants import POCKET_TYPE,SHOW_IN_LWT_CHOICES,METAL_PROCESS_TYPE

class CommonFields(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User,on_delete=models.PROTECT, null=True,related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User,null=True, on_delete=models.SET_NULL,related_name='%(class)s_updated_by')

    class Meta:
        abstract = True


class ErpPocket(CommonFields):
    id_pocket = models.AutoField(primary_key=True)
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="pocket_branch", default=None)
    entry_date = models.DateField()
    pocket_no = models.CharField(max_length=255,null=False) 
    type = models.IntegerField(choices=POCKET_TYPE, default=3)
    
    class Meta:
        db_table = 'erp_pocket'


class ErpPocketDetails(models.Model):
    id_pocket_detail = models.AutoField(primary_key=True)
    id_pocket = models.ForeignKey(ErpPocket, on_delete=models.CASCADE, related_name='pocket_ref')
    invoice_sale_item_id = models.ForeignKey(ErpInvoiceSalesDetails, on_delete=models.SET_NULL, related_name="pocket_partly_item_id", null=True, default=None)
    invoice_old_metal_item_id = models.ForeignKey(ErpInvoiceOldMetalDetails, on_delete=models.SET_NULL, related_name="pocket_old_metal_item_id", null=True, default=None)
    invoice_return_id = models.ForeignKey(ErpInvoiceSalesReturn, on_delete=models.SET_NULL, related_name="pocket_sales_return_item_id", null=True, default=None)
    tag_id = models.ForeignKey(ErpTagging,on_delete=models.CASCADE, related_name="pocket_partly_sale_tag_id", null=True, default=None)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="pocket_product", null=True, default=None)
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="pocket_design", null=True, default=None)
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE, related_name="pocket_sub_design", null=True, default=None)
    id_section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="pocket_section", null=True, default=None)
    pieces = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    
    class Meta:
        db_table = 'erp_pocket_details'
        indexes = [
            models.Index(fields=['invoice_old_metal_item_id','invoice_sale_item_id','id_product', 'id_design', 'id_sub_design']),
        ]


class ErpPocketStoneDetails(models.Model):
    id_pocket_stn_detail = models.AutoField(primary_key=True)
    id_pocket_detail = models.ForeignKey(ErpPocketDetails, on_delete=models.CASCADE, related_name="pocket_stone_detail", null=True, default=None)
    show_in_lwt       = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone          = models.ForeignKey(Stone, on_delete=models.CASCADE,related_name="pocket_stone_id",null=True, default=None)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="pocket_id_quality_code", null=True, default=None)
    uom_id            = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="pocket_stn_uom_id",null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    

    class Meta:
        db_table = 'erp_pocket_stone_details'
        indexes = [
            models.Index(fields=['id_stone', 'uom_id', 'id_pocket_detail']),
        ]


class ErpPocketOtherMetal(models.Model):
    
    id_purchase_other_metal  = models.AutoField(primary_key=True)
    id_pocket_detail = models.ForeignKey(ErpPocketDetails, on_delete=models.CASCADE, related_name="pocket_other_detail", null=True, default=None)
    id_category         = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="pocket_other_detail_cat_id", null=True, default=None)
    id_purity           = models.ForeignKey(Purity,on_delete=models.CASCADE,related_name="pocket_other_detail_purity_id", null=True, default=None)
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
   
    class Meta:
        db_table = 'erp_pocket_other_metal'


class ErpMetalProcessMaster(CommonFields):
    process_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255,null=False)
    
    class Meta:
        db_table = 'erp_metal_process_master'


class ErpMetalProcess(CommonFields):
    id_metal_process = models.AutoField(primary_key=True)
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="process_branch", default=None)
    entry_date = models.DateField()
    ref_no = models.CharField(max_length=255,null=False)
    type = models.IntegerField(choices=METAL_PROCESS_TYPE, default=1)
    process_id = models.ForeignKey(ErpMetalProcessMaster,on_delete=models.CASCADE, null=True, default=None,related_name="metal_process_master")
    id_supplier = models.ForeignKey(Supplier,on_delete=models.CASCADE, null=False,related_name="process_supplier")
    
    class Meta:
        db_table = 'erp_metal_process'


class ErpMeltingIssueDetails(models.Model):
    id_melting = models.AutoField(primary_key=True)
    id_metal_process = models.ForeignKey(ErpMetalProcess, on_delete=models.CASCADE, related_name='process_ref_id')
    id_pocket = models.ForeignKey(ErpPocket, on_delete=models.CASCADE, related_name='melting_pocket_ref')
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="melting_product", null=True, default=None)
    id_metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="melting_metal", null=True, default=None)
    melting_pieces = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    
    class Meta:
        db_table = 'erp_melting_issue_details'
        indexes = [
            models.Index(fields=['id_metal_process','id_pocket','id_product']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['id_metal_process','id_pocket', 'id_product'], name='unique_melting_pocket_product_details')
        ]


class ErpMeltingReceiptDetails(models.Model):
    id_melting_receipt = models.AutoField(primary_key=True)
    melting_issue_ref_no = models.ForeignKey(ErpMetalProcess, on_delete=models.CASCADE, related_name='melting_issue_process_ref_id',default=None,null=True)
    id_melting_issue = models.ForeignKey(ErpMeltingIssueDetails, on_delete=models.CASCADE, related_name='melting_ref_id',default=None,null=True,blank=True)
    id_metal_process = models.ForeignKey(ErpMetalProcess, on_delete=models.CASCADE, related_name='melting_receipt_process_ref_id')
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="melting_recd_product", null=True, default=None)
    pieces = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    charges = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)],default=0)
    tested_weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],default=0)
    tested_touch = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)],default=0)
    
    class Meta:
        db_table = 'erp_melting_receipt_details'
        indexes = [
            models.Index(fields=['id_melting_issue','id_product']),
        ]


class ErpTestingIssueDetails(models.Model):
    id_testing = models.AutoField(primary_key=True)
    id_metal_process = models.ForeignKey(ErpMetalProcess, on_delete=models.CASCADE, related_name='testing_issue_process_ref_id',default=None,null=True)
    receipt_metal_process = models.ForeignKey(ErpMetalProcess, on_delete=models.CASCADE, related_name='testing_receipt_process_ref_id',default=None,null=True)
    id_melting_receipt = models.ForeignKey(ErpMeltingReceiptDetails, on_delete=models.CASCADE, related_name='melting_receipt_id')
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="testing_issue_product", null=True, default=None)
    pieces = models.PositiveIntegerField()
    issue_weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    received_weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],default=0)
    touch = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],default=0)
    charges = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)],default = 0)
    
    class Meta:
        db_table = 'erp_testing_details'
        indexes = [
            models.Index(fields=['id_melting_receipt','id_product','id_metal_process','receipt_metal_process']),
        ]


class ErpRefining(models.Model):
    id_refining = models.AutoField(primary_key=True)
    issue_id_metal_process = models.ForeignKey(ErpMetalProcess, on_delete=models.CASCADE, related_name='refining_issue_process_ref_id',default=None,null=True)
    receipt_id_metal_process = models.ForeignKey(ErpMetalProcess, on_delete=models.CASCADE, related_name='refining_receipt_process_ref_id',default=None,null=True)
    charges = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)],default = 0)
    class Meta:
        db_table = 'erp_refining'


class ErpRefiningDetails(models.Model):
    id_refining_details = models.AutoField(primary_key=True)
    id_refining = models.ForeignKey(ErpRefining, on_delete=models.CASCADE, related_name='refining_issue_ref_id',default=None,null=True)
    id_melting_receipt = models.ForeignKey(ErpMeltingReceiptDetails, on_delete=models.CASCADE, related_name='refining_melting_receipt_id')
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="refining_issue_product", null=True, default=None)
    pieces = models.PositiveIntegerField()
    issue_weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    
    class Meta:
        db_table = 'erp_refining_details'


class ErpRefiningReceiptDetails(models.Model):
    id_refining_receipt_details = models.AutoField(primary_key=True)
    id_refining = models.ForeignKey(ErpRefining, on_delete=models.CASCADE, related_name='refining_receipt_ref_id',default=None,null=True)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="refining_recd_product", null=True, default=None)
    pieces = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    
    class Meta:
        db_table = 'erp_refining_receipt_details'