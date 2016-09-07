# -*- coding: utf-8 -*-

from openerp.osv import fields, osv

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    _columns = {
        'package': fields.char('Package', size=1024),
        'package_amount': fields.float('Package$'),
        'qty': fields.float('Qty'),
        'flower': fields.char('Flower', size=1024),
        'misc_pd': fields.char('Misc& P&D', size=1024),
        'remark_deco': fields.char('Remark/Deco', size=1024),
    }

stock_picking()