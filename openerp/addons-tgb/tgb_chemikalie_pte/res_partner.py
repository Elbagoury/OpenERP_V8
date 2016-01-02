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

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'code': fields.char('Code', size=1024),
        'tax_code': fields.char('Tax Code', size=1024),
        'attention': fields.char('Attention', size=1024),
        
        'delivery_street': fields.char('Street'),
        'delivery_street2': fields.char('Street2'),
        'delivery_zip': fields.char('Zip', size=24, change_default=True),
        'delivery_city': fields.char('City'),
        'delivery_state_id': fields.many2one("res.country.state", 'State', ondelete='restrict'),
        'delivery_country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
    }
    
res_partner()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: