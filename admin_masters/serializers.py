from rest_framework import serializers
from .models import ClientMaster, ModuleMaster, ProductMaster

class ClientMasterSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='id_country.name', read_only=True)
    state_name = serializers.CharField(source='id_state.name', read_only=True)
    city_name = serializers.CharField(source='id_city.name', read_only=True)
    class Meta:
        model = ClientMaster
        fields = '__all__'

class ModuleMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleMaster
        fields = '__all__'

class ProductMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMaster
        fields = '__all__'
