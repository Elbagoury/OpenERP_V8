# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF

class income_tax_details(models.Model):
    _name = "income.tax.detail"
    _rec_name = 'assesment_year_id'

        #IR8A Related fields
    assesment_year_id = fields.Many2one('assesment.year', 'Assesment Year')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    directories_fee = fields.Float('18. Directors Fee')
    date_of_approval_director = fields.Date("50. Date of Approval of directories fee")
    gain_profit = fields.Float("19(a). Gains & Profit from Share Options For S10 (1) (g)")
    exempt_income = fields.Float("20. Exempt Income/ Income subject to Tax Remission")
    exempt_remission = fields.Selection([('1', 'Tax Remission on Overseas Cost of Living Allowance (OCLA)'), ('2', 'Tax remission on Operation Headquarters (OHQ)'), ('3', 'Seaman'), ('4', 'Exemption'), ('N', 'Not Applicable')], string="30. Exempt/ Remission income Indicator", default="N")
    from_ir8s = fields.Selection([('Y', 'Yes'), ('N', 'No')], "29. Form IR8S", default="N")
    pension = fields.Float("34. Pension")
    insurance = fields.Float("15. Insurance")
    gratuity_payment = fields.Selection([('Y', 'Yes'), ('N', 'No')], "26. Gratuity/ Notice Pay/ Ex-gratia payment/ Others")
    wheather_compensation_loss_office = fields.Selection([('Y', 'Yes'), ('N', 'No')], "27. Compensation for loss of office", default="N")
    approve_obtain_from_ir8s = fields.Selection([('Y', 'Yes'), ('N', 'No')], "27(a). Approval obtained from IRAS")
    date_of_approval = fields.Date("27(b). Date of approval")
    compensation_loss_office = fields.Float("38(a). Compensation for loss of office")
    gratuity_payment_amount = fields.Float("38. Gratuity/ Notice Pay/ Ex-gratia payment/ Others")
    retirement_benefit_fund = fields.Char("51. Name of fund for Retirement benefits")
    retirement_benefit_upto = fields.Float("39. Retirement benefits accrued up to 31.12.92")
    retirement_benefit_accured_from = fields.Float("40. Retirement benefits accrued from 1993")
    benefits_in_kind = fields.Selection([('Y', 'Benefits-in-kind received'), ('N', 'Benefits-in-kind not received')], "23. Benefits-in-kind")
    section_applicable = fields.Selection([('Y', 'Yes'), ('N', 'No')], "24. Section 45 applicable")
    contribution_by_employer_pension_pf = fields.Float("41. Contributions made by employer to any pension / provident fund constituted outside Singapore")
    excess_volunatry_contribution_cpf_employer = fields.Float(" 42. Excess / voluntary contribution to CPF by employer")
    gain_profit_share_option = fields.Float("43. Gains and profits from share options for S10 (1) (b)")
    value_benefits_in_kind = fields.Float("44. Value of benefits-in- kinds")
    employee_voluntary_contribution_cpf = fields.Float("45. E'yees voluntary contribution to CPF obligatory by contract of employment (overseas posting)")
    employement_income_for_tax_borne_by_employer = fields.Float("21. Amount of employment income for which tax is borne by employer")
    fixed_income_tax_liability_borne_by_employer = fields.Float("22. Fixed Amount of income tax liability for which tax borne by employee")
    employee_income_tax = fields.Selection([('F', 'Tax fully borne by employer on employement income only'),
                                             ('P', 'Tax partially borne by employer on certain employment income items'),
                                             ('H', 'A fixed amount of income tax liability borne by employee, Not applicable if income tax is fully paid by employee'),
                                             ('N', 'Not applicable')], "25. Employees Income Tax borne by employer")
    cessation_provision_applicable = fields.Selection([('Y', 'Applicable'), ('N', 'Not Applicable')], '28. Cessation Provisions')
    date_of_commencement = fields.Date('47. Date of Commencement')
    date_of_cessation_posted_overseas = fields.Date('48. Date of Cessation/ Posted overseas')
    date_of_declaration_of_bonus = fields.Date('49. Date of declaration of bonus')


        #'mbmf': fields.float(),
        #'donation': fields.float(),
        #'cpf_designated_person_provident_fund': fields.float(),
        #'insurance': fields.float(),

        # IR8S Related fields

