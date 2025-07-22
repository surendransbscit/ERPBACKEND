from django.db import models
from datetime import datetime, date
import uuid
import os
from django.core.exceptions import ValidationError
from retailcataloguemasters.models import Product, Purity,Design,SubDesign,Stone,ProductCalculationType,QualityCode,Category,Section,Metal
from retailmasters.models import Branch , Uom,Taxgroupitems ,FinancialYear , City, State,Country,OtherCharges,Size,Taxmaster,OldMetalItemType
from inventory.models import ErpTagging
from customers.models import Customers
from employees.models import Employee
from managescheme.models import SchemeAccount
from customerorder.models import ERPOrderDetails
from estimations.models import ErpEstimationSalesDetails,ErpEstimationOldMetalDetails
from  utilities.constants import (  SHOW_IN_LWT_CHOICES,TAX_TYPE_CHOICES,STATUS_CHOICES,ITEM_TYPE_CHOICES,MC_TYPE_CHOICES,TAG_STN_CALC_TYPE_CHOICES,CEDIT_CHOICES,CEDIT_STATUS_CHOICES,BILL_TYPE_CHOICES)
from .constants import (INVOICE_FOR_CHOICES,INVOICE_TO_CHOICES,INVOICE_STATUS_CHOICES,INVOICE_TYPE_CHOICES,DELIVERY_LOCATION_CHOICES)
from django.core.validators import MinValueValidator,MaxValueValidator
from  utilities.constants import (TAG_OTHER_METAL_MC_TYPE_CHOICES,PARTIAL_SALE_CHOICES,DELIVERY_STATUS_CHOICES)
from promotionmanagement.models import (GiftVoucherIssue)
# Create your models here.
accounts_user = 'accounts.User'

def upload_item_delivered_image(instance, filename):
    _, file_extension = os.path.splitext(filename)
    unique_id = uuid.uuid4()
    return 'item_delivered_images/item_delivered_{item_delverid}/{pkid}{title}{ext}'.format(item_delverid=instance.erp_item_delivered.id_item_delivered, pkid=unique_id, 
                                                                                    title=datetime.now().strftime('%Y%m%d%H%M%S'), ext=file_extension)


class BankSettlements(models.Model):
    id_settlement = models.AutoField(primary_key=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="bank_settlement_branch",default=None,null=True)
    invoice_date = models.DateField()
    card_payment_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    card_received_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    net_banking_payment_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    net_banking_received_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    upi_payment_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    upi_received_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    created_by = models.ForeignKey(accounts_user, related_name='bill_settlement_created_user', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(accounts_user, related_name='bill_settlement_updated_user', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)
    
    def __str__(self) -> str:
        return 'Bank Settlement - ' + str(self.pk)
    
    class Meta:
        db_table = 'bank_settlements'
    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class ErpInvoice(models.Model):
    erp_invoice_id = models.AutoField(primary_key=True)
    metal = models.ForeignKey(Metal, on_delete=models.CASCADE,default=None,null=True, blank=True)
    fin_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE,related_name="invoice_year")
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="invoice_branch")
    invoice_date = models.DateField(null=False, blank=False)
    invoice_type = models.IntegerField(choices=INVOICE_TYPE_CHOICES, default=1)
    invoice_to = models.IntegerField(choices=INVOICE_TO_CHOICES, default=1)
    invoice_for = models.IntegerField(choices=INVOICE_FOR_CHOICES, default=1)
    delivery_location = models.IntegerField(choices=DELIVERY_LOCATION_CHOICES, default=1)
    id_customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    customer_name = models.TextField(null=False, blank=False)
    customer_mobile = models.TextField(null=False, blank=False)
    gst_number = models.CharField(max_length=255, null=True,default=None)
    pan_number = models.CharField(max_length=255, null=True,default=None)
    sales_invoice_no = models.CharField(max_length=255,default=None,null=True, blank=True)
    purchase_invoice_no = models.CharField(max_length=255, default=None,null=True, blank=True)
    return_invoice_no = models.CharField(max_length=255,default=None, null=True, blank=True)
    invoice_status = models.IntegerField(choices=INVOICE_STATUS_CHOICES, default=1)
    sales_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    total_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    charges_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    canceled_by = models.ForeignKey(accounts_user, related_name='canceled_invoices', on_delete=models.CASCADE, null=True, blank=True)
    canceled_on = models.DateTimeField(null=True, blank=True)
    canceled_reason = models.TextField(blank=True)
    is_credit   = models.IntegerField(choices=CEDIT_CHOICES, default=0)
    is_converted_bill = models.IntegerField(choices=[(0, 'No'),(1, 'Yes')], default=0)
    is_promotional_billing   = models.IntegerField(choices=CEDIT_CHOICES, default=0)
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    credit_status = models.IntegerField(choices=CEDIT_STATUS_CHOICES, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    due_date    =  models.DateField(null=True, blank=False)
    id_employee = models.ForeignKey(Employee, related_name='billed_invoices', on_delete=models.CASCADE,null=True, blank=True, default=None)
    created_by = models.ForeignKey(accounts_user, related_name='created_invoices', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(accounts_user, related_name='updated_invoices', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)
    id_counter = models.ForeignKey('retailmasters.Counter', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name="invoice_counter")

    class Meta:
        db_table = 'erp_invoice'

    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class ErpInvoiceCustomerAddress(models.Model):
    invoice_delivery_id = models.AutoField(primary_key=True)
    invoice_bill_id     = models.ForeignKey(ErpInvoice,on_delete=models.CASCADE,related_name="invoice_prof")
    address1            = models.CharField(max_length=30,blank=False,null=False)
    address2            = models.CharField(max_length=30,blank=True)
    address3            = models.CharField(max_length=30,blank=True)
    id_city             = models.ForeignKey(City,on_delete=models.CASCADE)
    id_state            = models.ForeignKey(State,on_delete=models.CASCADE)
    id_country          = models.ForeignKey(Country,on_delete=models.CASCADE)
    pincode             = models.CharField(max_length=10,blank=False)
    class Meta:
        db_table = 'erp_invoice_delivery'

class ErpInvoiceSalesDetails(models.Model):
    invoice_sale_item_id    = models.AutoField(primary_key=True)
    invoice_bill_id         = models.ForeignKey(ErpInvoice, on_delete=models.CASCADE,related_name="sales_invoice_id")
    item_type               = models.IntegerField(choices=ITEM_TYPE_CHOICES, default=0)
    is_partial_sale         = models.IntegerField(choices=PARTIAL_SALE_CHOICES, default=0)
    id_purity               = models.ForeignKey(Purity, on_delete=models.CASCADE,null=True,blank=True,default=None)
    uom_id                  = models.ForeignKey(Uom, on_delete=models.CASCADE,null=True)
    tag_id                  = models.ForeignKey(ErpTagging, on_delete=models.CASCADE,null=True,related_name="sales_tag_id")
    id_product              = models.ForeignKey(Product, on_delete=models.CASCADE,null=False,blank=False,related_name="sales_product")
    id_design               = models.ForeignKey(Design, on_delete=models.CASCADE,null=True,blank=True,default=None,related_name="sales_design")
    id_sub_design           = models.ForeignKey(SubDesign, on_delete=models.CASCADE,null=True,blank=True,related_name="sales_sub_design",default=None)
    id_section             = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="sales_section", null=True, default=None)
    pieces                  = models.PositiveIntegerField(null=False,blank=False,default=0)
    gross_wt                = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    less_wt                 = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    net_wt                  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    dia_wt                  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    stone_wt                = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    other_metal_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    wastage_percentage      = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    wastage_weight          = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    pure_weight             = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    mc_type                 = models.IntegerField(choices=MC_TYPE_CHOICES, default=1)
    mc_value                = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    flat_mc_value           = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    total_mc_value          = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    other_charges_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    other_metal_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    rate_per_gram           = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    sell_rate               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.0)])
    taxable_amount          = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    tax_group_id            = models.ForeignKey(Taxgroupitems, on_delete=models.CASCADE,null=True)
    tax_id                  = models.ForeignKey(Taxmaster, on_delete=models.CASCADE,null=True)
    tax_type                = models.IntegerField(choices=TAX_TYPE_CHOICES, default=2)
    tax_percentage          = models.DecimalField(max_digits=10,null=True,blank=True,decimal_places=2,default=0.00,validators=[MaxValueValidator(100.0)])
    tax_amount              = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    cgst_cost             = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    sgst_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    igst_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    discount_amount         = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    item_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    wastage_discount        = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    mc_discount_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    status                  = models.IntegerField(choices=STATUS_CHOICES, default=1)
    is_delivered            = models.BooleanField(default=True)
    ref_emp_id              = models.ForeignKey(Employee, on_delete=models.CASCADE,null=True,blank=True,default=None)
    ref_emp_id_1            = models.ForeignKey(Employee,related_name="support_emp_1", on_delete=models.CASCADE,null=True, default=None)
    ref_emp_id_2            = models.ForeignKey(Employee,related_name="support_emp_2", on_delete=models.CASCADE,null=True, default=None)
    size                    = models.ForeignKey(Size,on_delete=models.CASCADE,related_name="sales_size",null=True, default=None)
    order_detail            = models.ForeignKey(ERPOrderDetails,on_delete=models.SET_NULL,related_name="order_detail",null=True, default=None)
    id_tag_transfer         = models.ForeignKey("branchtransfer.ErpTagTransfer",on_delete=models.SET_NULL,related_name="stock_issue_detail",null=True, default=None)
    delivered_by            = models.ForeignKey(accounts_user, related_name='delivered_invoices', on_delete=models.CASCADE, null=True, blank=True)
    delivered_on            = models.DateTimeField(default=None, null=True, blank=True)
    wastage_percentage_after_disc = models.DecimalField(max_digits=10,null=False, blank=False, decimal_places=2,default=0.00, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    purchase_touch          = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    purchase_wastage        = models.DecimalField(max_digits=10,decimal_places = 2 ,null=True, blank=True, default=None,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])


    class Meta:
        db_table = 'erp_invoice_sales_details'

    indexes = [
            models.Index(fields=['invoice_bill_id','tag_id','id_product','id_design','id_sub_design']),
    ]

