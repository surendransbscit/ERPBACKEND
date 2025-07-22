# constants.py

ACTION_LIST = {"is_add_req": True, "is_edit_req": True, "is_delete_req": True,
               "is_print_req": False, "is_cancel_req": False, "is_revert_req": False, "is_total_req":False}
ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}


# LOYALTY SIZE
LOYALTY_TIER_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'tier_name', 'Header': 'Tier Name',
                                        'text_align': 'left'},
                                    {'accessor': 'multiplier', 'Header': 'Multiplier',
                                        'text_align': 'left'},
                                    {'accessor': 'min_lifetime_spend', 'Header': 'Min Life Spend', 'text_align': 'left'}, ACTION_COLUMN]
LOYALTY_TIER_ACTION_LIST = ACTION_LIST.copy()
LOYALTY_TIER_ACTION_LIST['is_edit_req'] = True



LOYALTY_SETTINGS_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'base_rate', 'Header': 'Base Rate ',
                                        'text_align': 'left'},
                                    {'accessor': 'point_value', 'Header': 'Point Value',
                                        'text_align': 'left'},
                                    {'accessor': 'max_redeem_percent', 'Header': 'Max Redeem Percent', 'text_align': 'left'},
                                    {'accessor': 'points_validity_days', 'Header': 'Point Validity Days', 'text_align': 'left'},
                                    
                                    ACTION_COLUMN]
LOYALTY_SETTINGS_ACTION_LIST = ACTION_LIST.copy()
LOYALTY_SETTINGS_ACTION_LIST['is_edit_req'] = True



LOYALTY_CUSTOMER_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'customer', 'Header': 'Customer Name',
                                        'text_align': 'left'},
                                    {'accessor': 'current_tier', 'Header': 'Loyalty Tier',
                                        'text_align': 'left'},
                                    {'accessor': 'current_points', 'Header': 'Current Points', 'text_align': 'left'},
                                    {'accessor': 'lifetime_spend', 'Header': 'Life Time Spend', 'text_align': 'left'},
                                    
                                    ACTION_COLUMN]
LOYALTY_CUSTOMER_ACTION_LIST = ACTION_LIST.copy()
LOYALTY_CUSTOMER_ACTION_LIST['is_edit_req'] = True



LOYALTY_TRANSACTION_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'customer', 'Header': 'Customer Name',
                                        'text_align': 'left'},
                                   {'accessor': 'type', 'Header': 'Type', 'text_align': 'left'},
                                    {'accessor': 'points', 'Header': 'Points', 'text_align': 'left'},
                                    {'accessor': 'amount_linked', 'Header': 'Amount Linked', 'text_align': 'left'},
                                    ACTION_COLUMN]
LOYALTY_TRANSACTION_ACTION_LIST = ACTION_LIST.copy()
LOYALTY_TRANSACTION_ACTION_LIST['is_edit_req'] = True