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
from openerp.addons.tgb_seawalk_hardware_trading.report import amount_to_text_en

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            'get_datenow': self.get_datenow,
            'convert_date_d_m_Y': self.convert_date_d_m_Y,
            'get_contact': self.get_contact,
            'get_do_no': self.get_do_no,
            'convert': self.convert,
        })
        
    def get_datenow(self):
        return time.strftime('%d/%m/%Y')

    def convert(self, amount):
        amount_text = amount_to_text_en.amount_to_text(amount, 'en', ' ')
        return amount_text.upper()

    def convert_date_d_m_Y(self,date):
        if date:
            return datetime.strptime(date,'%Y-%m-%d').strftime('%d/%m/%Y')
        return ''

    def get_contact(self, partner):
        contact = ''
        if partner and partner.child_ids:
            contact = partner.child_ids[0].name
        return contact

    
    def get_do_no(self, origin):
        do_no = ''
        if origin:
            sql = '''
                select name from stock_picking where name='%s'
            '''%(origin)
            self.cr.execute(sql)
            do = self.cr.fetchone()
            if not do:
                sql = '''
                    select name from stock_picking where origin='%s'
                '''%(origin)
                self.cr.execute(sql)
                do = self.cr.fetchone()
                return do and do[0] or ''
            else:
                return do[0]
        return do_no
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
