# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from datetime import datetime
from openerp.tools.translate import _



class purchase_order(osv.osv):

    _inherit = 'purchase.order'

    _columns={
        'stock_issue_id':fields.many2one('stock.issue','From Request'),
    }



class stock_issue(osv.osv):
    _name = 'stock.issue'

    def submit_request2(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'submitted'})
        return True


    def create(self, cr, uid, vals, context=None):
        if vals.get('si_voucher_no','/')=='/':
            vals['si_voucher_no'] = self.pool.get('ir.sequence').get(cr, uid, 'stock.issue', context=context) or '/'
        context = dict(context or {}, mail_create_nolog=True)
        this_project =  super(stock_issue, self).create(cr, uid, vals, context=context)
        return this_project

    def create_purchase_order(self,cr,uid,ids,context={}):
        for request in self.browse(cr,uid,ids):
            product_list = []
            for line in request.stock_issue_detail_ids:
                if line.issue_qty>line.qty_available:
                    product_list.append((line.product_id.id,line.issue_qty-line.qty_available))
            supplier_id  = self.pool.get('res.partner').search(cr,uid,[('name','=','Default Supplier')])
            if supplier_id and len(supplier_id)>0:
                supplier_id=supplier_id[0]
                property_product_pricelist_purchase = self.pool.get('res.partner').browse(cr,uid,supplier_id).property_product_pricelist_purchase.id,
                new_purchase_order = self.pool.get('purchase.order').create(cr,uid,{'partner_id':supplier_id,
                                                                                    'pricelist_id':property_product_pricelist_purchase,
                                                                                    'location_id':request.stock_location.id,
                                                                                    'stock_issue_id':request.id,})
                for product in product_list:
                    new_line = self.pool.get('purchase.order.line').create(cr,uid,{'product_id':product[0],
                                                                                   'name':self.pool.get('product.product').browse(cr,uid,product[0]).name + ' for ' + request.project_id.project_code,
                                                                                   'product_qty':product[1],
                                                                                   'price_unit':self.pool.get('product.product').browse(cr,uid,product[0]).standard_price,
                                                                                   'order_id':new_purchase_order,
                                                                                   'date_planned':datetime.now(),})



            id = new_purchase_order
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'purchase', 'purchase_order_form')
            view_id = view_ref and view_ref[1] or False,
            return {
                'type': 'ir.actions.act_window',
                'name': _('New Purchase Order'),
                'res_model': 'purchase.order',
                'res_id': id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'current',
                'nodestroy': True,
            }



    def cancel_request(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'cancelled'})
        return True

    def approve_request2(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'approved'})
        for request in self.browse(cr,uid,ids):
            if request.project_id:
                project_costing_id = self.pool.get('project.costing').search(cr,uid,[('project_id','=',request.project_id.id)])
                if project_costing_id and len(project_costing_id)>0:
                    project_costing_id = project_costing_id[0]
                    self.write(cr,uid,request.id,{'project_costing_id':project_costing_id})
        return True

    def reject_request(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'rejected'})
        return True


    def create_picking_out(self,cr,uid,ids,context={}):
        all_mr = self.search(cr,uid,[])
        for rq in self.browse(cr,uid,all_mr):
            if rq.project_id:
                self.write(cr,uid,rq.id,{'project_id':rq.project_id.id})
        return True

    def _get_total_cost(self,cr,uid,ids,a,b,context={}):
        res = {}
        for stock_issue in self.browse(cr,uid,ids):
            res[stock_issue.id] = 0
            for line in stock_issue.stock_issue_detail_ids:
                res[stock_issue.id] = line.product_id.standard_price * line.issue_qty
        return res

    def on_change_quotation(self,cr,uid,ids,sale_order_id,context=None):
        return {'value':{'project_id':self.pool.get('sale.order').browse(cr,uid,sale_order_id).project_id.id}}

    def onchange_project_id(self, cr, uid, ids, project_id=False, context=None):
        vals = {}
        if project_id:
            vals['wo_no'] = self.pool.get('project.project').browse(cr,uid,project_id).project_code
        return {'value': vals}

    _columns = {
        'project_id':fields.many2one('project.project','From Project', domain=[('state','=','open')], required = True,),
        'issue_type':fields.selection([('product','Product'), ('material','Material'), ('hr','Human Resource')], 'Request Type',),
        'si_voucher_no':fields.char('Request number',size=20,required=True),
        'si_source_voucher_no':fields.char('Source Voucher No.',size=20),
        'si_source_pp_voucher_no':fields.char('Source PP Voucher No.',sizez=20),
        'si_source_partial_pp_no':fields.char('Source Partial PP No.',size=20),
        'work_center_and_machine':fields.char('Work Center and Machine',size=20),
        'manu_res_user_id':fields.many2one('res.users','Request To'),
        'finished_good':fields.char('Finished Good',size=20),
        'si_date':fields.date('Request Date'),
        'schedule_start_date':fields.datetime('Scheduled Start Date & Time'),
        'schedule_start_end':fields.datetime('Scheduled End Date & Time'),
        'customer_id':fields.many2one('res.partner','Customer'),
        'stock_location':fields.many2one('stock.warehouse','Stock Location', required=True),
        'res_user_id':fields.many2one('res.users','Request By'),
        'employee_id':fields.many2one('hr.employee','Requested By'),
        'sale_order_id':fields.many2one('sale.order','Project Quotation', required=False),
        'request_location_id':fields.many2one('project.location','From Location'),
        'reference_no':fields.char('Reference No.',size=20),
        'stock_issue_emp_line':fields.one2many('stock.issue.employee','stock_issue_id','Stock Issue Employee'),
        'stock_issue_detail_ids':fields.one2many('stock.issue.detail','stock_issue_id','Request Detail'),
        'require_stock_return':fields.selection([('yes','Yes'), ('no','No')], 'Require Stock Return',),
        'project_costing_id':fields.many2one('project.costing','Project Costing id'),
        'project_costing_id2':fields.many2one('project.costing','Project Costing id'),
        'state':fields.selection([
            ('draft','Draft'),
            ('submitted','Submitted'),
            ('approved','Approved'),
            ('rejected','Rejected'),
            ('cancelled','Cancelled')], 'State',),
        'total_cost':fields.function(_get_total_cost, digits_compute=dp.get_precision('Account'),
                                          string='Total Cost',
                                           track_visibility='always'),
        
        'date_required':fields.date('Date Required'),
#         'wo_no':fields.char('W.O NO', size=1024),
        'wo_no':fields.related('project_id', 'project_code', string='W.O NO', type='char'),
        'site':fields.boolean('Site'),
        'office':fields.boolean('Office'),
        'self_collection':fields.boolean('Self-collection'),
    }
    _defaults = {
        'state':'draft',
        'si_voucher_no':'/',
    }

