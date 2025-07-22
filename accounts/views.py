from django.shortcuts import render
from django.db import IntegrityError
from django.http import HttpResponse, request, Http404
from rest_framework import generics, permissions, status
from django.utils.timezone import utc
# Create your views here.

def hom_view(request):
    return HttpResponse("Server is running")
