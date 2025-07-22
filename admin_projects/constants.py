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


# ADMIN PROJECT
ADMIN_PROJECT_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'project_name', 'Header': 'Project Name','text_align':'left',"type":"image"},
    {"accessor": "start_date", "Header":"Start Date", "text_align": "left"},
    {"accessor": "approx_end_date", "Header": "approx end date", "text_align": "left"},
    {"accessor": "final_cost", "Header": "Final Cost", "text_align": "left"},
    ACTION_COLUMN,
]
ADMIN_PROJECT_ACTION_LIST = ACTION_LIST.copy()
ADMIN_PROJECT_ACTION_LIST["is_edit_req"] = True

# ADMIN TASK
ADMIN_TASK_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'task_name', 'Header': 'Task Name','text_align':'left',"type":"image"},
    {"accessor": "start_date", "Header":"Start Date", "text_align": "left"},
    {"accessor": "closed_date", "Header":"Closed Date", "text_align": "left"},
    {"accessor": "status_display", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
ADMIN_TASK_ACTION_LIST = ACTION_LIST.copy()
ADMIN_TASK_ACTION_LIST["is_edit_req"] = True


# SUB TASK
SUB_TASK_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'id_task', 'Header': 'Task Name','text_align':'left'},
    {"accessor": "task_name", "Header":"Sub Task Name", "text_align": "left"},
    {"accessor": "status_display", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
SUB_TASK_ACTION_LIST = ACTION_LIST.copy()
SUB_TASK_ACTION_LIST["is_edit_req"] = True
SUB_TASK_ACTION_LIST["is_delete_req"] = True


# PERFORMANCE INVOICE
ADMIN_PERFORMANCE_COLUMN_LIST = [
    SNO_COLUMN,
    {'accessor': 'ref_no', 'Header': 'Ref No','text_align':'left',"type":"image"},
    {"accessor": "date", "Header":"Date", "text_align": "left"},
    {"accessor": "payment_amount", "Header":"payment_amount", "text_align": "left"},
    ACTION_COLUMN,
]
ADMIN_PERFORMANCE_ACTION_LIST = ACTION_LIST.copy()
ADMIN_PERFORMANCE_ACTION_LIST["is_edit_req"] = True


ADMIN_ERP_ATTENDANCE_COLUMNS = [
    SNO_COLUMN,
    {'accessor': 'firstname', 'Header': 'Employee Name','text_align':'left'},
    {'accessor': 'mobile', 'Header': 'Mobile Number','text_align':'left'},
    {"accessor": "date", "Header":"Date", "text_align": "left"},
    {"accessor": "status", "Header":"status", "text_align": "left"},
    # ACTION_COLUMN,
]
ADMIN_ERP_ATTENDANCE_ACTION_LIST = ACTION_LIST.copy()
ADMIN_PERFORMANCE_ACTION_LIST["is_edit_req"] = False
