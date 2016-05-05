# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class product_remark(osv.osv):
    _name = 'product.remark'
    _columns = {
        'time':fields.integer('Time (Days)',size=255,required=True),
        'remark':fields.char('Remark',size=128),
        'product_id':fields.many2one('product.template','Product',required=True),
    }
product_remark()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

