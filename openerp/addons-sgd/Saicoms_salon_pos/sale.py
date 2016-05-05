# -*- coding: utf-8 -*-
__author__ = 'Phamkr'
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, \
    float_compare


class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'perform_user_id':fields.many2one('res.users','Performing User'),
        'advisory_id':fields.many2one('res.users','Advisory'),
        'has_friends':fields.boolean('Customer has friend?'),
    }

sale_order()
