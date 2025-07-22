from django.db import models

# Create your models here.

class ChitSettings(models.Model):
    GENERATE_NO_CHOICES = [
        (1, 'Scheme wise'),
        (2, 'Branch wise'),
        (3, 'Scheme and branch wise')
    ]
    id                  = models.AutoField(primary_key=True)
    receipt_no_setting  = models.IntegerField(choices=GENERATE_NO_CHOICES, default=1)
    account_no_setting  = models.IntegerField(choices=GENERATE_NO_CHOICES, default=1)
    is_maintenance      = models.BooleanField(default=False)
    
    def __str__(self):
        return 'ChitSettings (ID %s) ' % (self.id )
    
    class Meta:
        db_table = 'chit_settings'
        
