from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from datetime import datetime
from customers.models import Customers

accounts_user = 'accounts.User' 



class LoyaltyTier(models.Model):
    id = models.AutoField(primary_key=True)
    tier_name = models.CharField(max_length=255)
    min_lifetime_spend = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    multiplier = models.CharField(max_length=20)
    description = models.TextField(null=True)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_loyalty_tier', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_loyalty_tier', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Loyalty Tier - ' + str(self.pk)

    class Meta:
        db_table = 'loyalty_tier'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')


class LoyaltySettings(models.Model):
    id = models.AutoField(primary_key=True)
    base_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    point_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    max_redeem_percent = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    points_validity_days = models.CharField(max_length=20)
    redemption_wait_days = models.CharField(max_length=20)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_loyalty_settings', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_loyalty_settings', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Loyalty Settings - ' + str(self.pk)

    class Meta:
        db_table = 'loyalty_settings'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    
    
    
class LoyaltyCustomer(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customers, on_delete=models.CASCADE, related_name="loyalty_customer")
    current_tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.CASCADE, related_name="loyalty_tier")
    current_points = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    lifetime_spend = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_loyalty_customer', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_loyalty_customer', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Loyalty Customer - ' + str(self.pk)

    class Meta:
        db_table = 'loyalty_customer'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')
    
    
class LoyaltyTransaction(models.Model):
    
    TYPE_CHOICES = [
        (1, 'Earn'),
        (2, 'Redeem'),
        (3, 'Bonus'),
        (4, 'Expire'),
    ]
    
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customers, on_delete=models.CASCADE, related_name="loyalty_transaction")
    type = models.IntegerField(choices=TYPE_CHOICES)
    points = models.CharField(max_length=255)
    amount_linked = models.CharField(max_length=255)
    description = models.TextField(null=True)
    issue_date = models.DateTimeField(null=True, blank=False, default=None)
    expiry_date = models.DateTimeField(null=True, blank=False, default=None)
    created_by = models.ForeignKey(
        accounts_user, related_name='created_loyalty_transaction', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        accounts_user, related_name='updated_loyalty_transaction', on_delete=models.CASCADE, null=True, blank=True)
    updated_on = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self) -> str:
        return 'Loyalty Transaction - ' + str(self.pk)

    class Meta:
        db_table = 'loyalty_transaction'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by', 'updated_on',
                             'updated_by')