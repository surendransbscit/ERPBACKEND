from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from utilities.constants import BILL_TYPE_CHOICES
from retailmasters.models import (Supplier, FinancialYear, Branch)
from employees.models import (Employee)
from customers.models import (Customers)
from managescheme.models import (SchemeAccount)

from datetime import datetime
from retailcataloguemasters.models import (
    Product,
)


accounts_user = 'accounts.User'


class OtherInventoryCategory(models.Model):

    CATEGORY_TYPE_CHOICES = [
        (1, 'Chit Gift'),
        (2, 'Packing Items'),
        (3, 'Retail Sales Gift'),
        (4, 'Others'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    short_code = models.CharField(max_length=15, unique=True,
                                  error_messages={'unique': "Category Short Code Already exists"})
    cat_type = models.IntegerField(choices=CATEGORY_TYPE_CHOICES)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_other_inventory_category', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_other_inventory_category', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Other Inventory Category - ' + str(self.pk)

    class Meta:
        db_table = 'other_inventory_category'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class OtherInventorySize(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=20)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_other_inventory_size', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_other_inventory_size', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Other Inventory Size - ' + str(self.pk)

    class Meta:
        db_table = 'other_inventory_size'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class OtherInventoryItem(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(
        OtherInventoryCategory, on_delete=models.PROTECT)
    size = models.ManyToManyField(OtherInventorySize)
    name = models.CharField(max_length=255)
    short_code = models.CharField(max_length=15, unique=True,
                                  error_messages={'unique': "Item Short Code Already exists"})
    created_by = models.ForeignKey(
        accounts_user, related_name='created_other_inventory_item', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_other_inventory_item', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Other Inventory Item - ' + str(self.pk)

    class Meta:
        db_table = 'other_inventory_items'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class OtherInventoryPurchaseEntry(models.Model):

    BILL_STATUS_CHOICES = [(1, 'Success'), (2, 'Cancelled')]

    id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="other_inventory_purchase_supplier")
    fin_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="other_inventory_purchase_branch")
    entry_date = models.DateField()
    ref_no = models.CharField(
        max_length=255, null=True, blank=False, default=None)
    bill_status = models.IntegerField(choices=BILL_STATUS_CHOICES, default=1)
    setting_bill_type = models.IntegerField(
        choices=BILL_TYPE_CHOICES, default=1)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_other_inventory_purchase', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)
    cancelled_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE,
                                     related_name='other_inventory_purchase_cancelled_by', null=True, blank=True)
    cancelled_on = models.DateTimeField(null=True, blank=False, default=None)
    cancelled_reason = models.TextField(blank=True)

    def __str__(self) -> str:
        return 'Other Inventory Purchase - ' + str(self.pk)

    class Meta:
        db_table = 'other_inventory_purchase_entry'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class OtherInventoryPurchaseEntryDetails(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_entry = models.ForeignKey(
        OtherInventoryPurchaseEntry, on_delete=models.PROTECT, related_name='other_inventory_purchase_details')
    item = models.ForeignKey(OtherInventoryItem, on_delete=models.PROTECT)
    size = models.ForeignKey(
        OtherInventorySize, on_delete=models.PROTECT, null=True, default=None)
    pieces = models.PositiveIntegerField()
    rate_per_item = models.DecimalField(max_digits=10, decimal_places=2, validators=[
                                        MinValueValidator(0.0)], default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[
                                       MinValueValidator(0.0)], default=0)

    def __str__(self) -> str:
        return 'Other Inventory Purchase Detail - ' + str(self.pk)

    class Meta:
        db_table = 'other_inventory_purchase_entry_details'


class OtherInventoryItemIssue(models.Model):

    ISSUE_TO_CHOICES = [(1, 'Customer'), (2, 'Employee'), (3, 'Others')]
    ISSUE_FOR_CHOICES = [(1, 'Against Bill'), (2, 'Against Chit')]
    ISSUE_STATUS = [(1, 'Success'), (2, 'Cancelled')]

    id = models.AutoField(primary_key=True)
    issue_to = models.IntegerField(choices=ISSUE_TO_CHOICES)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="other_inventory_issue_branch")
    item = models.ForeignKey(
        OtherInventoryItem, on_delete=models.PROTECT, null=True, default=None)
    pieces = models.PositiveIntegerField(null=True, default=None)
    issue_to_emp = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                     related_name="other_inventory_issue_emp", null=True, default=None)
    issue_to_cus = models.ForeignKey(Customers, on_delete=models.CASCADE,
                                     related_name="other_inventory_issue_cus", null=True, default=None)
    issued_for = models.IntegerField(choices=ISSUE_FOR_CHOICES)
    issue_no = models.CharField(
        max_length=255, null=True, blank=False, default=None)
    scheme_account = models.ForeignKey(SchemeAccount, on_delete=models.PROTECT)
    remarks = models.TextField(null=True, default=None)
    issue_date = models.DateField()
    issue_status = models.IntegerField(choices=ISSUE_STATUS, default=1)
    issued_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE,
                                  related_name='other_inventory_issued_by', null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    cancelled_by = models.ForeignKey(accounts_user, on_delete=models.CASCADE,
                                     related_name='other_inventory_item_issue_cancelled_by', null=True, blank=True)
    cancelled_on = models.DateTimeField(null=True, blank=False, default=None)
    cancelled_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'other_inventory_item_issue'

    def save(self, *args, **kwargs):
        if self.issued_by and not self.issued_by.is_adminuser:
            raise ValidationError(
                "Issued by must be an employee (is_adminuser=True).")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Other Inventory Item Issue {self.issue_no}"

    LOGGING_IGNORE_FIELDS = ('issue_date', 'issued_by')


class OtherInventoryPurchaseIssueLogs(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey(OtherInventoryItem, on_delete=models.PROTECT)
    from_branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                                    related_name='other_inventory_log_from_branch', null=True, default=None)
    to_branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                                  related_name='other_inventory_log_to_branch', null=True, default=None)
    status = models.IntegerField(choices=[(1, 'Inward'), (2, 'Outward')])
    ref_id = models.CharField(max_length=255)
    pieces = models.PositiveIntegerField()
    date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'other_inventory_purchase_log'

    def __str__(self):
        return f"Other Inventory Puchase Log {self.id}"


class OtherInventoryItemReOrder(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey(OtherInventoryItem, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                               related_name='erp_other_inventory_reorder', null=True, default=None)
    min_pcs = models.CharField(max_length=255, null=True, default=None)

    @property
    def branch_name(self):
        return self.branch.name if self.branch else None

    class Meta:
        db_table = 'erp_other_inventory_reorder'

    def __str__(self):
        return f"Other Inventory Item ReOrder {self.id} - {self.branch.name if self.branch else 'No Branch'}"
    


class ProductItemMapping(models.Model):
    id_product_mapping  = models.AutoField(primary_key=True)
    id_product          = models.ForeignKey(Product,on_delete=models.PROTECT,related_name='product')
    id_item             = models.ForeignKey(OtherInventoryItem, on_delete=models.PROTECT,related_name='id_item')
    created_on          = models.DateTimeField(auto_now_add=datetime.now())
    class Meta:
        db_table = 'erp_item_mapping'
        indexes = [
            models.Index(fields=['id_product', 'id_item']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['id_product', 'id_item'], name='unique_product_item')
        ]

