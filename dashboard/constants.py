ACTIVE_CHITS_COLUMN_LIST = [
    {'accessor': 'scheme_account', 'Header': 'Account Name'},
    {'accessor': 'customer_name', 'Header': 'Customer'},
    {'accessor': 'scheme_name', 'Header': 'Scheme Name'},
    {'accessor': 'amount', 'Header': 'Amount', 'isTotalReq': True,
        'decimal_places': 2, 'textAlign': 'right', 'isCurrency': True},
    {'accessor': 'weight', 'Header': 'Weight', 'isTotalReq': True,
        'decimal_places': 3, 'textAlign': 'right', },
    {'accessor': 'bonus', 'Header': 'Bonus', 'isTotalReq': True,
        'decimal_places': 2, 'textAlign': 'right', 'isCurrency': True},
]

MATURED_AND_UNCLAIMED_CHITS_COLUMN_LIST = [
    {'accessor': 'scheme_account', 'Header': 'Account Name'},
    {'accessor': 'customer_name', 'Header': 'Customer'},
    {'accessor': 'scheme_name', 'Header': 'Scheme Name'},
    {'accessor': 'amount', 'Header': 'Amount', 'isTotalReq': True,
        'decimal_places': 2, 'textAlign': 'right', 'isCurrency': True},
    {'accessor': 'weight', 'Header': 'Weight', 'isTotalReq': True,
        'decimal_places': 3, 'textAlign': 'right', },
    {'accessor': 'bonus', 'Header': 'Bonus', 'isTotalReq': True,
        'decimal_places': 2, 'textAlign': 'right', 'isCurrency': True},
]

PAYMENT_SUMMARY_COLUMN_LIST = [
    {'accessor': 'scheme_name', 'Header': 'Scheme Name'},
    {'accessor': 'amount', 'Header': 'Amount', 'isTotalReq': True,
        'decimal_places': 2, 'textAlign': 'right', 'isCurrency': True},
    {'accessor': 'rate', 'Header': 'Rate', 'isTotalReq': True,
        'decimal_places': 3, 'textAlign': 'right', },
    {'accessor': 'coverup', 'Header': 'Coverup', 'isTotalReq': True,
        'decimal_places': 1, 'textAlign': 'right', },
]
