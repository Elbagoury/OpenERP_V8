# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP SA (<http://openerp.com>).
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

import base64
import re
import threading
from openerp.tools.safe_eval import safe_eval as eval
from openerp import tools
import openerp.modules
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import datetime
import time
import calendar

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
    def _fs_end_date(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for emp in self.browse(cursor, user, ids, context=context):
            res[emp.id] = emp.director_appt_date or False
        return res
    
    def _estimate_chargable_income_date(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for emp in self.browse(cursor, user, ids, context=context):
            res[emp.id] = emp.director_appt_date or False
        return res
    
    def _annual_return_date(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for emp in self.browse(cursor, user, ids, context=context):
            res[emp.id] = emp.director_appt_date or False
        return res
    
    def _sole_proprietary_partnership_date(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for emp in self.browse(cursor, user, ids, context=context):
            res[emp.id] = emp.director_appt_date or False
        return res
    
    def _tax_form_cs(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for emp in self.browse(cursor, user, ids, context=context):
            res[emp.id] = emp.director_appt_date or False
        return res
    
    def _submit_monthly_cpf(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for emp in self.browse(cursor, user, ids, context=context):
            res[emp.id] = 0.0 or False
        return res
    
    def _compute_submit_yearly_staff_salary(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for emp in self.browse(cursor, user, ids, context=context):
            res[emp.id] = 0.0 or False
        return res
    
    _columns = {
        'company_roc': fields.char('Company ROC',size=1024),
        'nric': fields.char('NRIC',size=1024),
        'signature_specimen': fields.binary('Signature Specimen'),
        'hp': fields.char('HP',size=1024),
        'office_no': fields.char('Office No',size=1024),
        'street_personal': fields.char('Street'),
        'street2_personal': fields.char('Street2'),
        'zip_personal': fields.char('Zip', size=24, change_default=True),
        'city_personal': fields.char('City'),
        'state_personal_id': fields.many2one("res.country.state", 'State', ondelete='restrict'),
        'country_personal_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
        'street_secretary': fields.char('Street'),
        'street2_secretary': fields.char('Street2'),
        'zip_secretary': fields.char('Zip', size=24, change_default=True),
        'city_secretary': fields.char('City'),
        'state_secretary_id': fields.many2one("res.country.state", 'State', ondelete='restrict'),
        'country_secretary_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
        'period_of_year':fields.selection([('month','Month'),('quarter','Quarter'),('half_year','Half year'),('year','Year')],'Period or Year'),
        'document_collection_ids':fields.one2many('document.collection','partner_id','Document Collection'),
        'tracking_collection_ids':fields.one2many('document.collection','partner_traking_id','Tracking Collection'),
        'account_adjustment_ids':fields.one2many('document.collection','partner_adjustment_id','Account Adjustment'),
        'account_finalization_ids':fields.one2many('document.collection','partner_finalization_id','Account Finalization'),
        'estimate_chargeable_income_ids':fields.one2many('document.collection','partner_estimate_id','Estimate Chargeable Income'),
        'annual_report_preparation_ids':fields.one2many('document.collection','partner_annual_id','Annual Report Preparation'),
        
        'chairman':fields.boolean('Chairman'),
        
        'uen':fields.char('UEN'),
        'chinese_name':fields.char('Chinese Name'),
        'incorporation_date':fields.date('Incorporation Date'),
        'director_appt_date':fields.date('Director Appt Date'),
        'secretary_appt_date':fields.date('Secretary Appt Date'),
        'employment':fields.selection([('employee','Employee'),('shareholder','Shareholder')],'Employment'),
        'paid_up_capital':fields.float('Paid Up Capital'),
        'c_status':fields.selection([('live','Live'),('employeed','Employeed')],'C Satus'),
        'race':fields.char('Race'),
        'country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
        'block_house_no':fields.char('Block/House No'),
        'street_name': fields.char('Street Name'),
        'level_no': fields.char('Level No'),
        'unit_no': fields.char('Unit No'),
        'postal_code': fields.char('Postal Code'),
        'period_year':fields.selection([('period','Period'),('year','Year')],'Period or Year'),
        'fs_start_date':fields.date('FS Start Date'),
        'fs_end_date':fields.function(_fs_end_date, string='FS End Date', type='date'),
        'axp_report':fields.date('AXP Report'),
        'estimate_chargable_income_date':fields.function(_estimate_chargable_income_date,string='Estimate Chargable lncome Date', type='date'),
        'annual_general_meeting_date':fields.date('Annual General Meeting Date'),
        'annual_return_date':fields.function(_annual_return_date,string='Annual Return Date',type='date'),
        'financial_month':fields.many2one('account.period', string='Financial Month'),
        'next_annual_general_meeting_due_date':fields.date('Next Annual General Meeting Due Date'),
        'sole_proprietary_partnership':fields.selection([('sole_proprietary','Sole Proprietary'),('partnership','Partnership')],'Sole Proprietary or Partnership'),
        'last_financiall_year_end':fields.date('Last Financiall Year End'),
        'sole_proprietary_partnership_date':fields.function(_sole_proprietary_partnership_date, string='Tax:Sole Proprietary & Partnership',type='date'),
        'tax_form_cs':fields.function(_tax_form_cs, string='Tax:Form CS (YA)',type='date'),
        'submit_monthly_cpf':fields.function(_submit_monthly_cpf, string='Submit Monthly CPF',type='float'),
        'compute_submit_yearly_staff_salary':fields.function(_compute_submit_yearly_staff_salary, string='Compute & Submit Yearly Staff Salary',type='float'),
        'remarks_1': fields.char('Remarks 1'),
        'remarks_2': fields.char('Remarks 2'),
    }
    
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('period_of_year',False):
            if vals['period_of_year']=='month':
                document_collection_ids = []
                tracking_collection_ids = []
                account_adjustment_ids = []
                account_finalization_ids = []
                estimate_chargeable_income_ids = []
                annual_report_preparation_ids = []
                for seq,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December']):
                    year = int(time.strftime('%Y'))
                    month = seq+1
                    day = calendar.monthrange(year, month)[1]
                    alert_date = datetime.datetime(year,month,day)
                    document_collection_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    tracking_collection_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    account_adjustment_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    account_finalization_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    estimate_chargeable_income_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    annual_report_preparation_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                vals.update({'document_collection_ids':document_collection_ids,
                             'tracking_collection_ids':tracking_collection_ids,
                             'account_adjustment_ids':account_adjustment_ids,
                             'account_finalization_ids':account_finalization_ids,
                             'estimate_chargeable_income_ids':estimate_chargeable_income_ids,
                             'annual_report_preparation_ids':annual_report_preparation_ids})
            if vals['period_of_year']=='quarter':
                document_collection_ids = []
                tracking_collection_ids = []
                account_adjustment_ids = []
                account_finalization_ids = []
                estimate_chargeable_income_ids = []
                annual_report_preparation_ids = []
                for seq,m in enumerate(['First Quarter','Second Quarter', 'Third Quarter','Fourth Quarter']):
                    year = int(time.strftime('%Y'))
                    month = (seq+1)*3
                    day = calendar.monthrange(year, month)[1]
                    alert_date = datetime.datetime(year,month,day)
                    document_collection_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    tracking_collection_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    account_adjustment_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    account_finalization_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    estimate_chargeable_income_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    annual_report_preparation_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                vals.update({'document_collection_ids':document_collection_ids,
                             'tracking_collection_ids':tracking_collection_ids,
                             'account_adjustment_ids':account_adjustment_ids,
                             'account_finalization_ids':account_finalization_ids,
                             'estimate_chargeable_income_ids':estimate_chargeable_income_ids,
                             'annual_report_preparation_ids':annual_report_preparation_ids})
            if vals['period_of_year']=='half_year':
                document_collection_ids = []
                tracking_collection_ids = []
                account_adjustment_ids = []
                account_finalization_ids = []
                estimate_chargeable_income_ids = []
                annual_report_preparation_ids = []
                for seq,m in enumerate(['First Half','Second Half']):
                    year = int(time.strftime('%Y'))
                    month = (seq+1)*6
                    day = calendar.monthrange(year, month)[1]
                    alert_date = datetime.datetime(year,month,day)
                    document_collection_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    tracking_collection_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    account_adjustment_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    account_finalization_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    estimate_chargeable_income_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                    annual_report_preparation_ids.append((0,0,{'name':m,'alert_date':alert_date.strftime('%Y-%m-%d')}))
                vals.update({'document_collection_ids':document_collection_ids,
                             'tracking_collection_ids':tracking_collection_ids,
                             'account_adjustment_ids':account_adjustment_ids,
                             'account_finalization_ids':account_finalization_ids,
                             'estimate_chargeable_income_ids':estimate_chargeable_income_ids,
                             'annual_report_preparation_ids':annual_report_preparation_ids})
            if vals['period_of_year']=='year':
                vals.update({'document_collection_ids':[(0,0,{'name':time.strftime('%Y'),'alert_date':time.strftime('%Y-12-31')})],
                             'tracking_collection_ids':[(0,0,{'name':time.strftime('%Y'),'alert_date':time.strftime('%Y-12-31')})],
                             'account_adjustment_ids':[(0,0,{'name':time.strftime('%Y'),'alert_date':time.strftime('%Y-12-31')})],
                             'account_finalization_ids':[(0,0,{'name':time.strftime('%Y'),'alert_date':time.strftime('%Y-12-31')})],
                             'estimate_chargeable_income_ids':[(0,0,{'name':time.strftime('%Y'),'alert_date':time.strftime('%Y-12-31')})],
                             'annual_report_preparation_ids':[(0,0,{'name':time.strftime('%Y'),'alert_date':time.strftime('%Y-12-31')})]})
        return super(res_partner, self).create(cr, uid, vals, context)
    
    def send_mail(self, cr, uid, lead_email, msg_id,context=None):
        mail_message_pool = self.pool.get('mail.message')
        mail_mail = self.pool.get('mail.mail')
        msg = mail_message_pool.browse(cr, SUPERUSER_ID, msg_id, context=context)
        body_html = msg.body
        # email_from: partner-user alias or partner email or mail.message email_from
        if msg.author_id and msg.author_id.user_ids and msg.author_id.user_ids[0].alias_domain and msg.author_id.user_ids[0].alias_name:
            email_from = '%s <%s@%s>' % (msg.author_id.name, msg.author_id.user_ids[0].alias_name, msg.author_id.user_ids[0].alias_domain)
        elif msg.author_id:
            email_from = '%s <%s>' % (msg.author_id.name, msg.author_id.email)
        else:
            email_from = msg.email_from

        references = False
        if msg.parent_id:
            references = msg.parent_id.message_id

        mail_values = {
            'mail_message_id': msg.id,
            'auto_delete': True,
            'body_html': body_html,
            'email_from': email_from,
            'email_to' : lead_email,
            'references': references,
        }
        email_notif_id = mail_mail.create(cr, uid, mail_values, context=context)
        try:
             mail_mail.send(cr, uid, [email_notif_id], context=context)
        except Exception:
            a = 1
        return True
    
    def send_mail_for_admin(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        partner = user.partner_id
        partner.signup_prepare()
        body = ''
        ngay = time.strftime('%Y-%m-%d')
        sql = '''
            select id from res_partner where id in (select partner_id from document_collection where alert_date<'%(ngay)s')
                or id in (select partner_traking_id from document_collection where alert_date<'%(ngay)s')
                or id in (select partner_adjustment_id from document_collection where alert_date<'%(ngay)s')
                or id in (select partner_finalization_id from document_collection where alert_date<'%(ngay)s')
            group by id
            order by id
        '''%{'ngay':ngay}
        cr.execute(sql)
        partner_ids = [r[0] for r in cr.fetchall()]
        partner_obj = self.pool.get('res.partner')
        
#         doc_obj = self.pool.get('document.collection')
#         doc_ids = doc_obj.search(cr, uid, [('alert_date','<',time.strftime('%Y-%m-%d')),('partner_id','!=',False)],order='partner_id')
        for rp in partner_obj.browse(cr, uid, partner_ids):
            partner_id = False
            temp=0
            for seq,doc in enumerate(rp.document_collection_ids):
                if doc.alert_date<ngay:
                    if temp and doc.partner_id!=partner_id:
                        body+='</p>'
                        temp = 0
                    if doc.partner_id!=partner_id and \
                    (not doc.document_sales_invoice or not doc.document_receipt or not doc.document_payment_voucher or not doc.document_bank_statement or not doc.document_rental_contract or not doc.document_petty_cash):
                        temp = 1
                        body+='''
                            <p><b>%s</b><br>
                        '''%(doc.partner_id.name)
                        partner_id = doc.partner_id
                    if doc.partner_id==partner_id and \
                    (not doc.document_sales_invoice or not doc.document_receipt or not doc.document_payment_voucher or not doc.document_bank_statement or not doc.document_rental_contract or not doc.document_petty_cash):
                        body+='''
                            %s document still pending<br>
                        '''%(doc.name)
                        
            for seq,doc in enumerate(rp.tracking_collection_ids):
                if doc.alert_date<ngay:
                    if temp and doc.partner_traking_id!=partner_id:
                        body+='</p>'
                        temp = 0
                    if doc.partner_traking_id!=partner_id and \
                    (not doc.tracking_sales_invoice or not doc.tracking_receipt or not doc.tracking_payment_voucher or not doc.tracking_bank_statement or not doc.tracking_rental_contract or not doc.tracking_petty_cash):
                        temp = 1
                        body+='''
                            <p><b>%s</b><br>
                        '''%(doc.partner_traking_id.name)
                        partner_id = doc.partner_traking_id
                    if doc.partner_traking_id==partner_id and \
                    (not doc.tracking_sales_invoice or not doc.tracking_receipt or not doc.tracking_payment_voucher or not doc.tracking_bank_statement or not doc.tracking_rental_contract or not doc.tracking_petty_cash):
                        body+='''
                            %s tracking still pending<br>
                        '''%(doc.name)
                        
            for seq,doc in enumerate(rp.account_adjustment_ids):
                if doc.alert_date<ngay:
                    if temp and doc.partner_adjustment_id!=partner_id:
                        body+='</p>'
                        temp = 0
                    if doc.partner_adjustment_id!=partner_id and \
                    (not doc.account_adjustment):
                        temp = 1
                        body+='''
                            <p><b>%s</b><br>
                        '''%(doc.partner_adjustment_id.name)
                        partner_id = doc.partner_adjustment_id
                    if doc.partner_adjustment_id==partner_id and \
                    (not doc.account_adjustment):
                        body+='''
                            %s account adjustment still pending<br>
                        '''%(doc.name)
                        
            for seq,doc in enumerate(rp.account_finalization_ids):
                if doc.alert_date<ngay:
                    if temp and doc.partner_finalization_id!=partner_id:
                        body+='</p>'
                        temp = 0
                    if doc.partner_finalization_id!=partner_id and \
                    (not doc.account_finalization):
                        temp = 1
                        body+='''
                            <p><b>%s</b><br>
                        '''%(doc.partner_finalization_id.name)
                        partner_id = doc.partner_id
                    if doc.partner_finalization_id==partner_id and \
                    (not doc.account_finalization):
                        body+='''
                            %s account finalization still pending<br>
                        '''%(doc.name)
                    
            for seq,doc in enumerate(rp.estimate_chargeable_income_ids):
                if doc.alert_date<ngay:
                    if temp and doc.partner_estimate_id!=partner_id:
                        body+='</p>'
                        temp = 0
                    if doc.partner_estimate_id!=partner_id and \
                    (not doc.document_collection):
                        temp = 1
                        body+='''
                            <p><b>%s</b><br>
                        '''%(doc.partner_estimate_id.name)
                        partner_id = doc.partner_id
                    if doc.partner_estimate_id==partner_id and \
                    (not doc.document_collection):
                        body+='''
                            %s estimate chargeable income still pending<br>
                        '''%(doc.name)
                        
            for seq,doc in enumerate(rp.annual_report_preparation_ids):
                if doc.alert_date<ngay:
                    if temp and doc.partner_annual_id!=partner_id:
                        body+='</p>'
                        temp = 0
                    if doc.partner_annual_id!=partner_id and \
                    (not doc.document_collection):
                        temp = 1
                        body+='''
                            <p><b>%s</b><br>
                        '''%(doc.partner_annual_id.name)
                        partner_id = doc.partner_id
                    if doc.partner_annual_id==partner_id and \
                    (not doc.document_collection):
                        body+='''
                            %s annual report preparation still pending<br>
                        '''%(doc.name)
                        
        if body:
            post_values = {
                'subject': 'Still Pending',
                'body': body,
                'partner_ids': [],
                }
            lead_email = partner.email
            msg_id = self.message_post(cr, uid, [partner.id], type='comment', subtype=False, context=context, **post_values)
            self.send_mail(cr, uid, lead_email, msg_id, context)
        return True
    
#     def send_mail_for_admin(self, cr, uid, context=None):
#         user = self.pool.get('res.users').browse(cr, uid, uid)
#         partner = user.partner_id
#         partner.signup_prepare()
#         body = ''
#         doc_obj = self.pool.get('document.collection')
#         doc_ids = doc_obj.search(cr, uid, [('alert_date','<',time.strftime('%Y-%m-%d')),('partner_id','!=',False)],order='partner_id')
#         partner_id = False
#         temp=0
#         for seq,doc in enumerate(doc_obj.browse(cr, uid, doc_ids)):
#             if temp and doc.partner_id!=partner_id:
#                 body+='</p>'
#                 temp = 0
#             if doc.partner_id!=partner_id and \
#             ((not doc.document_sales_invoice or not doc.document_receipt or not doc.document_payment_voucher or not doc.document_bank_statement or not doc.document_rental_contract or not doc.document_petty_cash) \
#              or (not doc.tracking_sales_invoice or not doc.tracking_receipt or not doc.tracking_payment_voucher or not doc.tracking_bank_statement or not doc.tracking_rental_contract or not doc.tracking_petty_cash)):
#                 temp = 1
#                 body+='''
#                     <p><b>%s</b><br>
#                 '''%(doc.partner_id.name)
#                 partner_id = doc.partner_id
#             if doc.partner_id==partner_id and \
#             (not doc.document_sales_invoice or not doc.document_receipt or not doc.document_payment_voucher or not doc.document_bank_statement or not doc.document_rental_contract or not doc.document_petty_cash):
#                 body+='''
#                     %s document still pending<br>
#                 '''%(doc.name)
#             if doc.partner_id==partner_id and \
#             (not doc.tracking_sales_invoice or not doc.tracking_receipt or not doc.tracking_payment_voucher or not doc.tracking_bank_statement or not doc.tracking_rental_contract or not doc.tracking_petty_cash):
#                 body+='''
#                     %s tracking still pending<br>
#                 '''%(doc.name)
#         if body:
#             post_values = {
#                 'subject': 'Still Pending',
#                 'body': body,
#                 'partner_ids': [],
#                 }
#             lead_email = partner.email
#             msg_id = self.message_post(cr, uid, [partner.id], type='comment', subtype=False, context=context, **post_values)
#             self.send_mail(cr, uid, lead_email, msg_id, context)
#         return True
    
res_partner()

class document_collection(osv.osv):
    _name = "document.collection"
    _columns = {
        'name': fields.char('Name', size=1024, required=True),
        'partner_id':fields.many2one('res.partner','Partner',ondelete='cascade'),
        'alert_date': fields.date('Alert Date'),
        'document_sales_invoice':fields.boolean('Sales Invoice'),
        'document_receipt':fields.boolean('Receipt'),
        'document_payment_voucher':fields.boolean('Payment Voucher'),
        'document_bank_statement':fields.boolean('Bank Statement'),
        'document_rental_contract':fields.boolean('Rental Contract'),
        'document_petty_cash':fields.boolean('Petty Cash'),
        
        'partner_traking_id':fields.many2one('res.partner','Partner',ondelete='cascade'),
        'tracking_sales_invoice':fields.boolean('Sales Invoice'),
        'tracking_receipt':fields.boolean('Receipt'),
        'tracking_payment_voucher':fields.boolean('Payment Voucher'),
        'tracking_bank_statement':fields.boolean('Bank Statement'),
        'tracking_rental_contract':fields.boolean('Rental Contract'),
        'tracking_petty_cash':fields.boolean('Petty Cash'),
        
        'partner_adjustment_id':fields.many2one('res.partner','Partner',ondelete='cascade'),
        'account_adjustment':fields.boolean('Account Adjustment Check Box (Monthly)'),
        
        'partner_finalization_id':fields.many2one('res.partner','Partner',ondelete='cascade'),
        'account_finalization':fields.boolean('Account Finalization Check Box (Yearly)'),
        
        'partner_estimate_id':fields.many2one('res.partner','Partner',ondelete='cascade'),
        'partner_annual_id':fields.many2one('res.partner','Partner',ondelete='cascade'),
        'document_collection':fields.boolean('Document Collection'),
    }
    _defaults = {
             }
document_collection()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: