from django.db import models
from datetime import datetime
from retailcataloguemasters.models import Category, Product, Metal, Purity, Design, SubDesign, Stone, ProductCalculationType,QualityCode,Section
from retailmasters.models import Branch, Uom, Taxmaster, OtherCharges,Size,OldMetalItemType
from inventory.models import ErpTagging,ErpTaggingStone,ErpTagOtherMetal
from customers.models import Customers
from employees.models import Employee
from managescheme.models import SchemeAccount
from django.core.validators import MinValueValidator, MaxValueValidator

from  utilities.constants import (  # Adjust the import path as needed
    TAG_STN_CALC_TYPE_CHOICES,
    ITEM_TYPE_CHOICES,
    MC_TYPE_CHOICES,
    TAX_TYPE_CHOICES,
    STATUS_CHOICES,
    SHOW_IN_LWT_CHOICES,
    TAG_OTHER_METAL_CALC_TYPE_CHOICES,
    PARTIAL_SALE_CHOICES
)

accounts_user = 'accounts.User'

class ErpEstimation(models.Model):
    EST_FOR_CHOICES = [(1, 'Customer'),(2, 'Branch')]
    EST_APPROVED = [(1, 'Yes'),(0, 'No')]
    STATUS_CHOICES = [
    (0, 'Waiting For Approval'),
    (1, 'Approved'),
    (2, 'Rejected')
    ]
    estimation_id = models.AutoField(primary_key=True)
    metal = models.ForeignKey(Metal, on_delete=models.CASCADE,default=None,null=True, blank=True)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="est_branch")
    entry_date = models.DateField(null=False, blank=False)
    estimation_for = models.IntegerField(choices=EST_FOR_CHOICES, default=1)
    is_approved = models.IntegerField(choices=STATUS_CHOICES, default=0)
    is_estimation_approve_req = models.BooleanField(default=0)
    id_customer = models.ForeignKey(Customers, on_delete=models.CASCADE, related_name="est_customer",default=None, null=True, blank=True)
    est_no = models.CharField(max_length=255, null=False, blank=False)
    sales_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=False)
    purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=False)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=False)
    total_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=False)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=False)
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=False, blank=False)
    id_employee = models.ForeignKey(Employee, related_name='est_employee', on_delete=models.CASCADE)
    invoice_id = models.ForeignKey('billing.ErpInvoice', on_delete=models.CASCADE, related_name="est_sold_invoice",default=None, null=True, blank=True)
    created_by = models.ForeignKey(accounts_user, related_name='est_created_employee', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(accounts_user, related_name='est_approved_employee', on_delete=models.CASCADE, default=None, null=True)
    approved_on = models.DateTimeField(default=None, null=True)
    updated_by = models.ForeignKey(accounts_user, related_name='estimation_updated_by', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)
    send_to_approval = models.BooleanField(default=False)

    class Meta:
        db_table = 'erp_estimation'


class ErpEstimationSalesDetails(models.Model):
    est_item_id = models.AutoField(primary_key=True)
    estimation_id = models.ForeignKey(ErpEstimation, on_delete=models.CASCADE, related_name="sales_invoice_id")
    item_type = models.IntegerField(choices=ITEM_TYPE_CHOICES, default=0)
    is_partial_sale = models.IntegerField(choices=PARTIAL_SALE_CHOICES, default=0)
    id_purity = models.ForeignKey(Purity, on_delete=models.CASCADE, null=False, blank=False)
    uom_id = models.ForeignKey(Uom, on_delete=models.CASCADE, null=True)
    tag_id = models.ForeignKey(ErpTagging, on_delete=models.CASCADE, null=True, related_name="est_tag_id")
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, blank=False, related_name="est_product")
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, null=True, blank=False, default=None,related_name="est_design")
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE, null=True,default=None, blank=False, related_name="est_sub_design")
    id_section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True,default=None, related_name="est_section")
    pieces = models.PositiveIntegerField(null=False, blank=False, default=0)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    wastage_percentage = models.DecimalField(max_digits=10,null=False, blank=False,decimal_places=2, default=0.000, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    wastage_weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, null=False)
    other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, null=False)
    mc_type = models.IntegerField(choices=MC_TYPE_CHOICES, default=1)
    mc_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    flat_mc_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    total_mc_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    sell_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    other_charges_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    other_metal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    tax_id = models.ForeignKey(Taxmaster, on_delete=models.CASCADE,null=True)
    tax_type = models.IntegerField(choices=TAX_TYPE_CHOICES, default=2)
    tax_percentage = models.DecimalField(max_digits=10, null=True, blank=True, decimal_places=2, default=0.00, validators=[MaxValueValidator(100.0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    cgst_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    sgst_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    igst_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    wastage_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    mc_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    ref_emp_id = models.ForeignKey(Employee, on_delete=models.CASCADE,default=None,null=True)
    ref_emp_id_1            = models.ForeignKey(Employee,related_name="est_support_emp_1", on_delete=models.CASCADE,null=True, default=None)
    ref_emp_id_2            = models.ForeignKey(Employee,related_name="est_support_emp_2", on_delete=models.CASCADE,null=True, default=None)
    invoice_sale_item_id = models.ForeignKey('billing.ErpInvoiceSalesDetails', on_delete=models.CASCADE, null=True,related_name="est_sales_inv",)
    size = models.ForeignKey(Size,on_delete=models.CASCADE,related_name="est_size",null=True, default=None)
    wastage_percentage_after_disc = models.DecimalField(max_digits=10,null=False, blank=False, decimal_places=2,default=0.00, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])

    class Meta:
        db_table = 'erp_estimation_sales_details'
        indexes = [
            models.Index(fields=['estimation_id', 'tag_id', 'id_product', 'id_design', 'id_sub_design']),
        ]


class ErpEstimationSalesReturnDetails(models.Model):
    est_return_item_id = models.AutoField(primary_key=True)
    estimation_id = models.ForeignKey(ErpEstimation, on_delete=models.CASCADE, related_name="ret_est_id")
    id_purity = models.ForeignKey(Purity, on_delete=models.CASCADE, null=False, blank=False)
    uom_id = models.ForeignKey(Uom, on_delete=models.CASCADE, null=True)
    tag_id = models.ForeignKey(ErpTagging, on_delete=models.CASCADE, null=True, related_name="est_ret_tag_id")
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, blank=False, related_name="est_ret_product")
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, null=True, blank=True, related_name="est_ret_design")
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE, null=True,default=None, blank=False, related_name="est_ret_sub_design")
    pieces = models.PositiveIntegerField(null=False, blank=False, default=0)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    wastage_percentage = models.DecimalField(max_digits=10,null=False, blank=False,decimal_places=2, default=0.000, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    wastage_weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, null=False)
    mc_type = models.IntegerField(choices=MC_TYPE_CHOICES, default=1)
    mc_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    total_mc_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    sell_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    tax_id = models.ForeignKey(Taxmaster, on_delete=models.CASCADE,null=True)
    tax_type = models.IntegerField(choices=TAX_TYPE_CHOICES, default=2)
    tax_percentage = models.DecimalField(max_digits=10, null=True, blank=True, decimal_places=2, default=0.00, validators=[MaxValueValidator(100.0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    cgst_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    sgst_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    igst_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    invoice_sale_item_id = models.ForeignKey('billing.ErpInvoiceSalesDetails', on_delete=models.CASCADE, null=True,related_name="est_sales_return_inv",)
    invoice_return_id = models.ForeignKey('billing.ErpInvoiceSalesReturn', on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = 'erp_estimation_sales_return_details'
        indexes = [
            models.Index(fields=['estimation_id','invoice_sale_item_id', 'tag_id', 'id_product', 'id_design', 'id_sub_design']),
        ]

class ErpEstimationOldMetalDetails(models.Model):
    est_old_metal_item_id = models.AutoField(primary_key=True)
    estimation_id = models.ForeignKey(ErpEstimation, on_delete=models.CASCADE)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, blank=False, related_name="est_old_metal_product_id")
    item_type  = models.ForeignKey(OldMetalItemType, on_delete=models.CASCADE, null=True,default=None)
    pieces = models.PositiveIntegerField(null=False, blank=False, default=0)
    touch = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    dust_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    wastage_percentage = models.IntegerField(null=True, blank=True, default=0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    wastage_weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, null=False)
    pure_weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, null=False)
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    customer_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    invoice_old_metal_item_id = models.ForeignKey('billing.ErpInvoiceOldMetalDetails', on_delete=models.CASCADE, null=True)



    class Meta:
        db_table = 'erp_estimation_old_metal_details'
        indexes = [
            models.Index(fields=['estimation_id', 'id_product']),
        ]

class ErpEstimationStoneDetails(models.Model):
    est_stn_id = models.AutoField(primary_key=True)
    est_item_id = models.ForeignKey(ErpEstimationSalesDetails, on_delete=models.CASCADE, blank=True, null=True, related_name="stn_est_item_id")
    est_old_metal_item_id = models.ForeignKey(ErpEstimationOldMetalDetails, on_delete=models.CASCADE, blank=True, null=True, related_name="stn_est_old_metal_item_id")
    id_tag_stn_detail = models.ForeignKey(ErpTaggingStone,on_delete=models.SET_NULL,null=True,default=None, related_name="est_tag_stn_detail_id")
    est_return_item_id = models.ForeignKey(ErpEstimationSalesReturnDetails, on_delete=models.CASCADE, blank=True, null=True, related_name="stn_est_return_item_id")
    show_in_lwt = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone = models.ForeignKey(Stone, on_delete=models.CASCADE, related_name="est_stone_id", null=False, blank=False)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="est_id_quality_code", null=True, default=None)
    uom_id = models.ForeignKey(Uom, on_delete=models.CASCADE, related_name="est_uom_id", null=False, blank=False)
    stone_pcs = models.PositiveIntegerField(null=False, blank=False)
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0, validators=[MinValueValidator(0.0)])
    stone_rate = models.DecimalField(max_digits=10, decimal_places = 2, default=0, validators=[MinValueValidator(0.0)])
    stone_amount = models.DecimalField(max_digits=10, decimal_places = 2, default=0, validators=[MinValueValidator(0.0)])
    stone_calc_type = models.IntegerField(choices=TAG_STN_CALC_TYPE_CHOICES, default=1)



    class Meta:
        db_table = 'erp_estimation_stone_details'
        indexes = [
            models.Index(fields=['id_stone', 'est_item_id', 'est_old_metal_item_id', 'uom_id']),
        ]

