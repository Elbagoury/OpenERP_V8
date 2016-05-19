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

from openerp.osv import osv, fields
from openerp import models, api
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from itertools import groupby
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp.tools.safe_eval import safe_eval as eval
from openerp import SUPERUSER_ID

class hr_employee(osv.Model):
    _inherit = 'hr.employee'
    _columns = {
        # 'payroll_actatek_id':fields.char('Payroll ActaTek Id', size=64),
        'payroll_hourly_rate':fields.float('Payroll Hourly Rate', digits_compute=dp.get_precision('Account')),
        'payroll_ot_rate': fields.float('Payroll OT Rate', digits_compute=dp.get_precision('Account')),
        'payroll_ph_rate': fields.float('Payroll PH Rate', digits_compute=dp.get_precision('Account'))
            }

class hr_work_day(osv.Model):
    _inherit = 'hr.payslip.worked_days'
    _columns = {
        'project_no':fields.char('Project Number', size=64),
            }

class hr_employee(osv.Model):
    _inherit = 'hr.employee'
    _columns = {
    'contract_ids': fields.many2many('hr.contract', 'hr_contract_employee_rel', 'employee_id', 'contract_id', 'Contracts'),
    }

class hr_input(osv.Model):
    _inherit = 'hr.payslip.input'

    _columns = {
        'project_no':fields.char('Project Number', size=64),
            }

class project_costing(osv.Model):
    _inherit = 'project.costing'

    def payslip_costing(self,cr,uid,ids,context={}):
        attendance_obj = self.pool.get('hr.payslip.worked_days')
        input_obj = self.pool.get('hr.payslip.input')
        for costing in self.browse(cr,uid,ids):
            project = costing.project_id
            if project:
                project_no = project.project_code
            if project_no:

                # For working hours
                workdays = {}
                payslip_workdays = {}
                payslip_workdays_hours = {}
                payslip = {}

                # For input
                input_ids = input_obj.search(cr,uid,[('project_no', '=', project_no),
                                                     ('payslip_id.state', '=', 'done')], order='payslip_id')
                # workday_ids = attendance_obj.search(cr,uid,[('project_no', '=', project_no),
                #                                             ('payslip_id.state', '=', 'done')], order='payslip_id')
                total_amount = {}

                old_payslip = None
                payslips_allowance = {}
                for input in input_obj.browse(cr,uid,input_ids):
                    if old_payslip != input.payslip_id:
                        old_payslip = input.payslip_id
                        payslips_allowance = {}
                        for line in input.payslip_id.line_ids:
                            if line.code not in payslips_allowance:
                                payslips_allowance[line.code] = 0
                            payslips_allowance[line.code] += line.total
                    if input.payslip_id.employee_id.id not in total_amount:
                        total_amount[input.payslip_id.employee_id.id] = 0
                    if input.project_no == project_no:
                        if payslips_allowance.get(input.code):
                            total_amount[input.payslip_id.employee_id.id] += input.amount

                # for workday in attendance_obj.browse(cr,uid,workday_ids):
                #     if workday.payslip_id.employee_id.id not in workdays:
                #         workdays[workday.payslip_id.employee_id.id] = {}
                #     if workday.code not in workdays[workday.payslip_id.employee_id.id]:
                #         workdays[workday.payslip_id.employee_id.id][workday.code] = 0
                #     workdays[workday.payslip_id.employee_id.id][workday.code] += workday.number_of_hours
                #     if workday.payslip_id.id not in payslip:
                #         payslip[workday.payslip_id.id] = True
                #         for line in workday.payslip_id.line_ids:
                #             if workday.payslip_id.employee_id.id not in payslip_workdays:
                #                 payslip_workdays[workday.payslip_id.employee_id.id] = {}
                #             if line.code not in payslip_workdays[workday.payslip_id.employee_id.id]:
                #                 payslip_workdays[workday.payslip_id.employee_id.id][line.code] = 0
                #             payslip_workdays[workday.payslip_id.employee_id.id][line.code] += line.total
                #         for line in workday.payslip_id.worked_days_line_ids:
                #             if workday.payslip_id.employee_id.id not in payslip_workdays_hours:
                #                 payslip_workdays_hours[workday.payslip_id.employee_id.id] = {}
                #             if line.code not in payslip_workdays_hours[workday.payslip_id.employee_id.id]:
                #                 payslip_workdays_hours[workday.payslip_id.employee_id.id][line.code] = 0
                #             payslip_workdays_hours[workday.payslip_id.employee_id.id][line.code] += line.number_of_hours

                # for employee, employee_value in payslip_workdays.items():
                #     for code, value in employee_value.items():
                #         payslip_amount = value
                #         payslip_hours = payslip_workdays_hours[employee].get(code, 0)
                #         project_amount = 0
                #         if payslip_hours:
                #             project_amount = (payslip_amount/payslip_hours) * workdays[employee].get(code, 0)
                #         if employee not in total_amount:
                #             total_amount[employee] = 0
                #         total_amount[employee] += project_amount
        self.pool.get('project.hr.cost').unlink(cr,uid,self.pool.get('project.hr.cost').search(cr,uid,[('project_costing_id','=',costing.id)]))
        for employee_id, value in total_amount.items():
            self.pool.get('project.hr.cost').create(cr,uid,{'project_costing_id':costing.id,
                                                        'name': 'Project Payslips',
                                                        'employee_id': employee_id,
                                                        'amount': value,
                                                    })
        return

