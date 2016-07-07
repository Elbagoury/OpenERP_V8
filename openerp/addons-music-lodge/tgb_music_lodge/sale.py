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
from datetime import datetime, timedelta
import time
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta

class sale_rental(osv.osv):
    _name = "sale.rental"
    
    _columns = {
        'name': fields.char('Name', size=1024, readonly=True, states={'draft': [('readonly', False)]}),
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True, states={'draft': [('readonly', False)]}),
        'date': fields.date('Date', readonly=True, states={'draft': [('readonly', False)]}),
        'rental_line': fields.one2many('sale.rental.line', 'rental_id', 'Rental Line', readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('closed','closed')], 'Status', readonly=True),
        'rental_schedule': fields.selection([('monthly','Monthly'),('bi_monthly','Bi Monthly'),('quarterly','Quarterly'),('half_yearly','Half Yearly'),('yearly','Yearly')], 'Rental Schedule', readonly=True, states={'draft': [('readonly', False)]}),
        'next_run': fields.date('Next Run'),
        'prepay': fields.integer('Prepay'),
        'note': fields.text('Note'),
    }
    
    _defaults = {
        'state': 'draft',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'rental_schedule': 'monthly',
        'prepay': 0,
    }
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if 'name' not in vals or vals.get('name', False)=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.rental', context=context) or '/'
        return super(sale_rental, self).create(cr, uid, vals, context)
    
    def bt_confirm(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        for rental in self.browse(cr, uid, ids):
            invoice_line = []
            for line in rental.rental_line:
                invoice_line.append((0,0,{
                    'product_id': line.product_id and line.product_id.id or False,
                    'name': line.name,
                    'brand': line.brand,
                    'model': line.model,
                    'serial_no': line.serial_no,
                    'year_of_manufacture': line.year_of_manufacture,
                    'color': line.color,
                    'dimension': line.dimension,
                    'quantity': 1,
                    'price_unit': (line.deposit or 0)+(line.transport_charge or 0)*(line.product_qty or 0),
                    'discount': line.discount,
                }))
            date_invoice = rental.date
            invoice_vals = invoice_obj.onchange_partner_id(cr, uid, [], 'out_invoice', rental.partner_id.id, date_invoice)['value']
            invoice_vals.update({
                'partner_id': rental.partner_id and rental.partner_id.id or False,
                'date_invoice': date_invoice,
                'invoice_line': invoice_line,
                'type': 'out_invoice',
                'tgb_type': 'rental',
                'rental_id': rental.id,
                'is_first': True,
            })
            invoice_obj.create(cr, uid, invoice_vals, context)
            
            rental_date = datetime.strptime(rental.date,'%Y-%m-%d')
            next_run = ''
            if rental.rental_schedule=='monthly':
                month = 1
                if rental.prepay:
                    month = month*rental.prepay
                next_run = rental_date+relativedelta(months=month)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            if rental.rental_schedule=='bi_monthly':
                month = 2
                if rental.prepay:
                    month = month*rental.prepay
                next_run = rental_date+relativedelta(months=month)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            if rental.rental_schedule=='quarterly':
                month = 3
                if rental.prepay:
                    month = month*rental.prepay
                next_run = rental_date+relativedelta(months=month)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            if rental.rental_schedule=='half_yearly':
                month = 6
                if rental.prepay:
                    month = month*rental.prepay
                next_run = rental_date+relativedelta(months=month)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            if rental.rental_schedule=='yearly':
                month = 12
                if rental.prepay:
                    month = month*rental.prepay
                next_run = rental_date+relativedelta(months=month)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            
            
            if rental.prepay:
                invoice_line = []
                for line in rental.rental_line:
                    invoice_line.append((0,0,{
                        'product_id': line.product_id and line.product_id.id or False,
                        'name': line.name,
                        'brand': line.brand,
                        'model': line.model,
                        'serial_no': line.serial_no,
                        'year_of_manufacture': line.year_of_manufacture,
                        'color': line.color,
                        'dimension': line.dimension,
                        'quantity': line.product_qty,
                        'price_unit': line.price_unit*rental.prepay,
                        'discount': line.discount,
                    }))
                date_invoice = rental.date
                invoice_vals = invoice_obj.onchange_partner_id(cr, uid, [], 'out_invoice', rental.partner_id.id, date_invoice)['value']
                rental_for_month = 'Rental for the month of '+rental.date[8:10]+rental.date[5:7]+rental.date[2:4]+'-'
                if next_run:
                    next_run = datetime.strptime(next_run,'%Y-%m-%d')+timedelta(days=-1)
                    rental_for_month += next_run.strftime('%d%m%y')
                invoice_vals.update({
                    'partner_id': rental.partner_id and rental.partner_id.id or False,
                    'date_invoice': date_invoice,
                    'invoice_line': invoice_line,
                    'type': 'out_invoice',
                    'tgb_type': 'rental',
                    'rental_id': rental.id,
                    'rental_for_month': rental_for_month
                })
                invoice_obj.create(cr, uid, invoice_vals, context)
            
            
        return self.write(cr, uid, ids, {'state': 'confirmed'})
    
    def bt_close(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'closed'})
    
    def create_invoice_for_sale_rental(self, cr, uid, context=None):
        date_now = time.strftime('%Y-%m-%d')
        invoice_obj = self.pool.get('account.invoice')
        sql = '''
            select id from sale_rental where state='confirmed' and next_run is not null and next_run<='%s'
        '''%(date_now)
        cr.execute(sql)
        rental_ids = [r[0] for r in cr.fetchall()]
        for rental in self.pool.get('sale.rental').browse(cr, uid, rental_ids):
            
            pre_run = rental.next_run
            rental_date = datetime.strptime(rental.next_run,'%Y-%m-%d')
            next_run = ''
            if rental.rental_schedule=='monthly':
                next_run = rental_date+relativedelta(months=1)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            if rental.rental_schedule=='bi_monthly':
                next_run = rental_date+relativedelta(months=2)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            if rental.rental_schedule=='quarterly':
                next_run = rental_date+relativedelta(months=3)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            if rental.rental_schedule=='half_yearly':
                next_run = rental_date+relativedelta(months=6)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            if rental.rental_schedule=='yearly':
                next_run = rental_date+relativedelta(months=12)
                next_run = next_run.strftime('%Y-%m-%d')
                self.write(cr, uid, [rental.id], {'next_run': next_run})
            
            rental_for_month = 'Rental for the month of '+pre_run[8:10]+pre_run[5:7]+pre_run[2:4]+'-'
            if next_run:
                next_run = datetime.strptime(next_run,'%Y-%m-%d')+timedelta(days=-1)
                rental_for_month += next_run.strftime('%d%m%y')
            
            invoice_line = []
            for line in rental.rental_line:
                invoice_line.append((0,0,{
                    'product_id': line.product_id and line.product_id.id or False,
                    'name': line.name,
                    'brand': line.brand,
                    'model': line.model,
                    'serial_no': line.serial_no,
                    'year_of_manufacture': line.year_of_manufacture,
                    'color': line.color,
                    'dimension': line.dimension,
                    'quantity': line.product_qty,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                }))
            date_invoice = time.strftime('%Y-%m-%d')
            invoice_vals = invoice_obj.onchange_partner_id(cr, uid, [], 'out_invoice', rental.partner_id.id, date_invoice)['value']
            invoice_vals.update({
                'partner_id': rental.partner_id and rental.partner_id.id or False,
                'date_invoice': date_invoice,
                'invoice_line': invoice_line,
                'type': 'out_invoice',
                'tgb_type': 'rental',
                'rental_id': rental.id,
                'rental_for_month': rental_for_month
            })
            invoice_obj.create(cr, uid, invoice_vals, context)
            
        return True
    