class ErpInvoiceOldMetalDetails(models.Model):
    STATUS_CHOICES = [(2, 'Intransit'),(1, 'Added To Old Metal Process'),(0, 'ON PURCHASED')]

    invoice_old_metal_item_id = models.AutoField(primary_key=True)
    invoice_bill_id           = models.ForeignKey(ErpInvoice,on_delete=models.CASCADE,related_name="purchase_invoice_id")
    id_product                = models.ForeignKey(Product, on_delete=models.CASCADE,null=False,blank=False,related_name="old_metal_product_id")
    touch                     = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    pieces                    = models.PositiveIntegerField(null=False,blank=False,default=0)
    gross_wt                  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    less_wt                   = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    net_wt                    = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    dia_wt                    = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    stone_wt                  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    dust_wt                   = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    wastage_percentage        = models.IntegerField(null=True, blank=True,default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight            = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    pure_weight               = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    rate_per_gram             = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    customer_rate             = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    amount                    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    item_type                 = models.ForeignKey(OldMetalItemType, on_delete=models.CASCADE, null=True,default=None)
    purchase_status           = models.IntegerField(choices=STATUS_CHOICES, default=1)
    current_branch            = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="old_metal_branch",null=True,default=None)
    order                     = models.ForeignKey('customerorder.ERPOrder', on_delete=models.PROTECT, null=True, default=None)

    class Meta:
        db_table = 'erp_invoice_old_metal_details'

    indexes = [
            models.Index(fields=['invoice_bill_id','id_product']),
    ]

class ErpInvoiceStoneDetails(models.Model):

    id_inv_stn_detail = models.AutoField(primary_key=True)
    invoice_sale_item_id = models.ForeignKey(ErpInvoiceSalesDetails,on_delete=models.CASCADE, blank=True,null=True,related_name="sale_item_id")
    invoice_old_metal_item_id = models.ForeignKey(ErpInvoiceOldMetalDetails,on_delete=models.CASCADE, blank=True,null=True,related_name="old_metal_item_id")
    show_in_lwt       = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone          = models.ForeignKey(Stone, on_delete=models.CASCADE,related_name="sale_stone_id",null=False, blank=False)
    uom_id            = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="sale_uom_id",null=False, blank=False)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="inv_id_quality_code", null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    stone_rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_calc_type   = models.IntegerField(choices=TAG_STN_CALC_TYPE_CHOICES,default=1)
    class Meta:
        db_table = 'erp_invoice_stone_details'
    
    indexes = [
            models.Index(fields=['id_stone','invoice_sale_item_id','invoice_old_metal_item_id','uom_id']),
    ]

class ErpInvoiceItemCharges(models.Model):

    invoice_charges_sale_item_id = models.AutoField(primary_key=True)
    invoice_sale_item_id         = models.ForeignKey(ErpInvoiceSalesDetails,on_delete=models.CASCADE,null=False,blank=False)
    id_charges                   = models.ForeignKey(OtherCharges,on_delete=models.CASCADE,null=False,blank=False)
    charges_amount               = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_invoice_charges_details'


class ErpInvoiceSalesReturn(models.Model):

    invoice_return_id     = models.AutoField(primary_key=True)
    invoice_bill_id       = models.ForeignKey(ErpInvoice,on_delete=models.CASCADE,null=False,blank=False)
    invoice_sale_item_id  = models.ForeignKey(ErpInvoiceSalesDetails,on_delete=models.CASCADE,null=True,blank=True,related_name="return_sales_item_id",default=None)
    id_purity = models.ForeignKey(Purity, on_delete=models.CASCADE, null=True, blank=True,default=None)
    uom_id = models.ForeignKey(Uom, on_delete=models.CASCADE, null=True,default=None)
    tag_id = models.ForeignKey(ErpTagging, on_delete=models.CASCADE, null=True, default=None,related_name="sales_ret_tag_id")
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name="sales_ret_product",default=None)
    id_design = models.ForeignKey(Design, on_delete=models.CASCADE, null=True, blank=True, related_name="sales_ret_design")
    id_sub_design = models.ForeignKey(SubDesign, on_delete=models.CASCADE, null=True,default=None, blank=False, related_name="sales_ret_sub_design")
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
    
    class Meta:
        db_table = 'erp_invoice_sales_return_details'


class ErpInvoiceSchemeAdjusted(models.Model):
    invoice_scheme_adj_id = models.AutoField(primary_key=True)
    invoice_bill_id       = models.ForeignKey(ErpInvoice,on_delete=models.CASCADE,null=True,blank=False, default=None,related_name="chit_adjust")
    issue_receipt       = models.ForeignKey('billing.ErpIssueReceipt',on_delete=models.CASCADE,null=True,blank=False, default=None)
    id_scheme_account     = models.ForeignKey(SchemeAccount,on_delete=models.CASCADE,null=True,blank=True,default=None,related_name="scheme_adjust_id")
    scheme_acc_number      = models.TextField(null=True, blank=True,default = None)
    closing_weight        = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage               = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc             = models.DecimalField(max_digits=10,decimal_places=2,default=0.00, validators=[MinValueValidator(0.0)])
    closing_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0.00, validators=[MinValueValidator(0.0)])
    rate_per_gram = models.DecimalField(max_digits=10,decimal_places=2,default=0.00, validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_invoice_scheme_adjusted_details'


class ErpInvoicePaymentModeDetail(models.Model):
    CARD_TYPE_CHOICES = [
        (0, ''),
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    PAYMENT_TYPE_CHOICES = [
        (1,'Credit'),
        (2,'Debit'),
    ]
    invoice_pay_id     = models.AutoField(primary_key=True)
    invoice_bill_id    = models.ForeignKey(ErpInvoice, on_delete=models.PROTECT, related_name='invoice_pay_id', null=True)
    id_bank                 = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, blank=True,default=None)
    payment_date            = models.DateTimeField(auto_now_add=datetime.now())
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
    remark                  = models.CharField(max_length=275, null=True,default=None)
    id_pay_device           = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='invoice_pay_device_id', null=True,default=None)
       
    class Meta:
        db_table = 'erp_invoice_payment_details'


