from django.shortcuts import render
from rest_framework.response import Response
from utilities.pagination_mixin import PaginationMixin
from rest_framework import generics, permissions, status
from django.db import IntegrityError, transaction
from utilities.utils import format_date, date_format_with_time, format_number_with_decimal
from common.permissions import IsAdminUser, IsEmployee
from datetime import datetime, timedelta, date
from django.db.models import Sum

from .models import (McxBuySell)
from .serializers import (McxBuySellSerializer)
from customers.models import (Customers)

from .constants import (MCXBUYSELL_COLUMN_LIST, MCXBUYSELL_ACTION_LIST)
from utilities.constants import (FILTERS)

pagination = PaginationMixin()


class GetBuySellOpeningPosition(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = McxBuySell.objects.all()
    serializer_class = McxBuySellSerializer
    
    def get(self, request, *args, **kwargs):
        total_buy_weight = McxBuySell.objects.filter(type=1).aggregate(Sum('weight'))['weight__sum'] or 0

        total_sell_weight = McxBuySell.objects.filter(type=2, sell_to=1).aggregate(Sum('weight'))['weight__sum'] or 0
        
        opening_position = total_sell_weight - total_buy_weight
        print(total_buy_weight)
        print(total_sell_weight)
        output = {
            "total_buy_weight": f"{total_buy_weight:.3f}" if total_buy_weight else "0.000",
            "total_sell_weight": f"{total_sell_weight:.3f}" if total_sell_weight else "0.000",
            "opening_position": f"{opening_position:.3f}"
        }
        return Response(output, status=status.HTTP_200_OK)

class McxBuySellListView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = McxBuySell.objects.all()
    serializer_class = McxBuySellSerializer
    
    def post(self, request, *args, **kwargs):
        start_date = request.data.get('fromDate')
        end_date = request.data.get('toDate')
        
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        filters = {}
        if start_date and end_date:
            filters["created_date__range"] = (start_date, end_date)
        
        queryset = McxBuySell.objects.filter(**filters)
        paginator, page = pagination.paginate_queryset(queryset, request,None,MCXBUYSELL_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            if(data['type']==1):
                if(data['buy_from']==1):
                    data.update({"bought_from":"MT5"})
                elif(data['buy_from']==2):
                    data.update({"bought_from":"Bank"})
                elif(data['buy_from']==3):
                    data.update({"bought_from":"Bullion"})
                else:
                    data.update({"bought_from":"Others"})
                data.update({"type_label":"Buy"})
            if(data['type']==2):
                if(data['sell_to']==1):
                    data.update({"sold_to":"Customer"})
                else:
                    data.update({"sold_to":"MT5"})
                data.update({"type_label":"Sell"})
                
            if(data['metal']==1):
                data.update({"metal_label":"Gold"})
            if(data['metal']==2):
                data.update({"metal_label":"Silver"})
                
            
                
            if(data['customer']is not None):
                customer = Customers.objects.filter(id_customer=data['customer']).first()
                data.update({"customer_name":customer.firstname, "customer_mobile":customer.mobile})
            
            if(data['customer']is None):
                data.update({"customer_name":"-", "customer_mobile":"-"})
            
            data.update({"pk_id": data['id'],
                        'sno': index+1, "date_time":date_format_with_time(data['created_datetime']),
                        })
        filters_copy = FILTERS.copy()
        filters_copy['isDateFilterReq'] = True
        context = {
            'columns': MCXBUYSELL_COLUMN_LIST,
            'actions': MCXBUYSELL_ACTION_LIST,
            'page_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'is_filter_req': True,
            'filters': filters_copy
        }
        return pagination.paginated_response(serializer.data, context)
    

class McxBuySellCreateView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    queryset = McxBuySell.objects.all()
    serializer_class = McxBuySellSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = McxBuySellSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)