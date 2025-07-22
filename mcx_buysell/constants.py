ACTION_LIST = {"is_add_req": True, "is_edit_req": True, "is_delete_req": True,
               "is_print_req": False, "is_cancel_req": False, "is_revert_req": False, "is_total_req":False}
ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}

# PROFILE MASTER
MCXBUYSELL_COLUMN_LIST = [SNO_COLUMN, 
                          {'accessor': 'date_time', 'Header': 'Date Time', 'text_align': 'left'}, 
                          {'accessor': 'type_label', 'Header': 'type', 'text_align': 'left'}, 
                          {'accessor': 'metal_label', 'Header': 'Metal', 'text_align': 'left'}, 
                          {'accessor': 'bought_from', 'Header': 'Bought From', 'text_align': 'left'}, 
                          {'accessor': 'sold_to', 'Header': 'Sold To', 'text_align': 'left'}, 
                          {'accessor': 'customer_name', 'Header': 'Name', 'text_align': 'left'}, 
                          {'accessor': 'customer_mobile', 'Header': 'Mobile', 'text_align': 'left'}, 
                          {'accessor': 'weight', 'Header': 'Weight', 'text_align': 'right', 'is_total_req': True,"decimal_places": 3}, 
                          {'accessor': 'mt5_rate', 'Header': 'MT Rate', 'text_align': 'right'}, 
                          {'accessor': 'rate_per_gram', 'Header': 'Rate', 'text_align': 'right', 'is_money_format': True}, 
                          {'accessor': 'premium', 'Header': 'Premium', 'text_align': 'right', 'is_money_format': True, 'is_total_req': True, "decimal_places": 2}, 
                          ]
MCXBUYSELL_ACTION_LIST = ACTION_LIST.copy()
MCXBUYSELL_ACTION_LIST['is_edit_req'] = False
MCXBUYSELL_ACTION_LIST['is_add_req'] = True
MCXBUYSELL_ACTION_LIST['is_total_req'] = True
MCXBUYSELL_ACTION_LIST['is_delete_req'] = False