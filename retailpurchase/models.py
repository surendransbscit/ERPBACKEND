from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from retailcataloguemasters.models import (
    Category, Product, Metal, Purity, Design, SubDesign, Stone, ProductCalculationType,Section,QualityCode
)
from retailmasters.models import (
    Supplier, Branch, Uom, Taxgroupitems, FinancialYear,Taxmaster,OtherCharges
)
from employees.models import Employee
from customers.models import Customers

from  utilities.constants import (  # Adjust the import path as needed
    TAX_TYPE_CHOICES,
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
    BILL_TYPE_CHOICES
)
accounts_user = 'accounts.User'

# Models
from accounts.models import User


class CommonFields(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True,null=True)
    created_by = models.ForeignKey(User,on_delete=models.PROTECT, null=True,related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User,null=True, on_delete=models.SET_NULL,related_name='%(class)s_updated_by',default=None)

    class Meta:
        abstract = True

class ErpPurchaseEntry(CommonFields):
    id_purchase_entry = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_supplier")
    entry_date = models.DateField()
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="purchase_branch", default=None)
    supplier_bill_ref_no = models.CharField(max_length=255,null=True,blank=True,default=None) 
    supplier_bill_ref_date = models.DateField(null=True,blank=True,default=None)
    payment_date = models.DateField(null=True,blank=True,default=None)
    is_cancelled = models.BooleanField(default=False)
    is_rate_fixed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    auto_lot_generate = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_approved_by', null=True, blank=True)
    approved_on = models.DateTimeField(null=True,blank=False,default=None)
    cancelled_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_cancelled_by', null=True, blank=True)
    cancelled_on = models.DateTimeField(null=True,blank=False,default=None)
    cancelled_reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True , default = None , null = True)
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    tds_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    tds_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    net_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    class Meta:
        db_table = 'erp_purchase_entry'

    def __str__(self):
        return f"Purchase Entry {self.ref_no}"


class ErpPurchaseEntryDetails(models.Model):
    id_purchase_entry_detail = models.AutoField(primary_key=True)
    purchase_entry = models.ForeignKey(ErpPurchaseEntry, on_delete=models.CASCADE, related_name='purchase_details')
    id_purity = models.ForeignKey(Purity, on_delete=models.CASCADE, related_name="purchase_purity", null=True, default=None)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="purchase_product", null=True, default=None)
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="purchase_design", null=True, default=None)
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE, related_name="purchase_sub_design", null=True, default=None)
    id_section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="purchase_section", null=True, default=None)
    is_halmarked = models.BooleanField(default=False)
    pieces = models.PositiveIntegerField()
    uom_id = models.ForeignKey(Uom,on_delete=models.CASCADE, related_name="purchase_uom", null=True, default=None)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    sell_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)])
    purchase_touch = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_va = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_mc = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_flat_mc = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_mc_type = models.IntegerField(choices=PURCHASE_MC_TYPE_CHOICES, default=1)
    pure_wt_cal_type = models.IntegerField(choices=PURE_WT_CALC_TYPE_CHOICES, default=1)
    purchase_rate_type = models.IntegerField(choices=PURCHASE_RATE_TYPE_CHOICES, default=1)
    purchase_calculation = models.ForeignKey(ProductCalculationType, on_delete=models.CASCADE, null=True, default=None, related_name="purchase_product_calculation_type")
    purchase_tax_group = models.ForeignKey(Taxgroupitems, on_delete=models.CASCADE, null=True, related_name='purchase_tax_group', default=None)
    purchase_taxable_amt = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    pure_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    total_mc_value          = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    tax_id                  = models.ForeignKey(Taxmaster, on_delete=models.CASCADE,null=True,default = None)
    tax_type                = models.IntegerField(choices=TAX_TYPE_CHOICES, default=2)
    tax_amount              = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    cgst_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    sgst_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    igst_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    class Meta:
        db_table = 'erp_purchase_item_details'
        indexes = [
            models.Index(fields=['id_product', 'id_design', 'id_sub_design']),
        ]
        # constraints = [
        #     models.UniqueConstraint(fields=['purchase_entry', 'id_product', 'id_design', 'id_sub_design'], name='unique_purchase_details')
        # ]

    def __str__(self):
        return f"Purchase Detail {self.id_purchase_entry_detail}"


class ErpPurchaseStoneDetails(models.Model):
    id_purchase_stn_detail = models.AutoField(primary_key=True)
    purchase_entry_detail = models.ForeignKey(ErpPurchaseEntryDetails, on_delete=models.CASCADE, related_name="purchase_stone_detail", null=True, default=None)
    show_in_lwt       = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone          = models.ForeignKey(Stone, on_delete=models.CASCADE,related_name="purchase_stn_stone_id",null=True, default=None)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="purchase_id_quality_code", null=True, default=None)
    uom_id            = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="purchase_stn_uom_id",null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    pur_st_rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    pur_stn_cost      = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    pur_stn_cal_type   = models.IntegerField(choices=TAG_STN_CALC_TYPE_CHOICES,default=1)


    class Meta:
        db_table = 'erp_purchase_stone_details'
        indexes = [
            models.Index(fields=['id_stone', 'uom_id', 'purchase_entry_detail']),
        ]


class ErpPurchaseOtherMetal(models.Model):
    
    id_purchase_other_metal  = models.AutoField(primary_key=True)
    purchase_entry_detail = models.ForeignKey(ErpPurchaseEntryDetails, on_delete=models.CASCADE, related_name="purchase_other_detail", null=True, default=None)
    id_category         = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="purchase_other_detail_cat_id", null=True, default=None)
    id_purity           = models.ForeignKey(Purity,on_delete=models.CASCADE,related_name="purchase_other_detail_purity_id", null=True, default=None)
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_type             = models.IntegerField(choices=TAG_OTHER_METAL_MC_TYPE_CHOICES,default=1)
    mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    rate_per_gram       = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    other_metal_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_purchase_other_metal'

class ErpPurchaseIssueReceipt(CommonFields):

    ISSUE_TYPE_CHOICE = [(1, 'Qc'),(2, 'Halmarking')]
    ISSUE_STATUS = [(0, 'Issued'),(1, 'Receipted'),(2, 'Canceled')]


    id_issue_receipt = models.AutoField(primary_key=True)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="purchase_issued_branch", default=None)
    issue_type       = models.IntegerField(choices=ISSUE_TYPE_CHOICE,default=1)
    issue_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    issue_to_emp = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="issued_emp", null=True, default=None)
    issue_to_supplier =  models.ForeignKey('retailmasters.Supplier', on_delete=models.PROTECT, null=True, default=None)
    issue_date = models.DateField()
    status       = models.IntegerField(choices=ISSUE_STATUS,default=0)
    cancelled_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_issued_cancelled_by', null=True, blank=True)
    cancelled_on = models.DateTimeField(null=True,blank=False,default=None)
    cancelled_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'erp_purchase_item_issue_receipt'

    def __str__(self):
        return f"Purchase Entry Issue {self.issue_no}"
    
class ErpPurchaseIssueReceiptDetails(models.Model):

    id_issue_receipt_detail = models.AutoField(primary_key=True)
    issue_receipt = models.ForeignKey(ErpPurchaseIssueReceipt, on_delete=models.CASCADE, related_name='purchase_issues')
    purchase_entry_detail = models.ForeignKey(ErpPurchaseEntryDetails, on_delete=models.CASCADE, related_name="purchase_issue_detail", null=True, default=None)
    pieces = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    pure_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    recd_pieces = models.PositiveIntegerField(default=0)
    recd_gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],default=0.000)
    recd_less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0.000)
    recd_net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)], default=0.000)
    recd_dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],default=0.000)
    recd_stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],default=0.000)
    recd_other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    recd_pure_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    recd_purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)


   
    class Meta:
        db_table = 'erp_purchase_item_issue_receipt_details'

    def __str__(self):
        return f"Purchase Issue Receipt Detail {self.id_issue_receipt_detail}"
    

