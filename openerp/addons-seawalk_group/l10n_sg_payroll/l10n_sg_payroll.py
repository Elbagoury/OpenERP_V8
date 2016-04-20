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

from openerp.tools.translate import _
from itertools import groupby
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp.tools.safe_eval import safe_eval as eval
from openerp import SUPERUSER_ID


class hr_salary_rule_category(osv.osv):
    """
    HR Salary Rule Category
    """

    _inherit = 'hr.salary.rule.category'
    _columns = {
        'active': fields.boolean('Active'),
        #'print': fields.boolean('Print on Payslip?')
    }

    _defaults = {
        'active': True
    }

class res_company(osv.Model):
    _inherit = 'res.company'

    payday_value = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11),
                    (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20),
                    (21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30), (31, 31)]

    _columns = {
        'registration_number': fields.char('Business Registration Number', size=64, required=True, help='Business registration number for ACRA.'),
        #'cpf_number': fields.char('CPF Submission Number (CSN)', size=64, required=True, help='This is required for electronic submission of return to CPF Board.'),
        'iras_tax_number': fields.char('IRAS Tax Reference Number', size=64, required=True, help='This is required for electronic tax reporting to IRAS'),
        'payday': fields.selection(payday_value, 'When is the payday every month?', help=''),
        'next_payday': fields.selection([('next_day', 'Next Day'), ('previous_day', 'Previous Day')], 'If the payday falls on a non-working day, when is the salary payout?', help=''),
        'company_sector': fields.selection([('private', 'Private Sector'),
                                            ('statutory_body', 'Statutory Board'),
                                            ('aided_school', 'Government Department/Aided Schools'),
                                            ('ministries', 'Ministries and Defence'),
                                            ('other', 'Others')], 'Company Sector', help='This specifies whether company belongs to Public sector or Private.'),
        'business_nature': fields.char('Business Nature', size=64, translate=True),
        'establishment': fields.date('Business Established In Year'),
        'enable_esubmission': fields.selection([('yes', 'Yes'), ('no', 'No')], 'Do you have an account registered with CPF Board for e-Submission?'),
        'giro_pay': fields.boolean('Interbank GIRO'),
        'cheque_pay': fields.boolean('Cheque'),
        'cash_pay': fields.boolean('Cash'),
        'iras_approval': fields.boolean('Approval from IRAS'),
        'iras_approval_date': fields.date("IRAS approval date"),
        'nric_fin_passport_id':fields.char('NRIC / FIN / Passport Number', required=True, size=64, help='Enter the NRIC for Singaporean or Singaporean PR employees,'
                                  'Foreigh Identification Number(FIN) for employees work/employment pass, otherwise enter passport number.'),
        'org_id_type': fields.selection([
            ('7', 'UEN – Business Registration number issued by ACRA'),
            ('8', 'UEN – Local Company Registration number issued by ACRA'),
            ('A', 'ASGD – Tax Reference number assigned by IRAS'),
            ('I', 'ITR – Income Tax Reference number assigned by IRAS'),
            ('U', 'UENO – Unique Entity Number Others (e.g. Foreign Company Registration Number)')], 'Organization ID Type'),
        'org_id_no': fields.char('Organization ID No.', size=12),
    }

class company_sector_type(osv.Model):
    _name = 'company.sector.type'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'company_sector': fields.selection([
            ('private', 'Private'),
            ('non_pens_sbas', 'Non-Pensionable Employees (Statutory Bodies & Aided Schools)'),
            ('non_pens_min', 'Non-Pensionable Employees (Ministries)'),
            ('pen_sb', 'Pensionable Employees (Statutory Bodies)'),
            ('pen_min', 'Pensionable Employees (Ministries)'),
            ('non_pen_sbas_full', 'Non-Pensionable Employees (Statutory Bodies & Aided Schools) on full employer rates'),
            ('pen_sb_full', 'Pensionable Employees (Statutory Bodies) on full employer rates'),
            ('pri_full', 'Private Sector Employees on full employer rates')], 'Company Sector'),
        'description': fields.text('Description', translate=True),
    }

class DonationType(osv.Model):
    _name = 'donation.type'
    _columns = {
        'name': fields.char('Name', help='Trust/Donation Body name', required=True),
        'wage_start': fields.float("Wage Start"),
        'wage_end': fields.float("Wage End"),
        'python_code': fields.text('Python Code', required=True),
        'employee_donation_id': fields.many2one('employee.donation', 'Employee Donation'),
    }

class EmployeeDonation(osv.Model):
    _name = 'employee.donation'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'employee_ids': fields.many2many('hr.employee','donation_type_employee_rel', 'donation_type_id', 'emp_id', 'Employee'),
        'sequence': fields.integer("Sequence", required=True),
        'code': fields.char("Code", size=32, required=True),
        'duration': fields.selection([('once', 'Only Once'), ('month', 'Monthly'), ('year', 'Yearly')], "Duration"),
        'type': fields.selection([('percentage', 'Percentage'), ('fixed', 'Fixed')], 'Contribution Type'),
        'amount': fields.float('Contribution Amount'), #May be not needed, we get amount from python code itself
        'donation_rule_ids': fields.one2many("donation.type", 'employee_donation_id', 'Donation Rules'),
        'detail': fields.text('Details')
    }

class citizen_applicable(osv.Model):
    _name = 'citizen.applicable'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'citizenship': fields.selection([('singaporean', 'Singaporean'), ('singapore_pr', 'Singapore PR'), ('singapore_pr1', 'Singapore PR 1st Year'), ('singapore_pr2', 'Singapore PR 2nd Year'), ('singapore_pr3_and_on', 'Singapore PR 3rd Year and onwards'), ('singapore_pr1st_2nd_joint', 'Singapore PR 1st Year/2nd Year Joint'), ('foreigner', 'Foreigner')], 'Citizenship'),
        'description': fields.text('Description', translate=True),
    }

class hr_adress(osv.Model):
    _name = "hr.address"

    _columns = {
        'name': fields.char('Name', size=64),
        'address_type': fields.selection([('L', 'Local residential address'), ('F', 'Foreign address'), ('C', 'Local C/O address')], 'Address Type'),
        'block_no': fields.char('Block No.', size=32),
        'street': fields.char('Street name', size=64),
        'level_no': fields.char('Level No.', size=16), #optional, we can remove it
        'unit_no': fields.char('Unit No.', size=16), #optional, we can remove it
        'postal_code': fields.char('Postal code', size=16),
        'line1': fields.char('Line 1', size=32),
        'line2': fields.char('Line 2', size=32),
        'line3': fields.char('Line 3', size=32),
        'postal_code_unformatted': fields.char('Postal code unformatted'), #Postal code we can use it here
        'country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
    }

    _defaults = {
        'address_type': 'L'
    }

class hr_employee(osv.Model):
    _inherit = 'hr.employee'

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_latest_contract(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        obj_contract = self.pool.get('hr.contract')
        for emp in self.browse(cr, uid, ids, context=context):
            contract_ids = obj_contract.search(cr, uid, [('employee_ids','in',[emp.id]),], order='date_start', context=context)
            if contract_ids:
                res[emp.id] = contract_ids[-1:][0]
            else:
                res[emp.id] = False
        return res

    def _cpf_count(self, cr, uid, ids, field_name, arg, context=None):
        Cpf = self.pool['cpf.submission']
        return {
            employee_id: Cpf.search_count(cr,uid, [('employee_ids', 'in', employee_id)], context=context)
            for employee_id in ids
        }

    def _income_tax_count(self, cr, uid, ids, field_name, arg, context=None):
        IncomeTaxDetail = self.pool['income.tax.detail']
        return {
            employee_id: IncomeTaxDetail.search_count(cr, SUPERUSER_ID, [('employee_id', '=', employee_id)], context=context)
            for employee_id in ids
        }

    _columns = {
        'name_related': fields.related('resource_id', 'name', type='char', string='Name', readonly=True, store=True, help='Exact Name per NRIC / Passport'),
        'nric_fin_passport_id':fields.char('NRIC / FIN / Passport Number', required=True, size=64, help='Enter the NRIC for Singaporean or Singaporean PR employees,'
                                  'Foreigh Identification Number(FIN) for employees work/employment pass, otherwise enter passport number.'),
        'gender': fields.selection([('male', 'Male'),('female', 'Female')], 'Gender', required=True,),
        'birthday': fields.date("Date of Birth", required=True),
        'citizenship': fields.selection([('singaporean', 'Singaporean'), ('singapore_pr', 'Singapore PR'), ('foreigner', 'Foreigner')], 'Citizenship', required=True),
        'is_pensionable': fields.boolean('Pensionable or Not pensionable'),
        'employee_type': fields.selection([('pensionable', 'Pensionable'),
                                            ('non_pensionable', 'Non Pensionable'),
                                            ('bonuspmt', 'Bonus pmt'),
                                            ('contract', 'Contract svc men'),
                                            ('saver', 'Saver plan')], 'Employee Type', required=True),
        'country_id': fields.many2one('res.country', 'Country of Origin', required=True),
        'pr_startdate': fields.date('Singapore PR Start Date (dd/MMM/yyyy)'),
        'work_pass_information': fields.selection([('s_pass', 'S Pass'),('e_pass', 'E Pass'),('work_permit', 'Work Permit')], 'Worker’s Qualifications & Permit / Pass Information', ),
        'permit_ids': fields.one2many('permit.permit', 'employee_id', 'Permit Details'),
        'religion_id': fields.many2one('res.religion', 'Religion'),
        #Mobile field already there in hr.employee
        'employee_code': fields.char('Employee Code', size=64, required=True),
        'mobile': fields.char('Mobile', size=32,),
        'ethnic_race': fields.many2one('ethnic.race', 'Ethnic Race'),
        'mbmf': fields.boolean('Contribution for MBMF', help='Please Un-tick if not contributing'),
        'sinda': fields.boolean('Contribution for SINDA', help='Please Un-tick if not contributing'),
        'sdl': fields.boolean('Contribution for SDL', help='Please Un-tick if not contributing'),
        'other_address_id': fields.many2one('res.partner', 'Other Address', help='Overseas or Alternative address of the employee'),
        'status': fields.selection([('confirmed','Confirmed'), ('probation', ' New Joiner'), ('resigned', 'Resigned'), ('join_leave_same_month', 'Join & Leave in month')], 'Status', help='Present employee status'), #TODO: add types [('E', 'Exisitng Employee leave and join in same month'), ('L', 'Leaver'), ('N', 'New Joiner', ('O', 'Employee join and leave in same month'))]
        'ir8a_submission': fields.boolean('Exclude employee from IR8A eSubmission'),
        'cpf_detail_ids': fields.one2many('employee.cpf.detail', 'employee_id', 'CPF Contribution Details'),
        'spr_1and2_joint': fields.boolean('Ready to contribute at full employer and employee rates ?', help='SPR in the 1st and 2nd year of obtaining SPR status but who has jointly applied with employer to contribute at full employer and employee rates. It will be applied only if employee is having the Singapore PR citizenship.'),
        'company_sector': fields.related('company_id', 'company_sector', type='char', string='Company Sector'),
        'emergency_address_id': fields.many2one('res.partner', 'Emergency Address'),
        #Changed the logic of _get_latest_contract as we convert employee_id as employee_ids many2many in hr.cotact
        'contract_id':fields.function(_get_latest_contract, string='Contract', type='many2one', relation="hr.contract", help='Latest contract of the employee'),
        #Employee donation fields
        'is_mbmf': fields.boolean("MBMF"),
        'mbmf_duration': fields.selection([('once', 'Only Once'), ('month', 'Monthly'), ('year', 'Yearly')], "Duration"),
        'mbmf_type': fields.selection([('percentage', 'Percentage'), ('fixed', 'Fixed')], 'Type'),
        'mbmf_amount': fields.float('MBMF Amount'),
        'is_sinda': fields.boolean("SINDA"),
        'sinda_duration': fields.selection([('once', 'Only Once'),('month', 'Monthly'), ('year', 'Yearly')], "Duration"),
        'sinda_type': fields.selection([('percentage', 'Percentage'), ('fixed', 'Fixed')], 'Type'),
        'sinda_amount': fields.float('SINDA Amount'),
        'is_cdac': fields.boolean("CDAC"),
        'cdac_duration': fields.selection([('once', 'Only Once'),('month', 'Monthly'), ('year', 'Yearly')], "Duration"),
        'cdac_type': fields.selection([('percentage', 'Percentage'), ('fixed', 'Fixed')], 'Type'),
        'cdac_amount': fields.float('CDAC Amount'),
        'is_ecf': fields.boolean("ECF"),
        'ecf_duration': fields.selection([('once', 'Only Once'),('month', 'Monthly'), ('year', 'Yearly')], "Duration"),
        'ecf_type': fields.selection([('percentage', 'Percentage'), ('fixed', 'Fixed')], 'Type'),
        'ecf_amount': fields.float('ECF Amount'),
        'local_address_id': fields.many2one('hr.address', 'Local Residency Address'),
        'co_address_id': fields.many2one('hr.address', 'Local C/O Address'),
        'foreign_address_id': fields.many2one('hr.address', 'Foreign Address'),

        #donation master
        'donation_ids': fields.many2many('employee.donation', 'donation_type_employee_rel', 'emp_id', 'donation_type_id', 'Contribution'),

        'job_start': fields.date('Trial Start Date'),
        'job_end': fields.date('Trail End Date'),
        'confirm_date': fields.date('Employment Start Date'),
        'emp_end': fields.date('Employment End Date'),

        'cpf_count': fields.function(_cpf_count, type='integer', string='CPF Submission'),
        'income_tax_ids': fields.one2many('income.tax.detail', 'employee_id', 'Income Tax Details'),
        'income_tax_count': fields.function(_income_tax_count, type='integer', string='Contracts'),
    }


    def _default_company_sector(self, cr, uid, context=None):
        if context is None: context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_sector = user.company_id.company_sector
        return company_sector

    _defaults = {
        'citizenship': 'singaporean',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'hr.employee', context=c),
        'birthday': fields.date.context_today,
    }
    def _check_unique_code(self, cr, uid, ids, context=None):
        return True

    def get_employee_donation(self, cr, uid, ids, code=False, context=None):
        employee_record = self.browse(cr, uid, ids[0], context=context)
        if not employee_record.contract_id:
            except_orm(_("Warning"), _("Please select contract for employee"))
        code_donation = False
        selected_rule = False
        localdict = {'result': None, 'employee': employee_record, 'contract': employee_record.contract_id}
        for donation in employee_record.donation_ids:
            if donation.code == code:
                code_donation = donation
                break
        if code_donation:
            for rule in code_donation.donation_rule_ids:
                if employee_record.contract_id.wage >= rule.wage_start and employee_record.contract_id.wage <= rule.wage_end:
                    selected_rule = rule
                    break
        if selected_rule:
            eval(selected_rule.python_code, localdict, mode='exec', nocopy=True)
        return localdict['result'] or 0.0

    _constraints = [
            (_check_unique_code, 'Error! You cannot create duplicate code for Employee(s).', ['employee_code']),
    ]

class assesment_year(osv.Model):
    _name = 'assesment.year'

    _rec_name = 'assessment_year_value'

    _columns = {
        'name': fields.char('Assesment Year', required=True),
        'assessment_year_value': fields.integer('Assessment Year in Format YYYY', required=True),
        'code': fields.char('Code', size=6, required=True),
        #'company_id': fields.many2one('res.company', 'Company', required=True),
        'date_start': fields.date('Start Date', required=True),
        'date_stop': fields.date('End Date', required=True),
        #'period_ids': fields.one2many('account.period', 'fiscalyear_id', 'Periods'),
        #'state': fields.selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False),
        #'end_journal_period_id': fields.many2one(
        #     'account.journal.period', 'End of Year Entries Journal',
        #     readonly=True, copy=False),
    }

class permit_permit(osv.Model):
    _name = 'permit.permit'

    _columns = {
        'name': fields.selection([('passport', 'Passport'),
                                  ('voter', 'Voter ID'),
                                  ('drive', 'Driving Licence'),
                                  ('pan', 'Pan Card'),
                                  ('work', 'Work Permit'),
                                  ('nric', 'NRIC'),
                                  ('fin', 'FIN'),
                                  ('immref', 'Immigration File Ref No.'),
                                  ('malayic', 'Malaysian I/C (for non-resident director and seaman only)')], 'ID Name'),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        #'type': fields.many2one(''), #m2o with what ?
        'id_number': fields.char('Identification Number', size=64, required=True),
        'permit_startdate': fields.date('Permit/Pass Start Date'),
        'permit_enddate': fields.date('Permit/Pass Expiry Date'),
        'attachment_id': fields.binary('Document Copy'),
        'doc_name': fields.char('Document name')
    }

class res_religion(osv.Model):
    _name = 'res.religion'

    _columns = {
        'name': fields.char('Religion Name', size=64, translate=True),
    }

class ethnic_race(osv.Model):
    _name = 'ethnic.race'

    _columns = {
        'name': fields.char('Name', size=64, translate=True),
    }
