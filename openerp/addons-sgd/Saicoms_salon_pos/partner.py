# -*- coding:utf-8 -*-

from openerp.osv import osv, fields

class partner(osv.Model):
    
    _inherit = "res.partner"
    
    _columns = {
          'country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
          'customer_type_id':fields.many2one('saicoms.customer.type','Customer Type'),
          'customer_source_id':fields.many2one('saicoms.customer.source','Customer Source'),
          'saicoms_dob':fields.date('Date Of Birth'),
          'saicoms_occupation':fields.many2one('saicoms.occupation','Occupation'),
    }

    def _get_default_country(self, cr, uid, context=None):
        res = self.pool.get('res.country').search(cr, uid, [('code','=','VN')], context=context)
        return res[0] or False


    _defaults={
        'country_id':_get_default_country,
    }
    
partner()

class customer_type(osv.osv):
    _name = "saicoms.customer.type"

    _columns={
        'name':fields.char('Customer Type', size=50),
    }
customer_type()

class saicoms_occupation(osv.osv):
    _name = "saicoms.occupation"

    _columns={
        'name':fields.char('Partner Occupation', size=50),
    }
saicoms_occupation()


class customer_source(osv.osv):
    _name = "saicoms.customer.source"

    _columns={
        'name':fields.char('Customer Source', size=50),
    }
customer_source()