class ErpPurchaseIssueReceiptStoneDetails(models.Model):
    id_issue_stn_detail = models.AutoField(primary_key=True)
    issue_receipt_detail = models.ForeignKey(ErpPurchaseIssueReceiptDetails, on_delete=models.CASCADE, related_name="issue_receipt_stone_detail", null=True, default=None)
    purchase_stn_detail = models.ForeignKey(ErpPurchaseStoneDetails, on_delete=models.CASCADE, related_name="issue_receipt_stone", null=True, default=None)
    show_in_lwt       = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone          = models.ForeignKey(Stone, on_delete=models.CASCADE,related_name="issue_receipt_stone_id",null=True, default=None)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="issue_receipt_quality_code", null=True, default=None)
    uom_id            = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="issue_receipt_uom_id",null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    pur_st_rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    pur_stn_cost      = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    pur_stn_cal_type   = models.IntegerField(choices=TAG_STN_CALC_TYPE_CHOICES,default=1)
    recd_pcs         = models.PositiveIntegerField(default=0)
    recd_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])


    class Meta:
        db_table = 'erp_purchase_issue_receipt_stone_details'
        indexes = [
            models.Index(fields=['id_stone', 'uom_id', 'issue_receipt_detail']),
        ]


class ErpPurchaseIssueReceiptOtherMetal(models.Model):
    
    id_issue_other_metal  = models.AutoField(primary_key=True)
    issue_receipt_detail = models.ForeignKey(ErpPurchaseIssueReceiptDetails, on_delete=models.CASCADE, related_name="issue_receipt_other_detail", null=True, default=None)
    purchase_other_metal = models.ForeignKey(ErpPurchaseOtherMetal, on_delete=models.CASCADE, related_name="issue_receipt_other_metal", null=True, default=None)
    id_category         = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="issue_receipt_other_detail_cat_id", null=True, default=None)
    id_purity           = models.ForeignKey(Purity,on_delete=models.CASCADE,related_name="issue_receipt_other_detail_purity_id", null=True, default=None)
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_type             = models.IntegerField(choices=TAG_OTHER_METAL_MC_TYPE_CHOICES,default=1)
    mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    other_metal_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    recd_pcs         = models.PositiveIntegerField(default=0)
    recd_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_purchase_issue_receipt_other_metal'

class ErpSupplierPayment(CommonFields):
    PAYMENT_TYPE_CHOICES = [
        (1,'Against po'),
        (2,'Against metal process'),
    ]
    id_purchase_payment = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_payment")
    entry_date = models.DateField()
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="payment_branch", default=None)
    cash_from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="cash_from_branch", default=None)
    remarks= models.TextField(null=True, default=None)
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    class Meta:
        db_table = 'erp_supplier_payment'
    def __str__(self):
        return f"Supplier Payment {self.id_purchase_payment}"
    
class ErpSupplierPaymentDetails(CommonFields):
    PAYMENT_TYPE_CHOICES = [
        (1,'Against po'),
        (2,'Against metal process'),
        (3,'Against Repair Order'),
        (4,'Against Opening'),
        (5,'Advance'),
        (6,'Credit Received from Supplier'),
    ]
    id_payment_details = models.AutoField(primary_key=True)
    purchase_payment    = models.ForeignKey(ErpSupplierPayment, on_delete=models.PROTECT, related_name='purchase_payment_details', null=True, default=None)
    ref_id = models.IntegerField(null=True, blank=False,default=None)
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True,default=None,related_name="supplier_payment_ref")
    type   = models.IntegerField(choices=PAYMENT_TYPE_CHOICES,default=1)
    metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="supplier_payment_metal", null=True, default=None)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'erp_supplier_payment_details'
    def __str__(self):
        return f"Supplier Payment Details {self.id_payment_details}"

class ErpSupplierPaymentModeDetail(models.Model):
    CARD_TYPE_CHOICES = [
        (0, ''),
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    PAYMENT_TYPE_CHOICES = [
        (1,'Credit'),
        (2,'Debit'),
    ]
    id_payment_mode     = models.AutoField(primary_key=True)
    purchase_payment    = models.ForeignKey(ErpSupplierPayment, on_delete=models.PROTECT, related_name='purchase_payment_mode_details', null=True)
    id_bank                 = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, blank=True,default=None)
    payment_date            = models.DateTimeField(auto_now_add=True)
    payment_type            = models.IntegerField(choices=PAYMENT_TYPE_CHOICES,default=1)
    payment_mode            = models.ForeignKey('retailmasters.PaymentMode', on_delete=models.PROTECT, null=True)
    payment_amount          = models.DecimalField(max_digits=10, decimal_places=2)
    card_no                 = models.CharField(max_length=15, null=True,blank=True, default=None)
    card_holder             = models.CharField(max_length=75, null=True,blank=True,default=None)
    payment_ref_number      = models.CharField(max_length=25, null=True, blank=True,default=None)
    payment_status          = models.IntegerField(default = 0)
    card_type               = models.IntegerField(choices=CARD_TYPE_CHOICES, null=True, default=0)
    NB_type                 = models.IntegerField(default = 0, null=True,blank=True,) 
    net_banking_date        =  models.DateTimeField(null=True, default=None)
    remark                  = models.CharField(max_length=275, null=True)
    id_pay_device           = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='purchase_payment_pay_device_id', null=True)
       
    class Meta:
        db_table = 'erp_supplier_payment_mode'

class ErpSupplierRateCutAndMetalIssue(models.Model):
    STATUS_CHOICES = [(1, 'Success'),(2, 'Cancelled')]
    id = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="supplier_ratecut_metal_issue_branch", default=None)
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="id_supplier_ratecut_metal_issue",blank=False,default=None)
    entry_date = models.DateField(blank=False,default=None)
    status = models.IntegerField(choices=STATUS_CHOICES,default=1)
    remarks = models.TextField(null=True, default=None)
    created_on = models.DateTimeField(null=True, default=None)
    updated_on = models.DateTimeField(null=True, default=None)
    created_by = models.ForeignKey(User,on_delete=models.PROTECT, null=True,related_name='supplier_ratecut_metal_issue_created_by')
    updated_by = models.ForeignKey(User,null=True, on_delete=models.SET_NULL,related_name='supplier_ratecut_metal_issue_updated_by')
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    class Meta:
        db_table = 'erp_supplier_rate_cut_and_metal_issue'
    def __str__(self):
        return f"Supplier Rate Cut and Metal Issue {self.id}"    

class ErpSupplierRateCut(CommonFields):
    TYPE_CHOICES = [
        (1,'Purchase Payment'),
        (2,'Against Opening'),
        (3,'Advance Rate Cut'),
    ]
    id_rate_cut = models.AutoField(primary_key=True)
    parent = models.ForeignKey(ErpSupplierRateCutAndMetalIssue, on_delete=models.CASCADE, related_name='rate_cut_parent', null=True, default=None)
    type   = models.IntegerField(choices=TYPE_CHOICES,default=1)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_rate_cut",blank=False,default=None)
    entry_date = models.DateField(blank=False,default=None)
    purchase_entry    = models.ForeignKey(ErpPurchaseEntry, on_delete=models.PROTECT, related_name='po_details', null=True)
    id_metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="rate_cut_metal", null=True, default=None)
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2)
    pure_wt = models.DecimalField(max_digits=10, decimal_places=3)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2,default = 0)
    dicount_wt = models.DecimalField(max_digits=10, decimal_places=3,default = 0)
    remarks= models.TextField(null=True, default=None)
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    class Meta:
        db_table = 'erp_rate_cut'
    def __str__(self):
        return f"Rate Cut {self.id_rate_cut}"


