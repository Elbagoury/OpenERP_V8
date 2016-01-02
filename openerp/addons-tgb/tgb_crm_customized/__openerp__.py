# -*- coding: utf-8# -*- coding: utf-8 -*-
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
    'name': 'TGB CRM',
    'version': '1.0',
    'category': 'TGB',
    'sequence': 1,
    'depends': ['sale','account','hr','report_aeroo','web_digital_sign'],
    'data': [
        'report/agm/agm_dormant/agm_dormant_report_view.xml',
        'report/agm/agm_dormant/example/example_report_view.xml',
        'report/agm/agm_format_documents/1st_agm_one_director/1st_agm_one_director_report_view.xml',
        'report/agm/agm_format_documents/1st_agm_two_directors/1st_agm_two_directors_report_view.xml',
        'report/agm/agm_format_documents/subsequent_year_agm_two_directors/subsequent_year_agm_two_directors_report_view.xml',
        'report/agm/agm_strike_off_templates/agm_strike_off_templates_report_view.xml',
        'report/agm/agm_ye_blank/agm_ye_blank_report_view.xml',
        'report/eci_template/eci_template_report_view.xml',
        'report/appointment_letters/appointment_letters_report_view.xml',
        'report/appointment_of_secretary/appointment_of_secretary_report_view.xml',
        'report/change_of_company_name/change_of_company_name_report_view.xml',
        'report/incorporation_1st_resolution_two_directors/1st_directors_resolution_format/1st_directors_resolution_format_report_view.xml',
        'report/incorporation_1st_resolution_two_directors/forms_45_49/forms_45_49_report_view.xml',
        'report/incorporation_1st_resolution_two_directors/share_certificates_one_director_format/share_certificates_one_director_format_report_view.xml',
        'report/incorporation_1st_resolution_two_directors/share_certificates_two_director_format/share_certificates_two_director_format_report_view.xml',
        'report/issue_shares/issue_shares_report_view.xml',
        'report/resignation_of_director_and_secretary/resignation_of_director_and_secretary_report_view.xml',
        'report/resolution_form/page_01/page_01_report_view.xml',
        'report/resolution_form/page_02/page_02_report_view.xml',
        'report/resolution_form/page_03/page_03_report_view.xml',
        'report/resolution_form/page_04/page_04_report_view.xml',
        'report/resolution_form/page_05/page_05_report_view.xml',
        'report/resolution_form/page_06/page_06_report_view.xml',
        'report/resolution_form/page_07/page_07_report_view.xml',
        'report/resolution_form/page_08/page_08_report_view.xml',
        'report/resolution_form/page_09/page_09_report_view.xml',
        'report/resolution_form/page_10/page_10_report_view.xml',
        'report/resolution_form/page_11/page_11_report_view.xml',
        'report/resolution_form/page_12/page_12_report_view.xml',
        'report/resolution_form/page_13/page_13_report_view.xml',
        'report/resolution_form/page_14/page_14_report_view.xml',
        'report/share_transfer/share_transfer_report_view.xml',
        'report/share_transfer/format_egm_dated_xxxx/format_egm_dated_xxxx_report_view.xml',
        'report/share_transfer/format_share_transfer_form/format_share_transfer_form_report_view.xml',
        'report/strike_off_egm_templates/strike_off_egm_templates_report_view.xml',
        'report/strike_off_egm_templates/strike_off_sample/strike_off_sample_report_view.xml',
        'wizard/report_wizard_view.xml',
        'res_partner_view.xml',
        'hr_employee_view.xml',
        'schedule.xml',
    ],
    'css' : [
    ],
    'qweb': [
    ],
    'js': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: -*-