class ErpEstimationItemCharges(models.Model):
    charges_est_item_id = models.AutoField(primary_key=True)
    est_item_id = models.ForeignKey(ErpEstimationSalesDetails, on_delete=models.CASCADE, null=False, blank=False, related_name="charge_est_item_id")
    id_charges = models.ForeignKey(OtherCharges, on_delete=models.CASCADE, null=False, blank=False)
    charges_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_estimation_charges_details'

class ErpEstimationSchemeAdjusted(models.Model):
    est_scheme_adj_id = models.AutoField(primary_key=True)
    estimation_id = models.ForeignKey(ErpEstimation, on_delete=models.CASCADE, null=False, blank=False, related_name="est_scheme_id")
    id_scheme_account = models.ForeignKey(SchemeAccount, on_delete=models.CASCADE, null=False, blank=False, related_name="est_scheme_adjust_id")
    closing_weight        = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage               = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc             = models.DecimalField(max_digits=10,decimal_places=2,default=0.00, validators=[MinValueValidator(0.0)])
    closing_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0.00, validators=[MinValueValidator(0.0)])
    rate_per_gram = models.DecimalField(max_digits=10,decimal_places=2,default=0.00, validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_est_scheme_adjusted_details'

class ErpEstimationOtherMetal(models.Model):
    
    id_est_other_metal  = models.AutoField(primary_key=True)
    est_item_id         = models.ForeignKey(ErpEstimationSalesDetails, on_delete=models.CASCADE, null=False, blank=False, related_name="erp_est_other_metal_est_item_id")
    id_tag_other_metal  = models.ForeignKey(ErpTagOtherMetal,on_delete=models.SET_NULL,null=True,default=None, related_name="est_tag_other_metal_id")
    id_category         = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="erp_est_other_metal_cat_id", null=True, default=None)
    id_purity           = models.ForeignKey(Purity,on_delete=models.CASCADE,related_name="erp_est_other_metal_purity_id", null=True, default=None)
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_type             = models.IntegerField(choices=MC_TYPE_CHOICES,default=1)
    calc_type             = models.IntegerField(choices=TAG_OTHER_METAL_CALC_TYPE_CHOICES,default=1)
    mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    rate_per_gram       = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    other_metal_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_est_other_metal'
