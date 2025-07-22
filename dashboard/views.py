from django.shortcuts import render
from rest_framework import generics, status
from common.permissions import IsEmployee, isAdmin, isSuperuser,IsSuperuserOrEmployee
from rest_framework.response import Response
from datetime import datetime, timedelta, date
from collections import OrderedDict
import calendar
from django.utils import timezone
from django.db.models.expressions import RawSQL
from django.db.models import Sum, Avg, Count, Q, Func, Value, F, ExpressionWrapper, DecimalField, DateField
from decimal import Decimal, ROUND_HALF_UP
from django.utils.timezone import make_aware
from django.db.models.functions import TruncMonth, ExtractMonth, ExtractDay
from collections import defaultdict
from uuid import uuid4
from django.utils.timezone import now

from employees.models import (Employee)
from employees.serializers import (EmployeeSerializer)
from customers.models import (Customers, CustomerAddress)
from customers.serializers import (CustomerSerializer, CustomerAddressSerializer)
from retailmasters.models import (PaymentMode, Branch, Area, City,Supplier)
from schememaster.models import (Scheme, SchemeDigiGoldInterestSettings)
from retailmasters.serializers import (PaymentModeSerializer, BranchSerializer, AreaSerializer)
from schememaster.serializers import (SchemeSerializer)
from schemepayment.models import (Payment, PaymentModeDetail, PaymentStatus)
from schemepayment.serializers import (PaymentSerializer, PaymentModeDetailSerializer, PaymentStatusSerializer)
from managescheme.models import (SchemeAccount)
from managescheme.serializers import (SchemeAccountSerializer)
from managescheme.views import (SchemeAccountPaidDetails)
from inventory.models import (ErpTagging,ErpTaggingImages)
from customerorder.models import (ERPOrder,ERPOrderDetails, ErpJobOrderDetails)
from utilities.utils import (format_date , get_date_range_from_days_type)
from .constants import (ACTIVE_CHITS_COLUMN_LIST,MATURED_AND_UNCLAIMED_CHITS_COLUMN_LIST,PAYMENT_SUMMARY_COLUMN_LIST)
from retailpurchase.views import (ErpSupplierPaymentCreateAPIView)
from rest_framework.views import APIView
from retailpurchase.models import (ErpPurchaseEntryDetails)
from retailpurchase.serializers import (ErpPurchaseEntryDetailsListSerializer)
from django.db.models import Sum
from django.shortcuts import get_object_or_404

# def get_past_date(value):
#     if value is not None:
#         past_date =  (timezone.now() - timedelta(days=value)).date()
#         return past_date
#     return value

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
    # print([start_date, end_date])
    return start_date, end_date

class ConcatMonthDay(Func):
    function = 'CONCAT'
    template = "%(function)s(EXTRACT(MONTH FROM %(expressions)s), '-', EXTRACT(DAY FROM %(expressions)s))"

