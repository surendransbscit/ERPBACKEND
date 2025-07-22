from django.shortcuts import render
from django.db import IntegrityError, transaction
from django.http import HttpResponse, request, Http404
from datetime import datetime ,timedelta
from babel.numbers import format_decimal
from rest_framework import generics, permissions, status
from django.db import transaction , IntegrityError,DatabaseError,OperationalError,connection
# import numpy as np
from decimal import Decimal, ROUND_HALF_UP
import os
from django.conf import settings
from threading import Thread
import time
import logging
import random

# For Image upload
import base64
import uuid
import imghdr
from django.core.files.base import ContentFile
# For Image upload

# Comporess image
from PIL import Image
from io import BytesIO

def format_date(value) :
    if value is not None and value != '':
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime('%d-%m-%Y')
    return value

def format_date_short_year(value) :
    if value is not None and value != '':
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime('%d-%m-%y')
    return value

def date_format_with_time(value) :
    if value is not None:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime('%d-%m-%Y %H:%m:%S')
    return value

def format_currency(value):
    try:
        value = float(value)
        value = format(value,'.2f')
        formatted_value = format_decimal(value, format='#,##,##,##,###.00',locale='en_IN')
        return formatted_value
    except (ValueError, TypeError):
        return value

def format_currency_with_symbol(value):
    try:
        value = float(value)
        formatted_value = format_decimal(value, locale='en_IN')
    except (ValueError, TypeError):
        return value
    return f"₹ {formatted_value}"

def format_wt(value):
    try:
        value = float(value)
        formatted_value = format_decimal(value, format='#,##,##,##,###.000',locale='en_IN')
        return formatted_value
    except (ValueError, TypeError):
        return value
    

def format_number_with_decimal(value,decimal):
    try:
        value = float(value)
        if(int(decimal) == 3):
            formatted_value = format_decimal(value, format='#.000',locale='en_IN')
        elif(int(decimal)== 2):
            formatted_value = format_decimal(value, format='#.00',locale='en_IN')
        elif(int(decimal)==1):
            formatted_value = format_decimal(value, format='#.0',locale='en_IN')
        else:
            formatted_value = format_decimal(value, format='#',locale='en_IN')

        return formatted_value
    except (ValueError, TypeError):
        return value
    
def format_data_with_decimal(data,column):

    for row in data:

        for col in column:

            decimal_places = col.get('decimal_places')

            if(decimal_places):
               
                value = row[col['accessor']]
               
                value=format_number_with_decimal(value,decimal_places)

                row[col['accessor']] = value

    return data

def grand_total_data(data, column):
    response_data = {}

    for row in data:
        for col in column:
            value = row.get(col['accessor'], 0)
            is_total_req = col.get('is_total_req')

            if is_total_req:
                if col['accessor'] not in response_data:
                    response_data[col['accessor']] = 0

                response_data[col['accessor']] += float(value or 0)

    return response_data





def train_sales_model(df):

    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error

    # Prepare the data for training
    df['days_since_start'] = (df['invoice_bill_id__invoice_date'] - df['invoice_bill_id__invoice_date'].min()).dt.days
    X = df[['days_since_start']].values  # Input feature: time (days since start)
    y = df['total_pieces'].values       # Target: quantity sold

    # Check if there are enough samples to split the data
    if len(X) > 1:
        # Split the data into training and testing sets (only if we have more than 1 sample)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Test the model and calculate accuracy
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f'Mean Squared Error: {mse}')
    else:
        # If we don't have enough samples, train on the full dataset
        model = LinearRegression()
        model.fit(X, y)
        print('Insufficient data to perform train-test split. Model trained on full dataset.')

    return model

def predict_future_sales(model, days_from_now):
    # Predict the quantity to be sold in a given number of days
    future_days = np.array([[days_from_now]])
    predicted_sales = model.predict(future_days)
    return predicted_sales[0]


def dynamic_predict_future_sales(model, days_list):
    """
    Predict the quantity to be sold for multiple day intervals.
    
    Args:
        model: The trained prediction model.
        days_list: A list of days from now for which predictions are needed.
    
    Returns:
        A dictionary with the number of days as keys and predicted sales as values.
    """
    # Convert the list of days to a NumPy array for model input
    future_days = np.array(days_list).reshape(-1, 1)
    
    # Predict sales for the given days
    predicted_sales = model.predict(future_days)
    
    # Return a dictionary where keys are days and values are the predicted sales
    return {f"{days}_days": float(predicted_sales[i]) for i, days in enumerate(days_list)}



