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

import itertools
import csv
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO





class ftb_importer(osv.osv):
    _inherit = 'base_import.import'
    _name = 'ftb.importer'


    def row_is_empty(self,row=[]):
        for item in row:
            if item:
                return False
        return True

    def all_partner_is_customer(self,cr,uid,ids,context=None):
        partner_ids = self.pool.get('res.partner').search(cr,uid,[('id','>',4)])
        self.pool.get('res.partner').write(cr,uid,partner_ids,{'customer':True})

    def import_attendance_for_construction(self,cr,uid,ids,context=None):
        cr.execute('SAVEPOINT import')
        record = self.browse(cr, uid, ids, context=context)[0]
        csv_reader = csv.reader(StringIO(b64decode(record.file)), delimiter=',', quotechar='"')
        for row in csv_reader:
            timesheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
            attendance_obj = self.pool.get('hr.attendance')
            if row[0]!='No.':
                actatek_id = row[1]
                import_date = row[4]
                employee_id = self.pool.get('hr.employee').search(cr,uid,[('actatek_id','=',actatek_id)])
                if employee_id and len(employee_id)>0:
                    employee_id = employee_id[0]
                else:
                    raise osv.except_osv(_('Error!'),_("No employee defined for ID %s ") % (actatek_id))
                import_date =  datetime.strptime(import_date, '%Y/%m/%d')

                # sheet_id = timesheet_obj.search(cr,uid,[('date_from','<=',import_date),('date_to','>=',import_date)])
                # if sheet_id and len(sheet_id)>0:
                #     sheet_id = sheet_id[0]
                # else:
                #     raise osv.except_osv(_('Error!'),_("No timesheet defined for ID %s on %s") % (actatek_id,import_date))

                for i in range(5,len(row)-1,2):
                    if row[i] and row[i+1]:
                        login  = datetime.strptime(row[4] + " "+ row[i], '%Y/%m/%d %H:%M:%S')
                        logout = datetime.strptime(row[4] + " "+ row[i+1], '%Y/%m/%d %H:%M:%S')
                        login_new_id = attendance_obj.create(cr,uid,{'employee_id':employee_id,
                                                      'name':login.strftime('%Y-%m-%d %H:%M:%S'),
                                                      'action':'sign_in',
                                                      })
                        if login_new_id:
                            self.pool.get('import.attendance.detail').create(cr,uid,{'importer_id':record.id,
                                                                                     'attendance_id':login_new_id})

                        logout_new_id = attendance_obj.create(cr,uid,{'employee_id':employee_id,
                                                      'name':logout.strftime('%Y-%m-%d %H:%M:%S'),
                                                      'action':'sign_out',
                                                      })

                        if logout_new_id:
                            self.pool.get('import.attendance.detail').create(cr,uid,{'importer_id':record.id,
                                                                                     'attendance_id':logout_new_id})
                total_working_hours = row[len(row)-1]
                default_hourly_rate = 0
                default_contract_id = self.pool.get('hr.contract').search(cr,uid,[('employee_id','=',employee_id)])
                if default_contract_id and len(default_contract_id)>0:
                    default_contract_id = default_contract_id[0]
                    # default_hourly_rate = self.pool.get('hr.contract').browse(cr,uid,default_contract_id).hourly_rate
                else:
                    default_contract_id = None
                default_hourly_rate = self.pool.get('hr.employee').browse(cr,uid,employee_id).hourly_rate
                new_costing_detail = self.pool.get('import.costing.detail').create(cr,uid,{'importer_id':record.id,
                                                                      'employee_id':employee_id,
                                                                      'contract_id':default_contract_id,
                                                                      'hourly_rate':default_hourly_rate,
                                                                      'total_working_hours':total_working_hours,
                                                                      'total_cost':float(default_hourly_rate)*float(total_working_hours)})
        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True


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
                if detail.project_id:
                    project_costing_id = self.pool.get('project.costing').search(cr,uid,[('project_id','=',detail.project_id.id)])
                    if project_costing_id and len(project_costing_id)>0:
                        project_costing_id = project_costing_id[0]
                        self.pool.get('project.hr.cost').create(cr,uid,{'project_costing_id':project_costing_id,
                                                                        'employee_id':detail.employee_id.id,
                                                                        'importer_id':importer.id,
                                                                        'amount':detail.total_cost,
                                                                        })


    _columns = {
        'numero':fields.char('Test',size=255),
        'attendance_detail_ids':fields.one2many('import.attendance.detail','importer_id','Detail Ids'),
        'costing_detail_ids':fields.one2many('import.costing.detail','importer_id','Costing Detail Ids'),
        'total_cost':fields.function(_get_total_cost, digits_compute=dp.get_precision('Account'),
                                          string='Total Cost',multi='value',
                                           track_visibility='always'),
        'date_import' : fields.datetime(string='Date Import',
                                    readonly=True, states={'draft': [('readonly', False)]}, index=True,
                                    help="Keep empty to use the current date", copy=False),
        'imported_by':fields.many2one('res.users','Imported by'),
        'state':fields.selection([
            ('draft','Draft'),
            ('submitted','Confirmed'),
            ('approved','Approved'),
            ('rejected','Rejected'),
            ('done','Done'),
            ('cancelled','Cancelled')], 'State',),
    }
    _defaults={
        'state':'draft',
        'date_import': fields.datetime.now,
    }

ftb_importer()

class import_attendance_detail(osv.osv):
    _name = 'import.attendance.detail'

    _columns={
        'importer_id':fields.many2one('ftb.importer','Importer'),
        'attendance_id':fields.many2one('hr.attendance'),
        'employee_id':fields.related('attendance_id','employee_id',type='many2one',relation='hr.employee',string='Employee'),
        'time':fields.related('attendance_id','name',type='datetime',string='Time'),
        'action':fields.related('attendance_id','action',string='Action',type='char'),


    }

class import_costing_detail(osv.osv):
    _name = 'import.costing.detail'

    def _get_total_cost(self,cr,uid,ids,a,b,context={}):
        res = {}
        for line in self.browse(cr,uid,ids):
            res[line.id] = line.hourly_rate * line.total_working_hours
        return res

    _columns={
        'importer_id':fields.many2one('ftb.importer','Importer'),
        'employee_id':fields.many2one('hr.employee','Employee'),
        'total_working_hours':fields.float('Total Working Hours',digits_compute=dp.get_precision('Account'),),
        'contract_id':fields.many2one('hr.contract','Contract'),
        'total_cost':fields.function(_get_total_cost, digits_compute=dp.get_precision('Account'),
                                          string='Total Cost',
                                           track_visibility='always'),
        'hourly_rate':fields.float('Hourly Rate',digits_compute=dp.get_precision('Account'),),
        'project_id':fields.many2one('project.project','Project'),
    }

