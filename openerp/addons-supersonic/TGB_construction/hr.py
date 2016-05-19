# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class hr_employee(osv.osv):
    _inherit = "hr.employee"
    _description = "Employee"

    _columns = {
        #we need a related field in order to be able to sort the employee by name
        'actatek_id':fields.char('ActaTek Id', size=64),
        'passport_exp':fields.date('Passport Expiry Date'),
        'fin_no':fields.char('Fin No', size=255),
        'work_permit_no':fields.char('Work Permit No', size=255),
        'work_permit_exp':fields.date('Work Permit Expiry Date'),
        'SOC_no':fields.char('SOC No', size=255),
        'SOC_exp':fields.date('SOC Expiry Date'),
        'safety_supervisor_course':fields.char('Safety Supervisor Course', size=255),
        'other_cert':fields.char('Other Cert', size=255),
        'other_cert_exp':fields.date('Other Cert Expiry Date'),
        'date_of_commencement':fields.char('Date of Commencement', size=255),
        'designation':fields.char('Designation', size=255),
        'hourly_rate':fields.float('Hourly Rate', digits_compute=dp.get_precision('Account')),
    }
    _defaults={
        'hourly_rate':4,
    }
hr_employee()

class TGB_hr_timesheet_sheet(osv.osv):
    _inherit = "hr_timesheet_sheet.sheet"
    _description = "Timesheet"

    def action_send_to_cost(self,cr,uid,ids,context={}):
        for sheet in self.browse(cr,uid,ids):
            if sheet.TGB_contract_id and sheet.TGB_project_id:
                costing_obj = self.pool.get('project.costing')
                project_costing_id = costing_obj.search(cr,uid,[('project_id','=',sheet.TGB_project_id.id)])
                if project_costing_id and len(project_costing_id)>0:
                    project_costing_id=project_costing_id[0]
                    if sheet.TGB_contract_id.is_hourly_contract:
                        hourly_rate = sheet.TGB_contract_id.hourly_rate
                        total_hour = sheet.total_attendance
                        total_cost = total_hour*hourly_rate
                        self.pool.get('project.hr.cost').create(cr,uid,{'project_costing_id':project_costing_id,
                                                                        'employee_id':sheet.employee_id.id,
                                                                        'timesheet_id':sheet.id,
                                                                        'amount':total_cost,})
                    else:
                        raise osv.except_osv(_('Error!'),_("For now we only support contract with hourly rate") )
            else:
                raise osv.except_osv(_('Error!'),_("No contract or project defined for this timesheet") )
            self.write(cr,uid,sheet.id,{'costed':True})

    _columns = {
        'TGB_contract_id':fields.many2one('hr.contract','Contract'),
        'TGB_project_id':fields.many2one('project.project','Project'),
        'costed':fields.boolean('Costed'),
    }
    _defaults={
        'costed':False,
    }
TGB_hr_timesheet_sheet()