from django.urls import path
from .views import (EmployeeTypeDetils,EmployeeTypeList, CreateEmployeeAPI, EmployeeSignInAPI,
                    EmpSettingsView, EmpProfileView,EmployeeInfo, LogoutView,MenuStyleUpdateView,
                    EmployeeResetPassword, EmployeeChange,ActiveEmployeeAPI, ActiveEmployees, EmployeeOTPVerify, EmployeeResendOTP,
                    EmployeeDetailView, EmployeeNotifications, SystemUserEmployeeList, SystemUserEmployeeDropdownView)

urlpatterns = [
    path('emp_logout/', LogoutView.as_view()),
    path('emp_change/', EmployeeChange.as_view()),
    path('user_reset_pass/', EmployeeResetPassword.as_view()),
    path('menu_style_update/', MenuStyleUpdateView.as_view()),
    path('emp_info/', EmployeeInfo.as_view()),
    path('emp_notifications/', EmployeeNotifications.as_view()),
    path('employeetype/', EmployeeTypeList.as_view()),
    path('employeetype/<int:pk>/', EmployeeTypeDetils.as_view()),
    path('active_employee/', ActiveEmployees.as_view()),
    path('employee/', CreateEmployeeAPI.as_view()),
    path('employee/<int:pk>/', EmployeeDetailView.as_view()),
    path('emp_login/', EmployeeSignInAPI.as_view()),
    path('emp_verify_otp/', EmployeeOTPVerify.as_view()),
    path('emp_resend_otp/', EmployeeResendOTP.as_view()),
    path('employee_settings/', EmpSettingsView.as_view()),
    path('profile_details/', EmpProfileView.as_view()),
    path('employee/active/', ActiveEmployeeAPI.as_view()),
    path('system_user_employee/', SystemUserEmployeeList.as_view()),
    path('system_users_dropdown/', SystemUserEmployeeDropdownView.as_view()),
]