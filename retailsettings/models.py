from django.db import models

# Create your models here.

class RetailSettings(models.Model):
    GROUP_BY_CHOICE = [(1, 'Lot and Tag'), (2, 'Billing'),
                       (3, 'Purchase'), (4, 'Orders'), (5, 'General')]
    id_settings = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, error_messages={
                            'unique': "Retail Settings with this name already exists"})
    value = models.TextField()
    description = models.TextField()
    group_by = models.IntegerField(choices=GROUP_BY_CHOICE, default=1)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User', related_name='ret_settings_by_user', on_delete=models.PROTECT)
    # updated_on = models.DateTimeField(blank=True, null=True)
    # updated_by = models.ForeignKey(
    #     'accounts.User', related_name='ret_settings_updated_by_user', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self) -> str:
        return 'Retail Settings (ID %s) ' % (self.id_settings, )

    class Meta:
        db_table = 'settings'
        app_label = 'retailsettings'

    LOGGING_IGNORE_FIELDS = ('created_on', 'created_by')