from django.shortcuts import render
from rest_framework import generics, permissions, status , serializers
from rest_framework.response import Response
from django.db import IntegrityError, transaction
from django.utils import timezone
from common.permissions import IsAdminUser, IsCustomerUser, IsEmployee
import re

# from managescheme.views import (RateMasterClass)
from customers.models import (Customers, CustomerDeviceIdMaster)
from customers.serializers import (CustomerDeviceIdMasterSerializer)
from retailmasters.models import (ErpService, Branch, metalRatePurityMaster, MetalRates, Company)
from retailmasters.serializers import (MetalRatePurityMasterSerializer)
from schememaster.models import (Scheme)
from schemepayment.models import (Payment)
from utilities.notifications import (send_push_notification)


class RateMasterClass :

    def get_metal_rates(self,id_purity,id_metal):
        metal_rate = 0
        if(metalRatePurityMaster.objects.filter(id_metal=id_metal,id_purity=id_purity).exists()):
            queryset = metalRatePurityMaster.objects.get(id_metal=id_metal,id_purity=id_purity)
            serializer = MetalRatePurityMasterSerializer(queryset)
            if (serializer.data['id_purity']==id_purity and serializer.data['id_metal'] == id_metal):
                try: 
                    metal_rate = MetalRates.objects.latest('rate_id')
                    field_name = MetalRates._meta.get_field(queryset.rate_field)
                    rate_value = field_name.value_from_object(metal_rate)
                    metal_rate = rate_value
                except MetalRates.DoesNotExist:
                    metal_rate = 0
        return metal_rate


def render_service_message(content: str, replacements: dict) -> str:
    def replace_placeholder(match):
        key = match.group(1)
        return str(replacements.get(key, f"@@{key}@@"))
    return re.sub(r"@@(.*?)@@", replace_placeholder, content)

def generate_service_message(cus_id, short_code, data: dict) -> str:
    customer = Customers.objects.get(id_customer=cus_id)
    company = Company.objects.latest('id_company')
    service = ErpService.objects.get(short_code=short_code)
    

    replacements = {
        "cus_name": customer.firstname,
        "mobile": customer.mobile,
    }

    # if service_id == 1:
    #     if CustomerOTP.objects.filter(customer=customer.pk, otp_for=2, expiry__gt=timezone.now()).exists():
    #         raise Exception("A valid reset OTP already exists. Please use it / wait till its expire")

    #     OTP_code = randint(100000, 999999)
    #     expiry_time = timezone.now() + timedelta(minutes=5)

    #     replacements.update({
    #         "otp": OTP_code,
    #         "validate_sec": (expiry_time - timezone.now()).seconds,
    #     })

    if service.short_code == 'any':
        replacements.update({
            "company_name": company.company_name
        })

    elif service.short_code == 'any':
        scheme_id = data.get('scheme_id')
        scheme = Scheme.objects.get(scheme_id=scheme_id)
        replacements.update({
            "scheme_name": scheme.scheme_name
        })

    elif service.short_code == 'payment_confirmation':
        payment_id = data.get('payment_id')
        payment = Payment.objects.get(id_payment=payment_id)
        branch = Branch.objects.get(id_branch=payment.id_branch.pk)
        replacements.update({
            "scheme_name": payment.id_scheme.scheme_name,
            "payment_amount": payment.payment_amount,
            "receipt_no": payment.receipt_no,
            "company_name": branch.id_company.company_name
        })

    elif service.short_code == 'metal_rate_update':
        rate_master = RateMasterClass()
        gold_metal_rate = rate_master.get_metal_rates(1, 1)
        silver_metal_rate = rate_master.get_metal_rates(1, 2)
        replacements.update({
            "gold_22ct": gold_metal_rate,
            "silver_G": silver_metal_rate,
        })
    
    content = service.content
    return render_service_message(content, replacements)


def send_notification_for_metal_rate():
    customer = CustomerDeviceIdMaster.objects.filter(is_active=True)
    device_serializers = CustomerDeviceIdMasterSerializer(customer, many=True)
    for device in device_serializers.data:
        content = generate_service_message(device['customer'], 'metal_rate_update', {})
        # print(content)
        if device['subscription_id'] != None and device['subscription_id']!='':
            send_push_notification(device['subscription_id'], "Metal Rate Update", content)
            
def send_notification_for_scheme_payment(cus_id, data):
    content = generate_service_message(cus_id, 'payment_confirmation', data)
    print(content)
    service = ErpService.objects.get(short_code='payment_confirmation')