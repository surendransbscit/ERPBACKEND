from django.db import models
from accounts.models import User

class CommonFields(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User,on_delete=models.PROTECT, null=True,related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User,null=True, on_delete=models.SET_NULL,related_name='%(class)s_updated_by')

    class Meta:
        abstract = True