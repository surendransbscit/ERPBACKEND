# constants.py


MC_PER_GRAM = 'Per Gram'
MC_PER_PIECE = 'Per Piece'

BASED_ON_PCS = 'Based on Pieces'
BASED_ON_GRAM = 'Based on Gram'


LOT_TYPE_CHOICES = [
    (1, 'Normal'),
    (2, 'Sales Return'),
    (3, 'Partly Sale'),
    (4, 'Old Metal'),
    (5, 'Lot Merge'),
]

PURE_WT_CALC_TYPE_CHOICES = [
    (1, 'Net weight * Purchase Touch'),
    (2, '(Purchase Touch + Purchase Wastage%) * Net Weight'),
    (3, '(Net weight * Purchase Touch) * Purchase Wastage%'),
]

SERVICE_OPTIONS = [
    {"label":"Customer name", "value":"cus_name"},
    {"label":"Mobile", "value":"mobile"},
    {"label":"OTP", "value":"otp"},
    {"label":"OTP exp time", "value":"validate_sec"},
    {"label":"Company Name", "value":"company_name"},
    {"label":"Scheme Name", "value":"scheme_name"},
    {"label":"Payment Amount", "value":"payment_amount"},
    {"label":"Reciept No.", "value":"receipt_no"},
    {"label":"Gold", "value":"gold_22ct"},
    {"label":"Silver", "value":"silver_G"},
]

PURCHASE_MC_TYPE_CHOICES = [(1, MC_PER_GRAM),(2, MC_PER_PIECE)]

PURCHASE_RATE_TYPE_CHOICES = [(1, MC_PER_GRAM),(2, MC_PER_PIECE)]

PURCHASE_STN_CALC_TYPE_CHOICES = [(1, BASED_ON_GRAM),(2, BASED_ON_PCS)]

TAG_MC_TYPE_CHOICES = [(1, MC_PER_GRAM),(2, MC_PER_PIECE)]

TAG_STN_CALC_TYPE_CHOICES = [(1, BASED_ON_PCS),(2, BASED_ON_GRAM)]

TAG_OTHER_METAL_MC_TYPE_CHOICES = [(1, 'Per Gram'),(2, 'Per Pcs')]

TAG_OTHER_METAL_CALC_TYPE_CHOICES = [(1, 'Per Gram'),(2, 'Per Pcs')]

ITEM_TYPE_CHOICES = [(0, 'Tagged Item'),(1, 'Non Tag Item'),(2, 'Home Bill Item')]

PARTIAL_SALE_CHOICES = [(0, 'No'),(1, 'Yes')]

LOT_STATUS_CHOICES = [(0, 'Pending'),(1, 'Completed')]

MC_TYPE_CHOICES = [(1, 'Per Gram'),(2, 'Per Piece')]

TAX_TYPE_CHOICES = [(1, 'Inclusive'),(2, 'Exclusive')]

STATUS_CHOICES = [(2, 'Returned'),(1, 'Sold'),(0, 'ON SALE')]

DELIVERY_STATUS_CHOICES = [(1, 'Yes'),(2, 'No')]


CEDIT_CHOICES = [(0, 'No'),(1, 'Yes')]


CEDIT_STATUS_CHOICES = [(0, 'Pending'),(1, 'Paid')]

BILL_TYPE_CHOICES = [(1, 'Normal'),(0, 'Eda'),]


TAG_STN_CALC_TYPE_CHOICES = [(1, 'Based on Gram'),(2, 'Based on Pcs')]

FILTERS = {"isSchemeFilterReq":False,"isBranchFilterReq":False,"isDateFilterReq":False, "isProductFilterReq":False,
           "isTagCodeFilterReq":False, "isDeignFilterReq":False, "isSubDeignFilterReq":False, "StockTransferFilterReq":False,
           "isPurityFilterReq":False, "isSupplierFilterReq":False, "isLotFilterReq":False, "isMcTypeFilterReq":False,
           "isMcValueFilterReq":False, "isVaPercentFilterReq":False, "isVaFromToFilterReq":False, "isGwtFromToFilterReq":False,
           "isBranchFromToFilterReq":False, "isMetalFilterReq":False, "isIssueReciptFilterReq":False, "isEmployeeFilterReq": False,
           "isProcessFilterReq":False, "isStockTypeFilterReq":False, "isCustomerFilterReq":False, 'isVoucherIssueStatusFilter':False , 
           "isLotTypeFilterReq" : False}

TRANSACTION = [(1, 'Taging'),(2, 'Billing'),(3, 'Branch Transfer'),
               (4, 'Pending Transfer'),(5, 'Metal Issue'),(6, 'Special Discount Bill'),
               (7, 'Purchase Return'),(8, 'Stock Issue'),(9, 'Sale Import')]

SHOW_IN_LWT_CHOICES = [(0, 'NO'),(1, 'YES')]

METAL_PROCESS_TYPE = [(1, 'Issue'),(2, 'Receipt')]

POCKET_TYPE = [(1, 'Sales Return'),(2, 'Partly sale'),(3, 'Old Metal'),(4, 'Tagged Item'),(5, 'QC Rejected Pcs'),(6, 'Halmarked Pcs'),(7, 'Others')]