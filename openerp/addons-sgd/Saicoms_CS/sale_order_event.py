# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class sale_order_event(osv.osv):
    _name = 'sale.order.event'
    _columns = {
        'date':fields.date('Date',size=255,required=True),
        'remark':fields.char('Remark',size=128),
        'product_id':fields.many2one('product.product','Product',required=True),
        'sale_order_id':fields.many2one('sale.order','Order',),
        'pos_order_id':fields.many2one('pos.order','Order',),
    }
sale_order_event()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