class hr_payslip(osv.Model):
    _inherit = 'hr.payslip'
    _columns = {
        'payment_mode': fields.selection(
            [('cash', 'Cash'), ('cheque', 'Cheque'), ('deposit', 'Bank Deposit')],
            'Mode of Payment', readonly=True, states={'draft': [('readonly', False)]}),
    }
    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        def _sum_salary_rule_wage_type(localdict, wage_type, amount):
            localdict['wage_types'].dict[wage_type.code] = wage_type.code in localdict['wage_types'].dict and localdict['wage_types'].dict[wage_type.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class DonationLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, employee_donation_input as di \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = di.payroll_id AND di.code = %s",
                           (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
                            (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()
                return res and res[0] or 0.0

        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        #added
        wage_types_dict = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.pool.get('hr.payslip')
        inputs_obj = self.pool.get('hr.payslip.worked_days')
        obj_rule = self.pool.get('hr.salary.rule')
        payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)
        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line
            if worked_days_line.code+'_SUM' not in worked_days:
                worked_days[worked_days_line.code+'_SUM'] = []
            worked_days[worked_days_line.code+'_SUM'].append(worked_days_line)
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line
            if input_line.code+'_SUM' not in inputs:
                inputs[input_line.code+'_SUM'] = 0
            inputs[input_line.code+'_SUM'] += input_line.amount
        print inputs
        donations = {}
        for donation_line in payslip.input_donation_ids:
            donations[donation_line.code] = donation_line

        print "\n\ndonations is ::: ", donations
        #added
        wage_types_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, wage_types_dict)
        categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
        donation_obj = DonationLine(self.pool, cr, uid, payslip.employee_id.id, donations)
        worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
        payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)

        obj_employee = self.pool.get('hr.employee')

        localdict = {'wage_types':wage_types_obj,
                     'categories': categories_obj,
                     'rules': rules_obj,
                     'payslip': payslip_obj,
                     'worked_days': worked_days_obj,
                     'inputs': input_obj,
                     'donations': donation_obj}
        #get the ids of the structures on the contracts and their parent id as well
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        #get the rules of the structure and thier children
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict.update({'employee': employee, 'contract': contract})
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_name'] = False
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    #amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    amount, qty, rate, item_name = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    localdict = _sum_salary_rule_wage_type(localdict, rule.wage_type_id, tot_rule - previous_amount)
                    #create/overwrite the rule in the temporary results
                    if amount != 0.0:
                        result_dict[key] = {
                            'salary_rule_id': rule.id,
                            'contract_id': contract.id,
                            #'name': rule.name,
                            'name': item_name or 'Undefined',
                            'code': rule.code,
                            'category_id': rule.category_id.id,
                            'sequence': rule.sequence,
                            'appears_on_payslip': rule.appears_on_payslip,
                            'condition_select': rule.condition_select,
                            'condition_python': rule.condition_python,
                            'condition_range': rule.condition_range,
                            'condition_range_min': rule.condition_range_min,
                            'condition_range_max': rule.condition_range_max,
                            'amount_select': rule.amount_select,
                            'amount_fix': rule.amount_fix,
                            'amount_python_compute': rule.amount_python_compute,
                            'amount_percentage': rule.amount_percentage,
                            'amount_percentage_base': rule.amount_percentage_base,
                            'register_id': rule.register_id.id,
                            'amount': amount,
                            'employee_id': contract.employee_id.id,
                            'quantity': qty,
                            'rate': rate,
                            'employee_donation_id': rule.employee_donation_id.id
                        }
                else:
                    #blacklist this rule and its children
                    blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]

        result = [value for code, value in result_dict.items()]
        print "\n\nresult are ::: ", result
        return result