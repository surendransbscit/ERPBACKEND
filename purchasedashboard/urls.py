from django.urls import path

from .views import (ErpSupplierRateCutListAPIView)

urlpatterns = [
    path('supplier_rate_cut/', ErpSupplierRateCutListAPIView.as_view()),
]