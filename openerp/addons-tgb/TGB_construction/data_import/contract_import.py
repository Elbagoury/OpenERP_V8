# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import psycopg2
from openerp.osv import orm, fields
import xlrd
from base64 import b64decode
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
import math


class dksquare_contract_import(orm.TransientModel):
    _inherit = 'base_import.import'
    _name = 'dksquare.contract.import'




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

    def change_period_contract(self,cr,uid,ids,context=None):
        contract_ids = self.pool.get('dk.contract').search(cr,uid,[])
        for contract in self.pool.get('dk.contract').browse(cr,uid,contract_ids):
            start_date = contract.start_date
            exp_date = contract.exp_date
            start_code = start_date[2:]+'/'+'20'+start_date[:-2]
            exp_code = exp_date[2:]+'/'+'20'+exp_date[:-2]
        return True


    def import_employee(self, cr, uid, ids,context=None):
        cr.execute('SAVEPOINT import')
        # contract_ids = self.pool.get('dk.contract').search(cr,uid,[])
        # self.pool.get('dk.contract').write(cr,uid,contract_ids,{'state':'progress'})
        record = self.browse(cr, uid, ids, context=context)[0]
        if record.file:
            workbook = xlrd.open_workbook(file_contents=b64decode(record.file))
            sheet = workbook.sheet_by_index(0)
            type_list = []
            for r in range(0,sheet.nrows):
                if r>=6:
                    row = sheet.row_values(r)
                    name = row[1]
                    if name!="Name" and name!="":
                        nationality = row[2]
                        dob = row[3]
                        if dob =='-':
                            dob = None
                        else:
                            dob = datetime.strptime(dob, '%d/%m/%Y')
                        ic_no = row[4]
                        passport_no = row[5]
                        passport_exp = row[6]
                        passport_exp = passport_exp.strip()
                        if passport_exp=='-' or not passport_exp:
                            passport_exp= None
                        else:
                            passport_exp = datetime.strptime(passport_exp, '%d/%m/%Y')
                        fin_no = row[7]
                        work_permit_no = row[8]
                        work_permit_exp = row[9]
                        work_permit_exp=work_permit_exp.strip()
                        if work_permit_exp=='-' or  work_permit_exp=='':
                            work_permit_exp = None
                        else:
                            work_permit_exp= datetime.strptime(work_permit_exp, '%d/%m/%Y')
                        soc_no = row[10]
                        soc_exp=row[11]
                        soc_exp = soc_exp.strip()
                        if soc_exp =='-' or soc_exp =='':
                            soc_exp = None
                        else:
                            soc_exp = datetime.strptime(soc_exp, '%d/%m/%Y')
                        safety_supervisor_course = row[12]
                        other_cert = row[13]
                        other_cert_exp = row[14]
                        if other_cert_exp=='-' or not other_cert_exp:
                            other_cert_exp = None
                        else:
                            other_cert_exp = datetime.strptime(other_cert_exp, '%d/%m/%Y')

                        date_of_commencement=row[15]
                        if date_of_commencement=='-' or not date_of_commencement:
                            date_of_commencement = None
                        else:
                            date_of_commencement = datetime.strptime(date_of_commencement, '%d/%m/%Y')
                        designation = row[16]
                        address=row[17]
                        # acta_id=str(row[0])
                        # if len(acta_id)==1:
                        #     acta_id = '00'+acta_id
                        # elif len(acta_id)==2:
                        #     acta_id = '0'+acta_id
                        nationality_id = self.pool.get('res.country').search(cr,uid,[('name','=',nationality)])
                        if nationality_id and len(nationality_id)>0:
                            nationality_id=nationality_id[0]
                        else:
                            nationality_id = self.pool.get('res.country').create(cr,uid,{'name':nationality})

                        new_employee = self.pool.get('hr.employee').create(cr,uid,{'name':name,
                                                                                   'country_id':nationality_id,
                                                                                   'birthday':dob,
                                                                                   'identification_id':ic_no,
                                                                                   'passport_id':passport_no,
                                                                                   'passport_exp':passport_exp,
                                                                                   'fin_no':fin_no,
                                                                                   'work_permit_no':work_permit_no,
                                                                                   'work_permit_exp':work_permit_exp,
                                                                                   'SOC_no':soc_no,
                                                                                   'SOC_exp':soc_exp,
                                                                                   'safety_supervisor_course':safety_supervisor_course,
                                                                                   'other_cert':other_cert,
                                                                                   'date_of_commencement':date_of_commencement,
                                                                                   'designation':designation,
                                                                                   # 'actatek_id':acta_id,

                                                                                   })


        try:
            cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return True

    _columns = {

    }

dksquare_contract_import()