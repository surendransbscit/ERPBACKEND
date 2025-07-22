from django.urls import path

from .views import (OtherInventorySizeDetailView, OtherInventorySizeListView, OtherInventoryItemListView, OtherInventoryItemDetailView,
                    OtherInventoryCategoryListView, OtherInventoryCategoryDetailView, OtherInventoryPurchaseEntryListView,
                    OtherInventoryPurchaseCreateView, OtherInventoryPurchaseEntryCancelView,OtherInventoryPurchaseReportView,
                    OtherInventoryItemIssueListView, OtherInventoryItemIssueCancelView, OtherInventoryLogReportView,
                    OtherInventoryIssueReportView,ItemMappingView,ItemListView)


urlpatterns = [
    path('size/', OtherInventorySizeListView.as_view()),
    path('size/<int:pk>/', OtherInventorySizeDetailView.as_view()),
    path('category/', OtherInventoryCategoryListView.as_view()),
    path('category/<int:pk>/', OtherInventoryCategoryDetailView.as_view()),
    path('item/', OtherInventoryItemListView.as_view()),
    path('item/<int:pk>/', OtherInventoryItemDetailView.as_view()),
    path('purchase_entry/list/', OtherInventoryPurchaseEntryListView.as_view()),
    path('purchase_entry/create/', OtherInventoryPurchaseCreateView.as_view()),
    path('purchase_entry/cancel/', OtherInventoryPurchaseEntryCancelView.as_view()),
    path('purchase_entry/print/<int:pk>/',
         OtherInventoryPurchaseCreateView.as_view()),
    path('item_issue/', OtherInventoryItemIssueListView.as_view()),
    path('item_issue/cancel/', OtherInventoryItemIssueCancelView.as_view()),
    
    path('log_report/', OtherInventoryLogReportView.as_view()),
    path('purchase_report/', OtherInventoryPurchaseReportView.as_view()),
    path('issue_report/', OtherInventoryIssueReportView.as_view()),

    path('item_mapping/', ItemMappingView.as_view()),
    path('item_mapping/<int:pk>/', ItemMappingView.as_view()),
    path('items/', ItemListView.as_view(), name='item-list'),

]
