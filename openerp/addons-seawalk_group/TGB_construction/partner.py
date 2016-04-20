# -*- coding: utf-8 -*-

from datetime import datetime, date

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _



class partner(osv.osv):
    _inherit = "res.partner"
    _description = "Partner"

    _columns = {
        'supplier_service':fields.char('Services', size=255),
     }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: