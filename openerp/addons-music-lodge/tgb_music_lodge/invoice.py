# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP SA (<http://openerp.com>).
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import datetime
import time
import openerp.addons.decimal_precision as dp

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    _columns = {
        'stool': fields.boolean('Stool'),
        'heater': fields.boolean('Heater'),
        'delivery': fields.boolean('Delivery'),
        'year_guarantee': fields.integer('Year Guarantee'),
        'free_tuning': fields.boolean('Free Tuning (Weekday Only)'),
        'tgb_type': fields.selection([('rental','Rental')],'TGB Type'),
        'rental_id': fields.many2one('sale.rental', 'Rental'),
        'rental_for_month': fields.char('Rental for the month', size=1024),
        'is_first': fields.boolean('Is First'),
    }
    
    _defaults = {
        'comment': 'Goods sold are not returnable & exchangeable\nDeposit is not refundable in any circumstance.',
    }
    
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
    _columns = {
        'brand': fields.char('Brand', size=1024),
        'model': fields.char('Model', size=1024),
        'serial_no': fields.char('Serial No', size=1024),
        'year_of_manufacture': fields.char('Year of Manufacture', size=1024),
        'color': fields.char('Color', size=1024),
        'dimension': fields.char('Dimension', size=1024),
    }
    
account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: