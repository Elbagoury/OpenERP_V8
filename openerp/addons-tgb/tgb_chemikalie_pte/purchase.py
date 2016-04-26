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
from openerp.tools.float_utils import float_compare

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, group_id, context=None):
        ''' prepare the stock move data from the PO line. This function returns a list of dictionary ready to be used in stock.move's create()'''
        product_uom = self.pool.get('product.uom')
        price_unit = order_line.price_unit
        if order_line.product_uom.id != order_line.product_id.uom_id.id:
            price_unit *= order_line.product_uom.factor / order_line.product_id.uom_id.factor
        if order.currency_id.id != order.company_id.currency_id.id:
            #we don't round the price_unit, as we may want to store the standard price with more digits than allowed by the currency
            price_unit = self.pool.get('res.currency').compute(cr, uid, order.currency_id.id, order.company_id.currency_id.id, price_unit, round=False, context=context)
        res = []
        move_template = {
            'name': order_line.name or '',
            'product_id': order_line.product_id.id,
            'product_uom': order_line.product_uom.id,
            'product_uos': order_line.product_uom.id,
            'date': order.date_order,
            'date_expected': fields.date.date_to_datetime(self, cr, uid, order_line.date_planned, context),
            'location_id': order.partner_id.property_stock_supplier.id,
            'location_dest_id': order.location_id.id,
            'picking_id': picking_id,
            'partner_id': order.dest_address_id.id,
            'move_dest_id': False,
            'state': 'draft',
            'purchase_line_id': order_line.id,
            'company_id': order.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': order.picking_type_id.id,
            'group_id': group_id,
            'procurement_id': False,
            'origin': order.name,
            'route_ids': order.picking_type_id.warehouse_id and [(6, 0, [x.id for x in order.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id':order.picking_type_id.warehouse_id.id,
            'invoice_state': order.invoice_method == 'picking' and '2binvoiced' or 'none',
            'part_no': order_line.part_no,
            'brand': order_line.brand,
            'tgb_price_unit': order_line.tgb_price_unit,
        }

        diff_quantity = order_line.product_qty
        for procurement in order_line.procurement_ids:
            procurement_qty = product_uom._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, to_uom_id=order_line.product_uom.id)
            tmp = move_template.copy()
            tmp.update({
                'product_uom_qty': min(procurement_qty, diff_quantity),
                'product_uos_qty': min(procurement_qty, diff_quantity),
                'move_dest_id': procurement.move_dest_id.id,  #move destination is same as procurement destination
                'group_id': procurement.group_id.id or group_id,  #move group is same as group of procurements if it exists, otherwise take another group
                'procurement_id': procurement.id,
                'invoice_state': procurement.rule_id.invoice_state or (procurement.location_id and procurement.location_id.usage == 'customer' and procurement.invoice_state=='2binvoiced' and '2binvoiced') or (order.invoice_method == 'picking' and '2binvoiced') or 'none', #dropship case takes from sale
                'propagate': procurement.rule_id.propagate,
            })
            diff_quantity -= min(procurement_qty, diff_quantity)
            res.append(tmp)
        #if the order line has a bigger quantity than the procurement it was for (manually changed or minimal quantity), then
        #split the future stock move in two because the route followed may be different.
        if float_compare(diff_quantity, 0.0, precision_rounding=order_line.product_uom.rounding) > 0:
            move_template['product_uom_qty'] = diff_quantity
            move_template['product_uos_qty'] = diff_quantity
            res.append(move_template)
        return res
    
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        """Collects require data from purchase order line that is used to create invoice line
        for that purchase order line
        :param account_id: Expense account of the product of PO line if any.
        :param browse_record order_line: Purchase order line browse record
        :return: Value for fields of invoice lines.
        :rtype: dict
        """
        return {
            'name': order_line.name,
            'account_id': account_id,
            'price_unit': order_line.price_unit or 0.0,
            'quantity': order_line.product_qty,
            'product_id': order_line.product_id.id or False,
            'uos_id': order_line.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
            'account_analytic_id': order_line.account_analytic_id.id or False,
            'purchase_line_id': order_line.id,
            'part_no': order_line.part_no,
            'brand': order_line.brand,
            'tgb_price_unit': order_line.tgb_price_unit,
        }
    
    def write(self, cr, uid, ids, vals, context=None):
        new_write = super(purchase_order, self).write(cr, uid, ids, vals, context)
        if vals.get('state', False)=='approved':
            currency_obj = self.pool.get('res.currency')
            product_obj = self.pool.get('product.template')
            for po in self.browse(cr, uid, ids):
                for po_line in po.order_line:
                    new_amount = po_line.price_unit
                    if po.currency_id!=po.company_id.currency_id:
                        new_amount = currency_obj.compute(cr, uid,po.currency_id.id,po.company_id.currency_id.id, po_line.price_unit)
                    product_obj.write(cr, uid, [po_line.product_id.id], {'standard_price': new_amount})
        return new_write
    
purchase_order()

class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    
    _columns = {
        'part_no': fields.char('Part No', size=1024),
        'brand': fields.char('Brand', size=1024),
        'tgb_price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
    }
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order, fiscal_position_id, date_planned,
            name, price_unit, state, context)
        if product_id:
            product_obj = self.pool.get('product.product').browse(cr, uid, product_id)
            tgb_price_unit = res['value'].get('price_unit',False) and res['value']['price_unit'] or 0
            vals = self.onchange_tgb_price_unit(cr, uid, ids, partner_id, product_id, qty, tgb_price_unit, context)['value']
            res['value'].update({
                'brand': product_obj.brand,
                'tgb_price_unit': tgb_price_unit,
                'price_unit': vals.get('price_unit', False) and vals['price_unit'] or 0,
            })
        return res
    
    def onchange_tgb_price_unit(self, cr, uid, ids, partner_id=False, product_id=False, product_qty=0, tgb_price_unit=0, context=None):
        res = {}
        res['price_unit'] = tgb_price_unit
        if partner_id and product_qty and tgb_price_unit and product_id:
            sql = '''
                select case when amount_discount!=0 then amount_discount else 0 end amount_discount
                    from supplier_pricelist where partner_id=%s and %s between qty_from and qty_to and product_id=%s
                    order by id desc limit 1
            '''%(partner_id, product_qty, product_id)
            cr.execute(sql)
            discount = cr.fetchone()
            if discount and tgb_price_unit - discount[0]>0:
                res['price_unit'] = tgb_price_unit - discount[0]
        return {'value': res}
    
purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: