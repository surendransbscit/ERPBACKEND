# constants.py

ACTION_LIST = {
    "is_add_req": True,
    "is_edit_req": True,
    "is_delete_req": True,
    "is_print_req": False,
    "is_cancel_req": False,
    "is_revert_req": False,
}
ACTION_COLUMN = {"accessor": "actions", "Header": "Action"}
SNO_COLUMN = {"accessor": "sno", "Header": "S.No"}

# PROFILE MASTER
PROFILE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "profile_name", "Header": "Profile Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
PROFILE_ACTION_LIST = ACTION_LIST.copy()
PROFILE_ACTION_LIST["is_edit_req"] = True

# AREA MASTER
AREA_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "area_name", "Header": "Area Name", "text_align": "left"},
    {"accessor": "postal", "Header": "Postal Name", "text_align": "left"},
    {"accessor": "taluk", "Header": "Taluk Name", "text_align": "left"},
    {"accessor": "pincode", "Header": "Pin Code", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
AREA_ACTION_LIST = ACTION_LIST

# Bank MASTER
BANK_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "bank_name", "Header": "Bank Name", "text_align": "left"},
    {"accessor": "acc_name", "Header": "Acc Name", "text_align": "left"},
    {"accessor": "acc_number", "Header": "Acc Num", "text_align": "left"},
    {"accessor": "ifsc_code", "Header": "IFSC", "text_align": "left"},
    {"accessor": "upi_id", "Header": "UPI", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
BANK_ACTION_LIST = ACTION_LIST.copy()
BANK_ACTION_LIST["is_edit_req"] = True


# DEPARTMENT MASTER
DEPT_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Department Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# DEPT_ACTION_LIST = ACTION_LIST
DEPT_ACTION_LIST = ACTION_LIST.copy()
DEPT_ACTION_LIST["is_edit_req"] = True

# DESIGNATION MASTER
DESIGNATION_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Designation Name", "text_align": "left"},
    {"accessor": "department", "Header": "Department Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# DESIGNATION_ACTION_LIST = ACTION_LIST
DESIGNATION_ACTION_LIST = ACTION_LIST.copy()
DESIGNATION_ACTION_LIST["is_edit_req"] = True

# COMPANY MASTER
COMPANY_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "company_name", "Header": "Company Name", "text_align": "left"},
    {"accessor": "image", "Header": "Company Image", "text_align": "left"},
    {"accessor": "short_code", "Header": "Short Code", "text_align": "left"},
    {"accessor": "mobile", "Header": "Mobile", "text_align": "left"},
    ACTION_COLUMN,
]
COMPANY_ACTION_LIST = ACTION_LIST.copy()
COMPANY_ACTION_LIST["is_delete_req"] = False
COMPANY_ACTION_LIST["is_add_req"] = False

# UOM MASTER
UOM_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "uom_name", "Header": "Uom Name", "text_align": "left"},
    {"accessor": "uom_short_code", "Header": "Uom Short Code", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
UOM_ACTION_LIST = ACTION_LIST.copy()

# BRANCH MASTER
BRANCH_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Branch Name", "text_align": "left"},
    {"accessor": "short_name", "Header": "Short Code", "text_align": "left"},
    {"accessor": "company_name", "Header": "Company Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# BRANCH_ACTION_LIST = ACTION_LIST
BRANCH_ACTION_LIST = ACTION_LIST.copy()
BRANCH_ACTION_LIST["is_edit_req"] = True


SERVICE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Name", "text_align": "left"},
    {"accessor": "short_code", "Header": "Short Code", "text_align": "left"},
    ACTION_COLUMN,
]
# SERVICE_ACTION_LIST = ACTION_LIST
SERVICE_ACTION_LIST = ACTION_LIST.copy()
SERVICE_ACTION_LIST["is_edit_req"] = True

# FINANCIAL YEAR MASTER
FIN_YEAR_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "fin_year_name", "Header": "Name", "text_align": "left"},
    {"accessor": "fin_year_code", "Header": "Code", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    {"accessor": "fin_year_from", "Header": "From Date", "text_align": "left"},
    {"accessor": "fin_year_to", "Header": "To Date", "text_align": "left"},
    ACTION_COLUMN,
]
FIN_YEAR_ACTION_LIST = ACTION_LIST.copy()
FIN_YEAR_ACTION_LIST["is_edit_req"] = False

