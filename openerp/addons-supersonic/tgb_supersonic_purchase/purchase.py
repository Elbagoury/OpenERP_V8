# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta
class purchase_order(osv.osv):
    _inherit = "purchase.order"

    _columns = {
        'quotation_ref':fields.char('Quotation Ref', size=255),
        'quotation_dated':fields.date('Dated'),
        'delivery':fields.char('Delivery', size=1024),
        'warranty':fields.char('Warranty', size=1024),
        'area_re':fields.text('area RE'),
        'terms':fields.char('Terms'),
    }
    
    _defaults = {
        'area_re': '''Reference to the above-mentioned project and your Quotation Ref : , dated: , we are pleased to confirm our order to you as follows:-''',
        'terms': '30 days upon presentation of your Tax Invoice.',
        'delivery': 'To follow strictly to our work schedule.',
        'warranty': 'To provide 12 months warranty from the date of our successful testing and commissioning.',
        'notes': '''Not withstanding any information and technical particulars submitted.  All materials / equipment offer shall comply fully to the standard code of practice, Consultants tender specification for this project. Any equipment not complied to specification shall be made fully compliance at your own cost.''',
    }
    
    def onchange_partner_ref_date(self, cr, uid, ids, partner_ref=False, date_order=False, context=None):
        if date_order:
            date_order = datetime.strptime(date_order, '%Y-%m-%d %H:%M:%S') + timedelta(hours=8)
            date_order = date_order.strftime('%d/%m/%Y')
        area_re = '''Reference to the above-mentioned project and your Quotation Ref: %s, dated: %s, we are pleased to confirm our order to you as follows:-'''%(partner_ref or '',date_order or '')
        return {'value': {'area_re': area_re}}
    
purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
