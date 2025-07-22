from django.shortcuts import render
import requests
from datetime import datetime, timedelta, date


def create_order(order_details):
    url = 'https://sandbox.cashfree.com/pg/orders'
    headers = {
        'accept':'application/json',
        'Content-Type':'application/json',
        'x-api-version': '2023-08-01',
        'x-client-id': 'TEST103901437f295ca34d8ba50fa55834109301',
        'x-client-secret': 'cfsk_ma_test_c8f338ef6b9eb836331baafead535abb_17f6540c',
    }
    data = {
        "order_id": order_details['order_id'],
        "order_amount": order_details['order_amount'],
        "order_currency": "INR",
        "customer_details": order_details['customer_details'],
        "order_meta": {
            "return_url": "",
            "notify_url": "",
            "payment_methods": None,
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        return {"status":True,"result":response_data}
    except ValueError:
        print("Response content is not valid JSON")
        return {'message': 'Invalid response format', 'status':False,'content': response.text}
    


def get_gateway_order_details(order_id):
    url = f'https://sandbox.cashfree.com/pg/orders/{order_id}/payments'
    print(url)
    headers = {
        'accept':'application/json',
        'Content-Type':'application/json',
        'x-api-version': '2023-08-01',
        'x-client-id': 'TEST103901437f295ca34d8ba50fa55834109301',
        'x-client-secret': 'cfsk_ma_test_c8f338ef6b9eb836331baafead535abb_17f6540c',
    }
    try:
        response = requests.get(url,headers=headers)
        response_data = response.json()
        return {"status":True,"result":response_data}
    except ValueError:
        print("Response content is not valid JSON")
        return {'message': 'Invalid response format', 'status':False,'content': response.text}