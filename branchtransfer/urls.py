from django.urls import path

from .views import ( ErpBranchTransferCreateAPIView,ErpBranchTransferApprovalAPIView,ErpBranchTransferListAPIView,ErpBranchTransferCancelAPIView,ErpOldMetalDetailsAPIView,ErpStockIssuedDetailsAPIView)

urlpatterns = [
    path('create/', ErpBranchTransferCreateAPIView.as_view()),
    path('cancel/', ErpBranchTransferCancelAPIView.as_view()),
    path('list/', ErpBranchTransferListAPIView.as_view()),
    path('print/<int:pk>/', ErpBranchTransferCreateAPIView.as_view()),
    path('approval/', ErpBranchTransferApprovalAPIView.as_view()),
    path('approval/list/', ErpBranchTransferApprovalAPIView.as_view()),
    path('old_metal_details/', ErpOldMetalDetailsAPIView.as_view()),
    path('stock_issued_details/', ErpStockIssuedDetailsAPIView.as_view()),

]