stock_issue()

class stock_issue_employee(osv.osv):
    _name = 'stock.issue.employee'
    def _get_sub_code(self,cr,uid,context={}):
        return [('a','nothing')]
    def _get_sub_description(self,cr,uid,ids,a,b,context={}):
        detail = {}
        for emp in self.browse(cr,uid,ids):
            detail[emp.id]='Nothing'
        return detail


    _columns = {
        'stock_issue_id':fields.many2one('stock.issue','Stock Issue'),
        'subject_type':fields.selection([('emp','EMP'), ('grp','GRP')], 'Subject Type',),
        'sub_code':fields.selection(_get_sub_code, 'Subject Code', required=True,
            ),
        'sub_des':fields.function(_get_sub_description, string ='Subject Description',type='char',size=50,
            ),
        'product_id':fields.many2one('product.product','Inventory Code'),
        'product_code':fields.related('product_id','description',type='char',string='Inventory Description',store=True,),
        'qty_on_hand':fields.float('Quantity On Hand',digits_compute=dp.get_precision('Account')),
        'qty_available':fields.float('Quantity Available',digits_compute=dp.get_precision('Account')),
        'issue_qty':fields.float('Issue Quantity',digits_compute=dp.get_precision('Account')),
        'pack_size':fields.selection([('loose','LOOSE'),('p6','P6 (6.0)')], 'Pack Size',change_default=True),
        'no_of_pack':fields.float('No. of Pack',digits_compute=dp.get_precision('Account')),
        'serial_no':fields.char('Serial No.',size=20),

    }

    _default = {
    }

stock_issue_employee()



class stock_issue_detail(osv.osv):
    _name = 'stock.issue.detail'

    def on_change_issue_qty(self,cr,uid,ids,product_id,issue_qty,context=None):
        price = self.pool.get('product.product').browse(cr,uid,product_id).standard_price * issue_qty
        return {'value':{'total_cost':price}}

    def get_quantity_at_location(self,cr,uid,lid,p):
        ls = ['stock_real','stock_virtual','stock_real_value','stock_virtual_value']
        move_avail = self.pool.get('stock.location')._product_value(cr,uid,[lid],ls,0,{'product_id':p})
        return move_avail[lid]['stock_real']

    def _get_qty_available(self,cr,uid,ids,a,b,context={}):
        res = {}
        for line in self.browse(cr,uid,ids):
            stock_issue = line.stock_issue_id
            res[line.id] = line.product_id.qty_available
            get_qty = self.pool.get('product.product')._product_available(cr,uid,[line.product_id.id],None, False, None)
        return res


    def _get_total_cost(self,cr,uid,ids,a,b,context={}):
        res = {}
        for line in self.browse(cr,uid,ids):
            res[line.id] = line.product_id.standard_price * line.issue_qty
        return res


    _columns = {
        'stock_issue_id':fields.many2one('stock.issue','Stock Issue'),
        'product_id':fields.many2one('product.product','Product'),
        'product_code':fields.related('product_id','default_code',type='char',string='Product Code',store=True, readonly=True),
        'product_price':fields.related('product_id','standard_price',type='float',string='Unit Price',store=False, readonly=True),
        'qty_on_hand':fields.float('Quantity On Hand',digits_compute=dp.get_precision('Account'), readonly=True),
        'qty_available':fields.function(_get_qty_available, digits_compute=dp.get_precision('Account'),
                                          string='Qty Available',
                                           track_visibility='always'),
        'issue_qty':fields.float('Request Quantity',digits_compute=dp.get_precision('Account')),
        'total_cost':fields.function(_get_total_cost, digits_compute=dp.get_precision('Account'),
                                          string='Total Cost',
                                           track_visibility='always'),
        'remark':fields.char('Remark',size=255),
        
        'product_uom_id': fields.many2one('product.uom', 'Unit of Measure'),
        'supplier_id': fields.many2one('res.partner', 'Supplier'),
        'po_no':fields.char('P.O No.',size=255),
        'location':fields.char('Location',size=255),
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id=False, context=None):
        vals = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            vals = {'product_uom_id': product.uom_id and product.uom_id.id or False}
        return {'value': vals}

    _default = {
    }

stock_issue_detail()


class project_location(osv.osv):
    _name ='project.location'
    _columns={
        'name':fields.char('Name', size=255),
        'location':fields.text('Location',),
    }
project_location()



class stock_issue_employee(osv.osv):
    _name = 'stock.issue.manufacturing'

    _columns = {
    }

    _default = {
    }

stock_issue_employee()



