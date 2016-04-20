# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import psycopg2
from openerp.osv import orm, fields
import xlrd
from base64 import b64decode
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
import math
import openerp.addons.decimal_precision as dp

import itertools
import csv

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from pytz import timezone
from tzlocal import get_localzone


class attendance_importer(osv.osv):
    _inherit = 'base_import.import'
    _name = 'attendance.importer'

    def row_is_empty(self, row=[]):
        for item in row:
            if item:
                return False
        return True

    def import_attendance(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            cr.execute('SAVEPOINT import')
            csv_reader = csv.reader(StringIO(b64decode(record.file)), delimiter=',', quotechar='"')
            user_tz = None
            if context.get('tz'):
                user_tz = timezone(context.get('tz'))
            tz = get_localzone()
            payslip_obj = self.pool.get('hr.payslip')
            # contract_obj = self.pool.get('hr.contract')
            # attendance_obj = self.pool.get('hr.payslip.worked_days')
            input_obj = self.pool.get('hr.payslip.input')
            employee_payslip = {}
            count = 0
            input_type = ['Basic Pay', 'Overtime_OT', 'MEAL', 'TRANSPORT', 'ROOM', 'MEDICAL', 'OTHER']
            column_map = {
                'Project': 0,
                'Period': 1,
                'Mode of payment': 2,
                'Employee': 3,
            }
            for input in input_type:
                column_map[input] = input_type.index(input) + 4

            for row in csv_reader:
                count += 1
                if count == 1:
                    for col in row:
                        if column_map.get(col):
                            column_map[col] = row.index(col)
                    continue
                # project_no = row[0]
                # employee_name = row[1]
                row_value = {}
                for input in column_map:
                    row_input_value = row[column_map[input]]
                    input_value = row_input_value
                    if input in input_type:
                        try:
                            input_value = float(row_input_value.replace('$',''))
                        except:
                            input_value = 0
                    row_value[input] = input_value

                project_no = row_value['Project']
                employee_name = row_value['Employee']
                mode_of_payment = row_value['Mode of payment']
                if not mode_of_payment:
                    mode_of_payment = 'cash'
                period = row_value['Period']

                employee_id = self.pool.get('hr.employee').search(cr, uid, [('name', 'ilike', employee_name)])
                if employee_id and len(employee_id) > 0:
                    employee_id = employee_id[0]
                else:
                    raise osv.except_osv(_('Error!'), _("No employee defined for name %s ") % (employee_name))
                if not employee_payslip.get(employee_id):
                    employee_payslip[employee_id] = {'payment_mode': mode_of_payment.lower(),
                                                     'period': period}
                if not employee_payslip[employee_id].get(project_no):
                    employee_payslip[employee_id][project_no] = {}
                for input in input_type:
                    if not employee_payslip[employee_id][project_no].get(input):
                        employee_payslip[employee_id][project_no][input] = 0
                    employee_payslip[employee_id][project_no][input] += row_value[input]
            for employee_id, projects in employee_payslip.items():
                employee = self.pool.get('hr.employee').browse(cr, uid, employee_id)
                period = projects.pop('period', '')
                mode_of_payment = projects.pop('payment_mode', 'cash')
                contract_ids = employee.contract_ids
                if contract_ids:
                    contract = contract_ids[0]
                    struct = contract.struct_id
                    rule_list = []
                    for rule in struct.rule_ids:
                        rule_list.append(rule.code)
                    for input in input_type:
                        if input in rule_list:
                            rule = self.pool.get('hr.salary.rule').search(cr, uid,
                                                                          [('code', '=', input.replace(' ', '_'))])
                            if rule:
                                self.pool.get('hr.salary.rule').write(
                                    cr, uid, rule, {
                                        'condition_select': 'python',
                                        'amount_select': 'code',
                                        'condition_python': 'result = inputs.%s' % input.replace(' ', '_'),
                                        'amount_python_compute': 'result = inputs.%s_SUM' % input.replace(' ', '_'),
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
                                        'amount_python_compute': 'result = inputs.%s_SUM' % input.replace(' ', '_'),
                                    }
                                )
                                rule = rule[0]
                            else:
                                category_id = 1
                                addition_rule = self.pool.get('hr.salary.rule.category').search(cr, uid, [
                                    ('name', '=', 'Addition')])
                                if addition_rule:
                                    category_id = addition_rule[0]
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
                                    'amount_python_compute': 'result = inputs.%s_SUM' % input.replace(' ', '_'),
                                }
                                                                              )
                            self.pool.get('hr.payroll.structure').write(cr, uid, struct.id, {
                                'rule_ids': [(4, rule, _)]
                            })
                    payslip_id = payslip_obj.create(cr, uid, {'employee_id': employee_id,
                                                              'contract_id': contract.id,
                                                              'payment_mode': mode_of_payment,
                                                              'struct_id': contract.struct_id.id})
                    if period:
                        date_from = period[:6]
                        date_to = period[-6:]
                        try:
                            date_from = datetime.strptime(date_from, '%d%m%y')
                            date_from = datetime.strftime(date_from, '%Y-%m-%d')
                            date_to = datetime.strptime(date_to, '%d%m%y')
                            date_to = datetime.strftime(date_to, '%Y-%m-%d')
                            payslip_obj.write(cr, uid, payslip_id, {'date_from': date_from, 'date_to': date_to})
                        except:
                            raise osv.except_osv(_('Error!'), _("The period input is not valid!"))

                    for project_no, item in projects.items():
                        for input in input_type:
                            if item[input]:
                                input_obj.create(cr, uid, {'payslip_id': payslip_id,
                                                           'project_no': project_no,
                                                           'code': input.replace(' ', '_'),
                                                           'name': '[%s]%s' % (project_no, input),
                                                           'sequence': input_type.index(input),
                                                           'amount': item[input],
                                                           'contract_id': contract.id})
                    payslip_obj.compute_sheet(cr, uid, [payslip_id], context=context)
                else:
                    raise osv.except_osv(_('Error!'),
                                         _("Please create contract for employee name %s ") % (employee_name))

            try:
                cr.execute('RELEASE SAVEPOINT import')
            except psycopg2.InternalError:
                pass
            self.write(cr, uid, ids, {'file': None})
        else:
            raise osv.except_osv(_('Error!'), _("Please input a file!"))
        return True


attendance_importer()
