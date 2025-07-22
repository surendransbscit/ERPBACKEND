from django.urls import path

from .views import (ErpOrderCreateView, ErpOrderDetailView, ErpOrderListView, ErpOrderDeleteView, ErpOrderEditView,ErpRepairOrderListView,
                    ErpJobOrderCreateView, OpenOrderListView, OrderLinkView, OrderUnLinkView,ErpOrderDropdownView,ErpRepairOrderDeliveryCreateView,
                    JobOrdersListView, JobOrdersUpdateView, CustomerOrdersListView, CustomerOrdersUpdateView, OrderLinkListView,ErpOrderDeliveryDetailView,ErpRepairOrderDeliveryDetailView,
                    CustomerCartListCreateView, CustomerWishlistListCreateView, CustomerWishlistDetailView, CustomerCartDetailsView, ERPAllDetails,ERPTotalOrders, ERPreceivedOrders,
                    ERPTodayDeliveredOrders,ERPYetToAssignOrders,ERPTotalDeliveredOrders,ERPWeekDeliveryOrders,ERPNextWeekDeliveryOrders,
                    ERPOverDueOrderSupplier,ERPCustomerOverDueOrder,ERPTotalDeliveryReady,ERPWorkProgress,ErpOrderPrintView,
                    CustomerCustomizedOrderListView, CustomerCustomizedOrderDetailView, ERPCustomerCartListView, NonAssignedOrderListView,
                    InprogressOrdersListView, ErpPurchaseOrderListView, ErpPurchaseOrderPrintView, ErpPurchaseOrderDeleteView, PurchaseOrderStatusListView,
                    PurchaseOrderStatusUpdateView, ErpPurchaseOrderDetailView, ErpPurchaseOrderPurchaseSoldDetailView,ErpAssignInternalProcess,InternalOrderProcessListView,CustomerOrdersStatusListView,CustomerOrdersDeliveryUpdateView,
                    PurchaseCartListCreateView,ErpOrderAdminAppPrintView)

urlpatterns = [
    path('order/create/', ErpOrderCreateView.as_view()),
    path('order/dropdown/', ErpOrderDropdownView.as_view()),
    path('order/list/', ErpOrderListView.as_view()),
    path('order/<int:pk>/', ErpOrderDetailView.as_view()),
    path('order/print/<int:pk>/', ErpOrderCreateView.as_view()),
    path('repairorder/print/<int:pk>/', ErpOrderCreateView.as_view()),
    path('order/delete/<int:pk>/', ErpOrderDeleteView.as_view()),
    path('order/edit/<int:pk>/', ErpOrderEditView.as_view()),
    path('order_details_pdf/print/<int:pk>/', ErpOrderAdminAppPrintView.as_view()),
    
    
    #Purchase Orders
    path('purchase_order/list/', ErpPurchaseOrderListView.as_view()),
    path('purchase_order/<int:pk>/', ErpPurchaseOrderDetailView.as_view()),
    path('purchase_order/print/<int:pk>/', ErpPurchaseOrderPrintView.as_view()),
    path('purchase_order/delete/<int:pk>/', ErpPurchaseOrderDeleteView.as_view()),
    path('purchase_order_status/list/', PurchaseOrderStatusListView.as_view()),
    path('purchase_order_status/update/', PurchaseOrderStatusUpdateView.as_view()),
    path('purchase_order_purchase_sold/', ErpPurchaseOrderPurchaseSoldDetailView.as_view()),
    


    path('job_order/create/', ErpJobOrderCreateView.as_view()),
    path('open_orders/list/', OpenOrderListView.as_view()),
    path('order_link/list/', OrderLinkListView.as_view()),
    path('order/link/', OrderLinkView.as_view()),
    path('order/unlink/', OrderUnLinkView.as_view()),
    path('order/customer_orders/list/', CustomerOrdersListView.as_view()),
    path('order/customer_orders/update/', CustomerOrdersUpdateView.as_view()),
    path('order/customer_orders_deliverd/update/', CustomerOrdersDeliveryUpdateView.as_view()),
    path('order/job_orders/list/', JobOrdersListView.as_view()),
    path('order/job_orders/update/', JobOrdersUpdateView.as_view()),
    path('orderdelivery/', ErpOrderDeliveryDetailView.as_view()),
    path('repairorderdelivery/', ErpRepairOrderDeliveryDetailView.as_view()),
    path('repairorderdelivery/create/', ErpRepairOrderDeliveryCreateView.as_view()),
    path('repairorder/list/', ErpRepairOrderListView.as_view()),
    path('customercart/', CustomerCartListCreateView.as_view()),
    path('customercart/<int:pk>/', CustomerCartDetailsView.as_view()),
    path('purchasecart/', PurchaseCartListCreateView.as_view()),
    # path('customercart/<int:pk>/', CustomerCartDetailsView.as_view()),
    path('customerwishlist/', CustomerWishlistListCreateView.as_view()),
    path('customerwishlist/<int:pk>/', CustomerWishlistDetailView.as_view()),
    path('customized_order/list/', CustomerCustomizedOrderListView.as_view()),
    path('customized_order/<int:pk>/', CustomerCustomizedOrderDetailView.as_view()),
    
    path('orderdetails/',ERPAllDetails.as_view()),
    path('totalorderdetails/',ERPTotalOrders.as_view()),
    path('todayreciveddetails/',ERPreceivedOrders.as_view()),
    path('erptodaydeliveredorders/',ERPTodayDeliveredOrders.as_view()),
    path('erpyettoassignorders/',ERPYetToAssignOrders.as_view()),
    path('erptotaldeliveredorders/',ERPTotalDeliveredOrders.as_view()),
    path('erpweekdeliveryorders/',ERPWeekDeliveryOrders.as_view()),
    path('erpnextweekdeliveryorders/',ERPNextWeekDeliveryOrders.as_view()),
    path('erpoverdueordersupplier/',ERPOverDueOrderSupplier.as_view()),
    path('erpcustomeroverdueorder/',ERPCustomerOverDueOrder.as_view()),
    path('erptotaldeliveryready/',ERPTotalDeliveryReady.as_view()),
    path('erpworkprogress/',ERPWorkProgress.as_view()),
    path('erpcustomercart/',ERPCustomerCartListView.as_view()),
    
    path('non_assigned_orders/',NonAssignedOrderListView.as_view()),
    path('in_progress_orders/',InprogressOrdersListView.as_view()),

    # Internal order process
    path('internal_process_status/',InternalOrderProcessListView.as_view()),
    path('order/assign_internal_process/', ErpAssignInternalProcess.as_view()),

    # Repair Order Status
    path('order/repair_order_status/list/', CustomerOrdersStatusListView.as_view()),
]