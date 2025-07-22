from rest_framework import serializers
from .models import (Discount,Coupon, GiftVoucher, GiftVoucherIssue, GiftVoucherIssuePaymentDetail)


class DiscountSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Discount
        fields = '__all__'
        
        
class CouponSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Coupon
        fields = '__all__'
        
class GiftVoucherSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = GiftVoucher
        fields = '__all__'
        
class GiftVoucherIssueSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()
    voucher_name = serializers.SerializerMethodField()
    
    
    class Meta:
        model = GiftVoucherIssue
        fields = '__all__'
        
    def get_customer_name(self, obj):
        if obj.customer:
            return obj.customer.firstname
        return None

    def get_employee_name(self, obj):
        if obj.employee:
            return obj.employee.firstname
        return None

    def get_supplier_name(self, obj):
        if obj.supplier:
            return obj.supplier.supplier_name
        return None
    
    
    def get_voucher_name(self, obj):
        if obj.voucher:
            return obj.voucher.voucher_name
        return None

        
class GiftVoucherIssuePaymentDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = GiftVoucherIssuePaymentDetail
        fields = '__all__'