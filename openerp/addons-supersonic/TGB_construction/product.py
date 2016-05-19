# -*- coding: utf-8 -*-

from openerp.osv import fields, osv



class product(osv.osv):
    _inherit = "product.template"

    def onchange_type(self, cr, uid, ids, type):
        return {}

    _columns = {
        'size':fields.char('Size', size=255),
        'standard':fields.char('Standard', size=255),
        'brand_id':fields.many2one('tgb.brand','Brand'),
    }
class tgb_brand(osv.osv):
    _name = 'tgb.brand'

    _columns ={
        'name':fields.char('Name',size=255),
        'code':fields.char('Code',size=255),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
