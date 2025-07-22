ACTION_LIST     = {"is_add_req":True,"is_edit_req":True,"is_delete_req":False,"is_print_req":False,"is_cancel_req":False,"is_total_req":True}
ACTION_COLUMN   = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN      = {'accessor': 'sno', 'Header': 'S.No'}

# SCHEME ACCOUNTER
LOT_COLUMN_LIST = [
                    {'accessor': 'lot_code', 'Header': 'Lot No'},
                    {'accessor': 'lot_date', 'Header': 'Date'},
                    {'accessor': 'id_supplier__supplier_name', 'Header': 'Supplier'},
                    {'accessor': 'id_branch__name', 'Header': 'Branch'},
                    {'accessor': 'total_pieces', 'Header': 'Pcs','text_align':'right','is_total_req':True},
                    {'accessor': 'total_gross_wt', 'Header': 'Gross Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_net_wt', 'Header': 'Net Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_stn_wt', 'Header': 'Stone Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'total_dia_wt', 'Header': 'Dia Wt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'is_active', 'Header': 'Status'},
                    ACTION_COLUMN
                    ]

TAG_COLUMN_LIST = [
                   # {'accessor': 'image', 'Header': 'Image','text_align':'center'},
                    {'accessor': 'tag_code', 'Header': 'Tag Code','text_align':'center','width':'14%'},
                    {'accessor': 'lot_code', 'Header': 'Lot Code','text_align':'center','width':'14%'},
              #      {'accessor': 'supplier_name', 'Header': 'Supplier','text_align':'center','width':'14%'},
                    {'accessor': 'branch_name', 'Header': 'Branch','text_align':'center','width':'10%'},
                    {'accessor': 'date', 'Header': 'Date','text_align':'center','width':'10%'}, 
                    {'accessor': 'product_name', 'Header': 'Product','text_align':'center','width':'11%'}, 
                    {'accessor': 'design_name', 'Header': 'Design','text_align':'center','width':'11%'}, 
                    {'accessor': 'sub_design_name', 'Header': 'S.Design','text_align':'center','width':'11%'}, 
                    {'accessor': 'tag_pcs', 'Header': 'Pcs','text_align':'right','is_total_req':True,"decimal_places":0},
                    {'accessor': 'tag_gwt', 'Header': 'GWT','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'tag_nwt', 'Header': 'NWT','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'tag_lwt', 'Header': 'LWT','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'tag_wastage_percentage', 'Header': 'VA(%)'},
                    {'accessor': 'tag_mc_value', 'Header': 'MC','text_align':'right','is_total_req':True,"decimal_places":2},
                    ]

TAG_ISSUE_COLUMN_LIST = [
                    {'accessor': 'ref_no', 'Header': 'Ref no'},
                    {'accessor': 'entry_date', 'Header': 'Date'},
                    {'accessor': 'issue_employee__firstname', 'Header': 'Issued To'},
                    {'accessor': 'id_branch__name', 'Header': 'Branch'},
                    {'accessor': 'pieces', 'Header': 'Iss.Pcs','text_align':'right','is_total_req':True},
                    {'accessor': 'gross_wt', 'Header': 'Iss.Gwt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'receipt_pieces', 'Header': 'Rcp.Pcs','text_align':'right','is_total_req':True},
                    {'accessor': 'receipt_gross_wt', 'Header': 'Rcp.Gwt','text_align':'right','is_total_req':True,"decimal_places":3},
                    {'accessor': 'status', 'Header': 'Status'},
                    ACTION_COLUMN
                    ]

NON_TAG_INWARD_COLUMN_LIST = [
                    {'accessor': 'ref_no', 'Header': 'Ref no'},
                    {'accessor': 'entry_date', 'Header': 'Date'},
                    {'accessor': 'issue_employee__firstname', 'Header': 'Issued To'},
                    {'accessor': 'id_branch__name', 'Header': 'Branch'},
                    {'accessor': 'total_pieces', 'Header': 'Iss.Pcs','text_align':'right','is_total_req':True},
                    {'accessor': 'total_gross_wt', 'Header': 'Iss.Gwt','text_align':'right','is_total_req':True,"decimal_places":3},
                    ]

MONTH_CODE  = {
  1: 'A',
  2: 'B',
  3: 'C',
  4: 'D',
  5: 'E',
  6: 'F',
  7: 'G',
  8: 'H',
  9: 'I',
 10: 'J',
 11: 'K',
 12: 'L'
}