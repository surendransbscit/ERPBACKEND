
ACTION_LIST = {"is_add_req": True, "is_edit_req": True,
               "is_delete_req": True, "is_print_req": False, "is_cancel_req": False}
ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}

EST_COLUMN_LIST = [
                    {'accessor': 'est_no', 'Header': 'Est No'},
                    {'accessor': 'date', 'Header': 'Date'},
                    {'accessor': 'branch_name', 'Header': 'Branch'},
                    {'accessor': 'customer_name', 'Header': 'Customer'},
                    {'accessor': 'customer_mobile', 'Header': 'Mobile'},
                    {'accessor': 'invoice_no', 'Header': 'Invoice No'},
                    {'accessor': 'net_amount', 'Header': 'Amount','isTotalReq': True, 'decimal_places': 2, 'textAlign': 'right','isCurrency':True}
                    ]

CUS_LIST = [
                    SNO_COLUMN,
                    {'accessor': 'cus_name', 'Header': 'Customer Name'},
                    {'accessor': 'pieces', 'Header': 'Pcs','isTotalReq':True,'textAlign':'right',},
                    {'accessor': 'weight', 'Header': 'Weight','isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right',},
                    {'accessor': 'amount', 'Header': 'Amount','isTotalReq': True, 'decimal_places': 2, 'textAlign': 'right','isCurrency':True},
                    ]


SALES_REPORT = [
     SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'S.Design', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'isTotalReq': True, 'textAlign': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right'},
    {'accessor': 'other_metal_wt', 'Header': 'Other Metal', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right'},
    {'accessor': 'mc_value', 'Header': 'Mc', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right','isCurrency':True},
    {'accessor': 'wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'textAlign': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate', 'textAlign': 'left','isCurrency':True},
    {'accessor': 'tax_grp', 'Header': 'Tax(%)', 'textAlign': 'left'},
    {'accessor': 'item_cost', 'Header': 'TOTAL AMT', 'isTotalReq': True, 'decimal_places': 2, 'textAlign': 'right','isCurrency':True}
]

PURCHASE_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Invoice No', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Invoice Date', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'isTotalReq': True, 'textAlign': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right'},
    {'accessor': 'pure_weight', 'Header': 'Pure Wt', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right'},
    {'accessor': 'wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'textAlign': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'isTotalReq': True, 'decimal_places': 3, 'textAlign': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate Per Gram', 'textAlign': 'right','isCurrency':True },
    {'accessor': 'amount', 'Header': 'Total Amount', 'isTotalReq': True, 'decimal_places': 2, 'textAlign': 'right','isCurrency':True }
]

LOT_LIST = [
            SNO_COLUMN,
            {'accessor': 'lot_code', 'Header': 'Lot No'},
            {'accessor': 'rev_pieces', 'Header': 'Received Pcs','isTotalReq':True,'textAlign':'right',},
            {'accessor': 'rev_weight', 'Header': 'Received Weight','isTotalReq':True,'textAlign':'right','decimal_places': 3,},
            {'accessor': 'tag_pieces', 'Header': 'Tagged Pcs','isTotalReq':True,'textAlign':'right',},
            {'accessor': 'tag_weight', 'Header': 'Tagged Weight','isTotalReq':True,'textAlign':'right','decimal_places': 3,},
            {'accessor': 'balance_pcs', 'Header': 'Balance Pcs','isTotalReq':True,'textAlign':'right',},
            {'accessor': 'balance_gwt', 'Header': 'Balance Weight','isTotalReq':True,'textAlign':'right','decimal_places': 3,},
            ]
CREDIT_INVOICE_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Invoice No', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Invoice Date', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'net_amount', 'Header': 'Net Amount', 'isTotalReq': True, 'textAlign': 'right','decimal_places': 2,'isCurrency':True},
    {'accessor': 'received_amount', 'Header': 'Received Amount', 'isTotalReq': True, 'textAlign': 'right','decimal_places': 2,'isCurrency':True},
    {'accessor': 'due_amount', 'Header': 'Due Amount', 'isTotalReq': True, 'textAlign': 'right','decimal_places': 2,'isCurrency':True},
    {'accessor': 'collected_amount', 'Header': 'Collected Amount', 'isTotalReq': True, 'textAlign': 'right','decimal_places': 2,'isCurrency':True},
    {'accessor': 'balance_amount', 'Header': 'Balance Amount', 'isTotalReq': True, 'textAlign': 'right','decimal_places': 2,'isCurrency':True},
]

JOB_ORDER_REPORT = [
    SNO_COLUMN,
    {'accessor': 'ref_no', 'Header': 'Ref No', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'assigned_date', 'Header': 'Assiged Date', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'due_date', 'Header': 'Due Date', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'order_no', 'Header': 'Order No', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'karigar_name', 'Header': 'Supplier', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'status', 'Header': 'Status', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'design_name', 'Header': 'Deisgn', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'isTotalReq': True, 'textAlign': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Grs.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Net.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Less.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
]

CUS_ORDER_REPORT = [
    SNO_COLUMN,
    {'accessor': 'order_no', 'Header': 'Order No', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'order_date', 'Header': 'Order Date', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'customer_due_date', 'Header': 'Due Date', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'design_name', 'Header': 'Deisgn', 'isTotalReq': False, 'textAlign': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'isTotalReq': True, 'textAlign': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Grs.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Net.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Less.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
    {'accessor': 'status', 'Header': 'Status', 'isTotalReq': False, 'textAlign': 'left'},
]

TRANCFER_COLUMN_LIST = [
                    SNO_COLUMN,
                    {'accessor': 'trans_code', 'Header': 'Trans Code'},
                    {'accessor': 'trans_date', 'Header': 'Date'},
                    {'accessor': 'transfer_from', 'Header': 'From Branch'},
                    {'accessor': 'transfer_to', 'Header': 'To Branch'},
                    {'accessor': 'trans_to_type_name', 'Header': 'Trans To'},
                    {'accessor': 'transfer_type_name', 'Header': 'Transfer Type'},
                    {'accessor': 'pcs', 'Header': 'Pcs', 'isTotalReq': True, 'textAlign': 'right'},
                    {'accessor': 'gross_wt', 'Header': 'Grs.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
                    {'accessor': 'net_wt', 'Header': 'Net.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
                    {'accessor': 'less_wt', 'Header': 'Less.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
                    {'accessor': 'stn_wt', 'Header': 'Stn.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
                    {'accessor': 'dia_wt', 'Header': 'Dia.Wt', 'isTotalReq': True, 'textAlign': 'right', 'decimal_places': 3},
                    {'accessor': 'status', 'Header': 'Status'},
                    ]