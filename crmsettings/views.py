from datetime import datetime, timezone
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from common.permissions import IsEmployee

from .models import ChitSettings

from .serializers import ChitSettingsSerializer


# Create your views here.


class ChitSettingsListView(generics.ListCreateAPIView):
    permission_classes = [IsEmployee]
    queryset = ChitSettings.objects.all()
    serializer_class = ChitSettingsSerializer

    def get(self, request, format=None):
        all_query = ChitSettings.objects.all()
        all_serializer = ChitSettingsSerializer(all_query, many=True)
        if(len(all_serializer.data)==0):
            data = {}
            data.update({"reciept_no_setting":1, "account_no_setting":1, "is_maintanence":False})
            create_data_seri = ChitSettingsSerializer(data=data)
            create_data_seri.is_valid(raise_exception=True)
            create_data_seri.save()
        queryset = ChitSettings.objects.latest('id')
        serializer = self.get_serializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        request.data.update({"created_by": request.user.pk})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChitSettingsDetailsView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsEmployee]
    queryset = ChitSettings.objects.all()
    serializer_class = ChitSettingsSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_object()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs,):
        queryset = self.get_object()
        serializer = ChitSettingsSerializer(queryset, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
