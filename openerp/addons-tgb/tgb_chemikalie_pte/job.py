# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP SA (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
import re
import threading
from openerp.tools.safe_eval import safe_eval as eval
from openerp import tools
import openerp.modules
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from datetime import datetime
import time
import calendar
from dateutil.relativedelta import relativedelta

class job_order(osv.osv):
    _name = "job.order"
    
    def _get_count(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for job in self.browse(cr, uid, ids, context=context):
            hours = 0
            if job.date_confirmed and job.state in ['confirmed','done'] and job.priority:
                date_now = time.strftime('%Y-%m-%d %H:%M:%S')
                date_now = datetime.strptime(date_now,'%Y-%m-%d %H:%M:%S')
                date_confirmed = datetime.strptime(job.date_confirmed,'%Y-%m-%d %H:%M:%S')
                if job.date_done:
                    date_now = datetime.strptime(job.date_done,'%Y-%m-%d %H:%M:%S')
                t = date_now-date_confirmed
                temp = t.days*24+t.seconds/3600
                if job.priority=='high':
                    if temp<48:
                        hours = 48-temp
                if job.priority=='medium':
                    if temp<(14*24):
                        hours = (14*24)-temp
                if job.priority=='low':
                    if temp<(30*24):
                        hours = (30*24)-temp
            res[job.id] = hours
        return res
    
    _columns = {
        'name': fields.char('Part No', size=1024,readonly=True, states={'draft': [('readonly', False)]}),
        'date': fields.date('Date',readonly=True, states={'draft': [('readonly', False)]}),
        'partner_id': fields.many2one('res.partner', 'Customer',readonly=True, states={'draft': [('readonly', False)]}),
        'serial_no': fields.char('Serial No', size=1024,readonly=True, states={'draft': [('readonly', False)]}),
        'description': fields.text('Description',readonly=True, states={'draft': [('readonly', False)]}),
        'gate_pass': fields.char('Gate Pass', size=1024,readonly=True, states={'draft': [('readonly', False)]}),
        'priority': fields.selection([('high','High'),('medium','Medium'),('low','Low')], 'Priority',readonly=True, states={'draft': [('readonly', False)]}),
        'date_confirmed': fields.datetime('Date Confirmed'),
        'date_done': fields.datetime('Date Done'),
        'count': fields.function(_get_count,type='float',string='Count (Hours)',digits=(16,0)),
        'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('done','Done')], 'Status'),
    }
    
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'), 
        'state': 'draft',
    }
    
    def bt_confirm(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'confirmed','date_confirmed':time.strftime('%Y-%m-%d %H:%M:%S')})
    
    def bt_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'done','date_done':time.strftime('%Y-%m-%d %H:%M:%S')})
    
job_order()

class valve_failure_report(osv.osv):
    _name = "valve.failure.report"
    
    _columns = {
        'name': fields.char('Service No', size=1024),
        'user_id': fields.many2one('res.users', 'Report by'),
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'date': fields.date('Date'),
        'model': fields.char('Model', size=1024),
        'contact': fields.char('Contact', size=1024),
        'fab_no': fields.char('FAB No', size=1024),
        's_no': fields.char('S/No', size=1024),
        'job_id': fields.many2one('job.order', 'Job Order'),
        
        'service_contract': fields.boolean('Service Contract'),
        'warranty': fields.boolean('Warranty'),
        'new_units': fields.boolean('New Units'),
        'chargeable': fields.boolean('Chargeable'),
        
        'urgent_level': fields.selection([('high','High'),('medium','Medium'),('low','Low')], 'Urgent Level'),
        
        'completion_date_by': fields.date('Completion Date by'),
        
        'failure_analysis': fields.text('Failure Analysis'),
        
        'alignment_of_gate_plate': fields.boolean('Alignment of Gate/Plate'),
        'applied_lock_tight': fields.boolean('Applied Lock tight'),
        'medium_strength': fields.boolean('Medium Strength'),
        'high_strength': fields.boolean('High strength'),
        
        'pneumatic_smc': fields.boolean('Pneumatic (SMC)'),
        'vacuum_grease': fields.boolean('Vacuum Grease'),
        'gear_grease': fields.boolean('Gear Grease'),
        'krytox_240ac': fields.boolean('Krytox 240AC'),
        'pneumatic_vat_black': fields.boolean('Pneumatic (VAT/Black)'),
        'pneumatic_vat_white': fields.boolean('Pneumatic (VAT/White)'),
        'paste': fields.boolean('Paste'),
        'smc_lead_screw': fields.boolean('SMC Lead Screw'),
        
        'low_speed': fields.boolean('Low Speed Motion Controller (Fully Open/Close Position)'),
        'high_speed': fields.boolean('High Speed Motion controler (Fully Open/Closed & 45* position)'),
        
        'post_remarks': fields.text('Remarks'),
        
        'details_remarks': fields.text('Remarks'),
        
        'all_procedure_completed': fields.boolean('All procedure completed?'),
        'sn_vs_customer': fields.boolean('S/N vs Customer'),
        'cleaning_package_status': fields.boolean('Cleaning package status'),
        'valve_fully_closed_after_controlled': fields.boolean('Valve Fully closed after controlled'),
        'cylinder_pressure_check_70psi': fields.boolean('Cylinder Pressure Check(70PSI)'),
        'bellow_gate_not_expose': fields.boolean('Bellow/Gate not expose'),
        'series_number_engraved': fields.boolean('Series Number engraved'),
        
        'serviced_and_inspected': fields.char('Serviced and inspected', size=1024),
        
        'final_date': fields.date('Date'),
    }
    
    _defaults = {
        'user_id': lambda self, cr, uid, ctx=None: uid,
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('tgb_search_for_job', False) and context['tgb_search_for_job']:
            args += [('job_id','=',context['tgb_search_for_job'])]
        
        return super(valve_failure_report, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
    
valve_failure_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: