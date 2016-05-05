{
    'name' : 'Saicoms Customer Service Addons',
    'version' : '1.1',
    'author' : 'Sơn Phạm',
    'category' : 'Saicoms',
    'description' : """
    Saicoms Customer Service Customization for Saicoms
    """,
    'website': 'http://saicoms.vn',
    'images' : [''],
    'depends' : ['sale','project','point_of_sale'],
    'data': [
        'security/group.xml',
        'product_view.xml',
        'product_remark_view.xml',
        'sale_order_view.xml',
        'sale_order_event_view.xml',
        'sale_order_event_ir_cron.xml',
        'menu.xml',
        'project_view.xml',
        'partner_view.xml',
        'security/ir.model.access.csv',
        'account_security.xml',
        'customer_type_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
# -*- coding: utf-8 -*-

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