class ErpCustomerRateCut(models.Model):
    TYPE_CHOICES = [
        (1,'Purchase Payment'),
        (2,'Against Opening'),
    ]
    id_cus_rate_cut = models.AutoField(primary_key=True)
    type   = models.IntegerField(choices=TYPE_CHOICES,default=1)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_customer = models.ForeignKey(Customers, on_delete=models.CASCADE, related_name="customer_rate_cut",blank=False,default=None)
    entry_date = models.DateField(blank=False,default=None)
    erp_invoice_id    = models.ForeignKey('billing.ErpInvoice', on_delete=models.PROTECT, related_name='rate_cut_invoice', null=True)
    id_metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="customer_rate_cut_metal", null=True, default=None)
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2)
    pure_wt = models.DecimalField(max_digits=10, decimal_places=3)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2,default = 0)
    remarks= models.TextField(null=True, default=None)
    class Meta:
        db_table = 'erp_customer_rate_cut'
    def __str__(self):
        return f"Rate Cut {self.id_cus_rate_cut}"

        

class ErpSupplierMetalIssue(models.Model):
    TYPE_CHOICES = [
        (1,'Purchase Payment'),
        (2,'Metal Issue'),
    ]
    STATUS_CHOICES = [(1, 'Success'),(2, 'Cancelled')]
    
    id_issue = models.AutoField(primary_key=True)
    parent = models.ForeignKey(ErpSupplierRateCutAndMetalIssue, on_delete=models.CASCADE, related_name='metal_issue_parent', null=True, default=None)
    type   = models.IntegerField(choices=TYPE_CHOICES,default=1)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="supplier_metal_issue_branch", default=None)
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="id_supplier_metal_issue",blank=False,default=None)
    entry_date = models.DateField(blank=False,default=None)
    status = models.IntegerField(choices=STATUS_CHOICES,default=1)
    remarks = models.TextField(null=True, default=None)
    created_on = models.DateTimeField(auto_now_add=True,null=True)
    updated_on = models.DateTimeField(null=True, default=None)
    created_by = models.ForeignKey(User,on_delete=models.PROTECT, null=True,related_name='supplier_metal_issue_created_by')
    updated_by = models.ForeignKey(User,null=True, on_delete=models.SET_NULL,related_name='supplier_metal_issue_updated_by')
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    class Meta:
        db_table = 'erp_supplier_metal_issue'
    def __str__(self):
        return f"Supplier Metal Issue {self.id_issue}"    
class ErpSupplierMetalIssueDetails(models.Model):
    TYPE_CHOICES = [
        (1,'Purchase Payment'),
        (2,'Metal Issue'),
        (3,'Purchase Payment Advance'),
        (4,'Against Opening'),
    ]
    id_metal_issue = models.AutoField(primary_key=True)
    type   = models.IntegerField(choices=TYPE_CHOICES,default=1)
    issue   = models.ForeignKey(ErpSupplierMetalIssue, on_delete=models.PROTECT, related_name='po_metal_issue_details', null=True,default=None)
    purchase_entry    = models.ForeignKey(ErpPurchaseEntry, on_delete=models.PROTECT, related_name='po_metal_issue_details', null=True,default=None)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, default=None)
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE,null=True, default=None)
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE,null=True, default=None)
    touch = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)],default=0)
    issue_weight = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    discount = models.DecimalField(max_digits=10, decimal_places=3,default = 0)
    pure_wt = models.DecimalField(max_digits=10, decimal_places=3)
    class Meta:
        db_table = 'erp_supplier_metal_issue_details'
    def __str__(self):
        return f"Supplier Metal Issue {self.id_metal_issue}"
    
class ErpAccountStockProcess(CommonFields):
    PROCESS_TYPE_CHOICES = [
        (1,'Melting'),
        (2,'Lot Generate'),
        (3,'Non Tag'),
        (4,'Metal Issue'),
    ]
    STATUS_CHOICES = [(1, 'Success'),(2, 'Cancelled')]
    STOCK_TYPE_CHOICES = [(1, 'Sales Return'),(2, 'Partly sale'),(3, 'Old Metal')]


    id_account_stock_process = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="account_stock_branch", default=None)
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    entry_date = models.DateField(blank=False,default=None)
    process_type   = models.IntegerField(choices=PROCESS_TYPE_CHOICES,default=1)
    stock_type   = models.IntegerField(choices=STOCK_TYPE_CHOICES,default=1)
    status = models.IntegerField(choices=STATUS_CHOICES,default=1)
    class Meta:
        db_table = 'erp_account_stock_process'
    def __str__(self):
        return f"Rate Cut {self.id_account_stock_process}"
    
