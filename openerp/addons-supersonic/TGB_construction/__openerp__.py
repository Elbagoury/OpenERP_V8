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
                 'hr_contract',
                 'hr_timesheet_sheet',
                 'project',
                 'web_digital_sign',
                 'crm_helpdesk',
                 'crm_claim',
                 'report_aeroo',
                 ],
    "description": "TGB Construction Modules",
    "data": [
        "security/construction_security.xml",

        "menu.xml",
        'report/project_construction_report_view.xml',
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
        "make_deposit_wiz.xml",
        "data_import/contract_import.xml",
        "data_import/payroll_import.xml",
        "project_sequence.xml",
        "stock_issue_sequence.xml",
        "project_budgeting_view.xml",
        "crm_helpdesk_view.xml",
        "product_view.xml",
        "security/ir.model.access.csv",
    ],
    'qweb' : [
        "static/src/xml/test.xml",
    ],

    'installable': True,
    'auto_install': False,
}
