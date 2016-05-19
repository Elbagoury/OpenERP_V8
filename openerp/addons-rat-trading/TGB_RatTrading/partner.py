# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
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

from datetime import datetime, date
from lxml import etree
import time

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.addons.resource.faces import task as Task
from openerp.osv import fields, osv
from openerp.tools.translate import _



class partner(osv.osv):
    _inherit = "res.partner"

    _columns = {
        'customer_id': fields.char('Id', size=255),
        'customer_monday': fields.boolean('Customer (Monday)'),
        'customer_wednesday': fields.boolean('Customer (Wednesday)'),
        'customer_friday': fields.boolean('Customer (Friday)'),
     }

    _defaults = {
        'customer_monday':False,
        'customer_wednesday':False,
        'customer_friday':False,
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
