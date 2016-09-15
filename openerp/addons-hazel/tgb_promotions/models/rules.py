# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

try:
    #Backward compatible
    from sets import Set as set
except:
    pass
import uuid
import logging
from openerp.osv import osv, fields
from openerp.tools.misc import ustr
#from openerp import netsvc
from openerp.tools.translate import _

#Get the logger
_logger = logging.getLogger(__name__)
#LOGGER = netsvc.Logger()
DEBUG = True
PRODUCT_UOM_ID = 1

class TGBPromotionsRules(osv.Model):
    "Promotion Rules"
    _name = "tgb_promos.rules"
    _description = __doc__
    _order = 'sequence'

    _columns = {
        'name':fields.char('Promo Name', size=50, required=True),
        'sequence': fields.integer('Sequence'),
        'description':fields.text('Description'),
        'active':fields.boolean('Active'),
        'order_mode': fields.selection([('All', 'All'),
                                        ('Online','Online'),
                                        ('Offline', 'Offline'),
                                        ('Miscrosites', 'Miscrosites')],'Mode of order'),
        'accumulated': fields.boolean('Purchase can be accumulated'),
        'combined': fields.boolean('Can be combined with other discount'),
        'last_date': fields.boolean('Last Date of Redemption'),
        'stock': fields.boolean('While stock last'),
        'payment': fields.boolean('Upon payment'),
        'mode_of_payment': fields.selection([('Cash', 'Cash'),
                                             ('Card', 'Card'),
                                             ('Online', 'Online')], 'Mode of payment'),
        #'shop':fields.many2one('sale.shop', 'Shop', required=False),
        'partner_categories':fields.many2many(
                  'res.partner.category',
                  'rule_partner_cat_rel',
                  'category_id',
                  'rule_id',
                  string="Partner Categories",
                  help="Applicable to all if none is selected"
                                              ),
        'from_date':fields.datetime('From Date'),
        'to_date':fields.datetime('To Date'),
        'delivery_from_date':fields.datetime('From Date'),
        'delivery_to_date':fields.datetime('To Date'),
        'conditions': fields.one2many('tgb_promos.condition', 'promo_id', 'Conditions'),
        'products': fields.one2many('tgb_promos.product', 'promo_id', 'Conditions'),
        'products_to_exclude': fields.many2many('product.product', 'tgb_promos_products_to_exclude_ref', 'promo_id', 'product_id', 'Products to exclude'),
        'categories_to_exclude': fields.many2many('product.category', 'tgb_promos_categories_to_exclude_ref', 'promo_id', 'category_id', 'Categories to exclude'),
        'occasions_to_exclude': fields.many2many('product.occasion', 'tgb_promos_occasions_to_exclude_ref', 'promo_id', 'occasion_id', 'Occasions to exclude'),
        'singapore_only': fields.boolean('Singapore only'),
        'cheque_allowed': fields.boolean('Cheque allowed'),
        'products_to_include': fields.many2many('product.product', 'tgb_promos_products_to_include_ref', 'promo_id', 'product_id', 'Products to include'),
        'categories_to_include': fields.many2many('product.category', 'tgb_promos_categories_to_include_ref', 'promo_id', 'category_id', 'Categories to include'),
        'occasions_to_include': fields.many2many('product.occasion', 'tgb_promos_occasions_to_include_ref', 'promo_id', 'occasion_id', 'Occasions to include'),
        'customers_to_include': fields.many2many('res.partner', 'tgb_promos_customers_to_include_ref', 'promo_id', 'partner_id', 'Customers to include'),
        'customers_to_exclude': fields.many2many('res.partner', 'tgb_promos_customers_to_exclude_ref', 'promo_id', 'partner_id', 'Customers to exclude'),
        'minimum_amount': fields.float('Minimum amount'),
        'allow_voucher': fields.boolean('Allow voucher'),
        'cash_voucher_used_once': fields.boolean('Cash voucher used once'),
        'mode_of_payment_all': fields.boolean('All'),
        'mode_of_payment_credit': fields.boolean('Credit'),
        'mode_of_payment_card': fields.boolean('Card'),
        'mode_of_payment_cash': fields.boolean('Cash'),
        'mode_of_payment_cheque': fields.boolean('Cheque'),
        'mode_of_order_fax': fields.boolean('Fax'),
        'mode_of_order_phone': fields.boolean('Phone'),
        'mode_of_order_online': fields.boolean('Online'),
        'pick_only': fields.boolean('Pick only'),
        'pick_qty': fields.integer('Qty'),
        'max_cust_number': fields.integer('Max Cust Number'),
        'redemption_from_date': fields.datetime('Redemption from date'),
        'redemption_to_date': fields.datetime('Redemption to date'),
    }
    _defaults = {
        'order_mode': 'All',
        'active': True,
    }
TGBPromotionsRules

class TGBPromotionsCondition(osv.Model):
    "Promotion Rules"
    _name = "tgb_promos.condition"

    _columns = {
        'promo_id': fields.many2one('tgb_promos.rules', 'Promotions'),
        'product_id': fields.many2one('product.product', 'Item code'),
        'product_category': fields.many2one('product.category', 'Product group code'),
        'based_on': fields.selection([('Qty', 'Qty'),
                                      ('Amount', 'Amount')], 'Based on', required=True),
        'discount_type': fields.selection([('Percentage', 'Percentage'),
                                           ('Amount', 'Amount')], 'Discount type'),
        'from': fields.float('From'),
        'to': fields.float('To'),
        'value': fields.float('Value'),
        'new_price': fields.float('New price'),

    }
    _defaults = {
        'value': 0,
        'based_on': 'Qty',
    }
TGBPromotionsCondition

class TGBPromotionsProduct(osv.Model):
    "Promotion Rules"
    _name = "tgb_promos.product"

    _columns = {
        'promo_id': fields.many2one('tgb_promos.rules', 'Promotions'),
        'product_id': fields.many2one('product.product', 'Item code'),
        'qty': fields.integer('Quantity'),

    }
    _defaults = {
        'qty': 1,
    }
TGBPromotionsProduct
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: