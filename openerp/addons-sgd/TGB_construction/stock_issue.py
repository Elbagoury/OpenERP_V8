# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class stock_issue(osv.osv):
    _name = 'stock.issue'

    def submit_request2(self,cr,uid,ids,context={}):
        print 'wtf here', ids
        self.write(cr,uid,ids,{'state':'submitted'})
        return True

    def cancel_request(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'cancelled'})
        return True

    def approve_request2(self,cr,uid,ids,context={}):
        print 'why not here ???'
        self.write(cr,uid,ids,{'state':'approved'})
        for request in self.browse(cr,uid,ids):
            print 'request', request.sale_order_id,request.id
            if request.sale_order_id and request.sale_order_id.project_costing_id:
                print 'request.sale_order_id.project_costing_id.id', request.sale_order_id.project_costing_id.id
                self.write(cr,uid,request.id,{'project_costing_id':request.sale_order_id.project_costing_id.id})
        return True

    def reject_request(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'rejected'})
        return True


    def create_picking_out(self,cr,uid,ids,context={}):
        return True


    _columns = {
        'issue_type':fields.selection([('product','Product'), ('material','Material'), ('hr','Human Resource')], 'Request Type',),
        'si_voucher_no':fields.char('Request number',size=20),
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
        'sale_order_id':fields.many2one('sale.order','From Project', required=True),
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
    }
    _defaults = {
        'state':'draft',
    }

stock_issue()

class stock_issue_employee(osv.osv):
    _name = 'stock.issue.employee'
    def _get_sub_code(self,cr,uid,context={}):
        print 'active ids ', context
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
        'product_code':fields.related('product_id','default_code',type='char',string='Inventory Description',store=True,),
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

    _columns = {
        'stock_issue_id':fields.many2one('stock.issue','Stock Issue'),
        'product_id':fields.many2one('product.product','Product'),
        'product_code':fields.related('product_id','default_code',type='char',string='Product Description',store=True, readonly=True),
        'qty_on_hand':fields.float('Quantity On Hand',digits_compute=dp.get_precision('Account')),
        'qty_available':fields.float('Quantity Available',digits_compute=dp.get_precision('Account')),
        'issue_qty':fields.float('Request Quantity',digits_compute=dp.get_precision('Account')),
    }

    _default = {
    }

stock_issue_employee()


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



