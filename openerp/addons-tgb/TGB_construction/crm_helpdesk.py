# -*- coding: utf-8 -*-

import openerp
from openerp.addons.crm import crm
from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import html2plaintext


class crm_helpdesk(osv.osv):

    _inherit = "crm.helpdesk"
    _description = "Helpdesk"
    _order = "id desc"

    def create(self, cr, uid, vals, context=None):
        if vals.get('log_number','/')=='/':
            vals['log_number'] = self.pool.get('ir.sequence').get(cr, uid, 'crm.helpdesk', context=context) or '/'
        context = dict(context or {}, mail_create_nolog=True)
        this_project =  super(crm_helpdesk, self).create(cr, uid, vals, context=context)
        return this_project


    _columns = {
            'complain_type': fields.selection([('minor','Minor'), ('moderate','Moderate'), ('major','Major')], 'Type'),
            'log_number':fields.char('Log number',size=20,required=True),
    }

    _defaults = {
        'complain_type':'minor',
        'log_number':'/',

    }

