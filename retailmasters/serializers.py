from pyexpat import model
from statistics import mode
from django.contrib.auth.models import Group
from rest_framework.validators import UniqueValidator
from rest_framework import serializers

from .models import (Country, State, City, Branch, Company, Uom, Taxmaster, CustomerProof, 
                     Taxgroupmaster, Taxgroupitems, Department, Designation, IncentiveTransactions,
                     FinancialYear, Currency, ExchangeRate, Bank, PaymentMode, CustomerNotificationMaster, 
                     Profile, Area, Profession, Tenant, MetalRates,RelationType, CustomerNotifications,
                     PaymentGateway, PayDevice, District, Banner, NBType, metalRatePurityMaster,ErpDayClosed,
                     WeightRange,Size,Supplier,AttributeEntry,OtherCharges, ERPOrderStatus, ErpDayClosedLog,
                     StockIssueType,Floor,Counter,RegisteredDevices,Container,OldMetalItemType,OtherWeight,
                     CashOpeningBalance,AccountHead, SupplierStaffDetails, SupplierAccountDetails, ErpService,IncentiveSettings,
                     SupplierProductImageDetails, SupplierProductDetails, SupplierProducts,BankDeposit,DepositMaster,DepositMasterInterest,
                     CustomerDeposit, CustomerDepositItems, CustomerDepositPayment, CustomerDepositPaymentDetail,Religion,
                     DailyStatusMaster,Region)


# Country model serializer
class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = '__all__'
        
        
class ErpServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ErpService
        fields = '__all__'
        
class ERPOrderStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = ERPOrderStatus
        fields = '__all__'
        
#District
class DistrictSerializer(serializers.ModelSerializer):

    class Meta:
        model = District
        fields = '__all__'


# State model serializer
class StateSerializer(serializers.ModelSerializer):

    class Meta:
        model = State
        fields = '__all__'


# City model serializer
class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = '__all__'

# branch  model serializer
class BranchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Branch
        fields = '__all__'

# Company model serializer
class CompanySerializer(serializers.ModelSerializer):
    # company_name = serializers.CharField()

    class Meta:
        model = Company
        fields = '__all__'
        # extra_kwargs ={"company_name"}


# Get the Department details serialized:
class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Department
        # fields = ['username', 'email', 'is_customer', 'is_adminuser']
        fields = '__all__'


# Get the Designation details serialized:
class DesignationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Designation
        # fields = ['username', 'email', 'is_customer', 'is_adminuser']
        fields = '__all__'

class UOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = Uom
        fields = '__all__'
        
class TaxmasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taxmaster
        fields = '__all__'
        
class TaxgroupmasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taxgroupmaster
        fields = '__all__'
        
class TaxgroupitemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taxgroupitems
        fields = '__all__'

class FinancialYearSerializer(serializers.ModelSerializer):

    class Meta:
        model = FinancialYear
        fields = '__all__'
        
class CustomerProofSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerProof
        fields = '__all__'

class CurrencySerializer(serializers.ModelSerializer):

    class Meta:
        model = Currency
        fields = '__all__'

class ExchangeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExchangeRate
        fields = '__all__'
        
class BankSerializer(serializers.ModelSerializer):
    
     class Meta:
        model = Bank
        fields = '__all__'
        
class PaymentModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMode
        fields = '__all__'
        
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'
        
class RelationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationType
        fields = '__all__'

class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = '__all__'
        
        
class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'
        
        
class MetalRatesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = MetalRates
        fields = '__all__'
        

        
class PaymentGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGateway
        fields = '__all__'
        
class PayDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayDevice
        fields = '__all__'
        
class NBTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NBType
        fields = '__all__'
        
class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'
        
class MetalRatePurityMasterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = metalRatePurityMaster
        fields = '__all__'

class ErpDayClosedSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpDayClosed
        fields = '__all__'
        
class ErpDayClosedLogSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ErpDayClosedLog
        fields = '__all__'


class WeightRangeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = WeightRange
        fields = '__all__'
        extra_kwargs = {
                    'id_product': {'error_messages': {'required': 'Product is required.'}},
                    'from_weight': {'error_messages': {'required': 'From Weight is required.'}},
                    'to_weight': {'error_messages': {'required': 'To Weight is required.'}},
                    'weight_range_name': {'error_messages': {'required': 'Weight Range Name is required.'}}
                }
        
    def get_fields(self):
        fields = super().get_fields()
        fields['product_name'] = serializers.CharField(source='id_product.product_name', read_only=True, allow_null=True)
        return fields
class SizeSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='id_product.product_name', read_only=True)
    class Meta:
        model = Size
        fields = '__all__'
        extra_kwargs = {
                    'id_product': {'error_messages': {'required': 'Product is required.'}},
                    'value': {'error_messages': {'required': 'Value is required.'}},
                    'name': {'error_messages': {'required': 'Name is required.'}},
                }
        
class SupplierSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Supplier
        fields = '__all__'
        
        
class SupplierAccountDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SupplierAccountDetails
        fields = '__all__'
        
        
class SupplierStaffDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SupplierStaffDetails
        fields = '__all__'
        
        
class SupplierProductsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SupplierProducts
        fields = '__all__'
        
        
class SupplierProductDetailsSerializer(serializers.ModelSerializer):

    supplier_name = serializers.CharField(source='supplier_product.supplier.name', read_only=True)
    
    class Meta:
        model = SupplierProductDetails
        fields = '__all__'

    def get_supplier_name(self, obj):
        return obj.supplier_product.supplier.supplier_name
        
class SupplierProductImageDetailsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SupplierProductImageDetails
        fields = '__all__'

class AttributeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeEntry
        fields = '__all__'

class OtherChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherCharges
        fields = '__all__'

class StockIssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockIssueType
        fields = '__all__'

class FloorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Floor
        fields = '__all__'

class CounterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Counter
        fields = '__all__'

class RegisteredDevicesSerializer(serializers.ModelSerializer):

    class Meta:
        model = RegisteredDevices
        fields = '__all__'


class ContainerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Container
        fields = '__all__'

class OldMetalItemTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = OldMetalItemType
        fields = '__all__'

class OtherWeightSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtherWeight
        fields = '__all__'

class CashOpeningBalanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = CashOpeningBalance
        fields = '__all__'

class AccountHeadSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountHead
        fields = '__all__'

class BankDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDeposit
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        fields['bank_name'] = serializers.CharField(source='bank.bank_name', read_only=True)
        fields['acc_number'] = serializers.CharField(source='bank.acc_number', read_only=True)
        return fields

class DepositMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepositMaster
        fields = '__all__'
        
    def get_fields(self):
        fields = super().get_fields()
        fields['scheme_name'] = serializers.CharField(source='scheme.scheme_name', read_only=True)
        return fields
        
class DepositMasterInterestSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepositMasterInterest
        fields = '__all__'
        
class CustomerDepositSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerDeposit
        fields = '__all__'
        
    def get_fields(self):
        fields = super().get_fields()
        fields['deposit_code'] = serializers.CharField(source='deposit.code', read_only=True)
        fields['cus_name'] = serializers.CharField(source='customer.firstname', read_only=True)
        fields['cus_mobile'] = serializers.CharField(source='customer.mobile', read_only=True)
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        return fields
        
class CustomerDepositItemsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerDepositItems
        fields = '__all__'
        
class CustomerDepositPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerDepositPayment
        fields = '__all__'
        
class CustomerDepositPaymentDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerDepositPaymentDetail
        fields = '__all__'


class IncentiveSettingsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = IncentiveSettings
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        fields['branch_name'] = serializers.CharField(source='branch.name', read_only=True)
        return fields
    
class IncentiveTransactionsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = IncentiveTransactions
        fields = '__all__'


class ReligionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Religion
        fields = '__all__'
        
class CustomerNotificationMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerNotificationMaster
        fields = '__all__'
        
class CustomerNotificationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerNotifications
        fields = '__all__'
        
class DailyStatusMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = DailyStatusMaster
        fields = '__all__'
        
        
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'