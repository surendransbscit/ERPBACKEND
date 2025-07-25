from django.urls import path
from .views import (MenuList, MenuDetails, MenuFetch, EmployeeCheckTokenAPI, ChangesLogAPI, CustomerForgotPassword,
                    CustomerOTPVerify, CustomerChangePassword, CustomerResetPassword,CustomerAccountVerify, loginsessionView,
                    AdminChangePassword, BranchDropdownView, CheckAcess, EmployeeMenuFetch, EncodeAndDecodeView,ReportColumnsTemplatesList,
                    ProfileMenuAccess, GetProfileMenuAccess, ComposeMessage, TokenRefreshApi,MenuSearchView, BackupCurrentDB,
                    ProfileMenuAccessOptionsForCheckboxForm, ProfileMenuAccessForCheckboxForm)

urlpatterns = [
     path('adminmenu/', MenuList.as_view(),
         name='listcreate_adminmenu'),
     path('menu_access_options/', EmployeeMenuFetch.as_view(),
         name='employee_menu_access_options'),
     path('menu_access_checkbox_options/', ProfileMenuAccessOptionsForCheckboxForm.as_view()),
     path('get_profile_access_checkbox/', ProfileMenuAccessForCheckboxForm.as_view(),),
     path('profile_access/', ProfileMenuAccess.as_view(),
         name='profile_access'),
     path('get_profile_access/', GetProfileMenuAccess.as_view(),
         name='get_profile_access'),
    path('adminmenu/<int:pk>/', MenuDetails.as_view(),
         name='fetchupdatedelete_adminmenu_entry'),
    path('fetchmenu/', MenuFetch.as_view(),
         name='fetch_admin_menu'),
    path('access_check/', CheckAcess.as_view(),
         name='check_admin_access'),
    path('check_token/', EmployeeCheckTokenAPI.as_view(),
         name='check_token'),
    path('logs/', ChangesLogAPI.as_view(),
         name='logs_list_view'),
    path('cus_forgot_pass/', CustomerForgotPassword.as_view(),name='cus_forgot_pass'),
    path('login_branchdropdown/', BranchDropdownView.as_view()),
    path('cus_otp_verify/', CustomerOTPVerify.as_view(),name='cus_otp_verify'),
    path('cus_reset_pass/', CustomerResetPassword.as_view(),name='cus_reset_pass'),
    path('cus_change_pass/', CustomerChangePassword.as_view(),name='cus_change_pass'),
    path('cus_verify_account/', CustomerAccountVerify.as_view(),name='cus_account_verify'),
    path('login_det/', loginsessionView.as_view(),name='login_details'),
    path('admin_change_pass/', AdminChangePassword.as_view(),
       name='change_admin_pass'),
    path('encode_and_decode/', EncodeAndDecodeView.as_view(),name='encode_and_decode'),
    path('compose_message/', ComposeMessage.as_view(),name='compose_message'),
    path('token_refresh/', TokenRefreshApi.as_view(),name='token_refresh'),
    path('search_menu/', MenuSearchView.as_view(),name='search_menu'),
    path('backup_db/', BackupCurrentDB.as_view(),name='backup_db'),
    path('report_columns_template/', ReportColumnsTemplatesList.as_view(),name='backup_db'),

]
