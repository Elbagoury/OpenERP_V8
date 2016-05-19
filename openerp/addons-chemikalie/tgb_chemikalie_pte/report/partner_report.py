# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from openerp.report import report_sxw
from openerp.osv import osv
from openerp.tools.translate import _
import random
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
from dateutil.tz import tzlocal
from tzlocal import get_localzone
class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            'get_datenow': self.get_datenow,
            'get_partner_full_address': self.get_partner_full_address,
            'get_list_partner': self.get_list_partner,
            'get_contact': self.get_contact,
            'get_partner_full_delivery_address': self.get_partner_full_delivery_address,
        })
        
    def get_datenow(self):
        return time.strftime('%d/%m/%Y')

    def get_list_partner(self):
        partners = []
        if self.context.get('active_ids', []):
            partners = self.pool.get('res.partner').browse(self.cr, self.uid, self.context['active_ids'])
        return partners

    def get_partner_full_address(self, partner_id):
        address = ''
        if partner_id:
            partner = self.pool.get('res.partner').browse(self.cr, self.uid, partner_id)
            if partner.street:
                address += partner.street+' '
            if partner.street2:
                address += partner.street2+' '
            if partner.country_id:
                address += partner.country_id and partner.country_id.name or ''+' '
            if partner.zip:
                address += partner.zip+' '
        return address
    
    def get_partner_full_delivery_address(self, partner_id):
        address = ''
        if partner_id:
            partner = self.pool.get('res.partner').browse(self.cr, self.uid, partner_id)
            if partner.delivery_street:
                address += partner.delivery_street+' '
            if partner.delivery_street2:
                address += partner.delivery_street2+' '
            if partner.delivery_country_id:
                address += partner.delivery_country_id and partner.delivery_country_id.name or ''+' '
            if partner.delivery_zip:
                address += partner.delivery_zip+' '
        return address
    
    def get_contact(self, partner):
        contact = ''
        if partner and partner.child_ids:
            contact = partner.child_ids[0].name
        return contact
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