class CustomerImpDatesView(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    
    def get(self, request, *args, **kwargs):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        # start_of_next_week = start_of_week + timedelta(weeks=1)
        # end_of_next_week = start_of_next_week + timedelta(days=6)
        start_of_next_week = today + timedelta(days=(7 - today.weekday()))  
        end_of_next_week = start_of_next_week + timedelta(days=6)  
        next_month = today.replace(day=1) + timedelta(days=32)
        start_of_next_month = next_month.replace(day=1)
        end_of_next_month = next_month.replace(day=calendar.monthrange(next_month.year, next_month.month)[1])
        
        current_month = today.month
        current_day = today.day

        
        customers = Customers.objects.annotate(
            birth_month=ExtractMonth('date_of_birth'),
            birth_day=ExtractDay('date_of_birth'),
            wed_month=ExtractMonth('date_of_wed'),
            wed_day=ExtractDay('date_of_wed')
        )

        
        customers_today = customers.filter(
            (Q(birth_month=today.month) & Q(birth_day=today.day)) |
            (Q(wed_month=today.month) & Q(wed_day=today.day))
        )

        
        customers_tomorrow = customers.filter(
            (Q(birth_month=tomorrow.month) & Q(birth_day=tomorrow.day)) |
            (Q(wed_month=tomorrow.month) & Q(wed_day=tomorrow.day))
        )

        
        customers_this_week = customers.filter(
            (Q(birth_month__gte=start_of_week.month, birth_day__gte=start_of_week.day) &
             Q(birth_month__lte=end_of_week.month, birth_day__lte=end_of_week.day)) |
            (Q(wed_month__gte=start_of_week.month, wed_day__gte=start_of_week.day) &
             Q(wed_month__lte=end_of_week.month, wed_day__lte=end_of_week.day))
        )
        
        customers_nw = Customers.objects.annotate(
            birth_md=ConcatMonthDay('date_of_birth'),
            wed_md=ConcatMonthDay('date_of_wed')
        )
        
        start_md = f"{start_of_next_week.month}-{start_of_next_week.day}"
        end_md = f"{end_of_next_week.month}-{end_of_next_week.day}"

        # Filter customers for next week
        # customers_next_week = customers_nw.filter(
        #     (Q(birth_md__gte=start_md) & Q(birth_md__lte=end_md)) |
        #     (Q(wed_md__gte=start_md) & Q(wed_md__lte=end_md))
        # )
        customers_next_week = Customers.objects.filter(
            (Q(date_of_birth__month=start_of_next_week.month) & Q(date_of_birth__day__gte=start_of_next_week.day)) |
            (Q(date_of_wed__month=start_of_next_week.month) & Q(date_of_wed__day__gte=start_of_next_week.day)) |
            (Q(date_of_birth__month=end_of_next_week.month) & Q(date_of_birth__day__lte=end_of_next_week.day)) |
            (Q(date_of_wed__month=end_of_next_week.month) & Q(date_of_wed__day__lte=end_of_next_week.day))
        )
        # customers_next_week = customers.filter(
        #     (Q(birth_month__gte=start_of_next_week.month) & Q(birth_day__gte=start_of_next_week.day) & 
        #     Q(birth_month__lte=end_of_next_week.month) & Q(birth_day__lte=end_of_next_week.day)) |
        #     (Q(wed_month__gte=start_of_next_week.month) & Q(wed_day__gte=start_of_next_week.day) & 
        #     Q(wed_month__lte=end_of_next_week.month) & Q(wed_day__lte=end_of_next_week.day))
        # )

        
        customers_next_month = customers.filter(
            Q(birth_month=start_of_next_month.month) |
            Q(wed_month=start_of_next_month.month)
        )

        response_data = [
            {
                "name": "Today",
                "value": "1",
                "birthday": customers_today.filter(birth_month=today.month, birth_day=today.day).count(),
                "wedding": customers_today.filter(wed_month=today.month, wed_day=today.day).count(),
            },
            {
                "name": "Tomorrow",
                "value": "2",
                "birthday": customers_tomorrow.filter(birth_month=tomorrow.month, birth_day=tomorrow.day).count(),
                "wedding": customers_tomorrow.filter(wed_month=tomorrow.month, wed_day=tomorrow.day).count(),
            },
            {
                "name": "This week",
                "value": "3",
                "birthday": customers_this_week.filter(birth_month__gte=start_of_week.month, birth_day__gte=start_of_week.day).count(),
                "wedding": customers_this_week.filter(wed_month__gte=start_of_week.month, wed_day__gte=start_of_week.day).count(),
            },
            {
                "name": "Next week",
                "value": "4",
                "birthday": customers_next_week.filter(
                    Q(date_of_birth__month=start_of_next_week.month) & 
                    Q(date_of_birth__day__gte=start_of_next_week.day) |
                    Q(date_of_birth__month=end_of_next_week.month) & 
                    Q(date_of_birth__day__lte=end_of_next_week.day)
                ).count(),
                "wedding": customers_next_week.filter(
                    Q(date_of_wed__month=start_of_next_week.month) & 
                    Q(date_of_wed__day__gte=start_of_next_week.day) |
                    Q(date_of_wed__month=end_of_next_week.month) & 
                    Q(date_of_wed__day__lte=end_of_next_week.day)
                ).count(),
        },
            {
                "name": "Next month",
                "value": "5",
                "birthday": customers_next_month.filter(birth_month=start_of_next_month.month).count(),
                "wedding": customers_next_month.filter(wed_month=start_of_next_month.month).count(),
            },
        ]
        return Response(response_data, status=status.HTTP_200_OK)
    
class CustomerImpDatesListView(generics.GenericAPIView):
    permission_classes = [IsSuperuserOrEmployee]
    
    def post(self, request, *args, **kwargs):
        value = request.data['value']

        today = date.today()
        tomorrow = today + timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        # start_of_next_week = start_of_week + timedelta(weeks=1)
        # end_of_next_week = start_of_next_week + timedelta(days=6)
        start_of_next_week = today + timedelta(days=(7 - today.weekday()))  
        end_of_next_week = start_of_next_week + timedelta(days=6)  
        next_month = today.replace(day=1) + timedelta(days=32)
        start_of_next_month = next_month.replace(day=1)
        
        customers = Customers.objects.annotate(
            birth_month=ExtractMonth('date_of_birth'),
            birth_day=ExtractDay('date_of_birth'),
            wed_month=ExtractMonth('date_of_wed'),
            wed_day=ExtractDay('date_of_wed')
        )
        
        customers_list = customers.filter(
            (Q(birth_month=today.month) & Q(birth_day=today.day)) |
            (Q(wed_month=today.month) & Q(wed_day=today.day))
        )

        if value == 1:  
            customers_list = customers.filter(
            (Q(birth_month=today.month) & Q(birth_day=today.day)) |
            (Q(wed_month=today.month) & Q(wed_day=today.day))
        )
        elif value == 2: 
            customers_list = customers.filter(
            (Q(birth_month=tomorrow.month) & Q(birth_day=tomorrow.day)) |
            (Q(wed_month=tomorrow.month) & Q(wed_day=tomorrow.day))
        )
        elif value == 3:  
            customers_list = customers.filter(
            (Q(birth_month__gte=start_of_week.month, birth_day__gte=start_of_week.day) &
             Q(birth_month__lte=end_of_week.month, birth_day__lte=end_of_week.day)) |
            (Q(wed_month__gte=start_of_week.month, wed_day__gte=start_of_week.day) &
             Q(wed_month__lte=end_of_week.month, wed_day__lte=end_of_week.day))
        )  
        elif value == 4:  
            customers_list = Customers.objects.filter(
            (Q(date_of_birth__month=start_of_next_week.month) & Q(date_of_birth__day__gte=start_of_next_week.day)) |
            (Q(date_of_wed__month=start_of_next_week.month) & Q(date_of_wed__day__gte=start_of_next_week.day)) |
            (Q(date_of_birth__month=end_of_next_week.month) & Q(date_of_birth__day__lte=end_of_next_week.day)) |
            (Q(date_of_wed__month=end_of_next_week.month) & Q(date_of_wed__day__lte=end_of_next_week.day))
        ) 
        elif value == 5: 
            customers_list = customers.filter(
            Q(birth_month=start_of_next_month.month) |
            Q(wed_month=start_of_next_month.month)
        )

        # customers = Customers.objects.filter(
        #     date_of_birth__range=[start_date, end_date]
        # ) | Customers.objects.filter(
        #     date_of_wed__range=[start_date, end_date]
        # )
        customer_serializer = CustomerSerializer(customers_list, many=True, context={"request",request})
        response_data = []
        for customer in customer_serializer.data:
            instance = {}
            if(CustomerAddress.objects.filter(customer=customer['id_customer']).exists()):
                cus_address = CustomerAddress.objects.filter(customer=customer['id_customer']).get()
                area       = Area.objects.filter(id_area=cus_address.area.pk).get()
                city       = City.objects.filter(id_city=cus_address.city.pk).get()
                instance.update({"area":area.area_name})
                instance.update({"city":city.name})
            else:
                instance.update({"area":None})
                instance.update({"city":None})
            instance.update({
                "total_accounts":SchemeAccount.objects.filter(id_customer=customer['id_customer']).count(),
                "name": f"{customer['firstname']} {customer['lastname']}",
                "image": customer['cus_img'],
                "mobile": customer['mobile'],
                "email": customer['email'],
                "cus_id": customer['id_customer'],
                "birthday": format_date(customer['date_of_birth']) if customer['date_of_birth'] else None,
                "wedding": format_date(customer['date_of_wed']) if customer['date_of_wed'] else None,
            })
            if instance not in response_data:
                response_data.append(instance)
        return Response(response_data, status=status.HTTP_200_OK)

class NewUserDashView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        current_date = datetime.now().date()
        previous_7_days = []
        previous_7_days.append(current_date)
        for i in range(1, 7):
            previous_date = current_date - timedelta(days=i)
            previous_7_days.append(previous_date)
        
        output = []
        finoutput = {}
        yesterday = current_date - timedelta(days=1)
        print(yesterday)
        for date in previous_7_days:
            instance = {}
            queryset = Customers.objects.filter(custom_entry_date = date)
            serializer = CustomerSerializer(queryset, many=True)
            instance.update({"date":date, "count":len(serializer.data)})
            if instance not in output:
                output.append(instance)
        finoutput.update({"count":len(CustomerSerializer(Customers.objects.all(), many=True).data),
                          "data":output, "yesterday":len(CustomerSerializer(Customers.objects.filter(custom_entry_date = yesterday), many=True).data)})
        return Response(finoutput, status=status.HTTP_200_OK)
    
class AccountsDashView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        fin_op = []
        for sch_data in SchemeSerializer(Scheme.objects.all(), many=True).data:
            instance = {}
            instance.update({"scheme_name":sch_data['scheme_name']})
            amount = 0
            for acc_data in SchemeAccountSerializer(SchemeAccount.objects.filter(is_closed=False), many=True).data:
                # count = []
                if(sch_data['scheme_id'] == acc_data['acc_scheme_id']):
                    amount += 1
                    # count.append(acc_data['payment_amount'])
                instance.update({"scheme_name":sch_data['scheme_name'], "sch_id":sch_data['scheme_id'], "amount":amount})
                if instance not in output:
                    output.append(instance)
            amount = 0
        fin_op.append({"accounts_data":output, "total_accounts": len(SchemeAccountSerializer(SchemeAccount.objects.filter(is_closed=False), many=True).data)})
        return Response(fin_op, status=status.HTTP_200_OK)
    
class CustomerDashView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        finoutput = {}
        reg_data = [
            {"id":1, "name":"Web App"},
            {"id":2, "name":"Admin"},
            {"id":3, "name":"Mobile App"},
            {"id":4, "name":"Collection App"},
        ]
        for re_data in reg_data:
            instance = {}
            instance.update({"mode_name":re_data['name']})
            amount = 0
            for cus_data in CustomerSerializer(Customers.objects.all(), many=True).data:
                
                if(cus_data['registered_through'] == re_data['id']):
                    amount += 1
                instance.update({ "mode_name":re_data['name'], "amount":amount})
                if instance not in output:
                    output.append(instance)
            amount = 0
        
        without_acc = []
        intersted_acc = []
        for customer in CustomerSerializer(Customers.objects.all(), many=True).data:
            for sch_acc in SchemeAccountSerializer(SchemeAccount.objects.all(), many=True).data:
                if (sch_acc['id_customer'] == customer['id_customer']):
                    if(sch_acc['scheme_acc_number'] != None):
                         without_acc.append(customer)
            if(customer['is_email_verified']== False):
                intersted_acc.append(customer)
        finoutput.update({"reg_data":output, "without_acc":len(without_acc), "intersted_acc":len(intersted_acc)})
        return Response(finoutput, status=status.HTTP_200_OK)


class CustomerRegistrationDetailView(generics.GenericAPIView):
    permission_classes = [IsEmployee] 
    
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        six_months_ago = today - timedelta(days=6*30)
        customers_last_six_months = Customers.objects.filter(custom_entry_date__gte=six_months_ago)
        customers_by_month = customers_last_six_months.values('custom_entry_date__year', 'custom_entry_date__month') \
                            .annotate(customer_count=Count('id_customer')) \
                            .order_by('custom_entry_date__year', 'custom_entry_date__month')

        months_data = defaultdict(int)
        registered_customers = []
        months = []

        for entry in customers_by_month:
            year = entry['custom_entry_date__year']
            month_num = entry['custom_entry_date__month']
            customer_count = entry['customer_count']
            months_data[(year, month_num)] = customer_count

        for i in range(5, -1, -1):
            past_date = today - timedelta(days=i * 30)
            year = past_date.year
            month_num = past_date.month
            month_name = calendar.month_abbr[month_num]
            months.append(month_name)
            registered_customers.append(months_data.get((year, month_num), 0))

        output = {
            "registered_customers": registered_customers,
            "months": months
        }
        return Response(output, status=status.HTTP_200_OK)
    
class OrderDetailsView(generics.GenericAPIView):
    permission_classes = [IsEmployee] 
    
    def get(self, request, *args, **kwargs):
        today = datetime.now().date()
        six_months_ago = today - timedelta(days=180)

        orders = (
            ERPOrder.objects.filter(order_date__gte=six_months_ago)
            .annotate(month=TruncMonth('order_date'))
            .values('month')
            .annotate(order_count=Count('order_id'))
            .order_by('month')
        )

        order_counts = []
        months = []
        
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }

        for order in orders:
            order_counts.append(order['order_count'])
            months.append(month_names[order['month'].month])

        current_month = today.month
        for i in range(6):
            month_name = month_names[(current_month - i - 1) % 12 + 1]
            if month_name not in months:
                months.insert(0, month_name)
                order_counts.insert(0, 0)

        output = {
            "orders": order_counts,
            "months": months
        }

        return Response(output, status=status.HTTP_200_OK)


