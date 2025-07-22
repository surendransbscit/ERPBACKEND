ACTION_LIST = {"is_add_req": True, "is_edit_req": True,
               "is_delete_req": True, "is_print_req": False, "is_cancel_req": False}
ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}


# MENU MASTER
MENU_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'text', 'Header': 'Name','text_align':'left'},
                    {'accessor': 'link', 'Header': 'Link','text_align':'left'},
                    {'accessor': 'parent_page', 'Header': 'Parent Menu','text_align':'left'},
                    # {'accessor': 'submenus', 'Header': 'Sub Menus','text_align':'left'},
                    {'accessor': 'order', 'Header': 'Order',},
                    {'accessor': 'is_active', 'Header': 'Status'},
                    ACTION_COLUMN]
MENU_ACTION_LIST = ACTION_LIST
