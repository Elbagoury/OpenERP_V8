# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2013 Elico Corp. All Rights Reserved.
#    Author: Yannick Gouin <yannick.gouin@elico-corp.com>
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
    'name': 'Shonan Customize',
    'version': '1.0',
    'category': 'Sales Management',
    'description': """
    """,
    'author': 'Ho Di',
    'depends': ['hr', 'stock', 'account_accountant', 'scrollable_tree_view', 'web_digital_sign', 'sale','report_aeroo'],
    'init_xml': [],
    'update_xml': [
        "report/report_view.xml",
        "sale_view.xml",
        "report_view.xml"
    ],
    'demo_xml': [],
    'installable': True,
    'application': True,
    'active': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
