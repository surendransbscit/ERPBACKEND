# constants.py

ACTION_LIST     = {"is_add_req":True,"is_edit_req":True,"is_delete_req":True,"is_print_req":False,"is_cancel_req":False,
                   "is_revert_close_req": False, "is_total_req":True}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}

# SCHEME ACCOUNTER
SCHEME_ACCOUNT_COLUMN_LIST = [SNO_COLUMN,
                              {'accessor': 'account_name', 'Header': 'Account Name', 'text_align':'left'},
                              {'accessor': 'scheme_acc_number', 'Header': 'Acc No'},
                              {'accessor': 'branch_name', 'Header': 'Branch', 'text_align':'left'},
                              {'accessor': 'start_date', 'Header': 'Date',},
                              {'accessor': 'customer_name', 'Header': 'Customer', 'text_align':'left'}, 
                              {'accessor': 'mobile', 'Header': 'Mobile', 'text_align':'left'},
                              {'accessor': 'scheme_name', 'Header': 'Scheme', 'text_align':'left'},
                              {'accessor': 'paid_installments', 'Header': 'Paid Ins'},
                              {'accessor': 'total_paid_weight', 'Header': 'Paid Weight', 'text_align':'right', 'is_total_req':True, 'decimal_places':3},
                              {'accessor': 'total_paid_amount', 'Header': 'Paid Amount', 'text_align':'right', 'is_total_req':True, 'decimal_places':2},
                              ACTION_COLUMN]

SCHEME_CLOSED_ACCOUNT_COLUMN_LIST = [SNO_COLUMN,
                                     {'accessor': 'branch_name', 'Header': 'Branch'},
                                     {'accessor': 'customer_name', 'Header': 'Customer'}, 
                                     {'accessor': 'mobile', 'Header': 'Mobile'},
                                     {'accessor': 'scheme_name', 'Header': 'Scheme'}, 
                                     {'accessor': 'scheme_acc_number', 'Header': 'Acc No'},
                                     {'accessor': 'account_name', 'Header': 'Acc Name'},
                                     {'accessor': 'start_date', 'Header': 'Start Date'}, 
                                     {'accessor': 'closing_date', 'Header': 'Closed Date'}, 
                                     {'accessor': 'closing_amount', 'Header': 'Closing Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                     {'accessor': 'closing_weight', 'Header': 'Closing Weight', 'is_total_req':True, 'decimal_places':3,'text_align':'right','is_money_format':False},
                                     {'accessor': 'bonus_weight', 'Header': 'Bonus Weight', 'is_total_req':True, 'decimal_places':3,'text_align':'right','is_money_format':False},
                                     {'accessor': 'closed_by', 'Header': 'Closed By'},
                                    #  {'accessor': 'closing_balance', 'Header': 'Closing Balance', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                     
                                     ACTION_COLUMN
                                    ]
# SCHEME_CLOSED_ACCOUNT_ACTION_LIST = {"is_add_req":False,"is_edit_req":False,"is_delete_req":False,"is_print_req":False,"is_cancel_req":False, 'is_revert_close_req':True, "is_total_req":True}
# SCHEME_ACCOUNT_ACTION_LIST = ACTION_LIST.copy()
# SCHEME_ACCOUNT_ACTION_LIST['is_revert_close_req'] = True



