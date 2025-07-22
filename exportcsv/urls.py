from django.urls import path

from .views import (UploadTagDetailsDataView,UploadCustomerDataView,EmployeeExport, SchemeAbstractExport,UploadTagStatusDataView, 
                    ImportCustomerDataCSVView, ImportEmployeesAPI,ImportMetalCategoryProductCSV, ImportSchemeAccountDetailsView)

urlpatterns = [
    path('employee/', EmployeeExport.as_view()),
    path('scheme_abstract/', SchemeAbstractExport.as_view()),
    path('import_tag/', UploadTagDetailsDataView.as_view()),
    path('import_customer/', UploadCustomerDataView.as_view()),
    path('import_metal_product_cat/', ImportMetalCategoryProductCSV.as_view()),
    path('import_employee/', ImportEmployeesAPI.as_view()),
    path('import_tag_status/', UploadTagStatusDataView.as_view()),
    path('import_scheme_accounts/', ImportSchemeAccountDetailsView.as_view()),
    # path('update_import_installments/', UpdateInstallmentOfImportDatas.as_view()),
]