# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today
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
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime
from openerp import tools
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import timedelta
from dateutil import relativedelta
import time
import re
import os
import tempfile
from dateutil.relativedelta import relativedelta

class cpf_submission(osv.Model):
    _name = 'cpf.submission'
    _description = 'CPF submission'

    month = [(1, 'Janyary'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'),
              (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'),(12, 'December'),]

    _columns = {
        'file_date': fields.datetime('Date',required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one('res.company','Company',required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'employee_ids': fields.many2many('hr.employee','cpf_employee_submission_rel', 'emp_id', 'cpf_id', 'Employee', readonly=True, states={'draft': [('readonly', False)]}),

        'name': fields.char("Name", size=64, translate=True, readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
        'cpf_file_id': fields.many2one('ir.attachment',"CPF File", readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
        'state': fields.selection([('draft', 'Draft'), ('wait', 'Waiting Approval'), ('approve', 'Approved')], 'State'),
        'validate_id': fields.many2one('res.users', 'Validated By', readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
        'user_id': fields.many2one('res.users', 'Created By', readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
        'date': fields.datetime('Create Date', readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
        'advice_code': fields.char("Advice Code"),
        'serial_no': fields.char("Serial No"),
        'payment_type': fields.selection([('pte', 'PTE'), ('ams', 'AMS')], 'Payment Type', help='Payment mode for cpf'),
    }
    _rec_name = "file_date"

    def _get_default_employees(self, cr, uid, context=None):
        employee_ids = []
        #employee_ids = employee_obj.search(cr, uid, [('citizenship', '!=', 'foreigner')], context=context)
        return [(6, 0, employee_ids)]

    _defaults = {
        'employee_ids': _get_default_employees,
        'state': 'draft',
        'serial_no': '/',
        'payment_type': 'pte'
    }

    def create(self, cr, uid, vals, context=None):
        if context is None: context = {}
        if vals.get('serial_no', '/') == '/':
            vals['serial_no'] = self.pool.get('ir.sequence').get(cr, uid, 'cpf.serial') or '/'
        #if vals.get('serial_no') >= 99:
        #    vals['serial_no'] = ""
        return super(cpf_submission, self).create(cr, uid, vals, context=context)

    def open_payslip_batches(self, cr, uid, ids, context=None):
        payslip_obj = self.pool.get('hr.payslip')
        mod_obj = self.pool.get('ir.model.data')
        wizard = self.browse(cr, uid, ids[0], context)
        employee_ids = [employee.id for employee in wizard.employee_ids]
        wizard_date = datetime.strptime(wizard.file_date , '%Y-%m-%d %H:%M:%S')
        payslip_employee_search_ids = payslip_obj.search(cr, uid, [('employee_id', 'in', employee_ids), ('date_from', '>=', datetime(wizard_date.year, wizard_date.month, 1).strftime(DF)), ('date_to', '<=', (datetime(wizard_date.year, wizard_date.month, 1) + relativedelta(months=+1, days=-1)).strftime(DF))], context=context)
        payslip_employee_browse = payslip_obj.browse(cr, uid, payslip_employee_search_ids, context=context)
        payslip_employee_ids = [x.employee_id.id for x in payslip_employee_browse]
        print "\n\nemployee_ids and payslip_employee_ids ::: ", employee_ids, payslip_employee_ids
        view_id = mod_obj.get_object_reference(cr, uid, 'l10n_sg_payroll', 'hr_payslip_batch_form')[1]
        default_employee_ids = list(set(employee_ids) - set(payslip_employee_ids))
        return {
            'name': 'Payslips Batches',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.employee.batches',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id,'form')],
            'target': 'new',
            'context': {'default_employee_ids': [(6, 0, default_employee_ids)]}
        }

    def action_approve(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'approve'})
        return True

    def action_apply(self, cr, uid, ids, context=None):
        res_company = self.pool.get('res.company')
        contract_obj = self.pool.get('hr.contract')
        employee_obj = self.pool.get('hr.employee')
        payslip_obj = self.pool.get('hr.payslip')
        mod_obj = self.pool.get('ir.model.data')
        ir_obj = self.pool.get('ir.attachment')
        wizard = self.browse(cr, uid, ids[0], context)
        company = res_company.browse(cr, uid, wizard.company_id.id, context)
        employee_ids = [employee.id for employee in wizard.employee_ids]
        wizard_date = datetime.strptime(wizard.file_date , '%Y-%m-%d %H:%M:%S')

        def padding_zero(value, numeric_length, decimal_length=None, if_blank_fill_space=False):
            #TODO: Handle negative values
            if not value and if_blank_fill_space:
                value = value or ''
                return value.ljust(numeric_length)
            if not value:
                value = "0"
            if not isinstance(value, basestring):
                value = str(value)
            split_result = value.split(".")
            result = split_result[0].rjust(numeric_length, "0")
            if decimal_length:
                if len(split_result) > 1:
                    result += split_result[1].ljust(decimal_length, "0")
            return result

        payment_code_mapping = {'': '01', '': '02', '': '03', '': '04', '': '05', '': '06', '': '07', '': '08', '': '09', '': '10', '': '11'}
        #Raise Redirect warning if there are some payslip pending to create
        #TO ASK: Whether to raise warning if payslip is not generated for all employee or to check for employees only selected in wizard
        #TODO: Use relative delta to add one month -1 date
        print "Dates are ::::: ", datetime(wizard_date.year, wizard_date.month, 1, 1, 0, 0).strftime(DF), (datetime(wizard_date.year, wizard_date.month, 1, 23, 59, 59) + relativedelta(months=+1, days=-1)).strftime(DF)
        payslip_employee_search_ids = payslip_obj.search(cr, uid, [('employee_id', 'in', employee_ids), ('date_from', '>=', datetime(wizard_date.year, wizard_date.month, 1, 1, 0, 0).strftime(DF)), ('date_to', '<=', (datetime(wizard_date.year, wizard_date.month, 1, 23, 59, 59) + relativedelta(months=+1, days=-1)).strftime(DF))], context=context)
        payslip_employee_browse = payslip_obj.browse(cr, uid, payslip_employee_search_ids, context=context)
        payslip_employee_ids = [x.employee_id.id for x in payslip_employee_browse]
        payslip_ids = [x.id for x in payslip_employee_browse]
        if set(employee_ids) - set(payslip_employee_ids):
            raise Warning('There are some employees for which payslip is not generated for current month,\nPlease click on "Generate Batch Payslips" button from top right corner to create payslips for those employee.')

        file_month = datetime.strptime(wizard.file_date , '%Y-%m-%d %H:%M:%S')
        #Add payment_type and sno with nric_fin_passport_id number
        file_name = str(str(company.nric_fin_passport_id))+str(self.month[file_month.month-1][1][:3])+str(file_month.year)+'04.txt'
        fname, ext = file_name and os.path.splitext(file_name) or ('','')
        fd, rfname = tempfile.mkstemp(suffix=ext, prefix=fname)
        payment_type_mapping = {'pte': 'PTE', 'ams': 'AMS'}
        payment_type = payment_type_mapping[wizard.payment_type or 'pte']
        employee_type_map = {'pensionable': 'P', 'non_pensionable': 'N', 'bonuspmt': 'A', 'contract': 'C', 'saver': 'S'}
        contribution_summary_amount_sum = 0
        #TODO: To improve all ljust, it should have only str.ljust(12)
        #TO ASK: advice_code, currently consider 04 right now
        #Employer Header
        serial_no = wizard.serial_no and wizard.serial_no[:2]
        employer_record_count = 0
        employer_header = "F " + str(company.nric_fin_passport_id).ljust(10-len(str(company.nric_fin_passport_id)), " ") + payment_type + serial_no + " " + str("04") + file_month.strftime("%C%y%m%d") + file_month.strftime("%H%M%S") + "FTP.TXT"
        employer_header += " " * (150 - len(employer_header)-1)
        employer_record_count += 1
        os.write(fd, employer_header+"\n")

        #Employer Contribution Summary
        employer_contirution_summary = ""
        employer_contirution_summary_record = "F" + "0" + wizard.company_id.nric_fin_passport_id + payment_type + serial_no + " " + str("04") + file_month.strftime("%C%y%m%d") + "01"
        contribution_total_cpf = 0
        print "\n\npayslip_ids are ::: ", payslip_ids
        for payslip_browse in payslip_obj.browse(cr, uid, payslip_ids, context=context):
            contribution_total_cpf += payslip_browse.total_cpf #TODO: Here it should be contribution_summary_amount
        contribution_total_cpf = padding_zero(str(contribution_total_cpf), 10, 2, if_blank_fill_space=True)
        contribution_summary_amount_sum += int(contribution_total_cpf)
        employer_contirution_summary_record = employer_contirution_summary_record + str(contribution_total_cpf) + padding_zero(str(0), 9, if_blank_fill_space=False) #<-- Donor count
        employer_contirution_summary_record += " " * (150 - len(employer_contirution_summary_record) - 1) + "\n"
        employer_contirution_summary += employer_contirution_summary_record
        employer_record_count += 1
        #TODO: Create each record for MBMF, SINDA and add it to file, Here in loop create sum of al cpf, MBMF, SINDA and other payments, not for each employee
        #Need to iterate through payslip and then payslip lines and consider those lines which having donation_id
        donation_ids = self.pool.get('employee.donation').search(cr, uid, [], context=context)
        payslip_line_pool = self.pool.get('hr.payslip.line')
        for donation_id in donation_ids:
            sequence = 0
            donor_count = 0
            employer_contirution_summary_record = ""
            sequence_result = self.pool.get('employee.donation').read(cr, uid, donation_id, ['sequence'], context=context)
            if sequence_result:
                sequence = sequence_result.get('sequence')
            sequence = padding_zero(str(sequence), 2, if_blank_fill_space=False)
            donation_read_group = payslip_line_pool.read_group(cr, uid, [('slip_id', 'in', payslip_ids), ('employee_donation_id', '=', donation_id)], fields=['employee_donation_id', 'total'], groupby=['employee_donation_id'], context=context)
            print "\n\ndonation_read_group is :: ", donation_read_group
            employer_contirution_summary_record += "F" + "0" + wizard.company_id.nric_fin_passport_id + payment_type + serial_no + " " + str("04") + file_month.strftime("%C%y%m%d") + str(sequence)
            amount = 0.0
            if donation_read_group:
                amount = donation_read_group[0].get('total', 0.0)
            contribution_summary_amount_sum += int(amount)
            amount = padding_zero(str(amount), 10, 2, if_blank_fill_space=False)
            if donation_read_group:
                donor_count = donation_read_group[0].get('employee_donation_id_count', 0)
            donor_count = padding_zero(str(int(donor_count)), 9, if_blank_fill_space=False)
            employer_contirution_summary_record += amount + donor_count
            employer_contirution_summary_record += " " * (150 - len(employer_contirution_summary_record) - 1) + "\n"
            employer_contirution_summary += employer_contirution_summary_record
            employer_record_count += 1


        os.write(fd, employer_contirution_summary)

        salary_rule_category = self.pool.get('hr.salary.rule.category')
        employee_status_mapping = {'confirmed': 'E', 'probation': 'N', 'resigned': 'L', 'join_leave_same_month': 'O'}
        #Employer Contribution Detail
        employer_contribution_detail = "" #optional, for each payslip, iterate through all payslip of current month
        for payslip_browse in payslip_obj.browse(cr, uid, payslip_ids, context=context):
            employee_status = employee_status_mapping.get(payslip_browse.employee_id.status) if payslip_browse.employee_id.status else 'E'
            employer_contribution_detail_record = ""
            #TODO: ‘S’ prefix is used for Singapore citizens, permanent residents who are issued CPF account numbers by
            #the Board. However, the ‘T’ prefix will be issued to people who become permanent residents from 1
            #January 2000 as well as persons born on and after 1 January 2000.
            emp_account_no = ""
            emp_account_prefix = 'S' if payslip_browse.employee_id.citizenship in ['singaporean', 'singapore_pr'] else 'T'
            if payslip_browse.employee_id.nric_fin_passport_id:
                emp_account_no = emp_account_prefix + payslip_browse.employee_id.nric_fin_passport_id[-8:] + "1"

            additional_group_amount = 0
            addition_type_id = salary_rule_category.search(cr, uid, [('code', '=', 'ALW')], context=context)
            additional_read_group = payslip_line_pool.read_group(cr, uid, [('slip_id', '=', payslip_browse.id), ('category_id', '=', addition_type_id[0])], fields=['total', 'category_id'], groupby=['category_id'], context=context)
            if additional_read_group:
                additional_group_amount = additional_read_group[0].get('total')
            additional_group_amount = padding_zero(str(additional_group_amount), 10, 2, if_blank_fill_space=True)
            employer_contribution_detail_record += "F" + "1" + payslip_browse.employee_id.company_id.nric_fin_passport_id + payment_type + serial_no + " " + str("04") + file_month.strftime("%C%y%m%d") \
                                                    + "01" + emp_account_no + padding_zero(str(payslip_browse.employee_cpf), 10, 2, if_blank_fill_space=True) \
                                                    + padding_zero(str(payslip_browse.contract_id.wage), 8, 2, if_blank_fill_space=True) + additional_group_amount \
                                                    + employee_status + (payslip_browse.employee_id.name).ljust(22-len(str(payslip_browse.employee_id.name))) + " " + "   " #TO thing about MOF/MID, it should not be blank always what if this software is used by Army peoples
            employer_contribution_detail_record += " " * (150 - len(employer_contribution_detail_record) - 1) + "\n"
            employer_record_count += 1
            #Create each record for MBMF, SINDA and add it to file
            employer_contribution_detail += employer_contribution_detail_record
            for payslip_line in payslip_browse.line_ids:
                employer_contribution_detail_record = ""
                if not payslip_line.employee_donation_id:
                    continue
                payment_code = padding_zero(str(payslip_line.employee_donation_id.sequence), 2, if_blank_fill_space=False)
                employer_contribution_detail_record += "F" + "1" + payslip_browse.employee_id.company_id.nric_fin_passport_id \
                                                        + payment_type + serial_no + " " + str("04") + file_month.strftime("%C%y%m%d") \
                                                        + payment_code + emp_account_no + str(payslip_line.total).ljust(12-len(str(payslip_line.total))) \
                                                        + str(0).ljust(12) + str(0).ljust(12) + " " + (payslip_browse.employee_id.name).ljust(22-len(str(payslip_browse.employee_id.name))) + " " + "   "
                employer_contribution_detail_record += " " * (150 - len(employer_contribution_detail_record) - 1) + "\n"
                employer_record_count += 1
                employer_contribution_detail += employer_contribution_detail_record

        os.write(fd, employer_contribution_detail)

        #Employer Trailer Record
        employer_record_count += 1
        contribution_summary_amount_sum = padding_zero(str(amount), 10, 2, if_blank_fill_space=True)
        employer_trailer_record = "F" + "9" + str(company.nric_fin_passport_id) + payment_type + serial_no + " " + str("04") + str(employer_record_count) + contribution_summary_amount_sum
        employer_trailer_record = employer_trailer_record + " " * (150 - len(employer_trailer_record) - 1)
        os.write(fd, employer_trailer_record)

        os.close(fd)
        file_data = ""
        with open(rfname, 'rb') as file_content:
            file_data = file_content.read().encode('base64')
        vals = {
            'name': file_name,
            'res_model': self._name,
            'res_id': wizard.id or False,
            'datas': file_data,
            'datas_fname': file_name
        }
        file_id = ir_obj.create(cr, uid, vals, context=context)
        self.write(cr, uid, wizard.id, {'name': file_name,'state': 'wait','employee_ids': [(6,0, employee_ids)],'user_id': uid, 'cpf_file_id': file_id, 'date': datetime.now()}, context=context)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            #'params': {
            #    'menu_id': menu_id
            #},
        }

class hr_payslip_employee_batches(osv.osv_memory):
    _name = 'hr.payslip.employee.batches'
    _description = 'Payslip Batches'
    _columns = {
        'name': fields.char('Name', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'date_start': fields.date('Date From', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'date_end': fields.date('Date To', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('close', 'Close'),
        ], 'Status', select=True, readonly=True, copy=False),
        'credit_note': fields.boolean('Credit Note', help="Indicates this payslip has a refund of another", readonly=True, states={'draft': [('readonly', False)]}),
        'employee_ids': fields.many2many('hr.employee', 'hr_payslip_batch_employee_rel', 'payslip_batch_id', 'employee_id', 'Employees'),
    }

    _defaults = {
        'state': 'draft',
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_end': lambda *a: str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10],
    }

    #TODO: Create Payslip batches using payslip.run record
    def compute_sheet(self, cr, uid, ids, context=None):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        run_pool = self.pool.get('hr.payslip.run')
        hr_payslip_employee_batches_obj = self.browse(cr, uid, ids[0], context=context)
        slip_ids = []
        if context is None:
            context = {}
        from_date =  hr_payslip_employee_batches_obj.date_start or False
        to_date = hr_payslip_employee_batches_obj.date_end or False
        credit_note = hr_payslip_employee_batches_obj.credit_note or False
        print "\n\nEmployees are :::: ", hr_payslip_employee_batches_obj.employee_ids
        if not hr_payslip_employee_batches_obj.employee_ids:
            raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
        employee_ids = [x.id for x in hr_payslip_employee_batches_obj.employee_ids]
        print "\n\nemployee_ids is ::: ", employee_ids
        run_id = run_pool.create(cr, uid, {'name': hr_payslip_employee_batches_obj.name, 'date_start': hr_payslip_employee_batches_obj.date_start, 'date_end': hr_payslip_employee_batches_obj.date_end}, context=context)
        for emp in emp_pool.browse(cr, uid, employee_ids, context=context):
            slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)
            res = {
                'employee_id': emp.id,
                'name': slip_data['value'].get('name', False),
                'struct_id': slip_data['value'].get('struct_id', False),
                'contract_id': slip_data['value'].get('contract_id', False),
                'payslip_run_id': run_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
            }
            slip_ids.append(slip_pool.create(cr, uid, res, context=context))
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_payroll', 'hr_payslip_run_form')[1]
        return {
            'name': 'Payslips Batches',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id,'form')],
            'res_id': run_id,
        }