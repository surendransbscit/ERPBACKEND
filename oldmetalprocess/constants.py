ACTION_LIST     = {"is_add_req":True,"is_edit_req":False,"is_delete_req":False,"is_print_req":False,"is_cancel_req":False,"is_total_req":True}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}

# SCHEME ACCOUNTER
POCKET_COLUMN_LIST = [
                    {'accessor': 'pocket_no', 'Header': 'Pocket No'},
                    {'accessor': 'entry_date', 'Header': 'Date'},
                    {'accessor': 'type_name', 'Header': 'Type'},
                    {'accessor': 'id_branch__name', 'Header': 'Branch'},
                    {'accessor': 'pieces', 'Header': 'Pcs','text_align':'right','is_total_req':True,},
                    {'accessor': 'gross_wt', 'Header': 'Gross Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'net_wt', 'Header': 'Net Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
                    {'accessor': 'less_wt', 'Header': 'Less.Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
                    {'accessor': 'dia_wt', 'Header': 'Dia.Wt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
                    {'accessor': 'stone_wt', 'Header': 'Stn.Wt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
                    ]
POCKET_TYPE = [(1, 'Sales Return'),(2, 'Partly sale'),(3, 'Old Metal'),(4, 'Tagged Item'),(5, 'QC Rejected Pcs'),(6, 'Halmarked Pcs')]
