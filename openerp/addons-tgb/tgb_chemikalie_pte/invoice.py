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

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
    _columns = {
        'part_no': fields.char('Part No', size=1024),
        'brand': fields.char('Brand', size=1024),
        'tgb_price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
    }
    
account_invoice_line()

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    _columns = {
        'sgd_acc_number': fields.boolean('SGD Account No'),
        'usd_acc_number': fields.boolean('USD Account No'),
    }
    
account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: