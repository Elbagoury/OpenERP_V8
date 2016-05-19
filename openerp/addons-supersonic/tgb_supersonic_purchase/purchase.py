# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class purchase_order(osv.osv):
    _inherit = "purchase.order"

    _columns = {
        'quotation_ref':fields.char('Quotation Ref', size=255),
        'quotation_dated':fields.date('Dated'),
        'delivery':fields.char('Delivery', size=1024),
        'warranty':fields.char('Warranty', size=1024),
    }
    
purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
