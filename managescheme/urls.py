from django.urls import path

from .views import (SchemeAccountView, SchemeAccountDetailView,SchemeAccountClosedList,
                    SchemeAccountDrop, SchemeAccountClosingView, SchemeAccountCloseRevertView, CustomerDigiSchemesMobileAppView,
                    SetDigiSchemeTargetWeight)

urlpatterns = [
    path('customer_account/', SchemeAccountDrop.as_view()),
    path('scheme_account/', SchemeAccountView.as_view()),
    path('scheme_account/<int:pk>/', SchemeAccountDetailView.as_view()),
    path('scheme_account_close/', SchemeAccountClosedList.as_view()),
    path('scheme_account_close/<int:pk>/', SchemeAccountClosingView.as_view()),
    path('scheme_account_close_revert/<int:pk>/', SchemeAccountCloseRevertView.as_view()),
    path('customer_digi_scheme/', CustomerDigiSchemesMobileAppView.as_view()),
    path('set_target_digi_scheme/', SetDigiSchemeTargetWeight.as_view()),
    
]