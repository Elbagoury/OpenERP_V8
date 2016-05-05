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
import datetime


class package_redemption(osv.osv_memory):
    _name = 'package.redemption'

    def search_package(self,cr,uid,ids,context={}):
        for search in self.browse(cr,uid,ids,context):
            unlink_package_line_ids = self.pool.get('package.redemption.line').search(cr,uid,[('package_id','=',search.id)])
            if unlink_package_line_ids:
                search.pool.get('package.redemption.line').unlink(cr,uid,unlink_package_line_ids)
            search_condition =[]
            if search.partner_id:
                partner_id = search.partner_id
                search_condition.append(('partner_id','=',partner_id.id))
            if search.pos_reference:
                search_condition.append(('reference','=',search.pos_reference))
            if search.product_id:
                search_condition.append(('product_id','=',search.product_id.id))
            pos_package_ids = self.pool.get('pos.package').search(cr,uid,search_condition)
            if pos_package_ids:
                for package in self.pool.get('pos.package').browse(cr,uid,pos_package_ids):
                    now = fields.datetime.now,
                    self.pool.get('package.redemption.line').create(cr,uid,{'package_id':search.id,
                                                                            'origin_id':package.id,
                                                                            'date': datetime.datetime.now(),
                                                                            })
    def redeem(self,cr,uid,ids,context={}):
        for do in self.browse(cr,uid,ids):
            for service in do.package_redeem_ids:
                if service.qty >0:
                    perform_user_ids = []
                    for user in service.perform_user_ids:
                        perform_user_ids.append(user.id)
                    new_line = self.pool.get('pos.package.redeem').create(cr,uid,{'qty':service.qty,
                                                                       'date':service.date,
                                                                       'package_id':service.origin_id.id,
                                                                        'product_id':service.product_id.id,
                                                                        'unit_price':service.unit_price
                                                                       })
                    self.pool.get('pos.package.redeem').write(cr,uid,new_line,{'perform_user_ids':[(6,0,perform_user_ids)]})

                    for remark in service.product_id.product_remark_ids:
                        pos_order = self.pool.get('pos.order').search(cr,uid,[('pos_reference','=',service.reference)])
                        if pos_order and len(pos_order)>0:
                            pos_order=pos_order[0]
                        print 'service.date', service.date, remark.time
                        order_date = datetime.datetime.strptime(service.date[:10],'%Y-%m-%d')
                        event_date = order_date + relativedelta(days=remark.time)
                        self.pool.get('sale.order.event').create(cr,uid,{
                                                                        'date':event_date,
                                                                        'remark':remark.remark,
                                                                        'pos_order_id':pos_order,
                                                                        'product_id':service.product_id.id,
                                                                        })

    _columns={
        'partner_id':fields.many2one('res.partner','Customer',domain=[('customer','=',True)]),
        'pos_order_id':fields.many2one('pos.order','POS Order'),
        'pos_reference':fields.char('Reference',size=255),
        'product_id':fields.many2one('product.product','Services or Products'),
        'sale_order_id':fields.many2one('sale.order','Sale Order'),
        'date':fields.date('Order Date'),
        'package_redeem_ids':fields.one2many('package.redemption.line','package_id','Package Redemption'),
    }
package_redemption()


class package_redemption_line(osv.osv_memory):
    _name = 'package.redemption.line'
    _columns={
        'check':fields.boolean('Check'),
        'package_id':fields.many2one('package.redemption','Package Id'),
        'origin_id':fields.many2one('pos.package','Origin Package'),
        'date':fields.datetime('Time'),
        'product_id':fields.related('origin_id','product_id',type='many2one', relation='product.product',string='Product',required=True,readonly=True),
        'reference':fields.related('origin_id','reference',type='char',string='Reference',readonly=True),
        'perform_user_ids':fields.many2many('res.users','rel_user_package_redeem2','package_redem_line_id','user_id', string='Perform User'),
        'used':fields.related('origin_id','used',type='float',string='Used',readonly=True),
        'unit_price':fields.related('origin_id','unit_price',type='float',string='Price',readonly=True),
        'remain':fields.related('origin_id','remain',type='float',string='Remain',readonly=True),
        'qty':fields.float('Redeem Qty',digits=(16,0)),
        }

package_redemption_line()






