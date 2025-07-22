# constants.py

ACTION_LIST = {"is_add_req": True, "is_edit_req": True, "is_delete_req": True,
               "is_print_req": False, "is_cancel_req": False, "is_revert_req": False, "is_total_req":False}
ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}


# SIZE
OTHER_INVENTORY_SIZE_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'name', 'Header': 'Size Name',
                                        'text_align': 'left'},
                                    {'accessor': 'value', 'Header': 'Value',
                                        'text_align': 'left'},
                                    {'accessor': 'is_active', 'Header': 'Status', 'text_align': 'left'}, ACTION_COLUMN]
OTHER_INVENTORY_SIZE_ACTION_LIST = ACTION_LIST.copy()
OTHER_INVENTORY_SIZE_ACTION_LIST['is_edit_req'] = True


# ITEM
OTHER_INVENTORY_ITEM_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'name', 'Header': 'Name',
                                        'text_align': 'left'},
                                    {'accessor': 'category_name', 'Header': 'Category Name',
                                        'text_align': 'left'},
                                    {'accessor': 'short_code', 'Header': 'Short Code',
                                        'text_align': 'left'},
                                    ACTION_COLUMN]
OTHER_INVENTORY_ITEM_ACTION_LIST = ACTION_LIST.copy()
OTHER_INVENTORY_ITEM_ACTION_LIST['is_edit_req'] = True


# CATEGORY
OTHER_INVENTORY_CATEGORY_COLUMN_LIST = [SNO_COLUMN,
                                        {'accessor': 'name', 'Header': 'Item Name',
                                         'text_align': 'left'},
                                        {'accessor': 'short_code', 'Header': 'Short Code',
                                            'text_align': 'left'},
                                        {'accessor': 'cat_type', 'Header': 'Category Type',
                                         'text_align': 'left'},
                                        ACTION_COLUMN]
OTHER_INVENTORY_CATEGORY_ACTION_LIST = ACTION_LIST.copy()
OTHER_INVENTORY_CATEGORY_ACTION_LIST['is_edit_req'] = True


PURCHASE_ENTRY_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'ref_code', 'Header': 'Ref No'},
    {'accessor': 'entry_date', 'Header': 'Date'},
    {'accessor': 'supplier__supplier_name', 'Header': 'Supplier'},
    {'accessor': 'branch__name', 'Header': 'Branch'},
    {'accessor': 'total_pcs', 'Header': 'Pieces', 'text_align': 'right',
        'is_total_req': True, "decimal_places": 0},
    {'accessor': 'total_cost', 'Header': 'Cost', 'text_align': 'right',
        'is_total_req': True, "decimal_places": 2, 'isCurrency': True},
    # {'accessor': 'is_active', 'Header': 'Status'},
    ACTION_COLUMN
]
PURCHASE_ENTRY_ACTION_LIST = ACTION_LIST.copy()
PURCHASE_ENTRY_ACTION_LIST['is_edit_req'] = False
PURCHASE_ENTRY_ACTION_LIST['is_cancel_req'] = True
PURCHASE_ENTRY_ACTION_LIST['is_delete_req'] = False


OTHER_INVENTORY_ITEM_ISSUE_COLUMN_LIST = [SNO_COLUMN,
                                          {'accessor': 'branch', 'Header': 'Branch',
                                           'text_align': 'left'},
                                           {'accessor': 'item', 'Header': 'Item',
                                           'text_align': 'left'},
                                            {'accessor': 'pieces', 'Header': 'Pieces',
                                           'text_align': 'left'},
                                          {'accessor': 'scheme_account', 'Header': 'Scheme Name',
                                           'text_align': 'left'},
                                          
                                           
                                          {'accessor': 'issue_to', 'Header': 'Issue Type',
                                              'text_align': 'left'},
                                          ACTION_COLUMN]
OTHER_INVENTORY_ITEM_ISSUE_ACTION_LIST = ACTION_LIST.copy()
OTHER_INVENTORY_ITEM_ISSUE_ACTION_LIST['is_edit_req'] = False
OTHER_INVENTORY_ITEM_ISSUE_ACTION_LIST['is_cancel_req'] = True
OTHER_INVENTORY_ITEM_ISSUE_ACTION_LIST['is_delete_req'] = False


ITEM_LOG_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'inward_pieces', 'Header': 'Inward Pieces', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'outward_pieces', 'Header': 'Outward Pieces', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'closing_balance', 'Header': 'Closing Balance', 'is_total_req': True, 'text_align': 'right'},
]
ITEM_LOG_ACTION_LIST = ACTION_LIST.copy()
ITEM_LOG_ACTION_LIST['is_edit_req'] = False
ITEM_LOG_ACTION_LIST['is_delete_req'] = False
ITEM_LOG_ACTION_LIST['is_add_req'] = False
ITEM_LOG_ACTION_LIST['is_total_req'] = True


PURCHASE_REPORT_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'supplier_name', 'Header': 'Supplier', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'ref_no', 'Header': 'Ref No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'item_name', 'Header': 'Item', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pieces', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'total_amount', 'Header': 'Amount', 'text_align': 'right','is_total_req': True, "decimal_places": 2, 'is_money_format': True},
]
PURCHASE_REPORT_ACTION_LIST = ACTION_LIST.copy()
PURCHASE_REPORT_ACTION_LIST['is_edit_req'] = False
PURCHASE_REPORT_ACTION_LIST['is_delete_req'] = False
PURCHASE_REPORT_ACTION_LIST['is_add_req'] = False
PURCHASE_REPORT_ACTION_LIST['is_total_req'] = True

ISSUE_REPORT_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'item_name', 'Header': 'Item', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'recieved_by', 'Header': 'Recieved By', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'reciever_name', 'Header': 'Reciever Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'issued_by_name', 'Header': 'Issued By', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'issued_for', 'Header': 'Issued For', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'ref_no', 'Header': 'Ref No', 'is_total_req': False, 'text_align': 'left'},
]
ISSUE_REPORT_ACTION_LIST = ACTION_LIST.copy()
ISSUE_REPORT_ACTION_LIST['is_edit_req'] = False
ISSUE_REPORT_ACTION_LIST['is_delete_req'] = False
ISSUE_REPORT_ACTION_LIST['is_add_req'] = False