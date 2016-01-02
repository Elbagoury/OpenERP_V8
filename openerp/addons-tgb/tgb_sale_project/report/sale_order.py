# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from openerp.osv import osv
from openerp.report import report_sxw


class sample_with_one_project(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(sample_with_one_project, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            'time': time,
            'get_contact': self.get_contact,
            'get_total': self.get_total,
    })
    
    def get_contact(self,partner_id):
        vals = {
            'name': '',
            'email': '',
        }
        if partner_id and partner_id.child_ids:
            contact = partner_id.child_ids[0]
            vals = {
                'name': contact.name,
                'email': contact.email,
            }
        return vals

    def get_total(self, list_project_line):
        total = 0
        for line in list_project_line:
            total+=line.total_price
        return total

class report_sample_with_one_project(osv.AbstractModel):
    _name = 'report.tgb_sale_project.report_sample_with_one_project'
    _inherit = 'report.abstract_report'
    _template = 'tgb_sale_project.report_sample_with_one_project'
    _wrapped_report_class = sample_with_one_project


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
