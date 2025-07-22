from rest_framework import serializers
from .models import (ChitSettings)

class ChitSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChitSettings
        fields = '__all__'