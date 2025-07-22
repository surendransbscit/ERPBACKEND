from django.urls import path
from .views import (
    ClientMasterListCreateView, ClientMasterRetrieveUpdateDestroyView,
    ModuleMasterListCreateView, ModuleMasterRetrieveUpdateDestroyView,
    ProductMasterListCreateView, ProductMasterRetrieveUpdateDestroyView,
)

urlpatterns = [
    # ClientMaster URLs
    path('clients/', ClientMasterListCreateView.as_view()),
    path('clients/<int:pk>/', ClientMasterRetrieveUpdateDestroyView.as_view()),

    # ModuleMaster URLs
    path('modules/', ModuleMasterListCreateView.as_view()),
    path('modules/<int:pk>/', ModuleMasterRetrieveUpdateDestroyView.as_view()),

    # ProductMaster URLs
    path('products/', ProductMasterListCreateView.as_view()),
    path('products/<int:pk>/', ProductMasterRetrieveUpdateDestroyView.as_view()),
]
