# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class product_product(osv.osv):
    _inherit = 'product.template'
    _columns = {
        'product_remark_ids':fields.one2many('product.remark','product_id','Remarks'),
    }
product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

