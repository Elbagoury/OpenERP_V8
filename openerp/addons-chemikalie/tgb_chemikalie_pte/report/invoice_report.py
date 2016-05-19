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
            'get_ship_to_street': self.get_ship_to_street,
            'get_ship_to_street2': self.get_ship_to_street2,
            'get_ship_to_country': self.get_ship_to_country,
            'get_ship_to_zip': self.get_ship_to_zip,
            'get_contact': self.get_contact,
            'get_customer_po_no': self.get_customer_po_no,
            'get_quotation_no': self.get_quotation_no,
            'get_do_no': self.get_do_no,
            'get_bank': self.get_bank,
        })
        
    def get_datenow(self):
        return time.strftime('%d/%m/%Y')

    def convert_date_d_B_Y(self,date):
        if date:
            return datetime.strptime(date,'%Y-%m-%d').strftime('%d-%B-%Y')
        return ''
    
    def get_ship_to_street(self, partner):
        address = ''
        if partner:
            if partner.delivery_street:
                address += partner.delivery_street
            else:
                address += partner.street or ''
        return address
    
    def get_ship_to_street2(self, partner):
        address = ''
        if partner:
            if partner.delivery_street:
                address += partner.delivery_street2 or ''
            else:
                address += partner.street2 or ''
        return address
    
    def get_ship_to_country(self, partner):
        address = ''
        if partner:
            if partner.delivery_street:
                address += partner.delivery_country_id and partner.delivery_country_id.name or ''
            else:
                address += partner.country_id and partner.country_id.name or ''
        return address
    
    def get_ship_to_zip(self, partner):
        address = ''
        if partner:
            if partner.delivery_street:
                address += partner.delivery_zip or ''
            else:
                address += partner.zip or ''
        return address
    
    def get_contact(self, partner):
        contact = ''
        if partner and partner.child_ids:
            contact = partner.child_ids[0].name
        return contact

    def get_customer_po_no(self, origin):
        customer_po_no = ''
        if origin:
            sql = '''
                select customer_po_no from sale_order where name in (select origin from stock_picking where name='%s')
            '''%(origin)
            self.cr.execute(sql)
            sale = self.cr.fetchone()
            if not sale:
                sql = '''
                    select customer_po_no from sale_order where name='%s'
                '''%(origin)
                self.cr.execute(sql)
                sale = self.cr.fetchone()
                return sale and sale[0] or ''
            else:
                return sale[0]
        return customer_po_no
    
    def get_quotation_no(self, origin):
        quotation_no = ''
        if origin:
            sql = '''
                select name from sale_order where name in (select origin from stock_picking where name='%s')
            '''%(origin)
            self.cr.execute(sql)
            sale = self.cr.fetchone()
            if not sale:
                sql = '''
                    select name from sale_order where name='%s'
                '''%(origin)
                self.cr.execute(sql)
                sale = self.cr.fetchone()
                return sale and sale[0] or ''
            else:
                return sale[0]
        return quotation_no
    
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
    
    def get_bank(self, o):
        res = []
        if o.partner_id.bank_ids:
            bank = o.partner_id.bank_ids[0]
            res = [{
                'name': bank.bank_name,
                'address': (bank.street or '')+' '+(bank.street2 or '')+' '+(bank.country_id and bank.country_id.name or '')+' '+(bank.zip or ''),
                'swift_code': bank.swift_code,
                'acc_number': bank.acc_number,
                'usd_acc_number': bank.usd_acc_number,
            }]
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
