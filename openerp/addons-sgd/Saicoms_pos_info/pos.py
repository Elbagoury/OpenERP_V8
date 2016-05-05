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

_logger = logging.getLogger(__name__)

class pos_order(osv.osv):
    _inherit = 'pos.order'

    def create_from_ui(self, cr, uid, orders, context=None):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        existing_order_ids = self.search(cr, uid, [('pos_reference', 'in', submitted_references)], context=context)
        existing_orders = self.read(cr, uid, existing_order_ids, ['pos_reference'], context=context)
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]

        order_ids = []

        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            order_fields = self._order_fields(cr, uid, order, context=context)
            order_id = self.create(cr, uid, order_fields,context)
            for payments in order['statement_ids']:
                self.add_payment(cr, uid, order_id, self._payment_fields(cr, uid, payments[2], context=context), context=context)

            session = self.pool.get('pos.session').browse(cr, uid, order['pos_session_id'], context=context)
            if session.sequence_number <= order['sequence_number']:
                session.write({'sequence_number': order['sequence_number'] + 1})
                session.refresh()

            if order['amount_return']:
                cash_journal = session.cash_journal_id
                if not cash_journal:
                    cash_journal_ids = filter(lambda st: st.journal_id.type=='cash', session.statement_ids)
                    if not len(cash_journal_ids):
                        raise osv.except_osv( _('error!'),
                            _("No cash statement found for this session. Unable to record returned cash."))
                    cash_journal = cash_journal_ids[0].journal_id
                self.add_payment(cr, uid, order_id, {
                    'amount': -order['amount_return'],
                    'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_name': _('return'),
                    'journal': cash_journal.id,
                }, context=context)
            perform_user_id = None
            advisory_id  = None
            pos_source = None
            has_friend =False
            customer_user_rating = ''
            customer_rating = None
            customer_comment = ''
            if order.get('perform_user_id'):
                perform_user_id = order['perform_user_id']
            if order.get('advisory_id'):
                advisory_id = order['advisory_id']
            if order.get('pos_source'):
                pos_source = order['pos_source']
            if order.get('has_friend'):
                has_friend = order.get('has_friend')
            if order.get('customer_user_rating'):
                customer_user_rating = order.get('customer_user_rating')
            if order.get('customer_rating'):
                customer_rating = str(order.get('customer_rating'))
            if order.get('customer_comment'):
                customer_comment = order.get('customer_comment')
            print 'customer_rating', customer_rating
            self.write(cr,uid,order_id,{'perform_user_id':perform_user_id,
                                        'advisory_id':advisory_id,
                                        'pos_source':pos_source,
                                        'has_friend':has_friend,
                                        'customer_user_rating':customer_user_rating,
                                        'customer_rating':customer_rating,
                                        'customer_comment':customer_comment})
            order = self.pool.get('pos.order').browse(cr,uid,order_id)
            if order.partner_id:
                partner_id = order.partner_id
                if not partner_id.saicoms_project_id:
                    project_id = self.pool.get('project.project').create(cr,uid,{'name':partner_id.name,
                                                                                 'partner_id':partner_id.id,
                                                                                 'is_saicoms_cs':True})
                    self.pool.get('res.partner').write(cr,uid,partner_id.id,{'saicoms_project_id':project_id})

            order_ids.append(order_id)

            try:
                self.signal_workflow(cr, uid, [order_id], 'paid')
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if to_invoice:
                self.action_invoice(cr, uid, [order_id], context)
                order_obj = self.browse(cr, uid, order_id, context)
                self.pool['account.invoice'].signal_workflow(cr, uid, [order_obj.invoice_id.id], 'invoice_open')
        self.create_order_event(cr,uid,order_ids,context)
        return order_ids

    def create_order_event(self, cr, uid, order_ids, context=None):
        # Keep only new orders
        for order in self.browse(cr,uid,order_ids):
            order_date = datetime.strptime(order.date_order[:10],'%Y-%m-%d')
            for line in order.lines:
                if line.product_id:
                    for remark in line.product_id.product_remark_ids:
                        event_date = order_date + relativedelta(days=remark.time)
                        event_id = self.pool.get('sale.order.event').create(cr,uid,{
                                                                        'date':event_date,
                                                                        'remark':remark.remark,
                                                                        'pos_order_id':order.id,
                                                                        'product_id':line.product_id.id,
                                                                        })
        return order_ids

    _columns = {
        'perform_user_id':fields.many2one('res.users','Performing User'),
        'advisory_id':fields.many2one('res.users','Advisory'),
        'has_friend':fields.boolean('Customer has friend?'),
        'pos_source':fields.many2one('pos.source','Source Order'),
        'customer_user_rating':fields.char('Customer User Rating',size=255),
        'customer_rating':fields.selection([
            ('1', 'Rất hài lòng'),
            ('2', 'Hài lòng'),
            ('3', 'Bình thường'),
            ('4', 'Không hài lòng'),
            ('5','Quá tệ'),
        ],'Customer Rating', size=128),
        'customer_comment':fields.char('Customer Comment',size=255),
        'sale_order_event_ids':fields.one2many('sale.order.event','pos_order_id','Sale Order Event'),
    }

pos_order()

class saicoms_pos_order(point_of_sale.pos_order):
    _inherit = 'mail.thread'
saicoms_pos_order()

class saicoms_pos_info_session(point_of_sale.pos_session):
    inherit = 'mail.thread'
saicoms_pos_info_session()


class pos_source(osv.osv):
    _name = 'pos.source'
    _columns = {
        'name':fields.char('Source',size=128),
    }

pos_source()