class ErpAccountStockProcessDetails(models.Model):
    id_details = models.AutoField(primary_key=True)
    account_stock = models.ForeignKey(ErpAccountStockProcess, on_delete=models.CASCADE, related_name='account_stock_issues')
    invoice_sale_item_id = models.ForeignKey('billing.ErpInvoiceSalesDetails', on_delete=models.SET_NULL, related_name="account_stock_invoice_sale", null=True, default=None)
    invoice_old_metal_item_id = models.ForeignKey('billing.ErpInvoiceOldMetalDetails', on_delete=models.SET_NULL, related_name="account_stock_invoice_old_metal", null=True, default=None)
    invoice_return_id = models.ForeignKey('billing.ErpInvoiceSalesReturn', on_delete=models.CASCADE, related_name="account_stock_invoice_return", null=True, default=None)
    id_purity = models.ForeignKey(Purity, on_delete=models.CASCADE, related_name="account_stock_purity", null=True, default=None)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="account_stock_product", null=True, default=None)
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="account_stock_design", null=True, default=None)
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE, related_name="account_stock_sub_design", null=True, default=None)
    id_section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="account_stock_section", null=True, default=None)
    uom_id = models.ForeignKey(Uom,on_delete=models.CASCADE, related_name="account_stock_uom", null=True, default=None)
    tag_id = models.ForeignKey('inventory.ErpTagging',on_delete=models.CASCADE, related_name="account_stock_tag", null=True, default=None)
    pieces = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    dia_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    stone_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    other_metal_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    class Meta:
        db_table = 'erp_account_stock_process_details'
    def __str__(self):
        return f"Rate Cut {self.id_details}"
    
class ErpPurchaseEntryCharges(models.Model):

    id_purchase_charges = models.AutoField(primary_key=True)
    purchase_entry_detail         = models.ForeignKey(ErpPurchaseEntryDetails,on_delete=models.CASCADE,null=False,blank=False)
    id_charges                   = models.ForeignKey(OtherCharges,on_delete=models.CASCADE,null=False,blank=False)
    charges_amount               = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_purchase_item_charges_details'


class ErpPurchaseEntryChargesDetails(models.Model):

    id_purchase_charges      = models.AutoField(primary_key=True)
    id_purchase_entry        = models.ForeignKey(ErpPurchaseEntry,on_delete=models.CASCADE,null=False,blank=False)
    id_charges               = models.ForeignKey(OtherCharges,on_delete=models.CASCADE,null=False,blank=False)
    charges_amount           = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_purchase_entry_charges_details'
        
        
class ErpPurchaseReturn(models.Model):
    STATUS_CHOICES = [
        (1, 'Success'),
        (2, 'Canceled')
    ]
    id_purchase_return = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None)
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None) 
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_return_id_supplier",blank=False,default=None)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="purchase_return_stock_branch", default=None)
    entry_date = models.DateField(blank=False,default=None)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    remarks = models.TextField(null=True, default=None)
    canceled_by = models.ForeignKey(accounts_user, related_name='canceled_purchase_return', on_delete=models.CASCADE, null=True, blank=True)
    canceled_on = models.DateTimeField(null=True, blank=True)
    canceled_reason = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(null=True, default=None)
    created_by = models.ForeignKey(User,on_delete=models.PROTECT, related_name='erp_purchase_return_created_by')
    updated_by = models.ForeignKey(User,null=True, on_delete=models.SET_NULL,related_name='erp_purchase_return_updated_by')
    
    class Meta:
        db_table = 'erp_purchase_return'

    def __str__(self):
        return f"Purchase Return {self.id_purchase_return}"
    

class ErpPurchaseReturnDetails(models.Model):
    id_purchase_return_det = models.AutoField(primary_key=True)
    purchase_return = models.ForeignKey(ErpPurchaseReturn, on_delete=models.PROTECT,related_name="purchase_return_details")
    type = models.IntegerField(choices=[(1, "General"),(2, "Tag"), (3, "Non-Tag")], default=1)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="purchase_return_product")
    uom_id = models.ForeignKey(Uom,on_delete=models.CASCADE, related_name="return_stock_uom", null=True, default=None)
    tag_id = models.ForeignKey('inventory.ErpTagging',on_delete=models.CASCADE, related_name="return_tag_id", null=True, default=None,blank=True)
    piece = models.PositiveIntegerField()
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    less_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    flat_mc = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    total_mc = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    mc_type = models.IntegerField(choices=PURCHASE_MC_TYPE_CHOICES, default=1)
    touch = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    pure_wt = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0.0)])
    tax = models.ForeignKey(Taxmaster, on_delete=models.CASCADE,null=True)
    tax_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    igst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)], default=0)
    
    class Meta:
        db_table = 'erp_purchase_return_details'

    def __str__(self):
        return f"Purchase Return Detail {self.id_purchase_return_det}"
    
class ErpPurchaseReturnStoneDetails(models.Model):
    id_purchase_return_stone_det = models.AutoField(primary_key=True)
    purchase_return_detail = models.ForeignKey(ErpPurchaseReturnDetails, on_delete=models.PROTECT)
    show_in_lwt       = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    stone          = models.ForeignKey(Stone, on_delete=models.CASCADE,related_name="purchase_return_stn_stone_id",null=True, default=None)
    quality_code   = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="purchase_return_stn_quality_code", null=True, default=None)
    uom            = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="purchase_return_stn_uom_id",null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    stone_rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_calc_type   = models.IntegerField(choices=TAG_STN_CALC_TYPE_CHOICES,default=1)
    
    class Meta:
        db_table = 'erp_purchase_return__stone_details'

    def __str__(self):
        return f"Purchase Return Stone Detail {self.id_purchase_return_stone_det}"


class ErpPurchaseSupplierOpening(CommonFields):
    id = models.AutoField(primary_key=True)
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="opening_supplier")
    id_metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="supplier_opening_metal", null=True, default=None)
    entry_date = models.DateField()
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="supplier_opening_branch", default=None)
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    class Meta:
        db_table = 'erp_purchase_supplier_opening'

    def __str__(self):
        return f"Purchase Opening {self.id}"
 
class ErpSupplierAdvance(CommonFields):
    TYPE_CHOICES = [
        (1, 'From Supplier Payment'),
        (2, 'From Rate-Cut Metal Issue'),
        (3, 'From Rate-Cut Cash Metal')
    ]
    id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(ErpSupplierRateCutAndMetalIssue, on_delete=models.CASCADE, related_name='supplier_advance_rate_cut_parent', null=True, default=None)
    type = models.IntegerField(choices=TYPE_CHOICES, default=1)
    ref_id = models.IntegerField(null=True, blank=False,default=None)
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_adv_payment")
    id_metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="supplier_adv_metal", null=True, default=None)
    weight = models.DecimalField(max_digits=10, decimal_places=3,default=0.000)
    amount = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    class Meta:
        db_table = 'erp_purchase_supplier_advance'

    def __str__(self):
        return f"Purchase Advance {self.id}"

class ErpSupplierAdvanceAdj(CommonFields):
    ADJ_TYPE_CHOICES = [
        (1, 'Weight'),
        (2, 'Amount')
    ]
    TYPE_CHOICES = [
        (1, 'Supplier Payment'),
        (2, 'Rate-Cut')
    ]
    id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(ErpSupplierRateCutAndMetalIssue, on_delete=models.CASCADE, related_name='rate_cut_metal_issue_parent', null=True, default=None)
    ref_id = models.IntegerField(null=True, blank=False)
    type = models.IntegerField(choices=TYPE_CHOICES, default=1)
    id_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_adj_payment")
    id_metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="supplier_adj_metal", null=True, default=None)
    adj_type = models.IntegerField(choices=ADJ_TYPE_CHOICES, default=1)
    is_adjusted = models.BooleanField(default=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3,default=0.000)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    class Meta:
        db_table = 'erp_purchase_supplier_advance_adj'

    def __str__(self):
        return f"Purchase Advance Adj {self.id}"
    
class ErpCustomerPayment(CommonFields):
    PAYMENT_TYPE_CHOICES = [
        (1,'Against po'),
        (2,'Against metal process'),
    ]
    id = models.AutoField(primary_key=True)
    ref_no = models.CharField(max_length=255,null=True,blank=False,default=None) 
    id_customer = models.ForeignKey(Customers, on_delete=models.CASCADE, related_name="customer_purchase_payment",blank=False,default=None)
    metal = models.ForeignKey(Metal, on_delete=models.CASCADE, related_name="customer_purchase_payment_metal", null=True, default=None)
    entry_date = models.DateField()
    fin_year = models.ForeignKey(FinancialYear,on_delete=models.CASCADE, null=True, default=None)
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="customer_purchase_branch", default=None)
    cash_from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="customer_purchase_cash_from_branch", default=None)
    remarks= models.TextField(null=True, default=None)

    class Meta:
        db_table = 'erp_customer_purchase_payment'
    def __str__(self):
        return f"Customer Payment {self.id}"
class ErpCustomerPaymentDetails(CommonFields):
    PAYMENT_TYPE_CHOICES = [
        (1,'Against Invoice'),
        (2,'Against metal process'),
        (3,'Against Repair Order'),
        (4,'Against Opening'),
        (5,'Advance'),
        (6,'Credit Received from Supplier'),
    ]
    id_payment_details = models.AutoField(primary_key=True)
    customer_payment    = models.ForeignKey(ErpCustomerPayment, on_delete=models.PROTECT, related_name='customer_purchase_payment_details', null=True, default=None)
    ref_id = models.IntegerField(null=True, blank=False,default=None)
    type   = models.IntegerField(choices=PAYMENT_TYPE_CHOICES,default=1)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'erp_customer_purchase_payment_details'
    def __str__(self):
        return f"Customer Payment Details {self.id_payment_details}"

class ErpCustomerPaymentModeDetail(models.Model):
    CARD_TYPE_CHOICES = [
        (0, ''),
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    PAYMENT_TYPE_CHOICES = [
        (1,'Credit'),
        (2,'Debit'),
    ]
    id_payment_mode         = models.AutoField(primary_key=True)
    customer_payment        = models.ForeignKey(ErpCustomerPayment, on_delete=models.PROTECT, related_name='customer_payment_mode_details', null=True)
    id_bank                 = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, blank=True,default=None)
    payment_date            = models.DateTimeField(auto_now_add=True)
    payment_type            = models.IntegerField(choices=PAYMENT_TYPE_CHOICES,default=1)
    payment_mode            = models.ForeignKey('retailmasters.PaymentMode', on_delete=models.PROTECT, null=True)
    payment_amount          = models.DecimalField(max_digits=10, decimal_places=2)
    card_no                 = models.CharField(max_length=15, null=True,blank=True, default=None)
    card_holder             = models.CharField(max_length=75, null=True,blank=True,default=None)
    payment_ref_number      = models.CharField(max_length=25, null=True, blank=True,default=None)
    payment_status          = models.IntegerField(default = 0)
    card_type               = models.IntegerField(choices=CARD_TYPE_CHOICES, null=True, default=0)
    NB_type                 = models.IntegerField(default = 0, null=True,blank=True,) 
    net_banking_date        =  models.DateTimeField(null=True, default=None)
    remark                  = models.CharField(max_length=275, null=True)
    id_pay_device           = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='customer_purchase_pay_device_id', null=True)
       
    class Meta:
        db_table = 'erp_customer_purchase_payment_mode'

    def __str__(self):
        return f"Customer Payment Mode Details {self.id_payment_mode}"
    