#         'cpf_capping_indicator':
#         'singapore_permanent_resident_status':
#         'approval_has_been_obtained_cpf_board':
#         'indicator_for_cpf_contribution':
#         'employer_contribution':
#         'employee_contribution':
#         'additional_wage':
#         'date_of_payment_for_additional_wage':
#         'amount_of_refund_applicable_to_employers_contribution':
#         'amount_of_refund_applicable_to_employee_contribution':
#         'date_of_refund_given_employer':
#         'date_of_refund_given_employee':
#         'refund_employer_interest_contribution':
#         'refund_employee_interest_contribution':

    @api.constrains('assesment_year_id', 'employee_id')
    def _check_unique_income_tax(self):
        record = self[0]
        search_res = self.search([('assesment_year_id', '=', record.assesment_year_id.id), ('employee_id', '=', record.employee_id.id)])
        print "\n\nsearch_res are ::: ", search_res
        if len(search_res) > 1:
            raise Warning("You can not have two entry of Income Tax for same assesment year")
        return True

    @api.constrains('exempt_income', 'exempt_remission')
    def _check_exempt_remission(self):
        for record in self:
            if not record.exempt_income:
                return True
            if record.exempt_income and record.exempt_remission not in ['1', '2', '3', '4']:
                raise Warning("You have to choose Exempt/ Remission income Indicator from Tax Remission on Overseas Cost of Living Allowance (OCLA), Tax remission on Operation Headquarters (OHQ), Seaman, Exemption if Exempt Income/ Income subject to Tax Remission having some value.")
        return True

    #TODO: To check all wanings
    @api.constrains('employement_income_for_tax_borne_by_employer', 'fixed_income_tax_liability_borne_by_employer', 'employee_income_tax')
    def _check_employee_income_tax(self):
        print "\n\n Inside employee income tax :::>>>>>> "
        #record = self.browse(cr, uid, ids[0], context=context)
        for record in self:
            if record.employee_income_tax in ['F', 'H'] and record.employement_income_for_tax_borne_by_employer:
                raise Warning("Field 'Amount of employment income for which tax is borne by employer' must be blank if 'Amount of employment income for which tax is borne by employer' is  'Tax fully borne by employer on employment income only' or 'A fixed amount of income tax liability borne by employee. Not applicable if income tax is fully paid by employee'")
            if record.employee_income_tax in ['F', 'P'] and record.fixed_income_tax_liability_borne_by_employer:
                raise Warning("Field 'Fixed Amount of income tax liability for which tax borne by employee' must be blank if field '2. Employee’s Income Tax borne by employer' is either 'Tax fully borne by employer on employment income only' or 'Tax partially borne by employer on certain employment income items'.")
            if record.employement_income_for_tax_borne_by_employer and record.employee_income_tax != 'P':
                raise Warning("Field 'Employee's Income Tax borne by employer' Must be 'Tax partially borne by employer on certain employment income items' if 'Amount of employment income for which tax is borne by employer' not blank.")
            if record.fixed_income_tax_liability_borne_by_employer and record.employee_income_tax != 'H':
                raise Warning("Field 'Employee's Income Tax borne by employer' Must be 'A fixed amount of income tax liability borne by employee. Not applicable if income tax is fully paid by employee' if 'Fixed Amount of income tax liability for which tax borne by employee' not blank.")
            return True

    @api.constrains('gratuity_payment', 'gratuity_payment_amount')
    def _check_gratuity_payment(self):
        for record in self:
            if record.gratuity_payment_amount and record.gratuity_payment != 'Y':
                raise Warning("Gratuity/ Notice Pay/ Ex-gratia payment/ Others must be Gratuity/ payment in lieu of notice/ex-gratia paid if Field Gratuity/ Notice Pay/ Ex-gratia payment/ Others is not blank.")
        return True

    @api.constrains('wheather_compensation_loss_office', 'compensation_loss_office', 'approve_obtain_from_ir8s')
    def _check_wheather_compensation_loss_office(self):
        for record in self:
            if record.approve_obtain_from_ir8s and record.wheather_compensation_loss_office != 'Y':
                raise Warning("Compensation for loss of office must be Compensation / Retrenchment benefits paid If Approval obtained from IRAS has any value.")
            if record.compensation_loss_office and record.wheather_compensation_loss_office != 'Y':
                raise Warning("Item 27. Compensation for loss of office must be Compensation / Retrenchment benefits paid If Item 38(a) Compensation for loss of office has value")
        return True

    @api.constrains('date_of_approval', 'approve_obtain_from_ir8s')
    def _check_approve_obtain_from_ir8s(self):
        for record in self:
            if record.date_of_approval and record.approve_obtain_from_ir8s != 'Y':
                raise Warning("Approval obtained from IRAS must have value 'Yes' if Date of approval is not blank.")
        return True

    @api.constrains("cessation_provision_applicable", "date_of_commencement", "date_of_cessation_posted_overseas", "assesment_year_id")
    def _check_cessation_provision_applicable(self):
        for record in self:
            if not record.cessation_provision_applicable and record.date_of_commencement and record.date_of_commencement < '01-01-1969' \
                and record.date_of_cessation_posted_overseas and datetime.strptime(record.date_of_cessation_posted_overseas, DF).year == record.assesment_year_id.assessment_year_value:
                raise Warning("Cessation Provisions Cannot be blank if item 47 (Date of commencement) is before 01/01/1969 and item 48 (Date of cessation) is not blank and is within the Basis year in the Header Record.")
        return True

    @api.constrains("date_of_commencement", "cessation_provision_applicable", "assesment_year_id", "date_of_cessation_posted_overseas")
    def _check_date_of_commencement(self):
        for record in self:
            if not record.date_of_commencement and record.cessation_provision_applicable == 'Y':
                raise Warning("Date of Commencement Cannot be blank if 'Cessation Provisions' is Applicable.")
            if record.date_of_commencement:
                print "\n\nrecord.date_of_commencement ::: ", record.date_of_commencement, type(record.date_of_commencement)
                if fields.Date.from_string(record.date_of_commencement) > fields.Date.from_string("1969-01-01"):
                    raise Warning("Date of Commencement must be before 01/01/1969 if item 28 (Cessation Provisions) is ‘Applicable’.")
                commencement_year = datetime.strptime(record.date_of_commencement, DF).year
                if commencement_year > record.assesment_year_id.assessment_year_value and commencement_year < datetime.strptime(record.date_of_cessation_posted_overseas, DF).year:
                    raise Warning("Date of Commencement: YYYY cannot be later than the Basis year in the Header Record and must be earlier than or equal to item 48 (Date of Cessation/ Posted overseas).")
        return True

    @api.constrains("date_of_cessation_posted_overseas", "cessation_provision_applicable", "assesment_year_id", "date_of_commencement")
    def _check_date_of_cessation_posted_overseas(self):
        for record in self:
            if not record.date_of_cessation_posted_overseas and record.cessation_provision_applicable == 'Y':
                raise Warning("Date of Cessation/ Posted overseas Cannot be blank if item 28 (Cessation Provisions) is ‘Applicable’.")
            if record.date_of_cessation_posted_overseas:
                cessation_overseas_year = datetime.strptime(record.date_of_cessation_posted_overseas, DF).year
                if cessation_overseas_year != record.assesment_year_id.assessment_year_value and cessation_overseas_year < datetime.strptime(record.date_of_commencement, DF).year:
                    raise Warning("Date of Cessation/ Posted overseas: YYYY must be equal to the Basis year in the Header Record and YYYY must be within the Basis year in the Header Record and later than or equal to item 47 (Date of commencement).")
        return True

    @api.constrains("date_of_declaration_of_bonus", "assesment_year_id")
    def _check_date_of_declaration_of_bonus(self):
        for record in self:
            if record.date_of_declaration_of_bonus and datetime.strptime(record.date_of_declaration_of_bonus, DF).year != record.assesment_year_id.assessment_year_value:
                raise Warning("Date of declaration of bonus, YYYY must be equal to the Basis year in the Header Record.")
        return True

    #_constraints = [
    #        (_check_unique_income_tax, 'Error! You can not have two entry of Income Tax for same assesment year', ['assesment_year_id', 'employee_id']),
    #        (_check_exempt_remission, 'Error! You have to choose Exempt/ Remission income Indicator from Tax Remission on Overseas Cost of Living Allowance (OCLA), Tax remission on Operation Headquarters (OHQ), Seaman, Exemption if Exempt Income/ Income subject to Tax Remission having some value.', ['exempt_income', 'exempt_remission']),
#             (employee_income_tax, "Error! You must have Amount of employment income blank for which tax is borne by employer blank if you choose Employees Income Tax borne by employer from \
#                                 Tax fully borne by employer on employement income only or A fixed amount of income tax liability borne by employee, Not applicable if income tax is fully paid by employee \
#                                 OR you must have Fixed Amount of income tax liability for which tax borne by employee field blank if you choose Employees Income Tax borne by employer from \
#                                 Tax fully borne by employer on employement income only, Tax partially borne by employer on certain employment income items \
#                                 OR Employees Income Tax borne by employer must be Tax partially borne by employer on certain employment income items if Amount of employment income for which tax is borne by employer is not blank \
#                                 OR Employees Income Tax borne by employer must be A fixed amount of income tax liability borne by employee. Not applicable if income tax is fully paid by employee if Fixed Amount of income tax liability for which tax borne by employee is not blank",
#                                 ['employement_income_for_tax_borne_by_employer', 'fixed_income_tax_liability_borne_by_employer', 'employee_income_tax']),
    #        (_check_gratuity_payment, "Error! Gratuity/ Notice Pay/ Ex-gratia payment/ Others must be Gratuity/ payment in lieu of notice/ex-gratia paid if Field Gratuity/ Notice Pay/ Ex-gratia payment/ Others is not blank.", ['gratuity_payment', 'gratuity_payment_amount']),
    #        (_check_wheather_compensation_loss_office, "Error! Compensation for loss of office must be Compensation / Retrenchment benefits paid If Approval obtained from IRAS is true OR Compensation for loss of office has value", ['wheather_compensation_loss_office', 'compensation_loss_office', 'approve_obtain_from_ir8s']),
    #        (_check_approve_obtain_from_ir8s, "Error! Approval obtained from IRAS must have value Approval obtained from IRAS if Date of approval is not blank.", ['date_of_approval', 'approve_obtain_from_ir8s']),
    #        (_check_cessation_provision_applicable, "\nError! Cessation Provisions Cannot be blank if item 47 (Date of commencement) is before 01/01/1969 and item 48 (Date of cessation) is not blank and is within the Basis year in the Header Record.", ["cessation_provision_applicable", "date_of_commencement", "date_of_cessation_posted_overseas", "assesment_year_id"]),
    #        (_check_date_of_commencement, "\nError! Date of Commencement 1. Cannot be blank and must be before 01/01/1969 if item 28 (Cessation Provisions) is ‘Y’ \n 2. YYYY cannot be later than the Basis year in the Header Record and must be earlier than or equal to item 48 (Date of Cessation/ Posted overseas).", ["date_of_commencement", "cessation_provision_applicable", "assesment_year_id", "date_of_cessation_posted_overseas"]),
    #        (_check_date_of_cessation_posted_overseas, "\nError! Date of Cessation/ Posted overseas 1. Cannot be blank if item 28 (Cessation Provisions) is ‘Y’. \n 2. 2. YYYY must be equal to the Basis year in the Header Record. 3. 3. YYYY must be within the Basis year in the Header Record and later than or equal to item 47 (Date of commencement).", ["date_of_cessation_posted_overseas", "cessation_provision_applicable", "assesment_year_id", "date_of_commencement"]),
    #        (_check_date_of_declaration_of_bonus, "\nError! Date of declaration of bonus, YYYY must be equal to the Basis year in the Header Record.", ["date_of_declaration_of_bonus", "assesment_year_id"]),
    #]