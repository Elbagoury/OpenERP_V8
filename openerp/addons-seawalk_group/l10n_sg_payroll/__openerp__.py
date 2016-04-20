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
{
    'name' : 'Singapore Payroll',
    'version' : '1.0',
    'author' : 'LevelFive Solutions',
    'category' : 'Human Resources',
    'description' : """
Singapore Payroll
====================================

    This Module manages Singapore Payroll system as per Singapore
Government rules.
- Comapny details as per Singaporean rules
- Employee details as per Singaporean payroll rules
- Salary rules based on singapore localization
- CPF declaration and calculation in employee payslip
- eCPF submission to government
- IR8A esubmission

    """,
    'website': 'http://www.lfsolutions.net',
    'images' : [],
    'depends' : ['hr_payroll'],
    'data': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'wizard/ecpf_file_view.xml',
        'wizard/eir8a_file_view.xml',
        'l10n_sg_payroll_view.xml',
        'donation_data.xml',
        'l10n_sg_payroll_data.xml',
        'sequence.xml',
        'view/report_sg_payslipdetails.xml',
        'view/report_sg_ir8a.xml',
        #'sg_payroll_report.xml',
        'report/lf_style.xml',
        'l10n_sg_payroll_report.xml',
        'report/payslip_report.xml',
        #'l10n_sg_payroll_workflow.xml',
    ],
    'demo': ['l10n_sg_payroll_demo.xml'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: