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

class picking_list(osv.osv):
    _name = 'picking.list'
    _order = 'name desc'
    _columns = {
        'name': fields.datetime('Date', readonly=True, states={'draft': [('readonly', False)]}),
        'invoice_line_ids': fields.many2many('account.invoice.line', 'pickinglist_invoiceline_ref', 'pickinglist_id', 'invoiceline_id', 'Invoice Lines'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'Status', readonly=True),
    }
    
    _defaults = {
        'name': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state': 'draft',
    }
    
    def bt_confirm(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'})
    
    def done_create_picking_list_auto(self, cr, uid, context=None):
        picking_list_ids = self.search(cr, uid, [('state','=','draft')])
        if picking_list_ids:
            self.bt_confirm(cr, uid, picking_list_ids, context)
        self.create(cr, uid, {'name': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True
    
picking_list()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: