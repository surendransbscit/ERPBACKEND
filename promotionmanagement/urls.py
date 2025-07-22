from django.urls import path

from .views import ( DiscountListView , DiscountDetailView,CouponListView,CouponDetailView,VoucherIssueStatusDetailsListView,GiftVoucherIssueReportView,
                    GiftVoucherListView,GiftVoucherDetailView, GiftVoucherIssueListCreateView, CouponSearch,VoucherIssueStatusDetailsUpdateView,GiftVoucherPrintView)


urlpatterns = [
    path('discount/', DiscountListView.as_view()),
    path('discount/<int:pk>/', DiscountDetailView.as_view()),
    path('coupon/', CouponListView.as_view()),
    path('coupon/<int:pk>/', CouponDetailView.as_view()),
    path('gift_voucher/', GiftVoucherListView.as_view()),
    path('gift_voucher/<int:pk>/', GiftVoucherDetailView.as_view()),
    path('voucher_issue/', GiftVoucherIssueListCreateView.as_view()),
    path('gift_voucher/<int:pk>/', GiftVoucherDetailView.as_view()),
    path('voucher_search/', CouponSearch.as_view()),
    path('voucher_issue_status_details_list/', VoucherIssueStatusDetailsListView.as_view()),
    path('voucher_issue_status_details_update/', VoucherIssueStatusDetailsUpdateView.as_view()),
    
    
    path('gift_voucher_issue_report/', GiftVoucherIssueReportView.as_view()),
    path('voucher_issue/print/<int:pk>/', GiftVoucherPrintView.as_view()),
    
]
