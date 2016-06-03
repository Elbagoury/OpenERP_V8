from openerp import models, api
from openerp import fields as fields2
from openerp.osv import fields, osv
from base64 import b64decode
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import csv
import time
from datetime import datetime
from dateutil import relativedelta
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class payslip_import(models.Model):
    _name = 'hr.payslip.import'

    _columns = {
        'date_from': fields.date('Date From', readonly=True, states={'draft': [('readonly', False)]}, required=True),
        'date_to': fields.date('Date To', readonly=True, states={'draft': [('readonly', False)]}, required=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
        ], 'Status', select=True, readonly=True, copy=False,),
        'payslip_ids': fields.one2many('hr.payslip', 'importer', 'Payslips', readonly=True),
        'line_ids': fields.one2many('hr.payslip.import.line', 'slip_id', 'Payslip Lines', readonly=True, states={'draft':[('readonly',False)]}),
    }
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-01'),
        'date_to': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
        'state': 'draft',
    }

    def confirm_payslip(self,cr,uid,ids,context):
        payslip_obj = self.pool.get('hr.payslip')
        employee_obj = self.pool.get('hr.employee')
        contract_obj = self.pool.get('hr.contract')
        input_line = self.pool.get('hr.payslip.input')
        input_type = ['BASIC', 'OT', 'NS_OTHER', 'UNPAID', 'CPF', 'CDAC', 'latecomer', 'timeoff']
        less_type = ['NS_OTHER', 'UNPAID', 'CDAC', 'CPF', 'latecomer', 'timeoff']
        for im in self.browse(cr,uid,ids):
            for line in im.line_ids:
                contract_ids = line.employee_id.contract_ids
                if not contract_ids:
                    contract_ids = contract_obj.search(cr,uid,[('employee_ids', 'in', line.employee_id.id)], order='date_start desc')
                    contract_ids = contract_obj.browse(cr, uid, contract_ids)
                if contract_ids:
                    contract = contract_ids[0]
                else:
                    raise osv.except_osv('Error!', 'No contract for employee!')
                rule_list = []
                for rule in contract.struct_id.rule_ids:
                    rule_list.append(rule.code)
                payslip_id = payslip_obj.create(cr, uid, {'employee_id': line.employee_id.id,
                                                          'contract_id': contract.id,
                                                          'struct_id': contract.struct_id.id,
                                                          'date_from': im.date_from,
                                                          'date_to': im.date_to,
                                                          'importer': im.id,
                                                          'employer_cpf': line.employer_CPF,
							  'employee_cpf': line.CPF,
                                                          'total_cpf':line.total_CPF,
                                                          'latecomer_min':line.latecomer_min,
                                                          'UNPAID_DAY': line.UNPAID_DAY,
                                                          'timeoff_min':line.timeoff_min,})

                for input in input_type:
                    rule_code = 'result = inputs.%s.amount' % input.replace(' ', '_')
                    if input in less_type:
                        rule_code = 'result = -inputs.%s.amount' % input.replace(' ', '_')
                    if input in rule_list:
                        rule = self.pool.get('hr.salary.rule').search(cr, uid,
                                                                      [('code', '=', input.replace(' ', '_'))])
                        if rule:
                            self.pool.get('hr.salary.rule').write(
                                cr, uid, rule, {
                                    'condition_select': 'python',
                                    'amount_select': 'code',
                                    'condition_python': 'result = inputs.%s' % input.replace(' ', '_'),
                                    'amount_python_compute': rule_code,
                                }
                            )
                    if input not in rule_list:
                        rule = self.pool.get('hr.salary.rule').search(cr, uid,
                                                                      [('code', '=', input.replace(' ', '_'))])
                        if rule:
                            self.pool.get('hr.salary.rule').write(
                                cr, uid, rule, {
                                    'condition_select': 'python',
                                    'amount_select': 'code',
                                    'condition_python': 'result = inputs.%s' % input.replace(' ', '_'),
                                    'amount_python_compute': rule_code,
                                }
                            )
                            rule = rule[0]
                        else:
                            category_id = 1
                            addition_rule = self.pool.get('hr.salary.rule.category').search(cr, uid, [
                                ('name', '=', 'Addition')])
                            deduction_rule = self.pool.get('hr.salary.rule.category').search(cr, uid, [
                                ('name', '=', 'Deduction')])
                            if addition_rule:
                                category_id = addition_rule[0]
                            if input in less_type:
                                if deduction_rule:
                                    category_id = deduction_rule[0]
                            wage_type_id = 1
                            addition_wage_type = self.pool.get('cpf.wage.type').search(cr, uid, [
                                ('name', '=', 'Additional Wage')])
                            if addition_wage_type:
                                wage_type_id = addition_wage_type[0]
                            rule = self.pool.get('hr.salary.rule').create(cr, uid, {
                                'code': input.replace(' ', '_'),
                                'name': input,
                                'category_id': category_id,
                                'wage_type_id': wage_type_id,
                                'sequence': 'A%s' % input_type.index(input),
                                'irab_code': 'a_gross_salary',
                                'condition_select': 'python',
                                'amount_select': 'code',
                                'condition_python': 'result = inputs.%s' % input.replace(' ', '_'),
                                'amount_python_compute': rule_code,
                            }
                                                                          )
                        self.pool.get('hr.payroll.structure').write(cr, uid, contract.struct_id.id, {
                            'rule_ids': [(4, rule, _)]
                        })
                    input_line.create(cr,uid,{'payslip_id': payslip_id,
                                              'code': input.replace(' ', '_'),
                                               'name': '%s' % input,
                                               'sequence': input_type.index(input),
                                               'amount': getattr(line, input, 0),
                                               'contract_id': contract.id})

        self.write(cr,uid,ids,{'state': 'done'})

