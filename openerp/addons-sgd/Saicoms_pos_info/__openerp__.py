# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Saicoms POS Additional Information',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Saicoms POS Additional Information ',
    'description': """

=======================

Saicoms POS Additional Information

""",
    'author': 'Son Pham',
    'depends': ['point_of_sale','Saicoms_CS','Saicoms_salon_pos'],
    'data': [
        'views/templates.xml',
        'pos_order_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb':[
        'static/src/xml/splitbill.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
