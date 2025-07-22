# constants.py
STONE_CHOICES = (
        ("1", "Diamond"),
        ("2", "Gem Stones"),
        ("3", "Others"),
    )
ACTION_LIST = {"is_add_req": True, "is_edit_req": True,
               "is_delete_req": True, "is_print_req": False, "is_cancel_req": False}
ACTION_COLUMN = {'accessor': 'actions', 'Header': 'Action'}
SNO_COLUMN = {'accessor': 'sno', 'Header': 'S.No'}

#METAL  MASTER
METAL_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'metal_name', 'Header': 'Metal Name','text_align':'left'}, {
    'accessor': 'metal_code', 'Header': 'Metal Code','text_align':'left'}, {'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, ACTION_COLUMN]
METAL_ACTION_LIST = ACTION_LIST.copy()

DIAMOND_RATE_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'quality_code_name', 'Header': 'Quality Code','text_align':'left'}, ACTION_COLUMN]
DIAMOND_RATE_ACTION_LIST = ACTION_LIST.copy()

#PURITY  MASTER
PURITY_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'purity', 'Header': 'Purity','text_align':'left'}, {
    'accessor': 'description', 'Header': 'Description','text_align':'left'}, {'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, ACTION_COLUMN]
PURITY_ACTION_LIST = ACTION_LIST.copy()


# STONE MASTER
STONE_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'stone_name', 'Header': 'Stone Name','text_align':'left'}, {
    'accessor': 'stone_code', 'Header': 'Stone Code','text_align':'left'}, 
    {'accessor': 'stone_type', 'Header': 'Stone Type','text_align':'left'}, 
    {'accessor': 'uom_name', 'Header': 'Stone UOM','text_align':'left'},
    {'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, ACTION_COLUMN]
STONE_ACTION_LIST = ACTION_LIST.copy()

# PROFILE MASTER
SCHEME_CLASSIFICATION_COLUMN_LIST = [SNO_COLUMN,
                                     {'accessor': 'classification_name',
                                         'Header': 'Name','text_align':'left'},
                                     {'accessor': 'is_active', 'Header': 'Status','text_align':'left'},
                                     ACTION_COLUMN]
SCHEME_CLASSIFICATION_ACTION_LIST = ACTION_LIST.copy()

COUNTER_WISE_TARGET_COLUMN_LIST = [SNO_COLUMN,
                                  {'accessor': 'from_date','Header': 'From Date','text_align':'left'},
                                  {'accessor': 'to_date','Header': 'To Date','text_align':'left'},
                                  {'accessor': 'section_name', 'Header': 'Section','text_align':'left'},
                                  {'accessor': 'branch_name','Header': 'Branch','text_align':'left'},
                                  {'accessor': 'target_pieces','Header': 'Pieces','text_align':'left'},
                                  {'accessor': 'target_weight','Header': 'Weight','text_align':'left'},
                                  ACTION_COLUMN]
COUNTER_WISE_TARGET_ACTION_LIST = ACTION_LIST.copy()
COUNTER_WISE_TARGET_ACTION_LIST['is_delete_req'] = False


#PRODUCT MASTER
PRODUCT_COLUMN_LIST = [SNO_COLUMN,{'accessor': 'product_name', 'Header': 'Product Name','text_align':'left'},
{'accessor': 'image', 'Header': 'Image','text_align':'left'},
{'accessor':'short_code','Header':'Product Code','text_align':'left'},
{'accessor': 'hsn_code', 'Header': 'HSN Code','text_align':'left'},
{'accessor': 'category', 'Header': 'Category','text_align':'left'},
{'accessor': 'tax', 'Header': 'Tax','text_align':'left'},
{'accessor': 'stock_type', 'Header': 'Stock Type','text_align':'left'},
{'accessor': 'sales_based_on', 'Header': 'Sales Based on','text_align':'left'},
{'accessor': 'mc_on', 'Header': 'Mc on','text_align':'left'},
{'accessor': 'va_on', 'Header': 'Va on','text_align':'left'},
{'accessor': 'tax_type', 'Header': 'Tax Type','text_align':'left'},
{'accessor': 'is_active', 'Header': 'Status','text_align':'left'},ACTION_COLUMN]
PRODUCT_ACTION_LIST = ACTION_LIST.copy()

# DESIGN MASTER
DESIGN_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'design_name', 'Header': 'Design Name','text_align':'left'},
                      {'accessor': 'design_code', 'Header': 'Design Code','text_align':'left'},{
    'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, ACTION_COLUMN]
DESIGN_ACTION_LIST = ACTION_LIST.copy()

# CATEGORY PURITY RATE
CATEGORY_PURITY_RATE_COLUMN_LIST = [
    SNO_COLUMN, 
    {'accessor': 'category_name', 'Header': 'Category','text_align':'left'},
    {'accessor': 'purity_name', 'Header': 'Purity','text_align':'left'},
    {'accessor': 'rate_per_gram', 'Header': 'Rate','text_align':'left'},
    {'accessor': 'created_by', 'Header': 'Created By','text_align':'left'},
    {'accessor': 'date', 'Header': 'Date','text_align':'left'},
    ACTION_COLUMN]
CATEGORY_PURITY_RATE_ACTION_LIST = ACTION_LIST.copy()
CATEGORY_PURITY_RATE_ACTION_LIST['is_delete_req'] = False
CATEGORY_PURITY_RATE_ACTION_LIST['is_edit_req'] = False

# SUB DESIGN MASTER
SUB_DESIGN_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'sub_design_name', 'Header': 'Sub Design Name','text_align':'left'}, {
    'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, ACTION_COLUMN]
SUB_DESIGN_ACTION_LIST = ACTION_LIST.copy()

# SECTION MASTER
SECTION_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'section_name', 'Header': 'Section Name','text_align':'left'}, {
    'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, ACTION_COLUMN]

SECTION_ACTION_LIST = ACTION_LIST.copy()

# CATEGORY MASTER
CATEGORY_COLUMN_LIST = [SNO_COLUMN,
                        {'accessor': 'cat_name', 'Header': 'Category Name','text_align':'left'},
                        {'accessor': 'cat_type', 'Header': 'Category Type','text_align':'left'},
                        {'accessor': 'cat_code', 'Header': 'Category Code','text_align':'left'},
                        {'accessor': 'metal_name', 'Header': 'Metal Name','text_align':'left'},
                        {'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, ACTION_COLUMN]
CATEGORY_ACTION_LIST = ACTION_LIST.copy()

#CUT MASTER
CUT_COLUMN_LIST = [SNO_COLUMN,
                   {'accessor': 'cut', 'Header': 'Cut','text_align':'left'},
                   {'accessor': 'description', 'Header': 'Description','text_align':'left'},
                   {'accessor': 'is_active', 'Header': 'Status','text_align':'left'},ACTION_COLUMN]
CUT_ACTION_LIST = ACTION_LIST.copy()

#COLOR MASTER
COLOR_COLUMN_LIST = [SNO_COLUMN,
                   {'accessor': 'color', 'Header': 'Color','text_align':'left'},
                   {'accessor': 'description', 'Header': 'Description','text_align':'left'},
                   {'accessor': 'is_active', 'Header': 'Status','text_align':'left'},ACTION_COLUMN]
COLOR_ACTION_LIST = ACTION_LIST.copy()

#SHAPE MASTER
SHAPE_COLUMN_LIST = [SNO_COLUMN,
                   {'accessor': 'shape', 'Header': 'Shape','text_align':'left'},
                   {'accessor': 'description', 'Header': 'Description','text_align':'left'},
                   {'accessor': 'is_active', 'Header': 'Status','text_align':'left'},ACTION_COLUMN]
SHAPE_ACTION_LIST = ACTION_LIST.copy()

#CLARITY MASTER
CLARITY_COLUMN_LIST = [SNO_COLUMN,
                   {'accessor': 'clarity', 'Header': 'Clarity','text_align':'left'},
                   {'accessor': 'description', 'Header': 'Description','text_align':'left'},
                   {'accessor': 'is_active', 'Header': 'Status','text_align':'left'},ACTION_COLUMN]
CLARITY_ACTION_LIST = ACTION_LIST.copy()

#QUALITYCODE MASTER
QUALITY_COLUMN_LIST = [SNO_COLUMN,
                   {'accessor': 'code', 'Header': 'Code','text_align':'left'},    
                   {'accessor': 'cutName', 'Header': 'Cut','text_align':'left'},  
                   {'accessor': 'colorName', 'Header': 'Color','text_align':'left'},
                   {'accessor': 'shapeName', 'Header': 'Shape','text_align':'left'},
                   {'accessor': 'clarityName', 'Header': 'Clarity','text_align':'left'},
                   {'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, 
                   ACTION_COLUMN]
QUALITY_ACTION_LIST = ACTION_LIST.copy()


# SUB DESIGN MASTER
REPAIR_COLUMN_LIST = [SNO_COLUMN, {'accessor': 'name', 'Header': 'Name','text_align':'left'}, {
    'accessor': 'is_active', 'Header': 'Status','text_align':'left'}, ACTION_COLUMN]
REPAIR_ACTION_LIST = ACTION_LIST.copy()