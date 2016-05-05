# -*- coding:utf-8 -*-

from openerp.osv import osv, fields

class saicoms_customer_type(osv.Model):
    _name = 'saicoms.customer.type'
    _columns={
        'name':fields.char('Name',size=128,required=True),
        'point_type':fields.many2one('saicoms.customer.point.type','Type',required=True),
    }
saicoms_customer_type()

class saicoms_customer_point_type(osv.osv):
    _name='saicoms.customer.point.type'
    _columns={
        'name':fields.char('Name',size=128,required=True),
    }
saicoms_customer_point_type()