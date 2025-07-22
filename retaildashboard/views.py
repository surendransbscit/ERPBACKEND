from rest_framework import generics, status
from rest_framework.response import Response
from datetime import  timedelta, date
from django.core.exceptions import ObjectDoesNotExist
from utilities.pagination_mixin import PaginationMixin
pagination = PaginationMixin()  # Apply pagination
from common.permissions import IsEmployee
from estimations.models import ErpEstimation,ErpEstimationSalesDetails
from estimations.serializers import ErpEstimationSerializer,ErpEstimationSalesDetailsSerializer
from billing.models import Product,ErpInvoice,ErpInvoiceSalesReturn,ErpReceiptCreditCollection,ErpInvoiceSalesDetails,ErpInvoiceOldMetalDetails,ITEM_TYPE_CHOICES
from billing.serializers import ErpInvoiceSalesDetailsSerializer,get_invoice_no,ErpInvoiceSerializer,ErpInvoiceSalesReturnSerializer,ErpInvoiceOldMetalDetailsSerializer,ErpReceiptCreditCollectionSerializer
from customerorder.models import ERPOrderDetails,ErpJobOrder,ErpJobOrderDetails
from customerorder.serializers import ErpOrdersDetailSerializer
from inventory.models import ErpLotInwardDetails
from managescheme.models import SchemeAccount
from retailcataloguemasters.serializers import ProductSerializer
from customers.models import Customers
from branchtransfer.models import ErpStockTransfer,ErpTagTransfer,ErpNonTagTransfer
from branchtransfer.views import get_status_color
from django.db.models import Q,F,Sum,Count,Subquery,ExpressionWrapper,DecimalField,Value,Avg,PositiveIntegerField,IntegerField
from django.db.models.functions import Cast,Concat
from django.utils import timezone
from django.db.models.functions import Coalesce
from django.utils.timezone import make_aware
from datetime import datetime, timedelta, date
from babel.numbers import format_decimal
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from utilities.utils import format_number_with_decimal,format_date
from django.db import connection
from django.db import DatabaseError,OperationalError
from .constants import *


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
    print([start_date, end_date])
    return start_date, end_date


class EstimationDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        settings_type=1
        queryset = ErpEstimation.objects.filter(net_amount__gt = 0 )
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            print(from_date)
            print(to_date)
            if from_date and to_date:
                    queryset = queryset.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(id_branch=id_branch)

        serializer = ErpEstimationSerializer(queryset, many=True)
        created = created_per = converted = non_converted =  converted_per = non_converted_per = created_amt = converted_amt = non_converted_amt = 0.00


        for est in serializer.data:
            created_per = 100.00
            created+=1
            created_amt += float(est['net_amount']) 
            queryset_sales = ErpInvoice.objects.filter(
                sales_invoice_id__est_sales_inv__estimation_id=est['estimation_id'],
                invoice_status=1 ,
                setting_bill_type = settings_type
            ).order_by('-erp_invoice_id')
            if(queryset_sales):
                converted +=1
                converted_amt += float(est['net_amount']) 
            else:
                non_converted +=1
                non_converted_amt += float(est['net_amount']) 

        if(converted):
            converted_per = (((converted / created)*100))

        if(non_converted):
            non_converted_per = ((non_converted / created)*100)
        
        output = [
            { "lable" :"Created","type": 1,"count": created,"percentage":format_number_with_decimal(created_per,2),"amount": created_amt},
            { "lable" :"Converted","type": 2,"count": converted,"percentage":format_number_with_decimal(converted_per,2),"amount": converted_amt},
            { "lable" :"Non Converted","type": 3,"count": non_converted,"percentage":format_number_with_decimal(non_converted_per,2),"amount": non_converted_amt}
        ]
        return Response(output, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        output = []
        settings_type=1
        id_branch = request.data.get('branch', [])
        type = request.data.get('type', 1)
        queryset = ErpEstimation.objects.all()
        if (request.data['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.data['days']))
            if from_date and to_date:
                    queryset = queryset.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(id_branch=id_branch)

        serializer = ErpEstimationSerializer(queryset, many=True)
        created  = converted = non_converted = []

        for est in serializer.data:
            created.append(est)
            queryset_sales = ErpInvoice.objects.filter(
                sales_invoice_id__est_sales_inv__estimation_id=est['estimation_id'],
                invoice_status=1 ,
                setting_bill_type = settings_type
            ).order_by('-erp_invoice_id')
            if(queryset_sales):
                converted.append(est)
            else:
                non_converted.append(est)
        
        if(type == 1):
            output = created
        elif(type == 2):    
            output = converted
        elif(type == 3):    
            output = non_converted
        return Response(output, status=status.HTTP_200_OK)
    


class CustomerVistDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        settings_type = 1
        id_branch = request.query_params.getlist('branch', [])
        queryset = ErpInvoice.objects.filter(invoice_status=1,setting_bill_type = settings_type)

        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])

        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(id_branch__in=id_branch)
        elif id_branch:
            queryset = queryset.filter(id_branch=id_branch)

        
        new_customer = queryset.filter(id_customer__custom_entry_date=F('invoice_date')).aggregate(
            pieces=Sum('sales_invoice_id__pieces', default=0),
            weight=Sum('sales_invoice_id__gross_wt', default=0),
            cust_count=Count('id_customer', distinct=True),
            amount=Sum('sales_invoice_id__item_cost', default=0)
        )

        
        chit_subquery = SchemeAccount.objects.values('id_customer_id')

        non_chit_customer = queryset.exclude(id_customer_id__in=Subquery(chit_subquery)).exclude(id_customer__custom_entry_date=F('invoice_date')).aggregate(
            pieces=Sum('sales_invoice_id__pieces', default=0),
            weight=Sum('sales_invoice_id__gross_wt', default=0),
            cust_count=Count('id_customer', distinct=True),
            amount=Sum('sales_invoice_id__item_cost', default=0)
        )

        chit_customer = queryset.filter(id_customer_id__in=Subquery(chit_subquery)).aggregate(
            pieces=Sum('sales_invoice_id__pieces', default=0),
            weight=Sum('sales_invoice_id__gross_wt', default=0),
            cust_count=Count('id_customer', distinct=True),
            amount=Sum('sales_invoice_id__item_cost', default=0)
        )

        
        output = [
            {
                "name": "New",

                "type": 1,

                 **new_customer
            },
            {
                "name": "Chit",
                "type": 2,
                **chit_customer
            },
            {
                "name": "Non-Chit",
                "type": 3,
                **non_chit_customer
            }
        ]

        return Response(output, status=status.HTTP_200_OK)
    
class SalesDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        settings_type = 1
        id_branch = request.query_params.getlist('branch', [])  # Use getlist to get an array of branch IDs
        if id_branch:
            id_branch = [int(branch) for branch in id_branch]  # Convert the branch IDs to integers

        queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status=1,invoice_bill_id__setting_bill_type = settings_type)

        if request.query_params['days'] != 'undefined':
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

        if id_branch:
            queryset = queryset.filter(invoice_bill_id__id_branch__in=id_branch)  # Handle branch filtering

        queryset = queryset.values('id_product__id_metal').annotate(
            piece=Sum('pieces', default=0),
            weight=Sum('gross_wt', default=0),
            bill_count=Count('invoice_bill_id'),
            amount=Sum('item_cost', default=0),
            metal_name=F('id_product__id_metal__metal_name'),
            type=F('id_product__id_metal')
        ).values(
            'piece',
            'weight',
            'bill_count',
            'amount',
            'metal_name',
            'type'
        )

        return Response(queryset, status=status.HTTP_200_OK)
    
class CustomerOrderDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = {}
        id_branch = request.query_params.getlist('branch', [])
        queryset = ERPOrderDetails.objects.exclude(order_status=5)
        # if (request.query_params['days'] != 'undefined'):
        #     from_date,to_date = get_past_date(int(request.query_params['days']))
        #     # if from_date and to_date:
        #     #         queryset = queryset.filter(order__order_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(order__order_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(order__order_branch=id_branch)

 
        queryset = queryset.values('order_status').annotate(
            piece=Sum('pieces', default=0),
            weight=Cast(Sum('gross_wt', default=0), DecimalField(max_digits=10, decimal_places=3)),
            item_count=Count('detail_id'),
            amount=Cast(Sum('item_cost', default=0), DecimalField(max_digits=10, decimal_places=2)),
            status_name=F('order_status__name'),
            type=F('order_status'),
        ).values(
            'piece',
            'weight',
            'item_count',
            'amount',
            'status_name',
            'type'
        )
        now = make_aware(datetime.now()).date() 

        today_deliverd_queryset = ERPOrderDetails.objects.filter(order_status=5,delivered_on=now).annotate(
            piece=Sum('pieces', default=0),
            weight=Cast(Sum('gross_wt', default=0), DecimalField(max_digits=10, decimal_places=3)),
            item_count=Count('detail_id'),
            amount=Cast(Sum('item_cost', default=0), DecimalField(max_digits=10, decimal_places=2)),
            status_name=Concat(Value("Today"), Value(" "), F('order_status__name')),
            updated_ons=F('updated_on'),
            type=F('order_status'),
        ).values(
            'piece',
            'weight',
            'item_count',
            'amount',
            'status_name',
            'updated_ons',
            'type'
        )


        print(today_deliverd_queryset)
        print(now)
        if(today_deliverd_queryset):
            queryset = list(queryset)  # Check if there is a result from the second queryset
            queryset.append(today_deliverd_queryset.first())

        print(connection.queries[-1])


       
        return Response(queryset, status=status.HTTP_200_OK)


class SalesReturnDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        settings_type=1
        queryset = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id__invoice_status=1,invoice_bill_id__setting_bill_type = settings_type)
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(invoice_bill_id__id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(invoice_bill_id__id_branch=id_branch)

 
        queryset = queryset.values('id_product__id_metal').annotate(
            pieces=Sum('pieces', default=0),
            weight=Sum('gross_wt', default=0),
            bill_count=Count('invoice_bill_id',distinct=True),
            amount=Sum('item_cost', default=0),
            metal_name=F('id_product__id_metal__metal_name'),
            id_metal=F('id_product__id_metal')
        ).values(
            'pieces',
            'weight',
            'bill_count',
            'amount',
            'metal_name',
            'id_metal'
        )

       
        return Response(queryset, status=status.HTTP_200_OK)
    

class PurchaseDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        settings_type=1
        queryset = ErpInvoice.objects.filter(invoice_status=1,purchase_invoice_id__isnull=False,setting_bill_type = settings_type)
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(invoice_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(id_branch=id_branch)

 
        queryset = queryset.values('purchase_invoice_id__id_product__id_metal').annotate(
            pieces=Sum('purchase_invoice_id__pieces', default=0),
            weight=Sum('purchase_invoice_id__gross_wt', default=0),
            bill_count=Count('purchase_invoice_id'),
            rate=Avg('purchase_invoice_id__rate_per_gram', default=0,),
            wastage=Avg('purchase_invoice_id__wastage_percentage', default=0),
            metal_name=F('purchase_invoice_id__id_product__id_metal__metal_name'),
            id_metal = F('purchase_invoice_id__id_product__id_metal')
        ).values(
            'pieces',
            'weight',
            'bill_count',
            'rate',
            'metal_name',
            'wastage',
            'id_metal'
        )

        return Response(queryset, status=status.HTTP_200_OK)
    
class LotDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        queryset = ErpLotInwardDetails.objects.filter(id_product__stock_type=0)
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(lot_no__lot_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(lot_no__id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(lot_no__id_branch=id_branch)

 
        queryset = queryset.values('id_product__id_metal').annotate(
            rev_pieces=Sum('pieces', default=0),
            rev_weight=Sum('gross_wt', default=0),
            tag_pieces=Sum('tagged_pcs', default=0),
            tag_weight=Sum('tagged_gross_wt', default=0),
            balance_pcs=ExpressionWrapper(Sum('pieces') - Sum('tagged_pcs', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            balance_gwt=ExpressionWrapper(Sum('gross_wt') - Sum('tagged_gross_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            metal_name=F('id_product__id_metal__metal_name'),
            id_metal=F('id_product__id_metal')
        ).values(
            'rev_pieces',
            'rev_weight',
            'balance_pcs',
            'balance_gwt',
            'tag_weight',
            'tag_pieces',
            'metal_name',
            'id_metal'
        )

       
        return Response(queryset, status=status.HTTP_200_OK)
    

class CreditSalesDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        date_filter = ''
        settings_type=1
        id_branch = request.query_params.getlist('branch', [])
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            date_filter = F" AND iss.bill_date BETWEEN '{from_date}' AND '{to_date}'"
        branch = ''
        if isinstance(id_branch, list) and id_branch:
            branch = ",".join(map(str, id_branch))
        elif (id_branch):
            branch = id_branch
        if branch:
            branch = F" AND iss.id_branch in ({branch})"
        sql = F"""SELECT 
                    'Credit' as Label, 
                    COALESCE(SUM(iss.amount),0) as pending, 
                    COALESCE(SUM(c.paid),0) as res_amount,
                    (COALESCE(SUM(iss.amount),0) - COALESCE(SUM(c.paid),0)) as balance_amount
                FROM erp_issue_receipt iss 
                LEFT JOIN (
                    SELECT c.issue_id, SUM(c.received_amount + c.discount_amount) as paid
                    FROM erp_receipt_credit_collection c 
                    GROUP BY c.issue_id
                ) as c ON c.issue_id = iss.id
                WHERE 
                    iss.deposit_bill_id is NOT NULL and
                    iss.type = 1 
                    AND iss.bill_status = 1 
                    AND iss.issue_type = 1 
                    AND iss.setting_bill_type = {settings_type}   
                    {date_filter}  
                    {branch}
                """
        print(sql)
        results = execute_raw_query(sql)
        return Response(results, status=status.HTTP_200_OK)
 
class JobOrderDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        queryset = ErpJobOrderDetails.objects.all()
        from_date = date.today()
        to_date = date.today()
        tomorrow = to_date + timedelta(days=1)
        start_of_week = to_date - timedelta(days=(to_date.weekday() + 1) % 7)
            # if from_date and to_date:
            #         queryset = queryset.filter(order__order_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(order_detail__order__order_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(order_detail__order__order_branch=id_branch)
  
        print(queryset)      
        received_today = queryset.filter(delivery_date=to_date,status=5).aggregate(
             pcs=Coalesce(Sum('order_detail__pieces'), Value(0,output_field=PositiveIntegerField())),
             weight=Coalesce(Sum('order_detail__gross_wt'), Value(0,output_field=DecimalField())),
        )
        print(received_today)      
        received_today['type'] = 1
        received_today['Label'] = "Today - Received"
        
        pending_today = queryset.filter(due_date=to_date,status__in=[1,3,4]).aggregate(
             pcs=Coalesce(Sum('order_detail__pieces'), Value(0,output_field=PositiveIntegerField())),
             weight=Coalesce(Sum('order_detail__gross_wt'), Value(0,output_field=DecimalField())),
        )

        pending_today['type'] = 2
        pending_today['Label'] = "Today - Pending"

        pending_tommarrow = queryset.filter(due_date=tomorrow,status__in=[1,3,4]).aggregate(
             pcs=Coalesce(Sum('order_detail__pieces'), Value(0,output_field=PositiveIntegerField())),
             weight=Coalesce(Sum('order_detail__gross_wt'), Value(0,output_field=DecimalField())),
        )
        pending_tommarrow['type'] = 3
        pending_tommarrow['Label'] = "Tommorrow Due"

        this_week = queryset.filter(due_date__range=[start_of_week,to_date],status__in=[1,3,4]).aggregate(
             pcs=Coalesce(Sum('order_detail__pieces'), Value(0,output_field=PositiveIntegerField())),
             weight=Coalesce(Sum('order_detail__gross_wt'), Value(0,output_field=DecimalField())),
        )
        this_week['type'] = 4
        this_week['Label'] = "This Week"

        pending_delivery = queryset.filter(due_date__lte=to_date,status__in=[1,3,4]).aggregate(
             pcs=Coalesce(Sum('order_detail__pieces'), Value(0,output_field=PositiveIntegerField())),
             weight=Coalesce(Sum('order_detail__gross_wt'), Value(0,output_field=DecimalField())),
        )
        pending_delivery['type'] = 5
        pending_delivery['Label'] = "Pending Delivery"

        yet_to_delivery = queryset.filter(due_date__gte=to_date,status__in=[1,3,4]).aggregate(
             pcs=Coalesce(Sum('order_detail__pieces'), Value(0,output_field=PositiveIntegerField())),
             weight=Coalesce(Sum('order_detail__gross_wt'), Value(0,output_field=DecimalField())),
        )
        yet_to_delivery['type'] = 6
        yet_to_delivery['Label'] = "Yet to Delivery"


        return Response([received_today,pending_today,pending_tommarrow,this_week,pending_delivery,yet_to_delivery], status=status.HTTP_200_OK)


class StoreStatisticsDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        settings_type=1
        id_branch = request.query_params.getlist('branch', [])
        customer = Customers.objects.all().count()
        account = SchemeAccount.objects.all().count()
        b2bcreditissued= ErpInvoice.objects.filter(is_credit = 1,setting_bill_type = settings_type,invoice_status = 1,invoice_for=2).aggregate(total=Sum('due_amount'))['total'] or 0
        b2ccreditissued= ErpInvoice.objects.filter(is_credit = 1,setting_bill_type = settings_type,invoice_status = 1,invoice_for=1).aggregate(total=Sum('due_amount'))['total'] or 0
        b2bcreditcollected= ErpReceiptCreditCollection.objects.filter(issue__deposit_bill__invoice_for=2,receipt__bill_status= 1).aggregate(total=ExpressionWrapper(
            Sum('received_amount') - Sum('discount_amount'),
            output_field=DecimalField()
        ))['total'] or 0
        b2ccreditcollected= ErpReceiptCreditCollection.objects.filter(issue__deposit_bill__invoice_for=1,receipt__bill_status= 1).aggregate(total=ExpressionWrapper(
            Sum('received_amount') - Sum('discount_amount'),
            output_field=DecimalField()
        ))['total'] or 0

        pendingb2b= float(b2bcreditissued) - float(b2bcreditcollected)
        pendingb2c= float(b2ccreditissued) - float(b2ccreditcollected)

        id_branch = ",".join(map(str, id_branch))
        now = make_aware(datetime.now()).date()
        branch_filter = ''
        if(id_branch):
            branch_filter = F"AND tl.to_branch_id in ({id_branch})"
        else:
            branch_filter = "AND tl.to_branch_id IS NOT NULL"
        
        sql = (F"""SELECT
                            pro.id_metal_id,
                            tl.to_branch_id,
                            bra.name,
                            m.metal_name,
                            SUM(tag.tag_pcs) AS pieces,
                            SUM(tag.tag_gwt) AS gross_wt
                        FROM
                            erp_tagging tag
                        LEFT JOIN erp_tag_log_details tl ON
                            tl.tag_id_id = tag.tag_id {branch_filter}
                        LEFT JOIN erp_tag_log_details tl2 ON
                            tl2.tag_id_id = tag.tag_id AND tl2.id_tag_log > tl.id_tag_log AND tl2.date <=("{now}")
                        LEFT JOIN erp_product pro ON pro.pro_id = tag.tag_product_id_id
                        LEFT JOIN metal m ON m.id_metal = pro.id_metal_id
                        LEFT JOIN branch bra ON bra.id_branch = tl.to_branch_id
                        WHERE
                            tl2.tag_id_id IS NULL AND(
                                tl.id_stock_status_id = 1 OR tl.id_stock_status_id = 5
                            ) AND tl.date <=("{now}")
                        GROUP BY
                                pro.id_metal_id,tl.to_branch_id;""")
        #print(sql)
        
        results = execute_raw_query(sql)


        output = { "customer":customer,"account":account,"credit_pending_b2b": pendingb2b,"credit_pending_b2c": pendingb2c,"stock":results}
        return Response(output, status=status.HTTP_200_OK)
    
class TopProductSalesDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
        
    def get(self, request, *args, **kwargs):
        output = []
        settings_type=1
        id_branch = request.query_params.getlist('branch', [])
        queryset = ErpInvoice.objects.filter(invoice_status=1,sales_invoice_id__isnull=False,setting_bill_type = settings_type )
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            print(from_date,to_date)
            if from_date and to_date:
                    queryset = queryset.filter(invoice_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(id_branch=id_branch)

 
        queryset = queryset.values('sales_invoice_id__id_product').annotate(
            pieces=Sum('sales_invoice_id__pieces', default=0),
            weight=Sum('sales_invoice_id__gross_wt', default=0),
            bill_count=Count('erp_invoice_id'),
            amount=Sum('sales_amount', default=0),
            product_name=F('sales_invoice_id__id_product__product_name'),
            pro_id=F('sales_invoice_id__id_product'),
            image=F('sales_invoice_id__id_product__image')
        ).values(
            'pieces',
            'weight',
            'bill_count',
            'amount',
            'product_name',
            'pro_id',
            'image'
        ).order_by("-pieces")
        for data in queryset:
            product =  Product.objects.get(pro_id=data['pro_id'])
            product = ProductSerializer(product,context={"request":request}).data
            if (product['image'] == None):
                data.update({"image":None, "image_text":data['product_name'][0]})
            if (product['image'] != None):
                data.update({"image":product['image'], "image_text":data['product_name'][0]})

        return Response(queryset, status=status.HTTP_200_OK)
    
def execute_raw_query(sql):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            response_data = {"report_field":[],"report_data":[]}
            if cursor.description:
                result = cursor.fetchall()
                field_names = [desc[0] for desc in cursor.description]
                report_data = []
                for row in result:
                    field_value = dict(zip(field_names, row))
                    report_data.append(field_value)
                response_data = { "report_field":field_names,"report_data":report_data}
            else:
                result = None
            return response_data["report_data"]
    except OperationalError as e:
            raise e
    except DatabaseError as e:
            print(connection.queries[-1])
            raise e
    
class PoDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        today = datetime.now()
        start_of_this_week = today - timedelta(days=today.weekday())
        from_date = (start_of_this_week - timedelta(weeks=1)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        day = date.today()
        week_number = day.isocalendar().week - 1
        sql = (f"""SELECT
                        EXTRACT(WEEK FROM ent.entry_date) AS week_number,
                        pur.purchase_entry_id,
                        ent.ref_no,
                        ent.entry_date,
                        ent.payment_date,
                        DATE_FORMAT(ent.payment_date, '%d-%m-%Y') AS payment_date,
                        DATE_FORMAT(ent.entry_date, '%d-%m-%Y') AS entry_date,
                        pro.id_metal_id,
                        false as isChecked,
                        supp.supplier_name as supplier_name,
                        m.metal_name,
                        COALESCE(recv.pieces, 0) AS pieces,
                        COALESCE(recv.pure_wt, 0) AS pure_wt,
                        COALESCE(recv.purchase_cost, 0) AS purchase_cost,
                        COALESCE(rate_cut.paid_amount, 0) AS total_amount,
                        (COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) )  AS paid_weight,
                        COALESCE(payment.paid_amount, 0) AS paid_amount,
                        COALESCE(recv.pure_wt - (COALESCE(rate_cut.paid_weight, 0) + COALESCE(metal_issue.paid_weight, 0) ), 0) AS balance_weight,
                        COALESCE(rate_cut.paid_amount - COALESCE(payment.paid_amount, 0), 0) AS balance_amount
                    FROM
                        erp_purchase_item_details pur
                    LEFT JOIN erp_product pro ON
                        pro.pro_id = pur.id_product_id
                    LEFT JOIN metal m ON m.id_metal = pro.id_metal_id
                    LEFT JOIN erp_purchase_entry ent ON
                        ent.id_purchase_entry = pur.purchase_entry_id
                    LEFT JOIN erp_supplier supp ON
                        supp.id_supplier = ent.id_supplier_id
                    LEFT JOIN(
                        SELECT COALESCE(SUM(rec.recd_pieces), 0) AS pieces,
                            COALESCE(SUM(rec.recd_pure_wt), 0) AS pure_wt,
                            COALESCE(SUM(rec.recd_purchase_cost), 0) AS purchase_cost,
                            pur.purchase_entry_id,
                            pro.id_metal_id
                        FROM
                            erp_purchase_item_issue_receipt_details rec
                        LEFT JOIN erp_purchase_item_issue_receipt iss ON
                            iss.id_issue_receipt = rec.issue_receipt_id
                        LEFT JOIN erp_purchase_item_details pur ON
                            pur.id_purchase_entry_detail = rec.purchase_entry_detail_id
                        LEFT JOIN erp_product pro ON
                            pro.pro_id = pur.id_product_id
                        WHERE
                            iss.issue_type = 1 AND iss.status = 1
                        GROUP BY
                            pur.purchase_entry_id,
                            pro.id_metal_id
                    ) recv
                    ON
                        recv.purchase_entry_id = pur.purchase_entry_id AND recv.id_metal_id = pro.id_metal_id
                    LEFT JOIN(
                            SELECT
                                sp.metal_id,
                                sp.ref_id,
                                COALESCE(SUM(sp.paid_amount), 0) AS paid_amount
                            FROM
                                erp_supplier_payment_details sp
                            WHERE
                                sp.type = 1
                            GROUP BY
                                sp.ref_id,
                                sp.metal_id
                    ) payment
                    ON
                        payment.ref_id = pur.purchase_entry_id AND payment.metal_id = pro.id_metal_id
                    LEFT JOIN(
                        SELECT rc.id_metal_id,
                            rc.purchase_entry_id,
                            COALESCE(SUM(rc.amount), 0) AS paid_amount,
                            COALESCE(SUM(rc.pure_wt), 0) AS paid_weight
                        FROM
                            erp_rate_cut rc
                        GROUP BY
                            rc.purchase_entry_id,
                            rc.id_metal_id
                    ) rate_cut
                    ON
                        rate_cut.purchase_entry_id = pur.purchase_entry_id AND rate_cut.id_metal_id = pro.id_metal_id
                    LEFT JOIN(
                            SELECT
                                pro.id_metal_id,
                                mi.purchase_entry_id,
                                COALESCE(SUM(mi.issue_weight), 0) AS issue_weight,
                                COALESCE(SUM(mi.pure_wt), 0) AS paid_weight
                            FROM
                                erp_supplier_metal_issue_details mi
                            LEFT JOIN erp_product pro ON
                                pro.pro_id = mi.id_product_id
                            LEFT JOIN erp_supplier_metal_issue d ON
                                d.id_issue = mi.issue_id
                            WHERE
                                d.type = 1
                            GROUP BY
                                pro.id_metal_id,
                                mi.purchase_entry_id
                    ) metal_issue
                    ON
                        metal_issue.purchase_entry_id = pur.purchase_entry_id AND metal_issue.id_metal_id = pro.id_metal_id
                    WHERE
                        ent.is_approved = 1 and ent.entry_date >= "{from_date}"
                        AND ent.entry_date < "{to_date}"
                    GROUP BY
                        pur.purchase_entry_id,
                        pro.id_metal_id
                        """)        
        results = execute_raw_query(sql)
        last_week = []
        this_week = []
        for res in  results :
            if(week_number == res['week_number'] ):
               this_week.append(res)
            else:
               last_week.append(res)

        return Response({"this_week" : this_week,"last_week" : last_week })
    

class CustomerVistDashReportView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        settings_type = 1
        queryset = ErpInvoice.objects.filter(invoice_status=1,setting_bill_type = settings_type)
        type = int(request.query_params.get('type', 1))

        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                queryset = queryset.filter(invoice_date__range=[from_date, to_date])

        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(id_branch__in=id_branch)
        elif id_branch:
            queryset = queryset.filter(id_branch=id_branch)

        
        new_customer = queryset.filter(id_customer__custom_entry_date=F('invoice_date')).values("id_customer").annotate(
            pieces=Sum('sales_invoice_id__pieces', default=0),
            weight=Sum('sales_invoice_id__gross_wt', default=0),
            cus_name=F('customer_name'),
            amount=Sum('sales_amount', default=0)
        )

        
        chit_subquery = SchemeAccount.objects.values('id_customer_id')

        non_chit_customer = queryset.exclude(id_customer_id__in=Subquery(chit_subquery)).exclude(id_customer__custom_entry_date=F('invoice_date')).values("id_customer").annotate(
            pieces=Sum('sales_invoice_id__pieces', default=0),
            weight=Sum('sales_invoice_id__gross_wt', default=0),
            cus_name=F('customer_name'),
            amount=Sum('sales_amount', default=0)
        )

        chit_customer = queryset.filter(id_customer_id__in=Subquery(chit_subquery)).values("id_customer").annotate(
            pieces=Sum('sales_invoice_id__pieces', default=0),
            weight=Sum('sales_invoice_id__gross_wt', default=0),
            cus_name=F('customer_name'),
            amount=Sum('sales_amount', default=0)
        )

        if(type == 1):
            output = list(new_customer)
        elif(type == 2):    
            output = list(chit_customer)
        elif(type == 3):    
            output = list(non_chit_customer)
    
        for out in output:
            out.update({"sno":output.index(out)+1})

        return Response({"data":output,"column":CUS_LIST}, status=status.HTTP_200_OK)
    
class EstimationDashReportView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
        
    def get(self, request, *args, **kwargs):
        output = []
        settings_type = 1
        id_branch = request.query_params.getlist('branch', [])
        type = int(request.query_params.get('type', 1))
        queryset = ErpEstimation.objects.filter(net_amount__gt = 0 )
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(entry_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(id_branch=id_branch)

        serializer = ErpEstimationSerializer(queryset, many=True)
        created  = []
        converted = []
        non_converted = []

        for est in serializer.data:
            created.append(est)
            queryset_sales = ErpInvoice.objects.filter(
                sales_invoice_id__est_sales_inv__estimation_id=est['estimation_id'],
                setting_bill_type = settings_type,
                invoice_status=1 
            ).order_by('-erp_invoice_id')
            if(queryset_sales):
                invoice_no = []
                inv_data = ErpInvoiceSerializer(queryset_sales,many=True,context={'invoice_no': True}).data
                for dat in inv_data:
                    if dat['inv_no'] :
                        invoice_no.append(dat['inv_no']['invoice_no'])
                if invoice_no:
                    est['invoice_no'] = ", ".join(set(invoice_no))
                converted.append(est)
            else:
                non_converted.append(est)
        
        if(type == 1):
            output = created
        elif(type == 2):    
            output = converted
        elif(type == 3):    
            output = non_converted
        return Response({"data":output,"column":EST_COLUMN_LIST}, status=status.HTTP_200_OK)
    
class SalesDashReportView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        id_branch = request.query_params.getlist('branch', [])
        id_metal = request.query_params.get('id_metal')
        settings_type = 1
        
        if id_branch:
            id_branch = [int(branch) for branch in id_branch]  

        queryset = ErpInvoiceSalesDetails.objects.filter(invoice_bill_id__invoice_status=1,invoice_bill_id__setting_bill_type = settings_type)

        if request.query_params['days'] != 'undefined':
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])

        if id_branch:
            queryset = queryset.filter(invoice_bill_id__id_branch__in=id_branch)

        if id_metal:
            print("id_metal",id_metal)
            queryset = queryset.filter(id_product__id_metal=id_metal)

        data = ErpInvoiceSalesDetailsSerializer(queryset,many=True).data

        print(data)


        response_data=[]

        for item, instance in zip(data, queryset):

            inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

            inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                
            inv_data = get_invoice_no(inv_serializer)
            #purity = instance.purity_id.purity if instance.tag_purity_id else None
            tag_tax_grp = instance.tax_group_id.tgi_tgrpcode.tgrp_name if instance.tax_group_id else None
            mc_type_display = instance.get_mc_type_display()
            #item['tag_purity'] = purity
            item['tax_grp'] = tag_tax_grp
            item['mc_type_name'] = mc_type_display

            response_data.append({
                "sno":data.index(item)+1,
                **inv_serializer,
                'invoice_date': format_date(inv_serializer['invoice_date']),
                **item,
                **inv_data,
                'item_type': dict(ITEM_TYPE_CHOICES).get(instance.item_type, ''),
                'tag_code': instance.tag_id.tag_code if instance.tag_id else None,
            })

        return Response({"data":response_data,"column":SALES_REPORT}, status=status.HTTP_200_OK)
    
class SalesReturnReportDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        id_metal = request.query_params.get('type')
        settings_type = 1
        queryset = ErpInvoiceSalesReturn.objects.filter(invoice_bill_id__invoice_status=1,invoice_bill_id__setting_bill_type = settings_type)
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(invoice_bill_id__id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(invoice_bill_id__id_branch=id_branch)

        if id_metal:
            print("id_metal",id_metal)
            queryset = queryset.filter(id_product__id_metal=id_metal)
        data = ErpInvoiceSalesReturnSerializer(queryset,many=True).data

        response_data=[]

        for item, instance in zip(data, queryset):

            inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

            inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                
            inv_data = get_invoice_no(inv_serializer)
            #purity = instance.purity_id.purity if instance.tag_purity_id else None
            mc_type_display = instance.get_mc_type_display()
            #item['tag_purity'] = purity
            item['mc_type_name'] = mc_type_display

            response_data.append({
                "sno":data.index(item)+1,
                **inv_serializer,
                'invoice_date': format_date(inv_serializer['invoice_date']),
                **item,
                **inv_data,
            })

    
        return Response({"data":response_data,"column":SALES_REPORT}, status=status.HTTP_200_OK)
    
class PurchaseDashReportView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        id_metal = request.query_params.get('type')
        settings_type = 1
        queryset = ErpInvoiceOldMetalDetails.objects.filter(invoice_bill_id__invoice_status=1,invoice_bill_id__setting_bill_type = settings_type)
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(invoice_bill_id__invoice_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(invoice_bill_id__id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(invoice_bill_id__id_branch=id_branch)
        data = ErpInvoiceOldMetalDetailsSerializer(queryset,many=True).data

        if id_metal:
            queryset = queryset.filter(id_product__id_metal=id_metal)
        response_data=[]

        for item, instance in zip(data, queryset):

            inv_queryset = ErpInvoice.objects.get(erp_invoice_id = instance.invoice_bill_id.erp_invoice_id)

            inv_serializer = ErpInvoiceSerializer(inv_queryset).data
                
            inv_data = get_invoice_no(inv_serializer)

            response_data.append({
                "sno":data.index(item)+1,
                **inv_serializer,
                'invoice_date': format_date(inv_serializer['invoice_date']),
                **item,
                **inv_data,
            })


        return Response({"data":response_data,"column":PURCHASE_REPORT}, status=status.HTTP_200_OK)
    
    
class LotDashReportView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        id_branch = request.query_params.getlist('branch', [])
        queryset = ErpLotInwardDetails.objects.filter(id_product__stock_type=0)
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(lot_no__lot_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(lot_no__id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(lot_no__id_branch=id_branch)

 
        queryset = queryset.values('lot_no').annotate(
            lot_code = F('lot_no__lot_code'),
            rev_pieces=Sum('pieces', default=0),
            rev_weight=Sum('gross_wt', default=0),
            tag_pieces=Sum('tagged_pcs', default=0),
            tag_weight=Sum('tagged_gross_wt', default=0),
            balance_pcs=ExpressionWrapper(Sum('pieces') - Sum('tagged_pcs', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
            balance_gwt=ExpressionWrapper(Sum('gross_wt') - Sum('tagged_gross_wt', default=0),output_field=DecimalField(max_digits=10, decimal_places=3) ),
        ).values(
            'rev_pieces',
            'rev_weight',
            'balance_pcs',
            'balance_gwt',
            'tag_weight',
            'tag_pieces',
            'lot_no',
            'lot_code'
        )

        response_data = list(queryset)
        for item in response_data:
            item.update({"sno":response_data.index(item)+1})
        return Response({"data":response_data,"column":LOT_LIST}, status=status.HTTP_200_OK)
    
class CreditSalesDashReportView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        id_branch = request.query_params.getlist('branch', [])
        settings_type = 1
        queryset = ErpInvoice.objects.filter(is_credit=1,setting_bill_type = settings_type)
        if (request.query_params['days'] != 'undefined'):
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                    queryset = queryset.filter(invoice_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(id_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(id_branch=id_branch)

        data = ErpInvoiceSerializer(queryset,many=True,context={"invoice_no":True}).data

        for inv in data:
            received_amount = 0
            balance_amount =0
            issued_amount = float(inv["due_amount"])
            col = ErpReceiptCreditCollection.objects.filter(issue__deposit_bill = inv['erp_invoice_id'] ,receipt__bill_status= 1)
            col_data = ErpReceiptCreditCollectionSerializer(col,many=True).data
            for collection in col_data:
                received_amount += (float(collection['received_amount']) + float(collection['discount_amount']))
            balance_amount = issued_amount - received_amount
            inv.update({
                "sno":data.index(inv)+1,
                'invoice_no': inv['inv_no']['invoice_no'],
                'invoice_date': format_date(inv['invoice_date']),
                'issued_amount':issued_amount,
                'collected_amount':received_amount,
                'balance_amount':balance_amount,
            })

        return Response({"data":data,"column":CREDIT_INVOICE_REPORT}, status=status.HTTP_200_OK)
        

class StockTransferApprovalDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])  # Use getlist to get an array of branch IDs
        if id_branch:
            id_branch = [int(branch) for branch in id_branch]  # Convert the branch IDs to integers

        queryset = ErpStockTransfer.objects.all()

        if request.query_params['days'] != 'undefined':
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                queryset = queryset.filter(trans_date__range=[from_date, to_date])

        if id_branch:
            queryset = queryset.filter(transfer_from__in=id_branch)  # Handle branch filtering

        bta_req = queryset.filter(transfer_status__in = [0,1,3]).aggregate(
            count=Count('id_stock_transfer'),
        )['count']

        bta_com = queryset.filter(transfer_status = 1).aggregate(
            count=Count('id_stock_transfer'),
        )['count']
        bta_pen = queryset.filter(transfer_status = 0).aggregate(
            count=Count('id_stock_transfer'),
        )['count']
        bta_rej = queryset.filter(transfer_status = 3).aggregate(
            count=Count('id_stock_transfer'),
        )['count']

        btd_req = queryset.filter(transfer_status__in = [1,2]).aggregate(
            count=Count('id_stock_transfer'),
        )['count']

        btd_com = queryset.filter(transfer_status = 2).aggregate(
            count=Count('id_stock_transfer'),
        )['count']
        btd_pen = queryset.filter(transfer_status = 1).aggregate(
            count=Count('id_stock_transfer'),
        )['count']


        output = [
            {"label":"Stock Transfer Approval","type":1,"request":bta_req,"completed":bta_com,"pending":bta_pen,"rejected":bta_rej},
            {"label":"Stock Transfer Delivery","type":2,"request":btd_req,"completed":btd_com,"pending":btd_pen,"rejected":0}
        ]

        return Response(output, status=status.HTTP_200_OK)
    

class JobOrderReportDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        type = int(request.query_params.get('type', 1))
        queryset = ErpJobOrderDetails.objects.all()
        from_date = date.today()
        to_date = date.today()
        tomorrow = to_date + timedelta(days=1)
        start_of_week = to_date - timedelta(days=(to_date.weekday() + 1) % 7)
            # if from_date and to_date:
            #         queryset = queryset.filter(order__order_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(order_detail__order__order_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(order_detail__order__order_branch=id_branch)
        output = []
  
        if(type == 1):     
            received_today = queryset.filter(delivery_date=to_date,status=5).annotate(
                ref_no=F('job_order__ref_no'),
                assigned_date=F('job_order__assigned_date'),
                karigar_name=F('job_order__supplier__supplier_name'),
                order_no=F('order_detail__order__order_no'),
                order_status=F('status'),
                customer_due_date=F('order_detail__customer_due_date'),
                colour=F('status__colour'),
                order_status_name=F('status__name'),
                product_name=F('order_detail__product__product_name'),
                design_name=F('order_detail__design__design_name'),
                sub_design_name=F('order_detail__sub_design__sub_design_name'),
                pieces=F('order_detail__pieces'),
                gross_wt=F('order_detail__gross_wt'),
                net_wt=F('order_detail__net_wt'),
                less_wt=F('order_detail__less_wt'),
                detail_id=F('order_detail'))
            output = list(received_today.values())
        elif(type == 2):
            pending_today = queryset.filter(due_date=to_date,status__in=[1,3,4]).annotate(
                ref_no=F('job_order__ref_no'),
                assigned_date=F('job_order__assigned_date'),
                karigar_name=F('job_order__supplier__supplier_name'),
                order_no=F('order_detail__order__order_no'),
                order_status=F('status'),
                customer_due_date=F('order_detail__customer_due_date'),
                colour=F('status__colour'),
                order_status_name=F('status__name'),
                product_name=F('order_detail__product__product_name'),
                design_name=F('order_detail__design__design_name'),
                sub_design_name=F('order_detail__sub_design__sub_design_name'),
                pieces=F('order_detail__pieces'),
                gross_wt=F('order_detail__gross_wt'),
                net_wt=F('order_detail__net_wt'),
                less_wt=F('order_detail__less_wt'),
                detail_id=F('order_detail'))
            output = list(pending_today.values())
        elif(type == 3):
            pending_tommarrow = queryset.filter(due_date=tomorrow,status__in=[1,3,4]).annotate(
                ref_no=F('job_order__ref_no'),
                assigned_date=F('job_order__assigned_date'),
                karigar_name=F('job_order__supplier__supplier_name'),
                order_no=F('order_detail__order__order_no'),
                order_status=F('status'),
                customer_due_date=F('order_detail__customer_due_date'),
                colour=F('status__colour'),
                order_status_name=F('status__name'),
                product_name=F('order_detail__product__product_name'),
                design_name=F('order_detail__design__design_name'),
                sub_design_name=F('order_detail__sub_design__sub_design_name'),
                pieces=F('order_detail__pieces'),
                gross_wt=F('order_detail__gross_wt'),
                net_wt=F('order_detail__net_wt'),
                less_wt=F('order_detail__less_wt'),
                detail_id=F('order_detail'))
            output = list(pending_tommarrow.values())
        elif(type == 4):
            this_week = queryset.filter(due_date__range=[start_of_week,to_date],status__in=[1,3,4]).annotate(
                ref_no=F('job_order__ref_no'),
                assigned_date=F('job_order__assigned_date'),
                karigar_name=F('job_order__supplier__supplier_name'),
                order_no=F('order_detail__order__order_no'),
                order_status=F('status'),
                customer_due_date=F('order_detail__customer_due_date'),
                colour=F('status__colour'),
                order_status_name=F('status__name'),
                product_name=F('order_detail__product__product_name'),
                design_name=F('order_detail__design__design_name'),
                sub_design_name=F('order_detail__sub_design__sub_design_name'),
                pieces=F('order_detail__pieces'),
                gross_wt=F('order_detail__gross_wt'),
                net_wt=F('order_detail__net_wt'),
                less_wt=F('order_detail__less_wt'),
                detail_id=F('order_detail'))
            output = list(this_week.values())
        elif(type == 5):
            pending_delivery = queryset.filter(due_date__lte=to_date,status__in=[1,3,4]).annotate(
                ref_no=F('job_order__ref_no'),
                assigned_date=F('job_order__assigned_date'),
                karigar_name=F('job_order__supplier__supplier_name'),
                order_no=F('order_detail__order__order_no'),
                order_status=F('status'),
                customer_due_date=F('order_detail__customer_due_date'),
                colour=F('status__colour'),
                order_status_name=F('status__name'),
                product_name=F('order_detail__product__product_name'),
                design_name=F('order_detail__design__design_name'),
                sub_design_name=F('order_detail__sub_design__sub_design_name'),
                pieces=F('order_detail__pieces'),
                gross_wt=F('order_detail__gross_wt'),
                net_wt=F('order_detail__net_wt'),
                less_wt=F('order_detail__less_wt'),
                detail_id=F('order_detail'))
            output = list(pending_delivery.values())
        elif(type == 6):
            yet_to_delivery = queryset.filter(due_date__gte=to_date,status__in=[1,3,4]).annotate(
                ref_no=F('job_order__ref_no'),
                assigned_date=F('job_order__assigned_date'),
                karigar_name=F('job_order__supplier__supplier_name'),
                order_no=F('order_detail__order__order_no'),
                order_status=F('status'),
                customer_due_date=F('order_detail__customer_due_date'),
                colour=F('status__colour'),
                order_status_name=F('status__name'),
                product_name=F('order_detail__product__product_name'),
                design_name=F('order_detail__design__design_name'),
                sub_design_name=F('order_detail__sub_design__sub_design_name'),
                pieces=F('order_detail__pieces'),
                gross_wt=F('order_detail__gross_wt'),
                net_wt=F('order_detail__net_wt'),
                less_wt=F('order_detail__less_wt'),
                detail_id=F('order_detail'))
            output = list(yet_to_delivery.values())
        
        for out in output:
            out.update({"sno":output.index(out)+1,"status":out['order_status_name'],"colour":out['colour'],"due_date": format_date(out['due_date']),"assigned_date": format_date(out['assigned_date']),})
            
        return Response({"data":output,"column":JOB_ORDER_REPORT}, status=status.HTTP_200_OK)
    
    
class CustomerOrderReportDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = {}
        id_branch = request.query_params.getlist('branch', [])
        type = request.query_params.get('type')
        queryset = ERPOrderDetails.objects.filter(order_status=type)
        # if (request.query_params['days'] != 'undefined'):
        #     from_date,to_date = get_past_date(int(request.query_params['days']))
        #     # if from_date and to_date:
        #     #         queryset = queryset.filter(order__order_date__range=[from_date, to_date])
        if isinstance(id_branch, list) and id_branch:
            queryset = queryset.filter(order__order_branch__in=id_branch)
        elif (id_branch):
            queryset = queryset.filter(order__order_branch=id_branch)

        data = ErpOrdersDetailSerializer(queryset,many=True).data

        for detail, instance in zip(data, queryset):
            detail.update({
                "sno":data.index(detail)+1,
                "status": instance.order_status.name,
                "colour": instance.order_status.colour,
                "order_date": format_date(instance.order.order_date),
                "customer_due_date": format_date(instance.customer_due_date),
            })

        return Response({"data":data,"column":CUS_ORDER_REPORT}, status=status.HTTP_200_OK)


class StockTransferApprovalReportDashView(generics.GenericAPIView):
    permission_classes=[IsEmployee]
    
    def get(self, request, *args, **kwargs):
        output = []
        id_branch = request.query_params.getlist('branch', [])
        type = int(request.query_params.get('type'))

        if id_branch:
            id_branch = [int(branch) for branch in id_branch]  # Convert the branch IDs to integers

        queryset = ErpStockTransfer.objects.all()

        if request.query_params['days'] != 'undefined':
            from_date,to_date = get_past_date(int(request.query_params['days']))
            if from_date and to_date:
                queryset = queryset.filter(trans_date__range=[from_date, to_date])

        if id_branch:
            queryset = queryset.filter(transfer_from__in=id_branch)  # Handle branch filtering
        if(type == 1):
            queryset = queryset.filter(transfer_status__in = [0,1,3])
        elif(type == 2):
            print("type",type)
            queryset = queryset.filter(transfer_status__in = [1,2])

        response_data = []

        for index, stock_transfer in enumerate(queryset):

            if(stock_transfer.transfer_type == 1):
        
                transfer_list = ErpTagTransfer.objects.filter(stock_transfer=stock_transfer).values('stock_transfer').annotate(
                    pcs=Sum('tag_id__tag_pcs'),
                    gross_wt=Sum('tag_id__tag_gwt'),
                    net_wt=Sum('tag_id__tag_nwt'),
                    less_wt=Sum('tag_id__tag_lwt'),
                    stn_wt=Sum('tag_id__tag_stn_wt'),
                    dia_wt=Sum('tag_id__tag_dia_wt')
                ).values(
                    'stock_transfer',
                    'pcs',
                    'gross_wt', 
                    'net_wt',
                    'stn_wt',
                    'dia_wt',
                    'less_wt',
                ).get()

                response_data.append({
                    'sno':index+1,
                    'pk_id': stock_transfer.id_stock_transfer,
                    'trans_date': format_date(stock_transfer.trans_date),
                    'transfer_from':stock_transfer.transfer_from.name,
                    'transfer_to':(stock_transfer.transfer_to.name if(stock_transfer.transfer_to) else ''),
                    'status': dict(ErpStockTransfer.TRANSFER_STATUS_CHOICES).get(stock_transfer.transfer_status, ''),
                    'trans_code': stock_transfer.trans_code,
                    'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(stock_transfer.trans_to_type, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(stock_transfer.transfer_type, ''),
                    'tag_code':'',
                    **transfer_list,
                    'colour':get_status_color(stock_transfer.transfer_status),
                    'gross_wt': (transfer_list['gross_wt']),
                    'is_cancelable': True if stock_transfer.transfer_status == 0 else False,

                })

            if(stock_transfer.transfer_type == 2):
        
                transfer_list = ErpNonTagTransfer.objects.filter(stock_transfer=stock_transfer).values('stock_transfer').annotate(
                    total_gross_wt=Sum('gross_wt'),
                    total_net_wt=Sum('net_wt'),
                    total_less_wt=Sum('less_wt'),
                    total_stn_wt=Sum('stone_wt'),
                    total_dia_wt=Sum('dia_wt'),
                    pcs=Sum('pieces'),
                ).values(
                    'stock_transfer',
                    'pcs',
                    'total_gross_wt', 
                    'total_net_wt',
                    'total_less_wt',
                    'total_stn_wt',
                    'total_dia_wt',
                ).get()

                response_data.append({
                    'sno':index+1,
                    'pk_id': stock_transfer.id_stock_transfer,
                    'transfer_from':stock_transfer.transfer_from.name,
                    'transfer_to':(stock_transfer.transfer_to.name if(stock_transfer.transfer_to) else ''),
                    'trans_code': stock_transfer.trans_code,
                    'trans_date': format_date(stock_transfer.trans_date),
                    'trans_to_type_name': dict(ErpStockTransfer.TRANS_TYPE_TO).get(stock_transfer.trans_to_type, ''),
                    'transfer_type_name': dict(ErpStockTransfer.TRANSFER_TYPE_CHOICES).get(stock_transfer.transfer_type, ''),
                    'status': dict(ErpStockTransfer.TRANSFER_STATUS_CHOICES).get(stock_transfer.transfer_status, ''),
                    'gross_wt': (transfer_list['total_gross_wt']),
                    'net_wt': transfer_list['total_net_wt'],  
                    'less_wt': transfer_list['total_less_wt'],  
                    'stn_wt': transfer_list['total_stn_wt'],
                    'dia_wt': transfer_list['total_dia_wt'],
                    'pcs': transfer_list['pcs'],
                    'tag_code':'',
                    'colour':get_status_color(stock_transfer.transfer_status),
                    'is_cancelable': True if stock_transfer.transfer_status == 0 else False,
                })
       
        return Response({"data":response_data,"column":TRANCFER_COLUMN_LIST}, status=status.HTTP_200_OK)