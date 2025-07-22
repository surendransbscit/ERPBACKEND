
# constants.py

ACTION_LIST     = {"is_add_req":True,"is_edit_req":True,"is_delete_req":True,"is_print_req":False,"is_cancel_req":False}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}
FILTERS = {"isSchemeFilterReq":False,"isBranchFilterReq":False,"isDateFilterReq":False}


#EMPLOYEE MASTER
EMPLOYEE_COLUMN_LIST = [
                        {'accessor': 'image', 'Header': 'Image','text_align':'left'},
                        {'accessor': 'firstname', 'Header': 'Employee Name','text_align':'left'},
                        {'accessor': 'emp_code', 'Header': 'Code','text_align':'left'},
                        {'accessor':'department','Header':'Department','text_align':'left'},
                        {'accessor':'mobile','Header':'Mobile','text_align':'left'},
                        {'accessor': 'is_active', 'Header': 'Status','text_align':'left'},ACTION_COLUMN]
EMPLOYEE_ACTION_LIST = ACTION_LIST
