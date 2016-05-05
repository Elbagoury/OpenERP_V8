# -*- coding: utf-8 -*-
__author__ = 'Phamkr'
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.addons.point_of_sale import point_of_sale
import logging
from openerp import tools
import openerp.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)

class pos_package(osv.osv):
    _name = 'pos.package'

    def _get_package_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('pos.package.redeem').browse(cr, uid, ids, context=context):
            result[line.package_id.id] = True
        return result.keys()

    def _amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for package in self.browse(cr,uid,ids,context):
            res[package.id] = {}
            used = 0
            total = package.total
            for line in package.package_redeem_ids:
                used+=line.qty
            remain = total-used
            res[package.id]['used']=used
            res[package.id]['remain']=remain
        return res


    _columns={
        'product_id':fields.many2one('product.product','Product',required=True),
        'partner_id':fields.many2one('res.partner','Customer'),
        'reference':fields.char('Reference',size=128 ),
        'name':fields.char('Package No',size=128 ),
        'qty':fields.float('Qty',digits=(16,0)),
        'package_redeem_ids':fields.one2many('pos.package.redeem','package_id','Package Redemption'),
        'total':fields.float('Total',digits=(16,0)),
        'unit_price':fields.float('Price',digits=(16,0)),
        'used': fields.function(_amount_total, digits_compute=dp.get_precision('Account'), string='Used',
            store={
                'pos.package': (lambda self, cr, uid, ids, c={}: ids, ['package_redeem_ids','total'], 10),
                'pos.package.redeem': (_get_package_line, ['qty'], 10),
            },
            multi='sums', track_visibility='always'),

        'remain': fields.function(_amount_total, digits_compute=dp.get_precision('Account'), string='Remain',
            store={
                'pos.package': (lambda self, cr, uid, ids, c={}: ids, ['package_redeem_ids','total'], 10),
                'pos.package.redeem': (_get_package_line, ['qty'], 10),
            },
            multi='sums', track_visibility='always'),
    }
pos_package()


class pos_package_redeem(osv.osv):
    _name = 'pos.package.redeem'
    _columns={
        'product_id':fields.many2one('product.product','Product'),
        'perform_user_ids':fields.many2many('res.users','rel_user_package','package_redeem_id','user_id', string='Perform User'),
        'qty':fields.float('Qty',digits=(16,0)),
        'date':fields.datetime('Time'),
        'package_id':fields.many2one('pos.package','Package Id'),
        'partner_id':fields.related('package_id','partner_id',type="many2one", relation="res.partner", string="Customer",readonly=True),
        'reference':fields.related('package_id','reference',type="char", string="Reference",readonly=True,store=True),
        'unit_price':fields.float('Price',digits=(16,0)),
        'due_date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string="Start date from"),
        'due_date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string="Start date to"),
    }
pos_package_redeem()

