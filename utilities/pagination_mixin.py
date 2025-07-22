from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from utilities.constants import FILTERS
from django.db.models.query import QuerySet
from django.db.models import Q
from django.core.exceptions import FieldDoesNotExist
from django.db.models import CharField, TextField,IntegerField,FloatField,DecimalField

def is_valid_field(queryset, field_name):
    model = queryset.model  # Get the model from the QuerySet
    try:
        # Check the base field (ignoring nested lookups)
        field = model._meta.get_field(field_name.split("__")[0])
        return isinstance(field, (CharField, TextField))
    except FieldDoesNotExist:
        return False

def lookup_for_field(queryset,field_name, value):
    """
    Returns an appropriate lookup expression for a field.
    If the field is numeric, uses __exact, otherwise uses __icontains.
    """
    model = queryset.model
    try:
        # Get the base field name (for nested lookups like category__name)
        base_field = field_name.split("__")[0]
        field = model._meta.get_field(base_field)
        if isinstance(field, (IntegerField, FloatField, DecimalField)):
            if isinstance(value, IntegerField):
                value = int(value)
            elif isinstance(value, FloatField):
                value = float(value)
            elif isinstance(value, DecimalField):
                value = float(value)
            else:
                return Q()
            return Q(**{f"{field_name}__exact": value})
        elif isinstance(field, (CharField, TextField)):
            return Q(**{f"{field_name}__icontains": value})
        # Fallback: default to icontains (for most text-like lookups)
        return Q()
    except FieldDoesNotExist:
        # If the field doesn't exist, you can choose to ignore or log it.
        return Q()

class PaginationMixin:
    page_size = 10  
        
    def paginate_queryset(self, queryset, request, no_of_records=None,columns=None):
        # Default page number
        if 'page' in request.query_params and request.query_params['page'] != 'page':
            page_number = request.query_params.get('page', 1)
        else:
            page_number = request.data.get('page', 1)

        # Determine the page size
        if 'records' in request.query_params and request.query_params['records'] != 'undefined':
            page_size = int(request.query_params.get('records', self.page_size))
        else:
            page_size = int(request.data.get('records', self.page_size)) if request.data.get('records') else self.page_size
            
        if 'searchText' in request.query_params and request.query_params['searchText'] != 'undefined' and request.query_params['searchText'] != 'null':
            search = request.query_params.get('searchText')
            if isinstance(queryset, QuerySet) and columns is not None:
                search_q = Q()
                for field in columns:
                    search_q |= lookup_for_field(queryset,field['accessor'], search)
                        
                queryset = queryset.filter(search_q)

        # Allow overriding default with `no_of_records` if provided
        if no_of_records is not None:
            page_size = no_of_records

        # Paginator initialization
        paginator = Paginator(queryset, page_size)

        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        return paginator, page

    def paginated_response(self,data,context):
        filters = FILTERS
        is_filter_req = False
        if 'filters' in context:
            filters = context['filters']
        if 'is_filter_req' in context:
            is_filter_req = context['is_filter_req']
        return Response({
            **context,
            "columns":context['columns'],
            "rows":data,
            "actions":context['actions'],
            'no_of_records': context['page_count'],
            'total_pages':context['total_pages'],
            'current_page':context['current_page'],
            'filters':filters,
            'is_filter_req':is_filter_req
        },status=status.HTTP_200_OK)