class payslip_import(models.Model):
    _name = 'hr.payslip.import.line'
    @api.onchange('employee_id')
    def _check_change(self):
        contract_ids = self.employee_id.contract_ids
        contract_obj = self.pool.get('hr.contract')
        if not contract_ids:
            contract_ids = contract_obj.search(self.env.cr,self.env.user.id,[('employee_ids', 'in', self.employee_id.id)], order='date_start desc')
            contract_ids = contract_obj.browse(self.env.cr, self.env.user.id, contract_ids)
        if contract_ids:
            contract = contract_ids[0]
            self.BASIC = contract.wage
        
    _columns = {
        'slip_id':fields.many2one('hr.payslip.import', 'Pay Slip', required=True, ondelete='cascade'),
        'employee_id':fields.many2one('hr.employee', 'Employee', required=True),
        'BASIC': fields.float('Basic', digits_compute=dp.get_precision('Payroll')),
        'OT': fields.float('Overtime', digits_compute=dp.get_precision('Payroll')),
        'NS_OTHER': fields.float('NS & Other', digits_compute=dp.get_precision('Payroll')),
        'UNPAID': fields.float('Unpaid leave', digits_compute=dp.get_precision('Payroll')),
        'UNPAID_DAY': fields.float('Unpaid leave (day)', digits_compute=dp.get_precision('Payrol')),
        'latecomer': fields.float('Late comer($)', digits_compute=dp.get_precision('Payroll')),
        'latecomer_min': fields.float('Late comer(mins)', digits_compute=dp.get_precision('Payrol')),
        'timeoff': fields.float('Timeoff($)', digits_compute=dp.get_precision('Payroll')),
        'timeoff_min': fields.float('Timeoff(mins)', digits_compute=dp.get_precision('Payrol')),
        'gross': fields.float('Gross Salary', digits_compute=dp.get_precision('Payroll')),
        'SDL': fields.float('SDL', digits_compute=dp.get_precision('Payroll')),
        'FWL': fields.float('FWL', digits_compute=dp.get_precision('Payroll')),
        'CPF': fields.float('CPF', digits_compute=dp.get_precision('Payroll')),
        '1st_half_salary': fields.float('First half salary', digits_compute=dp.get_precision('Payroll')),
        '2nd_half_salary': fields.float('Second half salary', digits_compute=dp.get_precision('Payroll')),
        'total_CPF': fields.float('Total CPF', digits_compute=dp.get_precision('Payroll')),
        'employer_CPF': fields.float('Employer CPF', digits_compute=dp.get_precision('Payroll')),
        'CDAC': fields.float('CDAC', digits_compute=dp.get_precision('Payroll')),
        'net_salary': fields.float('Net Salary', digits_compute=dp.get_precision('Payroll')),
    }

class hr_payslip(models.Model):
    _inherit = 'hr.payslip'
    _columns = {
        'importer': fields.many2one('hr.payslip.importer', 'Importer'),
        'employer_cpf': fields.float(string='Employer CPF Amount', help="This CPF amount should be submitted"),
        'employee_cpf': fields.float(string='Employee CPF Amount', help="This CPF amount should be submitted"),
        'total_cpf': fields.float(string="Total CPF", help="This CPF amount should be submitted"),
        'UNPAID_DAY': fields.float('Unpaid leave (day)', digits_compute=dp.get_precision('Payrol')),
        'latecomer_min': fields.float('Late comer(mins)', digits_compute=dp.get_precision('Payrol')),
        'timeoff_min': fields.float('Timeoff(mins)', digits_compute=dp.get_precision('Payrol')),
    }
    def compute_sheet(self, cr, uid, ids, context=None):
        slip_line_pool = self.pool.get('hr.payslip.line')
        sequence_obj = self.pool.get('ir.sequence')
        for payslip in self.browse(cr, uid, ids, context=context):
            number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
            #delete old payslip lines
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)
#            old_slipline_ids
            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)
            if payslip.contract_id:
                #set the list of contract for which the rules have to be applied
                contract_ids = [payslip.contract_id.id]
            else:
                #if we don't give the contract, then the rules to apply should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
            lines = [(0,0,line) for line in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)]
            self.write(cr, uid, [payslip.id], {'line_ids': lines, 'number': number,}, context=context)
        return True