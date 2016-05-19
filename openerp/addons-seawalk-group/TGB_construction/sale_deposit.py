# -*- coding: utf-8 -*-
__author__ = 'Phamkr'
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import netsvc
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, \
    float_compare


class sale_deposit(osv.osv):
    _name = 'sale.deposit'

    _columns = {
        'customer_id':fields.many2one('res.partner','Customer'),
        'amount': fields.float('Total', digits_compute=dp.get_precision('Account'), required=True, readonly=True, ),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, ),
        'journal_id':fields.many2one('account.journal', 'Payment Method', required=True, readonly=True, domain=[('type','in',['bank','cash'])]),
        'date':fields.date('Date', readonly=True, select=True,  help="Effective date for accounting entries"),
        'sale_order_id':fields.many2one('sale.order','Sale',required=True),
        'cheque_no':fields.char('Cheque No',size=100,),
        'deposit_transferred':fields.boolean('Deposit transferred'),
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'deposit_transferred':False,
    }

sale_deposit()
