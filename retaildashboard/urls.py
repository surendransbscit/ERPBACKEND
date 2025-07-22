from django.urls import path
from .views import *

urlpatterns = [
        path('estimation/', EstimationDashView.as_view()),        
        path('customer_vist/', CustomerVistDashView.as_view()),        
        path('sales/', SalesDashView.as_view()),  
        path('customer_order/', CustomerOrderDashView.as_view()),        
        path('sales_return/', SalesReturnDashView.as_view()),        
        path('purchase/', PurchaseDashView.as_view()),  
        path('lot/', LotDashView.as_view()),   
        path('credit_sales/', CreditSalesDashView.as_view()),  
        path('karigar_order/', JobOrderDashView.as_view()),  
        path('top_products/', TopProductSalesDashView.as_view()),
        path('stock_approval/', StockTransferApprovalDashView.as_view()),  
        path('store_statistics/', StoreStatisticsDashView.as_view()),  
        path('po_details/', PoDashView.as_view()),
        
        path('estimation_report/', EstimationDashReportView.as_view()),        
        path('customer_vist_report/', CustomerVistDashReportView.as_view()),        
        path('sales_report/', SalesDashReportView.as_view()),  
        path('sales_return_report/', SalesReturnReportDashView.as_view()),        
        path('purchase_report/', PurchaseDashReportView.as_view()),  
        path('lot_report/',LotDashReportView.as_view()),
        path('credit_sales_report/', CreditSalesDashReportView.as_view()),
        path('karigar_order_report/', JobOrderReportDashView.as_view()),        
        path('customer_order_report/', CustomerOrderReportDashView.as_view()),   
        path('stock_approval_report/', StockTransferApprovalReportDashView.as_view()),  
]