from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime
from openerp import tools
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import time
import re
import os
import tempfile

class ir8a_submission(osv.Model):
    _name = 'ir8a.submission'
    _description = 'IR8A submission'

    month = [(1, 'Janyary'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'),
              (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'),(12, 'December'),]

    _columns = {
        'name': fields.char("Name", size=64, translate=True, readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
        'assesment_period_id': fields.many2one("assesment.year", 'Assesment Year', required=True),
        'ir8a_file_id': fields.many2one('ir.attachment',"IR8A File", readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),

        'authorized_user_id': fields.many2one("res.users", "Authorized Person", required=True),
        'batch_indicator_type': fields.selection([('o', 'Original'), ('a', 'ammendment')], 'Batch Indiactor', required=True, help='If Batch Indicator is O then all values of amount field must be postive.'),
        'file_date': fields.datetime('File Date',required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'batch_date': fields.date("Batch start"),
        'company_id': fields.many2one('res.company','Company',required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'employee_ids': fields.many2many('hr.employee','ir8a_employee_submission_rel', 'emp_id', 'cpf_id', 'Employee', readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([('draft', 'Draft'), ('wait', 'Waiting Approval'), ('approve', 'Approved')], 'State'),
        'validate_id': fields.many2one('res.users', 'Validated By', readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
        'user_id': fields.many2one('res.users', 'Created By', readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
        'date': fields.datetime('Create Date', readonly=False, invisible=False, states={'draft': [('readonly', True), ('invisible', True)]}),
    }

    _rec_name = "file_date"

    def _get_default_employees(self, cr, uid, context=None):
        employee_obj = self.pool.get('hr.employee')
        employee_ids = []
        #employee_ids = employee_obj.search(cr, uid, [('citizenship', '!=', 'foreigner')], context=context)
        return [(6, 0, employee_ids)]

    _defaults = {
        'employee_ids': _get_default_employees,
        'state': 'draft'
    }

    def open_payslip_batches(self, cr, uid, ids, context=None):
        payslip_obj = self.pool.get('hr.payslip')
        mod_obj = self.pool.get('ir.model.data')
        wizard = self.browse(cr, uid, ids[0], context)
        employee_ids = [employee.id for employee in wizard.employee_ids]
        wizard_date = datetime.strptime(wizard.file_date , '%Y-%m-%d %H:%M:%S')
        payslip_employee_search_ids = payslip_obj.search(cr, uid, [('employee_id', 'in', employee_ids), ('date_from', '>=', datetime(wizard_date.year, wizard_date.month, 1).strftime(DF)), ('date_to', '<=', datetime(wizard_date.year, wizard_date.month, 28).strftime(DF))], context=context)
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
        payslip_line_obj = self.pool.get('hr.payslip.line')
        mod_obj = self.pool.get('ir.model.data')
        ir_obj = self.pool.get('ir.attachment')
        wizard = self.browse(cr, uid, ids[0], context)
        company = res_company.browse(cr, uid, wizard.company_id.id, context)
        employee_ids = [employee.id for employee in wizard.employee_ids]
        wizard_date = datetime.strptime(wizard.file_date , '%Y-%m-%d %H:%M:%S')
        income_tax_record = False

        def padding_zero(value, numeric_length, decimal_length=None, if_blank_fill_zero=False):
            #TODO: Handle negative values
            print "\nInside padding_zero value is ::: ",value
            if not value and if_blank_fill_zero:
                value = value or ''
                if isinstance(value, float):
                    value = str(value)
                return value.ljust(numeric_length, "0")

            if not value and if_blank_fill_space:
                value = value or ''
                if isinstance(value, float):
                    value = str(value)
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
                else:
                     result += "".ljust(decimal_length, "0")
            print "\nInside padding_zero result is ::: ",result
            return result

        def padding_space(value, numeric_length, precedence):
            #TODO: Handle Precedence
            if not isinstance(value, basestring):
                value = str(value)
            return value.ljust(numeric_length)

        #Raise Redirect warning if there are some payslip pending to create
        #TO ASK: Whether to raise warning if payslip is not generated for all employee or to check for employees only selected in wizard
        print "\n\nwizard_date is ::: ", wizard_date, type(wizard_date)
        to_date = (wizard_date + relativedelta(months=1))
        payslip_employee_search_ids = payslip_obj.search(cr, uid, [('employee_id', 'in', employee_ids), ('date_from', '>=', datetime(wizard_date.year, wizard_date.month, 1, 0, 0, 0).strftime(DF)), ('date_to', '<=', datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59).strftime(DF))], context=context)
        payslip_employee_browse = payslip_obj.browse(cr, uid, payslip_employee_search_ids, context=context)
        payslip_employee_ids = [x.employee_id.id for x in payslip_employee_browse]
        payslip_ids = [x.id for x in payslip_employee_browse]
        if set(employee_ids) - set(payslip_employee_ids):
            raise Warning('There are some employees for which payslip is not generated for current month,\nPlease click on "Generate Batch Payslips" button from top right corner to create payslips for those employee.')

        file_name = 'IR8A.txt'
        fname, ext = file_name and os.path.splitext(file_name) or ('','')
        fd, rfname = tempfile.mkstemp(suffix=ext, prefix=fname)

        designation_authorized = ''
        related_employee_ids = self.pool.get("hr.employee").search(cr, uid, [('user_id', '=', wizard.authorized_user_id.id)], context=context)
        if related_employee_ids:
            related_employee = self.pool.get("hr.employee").browse(cr, uid, related_employee_ids[0], context=context)
            designation_authorized = (related_employee.user_id == wizard.authorized_user_id) and related_employee.job_id and related_employee.job_id.name
        designation_authorized = ((designation_authorized or '') + " " * (30 - len(designation_authorized)))

        #What about Goverment Department, what about Aided School currently added in other
        print "\n\nwizard.company_id.phone ::: ", wizard.company_id.phone, len(str(wizard.company_id.phone or ''))

        file_year = datetime.strptime(wizard.file_date , '%Y-%m-%d %H:%M:%S').year
        sector_mapping = {'private': 6, 'statutory_body': 5, 'ministries': 1, 'added_school': 9}
        header = "0" + str(sector_mapping.get(wizard.company_id.company_sector)) + str(file_year) + "08" + wizard.company_id.org_id_type + (wizard.company_id.org_id_no + " " * (12-len(str(wizard.company_id.org_id_no)))) \
                    + (wizard.authorized_user_id.name + " " * (30 - len(wizard.authorized_user_id.name))) + designation_authorized + (wizard.company_id.name + " " * (60 - len(wizard.company_id.name))) \
                    + str(str(wizard.company_id.phone or '') + " " * (20-len(str(wizard.company_id.phone or '')))) \
                    + (wizard.authorized_user_id.login[:50] + " " * (60 - len(wizard.authorized_user_id.login[:50]))) + (wizard.batch_indicator_type).upper() + datetime.strptime(wizard.file_date, DTF).strftime("%Y%m%d") + (" " * 30) + "IR8A"+ " " * 6
        header = header + " " * (1200 - len(header))
        os.write(fd, header+"\n")

        gender_mapping = {'male': 'M', 'female': 'F'}
        detail_records = []
        detail_record_count = 0
        total_cpf_amount = 0

        total_amount_of_payment = 0
        total_amount_of_salary = 0
        total_amount_of_bonus = 0
        total_amount_of_directors_fees = 0
        total_amount_of_others = 0
        total_amount_of_exempt_income = 0
        total_amount_of_employment_income_for_which_tax_is_borne_by_employer = 0
        total_amount_of_income_tax_liability_for_which_tax_is_borne_by_employee = 0
        total_amount_of_donation = 0
        total_amount_of_insurance = 0
        total_amount_of_mbf = 0
        total_amount_of_cpf = 0

        #TODO: To improve all ljust, it should have only str.ljust(12)
        #TODO: If not blank cannot have space, apply everywhere, what should be placed if that item is blank, 0 ?
        #TODO: 2. YYYY must be equal to the Basis year in the Header Record.  etc constraints
        for employee in wizard.employee_ids:
            detail_record = ""
            income_tax_record_ids = self.pool.get('income.tax.detail').search(cr, uid, [('assesment_year_id', '=', wizard.assesment_period_id.id), ('employee_id', '=', employee.id)])
            if not income_tax_record_ids:
                raise Warning('Please enter Income tax detail for selected assesment year in employee form.')
            else:
                income_tax_record = self.pool.get('income.tax.detail').browse(cr, uid, income_tax_record_ids[0], context=context)
            employee_payslip_ids = payslip_obj.search(cr, uid, [('employee_id', '=', employee.id), ('id', 'in', payslip_ids)])
            employee_payslip_line_ids = payslip_line_obj.search(cr, uid, [('slip_id', 'in', employee_payslip_ids)], context=context)
            employee_payslips = payslip_obj.browse(cr, uid, employee_payslip_ids, context=context)
            employee_id_type = (company.nric_fin_passport_id or 1) #TODO: How to identify wheather number is nric, passport or fin ?
            total_cpf_amount = sum([x.total_cpf for x in employee_payslips]) or 0
            first_payslip = employee_payslip_ids and employee_payslip_ids[0]
            last_payslip = employee_payslip_ids and employee_payslip_ids[-1]
            #TODO: Need to identify which address is using, currently we will having working address, need to put selection foreign address, local address
            #need to add period(date_from, date_to) for ir8a
            identification_type = ""
            identification_no = ""
            identification_type_mapping = {'nric': 1, 'fin': 2, 'immref': 3, 'malayis': 5, 'work': 4, 'passport': 6}
            for permit in employee.permit_ids:
                if permit.name not in ['nric', 'fin', 'immref', 'malayis', 'work', 'passport']:
                    continue
                identification_type = identification_type_mapping.get(permit.name)
                identification_no = permit.id_number

            #insurance_val = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'e4'), ('slip_id', '=', payslip.id)], ['amount'], context=context)
            #insurance_val = sum([x.get('amount') for x in insurance_val if x])
            insurance_val = income_tax_record.insurance
            insurance_val = padding_zero(insurance_val, 5, if_blank_fill_zero=True)

            mbf_val = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'e5'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
            mbf_val = sum([x.get('total') for x in mbf_val if x])
            mbf_val = abs(mbf_val)
            mbf_val = padding_zero(mbf_val, 5, if_blank_fill_zero=True)

            donation_sum_except_mbf = payslip_line_obj.search_read(cr, uid, [('employee_donation_id', '!=', False), ('irab_code', '!=', 'e5'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
            donation_sum_except_mbf = sum([x.get('total') for x in donation_sum_except_mbf if x])
            donation_sum_except_mbf = abs(donation_sum_except_mbf)
            donation_sum_except_mbf = padding_zero(donation_sum_except_mbf, 5, if_blank_fill_zero=True)

            bonus_val = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'b_bonus'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
            bonus_val = sum([x.get('total') for x in bonus_val if x])
            bonus_val = padding_zero(str(bonus_val), 9, if_blank_fill_zero=True)

            director_fee_val = income_tax_record.directories_fee
            director_fee_val = padding_zero(str(director_fee_val), 9, if_blank_fill_zero=True)

            gains_and_profit_from_share_val = income_tax_record.gain_profit
            gains_and_profit_from_share_val = padding_zero(gains_and_profit_from_share_val, 9, if_blank_fill_zero=True)

            employee_cpf_pf_fund = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'e2'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
            employee_cpf_pf_fund = sum([x.get('total') for x in employee_cpf_pf_fund if x])
            employee_cpf_pf_fund = abs(employee_cpf_pf_fund)
            employee_cpf_pf_fund = padding_zero(str(employee_cpf_pf_fund), 7, if_blank_fill_zero=True)

            #gratuity_val = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd41'), ('id', 'in', employee_payslip_line_ids)], ['amount'], context=context)
            #gratuity_val = sum([x.get('amount') for x in gratuity_val if x])
            #gratuity_val = str(gratuity_val).rjust(7, "0") if gratuity_val else " " * 7
            gratuity_val = income_tax_record.gratuity_payment_amount

            #pension_val = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd3'), ('id', 'in', employee_payslip_line_ids)], ['amount'], context=context)
            #pension_val = sum([x.get('amount') for x in pension_val if x])
            pension_val = income_tax_record.pension
            pension_val = padding_zero(pension_val, 9, 2, if_blank_fill_zero=True)

            transportation_allowance = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd11'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
            transportation_allowance = sum([x.get('total') for x in transportation_allowance if x])
            transportation_allowance = padding_zero(str(transportation_allowance), 9, 2, if_blank_fill_zero=True)

            entertaintement_allowance = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd12'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
            entertaintement_allowance = sum([x.get('total') for x in entertaintement_allowance if x])
            entertaintement_allowance = padding_zero(str(entertaintement_allowance), 9, 2, if_blank_fill_zero=True)

            name_of_retirement_benefit = income_tax_record.retirement_benefit_fund if income_tax_record.retirement_benefit_fund else ''

            retirement_benefits_before92 = income_tax_record.retirement_benefit_upto
            retirement_benefits_before92 = padding_zero(str(retirement_benefits_before92), 9, 2, if_blank_fill_zero=True)

            retirement_benefits_after92 = income_tax_record.retirement_benefit_accured_from
            retirement_benefits_after92 = padding_zero(str(retirement_benefits_after92), 9, 2, if_blank_fill_zero=True)

            excess_voluntry_contrib_cpf = income_tax_record.excess_volunatry_contribution_cpf_employer
            excess_voluntry_contrib_cpf = padding_zero(str(excess_voluntry_contrib_cpf), 9, 2, if_blank_fill_zero=True)

            value_of_benefits_in_kind = income_tax_record.value_benefits_in_kind
            value_of_benefits_in_kind = padding_zero(str(value_of_benefits_in_kind), 9, 2, if_blank_fill_zero=True)

            employee_designation = employee.job_id and (employee.job_id.name)
            employee_designation =  str(employee_designation).rjust(30) if employee_designation else " " * 30

            iras_approval_date = datetime.strptime(wizard.company_id.iras_approval_date, DF).strftime(DF) if wizard.company_id.iras_approval_date else " " * 8

            exempt_income_subject_to_remission = income_tax_record.exempt_income
            exempt_income_subject_to_remission = padding_zero(exempt_income_subject_to_remission, 9, if_blank_fill_zero=True)

            exempt_remission_income_indicator = income_tax_record.exempt_remission if income_tax_record.exempt_remission else ' '

            period_gross_commision_first_slip = payslip_obj.browse(cr, uid, first_payslip, context=context)
            period_gross_commision_first = period_gross_commision_first_slip.date_from
            peiod_gross_commision_last_slip = payslip_obj.browse(cr, uid, last_payslip, context=context)
            period_gross_commision_last = period_gross_commision_first_slip.date_to

            gross_commision = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd2'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
            gross_commision = sum([x.get('total') for x in gross_commision if x])
            gross_commision = padding_zero(str(gross_commision), 9, 2, if_blank_fill_zero=True)

            employement_income_for_tax_borne_by_employer = income_tax_record.employement_income_for_tax_borne_by_employer
            employement_income_for_tax_borne_by_employer = padding_zero(employement_income_for_tax_borne_by_employer, 9, if_blank_fill_zero=True)

            fixed_income_tax_liability_borne_by_employer = income_tax_record.fixed_income_tax_liability_borne_by_employer
            fixed_income_tax_liability_borne_by_employer = padding_zero(fixed_income_tax_liability_borne_by_employer, 9, if_blank_fill_zero=True)

            employee_income_tax = income_tax_record.employee_income_tax if income_tax_record.employee_income_tax else ' '

            compensation_loss_office = income_tax_record.compensation_loss_office
            compensation_loss_office = padding_zero(compensation_loss_office, 9, 2, if_blank_fill_zero=True)

            contribution_by_employer_pension_pf = income_tax_record.contribution_by_employer_pension_pf
            contribution_by_employer_pension_pf = padding_zero(contribution_by_employer_pension_pf, 9, 2, if_blank_fill_zero=True)

            gain_profit_share_option = income_tax_record.gain_profit_share_option
            gain_profit_share_option = padding_zero(gain_profit_share_option, 9, 2, if_blank_fill_zero=True)

            employee_voluntary_contribution_cpf = income_tax_record.employee_voluntary_contribution_cpf
            employee_voluntary_contribution_cpf = padding_zero(employee_voluntary_contribution_cpf, 7, if_blank_fill_zero=True)

            other_allowance = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd13'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
            other_allowance = sum([x.get('total') for x in other_allowance if x])
            other_allowance = padding_zero(str(other_allowance), 9, 2, if_blank_fill_zero=True)

            #TODO: Address must be handled properly as there is lots of rules for address regarding formatted and unformatted
            #Add three many2one field for local, foreign and c/o, create separate model for that, add required field
            #add one type field, local, c/o, foreign or other, if it is foreign then set some field required as per document,
            #Create two portion, Formatted address and Unformatted address, all having its fields, like porstal_code(may be create single field postal_code but put it twice in Formatted as well as in Unformatted address)
            address_type = (employee.local_address_id and "L") or (employee.co_address_id and "C") or (employee.foreign_address_id and "F") or "N"
            address = (employee.local_address_id) or (employee.co_address_id) or (employee.foreign_address_id)
            #Formatted Address
            block_no = (address and address.block_no or " ").ljust(10)
            street_name = (address and address.street or " ").ljust(32)
            level_no = (address and address.level_no or " ").ljust(3)
            unit_no = (address and address.unit_no or " ").ljust(5)
            postal_code = (address.postal_code or "".ljust(6, "0")) if address else "".ljust(6)

            #Unformatted Address
            line1 = (address and address.line1 or " ").ljust(30)
            line2 = (address and address.line2 or " ").ljust(30)
            line3 = (address and address.line3 or " ").ljust(30)
            postal_code_unformatted = (address.postal_code_unformatted or "".ljust(6, "0")) if address else "".ljust(6)

            #TO ASK: What to do about country  code and nationality code as we used currently exisiting res.country as a many2one
            country_code = (address.country_id or (" " * 3)) and (address.country_id.code or "").ljust(3) or (" " * 3)
            nationality_code = employee.country_id and (employee.country_id.code).ljust(3) or (" " * 3)

            others = int(gross_commision or 0) + int(pension_val or 0) + int(transportation_allowance or 0) + int(entertaintement_allowance or 0) + int(other_allowance or 0) \
                    + int(gratuity_val or 0) + int(retirement_benefits_after92 or 0) + int(contribution_by_employer_pension_pf or 0) + int(excess_voluntry_contrib_cpf or 0) \
                    + int(gain_profit_share_option or 0) + int(value_of_benefits_in_kind or 0)
            others = padding_zero(fixed_income_tax_liability_borne_by_employer, 9, if_blank_fill_zero=True)
            #Value must be the sum of items 31, 34, 35, 36, 37,38, 40, 41, 42, 43 and 44 Drop the decimals of the sum in items 31, 34, 35, 36, 37, 38, 40, 41, 42, 43 and 44.
            #i.e. sum of Gross Commission, Pension, Transport allowance, Entertainment allowance, Other allowances, Gratuity/ Notice Pay/ Ex-gratia payment/ Others,
            #Retirement benefits accrued from 1993, Contributions made by employer to any pension / provident fund constituted outside Singapore,
            #Excess / voluntary contribution to CPF by employer, Gains and profits from share options for S10 (1) (b), Value of benefits-in- kinds


            # Note: Currently Gross commision indicator is M(It can be O i.e. Other than monthly or B i.e. Both)
            # Note: From date and To date PeriodOfGrossCommisionFromdate411-418, ToDate419-426 is currently considered From date of first payslip and To date of last payslip

            benefits_in_kind = income_tax_record.benefits_in_kind if income_tax_record.benefits_in_kind else ' '
            section_applicable = income_tax_record.section_applicable if income_tax_record.section_applicable else ' '
            employee_income_tax = income_tax_record.employee_income_tax if income_tax_record.employee_income_tax else ' '
            gratuity_val_indicator = 'Y' if gratuity_val else 'N'
            wheather_compensation_loss_office = income_tax_record.wheather_compensation_loss_office if income_tax_record.wheather_compensation_loss_office else ' '
            iras_approval = 'Y' if wizard.company_id.iras_approval else 'N'
            cessation_provision_applicable = income_tax_record.cessation_provision_applicable if income_tax_record.cessation_provision_applicable else ' '
            from_ir8s = income_tax_record.from_ir8s if income_tax_record.from_ir8s else ' '
            period_gross_commision_first_val = (datetime.strptime(period_gross_commision_first, DF).strftime("%Y%m%d") if gross_commision else " "*8 )
            period_gross_commision_last_val = (datetime.strptime(period_gross_commision_last, DF).strftime("%Y%m%d") if gross_commision else " "*8)
            date_of_approval_director = datetime.strptime(income_tax_record.date_of_approval_director, DF).strftime("%Y%m%d") if income_tax_record.date_of_approval_director else (" "*8)
            date_of_commencement_val = datetime.strptime(income_tax_record.date_of_commencement, DF).strftime("%Y%m%d") if income_tax_record.date_of_commencement else " "*8
            date_of_cessation_posted_overseas_val = datetime.strptime(income_tax_record.date_of_cessation_posted_overseas, DF).strftime("%Y%m%d") if income_tax_record.date_of_cessation_posted_overseas else " "*8
            date_of_declaration_of_bonus_val = datetime.strptime(income_tax_record.date_of_declaration_of_bonus, DF).strftime("%Y%m%d") if income_tax_record.date_of_declaration_of_bonus else " "*8

            detail_record = "1" + str(identification_type) + str(identification_no).ljust(12) + (employee.name).ljust(40) + " ".ljust(40) \
                            + address_type + block_no + street_name + level_no + unit_no + postal_code + line1 + line2 + line3 \
                            + postal_code_unformatted + country_code + nationality_code + gender_mapping.get(employee.gender, 'M') + datetime.strptime(employee.birthday, DF).strftime("%Y%m%d") \
                            + padding_zero(str(employee.contract_id.wage + (int(bonus_val) or 0)), 9, if_blank_fill_zero=True) \
                            + (str(datetime.strptime(wizard.batch_date, DF).year) + "0101") + (str(datetime.strptime(wizard.batch_date, DF).year) + "1231") \
                            + mbf_val + donation_sum_except_mbf \
                            + employee_cpf_pf_fund + insurance_val \
                            + padding_zero(str(employee.contract_id.wage*len(employee_payslip_line_ids)), 9, if_blank_fill_zero=True) + bonus_val \
                            + director_fee_val + others \
                            + gains_and_profit_from_share_val + exempt_income_subject_to_remission \
                            + employement_income_for_tax_borne_by_employer + fixed_income_tax_liability_borne_by_employer \
                            + benefits_in_kind \
                            + section_applicable \
                            + employee_income_tax + gratuity_val_indicator \
                            + wheather_compensation_loss_office \
                            + iras_approval \
                            + iras_approval_date + cessation_provision_applicable \
                            + from_ir8s \
                            + exempt_remission_income_indicator + " " \
                            + gross_commision + period_gross_commision_first_val + period_gross_commision_last_val \
                            + "M" + pension_val + transportation_allowance \
                            + entertaintement_allowance + other_allowance \
                            + padding_zero(income_tax_record.gratuity_payment_amount, 9, 2, if_blank_fill_zero=True) + compensation_loss_office \
                            + retirement_benefits_before92 + retirement_benefits_after92 \
                            + contribution_by_employer_pension_pf + excess_voluntry_contrib_cpf \
                            + gain_profit_share_option + value_of_benefits_in_kind \
                            + employee_voluntary_contribution_cpf + employee_designation \
                            + date_of_commencement_val + date_of_cessation_posted_overseas_val + date_of_declaration_of_bonus_val \
                            + date_of_approval_director + ((name_of_retirement_benefit or "") + " " * (60 - len(name_of_retirement_benefit or ''))) + (" " *60) + " " + (" " * 8)

            detail_record = detail_record + (" " * (1150 - len(detail_record))) + (" " * 50)
            detail_records.append(detail_record)
            detail_record_count += 1

            #TODO Handle lstrip in all values, value may have '00-10', so lstrip('0') will remove precedding 0s
            total_amount_of_payment += (employee.contract_id.wage + int(bonus_val.lstrip("0") or 0) + int(director_fee_val.lstrip("0") or 0) + int(others.lstrip("0") or 0))
            total_amount_of_salary += employee.contract_id.wage
            total_amount_of_bonus += int(bonus_val.lstrip("0") or 0)
            total_amount_of_directors_fees += int(director_fee_val.lstrip("0") or 0)
            total_amount_of_others += int(others.lstrip("0") or 0)
            total_amount_of_exempt_income += int(exempt_income_subject_to_remission.lstrip("0") or 0)
            total_amount_of_employment_income_for_which_tax_is_borne_by_employer += int(employement_income_for_tax_borne_by_employer.lstrip("0") or 0)
            total_amount_of_income_tax_liability_for_which_tax_is_borne_by_employee += int(fixed_income_tax_liability_borne_by_employer.lstrip("0") or 0)
            total_amount_of_donation += int(donation_sum_except_mbf.lstrip("0") or 0)
            total_amount_of_cpf = int(employee_cpf_pf_fund.lstrip("0") or 0)
            total_amount_of_insurance += int(insurance_val.lstrip("0") or 0)
            total_amount_of_mbf += int(mbf_val.lstrip("0") or 0)

        to_write_detail_records = "\n".join(detail_records)
        os.write(fd, to_write_detail_records)


        total_amount_of_payment = padding_zero(str(total_amount_of_payment), 12, if_blank_fill_zero=True)
        total_amount_of_salary = padding_zero(str(total_amount_of_salary), 12, if_blank_fill_zero=True)
        total_amount_of_bonus = padding_zero(str(total_amount_of_bonus), 12, if_blank_fill_zero=True)
        total_amount_of_directors_fees = padding_zero(str(total_amount_of_directors_fees), 12, if_blank_fill_zero=True)
        total_amount_of_others = padding_zero(str(total_amount_of_others), 12, if_blank_fill_zero=True)
        total_amount_of_exempt_income = padding_zero(str(total_amount_of_exempt_income), 12, if_blank_fill_zero=True)
        total_amount_of_employment_income_for_which_tax_is_borne_by_employer = padding_zero(str(total_amount_of_employment_income_for_which_tax_is_borne_by_employer), 12, if_blank_fill_zero=True)
        total_amount_of_income_tax_liability_for_which_tax_is_borne_by_employee = padding_zero(str(total_amount_of_income_tax_liability_for_which_tax_is_borne_by_employee), 12, if_blank_fill_zero=True)
        total_amount_of_donation = padding_zero(str(total_amount_of_donation), 12, if_blank_fill_zero=True)
        total_amount_of_cpf = padding_zero(str(total_amount_of_cpf), 12, if_blank_fill_zero=True)
        total_amount_of_insurance = padding_zero(str(total_amount_of_insurance), 12, if_blank_fill_zero=True)
        total_amount_of_mbf = padding_zero(str(total_amount_of_mbf), 12, if_blank_fill_zero=True)

        trail_record = "2"+ str(detail_record_count).ljust(6) + total_amount_of_payment + total_amount_of_salary + total_amount_of_bonus \
                        + total_amount_of_directors_fees + total_amount_of_others + total_amount_of_exempt_income + total_amount_of_employment_income_for_which_tax_is_borne_by_employer \
                        + total_amount_of_income_tax_liability_for_which_tax_is_borne_by_employee + total_amount_of_donation + str(total_amount_of_cpf).ljust(12) + total_amount_of_insurance \
                        + total_amount_of_mbf
        trail_record = trail_record + " " * (1200 - len(trail_record))
        os.write(fd, "\n"+trail_record)

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
        self.write(cr, uid, wizard.id, {'name': file_name,'state': 'wait','employee_ids': [(6,0, employee_ids)],'user_id': uid, 'ir8a_file_id': file_id, 'date': datetime.now()}, context=context)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            #'params': {
            #    'menu_id': menu_id
            #},
        }