# FINANCIAL YEAR MASTER
SUPPLIER_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "supplier_name", "Header": "Name", "text_align": "left"},
    {"accessor": "short_code", "Header": "Code", "text_align": "left"},
    {"accessor": "image", "Header": "Image", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# SUPPLIER_ACTION_LIST = ACTION_LIST
SUPPLIER_ACTION_LIST = ACTION_LIST.copy()
SUPPLIER_ACTION_LIST["is_edit_req"] = True

# METAL RATE MASTER
METAL_RATE_COLUMN_LIST = [
    SNO_COLUMN,
    #   {'accessor': 'updatetime', 'Header': 'Date'},
    {"accessor": "datetime", "Header": "Date"},
    {"accessor": "gold_24ct", "Header": "Gold 24 kT", "text_align": "right", "is_money_format": True,},
    {"accessor": "gold_22ct", "Header": "Gold 22 kT", "text_align": "right", "is_money_format": True,},
    {"accessor": "gold_18ct", "Header": "Gold 18 kT", "text_align": "right", "is_money_format": True,},
    {"accessor": "silver_G", "Header": "Silver 1Gm", "text_align": "right", "is_money_format": True,},
    ACTION_COLUMN,
]
# METAL_RATE_ACTION_LIST = ACTION_LIST
METAL_RATE_ACTION_LIST = ACTION_LIST.copy()
METAL_RATE_ACTION_LIST["is_edit_req"] = True

# TAX MASTER
TAX_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "tax_code", "Header": "Tax Code", "text_align": "left"},
    {"accessor": "tax_name", "Header": "Tax Name", "text_align": "left"},
    {"accessor": "tax_percentage", "Header": "Tax Percentage", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# TAX_ACTION_LIST = ACTION_LIST
TAX_ACTION_LIST = ACTION_LIST.copy()
TAX_ACTION_LIST["is_edit_req"] = True

# SIZE MASTER
SIZE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Size Name", "text_align": "left"},
    {"accessor": "product_name", "Header": "Product Name", "text_align": "left"},
    {"accessor": "value", "Header": "Value", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# SIZE_ACTION_LIST = ACTION_LIST
SIZE_ACTION_LIST = ACTION_LIST.copy()
SIZE_ACTION_LIST["is_edit_req"] = True

# BANNER
BANNER_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "banner_name", "Header": "Banner Name", "text_align": "left"},
    {"accessor": "image", "Header": "Banner Image", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
BANNER_ACTION_LIST = ACTION_LIST.copy()
BANNER_ACTION_LIST["is_edit_req"] = True

# ATTRIBUTE MASTER
ATTRIBUTE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "attribute_name", "Header": "Attribute Name", "text_align": "left"},
    {"accessor": "value", "Header": "Value", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# ATTRIBUTE_ACTION_LIST = ACTION_LIST
ATTRIBUTE_ACTION_LIST = ACTION_LIST.copy()
ATTRIBUTE_ACTION_LIST["is_edit_req"] = True

# OTHER CHARGES
OTHER_CHARGES_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Charges Name"},
    {"accessor": "amount", "Header": "Amount"},
    {"accessor": "is_active", "Header": "Status"},
    ACTION_COLUMN,
]
# OTHER_CHARGES_ACTION_LIST = ACTION_LIST
OTHER_CHARGES_ACTION_LIST = ACTION_LIST.copy()
OTHER_CHARGES_ACTION_LIST["is_edit_req"] = True

# PAY DEVICE
PAY_DEVICE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "device_name", "Header": "Device Name", "text_align": "left"},
    {"accessor": "device_type", "Header": "Type", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# PAY_DEVICE_ACTION_LIST = ACTION_LIST
PAY_DEVICE_ACTION_LIST = ACTION_LIST.copy()
PAY_DEVICE_ACTION_LIST["is_edit_req"] = True

# STOCK ISSUE TYPE
STOCK_ISSUE_TYPE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Stock Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# STOCK_ISSUE_TYPE_ACTION_LIST = ACTION_LIST
STOCK_ISSUE_TYPE_ACTION_LIST = ACTION_LIST.copy()
STOCK_ISSUE_TYPE_ACTION_LIST["is_edit_req"] = True

# WEIGHT RANGE
WEIGHT_RANGE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "product_name", "Header": "Product", "text_align": "left"},
    ACTION_COLUMN,
]
# WEIGHT_RANGE_ACTION_LIST = ACTION_LIST
WEIGHT_RANGE_ACTION_LIST = ACTION_LIST.copy()
WEIGHT_RANGE_ACTION_LIST["is_edit_req"] = True


# FLOOR
FLOOR_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "branch", "Header": "Branch", "text_align": "left"},
    {"accessor": "floor_name", "Header": "Floor Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# FLOOR_ACTION_LIST = ACTION_LIST
FLOOR_ACTION_LIST = ACTION_LIST.copy()
FLOOR_ACTION_LIST["is_edit_req"] = True

# COUNTER
COUNTER_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "floor", "Header": "Floor Name", "text_align": "left"},
    {"accessor": "counter_name", "Header": "Counter Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# COUNTER_ACTION_LIST = ACTION_LIST
COUNTER_ACTION_LIST = ACTION_LIST.copy()
COUNTER_ACTION_LIST["is_edit_req"] = True


# REGISTERED_DEVICES
REGISTERED_DEVICES_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "counter", "Header": "Counter Name", "text_align": "left"},
    {"accessor": "name", "Header": "Registered Name", "text_align": "left"},
    {"accessor": "ref_no", "Header": "Ref No", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# REGISTERED_DEVICES_ACTION_LIST = ACTION_LIST
REGISTERED_DEVICES_ACTION_LIST = ACTION_LIST.copy()
REGISTERED_DEVICES_ACTION_LIST["is_edit_req"] = True


# PROFESSION
PROFESSION_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "profession_name", "Header": "Profession Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# PROFESSION_ACTION_LIST = ACTION_LIST
PROFESSION_ACTION_LIST = ACTION_LIST.copy()
PROFESSION_ACTION_LIST["is_edit_req"] = True


# CONTAINER
CONTAINER_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "branch", "Header": "Branch", "text_align": "left"},
    {"accessor": "container_name", "Header": "Container Name", "text_align": "left"},
    {"accessor": "sku_id", "Header": "SKU ID", "text_align": "left"},
    {"accessor": "weight", "Header": "Weight", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# CONTAINER_ACTION_LIST = ACTION_LIST
CONTAINER_ACTION_LIST = ACTION_LIST.copy()
CONTAINER_ACTION_LIST["is_edit_req"] = True

# OLDMETALITEM
OLD_METAL_ITEM_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Old Metal Name", "text_align": "left"},
    {"accessor": "metal", "Header": "Metal Name", "text_align": "left"},
    {"accessor": "code", "Header": "Code", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# OLD_METAL_ITEM_ACTION_LIST = ACTION_LIST
OLD_METAL_ITEM_ACTION_LIST = ACTION_LIST.copy()
OLD_METAL_ITEM_ACTION_LIST["is_edit_req"] = True


# OTHER WEIGHT

OTHER_WEIGHT_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Other Weight Name", "text_align": "left"},
    {"accessor": "weight", "Header": "Weight", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# OTHER_WEIGHT_ACTION_LIST = ACTION_LIST
OTHER_WEIGHT_ACTION_LIST = ACTION_LIST.copy()
OTHER_WEIGHT_ACTION_LIST["is_edit_req"] = True


# CASH OPENING BALANCE
CASH_OPENING_BALANCE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "branch", "Header": "Branch", "text_align": "left"},
    {"accessor": "amount", "Header": "Amount", "text_align": "left"},
    ACTION_COLUMN,
]
# CASH_OPENING_BALANCE_ACTION_LIST = ACTION_LIST
CASH_OPENING_BALANCE_ACTION_LIST = ACTION_LIST.copy()
CASH_OPENING_BALANCE_ACTION_LIST["is_edit_req"] = True


# ACCOUNT HEAD
ACCOUNT_HEAD_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Name", "text_align": "left"},
    {"accessor": "type", "Header": "Type", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# ACCOUNT_HEAD_ACTION_LIST = ACTION_LIST
ACCOUNT_HEAD_ACTION_LIST = ACTION_LIST.copy()
ACCOUNT_HEAD_ACTION_LIST["is_edit_req"] = True


# CUSTOMER PROOF
CUSTOMER_PROOF_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "customer", "Header": "Customer", "text_align": "left"},
    {"accessor": "aadhar_number", "Header": "Aadhar Number", "text_align": "left"},
    ACTION_COLUMN,
]
# CUSTOMER_PROOF_ACTION_LIST = ACTION_LIST
CUSTOMER_PROOF_ACTION_LIST = ACTION_LIST.copy()
CUSTOMER_PROOF_ACTION_LIST["is_edit_req"] = True

# RELATION TYPE
RELATION_TYPE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# RELATION_TYPE_ACTION_LIST = ACTION_LIST
RELATION_TYPE_ACTION_LIST = ACTION_LIST.copy()
RELATION_TYPE_ACTION_LIST["is_edit_req"] = True


# COUNTRY
COUNTRY_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Country Name", "text_align": "left"},
    {"accessor": "currency_name", "Header": "Currency Name", "text_align": "left"},
    ACTION_COLUMN,
]
# COUNTRY_ACTION_LIST = ACTION_LIST
COUNTRY_ACTION_LIST = ACTION_LIST.copy()
COUNTRY_ACTION_LIST["is_edit_req"] = True


# STATE
STATE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "country", "Header": "Country Name", "text_align": "left"},
    {"accessor": "name", "Header": "State Name", "text_align": "left"},
    ACTION_COLUMN,
]
# STATE_ACTION_LIST = ACTION_LIST
STATE_ACTION_LIST = ACTION_LIST.copy()
STATE_ACTION_LIST["is_edit_req"] = True

