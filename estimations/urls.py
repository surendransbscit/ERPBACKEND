from django.urls import path

from .views import (ErpEstimationCreateAPIView,ErpEstimationListAPIView,ErpEstimationAPIView,ErpEstimationStockTransferAPIView,
                    ErpEstimationApproveAPIView, ErpEstimationApprovalView, ErpEstimationApprovalPrint,ErpEstimationTagSearch,
                    ErpCalculateOldMetalView,ErpEstimationSearchAPIView)

urlpatterns = [
    path('list/', ErpEstimationListAPIView.as_view()),
    path('search/', ErpEstimationSearchAPIView.as_view()),
    path('create/', ErpEstimationCreateAPIView.as_view()),
    path('update/<int:pk>/', ErpEstimationCreateAPIView.as_view()),
    path('edit/<int:pk>/', ErpEstimationListAPIView.as_view()),
    path('print/<int:pk>/', ErpEstimationCreateAPIView.as_view()),
    path('search_tag/', ErpEstimationTagSearch.as_view()),
    path('calculate_item_details/', ErpEstimationTagSearch.as_view()),
    path('est_details/', ErpEstimationAPIView.as_view()),
    path('est_approve_details/', ErpEstimationApproveAPIView.as_view()),
    path('est_approve/', ErpEstimationApprovalView.as_view()),
    path('est_approve_print/<int:pk>/', ErpEstimationApprovalPrint.as_view()),
    # path('est_details/', ErpEstimationAPIView.as_view()),
    path('est_transfer_details/', ErpEstimationStockTransferAPIView.as_view()),
    path('calculate_old_metal_cost/', ErpCalculateOldMetalView.as_view()),
]