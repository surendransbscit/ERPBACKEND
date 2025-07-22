from django.urls import path

from .views import (SchemeListView,SchemeDetailView, SchemePaymentFormulaList, CustomerMultiSchemeListView)

urlpatterns = [
    path('list/', SchemeListView.as_view()),
    path('customer_multi_scheme_list/', CustomerMultiSchemeListView.as_view()),
    path('scheme_by_id/<int:pk>/', SchemeDetailView.as_view()),
    path('payment_setting_formula/', SchemePaymentFormulaList.as_view()),
]