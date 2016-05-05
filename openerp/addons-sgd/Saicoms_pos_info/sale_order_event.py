# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class sale_order_event(osv.osv):
    _inherit = 'sale.order.event'
    _columns = {
        'pos_order_id':fields.many2one('pos.order','Order',),
    }
sale_order_event()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

