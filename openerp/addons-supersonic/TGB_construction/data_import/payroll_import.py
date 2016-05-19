# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import psycopg2
from openerp.osv import orm, fields
import xlrd
from base64 import b64decode
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
import math
import openerp.addons.decimal_precision as dp


class payroll_import(osv.osv):
    _inherit = 'base_import.import'
    _name = 'payroll.import'


    def _get_total_cost(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for billing in self.browse(cr, uid, ids, context=context):
            res[billing.id]={'total_cost':0}
            total_cost = 0
            for detail in billing.costing_detail_ids:
                total_cost+=detail.total_cost
            res[billing.id]['total_cost']=total_cost
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

    def send_to_costing(self,cr,uid,ids,context={}):
        for importer in self.browse(cr,uid,ids):
            for detail in importer.costing_detail_ids:
                if detail.project_costing_id:
                    project_costing_id = detail.project_costing_id.id
                    self.pool.get('project.hr.cost').create(cr,uid,{'project_costing_id':project_costing_id,
                                                                    'employee_id':detail.employee_id.id,
                                                                    'amount':detail.total_cost,
                                                                    'note':importer.subject,
                                                                    })
            self.write(cr,uid,importer.id,{'state':'done'})
        return True
    def import_payroll(self, cr, uid, ids,context=None):
        cr.execute('SAVEPOINT import')
        # contract_ids = self.pool.get('dk.contract').search(cr,uid,[])
        # self.pool.get('dk.contract').write(cr,uid,contract_ids,{'state':'progress'})
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            workbook = xlrd.open_workbook(file_contents=b64decode(record.file))
            sheet = workbook.sheet_by_index(0)
            type_list = []
            for r in range(0,sheet.nrows):
                if r>=1:
                    row = sheet.row_values(r)
                    name = row[0]
                    employee_id = self.pool.get('hr.employee').search(cr,uid,[('name','=',name)])
                    if employee_id and len(employee_id)>0:
                        employee_id = employee_id[0]
                    else:
                        employee_id = self.pool.get('hr.employee').create(cr,uid,{'name':name})
                    worked_day = row[2]
                    daily_rate = row[3]
                    ot_hours = row[4]
                    ot_rate = row[5]
                    total_cost = row[6]
                    project_code = row[7]
                    project_costing_id = None
                    if project_code:
                        project_id = self.pool.get('project.project').search(cr,uid,[('project_code','=',project_code)])
                        if project_id and len(project_id)>0:
                            project_id = project_id[0]
                            project_costing_id = self.pool.get('project.costing').search(cr,uid,[('project_id','=',project_id)])
                            if project_costing_id and len(project_costing_id)>0:
                                project_costing_id = project_costing_id[0]
                    new_costing_deail = self.pool.get('payroll.costing.detail').create(cr,uid,{'importer_id':record.id,
                                                                                               'employee_id':employee_id,
                                                                                               'worked_day':worked_day,
                                                                                               'daily_rate':daily_rate,
                                                                                               'ot_hours':ot_hours,
                                                                                               'ot_rate':ot_rate,
                                                                                               'total_cost':total_cost,
                                                                                               'project_costing_id':project_costing_id,
                                                                                               })
        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True

    _columns = {
            'costing_detail_ids':fields.one2many('payroll.costing.detail','importer_id','Costing Detail Ids',states={'draft': [('readonly', False)]}, index=True,readonly=True,),
            'total_cost':fields.function(_get_total_cost, digits_compute=dp.get_precision('Account'),
                                              string='Total',multi='value',
                                               track_visibility='always'),
            'date_import' : fields.datetime(string='Date Import',
                                        readonly=True, states={'draft': [('readonly', False)]}, index=True,
                                        help="Keep empty to use the current date", copy=False,),
            'imported_by':fields.many2one('res.users','Imported by',states={'draft': [('readonly', False)]}, index=True,readonly=True,),
            'state':fields.selection([
                ('draft','Draft'),
                ('submitted','Confirmed'),
                ('approved','Approved'),
                ('rejected','Rejected'),
                ('done','Done'),
                ('cancelled','Cancelled')], 'Status',),
            'subject':fields.char('Subject', size=255,states={'draft': [('readonly', False)]}, index=True,readonly=True,),
    }

    _defaults={
        'state':'draft',
        'date_import': fields.datetime.now,
    }

payroll_import()


class payroll_costing_detail(osv.osv):

    _name = 'payroll.costing.detail'

    _columns={
        'importer_id':fields.many2one('payroll.import','Importer'),
        'employee_id':fields.many2one('hr.employee','Employee'),
        'total_working_hours':fields.float('Total Working Hours',digits_compute=dp.get_precision('Account'),),
        'contract_id':fields.many2one('hr.contract','Contract'),
        'worked_day':fields.char('Worked Day',size=255,),
        'daily_rate':fields.float('Daily Rate',digits_compute=dp.get_precision('Account'),),
        'ot_hours':fields.float('OT Hours',digits_compute=dp.get_precision('Account'),),
        'ot_rate':fields.float('OT Rate',digits_compute=dp.get_precision('Account'),),
        'total_cost':fields.float('Total',digits_compute=dp.get_precision('Account'),),
        'hourly_rate':fields.float('Hourly Rate',digits_compute=dp.get_precision('Account'),),
        'project_costing_id':fields.many2one('project.costing','Project Costing'),
    }