class ErpInvoiceOtherMetal(models.Model):
    
    id_inv_other_metal  = models.AutoField(primary_key=True)
    invoice_sale_item_id= models.ForeignKey(ErpInvoiceSalesDetails,on_delete=models.CASCADE, related_name="erp_other_metal_inv_id", null=True, default=None)
    id_category         = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="erp_inv_other_metal_cat_id", null=True, default=None)
    id_purity           = models.ForeignKey(Purity,on_delete=models.CASCADE,related_name="erp_inv_other_metal_purity_id", null=True, default=None)
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_type             = models.IntegerField(choices=TAG_OTHER_METAL_MC_TYPE_CHOICES,default=1)
    mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    rate_per_gram       = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    other_metal_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_invoice_other_metal'
        
class ErpItemDelivered(models.Model):
    id_item_delivered = models.AutoField(primary_key=True)
    bill = models.ForeignKey(ErpInvoice, on_delete=models.PROTECT)
    entry_date = models.DateField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="item_delivered_branch")
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE, related_name="item_delivered_customer")
    product = models.ForeignKey(Product, on_delete=models.CASCADE,null=False,blank=False,related_name="item_delivered_product")
    piece = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    is_delivered = models.IntegerField(choices=[(1, 'Yes'),(2, 'No')],default=2)
    remarks = models.TextField(null=True)
    delivered_on = models.DateTimeField(null=True, default=None)
    delivered_by = models.ForeignKey(accounts_user, related_name='item_delivered_by_user', on_delete=models.PROTECT, null=True, default=None)
    
    def __str__(self) -> str:
        return 'ERP Item Delivered - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_item_delivered'
        
    LOGGING_IGNORE_FIELDS = ('delivered_on', 'delivered_by')
    
class ErpItemDeliveredImages(models.Model):
    id = models.AutoField(primary_key=True)
    erp_item_delivered = models.ForeignKey(ErpItemDelivered, on_delete=models.PROTECT)
    name = models.CharField(max_length=255, null=True, default=None)
    item_delivered_image = models.ImageField(upload_to=upload_item_delivered_image)
    
    def __str__(self):
        return f"{self.id} - Image for Tag {self.erp_item_delivered}"

    class Meta:
        db_table = 'erp_item_delivered_images'
        
class ErpIssueReceipt(models.Model):
    
    TYPE_CHOICES = [(1, 'Issue'),(2, 'Receipt')]
    BILL_STATUS_CHOICES = [(1, 'Success'),(2, 'Cancelled')]
    STORE_AS_CHOICES = [(1, 'Amount'),(2, 'Weight')]
    ISSUE_TYPE_CHOICES = [(1, 'Credit'),(2, 'Refund'), (3, 'Petty Cash'), (4, 'Import'),(5,'Bank Deposit')]
    ISSUE_TO_CHOICES = [(1, 'Customer'),(2, 'Employee'),(3, 'Others')]
    RECEIPT_TYPE_CHOICES = [(1, 'General'),(2, 'Against Order'), (3, 'Advance Deposit'), (4, 'Import'),
                            (5, 'Credit Collection'),(6, 'Repair Order Delivery'),(7, 'Daily Cash Opening Balance'),
                            (8, 'Chit Deposit'),(9, 'Others')]

    
    id = models.BigAutoField(primary_key=True)
    type = models.IntegerField(choices=TYPE_CHOICES,default=2)
    issue_type = models.IntegerField(choices=ISSUE_TYPE_CHOICES,default=1, null=True)
    issue_to = models.IntegerField(choices=ISSUE_TO_CHOICES,default=1, null=True,)
    receipt_type = models.IntegerField(choices=RECEIPT_TYPE_CHOICES,default=1, null=True)
    fin_year = models.ForeignKey('retailmasters.FinancialYear',on_delete=models.PROTECT, null=True, default=None)
    branch = models.ForeignKey('retailmasters.Branch', on_delete=models.PROTECT, related_name='issue_receipt_branch_id')
    id_bank = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, related_name='bank_deposit_id',default=None,null=True)
    account_head = models.ForeignKey('retailmasters.AccountHead', on_delete=models.PROTECT, related_name='issue_receipt_account_head',null=True, default=None)
    customer = models.ForeignKey('customers.Customers', on_delete=models.PROTECT, related_name='issue_receipt_customer_id', null=True, default=None)
    bill_no = models.CharField(max_length=255)
    bill_date = models.DateField()
    order = models.ForeignKey('customerorder.ERPOrder', on_delete=models.PROTECT, null=True, default=None)
    deposit_bill = models.ForeignKey(ErpInvoice, on_delete=models.SET_NULL, null=True, default=None,related_name="deposit_bill")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=False, blank=False)
    store_as = models.IntegerField(choices=STORE_AS_CHOICES,default=2)
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, validators=[MinValueValidator(0.0)])
    scheme = models.ForeignKey('schememaster.Scheme', on_delete=models.PROTECT, related_name='issue_reciept_scheme_id', null=True, default=None)
    chit_weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=False, default=None)
    created_on = models.DateTimeField(auto_now_add=datetime.now())
    created_by = models.ForeignKey(accounts_user, related_name='issue_receipt_created_by_user', on_delete=models.PROTECT)
    updated_by = models.ForeignKey(accounts_user,related_name='issue_receipt_updated_by_user', null=True, on_delete=models.SET_NULL)
    updated_on = models.DateTimeField(null=True)
    cancel_reason = models.TextField(null=True, default=None)
    cancelled_by = models.ForeignKey(accounts_user,related_name='issue_receipt_cancelled_by_user', null=True, default=None, on_delete=models.PROTECT)
    cancelled_date = models.DateField(null=True, default=None)
    employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, null=True, default=None)
    bill_status = models.IntegerField(choices=BILL_STATUS_CHOICES,default=1)
    ref_id = models.IntegerField(null=True,default=None)
    remarks = models.TextField(null=True, default=None)
    setting_bill_type   = models.IntegerField(choices=BILL_TYPE_CHOICES, default=1)
    id_counter = models.ForeignKey('retailmasters.Counter', on_delete=models.CASCADE, null=True, blank=True, default=None, related_name="issue_counter")

    
    def __str__(self) -> str:
        return 'ERP Issue Receipt - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_issue_receipt'

        
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class ErpIssueReceiptPaymentDetails(models.Model):
    
    PAY_TYPE_CHOICES = [(1, 'Credit'),(2, 'Debit')]
    CARD_TYPE_CHOICES = [
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    issue_receipt = models.ForeignKey(ErpIssueReceipt, on_delete=models.PROTECT)
    type = models.IntegerField(choices=PAY_TYPE_CHOICES,default=1)
    payment_mode = models.ForeignKey('retailmasters.PaymentMode', on_delete=models.PROTECT)
    pay_device = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='issue_receipt_pay_det_device_id', null=True, default=None)
    nb_type = models.IntegerField(default = 1, null=True)
    bank = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, default=None)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    card_no = models.CharField(max_length=15, null=True, default=None)
    card_holder = models.CharField(max_length=75, null=True, default=None)
    card_type = models.IntegerField(choices=CARD_TYPE_CHOICES, null=True, default=None)
    cheque_no = models.CharField(max_length=255, null=True, default=None)
    ref_no = models.CharField(max_length=255, null=True, default=None)
    
    def __str__(self) -> str:
        return 'ERP Issue Receipt Payment Details - ' + str(self.pk)

    
    class Meta:
        db_table = 'erp_issue_receipt_payment_details'
        
