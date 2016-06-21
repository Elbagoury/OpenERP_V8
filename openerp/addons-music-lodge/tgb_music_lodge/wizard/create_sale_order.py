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
from openerp import netsvc,SUPERUSER_ID
from datetime import datetime
import time
import openerp.addons.decimal_precision as dp

class create_sale_order(osv.osv_memory):
    _name = 'create.sale.order'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(create_sale_order, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id',False):
            rental_id = context['active_id']
            rental = self.pool.get('sale.rental').browse(cr, uid, rental_id)
            create_so_line=[]
            for line in rental.rental_line:
                create_so_line.append((0,0,{
                    'rental_line_id': line.id,
                    'product_id': line.product_id and line.product_id.id or False,
                    'product_qty': line.product_qty,
                    'price_unit': line.price_unit,
                    'deposit': line.deposit,
                    'transport_charge': line.transport_charge,
                    'cost_price': line.product_id and line.product_id.standard_price or 0,
                    'sale_price': line.product_id and line.product_id.list_price or 0,
                }))
            res.update({'partner_id':rental.partner_id and rental.partner_id.id or fields,'create_so_line': create_so_line})
        return res
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'create_so_line': fields.one2many('create.sale.order.line', 'create_so_id','Line'),
    }
    
    def bt_create_so(self, cr, uid, ids, context=None):
        sale_obj = self.pool.get('sale.order')
        for create_so in self.browse(cr, uid, ids):
            sale_line = []
            for line in create_so.create_so_line:
                sale_line.append((0,0,{
                    'product_id': line.product_id and line.product_id.id or False,
                    'name': line.rental_line_id.name,
                    'brand': line.rental_line_id.brand,
                    'model': line.rental_line_id.model,
                    'serial_no': line.rental_line_id.serial_no,
                    'year_of_manufacture': line.rental_line_id.year_of_manufacture,
                    'color': line.rental_line_id.color,
                    'dimension': line.rental_line_id.dimension,
                    'product_uom_qty': line.product_qty,
                    'price_unit': line.price,
                    'discount': line.rental_line_id.discount,
                }))
            sale_vals = sale_obj.onchange_partner_id(cr, uid, [], create_so.partner_id.id, context)['value']
            sale_vals.update({
                'partner_id': create_so.partner_id.id,
                'order_line': sale_line,
                'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
            })
            sale_obj.create(cr, uid, sale_vals)
        return True
    
create_sale_order()

class create_sale_order_line(osv.osv_memory):
    _name = 'create.sale.order.line'
    
    _columns = {
        'create_so_id': fields.many2one('create.sale.order','Create SO', ondelete='cascade'),
        'rental_line_id': fields.many2one('sale.rental.line', 'Rental line'),
        'product_id': fields.many2one('product.product', 'Product'),
        'product_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS')),
        'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price')),
        'deposit': fields.float('Deposit', digits_compute= dp.get_precision('Product Price')),
        'transport_charge': fields.float('Transport Charge', digits_compute= dp.get_precision('Product Price')),
        'cost_price': fields.float('Cost Price', digits_compute= dp.get_precision('Product Price')),
        'sale_price': fields.float('Sale Price', digits_compute= dp.get_precision('Product Price')),
        'price': fields.float('PRICE', digits_compute= dp.get_precision('Product Price')),
    }
    
create_sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: