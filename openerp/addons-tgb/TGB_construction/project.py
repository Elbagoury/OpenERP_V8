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



class project(osv.osv):
    _inherit = "project.project"
    _description = "Project"

    def create(self, cr, uid, vals, context=None):
        if vals.get('project_code','/')=='/':
            vals['project_code'] = self.pool.get('ir.sequence').get(cr, uid, 'project.project', context=context) or '/'
        context = dict(context or {}, mail_create_nolog=True)
        this_project =  super(project, self).create(cr, uid, vals, context=context)
        return this_project

    _columns = {
        'sale_order_ids':fields.one2many('sale.order','project_confirm_id','Project Order Detail'),
        'project_code': fields.char('Project Reference', required=True, select=True, copy=False,),
     }

    _defaults={
        'project_code' : '/',
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