class ErpReceiptCreditCollection(models.Model):
    id = models.AutoField(primary_key=True)
    receipt = models.ForeignKey(ErpIssueReceipt, on_delete=models.PROTECT, related_name="collection_receipt_id", null=True)
    issue = models.ForeignKey(ErpIssueReceipt, on_delete=models.PROTECT, related_name="collection_issue_id",default=None, null=True)
    invoice_bill_id = models.ForeignKey(ErpInvoice,on_delete=models.SET_NULL,related_name="issued_invoice_id",default=None, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    
    def __str__(self) -> str:
        return 'ERP Receipt Credit Collection - ' + str(self.pk)

    class Meta:
        db_table = 'erp_receipt_credit_collection'

class ErpReceiptRefund(models.Model):
    id_refund = models.AutoField(primary_key=True)
    receipt = models.ForeignKey(ErpIssueReceipt, on_delete=models.PROTECT, related_name="refund_receipt", null=True)
    issue = models.ForeignKey(ErpIssueReceipt, on_delete=models.PROTECT, related_name="refund_issue",default=None, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    
    def __str__(self) -> str:
        return 'ERP Receipt Refund - ' + str(self.pk)

    class Meta:
        db_table = 'erp_receipt_refund'

class ErpReceiptAdvanceAdj(models.Model):
    id_advance_adj = models.AutoField(primary_key=True)
    receipt = models.ForeignKey(ErpIssueReceipt, on_delete=models.SET_NULL, related_name="advance_receipt", null=True)
    invoice_bill_id = models.ForeignKey(ErpInvoice,on_delete=models.SET_NULL,related_name="advance_adj_invoices",default=None, null=True)
    id_customer = models.ForeignKey(Customers, on_delete=models.CASCADE,null=True,default=None)
    is_adjusted = models.BooleanField(default=True)
    adj_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    
    def __str__(self) -> str:
        return 'ERP Advance Adjused - ' + str(self.pk)

    class Meta:
        db_table = 'erp_advance_adj'

class ErpInvoiceDiscount(models.Model):
    erp_invoice_id = models.AutoField(primary_key=True)
    fin_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE,related_name="dis_inv_year")
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="dis_inv_branch")
    invoice_date = models.DateField(null=False, blank=False)
    invoice_type = models.IntegerField(choices=INVOICE_TYPE_CHOICES, default=1)
    invoice_to = models.IntegerField(choices=INVOICE_TO_CHOICES, default=1)
    invoice_for = models.IntegerField(choices=INVOICE_FOR_CHOICES, default=1)
    delivery_location = models.IntegerField(choices=DELIVERY_LOCATION_CHOICES, default=1)
    id_customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    customer_name = models.TextField(null=False, blank=False)
    customer_mobile = models.TextField(null=False, blank=False)
    gst_number = models.CharField(max_length=255, null=True,default=None)
    pan_number = models.CharField(max_length=255, null=True,default=None)
    sales_invoice_no = models.CharField(max_length=255,default=None,null=True, blank=True)
    purchase_invoice_no = models.CharField(max_length=255, default=None,null=True, blank=True)
    return_invoice_no = models.CharField(max_length=255,default=None, null=True, blank=True)
    invoice_status = models.IntegerField(choices=INVOICE_STATUS_CHOICES, default=1)
    sales_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    total_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    canceled_by = models.ForeignKey(accounts_user, related_name='canceled_inv', on_delete=models.CASCADE, null=True, blank=True)
    canceled_on = models.DateTimeField(null=True, blank=True)
    canceled_reason = models.TextField(blank=True)
    is_credit   = models.IntegerField(choices=CEDIT_CHOICES, default=0)
    is_promotional_billing   = models.IntegerField(choices=CEDIT_CHOICES, default=0)
    credit_status = models.IntegerField(choices=CEDIT_STATUS_CHOICES, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,null=False, blank=False)
    due_date    =  models.DateField(null=True, blank=False)
    id_employee = models.ForeignKey(accounts_user, related_name='billed_inv', on_delete=models.CASCADE)
    created_by = models.ForeignKey(accounts_user, related_name='created_inv', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(accounts_user, related_name='updated_inv', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    class Meta:
        db_table = 'erp_invoice_discount'
    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')

class ErpInvoiceDiscountSalesDetails(models.Model):
    invoice_sale_item_id    = models.AutoField(primary_key=True)
    invoice_bill_id            = models.ForeignKey(ErpInvoiceDiscount, on_delete=models.CASCADE,related_name="sales_invoice")
    item_type               = models.IntegerField(choices=ITEM_TYPE_CHOICES, default=0)
    is_partial_sale         = models.IntegerField(choices=PARTIAL_SALE_CHOICES, default=0)
    id_purity               = models.ForeignKey(Purity, on_delete=models.CASCADE,null=False,blank=False)
    uom_id                  = models.ForeignKey(Uom, on_delete=models.CASCADE,null=True)
    tag_id                  = models.ForeignKey(ErpTagging, on_delete=models.CASCADE,null=True,related_name="sales_tag")
    id_product              = models.ForeignKey(Product, on_delete=models.CASCADE,null=False,blank=False,related_name="sales_dis_product")
    id_design               = models.ForeignKey(Design, on_delete=models.CASCADE,null=False,blank=False,related_name="sales_dis_design")
    id_sub_design           = models.ForeignKey(SubDesign, on_delete=models.CASCADE,null=True,blank=True,related_name="sales_dis_sub_design",default=None)
    pieces                  = models.PositiveIntegerField(null=False,blank=False,default=0)
    gross_wt                = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    less_wt                 = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    net_wt                  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    dia_wt                  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    stone_wt                = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    other_metal_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    calculation_type        = models.ForeignKey(ProductCalculationType, on_delete=models.CASCADE,null=True,blank=True,default=None)
    wastage_percentage      = models.IntegerField(null=True, blank=True, default=None,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight          = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    mc_type                 = models.IntegerField(choices=MC_TYPE_CHOICES, default=1)
    mc_value                = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    total_mc_value          = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    other_charges_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    other_metal_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    rate_per_gram           = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    taxable_amount          = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    tax_group_id            = models.ForeignKey(Taxgroupitems, on_delete=models.CASCADE,null=True)
    tax_id                  = models.ForeignKey(Taxmaster, on_delete=models.CASCADE,null=True)
    tax_type                = models.IntegerField(choices=TAX_TYPE_CHOICES, default=2)
    tax_percentage          = models.DecimalField(max_digits=10,null=True,blank=True,decimal_places=2,default=0.00,validators=[MaxValueValidator(100.0)])
    tax_amount              = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    cgst_cost             = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    sgst_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    igst_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    discount_amount         = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    item_cost               = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    wastage_discount        = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    mc_discount_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    status                  = models.IntegerField(choices=STATUS_CHOICES, default=1)
    is_delivered            = models.BooleanField(default=True)
    ref_emp_id              = models.ForeignKey(Employee, on_delete=models.CASCADE)
    size                    = models.ForeignKey(Size,on_delete=models.CASCADE,related_name="sales_dis_size",null=True, default=None)
    order_detail            = models.ForeignKey(ERPOrderDetails,on_delete=models.CASCADE,related_name="sales_dis_order_detail",null=True, default=None)
    delivered_by            = models.ForeignKey(accounts_user, related_name='sales_dis_delivered_by', on_delete=models.CASCADE, null=True, blank=True)
    delivered_on            = models.DateTimeField(default=None, null=True, blank=True)
    wastage_percentage_after_disc = models.DecimalField(max_digits=10,null=False, blank=False, decimal_places=2,default=0.00, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])

    class Meta:
        db_table = 'erp_invoice_discount_sales_details'

    indexes = [
            models.Index(fields=['invoice_bill_id','tag_id','id_product','id_design','id_sub_design']),
    ]

class ErpInvoiceDiscountOldMetalDetails(models.Model):
    invoice_old_metal_item_id = models.AutoField(primary_key=True)
    invoice_bill_id              = models.ForeignKey(ErpInvoiceDiscount,on_delete=models.CASCADE,related_name="purchase_dis_invoice")
    id_product                = models.ForeignKey(Product, on_delete=models.CASCADE,null=False,blank=False,related_name="old_metal_dis_product")
    touch                     = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    pieces                    = models.PositiveIntegerField(null=False,blank=False,default=0)
    gross_wt                  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    less_wt                   = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    net_wt                    = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    dia_wt                    = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    stone_wt                  = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    dust_wt                   = models.DecimalField(max_digits=10, decimal_places=3, default=0.000, validators=[MinValueValidator(0.0)])
    wastage_percentage        = models.IntegerField(null=True, blank=True,default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight            = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    pure_weight               = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    rate_per_gram             = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    customer_rate             = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    amount                    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    est_old_metal_item_id     = models.ForeignKey(ErpEstimationOldMetalDetails, on_delete=models.CASCADE, null=True)
    
    class Meta:
        db_table = 'erp_invoice_discount_old_metal_details'

    indexes = [
            models.Index(fields=['invoice_bill_id','id_product']),
    ]

class ErpInvoiceDiscountStoneDetails(models.Model):

    id_inv_stn_detail = models.AutoField(primary_key=True)
    invoice_sale_item_id = models.ForeignKey(ErpInvoiceDiscountSalesDetails,on_delete=models.CASCADE, blank=True,null=True,related_name="sale_id")
    invoice_old_metal_item_id = models.ForeignKey(ErpInvoiceDiscountOldMetalDetails,on_delete=models.CASCADE, blank=True,null=True,related_name="old_metal_id")
    show_in_lwt       = models.IntegerField(choices=SHOW_IN_LWT_CHOICES, default=1)
    id_stone          = models.ForeignKey(Stone, on_delete=models.CASCADE,related_name="sale_dis_stone_id",null=False, blank=False)
    uom_id            = models.ForeignKey(Uom, on_delete=models.CASCADE,related_name="sale_dis_uom_id",null=False, blank=False)
    id_quality_code = models.ForeignKey(QualityCode, on_delete=models.CASCADE, related_name="sale_dis_quality_code", null=True, default=None)
    stone_pcs         = models.PositiveIntegerField(null=False, blank=False)
    stone_wt          = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    stone_rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    stone_calc_type   = models.IntegerField(choices=TAG_STN_CALC_TYPE_CHOICES,default=1)
    class Meta:
        db_table = 'erp_invoice_discount_stone_details'
    
    indexes = [
            models.Index(fields=['id_stone','invoice_sale_item_id','invoice_old_metal_item_id','uom_id']),
    ]

class ErpInvoiceDiscountItemCharges(models.Model):

    invoice_charges_sale_item_id = models.AutoField(primary_key=True)
    invoice_sale_item_id         = models.ForeignKey(ErpInvoiceDiscountSalesDetails,on_delete=models.CASCADE,null=False,blank=False)
    id_charges                   = models.ForeignKey(OtherCharges,on_delete=models.CASCADE,null=False,blank=False)
    charges_amount               = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_invoice_discount_charges_details'

class ErpInvoiceDiscountPaymentModeDetail(models.Model):
    CARD_TYPE_CHOICES = [
        (0, ''),
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    PAYMENT_TYPE_CHOICES = [
        (1,'Credit'),
        (2,'Debit'),
    ]
    invoice_pay_id     = models.AutoField(primary_key=True)
    invoice_bill_id    = models.ForeignKey(ErpInvoiceDiscount, on_delete=models.PROTECT, related_name='invoice_dis_pay_id', null=True)
    id_bank                 = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, blank=True,default=None)
    payment_date            = models.DateTimeField(auto_now_add=datetime.now())
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
    id_pay_device           = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='invoice_pay_dis_device_id', null=True)
       
    class Meta:
        db_table = 'erp_invoice_discount_payment_details'


class ErpInvoiceDiscountOtherMetal(models.Model):
    
    id_inv_other_metal  = models.AutoField(primary_key=True)
    invoice_sale_item_id= models.ForeignKey(ErpInvoiceDiscountSalesDetails,on_delete=models.CASCADE, related_name="metal_inv_id", null=True, default=None)
    id_category         = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="metal_cat_id", null=True, default=None)
    id_purity           = models.ForeignKey(Purity,on_delete=models.CASCADE,related_name="metal_purity_id", null=True, default=None)
    piece               = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    weight              = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    wastage_percentage  = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0),MaxValueValidator(100.0)])
    wastage_weight      = models.DecimalField(max_digits=10, decimal_places=3, default=0,validators=[MinValueValidator(0.0)])
    mc_type             = models.IntegerField(choices=TAG_OTHER_METAL_MC_TYPE_CHOICES,default=1)
    mc_value            = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    rate_per_gram       = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])
    other_metal_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_invoice_discount_other_metal'
        
