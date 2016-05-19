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

class hr_employee(osv.osv):
    _inherit = 'hr.employee'

    
#     def _fs_end_date(self, cursor, user, ids, name, arg, context=None):
#         res = {}
#         for emp in self.browse(cursor, user, ids, context=context):
#             res[emp.id] = emp.director_appt_date or False
#         return res
#     
#     def _estimate_chargable_income_date(self, cursor, user, ids, name, arg, context=None):
#         res = {}
#         for emp in self.browse(cursor, user, ids, context=context):
#             res[emp.id] = emp.director_appt_date or False
#         return res
#     
#     def _annual_return_date(self, cursor, user, ids, name, arg, context=None):
#         res = {}
#         for emp in self.browse(cursor, user, ids, context=context):
#             res[emp.id] = emp.director_appt_date or False
#         return res
#     
#     def _sole_proprietary_partnership_date(self, cursor, user, ids, name, arg, context=None):
#         res = {}
#         for emp in self.browse(cursor, user, ids, context=context):
#             res[emp.id] = emp.director_appt_date or False
#         return res
#     
#     def _tax_form_cs(self, cursor, user, ids, name, arg, context=None):
#         res = {}
#         for emp in self.browse(cursor, user, ids, context=context):
#             res[emp.id] = emp.director_appt_date or False
#         return res
#     
#     def _submit_monthly_cpf(self, cursor, user, ids, name, arg, context=None):
#         res = {}
#         for emp in self.browse(cursor, user, ids, context=context):
#             res[emp.id] = 0.0 or False
#         return res
#     
#     def _compute_submit_yearly_staff_salary(self, cursor, user, ids, name, arg, context=None):
#         res = {}
#         for emp in self.browse(cursor, user, ids, context=context):
#             res[emp.id] = 0.0 or False
#         return res
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Company'),
#         'uen':fields.char('UEN'),
#         'chinese_name':fields.char('Chinese Name'),
#         'incorporation_date':fields.date('Incorporation Date'),
#         'director_appt_date':fields.date('Director Appt Date'),
#         'secretary_appt_date':fields.date('Secretary Appt Date'),
#         'employment':fields.selection([('employee','Employee'),('shareholder','Shareholder')],'Employment'),
#         'paid_up_capital':fields.float('Paid Up Capital'),
#         'c_status':fields.selection([('live','Live'),('employeed','Employeed')],'C Satus'),
#         'race':fields.char('Race'),
#         'country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
#         'block_house_no':fields.char('Block/House No'),
#         'street_name': fields.char('Street Name'),
#         'level_no': fields.char('Level No'),
#         'unit_no': fields.char('Unit No'),
#         'postal_code': fields.char('Postal Code'),
#         'period_year':fields.selection([('period','Period'),('year','Year')],'Period or Year'),
#         'fs_start_date':fields.date('FS Start Date'),
#         'fs_end_date':fields.function(_fs_end_date, string='FS End Date', type='date'),
#         'axp_report':fields.date('AXP Report'),
#         'estimate_chargable_income_date':fields.function(_estimate_chargable_income_date,string='Estimate Chargable lncome Date', type='date'),
#         'annual_general_meeting_date':fields.date('Annual General Meeting Date'),
#         'annual_return_date':fields.function(_annual_return_date,string='Annual Return Date',type='date'),
#         'financial_month':fields.many2one('account.period', string='Financial Month'),
#         'next_annual_general_meeting_due_date':fields.date('Next Annual General Meeting Due Date'),
#         'sole_proprietary_partnership':fields.selection([('sole_proprietary','Sole Proprietary'),('partnership','Partnership')],'Sole Proprietary or Partnership'),
#         'last_financiall_year_end':fields.date('Last Financiall Year End'),
#         'sole_proprietary_partnership_date':fields.function(_sole_proprietary_partnership_date, string='Tax:Sole Proprietary & Partnership',type='date'),
#         'tax_form_cs':fields.function(_tax_form_cs, string='Tax:Form CS (YA)',type='date'),
#         'submit_monthly_cpf':fields.function(_submit_monthly_cpf, string='Submit Monthly CPF',type='float'),
#         'compute_submit_yearly_staff_salary':fields.function(_compute_submit_yearly_staff_salary, string='Compute & Submit Yearly Staff Salary',type='float'),
#         'remarks_1': fields.char('Remarks 1'),
#         'remarks_2': fields.char('Remarks 2'),
    }
    
    
hr_employee()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: