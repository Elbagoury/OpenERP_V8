# -*- coding: utf-8 -*-

import openerp
from openerp import models, fields, api,_

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class project_progressive_billing(osv.osv):

    _inherit = ['mail.thread']
    _name ='progressive.billing'


    def _get_default_currency(self, cr, uid, context=None):
        currency_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        return currency_id


    def action_approve_billing(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'open'})
        for billing in self.browse(cr,uid,ids):
            if billing.sale_order_id:
                self.pool.get('sale.order').write(cr,uid,billing.sale_order_id.id,{'billing_time':billing.sale_order_id.billing_time + 1})
                for line in billing.line_ids:
                    if line.sale_order_line_id:
                        self.pool.get('sale.order.line').write(cr,uid,line.sale_order_line_id.id,{'billed_percent':line.total_work_up_to_date})

        return True

    def _total_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for billing in self.browse(cr, uid, ids, context=context):
            total_contract_sum=0
            amount_claim_todate = 0
            less_rentention = 0
            less_payment_claimed = 0
            amount_for_this_claim = 0
            for detail in billing.line_ids:
                total_contract_sum+=detail.contract_sum
                amount_claim_todate+=detail.total_work_to_date
                amount_for_this_claim+=detail.this_valuation
            less_rentention+= total_contract_sum*5/100
            less_payment_claimed = total_contract_sum-less_payment_claimed
            res[billing.id] = {'amount_claim_todate':amount_claim_todate,
                               'less_rentention':less_rentention,
                               'less_payment_claimed':less_payment_claimed,
                               'amount_for_this_claim':amount_for_this_claim,
                               }
        return res

    _columns = {
        'number':fields.char('Number'),
        'currency_id':fields.many2one('res.currency', string='Currency',
                                        required=True, readonly=True, states={'draft': [('readonly', False)]},
                                        track_visibility='always'),
        'sale_order_id':fields.many2one('sale.order', 'From Project', required=True),
        'customer_id':fields.related('sale_order_id','partner_id', type='many2one', relation='res.partner', readonly=True),
        'line_ids':fields.one2many('progressive.billing.line','billing_id','Progressive detail'),
        'state':fields.selection([
            ('draft','Draft'),
            ('open','Opening'),
            ('paid','Paid'),
            ('done','Done'),
            ('cancelled','Cancelled')], 'State',),
        'date_invoice' : fields.date(string='Created Date',
                                    readonly=True, states={'draft': [('readonly', False)]}, index=True,
                                    help="Keep empty to use the current date", copy=False),
        'amount_claim_todate':fields.function(_total_amount, digits_compute=dp.get_precision('Account'),
                                          string='Amount Claim Todate',multi='value',
                                           track_visibility='always'),
        'less_rentention':fields.function(_total_amount, digits_compute=dp.get_precision('Account'),
                                          string='Less retention 5% (Capped at 5% Contract Value)',multi='value',
                                           track_visibility='always'),
        'less_payment_claimed':fields.function(_total_amount, digits_compute=dp.get_precision('Account'),
                                          string='Less Payment Claimed',multi='value',
                                           track_visibility='always'),
        'amount_for_this_claim':fields.function(_total_amount, digits_compute=dp.get_precision('Account'),
                                          string='Amount Due for this Progress Claim',multi='value',
                                           track_visibility='always'),
        'deposit_amount':fields.float('Deposit Amount', digits_compute=dp.get_precision('Account')),

        'is_deposit_billing':fields.boolean('Is deposit Billing'),

        }

    _defaults={
        'number':'',
        'state':'draft',
        'currency_id': _get_default_currency,
        'date_invoice': fields.datetime.now,
        'is_deposit_billing':False,
    }

project_progressive_billing()

class project_progressive_billing_line(osv.osv):
    _name ='progressive.billing.line'

    def _get_valution(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for billing in self.browse(cr, uid, ids, context=context):
            total_work_up_to_date = billing.total_work_up_to_date
            contract_sum = billing.contract_sum
            res[billing.id] = {'total_work_to_date':contract_sum*total_work_up_to_date/100,
                               'this_valuation':contract_sum*total_work_up_to_date/100 - billing.total_work_previous_date,
                               }
        return res


    _columns = {
        'billing_id':fields.many2one('progressive.billing', 'Billing Id', required=True),
        'description':fields.text('Description', required=True),
        'contract_sum':fields.float('Contract Sum', digits_compute=dp.get_precision('Account')),

        'total_work_up_to_date':fields.float('Total Work Done % Up To Date',  digits_compute=dp.get_precision('Account')),

        'total_work_previous_date':fields.float('Total Work Done Up To Previous Valuation',  digits_compute=dp.get_precision('Account'), readonly=True),

        'sequence' : fields.integer(string='Sequence', default=10,
                                    help="Gives the sequence of this line when displaying the invoice."),

        'this_valuation':fields.function(_get_valution, digits_compute=dp.get_precision('Account'),
                                          string='This Valuation',multi='value',
                                           track_visibility='always'),
        'total_work_to_date':fields.function(_get_valution, digits_compute=dp.get_precision('Account'),
                                          string='Total Work Done To Date',multi='value',
                                           track_visibility='always'),
        'sale_order_line_id':fields.many2one('sale.order.line','Line id'),

        }

    _defaults={
    }

project_progressive_billing_line()

