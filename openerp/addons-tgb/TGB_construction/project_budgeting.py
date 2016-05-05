# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class project_budgeting(osv.osv):
    _name = 'project.budgeting'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for project in self.browse(cr,uid,ids):
            name = project.project_id.name
            res.append((project.id,name + 'Budget'))
        return res

    def submit_request(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'submitted'})
        return True

    def cancel_request(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'cancelled'})
        return True

    def approve_request(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'approved'})
        return True

    def reject_request(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'rejected'})
        return True


    def _amount_grand_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for project in self.browse(cr, uid, ids, context=context):
            total_budgeting = 0
            for material in project.project_budgeting_detail_ids:
                total_budgeting+= material.amount
            project_costing_ids = self.pool.get('project.costing').search(cr,uid,[('project_id','=',project.project_id.id)])
            total_cost = 0
            if project_costing_ids and len(project_costing_ids)>0:
                project_costing_ids = project_costing_ids[0]
                total_cost = self.pool.get('project.costing').browse(cr,uid,project_costing_ids).total_grand

            res[project.id] = {
                'total_budgeting': total_budgeting,
                'total_profit': total_budgeting-total_cost,
            }
        return res



    _columns = {
        'sale_order_id':fields.many2one('sale.order','Project'),
        'project_id':fields.many2one('project.project','Project'),
        'project_budgeting_detail_ids':fields.one2many('project.budgeting.detail','project_budgeting_id', 'Project Budgeting Detail'),
        'si_voucher_no':fields.char('Number',size=20),
        'res_user_id':fields.many2one('res.users','Manage By'),
        'state':fields.selection([
            ('draft','Draft'),
            ('opening','Opening'),
            ('completed','Completed'),
            ('done','Done'),
            ('cancelled','Cancelled')], 'State',),
        'total_budgeting':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Budgeting',
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'total_profit':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Profit',
                                          multi='grand', help="The amount of overview", track_visibility='always'),

    }
    _defaults = {
        'state':'opening',
    }

project_budgeting()

class project_budgeting_detail(osv.osv):
    _name = 'project.budgeting.detail'

    _columns = {
        'name':fields.char('Description',size=255),
        'amount':fields.float('Amount', digits_compute= dp.get_precision('Account'),),
        'project_budgeting_id':fields.many2one('project.costing','Project Costing id'),
        'date':fields.date('Date'),
        'remark':fields.char('Remarks',size=255),
    }
    _defaults={
        'date':fields.datetime.now,
    }
project_budgeting_detail()





