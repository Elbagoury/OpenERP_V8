# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class add_sale_deposit_wiz(osv.osv_memory):
    _name='add.sale.deposit.wiz'

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(add_sale_deposit_wiz, self).default_get(cr, uid, fields, context=context)
        sale_order_id = context.get('active_id')
        if isinstance(sale_order_id, list):
            purchase_order_id = sale_order_id[0]
        active_model = context.get('active_model')
        assert active_model in ('sale.order'), 'Bad context propagation'
        if 'sale_order_id' in fields:
            res.update(sale_order_id=sale_order_id)
        return res

    def confirm(self, cr, uid, ids, context=None):
        for track in self.browse(cr,uid,ids):
            if track.amount>0:
                progressive_billing_obj =self.pool.get('progressive.billing')
                order_id = self.pool.get('sale.order').browse(cr,uid,context.get('active_id'))
                customer_id = order_id.partner_id.id
                number = order_id.name+'/'+str(order_id.billing_time+1)
                new_billing = progressive_billing_obj.create(cr,uid,{'sale_order_id':track.sale_order_id.id,
                                                                     'customer_id':customer_id,
                                                                     'date_invoice':track.date,
                                                                     'deposit_amount':track.amount,
                                                                     'is_deposit_billing':True,
                                                                     'number':number,})

                view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'TGB_construction', 'tgb_progressive_billing_form')
                view_id = view_ref and view_ref[1] or False,

                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Progressive Billing for %s %s Time ' %(track.sale_order_id.name,str(track.sale_order_id.billing_time+1))),
                    'res_model': 'progressive.billing',
                    'res_id': new_billing,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'target': 'current',
                    'nodestroy': True,
                }
        return True
    _columns={
        'customer_id':fields.many2one('res.partner','Customer'),
        'amount': fields.float('Total', digits_compute=dp.get_precision('Account'), required=True, ),
        'partner_id':fields.many2one('res.partner', 'Partner', change_default=1, readonly=True, ),
        'date':fields.date('Date', readonly=True, select=True, help="Effective date for accounting entries"),
        'sale_order_id':fields.many2one('sale.order','Sale',required=True),
    }

    def _get_period(self, cr, uid, context=None):
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False
    _defaults={
    }
add_sale_deposit_wiz()