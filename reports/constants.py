# constants.py

ACTION_LIST     = {"is_add_req":False,"is_edit_req":True,"is_delete_req":True,"is_print_req":False,"is_cancel_req":False,"is_total_req":True}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No','text_align':'left',}

# PROFILE MASTER
SCHEME_ABSTRACT_COLUMN_LIST = [
                                {'accessor': 'receipt_no', 'Header': 'Receipt No', 'is_total_req':False,'text_align':'center','width':'10%;'},
                                {'accessor': 'entry_date', 'Header': 'Date','is_total_req':False,'text_align':'center','width':'10%;'},
                                {'accessor': 'scheme_name', 'Header': 'Scheme', 'is_total_req':False,'text_align':'center','width':'10%;'},
                                {'accessor': 'cus_name', 'Header': 'Customer', 'is_total_req':False,'text_align':'center'},
                                {'accessor': 'mobile', 'Header': 'Mobile', 'is_total_req':False,'text_align':'center'},
                                {'accessor': 'scheme_acc_number', 'Header': 'Acc No', 'is_total_req':False,'text_align':'center'},
                                {'accessor': 'payment_amount', 'Header': 'Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                {'accessor': 'discountAmt', 'Header': 'Discount', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                {'accessor': 'net_amount', 'Header': 'Net Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                {'accessor': 'metal_weight', 'Header': 'Weight', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
                                {'accessor': 'metal_rate', 'Header': 'Rate', 'is_total_req':False, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                {'accessor': 'paid_through', 'Header': 'Paid From','is_total_req':False,'text_align':'center'},
                                {'accessor': 'emp_name', 'Header': 'Employee','is_total_req':False,'text_align':'center'},
                               ]

SCHEME_OPENING_AND_CLOSING_COLUMN_LIST = [
                                {'accessor': 'sno', 'Header': 'S.No', 'is_total_req':False,'text_align':'center'},
                                {'accessor': 'scheme_name', 'Header': 'Scheme', 'is_total_req':False,'text_align':'center'},
                                {'accessor': 'opening_blc_amount', 'Header': 'Opening Amt', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                {'accessor': 'opening_blc_weight', 'Header': 'Opening WT', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
                                {'accessor': 'collection_amount', 'Header': 'Collection Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                {'accessor': 'collection_weight', 'Header': 'Collection Weight', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                                {'accessor': 'closed_amount', 'Header': 'Closed Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                {'accessor': 'closed_weight', 'Header': 'Closed Weight', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                                {'accessor': 'closing_balance_amount', 'Header': 'Closing Amt', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                                {'accessor': 'closing_balance_weight', 'Header': 'Closing Wt', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                               ]

CLOSED_ACC_COLUMN_LIST =[{'accessor': 'scheme_acc_number', 'Header': 'Acc No', 'is_total_req':False,'text_align':'left'},
                        {'accessor': 'closing_date', 'Header': 'Closed Date', 'is_total_req':False,'text_align':'left'},
                        {'accessor': 'scheme_name', 'Header': 'Scheme', 'is_total_req':False,'text_align':'left'},
                        {'accessor': 'cus_name', 'Header': 'Customer','is_total_req':False,'text_align':'left'},
                        {'accessor': 'mobile', 'Header': 'mobile','is_total_req':False,'text_align':'left'},
                        {'accessor': 'paid_installment', 'Header': 'Paid Installment', 'is_total_req':True, 'decimal_places':2,'text_align':'left'},
                        {'accessor': 'closing_amount', 'Header': 'Closed Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
                        {'accessor': 'closing_weight', 'Header': 'Closed Weight', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
                        {'accessor': 'closing_benefits', 'Header': 'Benefits', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
                        {'accessor': 'closing_deductions', 'Header': 'Deductions','is_total_req':True, 'decimal_places':2,'text_align':'right'},
                        ]

CUSTOMER_OUTSTANDING_COLUMN_LIST =[
                        {'accessor': 'cus_name', 'Header': 'Customer', 'is_total_req':False,'text_align':'left'},
                        {'accessor': 'mobile', 'Header': 'mobile', 'is_total_req':False,'text_align':'left'},
                        {'accessor': 'area_Header', 'Header': 'Area', 'is_total_req':False,'text_align':'left'},
                        {'accessor': 'total_paid_amount', 'Header': 'Paid Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
                        {'accessor': 'total_paid_weight', 'Header': 'Paid Weight', 'is_total_req':True, 'decimal_places':2,'text_align':'right'}
                        ]


CUSTOMER_UNPAID_REPORT_LIST =[
                        {'accessor': 'sno', 'Header': 'S.No','is_total_req':False,'text_align':'left'},
                        {'accessor': 'scheme_acc_number', 'Header': 'Acc No','is_total_req':False,'text_align':'left'},
                        {'accessor': 'scheme_Header', 'Header': 'Scheme','is_total_req':False,'text_align':'left'},
                        {'accessor': 'cus_Header', 'Header': 'Customer','is_total_req':False,'text_align':'left'},
                        {'accessor': 'mobile', 'Header': 'Mobile', 'is_total_req':False,'text_align':'left'},
                        {'accessor': 'start_date', 'Header': 'Start Date','is_total_req':False,'text_align':'left'},
                        {'accessor': 'total_instalment', 'Header': 'Total Installment', 'is_total_req':True, 'decimal_places':2,'text_align':'center'},
                        {'accessor': 'paid_installment', 'Header': 'Paid Installment', 'is_total_req':True, 'decimal_places':2,'text_align':'center'},
                        {'accessor': 'unpaid_dues', 'Header': 'Unpaid', 'is_total_req':True, 'decimal_places':0,'text_align':'left'},
                        {'accessor': 'paid_amount', 'Header': 'Paid Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
                        {'accessor': 'paid_weight', 'Header': 'Paid Weight', 'is_total_req':True, 'decimal_places':2,'text_align':'right'},
                        ]


STOCK_IN_AND_OUT_REPORT_LIST =[
                        # {'accessor': 'sno', 'Header': 'S.No','is_total_req':False,'text_align':'left'},
                        {'accessor': 'section_name', 'Header': 'Section','is_hidden':True,"showCol":True},
                        {'accessor': 'product_name', 'Header': 'Product','is_total_req':False,'text_align':'left',"showCol":True},
                        {'accessor': 'design_name', 'Header': 'Design','is_total_req':False,'text_align':'left',},
                        #{'accessor': 'sub_design_name', 'Header': 'SUB DESIGN','is_total_req':False,'text_align':'left',},
                        {'accessor': 'op_pieces', 'Header': 'O/P Pcs','is_total_req':True,'text_align':'right',"showCol":True},
                        {'accessor': 'op_gross_wt', 'Header': 'OP Gwt','is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                        {'accessor': 'op_net_wt', 'Header': 'OP Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                       # {'accessor': 'op_less_wt', 'Header': 'OP L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'op_dia_wt', 'Header': 'OP Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'op_stone_wt', 'Header': 'OP Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'inw_pieces', 'Header': 'Inw Pcs','is_total_req':True,'text_align':'right',"showCol":True},
                        {'accessor': 'inw_gross_wt', 'Header': 'Inw Gwt','is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                        {'accessor': 'inw_net_wt', 'Header': 'Inw Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                       # {'accessor': 'inw_les_wt', 'Header': 'INW L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'inw_dia_wt', 'Header': 'Inw Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'inw_stone_wt', 'Header': 'Inw Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'outw_pieces', 'Header': 'Out Pcs','is_total_req':True,'text_align':'right',"showCol":True},
                        {'accessor': 'outw_gross_wt', 'Header': 'Out Gwt','is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                        {'accessor': 'outw_net_wt', 'Header': 'Out Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                       # {'accessor': 'outw_les_wt', 'Header': 'OUTW L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'outw_dia_wt', 'Header': 'Out Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'outw_stone_wt', 'Header': 'Out Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'sales_pieces', 'Header': 'Sales Pcs','is_total_req':True,'text_align':'right',"showCol":True},
                        {'accessor': 'sales_gross_wt', 'Header': 'Sales Gwt','is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                        {'accessor': 'sales_net_wt', 'Header': 'Sales Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                       # {'accessor': 'sales_les_wt', 'Header': 'Sales L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'sales_dia_wt', 'Header': 'Sales Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'sales_stone_wt', 'Header': 'Sales Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'closing_pieces', 'Header': 'Clc Pcs','is_total_req':True,'text_align':'right',"showCol":True},
                        {'accessor': 'closing_gross_wt', 'Header': 'Clc Gwt','is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                        {'accessor': 'closing_net_wt', 'Header': 'Clc Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                      #  {'accessor': 'closing_les_wt', 'Header': 'CLOSING L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'closing_dia_wt', 'Header': 'Clc Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'closing_stone_wt', 'Header': 'Cls stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'issue_pieces', 'Header': 'Iss Pcs','is_total_req':True,'text_align':'right',"showCol":True},
                        {'accessor': 'issue_gross_wt', 'Header': 'Iss Gwt','is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                        {'accessor': 'issue_net_wt', 'Header': 'Iss Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,"showCol":False},
                       # {'accessor': 'issued_les_wt', 'Header': 'Iss L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'issue_dia_wt', 'Header': 'Iss Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        {'accessor': 'issue_stone_wt', 'Header': 'Iss Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right',"showCol":False},
                        ]

AVAILABLE_TAG_REPORT_LIST = [
    #{'accessor': 'image', 'Header': 'Image','text_align':'center','width':'10%;'},
    {'accessor': 'tag_code', 'Header': 'Tag No', 'is_total_req': False, 'text_align': 'left','width':'10%;'},
    {'accessor': 'old_tag_code', 'Header': 'Old Tag No', 'is_total_req': False, 'text_align': 'left','width':'10%;'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'metal_name', 'Header': 'Metal', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'S.Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'size_name', 'Header': 'Size', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_code', 'Header': 'Lot No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'current_branch', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'supplier_name', 'Header': 'Supplier', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_dia_wt', 'Header': 'Dwt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_stn_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_other_metal_wt', 'Header': 'Other Metal', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_mc_value', 'Header': 'MC', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'tag_wastage_wt', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_purity', 'Header': 'Purity', 'is_total_req': False, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_huid', 'Header': 'Huid', 'text_align': 'right'},
    {'accessor': 'tag_huid2', 'Header': 'Huid2', 'text_align': 'right'},
    {'accessor': 'tag_sell_rate', 'Header': 'S.rate', 'decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'tag_item_cost', 'Header': 'Cost', 'is_total_req': True, 'decimal_places': 2,'is_money_format':True ,'text_align': 'right'},
    {'accessor': 'tag_date', 'Header': 'Created On', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'section_name', 'Header': 'section', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'stock_age', 'Header': 'Age', 'is_total_req': False, 'text_align': 'left'}

]

STOCK_TRANSFER_APPROVAL_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'trans_code', 'Header': 'Tranc Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'trans_date', 'Header': 'Tranc Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'transfer_type_name', 'Header': 'Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'trans_to_type_name', 'Header': 'Trans To', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'issue_type', 'Header': 'Issue Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'status', 'Header': 'Trans Status', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Grs.Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Net.Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Less.Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia.Wt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stn_wt', 'Header': 'Stn.Wt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'approved_by', 'Header': 'APPROVED BY', 'is_total_req': False,  'text_align': 'left'},
    {'accessor': 'approved_date', 'Header': 'APPROVED ON', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'downloaded_by', 'Header': 'DOWNLOADED BY', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'downloaded_date', 'Header': 'DOWNLOADED ON', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'rejected_by', 'Header': 'REJECTED ON', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'rejected_on', 'Header': 'REJECTED BY', 'is_total_req': False, 'text_align': 'left'},
]



STOCK_TRANSFER_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'trans_code', 'Header': 'TRANS CODE', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'trans_date', 'Header': 'TRANS DATE', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'transfer_from', 'Header': 'FROM BRANCH', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'transfer_to', 'Header': 'TO BRANCH', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'transfer_type_name', 'Header': 'TRANS TYPE', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'trans_to_type_name', 'Header': 'TRANS TO', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'status', 'Header': 'TRANS STATUS', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'TAG CODE', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'PRODUCT', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'DESIGN', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'SUB DESIGN', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'PCS', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'GRS.WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'NET.WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'LESS.WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'DIA.WT', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stn_wt', 'Header': 'STN.WT', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'approved_by', 'Header': 'APPROVED BY', 'is_total_req': False,  'text_align': 'left'},
    {'accessor': 'approved_date', 'Header': 'APPROVED ON', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'downloaded_by', 'Header': 'DOWNLOADED BY', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'downloaded_date', 'Header': 'DOWNLOADED ON', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'rejected_by', 'Header': 'REJECTED ON', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'rejected_on', 'Header': 'REJECTED BY', 'is_total_req': False, 'text_align': 'left'},
]


SALES_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name','Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'weights', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'status', 'Header': 'Status', 'is_total_req': False,'text_align': 'center' },
    {'accessor': 'net_amount', 'Header': 'Net Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'received_amount', 'Header': 'Received Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': "due_amount", 'Header': "Due Amount",'text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True}
]

SALES_DETAIL_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'Sub Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'section_name', 'Header': 'Section', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'total_mc_value', 'Header': 'Tot.Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'taxable_amount', 'Header': 'Taxable', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tax_amount', 'Header': 'Tax', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'item_cost', 'Header': 'Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'emp_name', 'Header': 'Employee', 'is_total_req': False, 'text_align': 'left'}
]

ESTIMATE_SALES_REPORT = [
    {'accessor': 'est_no', 'Header': 'EstNO', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'entry_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Customer', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'section_name', 'Header': 'Section', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'total_mc_value', 'Header': 'Tot.Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'item_cost', 'Header': 'Item Cost', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'emp_name', 'Header': 'Emp Name', 'text_align': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Invoice No','width':'13%'},
    {'accessor': 'status', 'Header': 'Status'},
]

ESTIMATE_SALES_RETURN_REPORT = [
    {'accessor': 'est_no', 'Header': 'EstNO', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'entry_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Customer', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'section_name', 'Header': 'Section', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'total_mc_value', 'Header': 'Tot.Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'emp_name', 'Header': 'Emp Name', 'text_align': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Invoice No','width':'13%'},
    {'accessor': 'status', 'Header': 'Status'},
]

ESTIMATE_PURCHASE_REPORT = [
    {'accessor': 'est_no', 'Header': 'EstNO', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'entry_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Customer', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'dust_wt', 'Header': 'Dust.Wt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'emp_name', 'Header': 'Emp Name', 'text_align': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Invoice No','width':'13%'},
    {'accessor': 'status', 'Header': 'Status'},
]


SALES_SUMMARY_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'short_code', 'Header': 'Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'grosswt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'netwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lesswt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'diawt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stonewt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'wastage_wt', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'taxable', 'Header': 'Taxable', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tax', 'Header': 'Tax', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tot_amount', 'Header': 'Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]
SALES_SECTION_SUMMARY_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'section_name', 'Header': 'Section', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'short_code', 'Header': 'Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'grosswt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'netwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lesswt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'diawt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stonewt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'wastage_wt', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'taxable', 'Header': 'Taxable', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tax', 'Header': 'Tax', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tot_amount', 'Header': 'Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]
SALES_DESIGN_SUMMARY_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'grosswt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'netwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lesswt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'diawt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stonewt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'wastage_wt', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'taxable', 'Header': 'Taxable', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tax', 'Header': 'Tax', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tot_amount', 'Header': 'Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]
PURCHASE_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Invoice No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Invoice Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'metal_name', 'Header': 'Metal', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dust_wt', 'Header': 'Dust', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'pure_weight', 'Header': 'Pure Wt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    # {'accessor': 'wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'text_align': 'right'},
    # {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate Per Gram', 'text_align': 'right','is_money_format':True },
    {'accessor': 'amount', 'Header': 'Total Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True }
]

PURCHASE_RETURN_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'ref_no', 'Header': 'Ref No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'center'},
    {'accessor': 'purchase_type', 'Header': 'Purchase Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'stock_type', 'Header': 'Stock Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'supplier_name', 'Header': 'Supplier', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'piece', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'pure_wt', 'Header': 'Pure Wt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tax_amount', 'Header': 'Tax Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
    {'accessor': 'item_cost', 'Header': 'Total Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
    {'accessor': 'status', 'Header': 'Status', 'is_total_req': False,'text_align': 'center' },
]

CASH_ABSTRACT_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'PRODUCT', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'PCS', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'GRS.WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'NET.WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'LESS.WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'DIA.WT', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'STN.WT', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'other_metal_wt', 'Header': 'OTHER.WT', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'taxable_amount', 'Header': 'TAXABLE AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
    {'accessor': 'tax_amount', 'Header': 'TAX AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
    {'accessor': 'item_cost', 'Header': 'TOTAL AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True }
]


STOCK_AUDIT_REPORT_LIST =[
                        # {'accessor': 'sno', 'Header': 'S.No','is_total_req':False,'text_align':'left'},
                        {'accessor': 'product_name', 'Header': 'Product','is_total_req':False,'text_align':'left',},
                        #{'accessor': 'design_name', 'Header': 'DESIGN','is_total_req':False,'text_align':'left',},
                        #{'accessor': 'sub_design_name', 'Header': 'SUB DESIGN','is_total_req':False,'text_align':'left',},
                        {'accessor': 'op_pieces', 'Header': 'O/P Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'op_gross_wt', 'Header': 'OP Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'op_net_wt', 'Header': 'OP Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                       # {'accessor': 'op_less_wt', 'Header': 'OP L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'op_dia_wt', 'Header': 'OP Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'op_stone_wt', 'Header': 'OP Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'scanned_pieces', 'Header': 'Scanned Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'scanned_gross_wt', 'Header': 'Scanned Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'scanned_net_wt', 'Header': 'Scanned Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                      #  {'accessor': 'closing_les_wt', 'Header': 'CLOSING L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'scanned_diawt', 'Header': 'Scanned Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'scanned_stonewt', 'Header': 'Scanned stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'unscanned_pieces', 'Header': 'Unscanned Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'unscanned_gross_wt', 'Header': 'Unscanned Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'unscanned_net_wt', 'Header': 'Unscanned Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                      #  {'accessor': 'closing_les_wt', 'Header': 'CLOSING L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'unscanned_diawt', 'Header': 'Unscanned Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'unscanned_stonewt', 'Header': 'Unscanned stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                    #     {'accessor': 'inw_pieces', 'Header': 'Inw Pcs','is_total_req':True,'text_align':'right',},
                    #     {'accessor': 'inw_gross_wt', 'Header': 'Inw Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                    #     {'accessor': 'inw_net_wt', 'Header': 'Inw Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                    #    # {'accessor': 'inw_les_wt', 'Header': 'INW L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                    #     {'accessor': 'inw_dia_wt', 'Header': 'Inw Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                    #     {'accessor': 'inw_stone_wt', 'Header': 'Inw Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'outw_pieces', 'Header': 'Out Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'outw_gross_wt', 'Header': 'Out Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'outw_net_wt', 'Header': 'Out Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'outw_les_wt', 'Header': 'OUTW L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'outw_dia_wt', 'Header': 'Out Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'outw_stone_wt', 'Header': 'Out Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'closing_pieces', 'Header': 'Clc Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'closing_gross_wt', 'Header': 'Clc Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'closing_net_wt', 'Header': 'Clc Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                      #  {'accessor': 'closing_les_wt', 'Header': 'CLOSING L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'closing_dia_wt', 'Header': 'Clc Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'closing_stone_wt', 'Header': 'Cls stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        ]

STOCK_AUDIT_DETAIL_REPORT_LIST = [
    SNO_COLUMN,
    {'accessor': 'tag_code', 'Header': 'Tag No', 'is_total_req': False, 'text_align': 'left','width':'10%;'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    # {'accessor': 'sub_design_name', 'Header': 'S.Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 0},
    {'accessor': 'tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'scale_wt', 'Header': 'Scale Wt.', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_weight', 'Header': 'Bal. Wt.', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    # {'accessor': 'tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    # {'accessor': 'tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    # {'accessor': 'tag_dia_wt', 'Header': 'Dwt', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    # {'accessor': 'tag_stn_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
]

B2B_SALES_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'gst_number', 'Header': 'GST No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pan_number', 'Header': 'PAN No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'taxable', 'Header': 'Taxable', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True },
    {'accessor': 'tax', 'Header': 'Tax', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'cgst', 'Header': 'CGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'sgst', 'Header': 'SGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'igst', 'Header': 'IGST', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
    {'accessor': 'cost', 'Header': 'AMOUNT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
]

ADVANCE_REPORT = [
    SNO_COLUMN,
    {'accessor': 'bill_no', 'Header': 'Receipt  No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'bill_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'receipt_type', 'Header': 'Bill Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'amount', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'advadj_amount', 'Header': 'Adv Adj Amt', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'refund_amount', 'Header': 'Refund', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True },
    {'accessor': 'balance_amount', 'Header': 'Balance', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
]

CREDIT_COLLECTION_REPORT = [
    SNO_COLUMN,
    {'accessor': 'bill_no', 'Header': 'Receipt  No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'bill_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'against', 'Header': 'Against', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'amount', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'issued_amount', 'Header': 'Credit Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'received_amount', 'Header': 'Total Recived Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'balance_amount', 'Header': 'Balance Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},


]

CREDIT_INVOICE_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Invoice No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Invoice Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'net_amount', 'Header': 'Net Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'received_amount', 'Header': 'Received Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'due_amount', 'Header': 'Due Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
]


ADVANCE_ADJ_REPORT = [
    SNO_COLUMN,
    {'accessor': 'adj_invoice_no', 'Header': 'Adjusted Invoice  No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'bill_no', 'Header': 'Receipt  No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'bill_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'amount', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},

]


CHIT_ADJ_REPORT = [
    SNO_COLUMN,
    {'accessor': 'bill_no', 'Header': 'Receipt  No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'bill_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'scheme_name', 'Header': 'Scheme', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_installment', 'Header': 'Paid Installment', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'amount', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},

]


ADV_REFUND_REPORT = [
    SNO_COLUMN,
    {'accessor': 'bill_no', 'Header': 'Receipt  No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'bill_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'amount', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},

]

MODE_COLUMN_LIST =[ 
                SNO_COLUMN,
                {'accessor': 'mode_name', 'Header': 'Mode Name', 'is_total_req':False,'text_align':'left'},
                {'accessor': 'payment_amount', 'Header': 'Payment Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'left'},
                ]


SALES_RETURN_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'metal_name', 'Header': 'Metal', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'S.Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'size_name', 'Header': 'Size', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'weight_range', 'Header': 'Weight Range', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'other_metal_wt', 'Header': 'Other Metal', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'mc_value', 'Header': 'Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right','is_money_format':True},
    {'accessor': 'wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate', 'text_align': 'right','is_money_format':True},
    {'accessor': 'item_cost', 'Header': 'TOTAL AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]

SALES_RETURN_SUMMARY_REPORT = [
    SNO_COLUMN,
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'metal_name', 'Header': 'Metal', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate', 'text_align': 'right','is_money_format':True},
    {'accessor': 'item_cost', 'Header': 'TOTAL AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]

EMPLOYEE_SALES_REPORT = [
    {'accessor': 'emp_name', 'Header': 'Employee Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'metal_name', 'Header': 'Metal', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'S.Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'other_metal_wt', 'Header': 'Other Metal', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'mc_value', 'Header': 'Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right','is_money_format':True},
    {'accessor': 'wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate', 'text_align': 'left','is_money_format':True},
    {'accessor': 'tax_grp', 'Header': 'Tax(%)', 'text_align': 'left'},
    {'accessor': 'tax_amount', 'Header': 'Tax Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'item_cost', 'Header': 'TOTAL AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]


PETTY_CASH_REPORT =[ 
                SNO_COLUMN,
                {'accessor': 'bill_no', 'Header': 'Receipt  No', 'is_total_req': False, 'text_align': 'left'},
                {'accessor': 'bill_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
                {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
                {'accessor': 'issue_to', 'Header': 'Issue To', 'is_total_req': False, 'text_align': 'left'},
                {'accessor': 'borrower_name', 'Header': 'Borrower  Name', 'is_total_req': False, 'text_align': 'left'},
                {'accessor': 'borrower_mobile', 'Header': 'Borrower Mobile', 'is_total_req': False, 'text_align': 'left'},
                {'accessor': 'amount', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
                {'accessor': 'remarks', 'Header': 'Remarks', 'is_total_req': False, 'text_align': 'left'},
                ]

CREDIT_PENDING_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Invoice No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Invoice Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'net_amount', 'Header': 'Net Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'received_amount', 'Header': 'Received Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'due_amount', 'Header': 'Due Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'collected_amount', 'Header': 'Collected Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'balance_amount', 'Header': 'Balance Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
]

CREDIT_ISSUED_PENDING_REPORT = [
    SNO_COLUMN,
    {'accessor': 'bill_no', 'Header': 'Receipt  No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'bill_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'amount', 'Header': 'Due Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'collected_amount', 'Header': 'Collected Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'balance_amount', 'Header': 'Balance Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'remarks', 'Header': 'Remarks', 'is_total_req': False, 'text_align': 'left'},
]

PARTLY_SALES_REPORT = [
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'S.Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Sold Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Sold Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Sold Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Sold Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Sold Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Sold Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'other_metal_wt', 'Header': 'Sold Other Metal', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_pcs', 'Header': 'Tag Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'tag_gwt', 'Header': 'Tag Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_nwt', 'Header': 'Tag Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_lwt', 'Header': 'Tag Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_dia_wt', 'Header': 'Tag Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_stn_wt', 'Header': 'Tag Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_other_metal_wt', 'Header': 'Tag Other Metal', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'mc_value', 'Header': 'Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right','is_money_format':True},
    {'accessor': 'wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate', 'text_align': 'left','is_money_format':True},
    {'accessor': 'tax_grp', 'Header': 'Tax(%)', 'text_align': 'left'},
    {'accessor': 'item_cost', 'Header': 'TOTAL AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]

TAG_WISE_PROFIT_REPORT = [
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'S.Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Sold Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Sold Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Sold Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Sold Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    # {'accessor': 'dia_wt', 'Header': 'Sold Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    # {'accessor': 'stone_wt', 'Header': 'Sold Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    # {'accessor': 'other_metal_wt', 'Header': 'Sold Other Metal', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'mc_value', 'Header': 'Sold Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right','is_money_format':True},
    {'accessor': 'wastage_percentage', 'Header': 'Sold V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'Sold V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Sold Rate', 'text_align': 'left','is_money_format':True},
    {'accessor': 'item_cost', 'Header': 'Sold Cost', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tag_purchase_mc', 'Header': 'Pur Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tag_purchase_va', 'Header': 'Pur V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'tag_purchase_rate', 'Header': 'Pur Rate','decimal_places': 2, 'text_align': 'left','is_money_format':True},
    {'accessor': 'tag_purchase_cost', 'Header': 'Pur Cost', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'profit_cost', 'Header': 'Profit Cost', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}

]

SUPPLIER_WISE_SALES_REPORT = [
    {'accessor': 'supplier_name', 'Header': 'Supplier Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'S.Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'other_metal_wt', 'Header': 'Other Metal', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'mc_value', 'Header': 'Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right','is_money_format':True},
    {'accessor': 'wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate', 'text_align': 'left','is_money_format':True},
    {'accessor': 'tax_grp', 'Header': 'Tax(%)', 'text_align': 'left'},
    {'accessor': 'item_cost', 'Header': 'TOTAL AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]

CANCEL_BILLS_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sales_amount', 'Header': 'Sales Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'purchase_amount', 'Header': 'Purchase Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'net_amount', 'Header': 'Net Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'received_amount', 'Header': 'Received Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'emp_name', 'Header': 'Canceled By', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'canceled_on', 'Header': 'Canceled On', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'remarks', 'Header': 'Canceled Remarks', 'is_total_req': False, 'text_align': 'left'},
]

DISCOUNT_BILLS_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sales_amount', 'Header': 'Sales Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'purchase_amount', 'Header': 'Purchase Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'net_amount', 'Header': 'Net Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'received_amount', 'Header': 'Received Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'total_discount_amount', 'Header': 'Discount Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'discount_per', 'Header': 'Discount Percentage','text_align':'right',},
]

BILLWISE_TRANSACTION_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'counter_name', 'Header': 'Counter', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sales_amount', 'Header': 'Sales Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'purchase_amount', 'Header': 'Purchase Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'return_amount', 'Header': 'Return Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'total_discount_amount', 'Header': 'Discount Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'net_amount', 'Header': 'Net Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
]

PANBILLS_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'gst_number', 'Header': 'GST No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pan_number', 'Header': 'PAN No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'taxable', 'Header': 'Taxable', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True },
    {'accessor': 'tax', 'Header': 'Tax', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'cgst', 'Header': 'CGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'sgst', 'Header': 'SGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'igst', 'Header': 'IGST', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
    {'accessor': 'cost', 'Header': 'AMOUNT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
]

SALES_AND_SALES_RETURN_REPORT = [
    {'accessor': 'type', 'Header': 'Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Inv Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'taxable', 'Header': 'Taxable', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True },
    {'accessor': 'tax', 'Header': 'Tax', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'cgst', 'Header': 'CGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'sgst', 'Header': 'SGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True },
    {'accessor': 'igst', 'Header': 'IGST', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
    {'accessor': 'cost', 'Header': 'AMOUNT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True },
]


SALES_WISE_TARGET_COLUMN_LIST =[
{'accessor': 'section_name', 'Header': 'Section', 'is_total_req':False,'text_align':'left'},
{'accessor': 'product_name', 'Header': 'Product', 'is_total_req':False,'text_align':'left'},
{'accessor': 'from_date', 'Header': 'From Date', 'is_total_req':False,'text_align':'left'},
{'accessor': 'to_date', 'Header': 'To Date','is_total_req':False,'text_align':'left'},
{'accessor': 'target_pieces', 'Header': 'Target Pcs','is_total_req':True,'text_align':'right','decimal_places':0},
{'accessor': 'target_weight', 'Header': 'Target Wt','is_total_req':True,'text_align':'right','decimal_places':3},
{'accessor': 'sold_pcs', 'Header': 'Sold Pcs','is_total_req':True,'text_align':'right','decimal_places':0},
{'accessor': 'sold_weight', 'Header': 'Sold Wt','is_total_req':True,'text_align':'right','decimal_places':3},

]

MELTING_ISSUE_COLUMN_LIST = [
    { 'Header': "Ref No", 'accessor': "ref_no", 'text_align': "center" },
    { 'Header': "Metal Name", 'accessor': "metal_name", 'text_align': "center"},
    { 'Header': "Pcs", 'accessor': "total_pcs", 'text_align': "right", 'is_total_req': True, },
    { 'Header': "Gwt", 'accessor': "total_gross_wt", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True},
    { 'Header': "Nwt", 'accessor': "total_net_wt", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True, },
    { 'Header': "Lwt", 'accessor': "total_less_wt", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},
    { 'Header': "Dia.Wt", 'accessor': "total_dia_wt", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},
    { 'Header': "Stn.Wt", 'accessor': "total_stone_wt", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},

  ]

MELTING_RECIPTS_COLUMN_LIST = [
    { 'Header': "Ref No", 'accessor': "ref_no", 'text_align': "center",  },
    { 'Header': "Product", 'accessor': "product_name", 'text_align': "center"},
    { 'Header': "Pcs", 'accessor': "total_pcs",  'text_align': "right", 'is_total_req': True },
    { 'Header': "Issued Weight", 'accessor': "issue_weight",'decimal_places': 3,'text_align': "right", 'is_total_req': True },
    { 'Header': "Recived Weight", 'accessor': "total_gross_wt", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},
    { 'Header': "Charges", 'accessor': "total_charges", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},
  ]

  
TESTING_ISSUE_COLUMN_LIST = [
    { 'Header': "Ref No", 'accessor': "ref_no", 'text_align': "center" },
  #  { 'Header': "Product", 'accessor': "product_name", 'text_align': "center"},
    { 'Header': "Pcs", 'accessor': "total_pcs", 'text_align': "right", 'is_total_req': True },
    { 'Header': "Weight", 'accessor': "total_tested_weight", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},
  ]

TESTING_RECIPTS_COLUMN_LIST = [
    { 'Header': "Ref No", 'accessor': "ref_no", 'text_align': "center",  },
    #{ 'Header': "Product", 'accessor': "product_name", 'text_align': "center"},
    { 'Header': "Pcs", 'accessor': "total_pcs",  'text_align': "right", 'is_total_req': True },
    { 'Header': "Issued Weight", 'accessor': "total_issue_weight", 'decimal_places': 3, 'text_align': "left", 'is_total_req': True,},
    { 'Header': "Received Weight", 'accessor': "total_received_weight", 'decimal_places': 3, 'text_align': "left", 'is_total_req': True},
    { 'Header': "Charges", 'accessor': "total_charges", 'decimal_places': 3, 'text_align': "left", 'is_total_req': True,},
  ]

REFINING_ISSUE_COLUMN_LIST = [
    { 'Header': "Ref No", 'accessor': "ref_no", 'text_align': "center",  },
    { 'Header': "Product Name", 'accessor': "product_name", 'text_align': "center"},
    { 'Header': "Pcs", 'accessor': "total_pcs",'text_align': "right", 'is_total_req': True },
    { 'Header': "Weight", 'accessor': "total_issue_weight", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True },
  ]

REFINING_RECIPTS_COLUMN_LIST = [
    { 'Header': "Ref No", 'accessor': "ref_no", 'text_align': "center",  },
    { 'Header': "Pcs", 'accessor': "total_pcs",'text_align': "right", 'is_total_req': True },
    { 'Header': "Issued Weight", 'accessor': "total_issue_weight", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},
    { 'Header': "Received Weight", 'accessor': "total_received_weight", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},
    { 'Header': "Charges", 'accessor': "total_charges", 'decimal_places': 3, 'text_align': "right", 'is_total_req': True,},
]

OTHER_STOCK_IN_AND_OUT_REPORT_LIST =[
                        # {'accessor': 'sno', 'Header': 'S.No','is_total_req':False,'text_align':'left'},
                        {'accessor': 'type', 'Header': 'Type','is_hidden':True},
                        {'accessor': 'metal_name', 'Header': 'Metal Name','is_total_req':False,'text_align':'left',},
                        #{'accessor': 'design_name', 'Header': 'DESIGN','is_total_req':False,'text_align':'left',},
                        #{'accessor': 'sub_design_name', 'Header': 'SUB DESIGN','is_total_req':False,'text_align':'left',},
                        {'accessor': 'op_pieces', 'Header': 'O/P Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'op_gross_wt', 'Header': 'OP Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'op_net_wt', 'Header': 'OP Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                       # {'accessor': 'op_less_wt', 'Header': 'OP L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'op_dia_wt', 'Header': 'OP Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'op_stone_wt', 'Header': 'OP Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'inw_pieces', 'Header': 'Inw Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'inw_gross_wt', 'Header': 'Inw Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'inw_net_wt', 'Header': 'Inw Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                       # {'accessor': 'inw_les_wt', 'Header': 'INW L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'inw_dia_wt', 'Header': 'Inw Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'inw_stone_wt', 'Header': 'Inw Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'outw_pieces', 'Header': 'Out Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'outw_gross_wt', 'Header': 'Out Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'outw_net_wt', 'Header': 'Out Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                       # {'accessor': 'outw_les_wt', 'Header': 'OUTW L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'outw_dia_wt', 'Header': 'Out Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'outw_stone_wt', 'Header': 'Out Stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'closing_pieces', 'Header': 'Clc Pcs','is_total_req':True,'text_align':'right',},
                        {'accessor': 'closing_gross_wt', 'Header': 'Clc Gwt','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'closing_net_wt', 'Header': 'Clc Nwt', 'is_total_req':True,'text_align':'right','decimal_places':3,},
                      #  {'accessor': 'closing_les_wt', 'Header': 'CLOSING L.WT','is_total_req':True,'text_align':'right','decimal_places':3,},
                        {'accessor': 'closing_dia_wt', 'Header': 'Clc Dia', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        {'accessor': 'closing_stone_wt', 'Header': 'Cls stn', 'is_total_req':True, 'decimal_places':3,'text_align':'right'},
                        ]

CASH_BOOK_LIST = [
    SNO_COLUMN,
    { 'Header': "Trans Name", 'accessor': "trans_name", 'text_align': "center",  },
    { 'Header': "Credit", 'accessor': "credit",'text_align': "right", 'is_total_req': True,'decimal_places': 2 },
    { 'Header': "Debit", 'accessor': "debit", 'decimal_places': 2, 'text_align': "right", 'is_total_req': True,},
]

OTHER_METAL_PROFIT_LOSS_COLUMN_LIST =[
{'accessor': 'ref_no', 'Header': 'Ref.No', 'is_total_req':False,'text_align':'left'},
{'accessor': 'metal_name', 'Header': 'Metal Name', 'is_total_req':False,'text_align':'left'},
{'accessor': 'supplier_name', 'Header': 'Supllier Name', 'is_total_req':False,'text_align':'left'},
{'accessor': 'dateadd', 'Header': 'Entry Date', 'is_total_req':False,'text_align':'left'},
{'accessor': 'gross_wt', 'Header': 'Gross Wt','is_total_req':True,'text_align':'right','decimal_places':3},
{'accessor': 'melting_touch', 'Header': 'Touch','is_total_req':False,'text_align':'right','decimal_places':0},
{'accessor': 'type', 'Header': 'Type', 'is_total_req':False,'text_align':'center'},
{'accessor': 'tested_supplier', 'Header': 'Tested Supllier', 'is_total_req':False,'text_align':'left'},

]
BANK_STATMENT_LIST = [
   # SNO_COLUMN,
    { 'Header': "Bank", 'accessor': "bank_name", 'text_align': "center",  },
    { 'Header': "Trans Name", 'accessor': "trans_name", 'text_align': "center",  },
    { 'Header': "Credit", 'accessor': "credit",'text_align': "right", 'is_total_req': True,'decimal_places': 2,'is_money_format':True },
    { 'Header': "Debit", 'accessor': "debit", 'decimal_places': 2, 'text_align': "right", 'is_total_req': True,'is_money_format':True},
]

ABOVE2L_REPORT = [
    SNO_COLUMN,
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Cus Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_mobile', 'Header': 'Cus Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sales_amount', 'Header': 'Sales Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'purchase_amount', 'Header': 'Purchase Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    # {'accessor': 'return_amount', 'Header': 'Return Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    # {'accessor': 'total_discount_amount', 'Header': 'Discount Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'net_amount', 'Header': 'Net Amount','text_align':'right','is_total_req':True,"decimal_places":2,"is_money_format":True},
    {'accessor': 'received_amount', 'Header': 'Received Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'due_amount', 'Header': 'Due Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
]

EMP_INCENTIVE_REPORT = [
    {'accessor': 'invoice_no', 'Header': 'Inv No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'emp_name', 'Header': 'Employee Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Bill Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'branch_name', 'Header': 'Branch', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'incentive_type', 'Header': 'Incentive Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'calculation_method', 'Header': 'Calculation Method', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'employee_role', 'Header': 'Employee Role', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'incentive_amount', 'Header': 'Incentive Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'less_wt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'other_metal_wt', 'Header': 'Other Metal', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'mc_value', 'Header': 'Mc', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right','is_money_format':True},
    {'accessor': 'wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'wastage_weight', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate', 'text_align': 'left','is_money_format':True},
    {'accessor': 'taxable_amount', 'Header': 'Taxable', 'text_align': 'left'},
    {'accessor': 'item_cost', 'Header': 'TOTAL AMT', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]

SUPPLIER_BALANCE_REPORT = [
    SNO_COLUMN,
    { 'Header': "Supplier", 'accessor': "supplier_name", 'text_align': "center","hasLink": True  },
    {'accessor': 'short_code','Header': 'Code', 'text_align': 'left'},
    {'accessor': 'mobile_no','Header': 'Mobile No', 'text_align': 'left'},
    {'accessor': 'metal_name','Header': 'Metal', 'text_align': 'left'},
    { 'Header': "Amount Balance", 'accessor': "supplier_balance_amount",'text_align': "right", 'is_total_req': True,'is_total_money_format':True},
    { 'Header': "Weight Balance", 'accessor': "supplier_balance_weight",  'text_align': "right", 'is_total_req': True,'total_decimal_places':3},
]

SALES_WEIGHT_RANGE_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'weight_range_name', 'Header': 'Weight Range', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lesswt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'wastage_wt', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'taxable', 'Header': 'Taxable', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tax', 'Header': 'Tax', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tot_amount', 'Header': 'Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]
SALES_SIZE_REPORT = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'weight_range_name', 'Header': 'Weight Range', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'size_name', 'Header': 'Size', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lesswt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'stone_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'wastage_wt', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'taxable', 'Header': 'Taxable', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tax', 'Header': 'Tax', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True},
    {'accessor': 'tot_amount', 'Header': 'Amount', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]
PAYMNET_DEVICE_COLUMN_LIST =[ 
                SNO_COLUMN,
                {'accessor': 'date', 'Header': 'Date', 'is_total_req':False,'text_align':'left'},
                {'accessor': 'device_name', 'Header': 'Device Name', 'is_total_req':False,'text_align':'left'},
                {'accessor': 'ref_no', 'Header': 'Bill No', 'is_total_req':False,'text_align':'left'},
                {'accessor': 'type', 'Header': 'Type', 'is_total_req':False,'text_align':'left'},
                {'accessor': 'payment_ref_number', 'Header': 'Ref No', 'is_total_req':False,'text_align':'left'},
                {'accessor': 'payment_mode', 'Header': 'Mode Name', 'is_total_req':False,'text_align':'left'},
                {'accessor': 'payment_amount', 'Header': 'Payment Amount', 'is_total_req':True, 'decimal_places':2,'text_align':'right','is_money_format':True},
                ]



STOCK_ANALYSIS_REPORT = [
    SNO_COLUMN,
    {'accessor': 'tag_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag Code', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'sub_design_name', 'Header': 'S.Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'tag_pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_dia_wt', 'Header': 'Dia', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_stn_wt', 'Header': 'Stn', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_wastage_percentage', 'Header': 'V.A(%)','decimal_places': 2, 'text_align': 'right'},
    {'accessor': 'tag_wastage_wt', 'Header': 'V.A(WT)', 'is_total_req': True, 'decimal_places': 3, 'text_align': 'right'},
    {'accessor': 'tag_sell_rate', 'Header': 'Sell Rate', 'is_total_req': True, 'decimal_places': 2, 'text_align': 'right','is_money_format':True}
]

TAG_DETAILS_REPORT_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'center'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_stn_wt', 'Header': 'Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_dia_wt', 'Header': 'Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
]


SUPPLIER_CATALOG_REPORT_COLUMNS = [
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'supplier_name', 'Header': 'Supplier', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_mc', 'Header': 'MC', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2},
    {'accessor': 'total_va', 'Header': 'VA', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2},
    {'accessor': 'total_flat_mc', 'Header': 'Flat MC', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2},
    {'accessor': 'total_touch', 'Header': 'Touch', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2},
]



SUMMARY_SALES_REPORT_COLUMNS = [
    {'accessor': 'invoice_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'metal_name', 'Header': 'Metal', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'starting_invoice_no', 'Header': 'Starting No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'ending_invoice_no', 'Header': 'Ending No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pcs', 'Header': 'Pieces', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gross Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'taxable_amount', 'Header': 'Taxable Amt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'cgst_cost', 'Header': 'CGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'sgst_cost', 'Header': 'SGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'item_cost', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'avg_rate_per_gram', 'Header': 'Avg Rate', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
]


SUMMARY_PURCHASE_ENTRY_REPORT_COLUMNS = [
    {'accessor': 'group_name', 'Header': 'Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'invoice_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'metal_name', 'Header': 'Metal', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'starting_invoice_no', 'Header': 'Starting No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'ending_invoice_no', 'Header': 'Ending No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pcs', 'Header': 'Pieces', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Gross Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'pure_wt', 'Header': 'Pure Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'taxable_amount', 'Header': 'Taxable Amt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'cgst_cost', 'Header': 'CGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'sgst_cost', 'Header': 'SGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'igst_cost', 'Header': 'IGST', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'tds_amount', 'Header': 'TDS', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'item_cost', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'avg_rate_per_gram', 'Header': 'Avg Rate', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
]

STOCK_INWARD_REPORT_COLUMNS = [
    {'accessor': 'lot_code', 'Header': 'Lot No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_type', 'Header': 'Lot Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_tag_pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'total_tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_stn_wt', 'Header': 'Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'total_tag_dia_wt', 'Header': 'Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
]

STOCK_INWARD_PRODUCT_REPORT_COLUMNS = [
    {'accessor': 'cat_name', 'Header': 'Category Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_tag_pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'total_tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_stn_wt', 'Header': 'Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'total_tag_dia_wt', 'Header': 'Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
]


STOCK_INWARD_PRODUCT_SIZE_REPORT_COLUMNS = [
    {'accessor': 'cat_name', 'Header': 'Category Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'size_name', 'Header': 'Size', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_tag_pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'total_tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_stn_wt', 'Header': 'Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'total_tag_dia_wt', 'Header': 'Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
]


STOCK_INWARD_PRODUCT_WEIGHT_RANGE_REPORT_COLUMNS = [
    {'accessor': 'cat_name', 'Header': 'Category Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'weight_range_name', 'Header': 'Weight Range', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_tag_pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'total_tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_stn_wt', 'Header': 'Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'total_tag_dia_wt', 'Header': 'Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
]

COUNTER_STOCK_INWARD_REPORT_COLUMNS = [
    # {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'section_name', 'Header': 'Section', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_tag_pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'total_tag_gwt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_nwt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_lwt', 'Header': 'Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_tag_stn_wt', 'Header': 'Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'total_tag_dia_wt', 'Header': 'Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
]
TAG_INWARD_LIST = [
    {'accessor': 'tag_code', 'Header': 'Tag Code','text_align':'center','width':'14%'},
    {'accessor': 'lot_code', 'Header': 'Lot Code','text_align':'center','width':'14%'},
    {'accessor': 'date', 'Header': 'Date','text_align':'center','width':'10%'}, 
    {'accessor': 'cat_name', 'Header': 'Category','text_align':'center','width':'11%'}, 
    {'accessor': 'product_name', 'Header': 'Product','text_align':'center','width':'11%'}, 
    {'accessor': 'design_name', 'Header': 'Design','text_align':'center','width':'11%'}, 
    #{'accessor': 'sub_design_name', 'Header': 'S.Design','text_align':'center','width':'11%'}, 
    {'accessor': 'tag_pcs', 'Header': 'Pcs','text_align':'right','is_total_req':True,"decimal_places":0},
    {'accessor': 'tag_gwt', 'Header': 'GWT','text_align':'right','is_total_req':True,"decimal_places":3},
    {'accessor': 'tag_nwt', 'Header': 'NWT','text_align':'right','is_total_req':True,"decimal_places":3},
    {'accessor': 'tag_lwt', 'Header': 'LWT','text_align':'right','is_total_req':True,"decimal_places":3},
    {'accessor': 'tag_stn_wt', 'Header': 'Stn WT','text_align':'right','is_total_req':True,"decimal_places":3},
    {'accessor': 'tag_dia_wt', 'Header': 'Dia WT','text_align':'right','is_total_req':True,"decimal_places":3},
    ]

LOT_INWARD_PRODUCT_REPORT_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_no__lot_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'id_product__product_name', 'Header': 'Product Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_no__lot_code', 'Header': 'Lot No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_pcs', 'Header': 'Lot Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'lot_gwt', 'Header': 'Lot Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lot_nwt', 'Header': 'Lot Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lot_lwt', 'Header': 'Lot Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lot_stn_wt', 'Header': 'Lot Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'lot_dia_wt', 'Header': 'Lot Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'tag_pcs', 'Header': 'Tag Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'tag_gwt', 'Header': 'Tag Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_nwt', 'Header': 'Tag Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_lwt', 'Header': 'Tag Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_stn_wt', 'Header': 'Tag Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'tag_dia_wt', 'Header': 'Tag Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'balance_pcs', 'Header': 'Blc.Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'balance_gwt', 'Header': 'Blc.Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_nwt', 'Header': 'Blc.Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_lwt', 'Header': 'Blc.Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_stn_wt', 'Header': 'Blc.Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'balance_dia_wt', 'Header': 'Blc.Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
]

LOT_INWARD_REPORT_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_no__lot_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_no__lot_code', 'Header': 'Lot No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_pcs', 'Header': 'Lot Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'lot_gwt', 'Header': 'Lot Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lot_nwt', 'Header': 'Lot Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lot_lwt', 'Header': 'Lot Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'lot_stn_wt', 'Header': 'Lot Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'lot_dia_wt', 'Header': 'Lot Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'tag_pcs', 'Header': 'Tag Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'tag_gwt', 'Header': 'Tag Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_nwt', 'Header': 'Tag Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_lwt', 'Header': 'Tag Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'tag_stn_wt', 'Header': 'Tag Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'tag_dia_wt', 'Header': 'Tag Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'balance_pcs', 'Header': 'Blc.Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'balance_gwt', 'Header': 'Blc.Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_nwt', 'Header': 'Blc.Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_lwt', 'Header': 'Blc.Lwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_stn_wt', 'Header': 'Blc.Stn WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'balance_dia_wt', 'Header': 'Blc.Dia WT', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3,"showCol":False},
    {'accessor': 'is_active', 'Header': 'Status'},
]

LOT_BALANCE_REPORT_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lot_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'lotno', 'Header': 'Lot No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Lot Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Lot Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_pcs', 'Header': 'Blc Pcs','is_total_req': True,  "text_align":'right'},
    {'accessor': 'balance_gwt', 'Header':'Blc Gwt','is_total_req' :True,'text_align':'right','decimal_places' :3},
    {'accessor': 'is_active', 'Header': 'Status'},
    ACTION_COLUMN
]


LOT_BALANCE_REPORT_SUMMARY_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'design_name', 'Header': 'Design', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'pieces', 'Header': 'Lot Pcs', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'gross_wt', 'Header': 'Lot Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'balance_pcs', 'Header': 'Blc Pcs','is_total_req': True,  "text_align":'right'},
    {'accessor': 'balance_gwt', 'Header':'Blc Gwt','is_total_req' :True,'text_align':'right','decimal_places' :3},
    {'accessor': 'is_active', 'Header': 'Status'},
    ACTION_COLUMN
]


DIGIGOLD_REPORT_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'name', 'Header': 'Name', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'mobile', 'Header': 'Mobile', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'account_no', 'Header': 'Acc No', 'is_total_req': False, 'hasLink':True},
    {'accessor': 'joined_on', 'Header': 'Joined On', 'is_total_req': False, },
    {'accessor': 'maturity_date', 'Header': 'Maturity On', 'is_total_req': False, },
    {'accessor': 'curr_period_and_interest', 'Header': 'Period & Interest', 'is_total_req': False,},
    {'accessor': 'paid_amnt', 'Header': 'Paid Amount', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'rate', 'Header': 'Rate', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'weight', 'Header': 'Weight', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'bonus_weight', 'Header': 'Bonus Weight', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_weight', 'Header': 'Total Weight', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    
]

ACCOUNT_DIGIGOLD_REPORT_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False,},
    # {'accessor': 'date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'customer_name', 'Header': 'Name', 'is_total_req': False, },
    {'accessor': 'mobile', 'Header': 'Mobile', 'is_total_req': False, },
    {'accessor': 'acc_name', 'Header': 'Acc Name', 'is_total_req': False, },
    {'accessor': 'account_no', 'Header': 'Acc No', 'is_total_req': False, 'hasLink':True},
    {'accessor': 'joined_on', 'Header': 'Joined On', 'is_total_req': False, },
    {'accessor': 'maturity_date', 'Header': 'Maturity On', 'is_total_req': False, },
    {'accessor': 'paid_amnt', 'Header': 'Paid Amount', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    # {'accessor': 'rate', 'Header': 'Rate', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'weight', 'Header': 'Weight', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'bonus_weight', 'Header': 'Bonus Weight', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_weight', 'Header': 'Total Weight', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'status', 'Header': 'Account Status', 'is_total_req': False, },
    
]

APPROVAL_PENDING_REPORT_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False,},
    {'accessor': 'trans_date', 'Header': 'Date', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'trans_code', 'Header': 'Trans Code', 'is_total_req': False, 'text_align': 'left' },
    {'accessor': 'issue_to', 'Header': 'Issue To', 'is_total_req': False,  'text_align': 'left'},
    {'accessor': 'issue_to_name', 'Header': 'Name', 'is_total_req': False,  'text_align': 'left'},
    {'accessor': 'tag_code', 'Header': 'Tag No', 'is_total_req': False,  'text_align': 'left'},
    {'accessor': 'product_name', 'Header': 'Product', 'is_total_req': False, 'text_align': 'left' },
    {'accessor': 'pcs', 'Header': 'Pcs', 'is_total_req': True, 'text_align': 'right','decimal_places': 0},
    {'accessor': 'gross_wt', 'Header': 'Gwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'net_wt', 'Header': 'Nwt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},    
    # {'accessor': 'created_by', 'Header': 'Created Emp', 'is_total_req': False, 'text_align': 'left'},    
    # {'accessor': 'approved_emp', 'Header': 'Approved Emp', 'is_total_req': False, 'text_align': 'left'},    
    {'accessor': 'no_of_days', 'Header': 'On Hold', 'is_total_req': False, 'text_align': 'left'},    
]

LIABLITY_SUPPLIER_PAYMENT_REPORT_COLUMNS = [
    {'accessor': 'sno', 'Header': 'S.No', 'is_total_req': False,},
    {'accessor': 'supplier__supplier_name', 'Header': 'Supplier', 'is_total_req': False, 'text_align': 'left' },
    {'accessor': 'total_amount', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2, 'is_money_format':True},  
    {'accessor': 'total_paid_amount', 'Header': 'Paid Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2, 'is_money_format':True},  
    {'accessor': 'total_balance', 'Header': 'Bal. Amount', 'is_total_req': True, 'text_align': 'right','decimal_places': 2, 'is_money_format':True},  
]


PURCHASE_SUMMARY_REPORT_COLUMNS = [
    {'accessor': 'type', 'Header': 'Type', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'metal_name', 'Header': 'Metal', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'weight', 'Header': 'Gross Wt', 'is_total_req': True, 'text_align': 'right' , 'decimal_places': 3},
    {'accessor': 'net_weight', 'Header': 'Net Wt', 'is_total_req': True, 'text_align': 'right' , 'decimal_places': 3},
    {'accessor': 'amount', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right' , 'decimal_places': 2}
]

AVAILABLE_CUSTOMER_SALES_LOG_REPORT_LIST_AREA = [
    {'accessor': 'area_name', 'Header': 'Area', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_pieces', 'Header': 'Pieces', 'is_total_req': True, 'text_align': 'right' , 'decimal_places': 0},
    {'accessor': 'total_gwt', 'Header': 'GWt', 'is_total_req': True, 'text_align': 'right' , 'decimal_places': 3},
    {'accessor': 'total_nwt', 'Header': 'Net Wt', 'is_total_req': True, 'text_align': 'right' , 'decimal_places': 2},
    {'accessor': 'item_cost', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right' , 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'cus_cnt', 'Header': 'Customer', 'is_total_req': True, 'text_align': 'right' },
    {'accessor': 'average_order_value', 'Header': 'Average Order Value', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'top_selling_product', 'Header': 'Top Selling Product', 'is_total_req': False, 'text_align': 'right' },
]

AVAILABLE_CUSTOMER_SALES_LOG_REPORT_LIST_REGION = [
    {'accessor': 'region_name', 'Header': 'Region', 'is_total_req': False, 'text_align': 'left'},
    {'accessor': 'total_pieces', 'Header': 'Pieces', 'is_total_req': True, 'text_align': 'right','decimal_places': 0},
    {'accessor': 'total_gwt', 'Header': 'GWt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 3},
    {'accessor': 'total_nwt', 'Header': 'Net Wt', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2},
    {'accessor': 'item_cost', 'Header': 'Amount', 'is_total_req': True, 'text_align': 'right', 'decimal_places': 2,'is_money_format':True},
    {'accessor': 'cus_cnt', 'Header': 'Customer', 'is_total_req': True, 'text_align': 'right'},
    {'accessor': 'average_order_value', 'Header': 'Average Order Value', 'is_total_req': True, 'text_align': 'right','decimal_places': 2,'is_money_format':True},
    {'accessor': 'top_selling_product', 'Header': 'Top selling product', 'text_align': 'right' },
]



    

