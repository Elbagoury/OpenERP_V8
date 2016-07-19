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

    def _amount_cost_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for project in self.browse(cr, uid, ids, context=context):
            total_material_cost = 0
            total_others_cost = 0
            total_hr_cost = 0
            total_sub_contractor=0
            total_equipment_cost = 0
            for material in project.stock_issue_ids:
                for detail in material.stock_issue_detail_ids:
                    if detail.product_id:
                        total_material_cost+= detail.product_id.standard_price*detail.issue_qty
            for hr_cost in project.hr_cost_ids:
                total_hr_cost+= hr_cost.amount
            for other in project.others_cost_ids:
                total_others_cost+= other.amount

            for sub in project.sub_contractor_ids:
                total_sub_contractor+= sub.amount
            for equipment in project.equipment_ids:
                total_equipment_cost += equipment.amount
            res[project.id] = {
                'total_material_cost': total_material_cost,
                'total_others_cost': total_others_cost,
                'total_hr_cost': total_hr_cost,
                'total_sub_contractor':total_sub_contractor,
                'total_equipment_cost': total_equipment_cost,
            }
        return res
    
    def _amount_costing_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        costing_obj = self.pool.get('project.costing')
        for project in self.browse(cr, uid, ids, context=context):
            costing_stock_issue_ids = []
            costing_total_material_cost = 0
            costing_others_cost_ids = []
            costing_total_others_cost = 0
            costing_sub_contractor_ids = []
            costing_total_sub_contractor = 0
            costing_hr_cost_ids = []
            costing_total_hr_cost = 0
            costing_equipment_ids = []
            costing_total_equipment_cost = 0
            
            costing_ids = costing_obj.search(cr, uid, [('project_id','=',project.project_id.id)], order='id desc', limit=1)
            for costing in costing_obj.browse(cr, uid, costing_ids):
                for material in costing.stock_issue_ids:
                    costing_stock_issue_ids.append(material.id)
                    for detail in material.stock_issue_detail_ids:
                        if detail.product_id:
                            costing_total_material_cost += detail.product_id.standard_price*detail.issue_qty
                
                for other in costing.others_cost_ids:
                    costing_others_cost_ids.append(other.id)
                    costing_total_others_cost += other.amount
                
                for sub in costing.sub_contractor_ids:
                    costing_sub_contractor_ids.append(sub.id)
                    costing_total_sub_contractor += sub.amount
                
                for hr_cost in costing.hr_cost_ids:
                    costing_hr_cost_ids.append(hr_cost.id)
                    costing_total_hr_cost += hr_cost.amount
                
                for equipment in costing.equipment_ids:
                    costing_equipment_ids.append(equipment.id)
                    costing_total_equipment_cost += equipment.amount
                
            res[project.id] = {
                'costing_stock_issue_ids': costing_stock_issue_ids,
                'costing_total_material_cost': costing_total_material_cost,
                'costing_others_cost_ids': costing_others_cost_ids,
                'costing_total_others_cost': costing_total_others_cost,
                'costing_sub_contractor_ids': costing_sub_contractor_ids,
                'costing_total_sub_contractor': costing_total_sub_contractor,
                'costing_hr_cost_ids': costing_hr_cost_ids,
                'costing_total_hr_cost': costing_total_hr_cost,
                'costing_equipment_ids': costing_equipment_ids,
                'costing_total_equipment_cost': costing_total_equipment_cost,
            }
        return res

    _columns = {
        'sale_order_id':fields.many2one('sale.order','Project'),
        'project_id':fields.many2one('project.project','Project'),
        'project_budgeting_detail_ids':fields.one2many('project.budgeting.detail','project_budgeting_id', 'Project Budgeting Detail'),
        'stock_issue_ids':fields.one2many('stock.issue','project_budgeting_id', 'Material Costs'),
        'others_cost_ids':fields.one2many('project.other.cost','project_budgeting_id', 'Other Costs'),
        'sub_contractor_ids':fields.one2many('project.sub.contractor','project_budgeting_id', 'Sub Contractor'),
        'hr_cost_ids':fields.one2many('project.hr.cost','project_budgeting_id', 'HR Costs'),
        'equipment_ids':fields.one2many('project.equipment','project_budgeting_id', 'Equipment'),
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
                
        'total_material_cost':fields.function(_amount_cost_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Material Cost',
                                          multi='cost', help="The amount of overview", track_visibility='always'),

        'total_others_cost':fields.function(_amount_cost_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Miscellaneous Cost',
                                          multi='cost', help="The amount of overview", track_visibility='always'),

        'total_sub_contractor':fields.function(_amount_cost_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Sub-Contractor',
                                          multi='cost', help="The amount of overview", track_visibility='always'),

        'total_hr_cost':fields.function(_amount_cost_all, digits_compute=dp.get_precision('Account'),
                                          string='Total HR Cost',
                                          multi='cost', help="The amount of overview", track_visibility='always'),

        'total_equipment_cost':fields.function(_amount_cost_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Equipment Cost',
                                          multi='cost', help="The amount of overview", track_visibility='always'),
        
        'costing_stock_issue_ids': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Material Costs', type="many2many", relation="stock.issue",
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_total_material_cost': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Material Cost',
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_others_cost_ids': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Other Costs', type="many2many", relation="project.other.cost",
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_total_others_cost': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Miscellaneous Cost',
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_sub_contractor_ids': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Sub Contractor', type="many2many", relation="project.sub.contractor",
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_total_sub_contractor': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Sub-Contractor',
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_hr_cost_ids': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='HR Costs', type="many2many", relation="project.hr.cost",
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_total_hr_cost': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Total HR Cost',
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_equipment_ids': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Equipment Costs', type="many2many", relation="project.equipment",
                                          multi='costing', help="The amount of overview", track_visibility='always'),
        'costing_total_equipment_cost': fields.function(_amount_costing_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Equipment Cost',
                                          multi='costing', help="The amount of overview", track_visibility='always'),
    }
    _defaults = {
        'state':'opening',
    }
    
    def onchange_project_id(self, cr, uid, ids, project_id=False, context=None):
        vals = {}
        if project_id:
            project = self.pool.get('project.project').browse(cr, uid, project_id)
            vals.update({
                'si_voucher_no': project.project_code
            })
        return {'value': vals}

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





