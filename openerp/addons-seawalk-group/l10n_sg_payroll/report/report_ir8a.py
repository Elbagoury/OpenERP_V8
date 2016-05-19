#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp.osv import osv
from openerp.report import report_sxw
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF
from datetime import timedelta
from dateutil.relativedelta import relativedelta

class sg_ir8a_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(sg_ir8a_report, self).__init__(cr, uid, name, context)
        self.context = context
        self.localcontext.update({
            'get_ir8a_detail': self.get_ir8a_detail,
            'marital_status_mapping': {'single': 'S', 'married': 'M', 'widower': 'W', 'divorced': 'D'}
        })

    def get_ir8a_detail(self, obj):
        print "\n\nself attributes ::: ", self.cr, self.uid, dir(self)
        result = self.action_apply(self.cr, self.uid, [obj.id], self.context)
        return result

    def action_apply(self, cr, uid, ids, context=None):
        res_company = self.pool.get('res.company')
        contract_obj = self.pool.get('hr.contract')
        employee_obj = self.pool.get('hr.employee')
        payslip_obj = self.pool.get('hr.payslip')
        payslip_line_obj = self.pool.get('hr.payslip.line')
        mod_obj = self.pool.get('ir.model.data')
        # for records = [1,2,3....]
        # wizard_records = {id1: wizard_dict{employee_ids: [{per_employee_detail}, {per_employee_detail}]}, id2: wizard_dict{employee_ids: [{per_employee_detail}, {per_employee_detail}]}

        wizard_records = {}
        for wizard in self.pool.get('ir8a.submission').browse(cr, uid, ids, context):
            wizard_record = {'company_obj': wizard.company_id}
            wizard_records[wizard.id] = wizard_record
            company = res_company.browse(cr, uid, wizard.company_id.id, context)
            employee_ids = [employee.id for employee in wizard.employee_ids]
            wizard_date = datetime.strptime(wizard.file_date , '%Y-%m-%d %H:%M:%S')
            income_tax_record = False

            #Raise Redirect warning if there are some payslip pending to create
            #TO ASK: Whether to raise warning if payslip is not generated for all employee or to check for employees only selected in wizard
            to_date = (wizard_date + relativedelta(months=1))
            payslip_employee_search_ids = payslip_obj.search(cr, uid, [('employee_id', 'in', employee_ids), ('date_from', '>=', datetime(wizard_date.year, wizard_date.month, 1, 0, 0, 0).strftime(DF)), ('date_to', '<=', datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59).strftime(DF))], context=context)
            payslip_employee_browse = payslip_obj.browse(cr, uid, payslip_employee_search_ids, context=context)
            payslip_employee_ids = [x.employee_id.id for x in payslip_employee_browse]
            payslip_ids = [x.id for x in payslip_employee_browse]
            if set(employee_ids) - set(payslip_employee_ids):
                raise Warning('There are some employees for which payslip is not generated for current month,\nPlease click on "Generate Batch Payslips" button from top right corner to create payslips for those employee.')

            designation_authorized = ''
            related_employee_ids = self.pool.get("hr.employee").search(cr, uid, [('user_id', '=', wizard.authorized_user_id.id)], context=context)
            if related_employee_ids:
                related_employee = self.pool.get("hr.employee").browse(cr, uid, related_employee_ids[0], context=context)
                designation_authorized = (related_employee.user_id == wizard.authorized_user_id) and related_employee.job_id and related_employee.job_id.name
            designation_authorized = ((designation_authorized or '') + " " * (30 - len(designation_authorized)))

            #What about Goverment Department, what about Aided School currently added in other

            file_year = datetime.strptime(wizard.file_date , '%Y-%m-%d %H:%M:%S').year
            sector_mapping = {'private': 6, 'statutory_body': 5, 'ministries': 1, 'added_school': 9}
            gender_mapping = {'male': 'M', 'female': 'F'}

            #TODO: To improve all ljust, it should have only str.ljust(12)
            #TODO: If not blank cannot have space, apply everywhere, what should be placed if that item is blank, 0 ?
            #TODO: 2. YYYY must be equal to the Basis year in the Header Record.  etc constraints
            wizard_record['employee_ids'] = []
            wizard_record['wizard_obj'] = wizard
            for employee in wizard.employee_ids:
                total_cpf_amount = 0
                employee_dict = {'emp_obj': employee}
                wizard_record['employee_ids'].append(employee_dict)
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
                employee_dict['total_cpf'] = total_cpf_amount
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

                employee_dict['gross_sal_leave_overtime_pay'] = (employee.contract_id.wage + 0 + 0) #TODO: Leave pay and overtime to add

                insurance_val = income_tax_record.insurance
                employee_dict['insurance'] = insurance_val

                mbf_val = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'e5'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
                mbf_val = sum([x.get('total') for x in mbf_val if x])
                mbf_val = abs(mbf_val)
                employee_dict['mbf'] = mbf_val

                donation_sum_except_mbf = payslip_line_obj.search_read(cr, uid, [('employee_donation_id', '!=', False), ('irab_code', '!=', 'e5'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
                donation_sum_except_mbf = sum([x.get('total') for x in donation_sum_except_mbf if x])
                donation_sum_except_mbf = abs(donation_sum_except_mbf)
                employee_dict['except_mbf'] = donation_sum_except_mbf

                bonus_val = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'b_bonus'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
                bonus_val = sum([x.get('total') for x in bonus_val if x])
                employee_dict['bonus'] = bonus_val

                director_fee_val = income_tax_record.directories_fee
                employee_dict['director_fee'] = director_fee_val

                gains_and_profit_from_share_val = income_tax_record.gain_profit

                employee_cpf_pf_fund = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'e2'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
                employee_cpf_pf_fund = sum([x.get('total') for x in employee_cpf_pf_fund if x])
                employee_cpf_pf_fund = abs(employee_cpf_pf_fund)

                gratuity_val = income_tax_record.gratuity_payment_amount
                employee_dict['gratuity'] = gratuity_val

                pension_val = income_tax_record.pension
                employee_dict['pension'] = pension_val

                transportation_allowance = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd11'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
                transportation_allowance = sum([x.get('total') for x in transportation_allowance if x])
                employee_dict['transportation_allowance'] = transportation_allowance

                entertaintement_allowance = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd12'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
                entertaintement_allowance = sum([x.get('total') for x in entertaintement_allowance if x])
                employee_dict['entertaintement_allowance'] = entertaintement_allowance

                name_of_retirement_benefit = income_tax_record.retirement_benefit_fund if income_tax_record.retirement_benefit_fund else ''
                employee_dict['retirement_benefit_fund'] = name_of_retirement_benefit

                retirement_benefits_before92 = income_tax_record.retirement_benefit_upto
                employee_dict['retirement_benefit_upto'] = retirement_benefits_before92

                retirement_benefits_after92 = income_tax_record.retirement_benefit_accured_from
                employee_dict['retirement_benefit_accured_from'] = retirement_benefits_after92

                excess_voluntry_contrib_cpf = income_tax_record.excess_volunatry_contribution_cpf_employer
                employee_dict['excess_volunatry_contribution_cpf_employer'] = excess_voluntry_contrib_cpf

                value_of_benefits_in_kind = income_tax_record.value_benefits_in_kind
                employee_dict['value_benefits_in_kind'] = value_of_benefits_in_kind

                iras_approval_date = datetime.strptime(wizard.company_id.iras_approval_date, DF).strftime(DF) if wizard.company_id.iras_approval_date else " " * 8

                exempt_income_subject_to_remission = income_tax_record.exempt_income

                exempt_remission_income_indicator = income_tax_record.exempt_remission if income_tax_record.exempt_remission else ' '

                period_gross_commision_first_slip = payslip_obj.browse(cr, uid, first_payslip, context=context)
                period_gross_commision_first = period_gross_commision_first_slip.date_from
                peiod_gross_commision_last_slip = payslip_obj.browse(cr, uid, last_payslip, context=context)
                period_gross_commision_last = period_gross_commision_first_slip.date_to

                gross_commision = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd2'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
                gross_commision = sum([x.get('total') for x in gross_commision if x])
                employee_dict['gross_commision'] = gross_commision

                employement_income_for_tax_borne_by_employer = income_tax_record.employement_income_for_tax_borne_by_employer
                employee_dict['employement_income_for_tax_borne_by_employer'] = employement_income_for_tax_borne_by_employer

                fixed_income_tax_liability_borne_by_employer = income_tax_record.fixed_income_tax_liability_borne_by_employer

                employee_income_tax = income_tax_record.employee_income_tax if income_tax_record.employee_income_tax else ' '

                compensation_loss_office = income_tax_record.compensation_loss_office
                employee_dict['compensation_loss_office'] = compensation_loss_office

                contribution_by_employer_pension_pf = income_tax_record.contribution_by_employer_pension_pf
                employee_dict['contribution_by_employer_pension_pf'] = contribution_by_employer_pension_pf

                gain_profit_share_option = income_tax_record.gain_profit_share_option

                employee_voluntary_contribution_cpf = income_tax_record.employee_voluntary_contribution_cpf

                other_allowance = payslip_line_obj.search_read(cr, uid, [('irab_code', '=', 'd13'), ('id', 'in', employee_payslip_line_ids)], ['total'], context=context)
                other_allowance = sum([x.get('total') for x in other_allowance if x])
                employee_dict['other_allowance'] = other_allowance

                others = int(gross_commision or 0) + int(pension_val or 0) + int(transportation_allowance or 0) + int(entertaintement_allowance or 0) + int(other_allowance or 0) \
                        + int(gratuity_val or 0) + int(retirement_benefits_after92 or 0) + int(contribution_by_employer_pension_pf or 0) + int(excess_voluntry_contrib_cpf or 0) \
                        + int(gain_profit_share_option or 0) + int(value_of_benefits_in_kind or 0)
                #Value must be the sum of items 31, 34, 35, 36, 37,38, 40, 41, 42, 43 and 44 Drop the decimals of the sum in items 31, 34, 35, 36, 37, 38, 40, 41, 42, 43 and 44.
                #i.e. sum of Gross Commission, Pension, Transport allowance, Entertainment allowance, Other allowances, Gratuity/ Notice Pay/ Ex-gratia payment/ Others,
                #Retirement benefits accrued from 1993, Contributions made by employer to any pension / provident fund constituted outside Singapore,
                #Excess / voluntary contribution to CPF by employer, Gains and profits from share options for S10 (1) (b), Value of benefits-in- kinds

                benefits_in_kind = income_tax_record.benefits_in_kind if income_tax_record.benefits_in_kind else ' '
                section_applicable = income_tax_record.section_applicable if income_tax_record.section_applicable else ' '
                employee_income_tax = income_tax_record.employee_income_tax if income_tax_record.employee_income_tax else ' '
                gratuity_val_indicator = 'Y' if gratuity_val else 'N'

                wheather_compensation_loss_office = 'Yes' if income_tax_record.wheather_compensation_loss_office else 'No'
                employee_dict['wheather_compensation_loss_office'] = wheather_compensation_loss_office
                employee_dict['date_of_approval'] = income_tax_record.date_of_approval

                iras_approval = 'Y' if wizard.company_id.iras_approval else 'N'
                cessation_provision_applicable = income_tax_record.cessation_provision_applicable if income_tax_record.cessation_provision_applicable else ' '
                from_ir8s = income_tax_record.from_ir8s if income_tax_record.from_ir8s else ' '
                period_gross_commision_first_val = (datetime.strptime(period_gross_commision_first, DF).strftime("%Y%m%d") if gross_commision else " "*8 )
                period_gross_commision_last_val = (datetime.strptime(period_gross_commision_last, DF).strftime("%Y%m%d") if gross_commision else " "*8)
                date_of_approval_director = datetime.strptime(income_tax_record.date_of_approval_director, DF).strftime("%Y%m%d") if income_tax_record.date_of_approval_director else (" "*8)

                date_of_commencement_val = datetime.strptime(income_tax_record.date_of_commencement, DF).strftime("%d/%m/%Y") if income_tax_record.date_of_commencement else " "*8
                employee_dict['date_of_commencement'] = date_of_commencement_val

                date_of_cessation_posted_overseas_val = datetime.strptime(income_tax_record.date_of_cessation_posted_overseas, DF).strftime("%Y-%m-%d") if income_tax_record.date_of_cessation_posted_overseas else " "*8
                employee_dict['date_of_cessation_posted_overseas'] = date_of_cessation_posted_overseas_val
                date_of_declaration_of_bonus_val = datetime.strptime(income_tax_record.date_of_declaration_of_bonus, DF).strftime("%m/%d/%Y") if income_tax_record.date_of_declaration_of_bonus else " "*8

        print "\n\nwizard_records ::: ", wizard_records
        return wizard_records

class wrapped_report_sg_ir8a(osv.AbstractModel):
    _name = 'report.l10n_sg_payroll.report_sg_ir8a'
    _inherit = 'report.abstract_report'
    _template = 'l10n_sg_payroll.report_sg_ir8a'
    _wrapped_report_class = sg_ir8a_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: