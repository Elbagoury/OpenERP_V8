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

import base64
import re
import threading
from openerp.tools.safe_eval import safe_eval as eval
from openerp import tools
import openerp.modules
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import datetime
import time
import calendar
import openerp.addons.decimal_precision as dp

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        if context is None:
            context = {}
        vals = super(stock_picking, self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context)
        sale_obj = self.pool.get('sale.order')
        sale_ids = sale_obj.search(cr, uid, [('name','=',move.picking_id.origin)])
        sgd_acc_number = False
        usd_acc_number = False
        if sale_ids:
            sale = sale_obj.browse(cr, uid, sale_ids[0])
            sgd_acc_number =  sale.sgd_acc_number
            usd_acc_number =  sale.usd_acc_number
        vals.update({
            'sgd_acc_number': sgd_acc_number,
            'usd_acc_number': usd_acc_number,  
        })
        
        return vals
    
    _columns = {
        'delivery_address_id': fields.many2one('res.partner', 'Delivery Address'),
        'picking_type': fields.related('picking_type_id', 'code', type='char', string='Picking Type'),
    }
    
stock_picking()

class stock_move(osv.osv):
    _inherit = "stock.move"
    
    _columns = {
        'part_no': fields.char('Part No', size=1024),
        'brand': fields.char('Brand', size=1024),
        'tgb_price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price')),
    }
    
    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        fp_obj = self.pool.get('account.fiscal.position')
        # Get account_id
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = move.product_id.property_account_income.id
            if not account_id:
                account_id = move.product_id.categ_id.property_account_income_categ.id
        else:
            account_id = move.product_id.property_account_expense.id
            if not account_id:
                account_id = move.product_id.categ_id.property_account_expense_categ.id
        fiscal_position = partner.property_account_position
        account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)

        # set UoS if it's a sale and the picking doesn't have one
        uos_id = move.product_uom.id
        quantity = move.product_uom_qty
        if move.product_uos:
            uos_id = move.product_uos.id
            quantity = move.product_uos_qty

        taxes_ids = self._get_taxes(cr, uid, move, context=context)

        return {
            'name': move.name,
            'account_id': account_id,
            'product_id': move.product_id.id,
            'uos_id': uos_id,
            'quantity': quantity,
            'price_unit': self._get_price_unit_invoice(cr, uid, move, inv_type),
            'invoice_line_tax_id': [(6, 0, taxes_ids)],
            'discount': 0.0,
            'account_analytic_id': False,
            'part_no': move.part_no,
            'brand': move.brand,
            'tgb_price_unit': move.tgb_price_unit,
        }
    
stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: