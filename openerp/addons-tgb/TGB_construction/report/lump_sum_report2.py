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

class lump_sum_quotation2(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(lump_sum_quotation2, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_tgb_address': self.get_tgb_address,
        })

    def get_tgb_address(self, partner):
        add = ''
        if partner:
            if partner.street:
                add += partner.street+'\n'
            if partner.street2:
                add += partner.street2+'\n'
            if partner.country_id:
                add += partner.country_id.name+' '
            if partner.zip:
                add += partner.zip
        return add

report_sxw.report_sxw('report.lump.sum2', 'sale.order', 'addons/TGB_construction/report/lump_sum_report2.rml', parser=lump_sum_quotation2, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

