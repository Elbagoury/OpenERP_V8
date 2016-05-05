# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class product_template(osv.osv):
    _inherit = 'product.template'
    _columns = {
        'is_group_product2':fields.boolean('Is Service Package'),
        'product_group_ids2': fields.one2many('product.child2','parent_id2',string='Group Products'),
    }
    _defaults={
        'is_group_product2':False,
    }
product_template()



class product_child(osv.osv):
    _name = 'product.child2'
    _columns = {
        'product_id':fields.many2one('product.product','Product'),
        'parent_id2':fields.many2one('product.template','Parent Id'),
        'qty': fields.float('Qty',digits_compute=dp.get_precision('Product UoS')),
        'note':fields.text('Note'),
    }
product_child()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

