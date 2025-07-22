from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import (Payment, PaymentModeDetail, PaymentStatus)

        
class PaymentSerializer(serializers.ModelSerializer):

    paid_through_display = serializers.CharField(source='get_paid_through_display', read_only=True)
    class Meta:
        model = Payment
        fields = '__all__'
 
class PaymentModeDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentModeDetail
        fields = '__all__'
        
class PaymentStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentStatus
        fields = '__all__'