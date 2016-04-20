# -*- coding: utf-8 -*-

{
    "name" : "TGB Rat Trading Customization",
    "version" : "1.0",
    "author" : "Son Pham.",
    "category": 'TGB',
    'complexity': "easy",
    'depends': ['sale','account','report_aeroo'],
    "description": """
        This module provides the functionality to store digital signature image for a record.
        The example can be seen into the User's form view where we have added a test field under signature.
    """,
    'data': [
        'report/invoice_report_view.xml',
        'invoice_view.xml',
        'partner_view.xml',
        'report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
