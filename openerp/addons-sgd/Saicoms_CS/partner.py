# -*- coding:utf-8 -*-

from openerp.osv import osv, fields

class res_partner(osv.Model):
    _inherit = 'res.partner'
    # def create(self,cr,uid,vals,context=None):
    #     partner_id = super(res_partner, self).create(cr, uid, vals, context=context)
    #     if vals.get('customer'):
    #         project_obj = self.pool.get('project.project')
    #         project_id = project_obj.create(cr,uid,{'name':vals.get('name'),
    #                                    'partner_id':partner_id})
    #         self.write(cr,uid,partner_id,{'saicoms_project_id':project_id})
    #     return partner_id
    _columns={
        'saicoms_project_id':fields.many2one('project.project','CS Project'),
        'saicoms_co_name':fields.char('Company Name',size=128),
        'saicoms_co_address':fields.char('Company Address',size=128),
        'saicoms_co_district':fields.char('Company District',size=128),
        'saicoms_co_city':fields.char('Company City',size=128),
    }

res_partner()