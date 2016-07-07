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
from openerp.addons.tgb_rat_trading_report.report import amount_to_text_en
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            'get_datenow': self.get_datenow,
            'convert_date_d_m_Y': self.convert_date_d_m_Y,
            'convert': self.convert,
            'get_total_amount_paid': self.get_total_amount_paid,
        })
        
    def get_datenow(self):
        return time.strftime('%d/%m/%Y')
    
    def convert_date_d_m_Y(self,date):
        if date:
            return datetime.strptime(date,'%Y-%m-%d').strftime('%d/%m/%Y')
        return ''
    
    def convert(self, amount):
        amount_text = amount_to_text_en.amount_to_text(amount, 'en', ' ')
        return amount_text.upper()
    
    def get_total_amount_paid(self, o):
        total = 0
        if o.rental_id:
            sql = '''
                select id from account_invoice where rental_id=%s and state in ('open','paid')
            '''%(o.rental_id.id)
            self.cr.execute(sql)
            invoice_ids = [r[0] for r in self.cr.fetchall()]
            for invoice in self.pool.get('account.invoice').browse(self.cr, self.uid, invoice_ids):
                for pay in invoice.payment_ids:
                    total+=pay.credit or pay.debit
        return total

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