def generate_query_result(query):
    results = []
        # Execute the query
    with connection.cursor() as cursor:
        cursor.execute(query)
        # Fetch all rows from the executed query
        rows = cursor.fetchall()

        # Get column names from the cursor
        columns = [col[0] for col in cursor.description]

    # Create a list of dictionaries to represent the result
    for row in rows:
        results.append(dict(zip(columns, row)))
    
    return results

    
def format_with_decimal(value,type):
    try:
        if int(type) == 2 :
            format_value = "0.00"
        elif int(type) == 3 :
            format_value = "0.000"
        else:
            format_value = "0"
        value = Decimal(value)
        formatted_value = value.quantize(Decimal(format_value), rounding=ROUND_HALF_UP)  # 2 decimal places
        return formatted_value
    except (ValueError, TypeError):
        return value
    

def check_image_exists(image_path):
    # Replace `MEDIA_ROOT` with the actual path where images are stored
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)
    return os.path.exists(full_path)

def calculate_item_cost(props):
    item_cost = 0
    total_mc_value = 0
    taxAmount = 0
    cgst = 0
    sgst = 0
    igst = 0
    item_rate = 0
    piece = props['pieces']
    gross_wt = props['gross_wt']
    net_wt = props['net_wt']
    pure_wt = props['pure_wt']
    wastage_wt = props['wastage_wt']
    mc_type = props['mc_type']
    mc_value = props['mc_value']
    rate_per_gram =  props['rate_per_gram']
    tax_type = props['tax_type']
    tax_percentage = props['tax_percentage']
    product_details = props['productDetails']
    stone_amount = props['stone_amount']
    other_metal_amount =  props['other_metal_amount']
    other_charges_amount =  props['other_charges_amount']
    discount_amount = props['discount_amount']
    sell_rate = props['sell_rate']
    mc_calc_type = props['mc_calc_type']
    sales_mode = props['sales_mode']
    fixwd_rate_type = props['fixwd_rate_type']
    invoice_type = props['invoice_type']
    settings_billling_type = props['settings_billling_type']
    
    if(mc_calc_type==1):
        total_mc_value = (float(gross_wt)*float(mc_value) if mc_type == 1  else float(piece)*float(mc_value))
    else:
        total_mc_value = float(net_wt)*float(mc_value) if mc_type == 1  else float(piece)*float(mc_value)
    
    if(int(sales_mode) == 1):
        if(int(invoice_type)==2):
            
            item_rate = (float(float(pure_wt))*float(rate_per_gram))
        else:
            item_rate = (float(float(net_wt)+float(wastage_wt))*float(rate_per_gram))
        
    else:
        if(int(fixwd_rate_type)==2):
            item_rate = float(sell_rate)
        else:
            item_rate = float(float(sell_rate)*float(net_wt))
        
    taxable_amount = float(float(item_rate)+float(total_mc_value)+float(other_metal_amount)+float(stone_amount)+float(other_charges_amount)-float(discount_amount))
    if(tax_type!='' and tax_type!=0 and tax_percentage>0 and (not settings_billling_type)):
        if(tax_type==1):
            taxAmount = calculate_inclusive_tax(taxable_amount,tax_percentage)
            item_cost = float(taxable_amount)
            taxable_amount = float(float(taxable_amount)-float(taxAmount))
        else:
            taxAmount = calculate_exclusive_tax(taxable_amount,tax_percentage)
            item_cost = float(float(taxAmount)+float(taxable_amount))
        if(taxAmount>0):
            cgst = float(taxAmount/2)
            sgst = float(taxAmount/2)
    else:
        item_cost = taxable_amount
    return {
        "item_cost":format(round(item_cost),'.2f'),
        "taxAmount":format(taxAmount,'.2f'),
        "taxable_amount":format(taxable_amount,'.2f'),
        "cgst":format(cgst,'.2f'),
        "sgst":format(sgst,'.2f'),
        "igst":format(igst,'.2f'),
        "total_mc_value":format(total_mc_value,'.2f'),
        "discount_amount":format(discount_amount,'.2f'),
    }

