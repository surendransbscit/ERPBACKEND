
from rest_framework import serializers

from .models import RetailSettings


class RetailSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailSettings
        fields = '__all__'
