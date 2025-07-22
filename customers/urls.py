from django.urls import path

from .views import (CustomerListView, CustomerDetailView, CustomerSearchView, CustomerSignInAPI,
                    CustomerLoginpinCreateView, CustomerSignupAPI,LogoutView, CustomerTokenRefreshView,
                    CustomerApprovalListView,CustomerAccountEditView,EmployeeTokenRefreshView,
                    CustomerCatalogueRequestView, CustomerNotificationsListView, CustomerNotificationsDetailView,
                    CustomerSearchAutoCompleteView,CustomerRejectView, CustomerProfileImageEditView,CustomerRegOTPVerify,
                    CustomerRegResendVerify, CustomerEnquiryCreateView, CustomerEnquiryListView)


urlpatterns = [

    path('customer_logout/', LogoutView.as_view()),
    path('customer_signup/', CustomerSignupAPI.as_view()),
    path('customer_signup_verify_otp/', CustomerRegOTPVerify.as_view()),
    path('customer_signup_resend_otp/', CustomerRegResendVerify.as_view()),
    path('customer_login/', CustomerSignInAPI.as_view()),
    path('customer_token_refresh/', CustomerTokenRefreshView.as_view()),
    path('employee_token_refresh/', EmployeeTokenRefreshView.as_view()),
    path('cus_login_pin/', CustomerLoginpinCreateView.as_view()),
    path('customer/', CustomerListView.as_view()),
    path('customer/<int:pk>/', CustomerDetailView.as_view()),
    path('customer_search/', CustomerSearchView.as_view()),
    path('customer_autocomplete/', CustomerSearchAutoCompleteView.as_view()),
    path('customer_approval/', CustomerApprovalListView.as_view()),
    path('customer_catalogue_request/', CustomerCatalogueRequestView.as_view()),
    path('customer_profile_edit/', CustomerAccountEditView.as_view()),
    path('customer_image_edit/', CustomerProfileImageEditView.as_view()),
    path('customer_notifications/', CustomerNotificationsListView.as_view()),
    path('view_notification/', CustomerNotificationsDetailView.as_view()),
    path('customer_reject/', CustomerRejectView.as_view()),
    path('customer_enquiry/', CustomerEnquiryCreateView.as_view()),
    path('customer_enquiry_list/', CustomerEnquiryListView.as_view()),
    # path('customer/<int:pk>/', DepartmentDetailView.as_view()),
    
]