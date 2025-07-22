# constants.py

ACTION_LIST     = {"is_add_req":True,"is_edit_req":True,"is_delete_req":True,"is_print_req":False,"is_cancel_req":False}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}

# SCHEME MASTER
SCHEME_COLUMN_LIST = [
                    SNO_COLUMN,
                    {'accessor': 'scheme_name', 'Header': 'Scheme Name','text_align':'left'},
                    {'accessor': 'scheme_code', 'Header': 'Code','text_align':'left'},
                    {'accessor': 'scheme_type', 'Header': 'Scheme Type','text_align':'left'},
                    {'accessor': 'total_instalment', 'Header': 'Installment','text_align':'left'},
                    {'accessor': 'is_active', 'Header': 'Status','text_align':'left'},
                    ACTION_COLUMN
                    ]
# SCHEME_ACTION_LIST = ACTION_LIST.copy()
# SCHEME_ACTION_LIST['is_edit_req'] = True

condition = [
            { "value": 1, "label": "N/A" },
            { "value": 2, "label": "Avg < Y1 ins payable means set Y1 as payable" },
        ]
        
limit_by_arr = [
    { "value": 1, "label": "Amount" },
    { "value": 2, "label": "Weight" },
]

denom_type_arr = [
    { "value": 1, "label": "Multiples" },
    { "value": 2, "label": "Master" },
    { "value": 3, "label": "N/A" },
    { "value": 4, "label": "Grouping" },
]

discount_type_arr = [
    { "value": 1, "label": "Percent" },
    { "value": 2, "label": "Amount" },
]

payment_chance_type_arr = [
    { "value": 1, "label": "Daily" },
    { "value": 2, "label": "Monthly" },
]