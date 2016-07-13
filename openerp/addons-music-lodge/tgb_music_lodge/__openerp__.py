# -*- coding: utf-8# -*- coding: utf-8 -*-
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
    'name': 'TGB Music Lodge',
    'version': '1.0',
    'category': 'TGB',
    'sequence': 1,
    'depends': ['sale','account','account_accountant','account_voucher','report_aeroo','web_digital_sign'],
    'data': [
        'report/rental_agreement_report_view.xml',
        'report/invoice_report_view.xml',
        'wizard/create_sale_order_view.xml',
        'product_view.xml',
        'res_partner_view.xml',
        'invoice_view.xml',
        'sale_view.xml',
        'sequence.xml',
        'schedule.xml',
        'report_view.xml',
        'menu.xml',
    ],
    'css' : [
    ],
    'qweb': [
    ],
    'js': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: -*-