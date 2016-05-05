# -*- coding: utf-8 -*-

{
    "name" : "TGB Construction Project",
    "version" : "0.1",
    "author" : "Son Pham",
    "category" : "Generic Modules",
    "depends" : ['base',
                 'sale',
                 'purchase',
                 'hr_attendance',
                 'hr_timesheet_sheet',
                 'project',
                 'web_digital_sign',
                 ],
    "description": "TGB Construction Modules",
    "data": [
        "menu.xml",
        "project_order.xml",
        "project_billing.xml",
        "sale_make_invoice_advance.xml",
        "stock_issue_view.xml",
        "project_costing_view.xml",
        "project_view.xml",
        "hr_view.xml",
        "importer_view.xml",
        "project_progressive_billing.xml",
        'views/view.xml',
        "report/report_view.xml",
        "sale_deposit_view.xml",
        "make_deposit_wiz.xml"
    ],
    'qweb' : [
        "static/src/xml/test.xml",
    ],

    'installable': True,
    'auto_install': False,
}
