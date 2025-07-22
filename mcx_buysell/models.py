from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator

from customers.models import (Customers)


class McxBuySell(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customers, on_delete=models.PROTECT, related_name='mcx_customer_buysell', null=True, default=None)
    type = models.IntegerField(choices=[(1, 'Buy'), (2, 'Sell')])
    sell_to = models.IntegerField(choices=[(1, 'Customer'), (2, 'MT5')], null=True, default=None)
    buy_from = models.IntegerField(choices=[(1, 'MT5'), (2, 'Bank'), (3, 'Bullion'), (4, 'Others')], null=True, default=None)
    metal = models.IntegerField(choices=[(1, 'Gold'), (2, 'Silver')])
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    mt5_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    premium = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,validators=[MinValueValidator(0.0)])
    payment_mode = models.IntegerField(choices=[(1, 'Cash'), (2, 'Bank')], null=True, default=None)
    bullion_name = models.CharField(max_length=255, null=True, default=None)
    open_position = models.DecimalField(max_digits=10, decimal_places=3, default=0.000,null=False)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    
    def __str__(self) -> str:
        return 'MCX Buy / Sell - ' + str(self.pk)
    
    class Meta:
        db_table = 'mcx_buy_sell'
    
