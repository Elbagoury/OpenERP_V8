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

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the sales order and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'quotation_sent')
        return self.pool['report'].get_action(cr, uid, ids, 'tgb_sale_project.report_sample_with_one_project', context=context)
    
    _columns = {
        'list_project_line': fields.one2many('list.project','order_id','List Project'),
    }
    
    
sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    def _get_product_quantity(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            product_quantity = line.project_id.quantity*line.quantity
            sql = '''
                update sale_order_line set product_uom_qty=%s where id=%s
            '''%(product_quantity,line.id)
            cr.execute(sql)
            res[line.id] = product_quantity
        return res
    
    def _get_project(self, cr, uid, ids, context=None):
        result = {}
        list_project_ids = self.pool.get('sale.order.line').search(cr, uid, [('project_id','in',ids)])
        for id in list_project_ids:
            result[id] = True
        return result.keys()
    
    _columns = {
        'line_no': fields.integer('No.'),
        'project_id': fields.many2one('list.project','Project', ondelete='cascade'),
        'mark_up': fields.float('Mark Up (%)'),
        'assembly_cost': fields.boolean('Assembly Cost'),
        'quantity': fields.float('Quantity'),
        'product_quantity': fields.function(_get_product_quantity,string='Product Quantity',type='float', store={
                'sale.order.line': (lambda self, cr, uid, ids, c={}: ids, ['quantity','project_id'], 10),
                'list.project': (_get_project, ['order_id','project_line','quantity'], 10),
            }),
    }
    
    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            update_ids = self.search(cr, uid,[('project_id','=',line.project_id.id),('line_no','>',line.line_no)])
            if update_ids:
                cr.execute("UPDATE sale_order_line SET line_no=line_no-1 WHERE id in %s",(tuple(update_ids),))
        return super(sale_order_line, self).unlink(cr, uid, ids, context)  
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('project_id',False) and not vals.get('order_id',False):
            project = self.pool.get('list.project').browse(cr, uid, [vals['project_id']])
            vals.update({'order_id': project.order_id.id})
        if vals.get('project_id',False):
            vals['line_no'] = len(self.search(cr, uid,[('project_id', '=', vals['project_id'])])) + 1
        return super(sale_order_line, self).create(cr, uid, vals, context)
    
    def onchange_product(self, cr, uid, ids, product_id=False, context=None):
        vals = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            vals = {
                'name': product.name,
                'product_uom': product.uom_id.id,
                'price_unit': product.list_price,
            }
        return {'value':vals}
    
sale_order_line()

class list_project(osv.osv):
    _name = 'list.project'
    
    def _get_total_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        order_line_obj = self.pool.get('sale.order.line')
        for project in self.browse(cr, uid, ids, context=context):
            res[project.id] = {
                'total_amount': 0,
                'total_price': 0,
            }
            total_amount = 0
            order_line_ids = order_line_obj.search(cr, uid, [('project_id','=',project.id)])
            for order_line in order_line_obj.browse(cr, uid, order_line_ids):
                if 100-order_line.mark_up:
                    total_amount += (float(order_line.price_unit)/float(100-order_line.mark_up)*100)
            res[project.id]['total_amount'] = total_amount
            res[project.id]['total_price'] = total_amount*project.quantity
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        list_project_ids = self.pool.get('list.project').search(cr, uid, [('order_id','in',ids)])
        for id in list_project_ids:
            result[id] = True
        return result.keys()
    
    def _get_order_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids):
            result[line.project_id.id] = True
        return result.keys()
    
    _columns = {
        'order_id': fields.many2one('sale.order', 'Order', ondelete='cascade'),
        'name': fields.char('Project Title',size=1024),
        'quantity': fields.float('Quantity'),
        'total_amount': fields.function(_get_total_amount,string='Total Amount',type='float', store={
            'list.project': (lambda self, cr, uid, ids, c={}: ids, ['project_line','quantity'], 10),
            'sale.order': (_get_order, ['order_line','list_project_line'], 10),
            'sale.order.line': (_get_order_line, ['project','price_unit','mark_up'], 10),                                                              
            },multi='total'),
        'total_price': fields.function(_get_total_amount,string='Total Price',type='float', store={
            'list.project': (lambda self, cr, uid, ids, c={}: ids, ['project_line','quantity'], 10),
            'sale.order': (_get_order, ['order_line','list_project_line'], 10),
            'sale.order.line': (_get_order_line, ['project','price_unit','mark_up'], 10),                                                              
            },multi='total'),
        'project_line': fields.one2many('sale.order.line', 'project_id', 'Project Line'),
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('search_project', False):
            if context.get('list_project_line', False) and context['list_project_line']:
                project_ids = []
                for line in context['list_project_line']:
                    if len(line)>=1 and line[1] and line[0]==4:
                        project_ids.append(line[1])
                args += [('id','in',project_ids)]
        return super(list_project, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if context is None:
            context = {}
        ids = self.search(cr, user, args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)
    
list_project()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: