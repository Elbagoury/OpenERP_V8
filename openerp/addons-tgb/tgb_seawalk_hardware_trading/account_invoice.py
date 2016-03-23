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

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    _columns = {
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('waiting_manager', 'Waiting Confirm'),
            ('open','Open'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' when invoice is in Pro-forma status,invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice."),
        'our_do_no': fields.char('Our D/O No.'),
    }
    
    def bt_confirm(self, cr, uid, ids, context=None):
        sql = '''
            select uid from res_groups_users_rel
                where gid in (select res_id from ir_model_data where module='base' and name='group_sale_manager')
                    and uid=%s
        '''%(uid)
        cr.execute(sql)
        user_ids = [r[0] for r in cr.fetchall()]
        for invoice in self.browse(cr, uid, ids):
            if user_ids:
                self.signal_workflow(cr, uid, [invoice.id], 'invoice_open')
            else:
                temp = 0
                for line in invoice.invoice_line:
                    if line.quantity<0 or line.price_unit<line.product_id.list_price:
                        temp = 1
                        break
                if temp:
                    self.signal_workflow(cr, uid, [invoice.id], 'invoice_waiting_manager')
                else:
                    self.signal_workflow(cr, uid, [invoice.id], 'invoice_open')
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('state')=='open':
            picking_list_obj = self.pool.get('picking.list')
            picking_list_ids = picking_list_obj.search(cr, uid, [('state','=','draft')])
            invoice_line_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', 'in', ids)])
            if not picking_list_ids:
                picking_list_obj.create(cr, uid, {'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                  'invoice_line_ids': [(6,0,invoice_line_ids)]})
            else:
                for invoice_line in invoice_line_ids:
                    picking_list_obj.write(cr, uid, [picking_list_ids[0]], {'invoice_line_ids': [(4, invoice_line)],})
                    
        return super(account_invoice, self).write(cr, uid, ids, vals, context)
    
    _columns = {
        'your_ref_no': fields.char('Your Ref. No', size=1024),
        'terms': fields.char('Terms', size=1024),
    }
    
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
    _columns = {
        'shelf': fields.char('Shelf', size=1024),
    }
    
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: