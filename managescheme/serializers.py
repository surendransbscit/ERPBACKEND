
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import (SchemeAccount)


class SchemeAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchemeAccount
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=SchemeAccount.objects.all(),
                fields=(
                    'acc_scheme_id',
                    'scheme_acc_number',),
                message='This account number has been already assigned')]
        