class HrContract(osv.Model):
    _inherit = 'hr.contract'

    def _get_employee(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for emp in self.browse(cr, uid, ids, context=context):
            if emp.employee_ids:
                result[emp.id] = emp.employee_ids[0].id
        return result

    _columns = {
        #'wage': fields.float('Basic Salary', digits=(16,2), required=True, help="Basic Salary of the employee"),
        #'employee_id': fields.many2one('hr.employee', "Employee"),
        'overtime_applicable': fields.boolean('Overtime Pay Applicable'),
        'payment_mode': fields.selection([('cash', 'Cash')], 'Payment Mode', help=''),
        'employee_ids': fields.many2many('hr.employee', 'hr_contract_employee_rel', 'contract_id', 'employee_id', 'Employees'),
        'date_start': fields.date('Start Date', required=False),
        'employee_id': fields.function(_get_employee, type='many2one', relation='hr.employee', string='Employee', store=True),
    }

    def _check_one_contract(self, cr, uid, ids, context=None):
        employees = []
        for contract in self.browse(cr, uid, ids, context=context):
            for emp in contract.employee_ids:
                employees.append(emp.id)
        if employees:
            for employee in employees:
                contract_ids = self.search(cr, uid, [('employee_ids', 'in', employees)], context=context)
                if len(contract_ids) > 1:
                    return False
        return True


    _constraints = [
        (_check_one_contract, 'Error!, You cannot have two contract for employee', ['employee_ids']),
    ]

class cpf_wage_type(osv.Model):
    _name = 'cpf.wage.type'
    _columns = {
        'name': fields.char('Name', required=True, translate=True),
        'code': fields.char('Code', size=8, required=True),
        'description': fields.text('Description', translate=True),
    }

irab_code = [("a_gross_salary", "A-Gross Salary"),
                 ("b_bonus", "B-Bonus"),
                 ("c_director_fees", "C-Director's Fees"),
                 ("d11", "D11 - Transport"),
                 ("d12", "D12 - Entertainment"),
                 ("d13", "D13 - Other Allowances"),
                 ("d2", "D2 - Gross Commission"),
                 ("d3", "D3 - Pension"),
                 ("d41", "D41 - Gratuity"),
                 ("d42", "D42 - Notice Pay"),
                 ("d43", "D43 - Ex-Gratia"),
                 ("d44", "D44 - Other Lump Sum"),
                 ("d45", "D45 - Compensation"),
                 ("d51", "D51 - Retirement Benefits accrued up to 31 December 1992"),
                 ("d52", "D52 - Retirement Benefits accrued from 1993"),
                 ("d6", "D6 - Employer Overseas Pension / Provident Fund"),
                 ("d7", "D7 - Employer Excess / Voluntary CPF"),
                 ("d8", "D8 - Gains / Profits from Employee ESOP / ESOW Plans"),
                 ("d9", "D9 - Value of Benefits-In-Kind"),
                 ("e2", "E2 - Employee CPF / Pension / Fund"),
                 ("e3", "E3 - Donations"),
                 ("e4", "E4- Insurance Premium"),
                 ("e5", "E5 - MBF Donation"),
                 ("na", "NA - Not Applicable"),
                 ("iestr", "Income Exempt/Subject to Tax Remission")]

class hr_salary_rule(osv.Model):
    _inherit = 'hr.salary.rule'
    _order = 'sequence'

    _columns = {
        'cpf_applicability': fields.selection([('ordinary_wages','Ordinary Wages'), ('additional_wages', 'Additional Wages'), ('no_cpf', 'No CPF')], 'CPF Applicability & Type'),
        'irab_code': fields.selection(irab_code, 'IR8A Code', required=True),
        'wage_type_id': fields.many2one('cpf.wage.type', 'Wage Type', required=True),
        'employee_donation_id': fields.many2one('employee.donation', 'Donation Contribution'),
        'sequence': fields.char('Sequence', size=64),
        'python_input_name': fields.char('Input Name', size=64),
    }

    _defaults = {
        'sequence': 'X'
    }


    def compute_rule(self, cr, uid, rule_id, localdict, context=None):
        """
        :param rule_id: id of rule to compute
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float, float)
        """
        rule = self.browse(cr, uid, rule_id, context=context)
        if rule.amount_select == 'fix':
            try:
                #return rule.amount_fix, float(eval(rule.quantity, localdict)), 100.0
                return rule.amount_fix, float(eval(rule.quantity, localdict)), 100.0, rule.name
            except:
                raise osv.except_osv(_('Error!'), _('Wrong quantity defined for salary rule %s (%s).')% (rule.name, rule.code))
        elif rule.amount_select == 'percentage':
            try:
                return (float(eval(rule.amount_percentage_base, localdict)),
                        float(eval(rule.quantity, localdict)),
                        rule.amount_percentage, rule.name)
            except:
                raise osv.except_osv(_('Error!'), _('Wrong percentage base or quantity defined for salary rule %s (%s).')% (rule.name, rule.code))
        else:
            try:
                eval(rule.amount_python_compute, localdict, mode='exec', nocopy=True)
                if rule.python_input_name:
                    eval(rule.python_input_name, localdict, mode='exec', nocopy=True)
                #return float(localdict['result']), 'result_qty' in localdict and localdict['result_qty'] or 1.0, 'result_rate' in localdict and localdict['result_rate'] or 100.0
                return float(localdict['result']), 'result_qty' in localdict and localdict['result_qty'] or 1.0, 'result_rate' in localdict and localdict['result_rate'] or 100.0, ((rule.python_input_name and 'result_name' in localdict and localdict['result_name']) or rule.name)
            except:
                raise osv.except_osv(_('Error!'), _('Wrong python code defined for salary rule %s (%s). Check python code for either Salary rule or Input name')% (rule.name, rule.code))

class hr_payslip_line(osv.osv):
    '''
    Payslip Line
    '''

    _inherit = 'hr.payslip.line'

    _columns = {
        'sequence': fields.char('Sequence', size=64),
        'wage_code': fields.related('salary_rule_id', 'wage_type_id', 'code', type='char', string='Wage Type'),
        'employee_donation_id': fields.related('salary_rule_id', 'employee_donation_id', relation='employee.donation', type='many2one', store=True, string='Wage Type'), #Should be store = dict
        'irab_code': fields.related('salary_rule_id', 'irab_code', type="selection", selection=irab_code),
    }

class hr_payslip(osv.Model):
    _inherit = "hr.payslip"




    def sale_layout_lines(self, cr, uid, ids, order_id=None, context=None):
        """
        Returns order lines from a specified sale ordered by
        sale_layout_category sequence. Used in sale_layout module.

        :Parameters:
            -'order_id' (int): specify the concerned sale order.
        """
        ordered_lines = self.browse(cr, uid, order_id, context=context).line_ids
        sortkey = lambda x: x.category_id if x.category_id else ''
        return self.grouplines(cr, uid, ordered_lines, sortkey)

    def grouplines(self, cr, uid, ordered_lines, sortkey):
        grouped_lines = []
        for key, valuesiter in groupby(ordered_lines, sortkey):
            if not key.active:
                continue
            group = {}
            group['category'] = key
            group['lines'] = list(v for v in valuesiter)
            grouped_lines.append(group)
        return grouped_lines

    employee_employer_contribution_both = False

    def employee_employer_cpf_employee(self, cr, uid, ids, context=None):
        if context is None: context = {}
        result = {}
        rule_line_obj = self.pool.get('age.rule.line')
        contract_obj = self.pool.get('hr.contract')

        wage_types_dict = {}
        rules = {}

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0


        for payslip in self.browse(cr, uid, ids, context=context):
            employee = self.pool.get('hr.employee').browse(cr, uid, payslip.employee_id.id, context=context)
            contract_ids = contract_obj.search(cr, uid, [('employee_ids', 'in', [employee.id])])
            #TO ASK: What if employee do not have contract, so wage is going to be 0, there can more than one contract for employee
            if not contract_ids:
                raise osv.except_osv(_("Warning"), _("Please define contract for the employee."))
            contract = contract_obj.browse(cr, uid, contract_ids[0],  context=context)
            wage_types_obj = self.calculate_wage_obj(cr, uid, ids, contract_ids, payslip.id, context=context)
            rules_obj = BrowsableObject(self.pool, cr, uid, employee.id, rules)
            localdict = {'wage_types':wage_types_obj, 'rules': rules_obj, 'employee': employee, 'contract': contract}
            result[payslip.id] = {'employee_cpf': 0.0, 'employer_cpf': 0.0, 'total_cpf': 0.0}
            wage = contract.wage
            age = self.calc_age(datetime.strptime(employee.birthday, "%Y-%m-%d").date())
            cpf_rule_id = self.get_cpf_register(cr, uid, [employee.id], context=context)
#             if not cpf_rule_id:
#                 raise osv.except_osv(_('Warning!'),
#                             _('Employee %s does not fall into any CPF register!!!' % employee.name))

            if cpf_rule_id:
                line_ids = rule_line_obj.search(cr, uid, [('cpf_rule_id', '=', cpf_rule_id),
                                               ('age_start', '<', age),
                                               ('age_end', '>=', age),
                                               ('wage_start', '<', wage),
                                               ('wage_end', '>=', wage)])
                print "\n\nline_ids is ::: ", line_ids
                if line_ids:
                    employer_cpf = 0
                    employee_cpf = 0
                    lines = rule_line_obj.browse(cr, uid, line_ids, context=context)
                    for line in lines:
                        print "\n\nline.rule is :::  ", line
                        localdict['result'] = None
                        try:
                            eval(line.employer_python_code, localdict, mode='exec', nocopy=True)
                            employer_cpf += localdict['result'] or 0.0
                            localdict['result'] = None
                            eval(line.employee_python_code, localdict, mode='exec', nocopy=True)
                            employee_cpf += localdict['result'] or 0.0
                        except Exception, e:
                            raise osv.except_osv(_('Error!'), _('Wrong python code defined for salary rule.'))

                    #If employee has spr1_and2_joint boolean true then employee will pay both contribution, employer not pay anything
                    if self.employee_employer_contribution_both:
                        employee_cpf += employer_cpf
                        employer_cpf = 0

                    result[payslip.id].update({
                        'employee_cpf': employee_cpf,
                        'employer_cpf': employer_cpf,
                        'total_cpf': employee_cpf + employer_cpf
                    })
        return result

    def _employee_employer_cpf_employee(self, cr, uid, ids, fields, arg, context=None):
        """
        This method will call employee_employer_cpf_employee
        employee_employer_cpf_employee will return three value, employee CPF contribution, employer CPF contribution and total contribution
        Result we will apply to in this function result[id][employer_cpf] = employer_cpf.....
        """
        result = self.employee_employer_cpf_employee(cr, uid, ids, context=context)
        return result

    _columns = {
        'employer_cpf': fields.function(_employee_employer_cpf_employee, type='float', string='Employer CPF Amount', multi="contribution", help="This CPF amount should be submitted"),
        'employee_cpf': fields.function(_employee_employer_cpf_employee, type='float', string='Employee CPF Amount', multi="contribution", help="This CPF amount should be submitted"),
        'total_cpf': fields.function(_employee_employer_cpf_employee, type='float', string="Total CPF", multi="contribution", help="This CPF amount should be submitted"),
        'input_donation_ids': fields.one2many('employee.donation.input', 'payslip_id', 'Donations', required=False, readonly=True, states={'draft': [('readonly', False)]}),
    }

    def get_donations(self, cr, uid, employee_id, contract_ids, context=None):
        res = []
        contract_obj = self.pool.get('hr.contract')
        employee_obj = self.pool['hr.employee']
        employee = employee_obj.browse(cr, uid, employee_id, context=context)
        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            for donation in employee.donation_ids:
                contribution = employee.get_employee_donation(code=donation.code)
                inputs = {
                     'name': "Contributing towards " + donation.name,
                     'code': donation.code,
                     'amount': contribution,
                     'contract_id': contract.id,
                }
                res += [inputs]
        return res

    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        if context is None: context = {}
        input_donation_ids = []
        res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id=employee_id, contract_id=contract_id, context=context)
        print 'f res::>>>', res
        if res['value'].get('contract_id'):
            contract_ids = [res['value']['contract_id']]
            input_donation_ids = self.get_donations(cr, uid, employee_id, contract_ids, context=context)
        res['value'].update({
            'input_donation_ids': input_donation_ids,
        })
        print 'res>>>>>>>>>>>>', res
        return res

    def get_contract(self, cr, uid, employee, date_from, date_to, context=None):
        """
        @param employee: browse record of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        contract_obj = self.pool.get('hr.contract')
        clause = []
        #a contract is valid if it ends between the given dates
        clause_1 = ['&',('date_end', '<=', date_to),('date_end','>=', date_from)]
        #OR if it starts between the given dates
        clause_2 = ['&',('date_start', '<=', date_to),('date_start','>=', date_from)]
        #OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&',('date_start','<=', date_from),'|',('date_end', '=', False),('date_end','>=', date_to)]
        #clause_final =  [('employee_id', '=', employee.id),'|','|'] + clause_1 + clause_2 + clause_3
        clause_final =  [('employee_ids', 'in', [employee.id]),'|','|'] + clause_1 + clause_2 + clause_3
        contract_ids = contract_obj.search(cr, uid, clause_final, context=context)
        return contract_ids

    def calculate_wage_obj(self, cr, uid, ids, contract_ids, payslip_id, context=None):
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
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line

        #added
        wage_types_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, wage_types_dict)
        categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
        worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
        payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)

        obj_employee = self.pool.get('hr.employee')

        localdict = {'wage_types':wage_types_obj, 'categories': categories_obj, 'rules': rules_obj, 'payslip': payslip_obj, 'worked_days': worked_days_obj, 'inputs': input_obj}
        #get the ids of the structures on the contracts and their parent id as well
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        #get the rules of the structure and thier children
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        #Remove NP CPF type rules
        wage_type_ids = self.pool.get('cpf.wage.type').search(cr, uid, [('code', '=', 'NA')], context=context)
        na_salary_rule_ids = self.pool.get('hr.salary.rule').search(cr, uid, [('wage_type_id', 'in', wage_type_ids)])
        sorted_rule_ids = list(set(sorted_rule_ids) - set(na_salary_rule_ids))

        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict.update({'employee': employee, 'contract': contract})
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty, rate, rule_name = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0 or 0.0
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    localdict = _sum_salary_rule_wage_type(localdict, rule.wage_type_id, tot_rule - previous_amount)
        return localdict['wage_types']

    def calc_age(self, joining_date):
        '''
        joining_date: datetime.date() value
        '''
        today = date.today()
        try:
            age = joining_date.replace(year=today.year)
            difference_in_years = relativedelta(today, joining_date).years
            difference_in_months = relativedelta(today, joining_date).months
            difference_in_years = float(difference_in_years) + float("0." + str((100 * difference_in_months)/12))
            difference_in_days = relativedelta(today, joining_date).days
            #year_days = calendar.isleap() #TODO: Consider leap year scenario
            difference_in_years = float(difference_in_years) + float("0." + str(((100 * difference_in_days)/365)))
            print "\n\ndifference_in_years is ::: ", difference_in_years
        except ValueError: # raised when birth date is February 29 and the current year is not a leap year
            age = joining_date.replace(year=today.year, day=joining_date.day-1)
            difference_in_years = relativedelta(today, joining_date).years
            difference_in_months = relativedelta(today, joining_date).months
            difference_in_years = float(difference_in_years) + float("0." + str((100 * difference_in_months)/12))
            difference_in_days = relativedelta(today, joining_date).days
            #year_days = calendar.isleap() #TODO: Consider leap year scenario
            difference_in_years = float(difference_in_years) + float("0." + str(((100 * difference_in_days)/365)))
            print "\n\ndifference_in_years is ::: ", difference_in_years
        return difference_in_years
#         if age > today:
#             return today.year - joining_date.year - 1
#         else:
#             return today.year - joining_date.year

    def get_cpf_register(self, cr, uid, ids, context=None):
        cpf_register_rule_obj = self.pool.get('cpf.rule')
        citizen_applicable_obj = self.pool.get('citizen.applicable')
        sector_type_obj = self.pool.get('company.sector.type')
        employee = self.pool.get('hr.employee').browse(cr, uid, ids[0], context=context)

        citizenship = employee.citizenship
        citizenship_ids = []

        def get_full_rate_value(employee, company):
            full_rate_string = ''
            company_sector_mapping = {'private': 'pri', 'statutory_body': '', 'aided_school': ''}
            is_pensionable = company.company_sector != 'private' and (employee.is_pensionable and 'pen_' or 'non_pen_') or ''
            full_rate_string += is_pensionable
            if company.company_sector in ['statutory_body', 'aided_school']:
                full_rate_string += 'sbas'
            if company.company_sector == 'statutory_body':
                full_rate_string += 'sb'
            if company.company_sector == 'private':
                full_rate_string += 'pri'
            full_rate_string += "_full"
            return full_rate_string

        if citizenship == "singapore_pr":
            pr_startdate = datetime.strptime(employee.pr_startdate, DF)
            now_date = datetime.strptime(datetime.now().strftime(DF), DF)
            difference_date = now_date - pr_startdate
            difference_days = difference_date.days
            if employee.spr_1and2_joint: #/XMLID: citizenship_singaporean_pr1st_2nd, company_sector_non_pen_sbas_full, company_sector_pen_sb_full, company_sector_pri_full
                if difference_days <= 730: #ciitizenship ifeld: singapore_pr1st_2nd_joint, non_pen_sbas_full, pen_sb_full, pri_full
                    citizenship += "1st_2nd_joint"
                    self.employee_employer_contribution_both = True
                    self.full_rate = get_full_rate_value(employee, employee.company_id)
                    print "\n\nfull_rate is ::: ", self.full_rate
            else:
                #TO ASK: What about leap year
                if difference_days > 0 and difference_days <= 365:
                    citizenship += "1"
                elif difference_days > 365 and difference_days <= 730:
                    citizenship += "2"
                elif difference_days > 730:
                    citizenship += "3_and_on"
        ca_ids = citizen_applicable_obj.search(cr, uid, [('citizenship', '=', citizenship)], context=context)
        for citizen in citizen_applicable_obj.read(cr, uid, ca_ids, ['citizenship'], context=context):
            citizenship_ids.append(citizen['id'])

        is_pens = employee.is_pensionable
        sector = is_pens and 'pensionable' or 'non_pensionable'
        # Private Employees? if private sector then no need to check pentionable
        company_sector_mapping = {'private': 'private',
            'pensionable_private': 'private',
            'non_pensionable_private': 'private',
            'non_pensionable_statutory_body': 'non_pens_sbas',
            'non_pensionable_ministries': 'non_pens_min',
            'pensionable_statutory_body': 'pen_sb',
            'pensionable_ministries': 'pen_min',
            'pri_full': 'pri_full',
            'pen_sb_full': 'pen_sb_full',
            'non_pen_sbas_full': 'non_pen_sbas_full'
        }
        if not employee.company_id.company_sector:
            raise osv.except_osv(_('Error!'), _('You must configure sector in company configuration.'))

        if self.employee_employer_contribution_both:
            sector = self.full_rate
        else:
            sector = sector + '_' + employee.company_id.company_sector
        company_sector = company_sector_mapping.get(sector)
        sector_ids = sector_type_obj.search(cr, uid, [('company_sector', '=', company_sector)], context=context)
        #TODO: Here sector_ids will be comapny sector + employee pensionable or not
        all_registers = cpf_register_rule_obj.search(cr, uid, [('sector_ids', 'in', sector_ids), ('applicable_ids', 'in', citizenship_ids)], context=context)

        #remove following identify logic and added a domain in cpf_register search
        cpf_rule = all_registers and all_registers[0]

        return cpf_rule

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
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line
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

    #Report utility methods
    def get_addition_lines(self, cr, uid, ids, context=None):
        category_ids = []
        if isinstance(ids, int):
            ids = [ids]
        payslip_line_obj = self.pool.get('hr.payslip.line')
        addition_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'hr_payroll.ALW')
        overtime_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'l10n_sg_payroll.overtime')
        reimbursement_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'l10n_sg_payroll.reimbursement')
        basic_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'hr_payroll.BASIC')
        #gross_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'hr_payroll.GROSS')
        category_ids += [addition_id, overtime_id, reimbursement_id, basic_id]
        #TO ASK: Should NET, Company Contribution, be considered in addition lines ?
        #TODO: May be Use child of as category_id can be child of some other category
        payslip_line_ids = payslip_line_obj.search(cr, uid, [('slip_id', 'in', ids), ('category_id', 'in', category_ids)])
        payslip_records = payslip_line_obj.browse(cr, uid, payslip_line_ids)
        return payslip_records

    def total_pay_lines(self, cr, uid, ids, type, context=None):
        if isinstance(ids, int):
            ids = [ids]
        lines = []
        if type == 'add':
            lines = self.get_addition_lines(cr, uid, ids, context=context)
        if type == 'ded':
            lines = self.get_deduction_lines(cr, uid, ids, context=context)
        amount = 0.0
        for line in lines:
            amount += line.total
        return amount

    def get_net_salary(self, cr, uid, ids, context=None):
        category_ids = []
        if isinstance(ids, int):
            ids = [ids]
        payslip_line_obj = self.pool.get('hr.payslip.line')
        net_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'hr_payroll.NET')
        payslip_line_ids = payslip_line_obj.search(cr, uid, [('slip_id', 'in', ids), ('category_id', '=', net_id)])
        net_lines = payslip_line_obj.browse(cr, uid, payslip_line_ids)
        net = 0.0
        for n in net_lines:
            net += n.total
        return net

    def get_deduction_lines(self, cr, uid, ids, context=None):
        category_ids = []
        if isinstance(ids, int):
            ids = [ids]
        payslip_line_obj = self.pool.get('hr.payslip.line')
        deduction_id = self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'hr_payroll.DED')
        #TO ASK: What else can come in deduction
        #TODO: May be Use child of as category_id can be child of some other category
        category_ids += [deduction_id]
        payslip_line_ids = payslip_line_obj.search(cr, uid, [('slip_id', 'in', ids), ('category_id', 'in', category_ids)])
        return payslip_line_obj.browse(cr, uid, payslip_line_ids)

    def get_employee_basic(self, cr, uid, ids, context=None):
        id = ids
        if isinstance(ids, int):
            id = ids[0]
        payslip_line_obj = self.pool.get('hr.payslip.line')
        #We can fetch BASIC by search for xmlid of rule for Basic
        payslip_lines = payslip_line_obj.search_read(cr, uid, [('slip_id', '=', id), ('code', '=', 'BASIC')], ['amount', 'total'])
        if payslip_lines:
            return payslip_lines[0].get('total')
        return 0.0

    def to_date_wage(self, cr, uid, ids, type, context=None):
        # type can either be OW or AW
        Payslip = self.pool['hr.payslip']
        PayslipLine = self.pool.get('hr.payslip.line')
        total_wage = 0.0

        payslip = self.browse(cr, uid, ids, context=context)[0]
        year = datetime.strptime(payslip.date_from, DF).strftime('%Y')

        # all the payslips which are created
        pay_ids = Payslip.search(cr, uid, [('employee_id', '=', payslip.employee_id.id)], context=context)
        for slip in self.browse(cr, uid, pay_ids, context=context):
            slip_year = datetime.strptime(slip.date_from, DF).strftime('%Y')
            # compate year because we want info of same year, and need data of all the previous payslips created in this year
            if year == slip_year and datetime.strptime(slip.date_from, DF) <= datetime.strptime(payslip.date_from, DF):
                payslip_lines = PayslipLine.search_read(cr, uid, [
                    ('category_id.code', '=', 'ALW'),
                    ('slip_id.state', '=', 'done'),
                    ('slip_id', '=', slip.id),
                    ('wage_code', '=', type)], ['amount', 'total'])
                for pay in payslip_lines:
                    total_wage += pay['total']
        return total_wage

    def to_date_cpf(self, cr, uid, ids, type, context=None):
        # type can either be employee or employer
        Payslip = self.pool['hr.payslip']
        PayslipLine = self.pool.get('hr.payslip.line')
        total_cpf = 0.0

        payslip = self.browse(cr, uid, ids, context=context)[0]
        year = datetime.strptime(payslip.date_from, DF).strftime('%Y')

        # all the payslips which are created
        pay_ids = Payslip.search(cr, uid, [('employee_id', '=', payslip.employee_id.id)], context=context)
        for slip in self.browse(cr, uid, pay_ids, context=context):
            slip_year = datetime.strptime(slip.date_from, DF).strftime('%Y')
            # compate year because we want info of same year, and need data of all the previous payslips created in this year
            if year == slip_year and datetime.strptime(slip.date_from, DF) <= datetime.strptime(payslip.date_from, DF):
                if type == "employee":
                    total_cpf += slip.employee_cpf
                else:
                    total_cpf += slip.employer_cpf
        return total_cpf

class employee_cpf_detail(osv.Model):
    _name = 'employee.cpf.detail'
    _columns = {
        'name': fields.char('Name', translate=True),
        'date': fields.date('Date/Month'),
        'employee_cpf': fields.float('Employee Contribution'),
        'employer_cpf': fields.float('Employer Contribution'),
        'employee_id': fields.many2one('hr.employee', 'Employee')
    }

class cpf_rule(osv.Model):
    _name = 'cpf.rule' #Name as cpf.register

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'sector_ids':fields.many2many('company.sector.type', 'cpf_rule_sector_rel', 'rule_id', 'sector_id', 'Company Sectors'),
        'applicable_ids':fields.many2many('citizen.applicable', 'cpf_rule_citz_app_rel', 'rule_id', 'citizen_app_id', 'Applicable for'),
        'age_rule_ids': fields.one2many('age.rule.line', 'cpf_rule_id', 'Age Rules'), #Better name to rule_ids only, rule can also be wage base
    }

    def _check_unique_rule(self, cr, uid, ids, context=None):
        age_wage_list = []
        for register in self.browse(cr, uid, ids, context=context):
            for rule in register.age_rule_ids:
                age_wage_str = str(rule.wage_start) + str(rule.wage_end) + str(rule.age_start) + str(rule.age_end)
                if age_wage_list and age_wage_str in age_wage_list: #compare rule.wage_start, rule.wage_end, rule.date_start, rule.date_end
                    return False
                age_wage_list.append(age_wage_str)
        return True


    _constraints = [
            (_check_unique_rule, 'Error! You cannot create duplicate rule, age range and wage range should be different', ['age_start', 'age_end', 'wage_start', 'wage_end'])
    ]

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        res = super(cpf_rule, self).search(cr, uid, args, offset, limit, order, context, count)
        if context.get('employee_company_id') and context.get('emp_citizen'):
            company = self.pool.get('res.company').browse(cr, uid, context['employee_company_id'])
            company_sector = company.company_sector
            cpf_rule_ids = self.search(cr, uid, [('sector_ids.company_sector', '=', company_sector), ('applicable_ids.citizenship', '=', context['emp_citizen'])])
            if cpf_rule_ids:
                return cpf_rule_ids
        elif context.get('employee_company_id') and not context.get('emp_citizen'):
            company = self.pool.get('res.company').browse(cr, uid, context['employee_company_id'])
            company_sector = company.company_sector
            cpf_rule_ids = self.search(cr, uid, [('sector_ids.company_sector', '=', company_sector)])
            if cpf_rule_ids:
                return cpf_rule_ids
        elif not context.get('employee_company_id') and context.get('emp_citizen'):
            cpf_rule_ids = self.search(cr, uid, [('applicable_ids.citizenship', '=', context['emp_citizen'])])
            if cpf_rule_ids:
                return cpf_rule_ids
        return res


class age_rule_line(osv.Model):
    _name = 'age.rule.line'

    _columns = {
        'name': fields.char('Name', size=64, translate=True),
        'cpf_rule_id': fields.many2one('cpf.rule', 'CPF Rule Register'),
        'age_start': fields.float('Age Start'),
        'age_end': fields.float('Age End'),
        'wage_start': fields.float('Wage From'),
        'wage_end': fields.float('Wage End'),
        'employer_python_code': fields.text('Employer Python Code', required=True),
        'employee_python_code': fields.text('Employee Python Code', required=True),
    }

class cpf_submission_file(osv.Model):
    _name = "cpf.submission.file"

    _columns = {
        'name': fields.char("Name", size=64, translate=True,required=True),
        'cpf_file_id': fields.many2one('ir.attachment',"CPF File"),
        'employee_ids': fields.many2many('hr.employee','cpf_submission_file_rel', 'emp_id', 'cpf_file_id', 'Employee'),
        'state': fields.selection([('draft', 'Draft'), ('wait', 'Waiting Approval'), ('approve', 'Approved')], 'State'),
        'validate_id': fields.many2one('res.users', 'Validated By'),
        'user_id': fields.many2one('res.users', 'Created By'),
        'date': fields.datetime('Create Date'),
    }

class employee_donation_input(osv.osv):
    '''
    Donation Input
    '''

    _name = 'employee.donation.input'
    _description = 'Donation Input'
    _columns = {
        'name': fields.char('Description', required=True),
        'payslip_id': fields.many2one('hr.payslip', 'Pay Slip', ondelete='cascade', select=True),
        'sequence': fields.integer('Sequence', required=True, select=True),
        'code': fields.char('Code', size=52, required=True, help="The code that can be used in the salary rules"),
        'amount': fields.float('Amount', help="It is used in computation."),
        'contract_id': fields.many2one('hr.contract', 'Contract', required=True, help="The contract for which applied this input"),
    }
    _order = 'sequence'
    _defaults = {
        'sequence': 10,
        #'amount': 0.0,
    }