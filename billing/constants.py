
ACTION_LIST     = {"is_add_req":True,"is_edit_req":False,"is_delete_req":False,"is_print_req":True,"is_cancel_req":True,"is_total_req":True}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}


INVOICE_COLUMN_LIST = [
                    {'accessor': 'invoice_no', 'Header': 'Invoice No','width':'13%'},
                    {'accessor': 'invoice_date', 'Header': 'Date'},
                    {'accessor': 'branch_name', 'Header': 'Branch'},
                    {'accessor': 'customer_name', 'Header': 'Customer'},
                    {'accessor': 'customer_mobile', 'Header': 'Mobile'},
                    {'accessor': 'sale_wt', 'Header': 'Sale Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'sales_amount', 'Header': 'Sales Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                    {'accessor': 'purchase_amount', 'Header': 'Purchase Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                    {'accessor': 'net_amount', 'Header': 'Net Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                    {'accessor': 'received_amount', 'Header': 'Received Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                    {'accessor': 'status', 'Header': 'Status'},
                    ACTION_COLUMN
                    ]

ISSUE_RECEIPT_COLUMN_LIST = [SNO_COLUMN,
                    {'accessor': 'branch_name', 'Header': 'Branch'},
                    {'accessor': 'bill_no', 'Header': 'Bill No.'},
                    {'accessor': 'bill_date', 'Header': 'Date'},
                    {'accessor': 'type', 'Header': 'Type'},
                    {'accessor': 'employee_name', 'Header': 'Employee'},
                    {'accessor': 'customer_name', 'Header': 'Customer'},
                    {'accessor': 'amount', 'Header': 'Bill Amount', 'text_align':'right'},
                    {'accessor': 'bill_status', 'Header': 'Bill Status'},
                    {'accessor': 'remarks', 'Header': 'Remarks'},
                    ACTION_COLUMN
]



INVOICE_TYPE_CHOICES = [
    (1, 'Sale'),
    (2, 'Purchase'),
    (3, 'Return'),
    (4, 'Sales Purchase'),
    (5, 'Sales Return'),
    (6, 'Sales Purchase Return')
]

INVOICE_FOR_CHOICES = [
    (1, 'Individual Customer'),
    (2, 'Business Customer')
]

INVOICE_TO_CHOICES = [
    (1, 'Retailer'),
    (2, 'Wholesaler')
]

DELIVERY_LOCATION_CHOICES = [
    (1, 'Showroom'),
    (2, 'Customer Address')
]

INVOICE_STATUS_CHOICES = [
    (1, 'Success'),
    (2, 'Canceled')
]



SETTLEMENT_COLUMN_LIST = [SNO_COLUMN,
    {'accessor': 'invoice_date', 'Header': 'Date'},
    {'accessor': 'card_payment_amount', 'Header': 'Card Receivable','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'card_received_amount', 'Header': 'Card Received','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'card_difference_amount', 'Header': 'Card Difference','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'net_banking_payment_amount', 'Header': 'NB Receivable','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'net_banking_received_amount', 'Header': 'NB Received','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'net_banking_difference_amount', 'Header': 'NB Difference','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'upi_payment_amount', 'Header': 'UPI Receivable','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'upi_received_amount', 'Header': 'UPI Received', 'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'upi_difference_amount', 'Header': 'UPI Difference', 'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
]

BILLWISE_TRANSACTION_REPORT = [
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sales_amount', 'Header': 'Sales Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'purchase_amount', 'Header': 'Purchase Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'return_amount', 'Header': 'Return Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'total_discount_amount', 'Header': 'Discount Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'net_amount', 'Header': 'Net Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
]

ISSUERECIEPTWISE_TRANSACTION_REPORT = [
    {'accessor': 'bill_no', 'Header': 'Bill No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'bill_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    # {'accessor': 'sales_amount', 'Header': 'Sales Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    # {'accessor': 'purchase_amount', 'Header': 'Purchase Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    # {'accessor': 'return_amount', 'Header': 'Return Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    # {'accessor': 'total_discount_amount', 'Header': 'Discount Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    # {'accessor': 'net_amount', 'Header': 'Net Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
]

JEWEL_NOT_DELIVERED_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'customer', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'products', 'Header': 'Products', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pieces', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'weight', 'Header': 'Weight', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
    {'accessor': 'outstanding_amount', 'Header': 'Outstanding Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
]

LIABLITY_ENTRY_COLUMNS = [
                    {'accessor': 'bill_no', 'Header': 'Bill No','width':'13%'},
                    {'accessor': 'branch_name', 'Header': 'Branch',},
                    {'accessor': 'supplier_name', 'Header': 'Supplier'},
                    {'accessor': 'entry_date', 'Header': 'Date'},
                    {'accessor': 'amount', 'Header': 'Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                    {'accessor': 'paid_amount', 'Header': 'Paid Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                    ACTION_COLUMN
                    ]
LIABLITY_ENTRY_ACTION_LIST = ACTION_LIST.copy()
LIABLITY_ENTRY_ACTION_LIST["is_print_req"] = True
LIABLITY_ENTRY_ACTION_LIST["is_cancel_req"] = False
LIABLITY_ENTRY_ACTION_LIST["is_total_req"] = False


LIABLITY_PAYMENT_ENTRY_COLUMNS = [
                    {'accessor': 'receipt_no', 'Header': 'Receipt No','width':'13%'},
                    {'accessor': 'supplier_name', 'Header': 'Supplier'},
                    {'accessor': 'payment_date', 'Header': 'Date'},
                    {'accessor': 'payment_amount', 'Header': 'Paid Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                    ACTION_COLUMN
                    ]
LIABLITY_PAYMENT_ENTRY_ACTION_LIST = ACTION_LIST.copy()
LIABLITY_PAYMENT_ENTRY_ACTION_LIST["is_print_req"] = True
LIABLITY_PAYMENT_ENTRY_ACTION_LIST["is_cancel_req"] = False
LIABLITY_PAYMENT_ENTRY_ACTION_LIST["is_total_req"] = True


ERP_CUSTOMER_SALES_LOG_COLUMNS = [
                    {'accessor': 'section_name', 'Header': 'Section','width':'13%'},
                    {'accessor': 'net_wt', 'Header': 'Net Wt'},
                    {'accessor': 'incentive_amount', 'Header': 'Incentive Amount'},
                    # {'accessor': 'payment_amount', 'Header': 'Paid Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                    ACTION_COLUMN
                    ]
ERP_CUSTOMER_SALES_LOG_ACTION_LIST = ACTION_LIST.copy()
# LIABLITY_PAYMENT_ENTRY_ACTION_LIST["is_print_req"] = True
# LIABLITY_PAYMENT_ENTRY_ACTION_LIST["is_cancel_req"] = False
# LIABLITY_PAYMENT_ENTRY_ACTION_LIST["is_total_req"] = True