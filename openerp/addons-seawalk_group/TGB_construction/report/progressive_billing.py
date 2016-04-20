# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time

from openerp.report import report_sxw

class report_progressive_billing(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(report_progressive_billing, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_time_claim':self._get_time_claim,
            'get_total_contract_sum':self._get_total_contract_sum,
            'get_total_work_to_date':self._get_total_work_to_date,
            'get_total_work_previous_date':self._get_total_work_previous_date,
            'get_total_this_valuation':self._get_total_this_valuation,
            'get_retention_amount':self._get_retention_amount,
        })

    def _get_retention_amount(self,o):
        res = []
        if o.retention_required:
            des = 'Less '
            if o.retention_type == 'P':
                des +=' retention '+ str(o.retention_percent)+'% (Capped at '+str(o.retention_percent)+'% Contract Value)'
                res.append(des)
                res.append(o.amount_claim_todate*o.retention_percent/100)
                return res
            elif o.retention_type=='A':
                des += ' retention amount'
                res.append(des)
                res.append(o.retention_amount)
                return res
        return []



    def _get_time_claim(self,o):
        if o.billing_time>0:
            number = str(o.billing_time)
            end =1
            end = number[len(number)-1]
            if end =='1':
                return number+'st'
            elif end =='2':
                return number +'nd'
            elif end =='3':
                return number + 'rd'
            else:
                return number + 'th'
        else:
            return '1st'
        return '1st'

    def _get_total_contract_sum(self,billing, context=None):
        total = 0
        for line in billing.line_ids:
            total += line.contract_sum
        return total

    def _get_total_work_to_date(self,billing, context=None):
        total = 0
        for line in billing.line_ids:
            total += line.total_work_to_date
        return total

    def _get_total_work_previous_date(self,billing, context=None):
        total = 0
        for line in billing.line_ids:
            total += line.total_work_previous_date
        return total

    def _get_total_this_valuation(self,billing, context=None):
        total = 0
        for line in billing.line_ids:
            total += line.this_valuation
        return total



report_sxw.report_sxw('report.progressive.billing', 'progressive.billing', 'addons/TGB_construction/report/progressive_billing.rml', parser=report_progressive_billing, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