class PaymentSummaryView(generics.GenericAPIView):
    permission_classes = [IsEmployee] 
    
    def get(self, request, *args, **kwargs):
        filter_option = request.query_params.get('filter', '1')  

        now = make_aware(datetime.now())

        if filter_option == '2':
            start_date = now - timedelta(days=now.weekday())  
        elif filter_option == '3':
            first_day_of_current_month = now.replace(day=1)
            start_date = first_day_of_current_month - timedelta(days=1)
            start_date = start_date.replace(day=1)
        elif filter_option == '4':
            start_date = now
            # end_date = now
        elif filter_option == '5':
            start_date = now - timedelta(days=1)  
        else:  # Default is 'This Month'
            start_date = now.replace(day=1)  

        payments = Payment.objects.filter(date_payment__gte=start_date, date_payment__lte=now)
        total_schemes = SchemeAccount.objects.filter(is_closed=0).count()
        amount = payments.aggregate(total_amount=Sum('payment_amount'))['total_amount'] or 0
        rate = payments.aggregate(avg_rate=Avg('metal_rate'))['avg_rate'] or 0
        coverup_positions = SchemeAccount.objects.filter(is_closed=False).count()

        output = {
            "total_schemes": total_schemes,
            "amount": amount,
            "rate": rate,
            "coverup": float(amount/rate) if rate > 0 else 0  # Avoid division by zero
        }

        return Response(output, status=status.HTTP_200_OK)

class PaymentThroughView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        reg_data = [
            {"id":1, "name":"Admin", "colour":"#b643ff"},
            {"id":2, "name":"Mobile App", "colour":"#b5acff"},
            {"id":3, "name":"Collection App", "colour":"#f5db7b"},
        ]
        filter_option = request.query_params.get('filter', '1')  

        now = make_aware(datetime.now())

        if filter_option == '2':
            start_date = now - timedelta(days=now.weekday())  
        elif filter_option == '3':
            first_day_of_current_month = now.replace(day=1)
            start_date = first_day_of_current_month - timedelta(days=1)
            start_date = start_date.replace(day=1)
        elif filter_option == '4':
            start_date = now
            # end_date = now
        elif filter_option == '5':
            start_date = now - timedelta(days=1) 
        else: 
            start_date = now.replace(day=1)
            
        queryset = Payment.objects.filter(date_payment__gte=start_date,date_payment__lte=now)
        # queryset = Payment.objects.all()
        # if (request.query_params['days'] != 'undefined'):
        #     from_date = get_past_date(int(request.query_params['days']))
        #     to_date = date.today()
        #     queryset = Payment.objects.filter(date_payment__lte=to_date, date_payment__gte=from_date)
        serializer = PaymentSerializer(queryset, many=True)
        for re_data in reg_data:
            instance = {}
            instance.update({"mode_name":re_data['name']})
            amount = 0
            weight = 0
            for data in serializer.data:
                if(data['paid_through'] == re_data['id']):
                    amount += float(data['payment_amount'])
                    weight += float(data['metal_weight'])
                instance.update({ "mode_name":re_data['name'], "amount":round(amount,2), "weight":round(weight,3), "colour":re_data['colour']})
                if instance not in output:
                    output.append(instance)
            amount = 0
            weight = 0
        return Response(output, status=status.HTTP_200_OK)
    
class PaymentModeView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        mode_queryset = PaymentMode.objects.filter(is_active=True)
        mode_serializer = PaymentModeSerializer(mode_queryset, many=True)
        queryset = Payment.objects.filter(payment_status=1)
        if (request.query_params['days'] != 'undefined'):
            from_date = get_past_date(int(request.query_params['days']))
            to_date = date.today()
            queryset = Payment.objects.filter(date_payment__lte=to_date, date_payment__gte=from_date, payment_status=1)
        serializer = PaymentSerializer(queryset, many=True)
        for mode in mode_serializer.data:
            amount = 0
            for data in serializer.data:
                payment_detail = PaymentModeDetail.objects.filter(id_pay=data['id_payment'])
                payment_detail_serializer = PaymentModeDetailSerializer(payment_detail, many=True)
                for detail in payment_detail_serializer.data:
                    instance = {}
                    if(detail['payment_mode'] == mode['id_mode']):
                        amount += float(detail['payment_amount'])
            if (amount != 0):
                instance.update({ "mode_name":mode['mode_name'], "amount":amount})
            if instance != {} and instance not in output:
                output.append(instance)
            amount = 0
        return Response(output, status=status.HTTP_200_OK)
    
    
class PaymentStatusView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        queryset = Payment.objects.filter(paid_through=2)
        if (request.query_params['days'] != 'undefined'):
            from_date = get_past_date(int(request.query_params['days']))
            to_date = date.today()
            queryset = Payment.objects.filter(date_payment__lte=to_date, date_payment__gte=from_date)
        serializer = PaymentSerializer(queryset, many=True)
        status_queryset = PaymentStatus.objects.all()
        status_serializer = PaymentStatusSerializer(status_queryset, many=True)
        for statu in status_serializer.data:
            instance = {}
            count = 0
            for data in serializer.data:
                instance = {}
                if(statu['id'] == data['payment_status']):
                    count +=1
            if (count != 0):
                instance.update({ "name":statu['name'], "count":count})
            if instance != {} and instance not in output:
                output.append(instance)
            count = 0
        return Response(output, status=status.HTTP_200_OK)
    
