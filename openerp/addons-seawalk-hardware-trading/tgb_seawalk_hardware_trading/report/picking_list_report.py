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
            'convert_date_d_B_Y': self.convert_date_d_B_Y,
            'convert_datetime_d_m_Y_H_M': self.convert_datetime_d_m_Y_H_M,
        })
        
    def get_datenow(self):
        return time.strftime('%d/%m/%Y')

    def convert_date_d_B_Y(self,date):
        if date:
            return datetime.strptime(date,'%Y-%m-%d').strftime('%d-%B-%Y')
        return ''
    
    def convert_datetime_d_m_Y_H_M(self,date):
        if date:
            return (datetime.strptime(date,'%Y-%m-%d %H:%M:%S')+timedelta(hours=8)).strftime('%d/%m/%Y %H:%M')
        return ''
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
