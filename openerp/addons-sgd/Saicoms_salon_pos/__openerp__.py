# -*- coding: utf-8 -*-
{
    'name' : 'Saicoms POS for Salon',
    'version' : '1.1',
    'author' : 'Son Pham',
    'category' : 'Saicoms',
    'description' : """
    Saicoms POS Customized for Salon
    """,
    'website': 'http://saicoms.vn',
    'images' : ['static/src/img/company_logo.png'],
    'depends' : ['point_of_sale','Saicoms_vi_datas','Saicoms_CS'],
    'data': [
        'menu.xml',
        'security/group.xml',
        'security/ir.model.access.csv',
        'view/point_of_sale.xml',
        'partner_view.xml',
        'point_of_sale_view.xml',
        'product_view.xml',
        'view/templates.xml',
        'pos_decimal.xml',
        'pos_package_view.xml',
        'pos_package_redempton_view.xml',
        'package_booking_view.xml',
        'project_view.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
