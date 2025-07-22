from django import template
from utilities.utils import (format_currency as currency,format_currency_with_symbol as currency_with_symbol,format_date as date_format,format_wt as wt_format)

register = template.Library()

@register.filter
def format_currency(value):
    return currency(value)

@register.filter
def format_currency_with_symbol(value):
    return currency_with_symbol(value)

@register.filter
def format_date(value):
    return date_format(value)

@register.filter
def format_wt(value):
    return wt_format(value)
@register.filter
def check_value(value):
    if(value and float(value) > 0):
        return True
    else:
        return False
@register.filter
def check_element(value):
    if(value):
        return True
    else:
        return False