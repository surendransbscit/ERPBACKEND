# constants.py

ACTION_LIST = {"is_add_req": True, "is_edit_req": True, "is_delete_req": True,
               "is_print_req": False, "is_cancel_req": False, "is_revert_req": False, "is_total_req":False}
ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}


# DISCOUNT
DISCOUNT_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'discount_name', 'Header': 'Discount Name',
                                        'text_align': 'left'},
                                    {'accessor': 'discount_type', 'Header': 'Discount Type',
                                        'text_align': 'left'},
                                    {'accessor': 'discount_value', 'Header': 'Discount Value',
                                        'text_align': 'left'},
                                    {'accessor': 'is_active', 'Header': 'Status', 'text_align': 'left'},
                                     ACTION_COLUMN]
DISCOUNT_ACTION_LIST = ACTION_LIST.copy()
DISCOUNT_ACTION_LIST['is_edit_req'] = True
DISCOUNT_ACTION_LIST['is_delete_req'] = True


# COUPON
COUPON_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'coupon_code', 'Header': 'Coupon Code',
                                        'text_align': 'left'},
                                    {'accessor': 'discount_type', 'Header': 'Discount Type',
                                        'text_align': 'left'},
                                    {'accessor': 'discount_value', 'Header': 'Discount Value',
                                        'text_align': 'left'},
                                    {'accessor': 'is_active', 'Header': 'Status', 'text_align': 'left'}, ACTION_COLUMN]
COUPON_ACTION_LIST = ACTION_LIST.copy()
COUPON_ACTION_LIST['is_edit_req'] = True
COUPON_ACTION_LIST['is_delete_req'] = True



# GIFTVOUCHER
GIFT_VOUCHER_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'voucher_name', 'Header': 'Voucher Name',
                                        'text_align': 'left'},
                                    {'accessor': 'shortcode', 'Header': 'Short Code',
                                        'text_align': 'left'},
                                    {'accessor': 'voucher_amount', 'Header': 'Voucher Amount',
                                        'text_align': 'left'},
                                    {'accessor': 'is_active', 'Header': 'Status', 'text_align': 'left'},ACTION_COLUMN]
GIFT_VOUCHER_ACTION_LIST = ACTION_LIST.copy()
GIFT_VOUCHER_ACTION_LIST['is_edit_req'] = True
GIFT_VOUCHER_ACTION_LIST['is_delete_req'] = True

GIFT_VOUCHER_ISSUE_COLUMN_LIST = [SNO_COLUMN,
                                    {'accessor': 'concated_voucher_code', 'Header': 'Code','text_align': 'center'},
                                    {'accessor': 'issue_to', 'Header': 'Issue To','text_align': 'center'},
                                    {'accessor': 'name', 'Header': 'Name','text_align': 'center'},
                                    {'accessor': 'status', 'Header': 'Status', 'text_align': 'center'},
                                    {'accessor': 'amount', 'Header': 'Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
                                    
                                    ACTION_COLUMN]
GIFT_VOUCHER_ISSUE_ACTION_LIST = ACTION_LIST.copy()
GIFT_VOUCHER_ISSUE_ACTION_LIST['is_edit_req'] = False
GIFT_VOUCHER_ISSUE_ACTION_LIST['is_delete_req'] = False


GIFT_VOUCHER_REPORT_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'Voucher_name', 'Header': 'voucher Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'Voucher_code', 'Header': 'voucher Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Customer Name ', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'employee_name', 'Header': 'Employee Name ', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'supplier_name', 'Header': 'Supplier Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'status', 'Header': 'Status', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'total_amount', 'Header': 'Amount', 'text_align': 'right','is_total_req': True, "decimal_places": 2, 'is_money_format': True},
]
GIFT_VOUCHER_REPORT_ACTION_LIST = ACTION_LIST.copy()
GIFT_VOUCHER_REPORT_ACTION_LIST['is_edit_req'] = False
GIFT_VOUCHER_REPORT_ACTION_LIST['is_delete_req'] = False
GIFT_VOUCHER_REPORT_ACTION_LIST['is_add_req'] = False
GIFT_VOUCHER_REPORT_ACTION_LIST['is_total_req'] = True