sale_rental()

class sale_rental_line(osv.osv):
    _name = "sale.rental.line"
    
    _columns = {
        'rental_id': fields.many2one('sale.rental', 'Order Reference', ondelete='cascade'),
        'name': fields.text('Description'),
        'product_id': fields.many2one('product.product', 'Product'),
        'product_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS')),
        'price_unit': fields.float('Rental Price', digits_compute= dp.get_precision('Product Price')),
        'deposit': fields.float('Deposit', digits_compute= dp.get_precision('Product Price')),
        'transport_charge': fields.float('Transport Charge', digits_compute= dp.get_precision('Product Price')),
        'brand': fields.char('Brand', size=1024),
        'model': fields.char('Model', size=1024),
        'serial_no': fields.char('Serial No', size=1024),
        'year_of_manufacture': fields.char('Year of Manufacture', size=1024),
        'color': fields.char('Color', size=1024),
        'dimension': fields.char('Dimension', size=1024),
        'discount': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount')),
    }
    
    _defaults = {
        'product_qty': 1,
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id=False, context=None):
        vals = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            vals = {
                'name': self.pool.get('product.product').name_get(cr, uid, [product_id], context=context)[0][1],
                'brand': product.brand,
                'model': product.model,
                'serial_no': product.serial_no,
                'year_of_manufacture': product.year_of_manufacture,
                'color': product.color,
                'dimension': product.dimension,
            }
        return {'value': vals}
    
sale_rental_line()

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    _columns = {
        'brand': fields.char('Brand', size=1024),
        'model': fields.char('Model', size=1024),
        'serial_no': fields.char('Serial No', size=1024),
        'year_of_manufacture': fields.char('Year of Manufacture', size=1024),
        'color': fields.char('Color', size=1024),
        'dimension': fields.char('Dimension', size=1024),
    }
    
sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: