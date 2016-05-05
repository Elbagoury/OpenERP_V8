# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import psycopg2
from openerp.osv import orm, fields
import xlrd
from base64 import b64decode
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
import math

import itertools
import csv
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO





class ftb_importer(orm.TransientModel):
    _inherit = 'base_import.import'
    _name = 'ftb.importer'

    def do(self, cr, uid, ids,context=None):
        cr.execute('SAVEPOINT import')
        # contract_ids = self.pool.get('dk.contract').search(cr,uid,[])
        # self.pool.get('dk.contract').write(cr,uid,contract_ids,{'state':'progress'})
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            workbook = xlrd.open_workbook(file_contents=b64decode(record.file))
            sheet = workbook.sheet_by_index(0)
            type_list = []
            for r in range(0,sheet.nrows):
                if r>=1:
                    row = sheet.row_values(r)
                    print row
                    customer = row[1]
                    customer_obj = self.pool.get('res.partner')
                    customer_id = customer_obj.search(cr,uid,[('name','=',customer)])
                    if customer_id and len(customer_id)>0:
                        customer_id = customer_id[0]
                    else:
                        customer_add = row[2]

                        customer_tel = row[4]
                        customer_tel = customer_tel.split('/')
                        tel = customer_tel[0]
                        mobile=''
                        if len(customer_tel)>1:
                            mobile = customer_tel[1]
                        customer_id = customer_obj.create(cr,uid,{
                            'name':customer,
                            'street':customer_add,
                            'phone':tel,
                            'mobile':mobile,
                        })
                    ref_no = row[3]
                    type = row[5]
                    type_id = self.pool.get('dk.contract.type').search(cr,uid,[('name','=','type')])

                    if type_id and len(type_id)>0:
                        type_id = type_id[0]
                    else:
                        type_id = self.pool.get('dk.contract.type').create(cr,uid,{'name':type})
                    print 'type_id', type_id, type

                    qty = row[6]
                    start_date = row[7]
                    exp_date = row[8]
                    remarks = row[9]
                    last_svs_day = row[10]
                    schedule_date = row[11]
                    location = row[14]
                    location_obj = self.pool.get('dk.location')
                    location_id = location_obj.search(cr,uid,[('name','=',location)])
                    if location_id and len(location_id)>0:
                        location_id = location_id[0]
                    else:
                        location_id = location_obj.create(cr,uid,{'name':location})
                    note = row[15]
                    cheque_cash = row[16]
                    amount = row[17]
                    print 'schedule_date before',schedule_date
                    print 'last_svs_day before',last_svs_day
                    dk_contract_obj = self.pool.get('dk.contract')
                    if last_svs_day == '-' or not last_svs_day:
                        last_svs_day = False
                    if schedule_date == '-' or not schedule_date:
                        schedule_date = False

                    if last_svs_day:
                        last_svs_day = datetime(*xlrd.xldate_as_tuple(last_svs_day, workbook.datemode))
                    if schedule_date:
                        schedule_date = datetime(*xlrd.xldate_as_tuple(schedule_date, workbook.datemode))

                    print 'last_svs_day',last_svs_day
                    print 'schedule_date', schedule_date
                    new_contract = {
                                                    'partner_id':customer_id,
                                                    'ref_no':ref_no,
                                                    'type':type_id,
                                                    'qty':qty,
                                                    'start_date':start_date,
                                                    'exp_date':exp_date,
                                                    'remarks':remarks,
                                                    'last_svs_day':last_svs_day,
                                                    'schedule_date':schedule_date,
                                                    'location_id':location_id,
                                                    'note':note,
                                                    'cheque_cash':cheque_cash,
                                                    'amount':amount,
                    }
                    print 'new contract', new_contract
                    dk_contract_obj.create(cr,uid,new_contract)

        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True


    def import_type(self, cr, uid, ids,context=None):
        cr.execute('SAVEPOINT import')
        # contract_ids = self.pool.get('dk.contract').search(cr,uid,[])
        # self.pool.get('dk.contract').write(cr,uid,contract_ids,{'state':'progress'})
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            workbook = xlrd.open_workbook(file_contents=b64decode(record.file))
            sheet = workbook.sheet_by_index(0)
            type_list = []
            for r in range(0,sheet.nrows):
                if r>=1:
                    row = sheet.row_values(r)
                    type = row[13]
                    type_list.append(type)
            type_list = list(set(type_list))
            for type in type_list:
                self.pool.get('dk.contract.type').create(cr,uid,{'name':type})
        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True


    def do2(self, cr, uid, ids,context=None):
        cr.execute('SAVEPOINT import')
        # contract_ids = self.pool.get('dk.contract').search(cr,uid,[])
        # self.pool.get('dk.contract').write(cr,uid,contract_ids,{'state':'progress'})
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            workbook = xlrd.open_workbook(file_contents=b64decode(record.file))
            sheet = workbook.sheet_by_index(0)
            type_list = []
            for r in range(0,sheet.nrows):
                if r>=1:
                    row = sheet.row_values(r)
                    customer = row[0]
                    customer_obj = self.pool.get('res.partner')
                    customer_id = customer_obj.search(cr,uid,[('name','=',customer)])
                    city = row[8]
                    email = row[9]
                    if customer_id and len(customer_id)>0:
                        customer_id = customer_id[0]
                    else:
                        customer_add = row[1]
                        customer_id = customer_obj.create(cr,uid,{
                            'name':customer,
                            'street':customer_add,
                            'city':city,
                            'email':email,
                            })
                    type = row[13]
                    type_id = self.pool.get('dk.contract.type').search(cr,uid,[('name','=',type)])
                    if type_id and len(type_id)>0:
                        type_id = type_id[0]
                    else:
                        type_id = self.pool.get('dk.contract.type').search(cr,uid,[])[0].id

                    contact_person = row[2]
                    print 'contact_person_id', contact_person
                    contact_person_number = row[3]
                    location_of_service = row[4]
                    contact_person_id = customer_obj.search(cr,uid,[('name','=',contact_person)])
                    print 'contact_person_id', contact_person_id
                    if contact_person_id and len(contact_person_id)>0:
                        contact_person_id = contact_person_id[0]
                    else:
                        contact_person_id = customer_obj.create(cr,uid,{
                            'name':contact_person_id,
                            'street':location_of_service,
                            'phone':contact_person_number,

                            })

                    print 'contact_person_id', contact_person_id

                    start_date = row[5]
                    exp_date = row[6]

                    start_year = start_date[-2:]
                    start_month = start_date[:-3]
                    exp_year = exp_date[-2:]
                    exp_month = exp_date[:-3]

                    print 'exp_year' , exp_year
                    print 'exp_month ', exp_month

                    if start_month =='JAN':
                        start_month = '01'
                    elif start_month == 'FEB':
                        start_month = '02'
                    elif start_month == 'MAR':
                        start_month = '03'
                    elif start_month == 'APR':
                        start_month = '04'
                    elif start_month == 'MAY':
                        start_month = '05'
                    elif start_month == 'JUN':
                        start_month = '06'
                    elif start_month == 'JUL':
                        start_month = '07'
                    elif start_month == 'AUG':
                        start_month = '08'
                    elif start_month == 'SEP':
                        start_month = '09'
                    elif start_month == 'OCT':
                        start_month = '10'
                    elif start_month == 'NOV':
                        start_month = '11'
                    elif start_month == 'DEC':
                        start_month = '12'

                    if exp_month =='JAN':
                        exp_month = '01'
                    elif exp_month == 'FEB':
                        exp_month = '02'
                    elif exp_month == 'MAR':
                        exp_month = '03'
                    elif exp_month == 'APR':
                        exp_month = '04'
                    elif exp_month == 'MAY':
                        exp_month = '05'
                    elif exp_month == 'JUN':
                        exp_month = '06'
                    elif exp_month == 'JUL':
                        exp_month = '07'
                    elif exp_month == 'AUG':
                        exp_month = '08'
                    elif exp_month == 'SEP':
                        exp_month = '09'
                    elif exp_month == 'OCT':
                        exp_month = '10'
                    elif exp_month == 'NOV':
                        exp_month = '11'
                    elif exp_month == 'DEC':
                        exp_month = '12'

                    start_code = start_month + '/20'+start_year
                    exp_code = exp_month + '/20'+exp_year

                    print 'exp_code', exp_code
                    print 'start_code', start_code

                    start_date_ids = self.pool.get('account.period').search(cr,uid,[('code','=',start_code)])
                    exp_date_ids = self.pool.get('account.period').search(cr,uid,[('code','=',exp_code)])

                    start_period= None
                    exp_period = None

                    if start_date_ids and len(start_date_ids)>0:
                        start_period = start_date_ids[0]

                    if exp_date_ids and len(exp_date_ids)>0:
                        exp_period = exp_date_ids[0]


                    amount = row[7]
                    dk_contract_obj = self.pool.get('dk.contract')

                    new_contract = {
                        'partner_id':customer_id,
                        'type':type_id,
                        'start_date2':start_period,
                        'exp_date2':exp_period,
                        'amount':amount,
                        'state':'exp',
                        'location_of_service':location_of_service,
                        'contact_person_id':contact_person_id,
                        }
                    print 'new contract', new_contract
                    if customer_id and type_id and start_period and exp_period:
                        dk_contract_obj.create(cr,uid,new_contract)

        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True

    def set_process_contact(self, cr, uid, ids, context=None):
        contract_ids = self.pool.get('dk.contract').search(cr,uid,[('state','in',['exp','renew'])])
        self.pool.get('dk.contract').write(cr,uid,contract_ids,{'state':'progress'})
        return True

    def change_period_contract(self,cr,uid,ids,context=None):
        contract_ids = self.pool.get('dk.contract').search(cr,uid,[])
        for contract in self.pool.get('dk.contract').browse(cr,uid,contract_ids):
            start_date = contract.start_date
            exp_date = contract.exp_date
            start_code = start_date[2:]+'/'+'20'+start_date[:-2]
            print 'start_code', start_code, start_date
            exp_code = exp_date[2:]+'/'+'20'+exp_date[:-2]
            print 'exp_code', exp_code, exp_date, contract.ref_no
        return True

    last_invoice_id = False

    def import_data_paypal_module(self,cr,uid,ids,context=None):
        cr.execute('SAVEPOINT import')
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            workbook = xlrd.open_workbook(file_contents=b64decode(record.file))
            sheet = workbook.sheet_by_index(0)
            type_list = []
            for r in range(0,sheet.nrows):
                if r>=1:
                    row = sheet.row_values(r)
                    invoice_no =  row[0]
                    if invoice_no:
                        self.last_invoice_id=False
                    date = row[1]
                    payment_term = row[2]
                    payment_date = row[3]
                    customer = ''
                    customer_phone = ''
                    if row[4]:
                        customer_info = str(row[6]).split(':')
                        customer = str(customer_info[0]).strip()
                        if len(customer_info)>1:
                            customer_phone = str(customer_info[1]).strip()
                    customer_address = str(row[7]).strip()
                    customer_email = str(row[8]).strip()
                    product_name = str(row[9]).strip()
                    product_description = str(row[10]).strip()
                    qty = row[11]
                    unit_price = row[12]
                    amount = row[14]
                    discount = row[15]
                    customer_id = None
                    if len(customer)>0:
                        partner_obj = self.pool.get('res.partner')
                        customer_is_available = partner_obj.search(cr,uid,[('name','=',customer)])
                        if customer_is_available and len(customer_is_available)>0:
                            customer_id = customer_is_available[0]
                        else:
                            customer_id = partner_obj.create(cr,uid,{'name':customer,
                                                                     'customer':True,
                                                                     'phone':customer_phone,
                                                                     'street':customer_address,
                                                                     'email':customer_email})
                    product_id = None
                    if len(product_name)>0:
                        product_obj =self.pool.get('product.product')
                        product_is_available=product_obj.search(cr,uid,[('name','=',product_name)])
                        if product_is_available and len(product_is_available)>0:
                            product_id = product_is_available[0]
                        else:
                            product_id = product_obj.create(cr,uid,{'name':product_name,
                                                                    'list_price':unit_price})
                    if customer_id and not self.last_invoice_id:
                        p = self.pool.get('res.partner').browse(cr, uid, customer_id)
                        acc_id = p.property_account_receivable.id
                        invoice_obj = self.pool.get('account.invoice')
                        invoice_id = invoice_obj.create(cr,uid,{'partner_id':customer_id,
                                                                'account_id':acc_id})
                        self.last_invoice_id = invoice_id
                        if product_id:
                            discount_percent = 0
                            if discount and amount:
                                try:
                                    discount_percent = float(discount*100)/float(amount)
                                    print 'discount_percent', discount_percent, discount, amount
                                except:
                                    print 'amount', amount, 'discount', discount
                            invoice_line_obj = self.pool.get('account.invoice.line')
                            invoice_line_id = invoice_line_obj.create(cr,uid,{'product_id':product_id,
                                                                              'name':product_description,
                                                                              'quantity':qty,
                                                                              'price_unit':unit_price,
                                                                              'discount': discount_percent,
                                                                              'invoice_id':invoice_id,
                                                                              })

                    if not invoice_no and self.last_invoice_id:
                        if product_id:
                            discount_percent = 0
                            if discount and amount:
                                try:
                                    discount_percent = float(discount*100)/float(amount)
                                    print 'discount_percent', discount_percent,discount, amount
                                except:
                                    print 'amount', amount, 'discount', discount
                            invoice_line_obj = self.pool.get('account.invoice.line')
                            invoice_line_id = invoice_line_obj.create(cr,uid,{'product_id':product_id,
                                                                              'name':product_description,
                                                                              'quantity':qty,
                                                                              'price_unit':unit_price,
                                                                              'discount':discount_percent,
                                                                              'invoice_id':self.last_invoice_id})
                            print 'line_id', invoice_line_id

        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True


    def row_is_empty(self,row=[]):
        for item in row:
            if item:
                return False
        return True

    def all_partner_is_customer(self,cr,uid,ids,context=None):
        partner_ids = self.pool.get('res.partner').search(cr,uid,[('id','>',4)])
        self.pool.get('res.partner').write(cr,uid,partner_ids,{'customer':True})

    def import_for_computer_city(self,cr,uid,ids,context=None):
        cr.execute('SAVEPOINT import')
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            workbook = xlrd.open_workbook(file_contents=b64decode(record.file))
            sheet = workbook.sheet_by_index(0)
            type_list = []
            name=''
            street=''
            street2=''
            city = ''
            state = ''
            zip = ''
            phone=''
            mobile=''
            fax=''
            email=''
            contact=''
            is_company=False
            partner_obj = self.pool.get('res.partner')
            customer=False
            supplier=True
            for r in range(0,sheet.nrows):
                last_row = True
                if r>=0:
                    row = sheet.row_values(r)
                    if row[1]:
                        name = row[1]
                    if row[3]=='First Address:':
                        street=row[4]
                    elif row[3]=='':
                        street2=row[4]
                    elif row[3]=='City:':
                        city = row[4]
                    elif row[3]=='State:':
                        state = row[4]
                    elif row[3]=='Postcode:':
                        zip = row[4]
                    elif row[3]=='Phone #1:':
                        phone = row[4]
                    elif row[3]=='Phone #2:':
                        mobile = row[4]
                    elif row[3]=='FAX #:':
                        fax = row[4]
                    elif row[3]=='Email:':
                        email = row[4]
                    elif row[3]=='Contact:':
                        contact = row[4]
                        is_company = True
                    if row[5]=='Terms:':
                        print 'create new partner', name, street, street2, city, state, zip, phone, mobile, fax, email, contact
                        new_partner_id = partner_obj.create(cr,uid,{'name':name,
                                                   'street':street,
                                                   'street2':street2,
                                                   'city':city,
                                                   'zip':zip,
                                                   'phone':phone,
                                                   'mobile':mobile,
                                                   'fax':fax,
                                                   'email':email,
                                                   'is_company':is_company,
                                                   'customer':customer,
                                                   'supplier':supplier,
                                                   })
                        if contact:
                            print 'contact',contact
                            if new_partner_id:
                                partner_obj.create(cr,uid,{'name':contact,
                                                           'parent_id':new_partner_id})
                        name=''
                        street=''
                        street2=''
                        city = ''
                        state = ''
                        zip = ''
                        phone=''
                        mobile=''
                        fax=''
                        email=''
                        contact=''
        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True

    def import_product_for_computer_city(self,cr,uid,ids,context=None):
        cr.execute('SAVEPOINT import')
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            workbook = xlrd.open_workbook(file_contents=b64decode(record.file))
            sheet = workbook.sheet_by_index(0)
            type_list = []
            name=''
            description=''
            list_price=0
            qty = 0
            product_obj = self.pool.get('product.product')
            for r in range(0,sheet.nrows):
                if r>=10:
                    row = sheet.row_values(r)
                    if row[1]=='Item:':
                        name = row[3]
                        description=row[2]
                    elif row[1]=='On Hand:':
                        qty=row[2]
                    elif row[1]=='Value:':
                        if row[2]:
                            price = row[2].replace('$','')
                            price = price.replace(',','')
                            price = price.replace('(','')
                            price = price.replace(')','')
                            print 'price',price
                            list_price = float(price)
                    if self.row_is_empty(row) and name:
                        print 'create new product', name,  description, list_price, qty
                        new_product = product_obj.create(cr,uid,{'name':name,
                                                   'description':description,
                                                   'standard_price':list_price,
                                                   'qty_available':qty
                                                   })
                        name=''
                        description=''
                        list_price=0
                        qty = 0
        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True


    def import_attendance_for_construction(self,cr,uid,ids,context=None):
        cr.execute('SAVEPOINT import')
        record = self.browse(cr, uid, ids, context=context)[0]
        csv_reader = csv.reader(StringIO(b64decode(record.file)), delimiter=',', quotechar='"')
        for row in csv_reader:
            timesheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
            attendance_obj = self.pool.get('hr.attendance')
            if row[0]!='No.':
                actatek_id = row[1]
                import_date = row[4]
                employee_id = self.pool.get('hr.employee').search(cr,uid,[('actatek_id','=',actatek_id)])
                if employee_id and len(employee_id)>0:
                    employee_id = employee_id[0]
                else:
                    raise osv.except_osv(_('Error!'),_("No employee defined for ID %s ") % (actatek_id))
                import_date =  datetime.strptime(import_date, '%Y/%m/%d')
                sheet_id = timesheet_obj.search(cr,uid,[('date_from','<=',import_date),('date_to','>=',import_date)])
                if sheet_id and len(sheet_id)>0:
                    sheet_id = sheet_id[0]
                else:
                    raise osv.except_osv(_('Error!'),_("No timesheet defined for ID %s on %s") % (actatek_id,import_date))
                for i in range(5,len(row)-1,2):
                    if row[i] and row[i+1]:
                        print 'we have both sign in and sign out', row[i], row[i+1]
                        login  = datetime.strptime(row[4] + " "+ row[i], '%Y/%m/%d %H:%M:%S')
                        logout = datetime.strptime(row[4] + " "+ row[i+1], '%Y/%m/%d %H:%M:%S')
                        print 'login', login.strftime('%Y-%m-%d %H:%M:%S')
                        print 'logout', login.strftime('%Y-%m-%d %H:%M:%S')
                        login_new_id = attendance_obj.create(cr,uid,{'employee_id':employee_id,
                                                      'name':login.strftime('%Y-%m-%d %H:%M:%S'),
                                                      'action':'sign_in',
                                                      })

                        print 'login new id', login_new_id

                        logout_new_id = attendance_obj.create(cr,uid,{'employee_id':employee_id,
                                                      'name':logout.strftime('%Y-%m-%d %H:%M:%S'),
                                                      'action':'sign_out',
                                                      })

                        print 'logout_new_id', logout_new_id
        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True


    _columns = {
        'numero':fields.char('Test',size=255),

    }

ftb_importer()