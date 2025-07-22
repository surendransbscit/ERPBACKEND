ACTION_LIST = {"is_add_req": True, "is_edit_req": True, "is_delete_req": False,
               "is_print_req": False, "is_cancel_req": False, "is_total_req": True}


ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}

ORDER_COLUMN_LIST = [SNO_COLUMN,
                    {'accessor': 'order_no', 'Header': 'Order No'},
                    {'accessor': 'branch_name', 'Header': 'Branch'},
                    {'accessor': 'date', 'Header': 'Date'},
                    {'accessor': 'customer_name', 'Header': 'Customer'},
                    {'accessor': 'customer_mobile', 'Header': 'Customer'},
                    {'accessor': 'order_type', 'Header': 'Order Type'},
                    ACTION_COLUMN
]

PURCHASEORDER_COLUMN_LIST = [SNO_COLUMN,
                    {'accessor': 'order_no', 'Header': 'Order No'},
                    {'accessor': 'branch_name', 'Header': 'Branch'},
                    {'accessor': 'date', 'Header': 'Date'},
                    {'accessor': 'supplier_name', 'Header': 'Supplier'},
                    {'accessor': 'order_type', 'Header': 'Order Type'},
                    ACTION_COLUMN
]

PURCHASEORDER_SOLD_PURCHASE_COLUMN_LIST = [SNO_COLUMN,
                    {'accessor': 'supplier_name', 'Header': 'Supplier'},
                    {'accessor': 'purchased_wt', 'Header': 'Pur.Wt', 'decimal_places': 3,'text_align':'right', 'is_total_req':True},
                    {'accessor': 'purchased_pieces', 'Header': 'Pur.Pieces', 'decimal_places': 0,'text_align':'right', 'is_total_req':True},
                    {'accessor': 'sold_wt', 'Header': 'Sold.Wt', 'decimal_places': 3,'text_align':'right', 'is_total_req':True},
                    {'accessor': 'sold_pieces', 'Header': 'Sold.Pieces', 'decimal_places': 0,'text_align':'right', 'is_total_req':True},
                    {'accessor': 'balance_wt', 'Header': 'Bal.Wt', 'decimal_places': 3,'text_align':'right', 'is_total_req':True},
                    {'accessor': 'balance_pieces', 'Header': 'Bal.Pieces', 'decimal_places': 0,'text_align':'right', 'is_total_req':True},
]


ORDER_TOTAL_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'customer_name', 'Header': 'Customer Name','text_align':'left'},
    {'accessor': 'contact_number', 'Header': 'Phone No','text_align':'left'},
    {'accessor': 'order_number', 'Header': 'Order No','text_align':'left'},
    {'accessor': 'date_of_order', 'Header': 'Order Date','text_align':'left'},
    {'accessor': 'total_pieces', 'Header': 'Pcs','text_align':'right'},
    {'accessor': 'gross_weight', 'Header': 'Grs.Wt', 'decimal_places': 3,'text_align':'right', 'is_total_req':True},
    {'accessor': 'net_weight', 'Header': 'Net.Wt', 'decimal_places': 3,'text_align':'right', 'is_total_req':True},
    {'accessor': 'deduction_weight', 'Header': 'Less.Wt', 'decimal_places': 3,'text_align':'right', 'is_total_req':True},
    {'accessor': 'expected_delivery', 'Header': 'Due Date','text_align':'right'},
    {'accessor': 'product_title', 'Header': 'Product','text_align':'left'},
    {'accessor': 'design_title', 'Header': 'Design','text_align':'left'},
    {'accessor': 'status', 'Header': 'Status'}
    # ACTION_COLUMN
]


CUSTOMER_CART_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'customer_name', 'Header': 'Customer Name','text_align':'left'},
    {'accessor': 'customer_mobile', 'Header': 'Phone No','text_align':'left'},
    {'accessor': 'image', 'Header': 'Image','text_align':'left',"type":"image"},
    {'accessor': 'added_on', 'Header': 'Added On','text_align':'left'},
    {'accessor': 'product_name', 'Header': 'Product','text_align':'left'},
    {'accessor': 'design_name', 'Header': 'Design','text_align':'left'},
    {'accessor': 'tag_code', 'Header': 'Tag','text_align':'left'},
    {'accessor': 'pieces', 'Header': 'Pieces', 'decimal_places': 0,'text_align':'right', 'is_total_req':True},
    {'accessor': 'gross_wt', 'Header': 'Grs.Wt', 'decimal_places': 3,'text_align':'right', 'is_total_req':True},
    # ACTION_COLUMN
]
CUSTOMER_CART_ACTION_LIST = ACTION_LIST.copy()

PURCHASE_CART_COLUMN_LIST = [
    {'accessor': 'image', 'Header': 'Image','text_align':'left',"type":"image"},
    {'accessor': 'added_on', 'Header': 'Added On','text_align':'left'},
    {'accessor': 'product_name', 'Header': 'Product','text_align':'left'},
    {'accessor': 'design_name', 'Header': 'Design','text_align':'left'},
    {'accessor': 'pieces', 'Header': 'Pieces', 'decimal_places': 0,'text_align':'right', 'is_total_req':True},
    {'accessor': 'gross_wt', 'Header': 'Grs.Wt', 'decimal_places': 3,'text_align':'right', 'is_total_req':True},
    {'accessor': 'item_cost', 'Header': 'Item Cost', 'decimal_places': 2,'text_align':'right', 'is_total_req':True, 'is_currency':True},
    # ACTION_COLUMN
]
PURCHASE_CART_ACTION_LIST = ACTION_LIST.copy()