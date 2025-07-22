
ACTION_LIST     = {"is_add_req":True,"is_edit_req":False,"is_delete_req":False,"is_print_req":True,"is_cancel_req":True}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}


TRANCFER_COLUMN_LIST = [SNO_COLUMN,
                    {'accessor': 'trans_code', 'Header': 'Trans Code'},
                    {'accessor': 'trans_date', 'Header': 'Date'},
                    {'accessor': 'transfer_from', 'Header': 'From Branch'},
                    {'accessor': 'transfer_to', 'Header': 'To Branch'},
                    {'accessor': 'issued_to', 'Header': 'Issued To'},
                    {'accessor': 'trans_to_type_name', 'Header': 'Trans To'},
                    {'accessor': 'transfer_type_name', 'Header': 'Transfer Type'},
                    {'accessor': 'gross_wt', 'Header': 'Weight'},
                     {'accessor': 'status', 'Header': 'Status'},
                    ACTION_COLUMN
                    ]



INVOICE_TYPE_CHOICES = [
    (1, 'Sale'),
    (2, 'Purchase'),
    (3, 'Return'),
    (4, 'Sales Purchase'),
    (5, 'Sales Purchase Return')
]

INVOICE_FOR_CHOICES = [
    (1, 'Individual Customer'),
    (2, 'Business Customer')
]

DELIVERY_LOCATION_CHOICES = [
    (1, 'Showroom'),
    (2, 'Customer Address')
]

INVOICE_STATUS_CHOICES = [
    (1, 'Success'),
    (2, 'Canceled')
]
