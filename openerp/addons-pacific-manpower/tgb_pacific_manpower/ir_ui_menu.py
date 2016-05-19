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

class ir_ui_menu(osv.osv):
    _inherit = 'ir.ui.menu'

    _columns = {
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True,
    }
    
    def _auto_init(self, cr, context=None):
        super(ir_ui_menu, self)._auto_init(cr, context)
        def browse_rec(root, pos=0):
            cr.execute("SELECT id FROM ir_ui_menu WHERE parent_id=%s order by sequence"%(root))
            pos2 = pos + 1
            for id in cr.fetchall():
                pos2 = browse_rec(id[0], pos2)
            cr.execute('update ir_ui_menu set parent_left=%s, parent_right=%s where id=%s', (pos, pos2, root))
            return pos2 + 1  
        query = "SELECT id FROM ir_ui_menu WHERE parent_id IS NULL order by sequence"
        pos = 0
        cr.execute(query)
        for (root,) in cr.fetchall():
            pos = browse_rec(root, pos)
    
ir_ui_menu()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: