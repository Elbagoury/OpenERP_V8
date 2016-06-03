# -*- coding: utf-8 -*-

{
    "name" : "TGB Payslip Import",
    "version" : "1.0",
    "author" : "",
    "category": 'TGB',
    'sequence': 1,
    'depends': ['hr','report_aeroo'],
    "description": """
    """,
    'data': [
        'report/letter_of_offer_report_view.xml',
        'import_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
