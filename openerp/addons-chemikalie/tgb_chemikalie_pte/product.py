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
import openerp.addons.decimal_precision as dp

class product_template(osv.osv):
    _inherit = "product.template"

    def _get_currency(self, cr, uid, ctx):
        comp = self.pool.get('res.users').browse(cr,uid,uid).company_id
        if not comp:
            comp_id = self.pool.get('res.company').search(cr, uid, [])[0]
            comp = self.pool.get('res.company').browse(cr, uid, comp_id)
        return comp.currency_id.id

    _columns = {
        'brand': fields.char('Brand', size=1024),
        'factor': fields.float('Factor', digits_compute= dp.get_precision('Product Price')),
        'cost_currency_id' : fields.many2one('res.currency', "Currency", required=True, help="The currency the field is expressed in."),
        'supplier_pricelist_line': fields.one2many('supplier.pricelist', 'product_id', 'Pricelist'),

    }
    _defaults = {
        'factor': 1,
        "cost_currency_id": _get_currency
    }
product_template()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: