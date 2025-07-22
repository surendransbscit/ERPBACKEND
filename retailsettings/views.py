from datetime import datetime, timezone
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from common.permissions import IsEmployee
from .models import RetailSettings
from .serializers import RetailSettingsSerializer
from utilities.pagination_mixin import PaginationMixin
from .constants import (SETTINGS_COLUMN_LIST,SETTINGS_ACTION_LIST)


# Create your views here.

pagination = PaginationMixin()  # Apply pagination

class RetailSettingsListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = RetailSettings.objects.all()
    serializer_class = RetailSettingsSerializer

    def get(self, request, format=None):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
       
        queryset = RetailSettings.objects.all()
        paginator, page = pagination.paginate_queryset(self.queryset, request,None,SETTINGS_COLUMN_LIST)
        serializer = self.serializer_class(page, many=True)
        for index, data in enumerate(serializer.data):
            data.update(
                {'pk_id': data['id_settings'], 'sno': index+1})
        context = {'columns': SETTINGS_COLUMN_LIST, 'actions': SETTINGS_ACTION_LIST,
                   'page_count': paginator.count, 'total_pages': paginator.num_pages, 'current_page': page.number}
        return pagination.paginated_response(serializer.data, context)


    def post(self, request, format=None):
        # request.data.update({"created_by": request.user.pk})
        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        with transaction.atomic():
            if(len(request.data['settings_list']) > 0):
                if(RetailSettings.objects.filter(group_by=request.data['group_by']).exists()):
                    RetailSettings.objects.filter(group_by=request.data['group_by']).delete()
                for data in request.data['settings_list']:
                    data.update({"created_by": request.user.pk})
                    serializer = self.get_serializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                return Response({"message":"Settings created successfully"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"error_detail": ["Settings list can't be empty."]}, status=status.HTTP_400_BAD_REQUEST)
        


class RetailSettingsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = RetailSettings.objects.all()
    serializer_class = RetailSettingsSerializer

    def get(self, request, pk, format=None):
        # obj = self.get_object()
        # serializer = self.get_serializer(obj)
        # output = serializer.data
        # output.update({"created_by": obj.created_by.username,
        #                "updated_by": obj.updated_by.username if obj.updated_by != None else None})
        queryset = RetailSettings.objects.filter(group_by=pk)
        serializer = RetailSettingsSerializer(queryset, many=True)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        obj = self.get_object()
        request.data.update({"created_by": obj.created_by.pk})
        serializer = self.get_serializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user,
                        updated_on=datetime.now(tz=timezone.utc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    
    
    def delete(self, request, pk, format=None):
        queryset = self.get_object()
        try:
            queryset.delete()
        except ProtectedError:
            return Response({"error_detail": ["Settings can't be deleted, as it is already used in transaction"]}, status=status.HTTP_423_LOCKED)
        return Response(status=status.HTTP_204_NO_CONTENT)




@api_view(['post', ])
def RetailSettingsbyname(request):
    if 'name' in request.data:
        # print(request.data['name'])
        try:
            obj = RetailSettings.objects.get(
                name__contains=request.data['name'])
        except (RetailSettings.DoesNotExist, RetailSettings.MultipleObjectsReturned):
            return Response({"error_detail": ["Required retail settings missing"]})
        # print(obj)
        return Response({'ret_settings_name': obj.name, 'ret_settings_value': obj.value})
    return Response(status=status.HTTP_400_BAD_REQUEST)
