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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from datetime import datetime, timedelta
import time
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta

class tgb_inventory_inventory(osv.osv):
    _name = "tgb.inventory.inventory"
    
    _columns = {
        'name': fields.char('Name', size=1024),
        'type': fields.selection([('inventory', 'Inventory'),
                                  ('card', 'Card'),
                                  ('phone_line', 'Phone Line'),
                                  ('mobile_plan', 'Mobile Plan')], 'Type'),
        'inventory_line': fields.one2many('tgb.inventory.inventory.line', 'inventory_id', 'Inventory Line'),
        'inventory_card_line': fields.one2many('tgb.inventory.card.line', 'inventory_id', 'Inventory Card Line'),
        'inventory_mobile_plan_line': fields.one2many('tgb.inventory.mobile.plan.line', 'inventory_id', 'Inventory Mobile Plan Line'),
        'inventory_phone_line': fields.one2many('tgb.inventory.phone.line', 'inventory_id', 'Inventory Phone Line'),
        'tgb_type': fields.selection([('office_inventory', 'Office Inventor'),
                                  ('site_inventory', 'Site Inventory'),
                                  ('mobile_plan', 'Mobile Plan')], 'TGB Type'),
    }
    
    _defaults = {
        'type': 'inventory',
    }
    
tgb_inventory_inventory()

class tgb_inventory_inventory_line(osv.osv):
    _name = "tgb.inventory.inventory.line"
    
    _columns = {
        'inventory_id': fields.many2one('tgb.inventory.inventory', 'Inventory', ondelte='cascade'),
        'employee_id': fields.many2one('hr.employee', "User's Name"),
        'brand': fields.char('Brand', size=1024),
        'specs': fields.char('Specs', size=1024),
        'serial_no': fields.char('Serial No', size=1024),
        'model_part_no': fields.char('Model Part No', size=1024),
        'date_out': fields.date('Date Out'),
        'date_of_hand_over': fields.date('Date of Hand Over'),
        'site_no_id': fields.many2one('res.partner', 'Site No'),
        'client_name_id': fields.many2one('res.partner', "Client's Name"),
        'remark': fields.char('Remarks', size=1024),
    }
    
    def onchange_site_no_id(self, cr, uid, ids, site_no_id=False, context=None):
        vals = {}
        if site_no_id:
            site_no = self.pool.get('res.partner').browse(cr, uid, site_no_id)
            vals = {
                'client_name_id': site_no.parent_id and site_no.parent_id.id or False,
            }
        return {'value': vals}
    
tgb_inventory_inventory_line()

class tgb_inventory_card_line(osv.osv):
    _name = "tgb.inventory.card.line"
    
    _columns = {
        'inventory_id': fields.many2one('tgb.inventory.inventory', 'Inventory', ondelte='cascade'),
        'number': fields.char('Number', size=1024),
        'type': fields.char('Type', size=1024),
    }
    
tgb_inventory_card_line()

class tgb_inventory_mobile_plan_line(osv.osv):
    _name = "tgb.inventory.mobile.plan.line"
    
    _columns = {
        'inventory_id': fields.many2one('tgb.inventory.inventory', 'Inventory', ondelte='cascade'),
        'user_id': fields.many2one('res.users', "User"),
        'number': fields.char('Number', size=1024),
        'description': fields.char('Description', size=1024),
    }
    
tgb_inventory_mobile_plan_line()

class tgb_inventory_phone_line(osv.osv):
    _name = "tgb.inventory.phone.line"
    
    _columns = {
        'inventory_id': fields.many2one('tgb.inventory.inventory', 'Inventory', ondelte='cascade'),
        'number': fields.char('Number', size=1024),
        'name': fields.char('Name', size=1024),
    }
    
tgb_inventory_phone_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: