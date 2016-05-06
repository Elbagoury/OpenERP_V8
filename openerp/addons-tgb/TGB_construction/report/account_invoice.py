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

import time

from openerp.report import report_sxw

class TGB_account_invoice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(TGB_account_invoice, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'amount_word':self._amount_word,
            'gst_amount':self._gst_amount,
            'previous_claim':self._previous_claim,
            'get_time_claim':self._get_time_claim,
            'old_claim_gst':self._get_old_claim_gst,
            'get_variation_amount':self._get_variation_amount,
            'get_this_amount':self._get_this_amount,
            'get_gst_amount':self._get_gst_amount,
            'get_being_work_todate':self._get_being_work_todate,
            'get_user_title':self._get_user_title,
            'get_this_claim':self._get_this_claim,
            'get_additional_quotation':self._get_additional_quotation,
            'get_original_contract_sum':self._get_original_contract_sum,
        })

    _this_amount = 0
    _this_gst_amount = 0
    _this_claim = 0

    def _get_this_claim(self):
        return self._this_claim

    def _get_gst_amount(self):
        return self._this_gst_amount
    def _get_user_title(self,user_id):
#         employee_id = self.pool.get('hr.employee').search(self.cr,self.uid,[('user_id','=',user)])
#         if employee_id and len(employee_id)>0:
#             return self.pool.get('hr.employee').browse(self.cr,self.uid,employee_id[0]).job_id.name
        if user_id:
            user = self.pool.get('res.users').browse(cr, 1, user_id)
            return user and user.partner_id and user.partner_id.title and user.partner_id.title.name or ''
        return ''
    
    def _get_being_work_todate(self,o):
        if o.billing_time==1:
            return 'Being Downpayment Claim'
        else:
            return 'Being Work done todate'

    def _get_this_amount(self,o):
        self._previous_claim(o)
        return self._this_amount

    def _get_old_claim_gst(self,o):
        if o.progressive_id:
            old_gst = o.progressive_id.amount_claim_todate*7/100
            return old_gst
        return 0

    def _get_variation_amount(self,o):
        project_id = o.sale_order_id.project_id.id
        variation_order = self.pool.get('sale.order').search(self.cr,self.uid,[('project_id','=',project_id),('is_variation','=',True)])
        variation_amount = 0
        if variation_order and len(variation_order)>0:
            for order in self.pool.get('sale.order').browse(self.cr,self.uid,variation_order):
                variation_amount = variation_amount + order.amount_untaxed + order.scope_amount+order.amount_hr_total+ order.amount_bq_total

        # addition_order = self.pool.get('sale.order').search(self.cr,self.uid,[('project_id','=',project_id),('is_addition','=',True)])
        # if addition_order and len(addition_order)>0:
        #     for order in self.pool.get('sale.order').browse(self.cr,self.uid,addition_order):
        #         variation_amount = variation_amount + order.amount_untaxed + order.scope_amount+order.amount_hr_total+ order.amount_bq_total
        return variation_amount

    def _get_additional_quotation(self,o):
        val = []
        project_id = o.sale_order_id.project_id.id
        additional_ids = self.pool.get('sale.order').search(self.cr,self.uid,[('project_id','=',project_id),('is_addition','=',True)])
        if additional_ids and len(additional_ids)>0:
            for order in self.pool.get('sale.order').browse(self.cr,self.uid,additional_ids):
                amount = order.amount_untaxed + order.scope_amount+order.amount_hr_total+ order.amount_bq_total
                val.append([order.subject,amount])
        return val

    def _get_original_contract_sum(self,o):
        total = 0
        for line in o.sale_order_id.order_line:
            if line.line_type=='normal':
                total+=line.price_subtotal
        return total

    def _amount_word(self,amount):
        from num2words import num2words
        amount = round(amount,2)
        amount_decimal = round((amount-int(amount))*100,0)
        amount_word = num2words(int(amount)).replace(' and','')
        if amount_decimal>0:
            amount_decimal_word = num2words(amount_decimal).replace(' and','')
            amount_word = amount_word +' AND CENTS '+ amount_decimal_word
        return_val = (amount_word+' ONLY').upper()
        return return_val

    def _gst_amount(self,amount):
        return amount*7/100
    def _previous_claim(self,o):
        res = []
        if o.is_progressive:
            being_work_todate = o.progressive_id.amount_claim_todate
            retention = 0
            payment_claimed = 0
            if not o.progressive_id.is_deposit_billing:
                if o.progressive_id.retention_required:
                    des = 'Less '
                    capped_amount = o.sale_order_id.capped_amount
                    if o.progressive_id.retention_type == 'P':
                        des +=str(o.progressive_id.retention_percent)+'% Retention Sum'
                        retention = o.progressive_id.amount_claim_todate*o.progressive_id.retention_percent/100
                    elif o.progressive_id.retention_type=='A':
                        des +=str(o.progressive_id.retention_amount)+' Retention Sum'
                        retention = o.progressive_id.retention_amount
                    if capped_amount>0 and capped_amount<retention:
                            retention = capped_amount
                    res.append([des,o.company_id.currency_id.symbol + ' ' +'(' + str(retention) +')'])

            previous_claim = self.pool.get('account.invoice').search(self.cr,self.uid,[('sale_order_id','=',o.sale_order_id.id),('is_progressive','=',True),
                                                                                       ('billing_time','<',o.billing_time)])
            if previous_claim and len(previous_claim)>0:
                previous_claim.sort()
                for invoice in self.pool.get('account.invoice').browse(self.cr,self.uid,previous_claim):
                    claim_times = 1
                    end_billing_time = str(invoice.billing_time)
                    end = end_billing_time[len(end_billing_time)-1]
                    if end =='1':
                        end = end +'st'
                    elif end =='2':
                        end =  end +'nd'
                    elif end =='3':
                        end = end + 'rd'
                    else:
                        end = end + 'th'
                    res.append(['Less '+ end + ' Progress Claim',o.company_id.currency_id.symbol + ' ' +'(' +  str(invoice.progressive_id.amount_for_this_claim)+')'])
                    payment_claimed += invoice.progressive_id.amount_for_this_claim
            this_claim = being_work_todate - retention - payment_claimed
            if not o.billing_time ==1:
                self._this_claim = this_claim
            gst_amount = this_claim*7/100
            # res.append(['Add 7% GST',gst_amount])
            self._this_gst_amount = gst_amount
            self._this_amount = this_claim+gst_amount
        return res

    def _get_time_claim(self,o, context=None):
        number= str(o.billing_time)
        if o.progressive_id.is_deposit_billing:
            return 'Downpayment'
        end = number[len(number)-1]
        if end =='1':
            return number+'st Progress'
        elif end =='2':
            return number +'nd Progress'
        elif end =='3':
            return number + 'rd Progress'
        else:
            return number + 'th Progress'
        return str(billing_time) + 'th Progress'


report_sxw.report_sxw('report.TGB.account.invoice', 'account.invoice', 'addons/TGB_construction/report/account_invoice.rml', parser=TGB_account_invoice, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: