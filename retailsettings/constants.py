ACTION_LIST = {"is_add_req": True, "is_edit_req": True,
               "is_delete_req": True, "is_print_req": False, "is_cancel_req": False}
ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}

#SETTINGS
SETTINGS_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'name', 'Header': 'Name'}, {
    'accessor': 'value', 'Header': 'Value'}, {'accessor': 'description', 'Header': 'Description'}, ACTION_COLUMN]
SETTINGS_ACTION_LIST = ACTION_LIST.copy()