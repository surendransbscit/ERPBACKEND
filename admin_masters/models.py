from django.db import models
from  utilities.model_utils import CommonFields
from datetime import datetime, timedelta, date
import os

def upload_pic(instance, filename):
    _, file_extension = os.path.splitext(filename)
    return 'images/cient/{id}{title}{ext}'.format(id=instance.mobile, title=datetime.now().strftime('%Y%m%d%H%M%S'), ext=file_extension)

class ClientMaster(CommonFields):
    client_id = models.AutoField(primary_key=True)
    company_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255,blank=True, null=True)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(max_length=255,blank=True, null=True)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    client_img = models.ImageField(upload_to=upload_pic, null=True)
    id_country = models.ForeignKey('retailmasters.Country', on_delete=models.PROTECT, null=True)
    id_state=models.ForeignKey('retailmasters.State',on_delete=models.PROTECT, null=True)
    id_city=models.ForeignKey('retailmasters.City',on_delete=models.PROTECT, null=True) 
    
    def __str__(self):
        return f"{self.company_name} ({self.client_id})"
    class Meta:
        db_table = 'client_master'

class ModuleMaster(CommonFields):
    id_module = models.AutoField(primary_key=True)
    module_name = models.CharField(max_length=255)
    short_code = models.CharField(max_length=50,blank=True, null=True)
    approx_cost = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.module_name} ({self.id_module})"
    class Meta:
        db_table = 'module_master'

class ProductMaster(CommonFields):
    id_product = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    short_code = models.CharField(max_length=50,blank=True, null=True)
    Approx_cost = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    module = models.ManyToManyField(ModuleMaster,blank=True,default=None)
    
    def __str__(self):
        return f"{self.product_name} ({self.id_product})"
    class Meta:
        db_table = 'admin_product_master'



