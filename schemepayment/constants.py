ACTION_LIST     = {"is_add_req":True,"is_edit_req":False,"is_delete_req":False,"is_print_req":True,"is_cancel_req":True,"is_total_req":True}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}

# PROFILE MASTER
PAYMENT_COLUMN_LIST = [
                        {'accessor': 'receipt_no', 'Header': 'Receipt No','width':'8%'},
                        {'accessor': 'date_payment', 'Header': 'Date','width':'10%'},
                        {'accessor': 'branch_name', 'Header': 'Branch'},
                        {'accessor': 'cus_name', 'Header': 'Customer'},
                        {'accessor': 'mobile', 'Header': 'Mobile'},
                        {'accessor': 'scheme_name', 'Header': 'Scheme','width':'10%'},
                        {'accessor': 'account_no', 'Header': 'Acc No', 'hasLink':True},
                        {'accessor': 'installment', 'Header': 'Ins','width':'2%'},
                        {'accessor': 'payment_amount', 'Header': 'Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                        {'accessor': 'metal_weight', 'Header': 'Weight','text_align':'right','is_total_req':True,"decimal_places":3},
                        {'accessor': 'payment_status', 'Header': 'Status','width':'10%'},
                        {'accessor': 'paid_through', 'Header': 'Paid From','width':'5%'},
                        {'accessor': 'employee_name', 'Header': 'Employee'},
                        ACTION_COLUMN
                        ]