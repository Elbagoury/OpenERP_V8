# -*- coding: utf-8 -*-
__author__ = 'Phamkr'
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

class sale_order(osv.osv):
    _inherit = 'sale.order'
    def action_button_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.signal_workflow(cr, uid, ids, 'order_confirm')
        for order in self.browse(cr,uid,ids):
            order_date = datetime.strptime(order.date_order[:10],'%Y-%m-%d')
            if order.partner_id:
                partner_id = order.partner_id
                if not partner_id.saicoms_project_id:
                    project_id = self.pool.get('project.project').create(cr,uid,{'name':partner_id.name,
                                                                                 'partner_id':partner_id.id,
                                                                                 'is_saicoms_cs':True})
                    self.pool.get('res.partner').write(cr,uid,partner_id.id,{'saicoms_project_id':project_id})

        return True

    def check_sale_order_event(self, cr, uid, context=None):
        uid=1
        today = fields.date.context_today(self, cr, uid, context=context)
        sale_order_event_ids = self.pool.get('sale.order.event').search(cr,uid,[('date','=',today)])
        if sale_order_event_ids and len(sale_order_event_ids)>0:
            for event_id in self.pool.get('sale.order.event').browse(cr,uid,sale_order_event_ids):
                name = event_id.remark
                if event_id.sale_order_id or event_id.pos_order_id:
                    partner_id = False
                    if event_id.sale_order_id and event_id.sale_order_id.partner_id:
                        partner_id = event_id.sale_order_id.partner_id
                    if event_id.pos_order_id and event_id.pos_order_id.partner_id:
                        partner_id = event_id.pos_order_id.partner_id
                    if partner_id:
                        project_id = False
                        if not partner_id.saicoms_project_id:
                            project_id = self.pool.get('project.project').create(cr,uid,{'name':partner_id.name,
                                                                                         'partner_id':partner_id.id,
                                                                                         'is_saicoms_cs':True})
                            self.pool.get('res.partner').write(cr,uid,partner_id.id,{'saicoms_project_id':project_id})
                        else:
                            project_id = partner_id.saicoms_project_id.id
                        user_id = None

                        if event_id.sale_order_id.user_id:
                            user_id = event_id.sale_order_id.user_id.id
                        task_id = self.pool.get('project.task').create(cr,uid,{'name':name,
                                                                         'project_id':project_id,
                                                                         'user_id':user_id,
                                                                         'is_saicoms_cs':True
                                                                     })
        return True

    _columns = {
        'sale_order_event_ids':fields.one2many('sale.order.event','sale_order_id','Sale Order Event'),
    }

sale_order()