class ErpAdvanceAdj(models.Model):
    id_advance_adj = models.AutoField(primary_key=True)
    receipt = models.ForeignKey(ErpIssueReceipt, on_delete=models.PROTECT, related_name="advance_recpt", null=True)
    invoice_bill_id = models.ForeignKey(ErpInvoiceDiscount,on_delete=models.PROTECT,related_name="advance_adj_inv",default=None, null=True)
    adj_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    
    def __str__(self) -> str:
        return 'ERP AdvAdj - ' + str(self.pk)
    
    class Meta:
        db_table = 'erp_invoice_discount_advance_adj'


class ErpCustomerSalesLog(models.Model):
    id = models.AutoField(primary_key=True)
    fin_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE,related_name="customer_sales_log_year")
    id_branch = models.ForeignKey(Branch, on_delete=models.CASCADE,related_name="customer_sales_log_branch")
    invoice_date = models.DateField(null=False, blank=False)
    id_customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    customer_name = models.TextField(null=False, blank=False)
    customer_mobile = models.TextField(null=False, blank=False)
    ref_id = models.IntegerField(null=True,default=None) 
    invoice_sale_item = models.ForeignKey(ErpInvoiceSalesDetails, on_delete=models.SET_NULL,null=True)
    pieces  = models.PositiveIntegerField(null=False, blank=False,validators=[MinValueValidator(0.0)],default=0)
    gross_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    net_wt = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,validators=[MinValueValidator(0.0)])
    tax_id = models.ForeignKey(Taxmaster, on_delete=models.CASCADE,null=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    item_cost  = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    remark = models.CharField(max_length=275, null=True)
    id_employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)
    id_section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, default=None)
    id_product = models.ForeignKey(Product, on_delete=models.CASCADE,null=True,default=None)
    incentive_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    created_by = models.ForeignKey(accounts_user, related_name='created_cus_sale_log', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(accounts_user, related_name='updated_cus_sale_log', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    class Meta:
        db_table = 'erp_customer_sales_log'
    
    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    
    
class ErpInvoiceGiftDetails(models.Model):
    invoice_gift_id = models.AutoField(primary_key=True)
    issue_id = models.ForeignKey(GiftVoucherIssue,on_delete=models.CASCADE,null=True,blank=False, default=None,related_name="gift_details")
    invoice_bill_id       = models.ForeignKey(ErpInvoice,on_delete=models.CASCADE,null=True,blank=False, default=None,related_name="invoice_gift_details")
    amount          = models.DecimalField(max_digits=10,decimal_places=2,default=0.00, validators=[MinValueValidator(0.0)])

    class Meta:
        db_table = 'erp_invoice_gift_adjusted_details'
        
        
class ErpLiablityEntry(models.Model):
    id = models.AutoField(primary_key=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT,related_name="erp_liablity_branch")
    supplier = models.ForeignKey('retailmasters.Supplier', on_delete=models.PROTECT,related_name="erp_liablity_supplier")
    fin_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE,related_name="erp_liablity_fin_year")
    bill_no = models.CharField(max_length=255)
    ref_bill_no = models.CharField(max_length=255, null=True, default=None)
    entry_date = models.DateField()
    due_date = models.DateField(null=True, default=None)
    remarks = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['bill_no', 'branch', 'fin_year']
        db_table = 'erp_liablity_entry'

    def save(self, *args, **kwargs):
        if self.supplier and not self.supplier.is_vendor==6:
            raise ValidationError(
                "Supplier must be an local vendor (is_vendor=6).")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Liablity entry - {self.id}"
    

class ErpLiablityEntryPament(models.Model):
    id = models.AutoField(primary_key=True)
    payment_date = models.DateField()
    fin_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE,related_name="erp_liablity_payment_fin_year", null=True, default=None)
    # branch = models.ForeignKey(Branch, on_delete=models.PROTECT,related_name="erp_liablity_payment_branch", null=True, default=None)
    supplier = models.ForeignKey('retailmasters.Supplier', on_delete=models.PROTECT,related_name="erp_liablity_payment_supplier", null=True, default=None)
    payment_amount      = models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0.01)])
    receipt_no          = models.CharField(max_length=75, null=True, default=None)
    remarks = models.TextField(null=True, default=None)
    
    def __str__(self) -> str:
        return 'ERP Liablity Payment - ' + str(self.pk)

    class Meta:
        db_table = 'erp_liablity_entry_payment'
        

