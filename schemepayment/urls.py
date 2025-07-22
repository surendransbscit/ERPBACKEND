from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
from .views import (SchemePaymentView, SchemePaymentDetailView,GenerateReceiptView, CancelPaymentView, 
                    AccountPaymentHistoryView,PaymentHistoryView,SchemePaymentStatusUpdateView)

urlpatterns = [
    path('scheme_payment/', SchemePaymentView.as_view()),
    path('payment_status_update/', SchemePaymentStatusUpdateView.as_view()),
    path('scheme_payment/<int:pk>/', SchemePaymentDetailView.as_view()),
    path('cancel_payment/', CancelPaymentView.as_view()),
    path('payment_history/', PaymentHistoryView.as_view()),
    path('account_payment_history/<int:pk>/', AccountPaymentHistoryView.as_view()),
    path('receipt/<int:pk>/', GenerateReceiptView.as_view(), name='generate-receipt'),
]