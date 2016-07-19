# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class project_costing(osv.osv):
    _name = 'project.costing'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for project in self.browse(cr,uid,ids):
            name = project.project_id.name
            res.append((project.id,name))
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

    def create_picking_out(self,cr,uid,ids,context={}):
        return True

    def _amount_grand_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for project in self.browse(cr, uid, ids, context=context):
            total_material_cost = 0
            total_others_cost = 0
            total_grand = 0
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
            total_grand = total_material_cost+total_others_cost+total_hr_cost+total_sub_contractor
            res[project.id] = {
                'total_material_cost': total_material_cost,
                'total_others_cost': total_others_cost,
                'total_hr_cost': total_hr_cost,
                'total_grand': total_grand,
                'total_sub_contractor':total_sub_contractor,
                'total_equipment_cost': total_equipment_cost,
            }
        return res



    _columns = {
        'sale_order_id':fields.many2one('sale.order','Project'),
        'project_id':fields.many2one('project.project','Project'),
        'stock_issue_ids':fields.one2many('stock.issue','project_costing_id', 'Material Costs'),
        'others_cost_ids':fields.one2many('project.other.cost','project_costing_id3', 'Other Costs'),
        'sub_contractor_ids':fields.one2many('project.sub.contractor','project_costing_id4', 'Sub Contractor'),
        'hr_cost_ids':fields.one2many('project.hr.cost','project_costing_id', 'HR Costs'),
        'equipment_ids':fields.one2many('project.equipment','project_costing_id', 'Equipment'),
        'si_voucher_no':fields.char('Costing number',size=20),
        'res_user_id':fields.many2one('res.users','Manage By'),
        'reference_no':fields.char('Reference No.',size=20),
        'state':fields.selection([
            ('draft','Draft'),
            ('opening','Opening'),
            ('completed','Completed'),
            ('done','Done'),
            ('cancelled','Cancelled')], 'State',),
        'total_material_cost':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Material Cost',
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'total_others_cost':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Miscellaneous Cost',
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'total_sub_contractor':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Sub-Contractor',
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'total_hr_cost':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total HR Cost',
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'total_equipment_cost':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Equipment Cost',
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'total_grand':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Costing Total',
                                          multi='grand', help="The amount of overview", track_visibility='always'),
    }
    _defaults = {
        'state':'opening',
    }

project_costing()

class project_other_costing(osv.osv):
    _name = 'project.other.cost'

    _columns = {
        'name':fields.char('Name',size=255),
        'amount':fields.float('Amount', digits_compute= dp.get_precision('Account'),),
        'project_costing_id3':fields.many2one('project.costing','Project Costing id',ondelete='cascade'),
        'project_budgeting_id':fields.many2one('project.budgeting','Project Budgeting', ondelete='cascade'),
        'date':fields.date('Date'),
    }
    _defaults={
        'date':fields.datetime.now,
    }

class project_sub_contractor(osv.osv):
    _name = 'project.sub.contractor'

    _columns = {
        'name':fields.char('Name',size=255),
        'amount':fields.float('Amount', digits_compute= dp.get_precision('Account'),),
        'project_costing_id4':fields.many2one('project.costing','Project Costing id',ondelete='cascade'),
        'project_budgeting_id':fields.many2one('project.budgeting','Project Budgeting', ondelete='cascade'),
        'date':fields.date('Date'),
    }
    _defaults={
        'date':fields.datetime.now,
    }


class project_hr_costing(osv.osv):
    _name = 'project.hr.cost'

    _columns = {
        'name':fields.char('Name',size=255),
        'amount':fields.float('Amount',),
        'project_costing_id':fields.many2one('project.costing','Project Costing id',ondelete='cascade'),
        'project_budgeting_id':fields.many2one('project.budgeting','Project Budgeting', ondelete='cascade'),
        'employee_id':fields.many2one('hr.employee','Employee',required=True),
        'timesheet_id':fields.many2one('hr_timesheet_sheet.sheet','Timesheet'),
        'note':fields.char('Note',size=255),
        'importer_id':fields.many2one('ftb.importer','From Import'),

    }

class project_equipment(osv.osv):
    _name = 'project.equipment'

    _columns = {
        'name':fields.char('Name',size=255),
        'amount':fields.float('Amount', digits_compute= dp.get_precision('Account'),),
        'project_costing_id':fields.many2one('project.costing','Project Costing id',ondelete='cascade'),
        'project_budgeting_id':fields.many2one('project.budgeting','Project Budgeting', ondelete='cascade'),
        'date':fields.date('Date'),
    }
    _defaults={
        'date':fields.datetime.now,
    }



