from django.urls import path

from .views import RetailSettingsDetailView, RetailSettingsListView, RetailSettingsbyname

urlpatterns = [
    path('ret_settings/', RetailSettingsListView.as_view()),
    path('ret_settings/<int:pk>/', RetailSettingsDetailView.as_view()),
    path('ret_settings_byname/', RetailSettingsbyname),

]
