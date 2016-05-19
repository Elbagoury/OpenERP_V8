# -*- coding: utf-8 -*-

import openerp
from openerp import models, fields, api,_

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class project_progressive_billing(osv.osv):

    _inherit = ['mail.thread']
    _name ='progressive.billing'

    def _prepare_invoice(self, cr, uid, order, context=None):
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_invoice_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_ids[0],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_invoice_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'section_id' : order.section_id.id,
            'sale_order_id':order.id,
            'is_progressive':True,
            'billing_time':order.billing_time,
        }
        return invoice_vals


    def _get_default_currency(self, cr, uid, context=None):
        currency_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        return currency_id

    def _prepare_order_line_invoice_line(self, cr, uid, line,invoice_id, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = {}
        prop = self.pool.get('ir.property').get(cr, uid,
                'property_account_income_categ', 'product.category',
                context=context)
        account_id = prop and prop.id or False
        uosqty = 0
        pu = 0.0
        fpos = line.billing_id.sale_order_id.fiscal_position or False
        account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
        if not account_id:
            raise osv.except_osv(_('Error!'),
                        _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
        res = {
            'name': line.description,
            'origin': line.billing_id.number,
            'account_id': account_id,
            'price_unit': line.this_valuation,
            'quantity': 1,
            'invoice_id':invoice_id,
        }

        return res


    def action_view_invoice(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree1')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of invoices to display
        inv_ids = []
        for so in self.browse(cr, uid, ids, context=context):
            inv_ids += [so.invoice_id.id]
        #choose the view_mode accordingly
        if len(inv_ids)>1:
            result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_invoice_form_new')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = inv_ids and inv_ids[0] or False
        return result


    def action_create_invoice(self,cr,uid,ids,context={}):
        for billing in self.browse(cr,uid,ids):
            if not billing.invoiced:
                invoice_vals = self._prepare_invoice(cr,uid,billing.sale_order_id)
                new_invoice = self.pool.get('account.invoice').create(cr,uid,invoice_vals)
                if new_invoice:
                    self.pool.get('account.invoice').write(cr,uid,new_invoice,{'progressive_id':billing.id})
                    self.write(cr,uid,billing.id,{'invoiced':True,
                                                  'invoice_id':new_invoice,
                                                  'state':'invoiced'})
                    for line in billing.line_ids:
                        new_line = self._prepare_order_line_invoice_line(cr,uid,line,new_invoice)
                        self.pool.get('account.invoice.line').create(cr,uid,new_line)

                    if billing.is_deposit_billing:
                        deposit_res =  {}
                        prop = self.pool.get('ir.property').get(cr, uid,
                                'property_account_income_categ', 'product.category',
                                context=context)
                        account_id = prop and prop.id or False
                        fpos = billing.sale_order_id.fiscal_position or False
                        account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
                        if not account_id:
                            raise osv.except_osv(_('Error!'),
                                        _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
                        deposit_res = {
                            'name': 'Deposit Amount',
                            'origin': billing.number,
                            'account_id': account_id,
                            'price_unit': billing.deposit_amount,
                            'quantity': 1,
                            'invoice_id':new_invoice,
                        }
                        self.pool.get('account.invoice.line').create(cr,uid,deposit_res)

                    mod_obj = self.pool.get('ir.model.data')
                    act_obj = self.pool.get('ir.actions.act_window')

                    result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree1')
                    id = result and result[1] or False
                    result = act_obj.read(cr, uid, [id], context=context)[0]

                    inv_ids = [new_invoice]
                    if len(inv_ids)>1:
                        result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
                    else:
                        res = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_invoice_form_new')
                        result['views'] = [(res and res[1] or False, 'form')]
                        result['res_id'] = inv_ids and inv_ids[0] or False
                    return result

    def action_approve_billing(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'open'})
        for billing in self.browse(cr,uid,ids):
            if billing.sale_order_id:
                last_bill_time = billing.sale_order_id.billing_time
                self.pool.get('sale.order').write(cr,uid,billing.sale_order_id.id,{'billing_time':last_bill_time + 1})
                self.write(cr,uid,billing.id,{'billing_time':last_bill_time+1})
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
            amount_for_this_claim = billing.deposit_amount
            for detail in billing.line_ids:
                total_contract_sum+=detail.contract_sum
                amount_claim_todate+=detail.total_work_to_date
                amount_for_this_claim+=detail.this_valuation
                less_payment_claimed+=detail.total_work_previous_date
            if billing.is_deposit_billing:
                amount_claim_todate = billing.deposit_amount
            deposit_id = self.search(cr,uid,[('sale_order_id','=',billing.sale_order_id.id),('is_deposit_billing','=',True)])
            if deposit_id and len(deposit_id)>0:
                for deposit_billing in self.browse(cr,uid,deposit_id):
                    less_payment_claimed+= deposit_billing.deposit_amount
            less_rentention+= total_contract_sum*billing.retention_amount/100
            res[billing.id] = {'amount_claim_todate':amount_claim_todate,
                               'less_rentention':less_rentention,
                               'less_payment_claimed':less_payment_claimed,
                               'amount_for_this_claim':amount_for_this_claim,
                               }
        return res

    _columns = {
        'number':fields.char('Number'),
        'retention_amount':fields.float('Retention Amount', digits_compute=dp.get_precision('Account')),
        'currency_id':fields.many2one('res.currency', string='Currency',
                                        required=True, readonly=True, states={'draft': [('readonly', False)]},
                                        track_visibility='always'),
        'sale_order_id':fields.many2one('sale.order', 'From Quotation', required=True),
        'customer_id':fields.related('sale_order_id','partner_id', type='many2one', relation='res.partner', readonly=True),
        'line_ids':fields.one2many('progressive.billing.line','billing_id','Progressive detail'),
        'state':fields.selection([
            ('draft','Draft'),
            ('open','Opening'),
            ('paid','Paid'),
            ('invoiced','Invoiced'),
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
        'invoiced':fields.boolean('Invoiced'),
        'invoice_id':fields.many2one('account.invoice','Invoice id'),
        'retention_required':fields.boolean('Have Retention',readonly=True),
        'retention_type':fields.selection([('P','Percent'),('A','Amount')], 'Retention Type',readonly=True),
        'retention_percent': fields.float('Retention Percent',readonly=True),
        'retention_day': fields.integer('Retention Months',readonly=True),
        'retention_date':fields.related('sale_order_id','retention_date','Retention Months', readonly=True),
        'billing_time':fields.integer('Billing Claim'),
        }

    _defaults={
        'billing_time':0,
        'invoiced':False,
        'retention_required':False,
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
            old_lines = self.search(cr,uid,[('sale_order_line_id','=',billing.sale_order_line_id.id)])
            total_work_previous_date = 0
            old_lines.remove(billing.id)
            if old_lines and len(old_lines)>0:
                total_work_previous_date = 0
                for old in self.browse(cr,uid,old_lines):
                    if old.total_work_up_to_date>total_work_previous_date:
                        total_work_previous_date = old.total_work_up_to_date

            total_work_up_to_date = billing.total_work_up_to_date
            contract_sum = billing.contract_sum

            res[billing.id] = {'total_work_to_date':contract_sum*total_work_up_to_date/100,
                               'this_valuation':contract_sum*total_work_up_to_date/100 - total_work_previous_date*contract_sum/100,
                               'total_work_previous_date':total_work_previous_date*contract_sum/100,
                               }
        return res


    _columns = {
        'billing_id':fields.many2one('progressive.billing', 'Billing Id', required=True),
        'description':fields.text('Description', required=True),
        'contract_sum':fields.float('Contract Sum', digits_compute=dp.get_precision('Account')),

        'total_work_up_to_date':fields.float('Total Work Done % Up To Date',  digits_compute=dp.get_precision('Account')),

        'total_work_previous_date':fields.function(_get_valution, digits_compute=dp.get_precision('Account'),
                                          string='Total Work Done Up To Previous Valuation',multi='value',
                                           store={
                                              'progressive.billing.line': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                                          },
                                           track_visibility='always'),

        'sequence' : fields.integer(string='Sequence', default=10,
                                    help="Gives the sequence of this line when displaying the invoice."),

        'this_valuation':fields.function(_get_valution, digits_compute=dp.get_precision('Account'),
                                          string='This Valuation',multi='value',
                                         store={
                                              'progressive.billing.line': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                                          },
                                           track_visibility='always'),
        'total_work_to_date':fields.function(_get_valution, digits_compute=dp.get_precision('Account'),
                                          string='Total Work Done To Date',multi='value',
                                             store={
                                              'progressive.billing.line': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                                          },
                                           track_visibility='always'),
        'sale_order_line_id':fields.many2one('sale.order.line','Line id'),

        }

    _defaults={
    }

project_progressive_billing_line()

