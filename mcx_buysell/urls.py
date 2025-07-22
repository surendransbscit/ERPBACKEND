from django.urls import path

from .views import (McxBuySellListView, McxBuySellCreateView, GetBuySellOpeningPosition)


urlpatterns = [
    path('buy_sell/list/', McxBuySellListView.as_view()),
    path('buy_sell/create/', McxBuySellCreateView.as_view()),
    path('buy_sell/get_opening_position/', GetBuySellOpeningPosition.as_view()),
]