class ErpLiablityPaymentEntryDetails(models.Model):
    id = models.AutoField(primary_key=True)
    liablity_entry_payment = models.ForeignKey(ErpLiablityEntryPament, related_name='liablity_payment_id', on_delete=models.PROTECT)
    liablity_entry = models.ForeignKey(ErpLiablityEntry, related_name='liablity_entry_id',on_delete=models.PROTECT)
    payment_date = models.DateField(auto_now_add=date.today())
    remarks = models.TextField(null=True, default=None)
    payment_amount      = models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0.01)])
    
    def __str__(self) -> str:
        return 'ERP Liablity Payment Details - ' + str(self.pk)

    class Meta:
        db_table = 'erp_liablity_payment_details'
    
    

class ErpLiablityPaymentModeDetails(models.Model):
    
    PAY_TYPE_CHOICES = [(1, 'Credit'),(2, 'Debit')]
    CARD_TYPE_CHOICES = [
        (1, 'Credit Card'),
        (2, 'Debit Card'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    liablity_payment = models.ForeignKey(ErpLiablityEntryPament, on_delete=models.PROTECT)
    type = models.IntegerField(choices=PAY_TYPE_CHOICES,default=1)
    payment_mode = models.ForeignKey('retailmasters.PaymentMode', on_delete=models.PROTECT)
    pay_device = models.ForeignKey('retailmasters.PayDevice', on_delete=models.PROTECT, related_name='liablity_entry_pay_det_device_id', null=True, default=None)
    nb_type = models.IntegerField(default = 1, null=True)
    bank = models.ForeignKey('retailmasters.Bank', on_delete=models.PROTECT, null=True, default=None)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    card_no = models.CharField(max_length=15, null=True, default=None)
    card_holder = models.CharField(max_length=75, null=True, default=None)
    card_type = models.IntegerField(choices=CARD_TYPE_CHOICES, null=True, default=None)
    cheque_no = models.CharField(max_length=255, null=True, default=None)
    ref_no = models.CharField(max_length=255, null=True, default=None)
    
    def __str__(self) -> str:
        return 'ERP Liablity Payment Mode Detail - ' + str(self.pk)

    class Meta:
        db_table = 'erp_liablity_payment_mode_details'