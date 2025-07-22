from django.urls import path

from .views import *

urlpatterns = [
    path('purchase_stock_details/', GetPurchaseStockDetails.as_view()),
    path('create_pocket/', CreatePocket.as_view()),
    path('pocket_list/', PocketEntryListView.as_view()),
    path('pocket_for_melting/', PocketDetails.as_view()),
    path('create_metal_process/', CreateMetalProcess.as_view()),
    path('melting_issue_details/', MeltingIssuedDetails.as_view()),
    path('melting_received_details/', MeltingReceivedDetails.as_view()),
    path('testing_issued_details/', TestingIssuedDetails.as_view()),
    path('testing_received_details/', TestingReceivedDetails.as_view()),
    path('refining_issued_details/', RefiningIssuedDetails.as_view()),

]