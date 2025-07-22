from django.urls import path
from .views import (ChitSettingsListView,ChitSettingsDetailsView)

urlpatterns = [
        path('chit_settings/', ChitSettingsListView.as_view()),
        path('chit_settings/<int:pk>/', ChitSettingsDetailsView.as_view()),

      
]