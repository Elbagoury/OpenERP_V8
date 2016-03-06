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
    
    def _get_sale_history(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            history_ids = self.search(cr, uid, [('partner_id', '=', order.partner_id.id),('state', 'not in', ['draft','sent','cancel']),('id', '!=', order.id)])
            res[order.id] = history_ids
        return res
    
    _columns = {
        'sale_history_ids': fields.function(_get_sale_history, type='many2many', relation='sale.order', string='Past Sale History'),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_manager', 'Waiting Confirm'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True),
    }
    
    def bt_confirm(self, cr, uid, ids, context=None):
        sql = '''
            select uid from res_groups_users_rel
                where gid in (select res_id from ir_model_data where module='base' and name='group_sale_manager')
                    and uid=%s
        '''%(uid)
        cr.execute(sql)
        user_ids = [r[0] for r in cr.fetchall()]
        for order in self.browse(cr, uid, ids):
            if user_ids:
                self.action_button_confirm(cr, uid, [order.id], context)
            else:
                temp = 0
                for line in order.order_line:
                    if line.product_uom_qty<0 or line.price_unit<line.product_id.list_price:
                        temp = 1
                        break
                if temp:
                    self.signal_workflow(cr, uid, [order.id], 'quotation_waiting_manager')
                else:
                    self.action_button_confirm(cr, uid, [order.id], context)
        return True
    
sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: