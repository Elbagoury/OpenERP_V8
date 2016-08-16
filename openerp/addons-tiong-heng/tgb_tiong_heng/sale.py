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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta
import time
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    _columns = {
        'timing_id': fields.many2one('tgb.timing', 'Timing'),
        'bus_capacity_id': fields.many2one('tgb.bus.capacity', 'Bus Capacity'),
        'route_id': fields.many2one('tgb.route', 'Route'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(sale_order_line, self).default_get(cr, uid, fields, context=context)
        module, product_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_product_consultant_product_template')
        res.update({
            'product_id': product_id,
        })
        return res

sale_order_line()


class tgb_timing(osv.osv):
    _name = 'tgb.timing'

    _columns = {
        'name': fields.char('Name',size=1024,required=True),
    }
    
tgb_timing()

class tgb_bus_capacity(osv.osv):
    _name = 'tgb.bus.capacity'

    _columns = {
        'name': fields.char('Name',size=1024,required=True),
    }
    
tgb_bus_capacity()

class tgb_route(osv.osv):
    _name = 'tgb.route'

    _columns = {
        'name': fields.char('Name',size=1024,required=True),
    }
    
tgb_route()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: