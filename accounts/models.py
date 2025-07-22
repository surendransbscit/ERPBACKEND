from django.db import models
from datetime import datetime, timedelta
from email.policy import default
from django.contrib.auth.models import AbstractUser, Group, Permission


# Create your models here.
class User(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_adminuser = models.BooleanField(default=False)
    email = models.EmailField(unique=False, null=True,default=None, blank=True)
    account_expiry = models.DateField(null=True)
    groups = models.ManyToManyField(Group, related_name='user_accounts')
    # Add or change a related_name for user_permissions
    user_permissions = models.ManyToManyField(
        Permission, related_name='user_accounts_permissions'
    )


    def __str__(self):
        return self.username

    class Meta:
        db_table = 'auth_user'
        constraints = [
            models.CheckConstraint(violation_error_message='isAdmin and isCustomer values cannot be same', name='Admin and Customer values cannot be same', check=~(
                models.Q)(is_customer=models.F('is_adminuser'))),
            models.CheckConstraint(violation_error_message='Customer cannot become a staff',
                                   name='Customer cannot become a staff', check=~models.Q(models.Q(is_customer=True), models.Q(is_staff=True))),
            models.CheckConstraint(violation_error_message='Customer cannot become superuser',
                                   name='Customer cannot become superuser', check=~models.Q(models.Q(is_customer=True), models.Q(is_superuser=True))),
            models.CheckConstraint(
                check=models.Q(
                    username__regex=r'^\w(?:\w|[.-](?=\w))*$'
                ),
                name="Invalid username",
                violation_error_message="Username must only contain alphanumeric characters, '@', '#', '-', '_', and '.'",
            )
        ]

    LOGGING_IGNORE_FIELDS = ('is_customer', 'is_adminuser', 'is_staff',
                             'last_name', 'first_name', 'is_superuser', 'last_login', 'password')