def calculate_inclusive_tax(taxable_amount,tax_percentage):
    amt_without_gst = (float(taxable_amount)*100)/(100+float(tax_percentage))
    inclusive_tax_amount = float(float(taxable_amount)	- float(amt_without_gst))
    return inclusive_tax_amount

def calculate_exclusive_tax(taxable_amount,tax_percentage):
    exclusive_tax_amount = float(float(float(taxable_amount)*float(tax_percentage))/100)
    return exclusive_tax_amount

def convert_tag_to_formated_data(item):
        return_data = {
            "product_name": item["product_name"],
            "design_name": item.get("design_name",""),
            "sub_design_name": item.get("sub_design_name",""),
            "purity_name": item.get("purity_name",""),
            "id_product": item["tag_product_id"],
            "id_design": item["tag_design_id"],
            "id_purity": item["tag_purity_id"],
            "id_sub_design": item["tag_sub_design_id"],
            "pieces": item["tag_pcs"],
            "gross_wt": item["tag_gwt"],
            "net_wt": item["tag_nwt"],
            "less_wt": item["tag_lwt"],
            "stone_wt": item["tag_stn_wt"],
            "dia_wt": item["tag_dia_wt"],
            "other_metal_wt": item["tag_other_metal_wt"],
            "wastage_wt": item["tag_wastage_wt"],
            "wastage_percentage": item["tag_wastage_percentage"],
            "pure_wt": item["tag_pure_wt"],
            "purchase_touch": item["tag_purchase_touch"],
            "purchase_va": item["tag_purchase_va"],
            "mc_value": item["tag_mc_value"],
            "mc_type": item["tag_mc_type"],
            "sell_rate": item["tag_sell_rate"],
            "buy_rate": item["tag_buy_rate"],
            "flat_mc_value": item["flat_mc_value"],
            "total_mc_value": item["total_mc_value"],
            "old_tag_code": item["old_tag_code"],
        }
        return return_data


def delete_file_after_delay(file_path, delay=5):
        def delete_file():
            time.sleep(delay)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"File deleted successfully: {file_path}")
                except Exception as e:
                    logging.error(f"Error deleting file {file_path}: {e}")
            else:
                logging.warning(f"File does not exist: {file_path}")

        # Run the deletion in a separate thread
        thread = Thread(target=delete_file)
        thread.start()

    

def base64_to_file(base64_string, filename_prefix="uploaded", file_extension="jpg"):
    try:
        if ";base64," in base64_string:
            header, base64_data = base64_string.split(";base64,")
        else:
            base64_data = base64_string
        
        # Add padding if missing
        missing_padding = len(base64_data) % 4
        if missing_padding:
            base64_data += '=' * (4 - missing_padding)

        # Decode
        file_data = base64.b64decode(base64_data)
        
        # Create unique filename
        file_name = f"{filename_prefix}_{uuid.uuid4()}.{file_extension}"
        
        return ContentFile(file_data, name=file_name)

    except Exception as e:
        print(f"❌ Error in base64_to_file: {e}")
        return None
    
def compress_image(file, format='JPEG', quality=70):
    try:
        image = Image.open(file)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        buffer = BytesIO()
        image.save(buffer, format=format, quality=quality)
        buffer.seek(0)

        return ContentFile(buffer.read(), name=file.name)
    except Exception as e:
        print(f"❌ Error in compress_image: {e}")
        return file  # Fallback to original if compression fails


def generate_random_number():
    number = random.randint(1000, 9999)
    return number



def get_date_range_from_days_type(days_type):
    today = datetime.today().date()

    if days_type == '4':  # Today
        return today, today
    elif days_type == '5':  # Yesterday
        day = today - timedelta(days=1)
        return day, day
    elif days_type == '2':  # This Week
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    elif days_type == '1':  # This Month
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)
        return start_date, end_date
    elif days_type == '3':  # Next Month
        next_month = today.replace(day=28) + timedelta(days=4)
        start_date = next_month.replace(day=1)
        next_next = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_next.replace(day=1) - timedelta(days=1)
        return start_date, end_date
    else:
        return None, None