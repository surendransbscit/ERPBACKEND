from django.urls import path

from .views import (LoyaltyTierListView,LoyaltyTierDetailView,LoyaltySettingsListView,LoyaltySettingsDetailView,
                    LoyaltyCustomerListView,LoyaltyCustomerDetailView,LoyaltyTransactionDetailView,LoyaltyTransactionListView)


urlpatterns = [
    path('loyalty_tier/', LoyaltyTierListView.as_view()),
    path('loyalty_tier/<int:pk>/', LoyaltyTierDetailView.as_view()),
    path('loyalty_settings/', LoyaltySettingsListView.as_view()),
    path('loyalty_settings/<int:pk>/', LoyaltySettingsDetailView.as_view()),
    path('loyalty_customer/', LoyaltyCustomerListView.as_view()),
    path('loyalty_customer/<int:pk>/', LoyaltyCustomerDetailView.as_view()),
    path('loyalty_transactions/', LoyaltyTransactionListView.as_view()),
    path('loyalty_transactions/<int:pk>/', LoyaltyTransactionDetailView.as_view()),
]
