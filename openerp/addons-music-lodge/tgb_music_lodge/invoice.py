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
from openerp import api

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def _get_signature_customer(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for inv in self.browse(cr, uid, ids, context=context):
            res[inv.id] = inv.signature
        return res
    
    _columns = {
        'stool': fields.boolean('Adjst Stool'),
        'com_stool': fields.boolean('Com Stool'),
        'heater': fields.boolean('Heater'),
        'delivery': fields.boolean('Delivery'),
        'year_guarantee': fields.integer('Year Guarantee'),
        'free_tuning': fields.boolean('Free Tuning (Weekday Only)'),
        'tgb_type': fields.selection([('rental','Rental'),('piano_sale','Piano Sale')],'TGB Type'),
        'rental_id': fields.many2one('sale.rental', 'Rental'),
        'rental_for_month': fields.char('Rental for the month', size=1024),
        'is_first': fields.boolean('Is First'),
        'is_first_prepay': fields.boolean('Is First Prepay'),
        'signature': fields.binary('Customer Signature'),
        'signature_customer': fields.function(_get_signature_customer, type='binary', string='Customer Signature'),
        'company_signature': fields.binary('Company Signature'),
    }
    
    _defaults = {
        'comment': 'Goods sold are not returnable & exchangeable\nDeposit is not refundable in any circumstance.',
        'heater': True,
        'delivery': True,
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
        'discount_amount': fields.float('Discount Amt', digits_compute= dp.get_precision('Discount')),
    }
    
    from openerp import fields
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        if not self.discount and self.discount_amount:
            price = self.price_unit - self.discount_amount
            
        taxes = self.invoice_line_tax_id.compute_all(price, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = taxes['total']
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)
    price_subtotal = fields.Float(string='Amount', digits= dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_price')
    
    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):
        res = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type,partner_id, fposition_id, price_unit, currency_id,company_id)
        if product:
            product = self.env['product.product'].browse(product)
            res['value'].update({
                'model': product.model,
                'serial_no': product.serial_no,
            })
        return res
    
account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: