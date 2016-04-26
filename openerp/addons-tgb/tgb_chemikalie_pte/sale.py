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
from datetime import datetime
import time
import calendar
from dateutil.relativedelta import relativedelta

class sale_order(osv.osv):
    _inherit = "sale.order"
    
    _columns = {
        'customer_po_no': fields.char("Customer's PO No.", size=1024,readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'sgd_acc_number': fields.boolean('SGD Account No',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'usd_acc_number': fields.boolean('USD Account No',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'client_order_ref': fields.char('Reference/Description', copy=False,readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'note': fields.text('Terms and conditions',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'payment_term': fields.many2one('account.payment.term', 'Payment Term',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'user_id': fields.many2one('res.users', 'Salesperson',readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True, track_visibility='onchange'),
        'incoterm': fields.many2one('stock.incoterms', 'Incoterm', help="International Commercial Terms are a series of predefined commercial terms used in international transactions.",readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True,readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'origin': fields.char('Source Document', help="Reference of the document that generated this sales order request.",readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'parent_id': fields.many2one('sale.order', 'Parent'),
    }
    
    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        vals = super(sale_order, self)._prepare_order_line_procurement(cr, uid, order, line, group_id=group_id, context=context)
        location_id = order.partner_shipping_id.property_stock_customer.id
        vals['location_id'] = location_id
        routes = line.route_id and [(4, line.route_id.id)] or []
        vals['route_ids'] = routes
        vals['warehouse_id'] = order.warehouse_id and order.warehouse_id.id or False
        vals['partner_dest_id'] = order.partner_shipping_id.id
        vals['part_no'] = line.part_no
        vals['brand'] = line.brand
        return vals
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        if context is None:
            context = {}
            
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context)
        invoice_vals.update({
            'sgd_acc_number': order.sgd_acc_number,
            'usd_acc_number': order.usd_acc_number,
        })
        return invoice_vals
    
    def write(self, cr, uid, ids, vals, context=None):
        for sale in self.browse(cr, uid, ids):
            if sale.state in ['draft','sent'] and 'state' not in vals and 'message_last_post' not in vals and 'name' not in vals:
                if not sale.parent_id:
                    sql = '''
                        select count(id) from sale_order where parent_id=%s
                    '''%(sale.id)
                    cr.execute(sql)
                    num_of_sale = cr.fetchone()[0]
                    new_name = sale.name +'_R'+str(num_of_sale+1)
                    parent_id = False
                else:
                    sql = '''
                        select count(id) from sale_order where parent_id=%s
                    '''%(sale.parent_id.id)
                    cr.execute(sql)
                    num_of_sale = cr.fetchone()[0]
                    new_name = sale.parent_id.name +'_R'+str(num_of_sale+1)
                    parent_id = sale.parent_id.id
                old_name = sale.name
                super(sale_order,self).write(cr, uid, [sale.id], {'name':new_name}, context)
                default = {'parent_id': parent_id,'name': old_name}
                new_id = self.copy(cr, uid, sale.id, default)
                if not sale.parent_id:
                    sql = '''
                        update sale_order set parent_id=%s where id=%s;
                        update sale_order set parent_id=%s where parent_id=%s;
                    '''%(new_id,sale.id,new_id,sale.id)
                    cr.execute(sql)
        return super(sale_order,self).write(cr, uid, ids, vals, context)
    
sale_order()

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    _columns = {
        'part_no': fields.char('Part No', size=1024),
        'brand': fields.char('Brand', size=1024),
    }
    
    def _check_unit_price(self, cr, uid, ids, context=None):
        for so_line in self.browse(cr, uid, ids, context=context):
            if so_line.product_id and so_line.price_unit < so_line.product_id.standard_price:
                return False
        return True

    _constraints = [
        (_check_unit_price, 'The sale price much be greater than the cost price', ['product_id','price_unit']),
    ]
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        
        result = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging, fiscal_position, flag, context)
        if product:
            product_obj = self.pool.get('product.product').browse(cr, uid, product)
            result['value'].update({
                'brand': product_obj.brand,
            })
        return result
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id, context)
        res.update({
                'brand': line.brand,
            })
        return res
    
sale_order_line()

class procurement_order(osv.osv):
    _inherit = "procurement.order"
    _columns = {
        'part_no': fields.char('Part No', size=1024),
        'brand': fields.char('Brand', size=1024),
    }
    
    def _run_move_create(self, cr, uid, procurement, context=None):
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        newdate = (datetime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=procurement.rule_id.delay or 0)).strftime('%Y-%m-%d %H:%M:%S')
        group_id = False
        if procurement.rule_id.group_propagation_option == 'propagate':
            group_id = procurement.group_id and procurement.group_id.id or False
        elif procurement.rule_id.group_propagation_option == 'fixed':
            group_id = procurement.rule_id.group_id and procurement.rule_id.group_id.id or False
        #it is possible that we've already got some move done, so check for the done qty and create
        #a new move with the correct qty
        already_done_qty = 0
        already_done_qty_uos = 0
        for move in procurement.move_ids:
            already_done_qty += move.product_uom_qty if move.state == 'done' else 0
            already_done_qty_uos += move.product_uos_qty if move.state == 'done' else 0
        qty_left = max(procurement.product_qty - already_done_qty, 0)
        qty_uos_left = max(procurement.product_uos_qty - already_done_qty_uos, 0)
        vals = {
            'name': procurement.name,
            'company_id': procurement.rule_id.company_id.id or procurement.rule_id.location_src_id.company_id.id or procurement.rule_id.location_id.company_id.id or procurement.company_id.id,
            'product_id': procurement.product_id.id,
            'product_uom': procurement.product_uom.id,
            'product_uom_qty': qty_left,
            'product_uos_qty': (procurement.product_uos and qty_uos_left) or qty_left,
            'product_uos': (procurement.product_uos and procurement.product_uos.id) or procurement.product_uom.id,
            'partner_id': procurement.rule_id.partner_address_id.id or (procurement.group_id and procurement.group_id.partner_id.id) or False,
            'location_id': procurement.rule_id.location_src_id.id,
            'location_dest_id': procurement.location_id.id,
            'move_dest_id': procurement.move_dest_id and procurement.move_dest_id.id or False,
            'procurement_id': procurement.id,
            'rule_id': procurement.rule_id.id,
            'procure_method': procurement.rule_id.procure_method,
            'origin': procurement.origin,
            'picking_type_id': procurement.rule_id.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, x.id) for x in procurement.route_ids],
            'warehouse_id': procurement.rule_id.propagate_warehouse_id.id or procurement.rule_id.warehouse_id.id,
            'date': newdate,
            'date_expected': newdate,
            'propagate': procurement.rule_id.propagate,
            'priority': procurement.priority,
            'part_no': procurement.part_no,
            'brand': procurement.brand,
        }
        return vals

procurement_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: