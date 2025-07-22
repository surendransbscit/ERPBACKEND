ACTION_LIST     = {"is_add_req":True,"is_edit_req":False,"is_delete_req":False,"is_print_req":True,"is_cancel_req":True,"is_total_req":True}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}

PURCHASE_ENTRY_COLUMN_LIST = [
                    SNO_COLUMN,
                    {'accessor': 'ref_code', 'Header': 'Ref No'},
                    {'accessor': 'entry_date', 'Header': 'Date'},
                    {'accessor': 'id_supplier__supplier_name', 'Header': 'Supplier'},
                    {'accessor': 'id_branch__name', 'Header': 'Branch'},
                    {'accessor': 'total_gross_wt', 'Header': 'Gross Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_net_wt', 'Header': 'Net Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_stn_wt', 'Header': 'Stone Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_dia_wt', 'Header': 'Dia Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'is_active', 'Header': 'Status'},
                    ACTION_COLUMN
                    ]

PURCHASE_ISSUE_COLUMN_LIST = [
                    SNO_COLUMN,
                    {'accessor': 'issue_no', 'Header': 'Issue No'},
                    {'accessor': 'issue_date', 'Header': 'Date'},
                    {'accessor': 'issue_type', 'Header': 'Issue Type'},
                    {'accessor': 'issue_to_emp__firstname', 'Header': 'Employee'},
                    {'accessor': 'total_gross_wt', 'Header': 'Gross Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_net_wt', 'Header': 'Net Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_stn_wt', 'Header': 'Stone Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_dia_wt', 'Header': 'Dia Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_recd_gross_wt', 'Header': 'Recv Gross Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_recd_net_wt', 'Header': 'Recv Net Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_recd_stn_wt', 'Header': 'Recv Stone Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_recd_dia_wt', 'Header': 'Recv Dia Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'status', 'Header': 'Status'},
                    ACTION_COLUMN
                    ]

PURCHASE_ISSUE_ACTION_LIST     = {"is_add_req":True,"is_edit_req":False,"is_delete_req":False,"is_print_req":False,"is_cancel_req":True,"is_total_req":True}

METAL_ISSUE_COLUMN_LIST = [
                    SNO_COLUMN,
                    {'accessor': 'ref_no', 'Header': 'Ref No'},
                    {'accessor': 'issue_date', 'Header': 'Date'},
                    {'accessor': 'branch_name', 'Header': 'Branch'},
                    {'accessor': 'supplier_name', 'Header': 'Supplier'},
                     {'accessor': 'issue_type', 'Header': 'Type'},
                    {'accessor': 'issue_weight', 'Header': 'Issued Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'pure_wt', 'Header': 'Pure Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'status', 'Header': 'Status'},
                    ]

PURCHASE_RETURN_COLUMN_LIST = [
                    SNO_COLUMN,
                    {'accessor': 'entry_date', 'Header': 'Date'},
                    {'accessor': 'supplier_name', 'Header': 'Supplier'},
                    {'accessor': 'branch_name', 'Header': 'Branch'},
                    {'accessor': 'total_gross_wt', 'Header': 'Gross Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_net_wt', 'Header': 'Net Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_pure_wt', 'Header': 'Pure Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                     {'accessor': 'status', 'Header': 'Status'},
                    ACTION_COLUMN
                    ]

METAL_ISSUE_ACTION_LIST     = {"is_add_req":True,"is_edit_req":False,"is_delete_req":False,"is_print_req":False,"is_cancel_req":True,"is_total_req":True}

SUPPLIER_PAYMENT_ACTION_LIST     = {"is_add_req":True,"is_edit_req":False,"is_delete_req":False,"is_print_req":True,"is_cancel_req":True,"is_total_req":True}

SUPPLIER_PAYMENT_COLUMN_LIST = [
                    SNO_COLUMN,
                    {'accessor': 'ref_no', 'Header': 'Ref No'},
                    {'accessor': 'entry_date', 'Header': 'Date'},
                    {'accessor': 'branch_name', 'Header': 'Branch'},
                    {'accessor': 'supplier_name', 'Header': 'Supplier'},
                    {'accessor': 'paid_amount', 'Header': 'Amount','text_align':'right','is_total_req':True,"decimal_places":2},
                    ACTION_COLUMN
                    ]