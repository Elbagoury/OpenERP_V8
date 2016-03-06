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
import datetime
import time
import calendar

class test_web(osv.osv):
    _name = 'test.web'
    
    _columns = {
        'name': fields.text('Name'),
        'test_web_line': fields.one2many('test.web.line', 'test_web_id', 'Test Web Line'),
        'number': fields.float('Number'),
    }
    
test_web()

class test_web_line(osv.osv):
    _name = 'test.web.line'
    
    _columns = {
        'test_web_id': fields.many2one('test.web', 'Test Web', ondelete='cascade'),
        'x': fields.char('X'),
        'y': fields.char('Y'),
        'value': fields.float('Value'),
    }
    
test_web_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: