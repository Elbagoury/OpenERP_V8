# -*- coding: utf-8 -*-

from openerp.osv import fields, osv

class sale_order(osv.osv):
    _inherit = "sale.order"
    
    _columns = {
        'ref_no': fields.char('REF NO', size=1024),
        'valid_date': fields.date('VALID DATE'),
    }
    
    _defaults = {
        'note': '''Production leadtime: 7 to 10 working days upon artwork and order
confirmation
Price is inclusive of one time epson proof only
Additional epson proof is chargable

Delivery to 1 location within Singapore''',
    }
    
sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    _columns = {
        'material': fields.char('Material', size=1024),
        'cover_material': fields.char('Cover Material', size=1024),
        'insert_material': fields.char('Insert Material', size=1024),
        'open_size': fields.char('Open Size', size=1024),
        'closed_size': fields.char('Closed Size', size=1024),
        'printing': fields.char('Printing', size=1024),
        'extend': fields.char('Extend', size=1024),
        'finishing': fields.char('Finishing', size=1024),
        'packing': fields.char('Packing', size=1024),
        'handle': fields.char('Handle', size=1024),
        'with_Without_baseboard': fields.boolean('With/Without Baseboard'),
        'materbatch': fields.char('Materbatch', size=1024),
    }

sale_order_line()

