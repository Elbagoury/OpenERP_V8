# -*- coding: utf-8 -*-
__author__ = 'Phamkr'
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.addons.point_of_sale import point_of_sale
import logging
from openerp import tools
import openerp.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)

class pos_order(osv.osv):
    _inherit = 'pos.order'


    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False,lazy=True):
        result= super(pos_order, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby,lazy)
        return result

    def check_redeemption(self,cr,uid,ids):
        for order in self.browse(cr,uid,ids):
            if order.pos_reference:
                package_redemption_ids = self.pool.get('pos.package.redeem').search(cr,uid,[('reference','=',order.pos_reference)])
                if package_redemption_ids and len(package_redemption_ids)>0:
                    return False
        return True

    def refund(self, cr, uid, ids, context=None):
        """Create a copy of order  for refund order"""
        have_redemption = self.check_redeemption(cr,uid,ids)
        if not have_redemption:
            raise osv.except_osv('Error','Cannot return the order which already have redemption')
        clone_list = []
        line_obj = self.pool.get('pos.order.line')

        for order in self.browse(cr, uid, ids, context=context):
            current_session_ids = self.pool.get('pos.session').search(cr, uid, [
                ('state', '!=', 'closed'),
                ('user_id', '=', uid)], context=context)
            if not current_session_ids:
                raise osv.except_osv(_('Error!'), _('To return product(s), you need to open a session that will be used to register the refund.'))

            clone_id = self.copy(cr, uid, order.id, {
                'name': order.name + ' REFUND', # not used, name forced by create
                'session_id': current_session_ids[0],
                'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
            }, context=context)
            clone_list.append(clone_id)

        for clone in self.browse(cr, uid, clone_list, context=context):
            for order_line in clone.lines:
                line_obj.write(cr, uid, [order_line.id], {
                    'qty': -order_line.qty
                }, context=context)

        abs = {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id':clone_list[0],
            'view_id': False,
            'context':context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        return abs



    def _order_fields(self, cr, uid, ui_order, context=None):
        lines = ui_order['lines']
        child_lines = []
        return_lines = []
        product_obj = self.pool.get('product.product')
        partner = order_id = False
        if ui_order.get('partner_id'):
            partner = ui_order['partner_id']
        order_id = ui_order['name']
        for line in lines:
            return_lines.append(line)
            product_id = line[2]['product_id']
            qty = line[2]['qty']
            if product_id:
                product = product_obj.browse(cr,uid,product_id)
                if product.is_group_product2:
                    for child in product.product_group_ids2:
                        child_product_id = child.product_id.id
                        child_product_price = child.product_id.list_price
                        product_qty = child.qty
                        new_item = self.pool.get('pos.package').create(cr,uid,{'product_id':child_product_id,
                                                                    'partner_id':partner,
                                                                    'reference':order_id,
                                                                    'total': qty*product_qty,
                                                                    'unit_price':child_product_price})
                        return_lines.append([0,0,{'discount': 0,'price_unit': 0, 'product_id': child_product_id, 'qty': qty*product_qty,'is_child_line':True,}])
                else:
                    unit_price = self.pool.get('product.product').browse(cr,uid,product_id).list_price
                    new_item =  self.pool.get('pos.package').create(cr,uid,{'product_id':product_id,
                                                                'partner_id':partner,
                                                                'reference':order_id,
                                                                'total': qty,
                                                                'unit_price':unit_price,
                                                                })

        return {
            'name':         ui_order['name'],
            'user_id':      ui_order['user_id'] or False,
            'session_id':   ui_order['pos_session_id'],
            'lines':        return_lines,
            'pos_reference':ui_order['name'],
            'partner_id':   ui_order['partner_id'] or False,
        }

pos_order()


class pos_session(osv.osv):
    _inherit = 'pos.session'
    def _get_total_transaction(self,cr,uid,ids,a,b,context={}):
        val={}
        for session in self.browse(cr,uid,ids):
            val[session.id] = 0
            for statement in session.statement_ids:
                val[session.id]+=statement.total_entry_encoding
        return val
    def saicoms_wkf_action_closing_control(self, cr, uid, ids, context=None):
        for session in self.browse(cr, uid, ids, context=context):
            for statement in session.statement_ids:
                if (statement != session.cash_register_id) and (statement.balance_end != statement.balance_end_real):
                    self.pool.get('account.bank.statement').write(cr, uid, [statement.id], {'balance_end_real': statement.balance_end})
        return True

    _columns = {
        'due_date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string="Start date from"),
        'due_date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string="Start date to"),
        'saicoms_total_transaction': fields.function(_get_total_transaction, digits_compute=dp.get_precision('Point Of Sale'), string='Total Transaction',
             help="The total transaction of the session."),
    }


pos_session()

class pos_order_line(osv.osv):
    _inherit = "pos.order.line"
    _columns={
        'is_child_line':fields.boolean('Is child line'),
    }
    _defaults={
        'is_child_line':False,
    }
pos_order_line()



