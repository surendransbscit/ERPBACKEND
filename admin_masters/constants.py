# constants.py

ACTION_LIST = {
    "is_add_req": True,
    "is_edit_req": True,
    "is_delete_req": True,
    "is_print_req": False,
    "is_cancel_req": False,
    "is_revert_req": False,
    "is_total_req": False,
}
ACTION_COLUMN = {"accessor": "actions", "Header": "Action"}
SNO_COLUMN = {"accessor": "sno", "Header": "S.No"}


# ADMIN MASTER
ADMIN_MASTER_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'image', 'Header': 'Image','text_align':'left',"type":"image"},
    {"accessor": "company_name", "Header":"Company Name", "text_align": "left"},
    {"accessor": "first_name", "Header": "Name", "text_align": "left"},
    {"accessor": "mobile", "Header": "Mobile", "text_align": "left"},
    {"accessor": "gst_number", "Header": "GST Number", "text_align": "left"},
    {"accessor": "pan_number", "Header": "PAN Number", "text_align": "left"},
    {"accessor": "email", "Header": "Email", "text_align": "left"},
    ACTION_COLUMN,
]
ADMIN_MASTER_ACTION_LIST = ACTION_LIST.copy()
ADMIN_MASTER_ACTION_LIST["is_edit_req"] = True

# ADMIN MODULE MASTER
ADMIN_MODULE_MASTER_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "module_name", "Header":"name", "text_align": "left"},
    {"accessor": "short_code", "Header": "Short code", "text_align": "left"},
    {"accessor": "approx_cost", "Header": "Approx cost", "text_align": "left"},
    ACTION_COLUMN,
]
ADMIN_MODULE_MASTER_ACTION_LIST = ACTION_LIST.copy()
ADMIN_MODULE_MASTER_ACTION_LIST["is_edit_req"] = True

# ADMIN MASTER PRODUCT
ADMIN_PRODUCT_MASTER_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "product_name", "Header":"name", "text_align": "left"},
    {"accessor": "short_code", "Header": "Short code", "text_align": "left"},
    {"accessor": "Approx_cost", "Header": "Approx cost", "text_align": "left"},
    ACTION_COLUMN,
]
ADMIN_PRODUCT_MASTER_ACTION_LIST = ACTION_LIST.copy()
ADMIN_PRODUCT_MASTER_ACTION_LIST["is_edit_req"] = True