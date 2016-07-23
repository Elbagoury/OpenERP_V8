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
        if move.picking_id.sale_id and move.picking_id.sale_id.rental_id:
            vals.update({
                'rental_id': move.picking_id.sale_id.rental_id.id,
                'tgb_type': 'piano_sale',
            })
        
        return vals
    
    _columns = {
        'rental_id': fields.many2one('sale.rental', 'Rental'),
    }
    
stock_picking()

class stock_move(osv.osv):
    _inherit = "stock.move"
    
    _columns = {
        'model': fields.char('Model', size=1024),
        'serial_no': fields.char('Serial No', size=1024),
    }
    
    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context)
        res.update({
            'model': move.model,
            'serial_no': move.serial_no,
        })
        return res
    
stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: