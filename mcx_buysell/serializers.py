from rest_framework import serializers

from .models import (McxBuySell)


class McxBuySellSerializer(serializers.ModelSerializer):

    class Meta:
        model = McxBuySell
        fields = '__all__'