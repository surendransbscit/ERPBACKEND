ACTION_LIST     = {"is_add_req":True,"is_edit_req":True,"is_delete_req":True,"is_print_req":False,"is_cancel_req":False,
                   "is_approve_req":False}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}


#CUSTOMER LIST
CUSTOMER_COLUMN_LIST = [
                        {'accessor': 'image', 'Header': 'Image','text_align':'left'},
                        {'accessor':'name','Header':"Name",'text_align':'left'},
                        {'accessor':'mobile','Header':'Mobile','text_align':'left'},
                        {'accessor':'date_add','Header':'Date','text_align':'left'},
                        {'accessor':'area_name','Header':'Area','text_align':'left'},
                        {'accessor':'is_active','Header':'Status','text_align':'left'},
                        {'accessor':'total_accounts','Header':'Accounts','text_align':'left'},
                        ACTION_COLUMN]
CUSTOMER_ACTION_LIST = ACTION_LIST.copy()


APPROVAL_CUSTOMER_COLUMN_LIST = [
                        {'accessor': 'image', 'Header': 'Image','text_align':'left',"type":"image"},
                        {'accessor':'name','Header':"Name"},
                        {'accessor':'mobile','Header':'Mobile'},
                        {'accessor':'date_add','Header':'Registered Date'},
                        {'accessor':'date_of_birth','Header':'DOB'},
                        {'accessor':'area_name','Header':'Area'}]