# CITY
CITY_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "state", "Header": "State Name", "text_align": "left"},
    {"accessor": "name", "Header": "City Name", "text_align": "left"},
    ACTION_COLUMN,
]
# CITY_ACTION_LIST = ACTION_LIST
CITY_ACTION_LIST = ACTION_LIST.copy()
CITY_ACTION_LIST["is_edit_req"] = True

BANK_DEPOSIT_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "entry_date", "Header": "Date", "text_align": "left"},
    {"accessor": "branch_name", "Header": "Branch Name", "text_align": "left"},
    {"accessor": "bank_name", "Header": "Bank Name", "text_align": "left"},
    {"accessor": "acc_number", "Header": "Acc Num", "text_align": "left"},
    {"accessor": "amount", "Header": "Deposit Amount", "text_align": "left"},
    ACTION_COLUMN,
]
BANK_DEPOSIT_ACTION_LIST = ACTION_LIST.copy()
BANK_DEPOSIT_ACTION_LIST["is_edit_req"] = True

DEPOSIT_MASTER_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "scheme", "Header": "Scheme Name", "text_align": "left"},
    {"accessor": "code", "Header": "Code", "text_align": "left"},
    {"accessor": "type", "Header": "Type", "text_align": "left"},
    {"accessor": "payable_type", "Header": "Payable Type", "text_align": "left"},
    {"accessor": "interest", "Header": "Interest", "text_align": "left"},
    {"accessor": "interest_percentage", "Header": "Percent", "text_align": "left"},
    {"accessor": "interest_type", "Header": "Interest Type", "text_align": "left"},
    ACTION_COLUMN,
]
# DEPOSIT_MASTER_ACTION_LIST =ACTION_LIST
DEPOSIT_MASTER_ACTION_LIST = ACTION_LIST.copy()
DEPOSIT_MASTER_ACTION_LIST["is_edit_req"] = True

CUSTOMER_DEPOSIT_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "cus_name", "Header": "Customer", "text_align": "left"},
    {"accessor": "cus_mobile", "Header": "Mobile", "text_align": "left"},
    {"accessor": "deposit_code", "Header": "Code", "text_align": "left"},
    {"accessor": "ref_no", "Header": "Ref No", "text_align": "left"},
    {"accessor": "branch_name", "Header": "Branch", "text_align": "left"},
    {"accessor": "start_date", "Header": "Start Date", "text_align": "left"},
    {"accessor": "closing_date", "Header": "Closing Date", "text_align": "left"},
    {
        "accessor": "deposit_amount",
        "Header": "Amount",
        "text_align": "right",
        "is_total_req": True,
        "decimal_places": 2,
        "is_money_format": True,
    },
    {
        "accessor": "deposit_weight",
        "Header": "Weight",
        "text_align": "right",
        "is_total_req": True,
        "decimal_places": 3,
        "is_money_format": True,
    },
    ACTION_COLUMN,
]
CUSTOMER_DEPOSIT_ACTION_LIST = ACTION_LIST.copy()
CUSTOMER_DEPOSIT_ACTION_LIST["is_edit_req"] = False

INCENTIVE_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "start_date", "Header": "Start Date", "text_align": "left"},
    {"accessor": "end_date", "Header": "End Date", "text_align": "left"},
    {"accessor": "branch_name", "Header": "Branch Name", "text_align": "left"},
    {"accessor": "section_name", "Header": "Section", "text_align": "left"},
    {"accessor": "pcs_target_value","Header": "Pcs Target Value","text_align": "left",},
    {"accessor": "amt_target_value","Header": "Amount Target Value","text_align": "left",},
    {"accessor": "wt_target_value","Header": "Weight Target Value","text_align": "left",},
    ACTION_COLUMN,
]
INCENTIVE_ACTION_LIST = ACTION_LIST.copy()
INCENTIVE_ACTION_LIST["is_edit_req"] = True

# religion
RELIGION_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "name", "Header": "Religion Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
# RELIGION_ACTION_LIST = ACTION_LIST
RELIGION_ACTION_LIST = ACTION_LIST.copy()
RELIGION_ACTION_LIST["is_edit_req"] = True


DAILY_STATUS_MASTER_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "type_name", "Header": "Type",},
    {"accessor": "is_active", "Header": "Status",},
    # ACTION_COLUMN,
]
# RELIGION_ACTION_LIST = ACTION_LIST
DAILY_STATUS_MASTER_ACTION_LIST = ACTION_LIST.copy()
DAILY_STATUS_MASTER_ACTION_LIST["is_edit_req"] = False


# REGION
REGION_COLUMN_LIST = [
    SNO_COLUMN,
    {"accessor": "region_name", "Header": "Region Name", "text_align": "left"},
    {"accessor": "is_active", "Header": "Status", "text_align": "left"},
    ACTION_COLUMN,
]
REGION_ACTION_LIST = ACTION_LIST.copy()
REGION_ACTION_LIST["is_edit_req"] = True