class ActiveChitsView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        filter_option = request.query_params.get('filter', '1')  

        now = make_aware(datetime.now())

        if filter_option == '2':
            start_date = now - timedelta(days=now.weekday())  
        elif filter_option == '3':
            first_day_of_current_month = now.replace(day=1)
            start_date = first_day_of_current_month - timedelta(days=1)
            start_date = start_date.replace(day=1) 
        elif filter_option == '4':
            start_date = now
            # end_date = now
        elif filter_option == '5':
            start_date = now - timedelta(days=1) 
        else: 
            start_date = now.replace(day=1)  

        queryset = SchemeAccount.objects.filter(is_closed=False)
        serializer = SchemeAccountSerializer(queryset, many=True)
        weight = 0
        amount = 0
        bonus = 0
        instance = {}

        for data in serializer.data:
            payment_detail = Payment.objects.filter(
                id_scheme_account=data['id_scheme_account'],
                date_payment__gte=start_date,
                date_payment__lte=now 
            )
            payment_detail_serializer = PaymentSerializer(payment_detail, many=True)
            for detail in payment_detail_serializer.data:
                amount += float(detail['payment_amount'])
                weight += float(detail['metal_weight'])
                bonus += float(detail['discountAmt'])

        instance.update({
            "accounts": len(serializer.data), 
            "amount": round(amount,2),
            "weight": round(weight,3), 
            "bonus": bonus
        })

        return Response(instance, status=status.HTTP_200_OK)
    
class MaturedandUnclaimedChitsView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        queryset = SchemeAccount.objects.filter(is_closed=True, is_utilized=False)
        serializer = SchemeAccountSerializer(queryset, many=True)
        weight = 0
        amount = 0
        bonus = 0
        instance = {}
        for data in serializer.data:
            payment_detail = Payment.objects.filter(id_scheme_account=data['id_scheme_account'])
            payment_detail_serializer = PaymentSerializer(payment_detail, many=True)
            for detail in payment_detail_serializer.data:
                amount += float(detail['payment_amount'])
                weight += float(detail['metal_weight'])
                bonus += float(detail['discountAmt'])
        instance.update({"accounts":len(serializer.data), "amount":round(amount, 2),"weight":round(weight, 3), "bonus":round(bonus,2)})
        return Response(instance, status=status.HTTP_200_OK)

class ChitClosingDetailsView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, format=None):
        today = date.today()
        one_month_later = today + timedelta(days=30)
        two_months_later = today + timedelta(days=60)

        matured_accounts = SchemeAccount.objects.filter(is_closed=True) 
        one_month_accounts = SchemeAccount.objects.filter(is_closed=False, closing_date__lte=one_month_later)
        two_months_accounts = SchemeAccount.objects.filter(is_closed=False, closing_date__gt=one_month_later, closing_date__lte=two_months_later)
        renewals_pending_accounts = SchemeAccount.objects.filter(is_closed=False, closing_date__isnull=True)  # No closing date set

        def aggregate_data(scheme_accounts):
            account_count = scheme_accounts.count()
            total_benefit = sum([account.closing_benefits or 0 for account in scheme_accounts])
            total_weight = sum([account.closing_weight or 0 for account in scheme_accounts])
            total_weight_benefit = total_weight 
            return {
                "account": account_count,
                "benefit": total_benefit,
                "weight": total_weight,
                "weight_benefit": total_weight_benefit
            }

        output = [
            {
                "name": "Matured",
                **aggregate_data(matured_accounts)
            },
            {
                "name": "One Month",
                **aggregate_data(one_month_accounts)
            },
            {
                "name": "Two Months",
                **aggregate_data(two_months_accounts)
            },
            {
                "name": "Renewals Pending",
                **aggregate_data(renewals_pending_accounts)
            },
        ]
        return Response(output, status=status.HTTP_200_OK)
    
class InActiveChits(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []

        today = date.today()
        two_months_ago = today - timedelta(days=60)
        four_months_ago = today - timedelta(days=120)
        six_months_ago = today - timedelta(days=180)

        # Fetch all schemes
        schemes = Scheme.objects.all()

        for scheme in schemes:
            greater_than_two = SchemeAccount.objects.filter(
                acc_scheme_id=scheme, 
                is_closed=True,
                start_date__lte=two_months_ago
            ).count()
            
            greater_than_four = SchemeAccount.objects.filter(
                acc_scheme_id=scheme, 
                is_closed=True,
                start_date__lte=four_months_ago
            ).count()

            greater_than_six = SchemeAccount.objects.filter(
                acc_scheme_id=scheme, 
                is_closed=True,
                start_date__lte=six_months_ago
            ).count()

            output.append({
                "scheme_name": scheme.scheme_name,
                "greater_than_two": greater_than_two,
                "greater_than_four": greater_than_four,
                "greater_than_six": greater_than_six
            })

        return Response(output, status=status.HTTP_200_OK)


class UsersJoinedThrough(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        device_data = [
            {"id":1, "name":"Admin App", "colour":"#b643ff", "icon_name":"monitor"},
            {"id":2, "name":"Mobile App", "colour":"#b5acff",  "icon_name":"mobile"},
            {"id":3, "name":"Collection App", "colour":"#f5db7b",  "icon_name":"tablet"},
        ]
        queryset = Customers.objects.filter(active=True)
        if (request.query_params['days'] != 'undefined'):
            from_date = get_past_date(int(request.query_params['days']))
            to_date = date.today()
            queryset = Customers.objects.filter(custom_entry_date__lte=to_date, 
                                                custom_entry_date__gte=from_date, active=True)
        serializer = CustomerSerializer(queryset, many=True)
        for device in device_data:
            instance = {}
            count = 0
            for data in serializer.data:
                if(data['registered_through'] == device['id']):
                    count += 1
                instance.update({ "mode_name":device['name'], "count":count, "colour":device['colour']})
                if instance not in output:
                    output.append(instance)
            count = 0
        return Response(output, status=status.HTTP_200_OK)

class RegisteredThrough(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        filter_option = request.query_params.get('filter', '1') 

        # Get the current date
        today = make_aware(datetime.now())
        

        if filter_option == '2':
            start_date = today - timedelta(days=today.weekday())  
        elif filter_option == '3':
            first_day_of_current_month = today.replace(day=1)
            start_date = first_day_of_current_month - timedelta(days=1)  
            start_date = start_date.replace(day=1)
        elif filter_option == '4':
            start_date = today
        elif filter_option == '5':
            start_date = today - timedelta(days=1)   
        else: 
            start_date = today.replace(day=1)  

        one_month_ago = today - timedelta(days=30)
        two_months_ago = today - timedelta(days=60)
        six_months_ago = today - timedelta(days=180)
        one_year_ago = today - timedelta(days=365)

        device_data = [
            {"id": 1, "name": "Admin App", "icon_name": "monitor"},
            {"id": 2, "name": "Mobile App", "icon_name": "mobile"},
            {"id": 3, "name": "Web App", "icon_name": "web"},
            {"id": 4, "name": "Collection App", "icon_name": "tablet"},
            {"id": 5, "name": "Marketing App", "icon_name": "campaign"},
        ]

        def get_count_for_range(device_id, from_date, to_date):
            return Customers.objects.filter(
                registered_through=device_id, 
                custom_entry_date__lte=to_date, 
                custom_entry_date__gte=from_date,
                active=True
            ).count()

        output = []
        for device in device_data:
            instance = {
                "name": device['name'],
                "this_month": get_count_for_range(device['id'], start_date, today),  # Based on selected filter
                "two_months_above": get_count_for_range(device['id'], two_months_ago, one_month_ago),
                "six_months_above": get_count_for_range(device['id'], six_months_ago, two_months_ago),
                "one_year_above": get_count_for_range(device['id'], one_year_ago, six_months_ago),
            }
            output.append(instance)

        return Response(output, status=status.HTTP_200_OK)
    
class SchemeWiseJoinedView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        scheme_queryset = Scheme.objects.filter(status=True)
        scheme_serializer = SchemeSerializer(scheme_queryset, many=True)
        queryset = SchemeAccount.objects.filter(is_closed=False)
        if (request.query_params['days'] != 'undefined'):
            from_date = get_past_date(int(request.query_params['days']))
            to_date = date.today()
            queryset = SchemeAccount.objects.filter(start_date__lte=to_date, 
                                                start_date__gte=from_date, is_closed=False)
        serializer = SchemeAccountSerializer(queryset, many=True)
        for scheme in scheme_serializer.data:
            instance = {}
            count = 0
            for data in serializer.data:
                if(scheme['scheme_id'] == data['acc_scheme_id']):
                    count +=1
            # if (count != 0):
            #     instance.update({ "name":scheme['scheme_name'], "count":count})
            instance.update({ "name":scheme['scheme_name'],"shortcode":scheme['scheme_code'], "count":count})
            if instance != {} and instance not in output:
                output.append(instance)
            count = 0
        return Response(output, status=status.HTTP_200_OK)
    
class SchemeWiseClosedView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        scheme_queryset = Scheme.objects.filter(status=True)
        scheme_serializer = SchemeSerializer(scheme_queryset, many=True)
        queryset = SchemeAccount.objects.filter(is_closed=True)
        if (request.query_params['days'] != 'undefined'):
            from_date = get_past_date(int(request.query_params['days']))
            to_date = date.today()
            queryset = SchemeAccount.objects.filter(closing_date__lte=to_date, 
                                                closing_date__gte=from_date, is_closed=True)
        serializer = SchemeAccountSerializer(queryset, many=True)
        for scheme in scheme_serializer.data:
            instance = {}
            count = 0
            for data in serializer.data:
                if(scheme['scheme_id'] == data['acc_scheme_id']):
                    count +=1
            if (count != 0):
                instance.update({ "name":scheme['scheme_name'], "count":count})
            if instance != {} and instance not in output:
                output.append(instance)
            count = 0
        return Response(output, status=status.HTTP_200_OK)
    
class BranchWiseJoinedView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        branch_queryset = Branch.objects.filter(active=True)
        branch_serializer = BranchSerializer(branch_queryset, many=True)
        queryset = SchemeAccount.objects.filter(is_closed=False)
        if (request.query_params['days'] != 'undefined'):
            from_date = get_past_date(int(request.query_params['days']))
            to_date = date.today()
            queryset = SchemeAccount.objects.filter(start_date__lte=to_date, 
                                                start_date__gte=from_date, is_closed=False)
        serializer = SchemeAccountSerializer(queryset, many=True)
        for branch in branch_serializer.data:
            instance = {}
            count = 0
            for data in serializer.data:
                if(branch['id_branch'] == data['id_branch']):
                    count +=1
            # if (count != 0):
            #     instance.update({ "name":branch['name'], "count":count})
            instance.update({ "name":branch['name'], "count":count})
            if instance != {} and instance not in output:
                output.append(instance)
            count = 0
        return Response(output, status=status.HTTP_200_OK)
    
class BranchWiseClosedView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        branch_queryset = Branch.objects.filter(active=True)
        branch_serializer = BranchSerializer(branch_queryset, many=True)
        queryset = SchemeAccount.objects.filter(is_closed=True)
        if (request.query_params['days'] != 'undefined'):
            from_date = get_past_date(int(request.query_params['days']))
            to_date = date.today()
            queryset = SchemeAccount.objects.filter(closing_date__lte=to_date, 
                                                closing_date__gte=from_date, is_closed=True)
        serializer = SchemeAccountSerializer(queryset, many=True)
        for branch in branch_serializer.data:
            instance = {}
            count = 0
            for data in serializer.data:
                if(branch['id_branch'] == data['id_branch']):
                    count +=1
            if (count != 0):
                instance.update({ "name":branch['name'], "count":count})
            if instance != {} and instance not in output:
                output.append(instance)
            count = 0
        return Response(output, status=status.HTTP_200_OK)
    
class UserByAreasView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(swelf, request, *args, **kwargs):
        output = []
        area_query = Area.objects.filter(is_active=True)
        area_serializer = AreaSerializer(area_query, many=True)
        scheme_paid_class   = SchemeAccountPaidDetails()
        for area in area_serializer.data:
            address_query = CustomerAddress.objects.filter(area=area['id_area'])
            address_serializer = CustomerAddressSerializer(address_query, many=True)
            count = 0
            instance = {}
            for address in address_serializer.data:
                if (area['id_area'] == address['area']):
                    count +=1
                if (count != 0):
                    instance.update({ "area":area['area_name'], "customers":count})
                account_query = SchemeAccount.objects.filter(id_customer=address['customer'])
                account_serializer = SchemeAccountSerializer(account_query, many=True)
                weight = 0
                amount = 0
                for account in account_serializer.data:
                    paid_details        = scheme_paid_class.get_scheme_account_paid_details(account['id_scheme_account'])
                    weight += float(paid_details['total_paid_weight'])
                    amount += float(paid_details['total_paid_amount'])
                    instance.update({ "area":area['area_name'], "customers":count, "amount":amount, "weight":weight})
                
                if instance != {} and instance not in output:
                    output.append(instance)
                weight = 0
                amount = 0
            count = 0
        return Response(output, status=status.HTTP_200_OK)
    
class ActiveCustomersView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)

class ActiveChitsReportsView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        filter_option = request.query_params.get('filter', '1')  

        now = make_aware(datetime.now())

        from_date,to_date = get_past_date(int(filter_option)) 

        queryset = SchemeAccount.objects.filter(is_closed=False)
        serializer = SchemeAccountSerializer(queryset, many=True)
        output = []
        for data in serializer.data:
            weight = 0
            amount = 0
            bonus = 0
            instance = {}
            customer = Customers.objects.filter(id_customer=data['id_customer']).first()
            scheme = Scheme.objects.filter(scheme_id=data['acc_scheme_id']).first()
            payment_detail = Payment.objects.filter(
                id_scheme_account=data['id_scheme_account'],
                date_payment__gte=from_date,
                date_payment__lte=now 
            )
            payment_detail_serializer = PaymentSerializer(payment_detail, many=True)
            for detail in payment_detail_serializer.data:
                amount += float(detail['payment_amount'])
                weight += float(detail['metal_weight'])
                bonus += float(detail['discountAmt'])

            instance.update({
                "scheme_account" : data['account_name'],
                "customer_name":customer.firstname,
                "scheme_name":scheme.scheme_name,
                "amount": amount,
                "weight": weight, 
                "bonus": bonus
            })
            if instance not in output:
                output.append(instance)
        return Response({"data":output,"column":ACTIVE_CHITS_COLUMN_LIST}, status=status.HTTP_200_OK)


class MaturedandUnclaimedChitsReportView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        queryset = SchemeAccount.objects.filter(is_closed=True, is_utilized=False)
        serializer = SchemeAccountSerializer(queryset, many=True)
        output = []
        for data in serializer.data:
            weight = 0
            amount = 0
            bonus = 0
            instance = {}
            customer = Customers.objects.filter(id_customer=data['id_customer']).first()
            scheme = Scheme.objects.filter(scheme_id=data['acc_scheme_id']).first()
            payment_detail = Payment.objects.filter(id_scheme_account=data['id_scheme_account'])
            payment_detail_serializer = PaymentSerializer(payment_detail, many=True)
            for detail in payment_detail_serializer.data:
                amount += float(detail['payment_amount'])
                weight += float(detail['metal_weight'])
                bonus += float(detail['discountAmt'])
            instance.update({
                "scheme_account" : data['account_name'],
                "customer_name":customer.firstname,
                "scheme_name":scheme.scheme_name,
                "amount": amount,
                "weight": weight, 
                "bonus": bonus
            })
            if instance not in output:
                output.append(instance)
        return Response({"data":output,"column":MATURED_AND_UNCLAIMED_CHITS_COLUMN_LIST}, status=status.HTTP_200_OK)

class PaymentSummaryReportView(generics.GenericAPIView):
    permission_classes = [IsEmployee] 
    
    def get(self, request, *args, **kwargs):
        filter_option = request.query_params.get('filter', '1')  
        now = make_aware(datetime.now())
        from_date,to_date = get_past_date(int(filter_option)) 
        schemes = Scheme.objects.all()
        scheme_serializer = SchemeSerializer(schemes, many=True)
        output = []
        for data in scheme_serializer.data:
            instance = {}
            payments = Payment.objects.filter(date_payment_gte=from_date, date_payment_lte=now,
                                              id_scheme=data['scheme_id'])
            amount = payments.aggregate(total_amount=Sum('payment_amount'))['total_amount'] or 0
            rate = payments.aggregate(avg_rate=Avg('metal_rate'))['avg_rate'] or 0
            coverup_positions = SchemeAccount.objects.filter(acc_scheme_id=data['scheme_id'], is_closed=False).count()
            instance.update({"scheme_name":data['scheme_name'],"amount": amount,         
                            "rate": rate,
                            "coverup": float(amount/rate) if rate > 0 else 0})
            if instance not in output:
                output.append(instance)
        return Response({"data":output,"column":PAYMENT_SUMMARY_COLUMN_LIST}, status=status.HTTP_200_OK)
    
class AdminAppDashboardDatas(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        today = date.today()
        
        yet_to_approve = Customers.objects.filter(catalogue_req_status=1).count()
        approved_customers = Customers.objects.filter(catalogue_req_status=2).count()
        rejected_customers = Customers.objects.filter(approved_status=3).count()
        non_assigned_orders_count = ERPOrderDetails.objects.filter(order_status__in=[1]).count()
        work_in_progress_count = ErpJobOrderDetails.objects.filter(status=3).count()
        delivery_ready_count = ERPOrderDetails.objects.filter(order_status=4).count()
        cad_yet_to_assign = ERPOrderDetails.objects.filter(internal_order_process=1).count()
        cad_work_in_progress = ERPOrderDetails.objects.filter(internal_order_process=2).count()
        cam_yet_assign = ERPOrderDetails.objects.filter(internal_order_process=3).count()
        cam_work_in_progress = ERPOrderDetails.objects.filter(internal_order_process=4).count()
        production_yet_to_assign = ERPOrderDetails.objects.filter(internal_order_process=5).count()
        production_in_progress = ERPOrderDetails.objects.filter(internal_order_process=6).count()
        overdue_count = ErpJobOrderDetails.objects.filter(status=3,due_date__lt=today).count()
        customer_overdue_count = ERPOrderDetails.objects.filter(order_status=3,customer_due_date__lt=today).count()
        tag_without_images = 0

        taggings = ErpTagging.objects.annotate(image_count=Count('erptaggingimages'))
        for tagging in taggings:
            if tagging.image_count == 0:
                tag_without_images += 1
        
        data = {
            "yet_to_approve_customers":yet_to_approve,
            "approved_customers":approved_customers,
            "rejected_customers":rejected_customers,
            "non_assigned_orders_count":non_assigned_orders_count,
            "work_in_progress_orders_count":work_in_progress_count,
            "delivery_ready_orders_count":delivery_ready_count,
            "overdue_orders_count":overdue_count,
            "customer_overdue_count":customer_overdue_count,
            "cad_yet_to_assign":cad_yet_to_assign,
            "cad_work_in_progress":cad_work_in_progress,
            "cam_yet_assign":cam_yet_assign,
            "cam_work_in_progress":cam_work_in_progress,
            "production_yet_to_assign":production_yet_to_assign,
            "production_in_progress":production_in_progress,
            "tag_without_images":tag_without_images

        }
        return Response({"data":data}, status=status.HTTP_200_OK)
    
# Purches Order Dashboard for Rate Cut
class SupplierRateCutList(APIView):
    def post(self, request):
        days_type = request.data.get('days', None)
        if not days_type:
            return Response({"error": "days type is required"}, status=status.HTTP_400_BAD_REQUEST)

        start_date, end_date = get_date_range_from_days_type(days_type)
        if not start_date or not end_date:
          return Response({"error": "Invalid days type"}, status=status.HTTP_400_BAD_REQUEST)

        # Static IDs for now — adjust as needed
        id_supplier = 2
        id_metal = 1
        bill_setting_type = 1
        supplier = get_object_or_404(Supplier, id_supplier=id_supplier)
        supplier_payment = ErpSupplierPaymentCreateAPIView()
        result = supplier_payment.get_payment_details(id_supplier, id_metal, bill_setting_type)
        filtered = []
        for entry in result:
            entry_date = entry['entry_date']
            if start_date <= entry_date <= end_date:
                filtered.append({
                    'supplier_name': supplier.supplier_name,
                    'ref_no': entry['ref_no'],
                    # 'entry_date': entry['entry_date'],
                    'payment_date': entry['payment_date'],
                    'metal_name': entry['metal_name'],
                    'balance_amount': entry['balance_amount'],
                })

        return Response(filtered, status=status.HTTP_200_OK)

# Dashboard Slipper Details List
class SupllierPurchaseEntryDetailsList(APIView):
    def post(self, request):
        days_type = request.data.get('days', None)
        if not days_type:
            return Response({"error": "days type is required"}, status=status.HTTP_400_BAD_REQUEST)

        start_date, end_date = get_date_range_from_days_type(days_type)
        if not start_date or not end_date:
          return Response({"error": "Invalid days type"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = (
            ErpPurchaseEntryDetails.objects
            .select_related('purchase_entry__id_supplier', 'id_product__id_metal')
            .filter(purchase_entry__entry_date__range=[start_date, end_date])
            .values('purchase_entry__id_supplier__supplier_name', 'id_product__id_metal__metal_name')
            .annotate(
                gross_wt_sum=Sum('gross_wt'),
                pure_wt_sum=Sum('pure_wt')
            )
        )
        result = [
            {
                'supplier_name': item['purchase_entry__id_supplier__supplier_name'],
                'metal_name': item['id_product__id_metal__metal_name'],
                'gross_wt': round(item['gross_wt_sum'], 3) if item['gross_wt_sum'] else 0,
                'pure_wt': round(item['pure_wt_sum'], 3) if item['pure_wt_sum'] else 0
            }
            for item in queryset
        ]
        return Response(result, status=status.HTTP_200_OK)

class PurchaseDetailList(APIView):
    def post(self, request):
        days_type = request.data.get('days', None)
        if not days_type:
            return Response({"error": "days type is required"}, status=status.HTTP_400_BAD_REQUEST)

        start_date, end_date = get_date_range_from_days_type(days_type)
        if not start_date or not end_date:
          return Response({"error": "Invalid days type"}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = (
            ErpPurchaseEntryDetails.objects
            .select_related('purchase_entry', 'id_product__id_metal')
            .filter(purchase_entry__entry_date__range=[start_date, end_date])
            .values('id_purchase_entry_detail', 'gross_wt', 'pure_wt', 'id_product__id_metal__metal_name')
        )
        result = [
            {
                'id_purchase_entry_detail': item['id_purchase_entry_detail'],
                'gross_wt': round(item['gross_wt'], 3) if item['gross_wt'] else 0,
                'pure_wt': round(item['pure_wt'], 3) if item['pure_wt'] else 0,
                'metal_name': item['id_product__id_metal__metal_name'],
            }
            for item in queryset
        ]
        # Return the response with serialized data
        return Response(result, status=status.HTTP_200_OK)


class BranchWiseCollectionView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        filter_option = request.query_params.get('filter', '1')  

        now = make_aware(datetime.now())

        if filter_option == '2':
            start_date = now - timedelta(days=now.weekday())  
        elif filter_option == '3':
            first_day_of_current_month = now.replace(day=1)
            start_date = first_day_of_current_month - timedelta(days=1)
            start_date = start_date.replace(day=1)
        elif filter_option == '4':
            start_date = now
            # end_date = now
        elif filter_option == '5':
            start_date = now - timedelta(days=1)  
        else:  # Default is 'This Month'
            start_date = now.replace(day=1) 
        
        opening_date = start_date - timedelta(days=1)

        def safe_amount_decimal(val, dp=2):
            return round(val or Decimal('0.00'), dp)
        
        def safe_weight_decimal(val, dp=3):
            return Decimal(val or Decimal('0.000'))

        
        opening_qs = Payment.objects.filter(date_payment__lte=opening_date).values('id_branch').annotate(
            amount=Sum('payment_amount'),
            weight=Sum(ExpressionWrapper(F('metal_weight') + F('bonus_metal_weight'), output_field=DecimalField(max_digits=10, decimal_places=3)))
        )

        
        collection_qs = Payment.objects.filter(date_payment__range=[start_date, now]).values('id_branch').annotate(
            amount=Sum('payment_amount'),
            weight=Sum(ExpressionWrapper(F('metal_weight') + F('bonus_metal_weight'), output_field=DecimalField(max_digits=10, decimal_places=3)))
        )

        
        closing_qs = SchemeAccount.objects.filter(closing_date__range=[start_date, now]).values('id_branch').annotate(
            amount=Sum('closing_amount'),
            weight=Sum('closing_weight')
        )

        
        opening_data = {entry['id_branch']: entry for entry in opening_qs}
        collection_data = {entry['id_branch']: entry for entry in collection_qs}
        closing_data = {entry['id_branch']: entry for entry in closing_qs}
        # closing_data = {
        #     item['id_branch']: {
        #         'amount': (item['amount'] or Decimal('0.00')).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
        #         'weight': (item['weight'] or Decimal('0.000')).quantize(Decimal('0.000'), rounding=ROUND_HALF_UP)
        #     }
        #     for item in closing_qs
        # }

        
        all_branch_ids = set(opening_data.keys()) | set(collection_data.keys()) | set(closing_data.keys())

        
        branch_names = Branch.objects.filter(id_branch__in=all_branch_ids).values('id_branch', 'name')
        branch_name_map = {b['id_branch']: b['name'] for b in branch_names}

       
        branch_summary = []

        for branch_id in all_branch_ids:
            opening = opening_data.get(branch_id, {})
            collection = collection_data.get(branch_id, {})
            closing = closing_data.get(branch_id, {})

            opening_amt = safe_amount_decimal(opening.get('amount'), 2)
            opening_wt = safe_weight_decimal(opening.get('weight'), 3)

            collection_amt = safe_amount_decimal(collection.get('amount'), 2)
            collection_wt = safe_weight_decimal(collection.get('weight'), 3)

            closing_amt = safe_amount_decimal(closing.get('amount'), 2)
            closing_wt = safe_weight_decimal(closing.get('weight'), 3)

            branch_summary.append({
                'branchId': branch_id,
                'branchName': branch_name_map.get(branch_id, "Unknown Branch"),
                'opening': {
                    'amount': opening_amt,
                    'weight': opening_wt
                },
                'collection': {
                    'amount': collection_amt,
                    'weight': collection_wt
                },
                'closing': {
                    'amount': closing_amt,
                    'weight': closing_wt
                },
                'available': {
                    'amount': safe_amount_decimal((opening_amt + collection_amt - closing_amt), 2),
                    'weight': safe_weight_decimal((opening_wt + collection_wt - closing_wt), 3)
                }
            })

        return Response(branch_summary, status=status.HTTP_200_OK)

class DigiGoldDashboardSummaryView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        filter_option = request.query_params.get('filter', '1')  
        now = make_aware(datetime.now())
        from_date,to_date = get_past_date(int(filter_option)) 
        
        digi_accounts = SchemeAccount.objects.filter(acc_scheme_id__scheme_type=2)
        customers_query = Customers.objects.all()
        
        payments_query = Payment.objects.filter(id_scheme__scheme_type=2)
        filtered_payments_query = Payment.objects.filter(date_payment__lte=to_date, date_payment__gte=from_date, id_scheme__scheme_type=2)
        
        digi_customer_ids = digi_accounts.values_list('id_customer', flat=True).distinct()
        digi_customers_count = digi_customer_ids.count()
        
        total_payment_amount = payments_query.aggregate(total=Sum('payment_amount'))['total'] or Decimal('0.00')
        
        total_gold_paid_weight = payments_query.filter(id_scheme__sch_id_metal=1).aggregate(
            total=Sum('metal_weight'))['total'] or Decimal('0.000')
        total_gold_bonus_weight = payments_query.filter(id_scheme__sch_id_metal=1).aggregate(
            total=Sum('bonus_metal_weight'))['total'] or Decimal('0.000')
        
        total_silver_paid_weight = payments_query.filter(id_scheme__sch_id_metal=2).aggregate(
            total=Sum('metal_weight'))['total'] or Decimal('0.000')
        total_silver_bonus_weight = payments_query.filter(id_scheme__sch_id_metal=2).aggregate(
            total=Sum('bonus_metal_weight'))['total'] or Decimal('0.000')
        
        total_payment_amount_filtered = filtered_payments_query.aggregate(total=Sum('payment_amount'))['total'] or Decimal('0.00')
        instance = {
            'enrolled_users':digi_customers_count,
            'total_accounts':digi_accounts.count(),
            'total_investment':Decimal(total_payment_amount),
            'total_investment_filtered':Decimal(total_payment_amount_filtered),
            'total_gold':Decimal(total_gold_paid_weight + total_gold_bonus_weight),
            'total_silver':Decimal(total_silver_paid_weight + total_silver_bonus_weight),
        }
        return Response({'data':instance}, status=status.HTTP_200_OK)
    
class DigiMonthlyMetalWiseCountView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        year = int(request.GET.get('year', date.today().year))
        payments_query = Payment.objects.filter(id_scheme__scheme_type=2, date_payment__year=year)

        monthly_gold = payments_query.filter(id_scheme__sch_id_metal=1).annotate(
            month=TruncMonth('date_payment')
        ).values('month').annotate(
            total_gold=Sum('metal_weight'),
            total_gold_bonus=Sum('bonus_metal_weight')
        )

        monthly_silver = payments_query.filter(id_scheme__sch_id_metal=2).annotate(
            month=TruncMonth('date_payment')
        ).values('month').annotate(
            total_silver=Sum('metal_weight'),
            total_silver_bonus=Sum('bonus_metal_weight')
        )

        monthly_data = OrderedDict()
        for month_num in range(1, 13):
            month_name_str = calendar.month_abbr[month_num]  
            monthly_data[month_num] = {
                'month': month_num,
                'month_name': month_name_str,
                'total_gold': Decimal('0.000'),
                'total_silver': Decimal('0.000')
            }

        for entry in monthly_gold:
            month = entry['month'].month
            total = (entry['total_gold'] or Decimal('0.000')) + (entry['total_gold_bonus'] or Decimal('0.000'))
            monthly_data[month]['total_gold'] = total.quantize(Decimal('0.000'))

        for entry in monthly_silver:
            month = entry['month'].month
            total = (entry['total_silver'] or Decimal('0.000')) + (entry['total_silver_bonus'] or Decimal('0.000'))
            monthly_data[month]['total_silver'] = total.quantize(Decimal('0.000'))

        return Response({'data': list(monthly_data.values())}, status=status.HTTP_200_OK)
    
class DigiSchemesClosedAccountsSummaryView(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        # Filter only closed digital gold scheme accounts
        digi_closed_accounts = SchemeAccount.objects.filter(
            acc_scheme_id__scheme_type=2,
            is_closed=True,
            closing_date__isnull=False,
            start_date__isnull=False,
            acc_scheme_id__digi_maturity_days__isnull=False
        ).annotate(
            maturity_date=ExpressionWrapper(
                F('start_date') + timedelta(days=1),
                output_field=DateField()
            )
        )

        after_maturity = 0
        before_maturity = 0

        for account in digi_closed_accounts:
            maturity_days = account.acc_scheme_id.digi_maturity_days or 0
            maturity_date = account.start_date + timedelta(days=maturity_days)
            if account.closing_date >= maturity_date:
                after_maturity += 1
            else:
                before_maturity += 1

        response_data = [
            { "id": str(uuid4()), "value": after_maturity, "label": "After Maturity", "color": "#00B0BD" },
            { "id": str(uuid4()), "value": before_maturity, "label": "Before Maturity", "color": "#9AA5B1" }
        ]

        return Response({'data': response_data}, status=status.HTTP_200_OK)
    

class DigiGoldSchemeSlabWiseAccountCount(generics.GenericAPIView):
    permission_classes = [IsEmployee]
    
    def get(self, request, *args, **kwargs):
        today = now().date()
        response_data = []
        filter_option = request.query_params.get('metal_type', 1)  

        # Get all DigiGold schemes
        digi_schemes = Scheme.objects.filter(scheme_type=2, status=True)
        
        # for scheme in digi_schemes:
        #     benefit_slabs = SchemeBenefitSettings.objects.filter(scheme=scheme)
        #     scheme_accounts = SchemeAccount.objects.filter(acc_scheme_id=scheme, is_closed=False)
        
        benefit_slabs = SchemeDigiGoldInterestSettings.objects.filter(scheme__sch_id_metal=1)
        if(int(filter_option) == 2):
            benefit_slabs = SchemeDigiGoldInterestSettings.objects.filter(scheme__sch_id_metal=2)
        elif(int(filter_option) == 1):
            benefit_slabs = SchemeDigiGoldInterestSettings.objects.filter(scheme__sch_id_metal=1)
        for slab in benefit_slabs:
            scheme_accounts = SchemeAccount.objects.filter(acc_scheme_id=slab.scheme.pk, is_closed=False)
            count = 0
            amount = 0
            bonus_amount = 0
            weight = 0
            bonus_weight = 0
            customers = 0
            for account in scheme_accounts:
                days_diff = (today - account.start_date).days
                if slab.from_day <= days_diff <= slab.to_day:
                    digi_customer_ids = scheme_accounts.values_list('id_customer', flat=True).distinct()
                    payment_amount = Payment.objects.filter(id_scheme_account=account.id_scheme_account).aggregate(total=Sum('payment_amount'))['total'] or Decimal('0.00')
                    bonus_payment_amount = Payment.objects.filter(id_scheme_account=account.id_scheme_account).aggregate(total=Sum('bonus_metal_amount'))['total'] or Decimal('0.00')
                    bonus_payment_weight = Payment.objects.filter(id_scheme_account=account.id_scheme_account).aggregate(total=Sum('bonus_metal_weight'))['total'] or Decimal('0.000')
                    payment_weight = Payment.objects.filter(id_scheme_account=account.id_scheme_account).aggregate(total=Sum('metal_weight'))['total'] or Decimal('0.000')
                    
                    amount += Decimal(payment_amount)
                    bonus_amount += Decimal(bonus_payment_amount)
                    weight += Decimal(payment_weight)
                    bonus_weight += Decimal(bonus_payment_weight)
                    count += 1
                    customers = digi_customer_ids.count()
            response_data.append({
                'scheme_name': slab.scheme.scheme_name,
                'id': slab.scheme.pk,
                'slab': f"{slab.from_day}-{slab.to_day}",
                'account_count': count,
                'amount': amount,
                'bonus_amount': bonus_amount,
                'weight': weight,
                'bonus_weight': bonus_weight,
                'customers': customers,
            })
        
        extra_schemes = Scheme.objects.filter(scheme_type=2, status=True, sch_id_metal=int(filter_option))
        for scheme in extra_schemes:
            scheme_accounts = SchemeAccount.objects.filter(acc_scheme_id=scheme.pk, is_closed=False)
            count = 0
            amount = 0
            bonus_amount = 0
            weight = 0
            bonus_weight = 0
            for account in scheme_accounts:
                days_diff = (today - account.start_date).days
                if days_diff > 330:
                    payment_amount = Payment.objects.filter(id_scheme_account=account.id_scheme_account).aggregate(
                        total=Sum('payment_amount'))['total'] or Decimal('0.00')
                    bonus_payment_amount = Payment.objects.filter(id_scheme_account=account.id_scheme_account).aggregate(
                        total=Sum('bonus_metal_amount'))['total'] or Decimal('0.00')
                    bonus_payment_weight = Payment.objects.filter(id_scheme_account=account.id_scheme_account).aggregate(
                        total=Sum('bonus_metal_weight'))['total'] or Decimal('0.000')
                    payment_weight = Payment.objects.filter(id_scheme_account=account.id_scheme_account).aggregate(
                        total=Sum('metal_weight'))['total'] or Decimal('0.000')

                    amount += Decimal(payment_amount)
                    bonus_amount += Decimal(bonus_payment_amount)
                    weight += Decimal(payment_weight)
                    bonus_weight += Decimal(bonus_payment_weight)
                    count += 1

            # if count > 0:
            customers = scheme_accounts.filter(
                start_date__lte=today - timedelta(days=331)
            ).values_list('id_customer', flat=True).distinct().count()
            response_data.append({
                'scheme_name': scheme.scheme_name,
                'id': scheme.pk,
                'slab': "330+",
                'account_count': count,
                'amount': amount,
                'bonus_amount': bonus_amount,
                'weight': weight,
                'bonus_weight': bonus_weight,
                'customers': customers,
            })

        return Response(response_data, status=status.HTTP_200_OK)
    
class DigiGoldUpcomingMaturitiesAccountsView(generics.GenericAPIView):
    permission_classes = [IsEmployee]

    def get(self, request, *args, **kwargs):
        today = now().date()
        periods = [30, 60, 90]
        result = []

        for period in periods:
            start_range = today if period == 30 else today + timedelta(days=period - 30)
            end_range = today + timedelta(days=period)

            matured_accounts = SchemeAccount.objects.select_related('acc_scheme_id').filter(
                acc_scheme_id__scheme_type=2
            )

            gold_weight = Decimal("0.000")
            silver_weight = Decimal("0.000")
            gold_count = 0
            silver_count = 0

            scheme_account_ids = []
            scheme_id_to_metal = {}

            for acc in matured_accounts:
                # Calculate maturity date manually
                maturity_date = acc.start_date + timedelta(days=acc.acc_scheme_id.digi_maturity_days)

                if start_range < maturity_date <= end_range:
                    scheme_account_ids.append(acc.id_scheme_account)
                    scheme_id_to_metal[acc.id_scheme_account] = acc.acc_scheme_id.sch_id_metal_id

            payments = Payment.objects.filter(
                id_scheme_account__in=scheme_account_ids
            ).values('id_scheme_account').annotate(
                total_bonus=Sum('bonus_metal_weight')
            )

            for pay in payments:
                acc_id = pay['id_scheme_account']
                weight = pay['total_bonus'] or Decimal("0.000")
                metal_id = scheme_id_to_metal.get(acc_id)

                if metal_id == 1:
                    gold_weight += weight
                    gold_count += 1
                elif metal_id == 2:
                    silver_weight += weight
                    silver_count += 1

            result.append({
                "period": f"Next {period} Days",
                "customers_maturing": gold_count + silver_count,
                "total_gold_bonus": float(gold_weight),
                "total_silver_bonus": float(silver_weight),
            })

        return Response({'data': result}, status=status.HTTP_200_OK)
