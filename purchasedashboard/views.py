from django.shortcuts import render
from rest_framework import generics, permissions, status , serializers
from rest_framework.response import Response
from datetime import datetime, timedelta, date
from django.utils.timezone import make_aware

from common.permissions import (IsEmployee)
from utilities.utils import (format_date)
from retailpurchase.models import (ErpSupplierRateCut)
from retailpurchase.serializers import (ErpSupplierRateCutSerializer)
from retailmasters.models import (Supplier)


def get_past_date(value):
    now = make_aware(datetime.now()).date()  # Get only the date part
    start_date = now
    end_date = now  # Default is current date for end date

    if value == 2:  # THIS WEEK
        start_date = now - timedelta(days=now.weekday())  # Start of this week (Monday)
        end_date = start_date + timedelta(days=6)  # End of this week (Sunday)
    elif value == 3:  # LAST MONTH
        first_day_of_current_month = now.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        start_date = last_day_of_last_month.replace(day=1)  # Start of last month
        end_date = last_day_of_last_month  # End of last month
    elif value == 4:  # TODAY
        start_date = now
        end_date = now
    elif value == 5:  # YESTERDAY
        start_date = now - timedelta(days=1)
        end_date = start_date
    else:  # Default is THIS MONTH
        start_date = now.replace(day=1)  # Start of this month
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)  # End of this month
    return start_date, end_date


class ErpSupplierRateCutListAPIView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        settings_type=1
        queryset = ErpSupplierRateCut.objects.filter(setting_bill_type = settings_type )
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(entry_date__range=[from_date, to_date])
        serializer = ErpSupplierRateCutSerializer(queryset, many=True)
        for data in serializer.data:
            supplier = Supplier.objects.filter(id_supplier=data['id_supplier']).first()
            data.update({"supplier_name":supplier.supplier_name, "entry_date":format_date(data['entry_date'])})
        return Response(serializer.data, status=status.HTTP_200_OK)