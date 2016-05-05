# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools.translate import _

class sale_order(orm.Model):
    _inherit = 'sale.order'


    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)
        return res

    def action_wait(self, cr, uid, ids, context=None):
        context = context or {}
        for o in self.browse(cr, uid, ids):
            noprod = self.test_no_product(cr, uid, o, context)
            if (o.order_policy == 'manual') or noprod:
                self.write(cr, uid, [o.id], {'state': 'manual', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
            else:
                self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
            self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line])
        return True

    def action_create_variation_quotation(self,cr,uid,ids,context={}):
            id = self.copy(cr, uid, ids[0],{'parent_order_id':ids[0]}, context=context)
            self.write(cr,uid,id,{'is_variation':True})
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'TGB_construction', 'project_view_order_form')
            view_id = view_ref and view_ref[1] or False,
            return {
                'type': 'ir.actions.act_window',
                'name': _('Sales Order'),
                'res_model': 'sale.order',
                'res_id': id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'current',
                'nodestroy': True,
            }

    def action_create_additional_quotation(self,cr,uid,ids,context={}):
            id = self.copy(cr, uid, ids[0],{'parent_order_id':ids[0]}, context=context)
            self.write(cr,uid,id,{'is_addition':True})
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'TGB_construction', 'project_view_order_form')
            view_id = view_ref and view_ref[1] or False,
            return {
                'type': 'ir.actions.act_window',
                'name': _('Sales Order'),
                'res_model': 'sale.order',
                'res_id': id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'current',
                'nodestroy': True,
            }

    def action_create_progressive_billing(self,cr,uid,ids,context={}):
        for project in self.browse(cr,uid,ids):
            number = project.name+'/'+str(project.billing_time+1)
            retention_amount = 0
            if project.retention_required:
                retention_amount = project.retention_percent
            new_id = self.pool.get('progressive.billing').create(cr,uid,{'number':number,
                                                                          'sale_order_id':project.id,
                                                                         'retention_required':project.retention_required,
                                                                         'retention_amount':project.retention_amount,
                                                                         'retention_type':project.retention_type,
                                                                         'retention_percent':project.retention_percent,
                                                                         'billing_time':project.billing_time+1,
                                                                        })

            for line in project.order_line:
                self.pool.get('progressive.billing.line').create(cr,uid,{'billing_id':new_id,
                                                                         'description':line.name,
                                                                         'contract_sum':line.price_subtotal,
                                                                         'total_work_up_to_date':line.billed_percent,
                                                                         'sale_order_line_id':line.id,
                                                                         })

            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'TGB_construction', 'tgb_progressive_billing_form')
            view_id = view_ref and view_ref[1] or False,

            return {
                'type': 'ir.actions.act_window',
                'name': _('Progressive Billing for %s %s Time ' %(project.name,str(project.billing_time+1))),
                'res_model': 'progressive.billing',
                'res_id': new_id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'current',
                'nodestroy': True,
            }



    def _prepare_lump_sum_invoice_line(self, cr, uid, order, context=None):
        res = {}
        prop = self.pool.get('ir.property').get(cr, uid,
                'property_account_income_categ', 'product.category',
                context=context)
        account_id = prop and prop.id or False
        uosqty = 0
        pu = 0.0
        fpos = order.fiscal_position or False
        account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
        if not account_id:
            raise osv.except_osv(_('Error!'),
                        _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
        res = {
            'name': order.scope_of_work,
            'origin': order.name,
            'account_id': account_id,
            'price_unit': order.scope_amount,
            'quantity': 1,
        }

        return res

    def lump_sum_invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        create_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            if not line.lump_sum_invoiced and line.lump_sum_type=='text':
                vals = self._prepare_lump_sum_invoice_line(cr, uid, line, context)
                if vals:
                    inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
                    self.write(cr, uid, [line.id], {'lump_sum_invoiced':True}, context=context)
                    create_ids.append(inv_id)
            elif not line.lump_sum_invoiced and line.lump_sum_type=='line':
                prop = self.pool.get('ir.property').get(cr, uid,
                'property_account_income_categ', 'product.category',
                context=context)
                account_id = prop and prop.id or False
                uosqty = 0
                pu = 0.0
                fpos = line.fiscal_position or False
                account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
                if not account_id:
                    raise osv.except_osv(_('Error!'),
                                _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
                for sum_line in line.lump_sum_lines:
                    inv_id = self.pool.get('account.invoice.line').create(cr,uid,{'name':sum_line.name,
                                                                                  'origin':line.name,
                                                                                  'account_id':account_id,
                                                                                  'price_unit':0,
                                                                                  'quantity':sum_line.qty})
                    create_ids.append(inv_id)
                last_inv_id = self.pool.get('account.invoice.line').create(cr,uid,{'name':'Total Amount',
                                                                                  'origin':line.name,
                                                                                  'account_id':account_id,
                                                                                  'price_unit':line.scope_amount,
                                                                                  'quantity':1})
                create_ids.append(last_inv_id)
                self.write(cr, uid, [line.id], {'lump_sum_invoiced':True}, context=context)

        return create_ids

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_invoice_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_invoice_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'section_id' : order.section_id.id,
            'sale_order_id':order.id,
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals


    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None, date_invoice = False, context=None):
        if states is None:
            states = ['confirmed', 'done', 'exception']
        res = False
        invoices = {}
        invoice_ids = []
        invoice = self.pool.get('account.invoice')
        obj_sale_order_line = self.pool.get('sale.order.line')
        partner_currency = {}
        # If date was specified, use it as date invoiced, usefull when invoices are generated this month and put the
        # last day of the last month as invoice date
        if date_invoice:
            context = dict(context or {}, date_invoice=date_invoice)
        for o in self.browse(cr, uid, ids, context=context):
            currency_id = o.pricelist_id.currency_id.id
            if (o.partner_id.id in partner_currency) and (partner_currency[o.partner_id.id] <> currency_id):
                raise osv.except_osv(
                    _('Error!'),
                    _('You cannot group sales having different currencies for the same partner.'))

            partner_currency[o.partner_id.id] = currency_id
            lines = []
            created_lines = []
            if o.order_type=='big':
                for line in o.order_line:
                    if line.invoiced:
                        continue
                    elif (line.state in states):
                        lines.append(line.id)
                created_lines = obj_sale_order_line.invoice_line_create(cr, uid, lines)
            elif o.order_type=='bq':
                for line in o.sale_bq_ids:
                    if line.invoiced:
                        continue
                    else:
                        lines.append(line.id)
                bq_lines = self.pool.get('sale.bq.line').invoice_line_create(cr, uid, lines)
                created_lines.extend(bq_lines)
            elif o.order_type=='sor':
                for line in o.sale_hr_ids:
                    if line.invoiced:
                        continue
                    else:
                        lines.append(line.id)
                hr_lines = self.pool.get('sale.hr.line').invoice_line_create(cr, uid, lines)
                created_lines.extend(hr_lines)
            elif o.order_type=='lump_sum':
                lump_sum_lines = []
                if not o.lump_sum_invoiced:
                    lump_sum_lines = self.lump_sum_invoice_line_create(cr,uid,[o.id])
                created_lines.extend(lump_sum_lines)
            if len(created_lines)>0:
                invoices.setdefault(o.partner_invoice_id.id or o.partner_id.id, []).append((o, created_lines))
        if not invoices:
            for o in self.browse(cr, uid, ids, context=context):
                for i in o.invoice_ids:
                    if i.state == 'draft':
                        return i.id
        for val in invoices.values():
            if grouped:
                res = self._make_invoice(cr, uid, val[0][0], reduce(lambda x, y: x + y, [l for o, l in val], []), context=context)
                invoice_ref = ''
                origin_ref = ''
                for o, l in val:
                    invoice_ref += (o.client_order_ref or o.name) + '|'
                    origin_ref += (o.origin or o.name) + '|'
                    self.write(cr, uid, [o.id], {'state': 'progress'})
                    cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (o.id, res))
                    self.invalidate_cache(cr, uid, ['invoice_ids'], [o.id], context=context)
                #remove last '|' in invoice_ref
                if len(invoice_ref) >= 1:
                    invoice_ref = invoice_ref[:-1]
                if len(origin_ref) >= 1:
                    origin_ref = origin_ref[:-1]
                invoice.write(cr, uid, [res], {'origin': origin_ref, 'name': invoice_ref})
            else:
                for order, il in val:
                    res = self._make_invoice(cr, uid, order, il, context=context)
                    invoice_ids.append(res)
                    self.write(cr, uid, [order.id], {'state': 'progress'})
                    cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (order.id, res))
                    self.invalidate_cache(cr, uid, ['invoice_ids'], [order.id], context=context)
        return res


    def manual_invoice(self, cr, uid, ids, context=None):
        """ create invoices for the given sales orders (ids), and open the form
            view of one of the newly created invoices
        """
        mod_obj = self.pool.get('ir.model.data')

        # create invoices through the sales orders' workflow
        inv_ids0 = set(inv.id for sale in self.browse(cr, uid, ids, context) for inv in sale.invoice_ids)
        self.signal_workflow(cr, uid, ids, 'manual_invoice')
        inv_ids1 = set(inv.id for sale in self.browse(cr, uid, ids, context) for inv in sale.invoice_ids)
        # determine newly created invoices
        new_inv_ids = list(inv_ids1 - inv_ids0)

        res = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_invoice_form_new')
        res_id = res and res[1] or False,

        return {
            'name': _('Customer Project Billing'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': new_inv_ids and new_inv_ids[0] or False,
        }

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _get_order_hr(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.hr.line').browse(cr, uid, ids, context=context):
            result[line.sale_order_hr_id.id] = True
        return result.keys()


    def _get_order_bq(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.bq.line').browse(cr, uid, ids, context=context):
            result[line.sale_order_bq_id.id] = True
        return result.keys()


    def action_button_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)

        # redisplay the record as a sales order



        for quotation in self.browse(cr,uid,ids):
            is_construction = True
            for line in quotation.order_line:
                if line.product_id:
                    is_construction = False
            if is_construction:
                view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'TGB_construction', 'project_view_order_form')
                view_id = view_ref and view_ref[1] or False,
                self.write(cr,uid,quotation.id,{'is_construction':True})

                if quotation.is_variation or quotation.is_addition:
                    order_parent_id = quotation.parent_order_id
                    print 'order_parent_id', order_parent_id
                    if order_parent_id:
                        print 'quotation.', quotation.is_addition, quotation.is_variation
                        if quotation.is_variation:
                            for line in quotation.order_line:
                                new_line = self.pool.get('sale.order.line').copy(cr,uid,line.id,{'order_id':order_parent_id.id,
                                                                                                 'line_type':'variation'})
                                print 'nbew line', new_line
                        if quotation.is_addition:
                            for line in quotation.order_line:
                                new_line = self.pool.get('sale.order.line').copy(cr,uid,line.id,{'order_id':order_parent_id.id,
                                                                                                 'line_type':'additional'})
                                print 'nbew line', new_line

                if not quotation.project_id:
                    subject = quotation.subject
                    partner_id = quotation.partner_id
                    if not subject:
                        subject = partner_id.name + ' Project'
                    project_id = self.pool.get('project.project').create(cr,uid,{'name':subject,
                                                                'partner_id':partner_id.id})
                    written = self.write(cr,uid,quotation.id,{'project_id':project_id,
                                                    'project_confirm_id':project_id})
                    project_costing_id = self.pool.get('project.costing').create(cr,uid,{'project_id':project_id})
                else:
                    self.write(cr,uid,quotation.id,{'project_confirm_id':quotation.project_id.id})
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Sales Order'),
                    'res_model': 'sale.order',
                    'res_id': ids[0],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'target': 'current',
                    'nodestroy': True,
                }
            else:
                self.write(cr,uid,quotation.id,{'is_construction':False})
                view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
                view_id = view_ref and view_ref[1] or False,
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Sales Order'),
                    'res_model': 'sale.order',
                    'res_id': ids[0],
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'target': 'current',
                    'nodestroy': True,
                }

    def action_view_project(self,cr,uid,ids,context={}):
        for quotation in self.browse(cr,uid,ids):
            if quotation.project_id:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Project'),
                    'res_model': 'project.project',
                    'res_id': quotation.project_id.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'current',
                    'nodestroy': True,
                }


    def action_view_invoice(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')


        #compute the number of invoices to display
        inv_ids = []
        for so in self.browse(cr, uid, ids, context=context):
            result = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_construction_project_billing_action')
            if not so.is_construction:
                result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree1')
            id = result and result[1] or False
            result = act_obj.read(cr, uid, [id], context=context)[0]

            inv_ids += [invoice.id for invoice in so.invoice_ids]
        #choose the view_mode accordingly
            if len(inv_ids)>1:
                result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
            else:
                res = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_invoice_form_new')
                if not so.is_construction:
                    res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
                result['views'] = [(res and res[1] or False, 'form')]
                result['res_id'] = inv_ids and inv_ids[0] or False

        return result

    def action_view_progressive_billing(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_construction_project_progressive_billing_action')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of invoices to display
        inv_ids = []
        inv_ids = self.pool.get('progressive.billing').search(cr,uid,[('sale_order_id','in',ids)])
        #choose the view_mode accordingly
        if len(inv_ids)>1:
            result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_progressive_billing_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = inv_ids and inv_ids[0] or False

        return result

    def _get_default_currency(self, cr, uid, context=None):
        currency_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        return currency_id

    def _amount_hr_all(self, cr, uid, ids, field_name, arg, context=None):
        from num2words import num2words
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_hr_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.currency_id
            for line in order.sale_hr_ids:
                val1 += line.price_subtotal
            res[order.id]['amount_hr_total'] = cur_obj.round(cr, uid, cur, val1)
            amount_hr_total = res[order.id]['amount_hr_total']
            amount_hr_total_decimal = round((amount_hr_total-int(amount_hr_total))*100,0)
            amount_hr_total_word = num2words(int(amount_hr_total)).replace(' and','')
            if amount_hr_total_decimal>0:
                amount_hr_total_word = amount_hr_total_word+ ' AND CENTS '+num2words(int(amount_hr_total_decimal)).replace(' and','')
            res[order.id]['amount_hr_total_word'] = (amount_hr_total_word+ ' ONLY').upper()
        return res


    def _amount_bq_all(self, cr, uid, ids, field_name, arg, context=None):
        from num2words import num2words
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_bq_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.currency_id
            for line in order.sale_bq_ids:
                val1 += line.price_subtotal
            res[order.id]['amount_bq_total'] = cur_obj.round(cr, uid, cur, val1)
            amount_bq_total = res[order.id]['amount_bq_total']
            amount_bq_total_decimal = round((amount_bq_total-int(amount_bq_total))*100,0)
            amount_bq_total_word = num2words(int(amount_bq_total)).replace(' and','')
            if amount_bq_total_decimal>0:
                amount_bq_total_word = amount_bq_total_word + ' AND CENTS '+ num2words(amount_bq_total_decimal).replace(' and','')
            res[order.id]['amount_bq_total_word'] = (amount_bq_total_word+' ONLY').upper()
        return res


    def onchange_scope_amount(self,cr,uid,ids,scope_amount,context={}):
        from num2words import num2words
        scope_amount_decimal = round((scope_amount-int(scope_amount))*100,0)
        total_amount_word = num2words(int(scope_amount)).replace(' and','')
        if scope_amount_decimal>0:
            total_amount_word = total_amount_word + ' AND CENTS '+ num2words(int(scope_amount_decimal)).replace(' and','')
        return {'value':{'total_amount_word':(total_amount_word + ' ONLY').upper()}}

    def _amount_grand_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            detail_add_show = False
            have_add = False
            have_remark = False
            hr_add_show = 'noboth'
            bq_add_show = False
            for line in order.order_line:
                if line.add_percent>0:
                    detail_add_show = True
            for hr_line in order.sale_hr_ids:
                if hr_line.add_percent>0:
                    have_add = True
                if hr_line.remark:
                    have_remark = True
            if have_add and have_remark:
                hr_add_show = 'showboth'
            elif have_add and not have_remark:
                hr_add_show = 'showadd'
            elif not have_add and have_remark:
                hr_add_show = 'showremark'
            for bq_line in order.sale_bq_ids:
                if bq_line.add_percent>0:
                    bq_add_show = True
            res[order.id] = {
                'hr_add_show':hr_add_show,
                'bq_add_show':bq_add_show,
                'total_scope_of_work': order.scope_amount,
                'total_detail': order.amount_untaxed,
                'total_hr': order.amount_hr_total,
                'total_grand': order.scope_amount+order.amount_untaxed+order.amount_hr_total,
                'detail_add_show':detail_add_show,
            }
        return res


    def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
        """ Wrapper because of direct method passing as parameter for function fields """
        return self._amount_all(cr, uid, ids, field_name, arg, context=context)

    def _get_user_id_title(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in  self.browse(cr,uid,ids):
            res[order.id]=""
            if order.user_id:
                employee_id = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',order.user_id.id)])
                if employee_id and len(employee_id)>0:
                    res[order.id]=self.pool.get('hr.employee').browse(cr,uid,employee_id[0]).job_id.name
        return res



    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        from num2words import num2words
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
            amount_untaxed = res[order.id]['amount_untaxed']

            amount_untaxed_decimal = round((amount_untaxed - int(amount_untaxed))*100,0)
            amount_untaxed_word = num2words(int(amount_untaxed)).replace(' and','')
            amount_untaxed_decimal_word = ''
            if amount_untaxed_decimal>0:
                amount_untaxed_decimal_word = num2words(int(amount_untaxed_decimal)).replace(' and','')
            if len(amount_untaxed_decimal_word)>0:
                amount_untaxed_word = amount_untaxed_word+' AND CENTS '+amount_untaxed_decimal_word
            res[order.id]['amount_untaxed_word']= (amount_untaxed_word + ' ONLY').upper()
        return res


    def make_deposit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False
        })
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.sale.deposit.wiz',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }


    def _get_partners(self, cr, uid, ids, context=None):
        partners = set()
        for aml in self.browse(cr, uid, ids, context=context):
            if aml.user_id:
                employee_ids = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',aml.user_id.id)])
                partners.update(set(employee_ids))
        print 'partners ', partners
        return list(partners)

    _columns = {
        'order_type':fields.selection([('big','Big Project'),('lump_sum','Lump Sum'),('sor','SOR'),('bq','BQ')], 'Project Type',required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'lump_sum_type':fields.selection([('text','Text'),('line','Lines')], 'Lump Sum Type'),
        'lump_sum_lines': fields.one2many('lump.sum.line', 'order_id', 'Lump Sum Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=True),
        'customer_po':fields.char('Customer PO',size=255),
        'delivery_ref':fields.char('Delivery Order Ref',size=255),
        'lump_sum_invoiced':fields.boolean('Invoiced Lump Sum'),
        'is_construction':fields.boolean('Is Construction Order'),
        'is_variation':fields.boolean('Is Variation Order'),
        'is_addition':fields.boolean('Is Additional Order'),
        'project_code':fields.related('project_id','project_code',type='char',readonly=True,size=255,string="Project No"),
        'billing_time':fields.integer('Billing Claim'),
        'thankyou_text':fields.text('Thank you'),
        'thankyou_text2':fields.text('Thank you'),
        'project_id':fields.many2one('project.project','Project'),
        'project_confirm_id':fields.many2one('project.project','Project'),
        'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=True),
        'total_scope_of_work':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total of Scope',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['amount_untaxed','scope_amount','amount_hr_total','order_line','sale_hr_ids'], 10),
                                          },
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'total_detail':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total of Detail',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['amount_untaxed','scope_amount','amount_hr_total','order_line','sale_hr_ids'], 10),
                                          },
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'total_hr':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Total of HR',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['amount_untaxed','scope_amount','amount_hr_total','order_line','sale_hr_ids'], 10),
                                          },
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'hr_add_show':fields.function(_amount_grand_all, string='We show add percent', type = 'char',size=255,
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['sale_hr_ids'], 10),
                                          },
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'detail_add_show':fields.function(_amount_grand_all, string='We show add percent detail', type = 'char',size=255,
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                          },
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'bq_add_show':fields.function(_amount_grand_all, string='We BQ show add percent', type = 'boolean',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['sale_bq_ids'], 10),
                                          },
                                          multi='grand', help="The amount of overview", track_visibility='always'),


        'total_grand':fields.function(_amount_grand_all, digits_compute=dp.get_precision('Account'),
                                          string='Grand Total',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['amount_untaxed','scope_amount','amount_hr_total','order_line','sale_hr_ids'], 10),
                                          },
                                          multi='grand', help="The amount of overview", track_visibility='always'),

        'signature_image': fields.binary(string='Signature'),
        'signature_image2': fields.binary(string='Signature'),

        'validity':fields.char('Validity', size=255),
        'term':fields.char('Terms', size=255),
        'exclusion':fields.char('Exclusion', size=255),

        'currency_id': fields.many2one('res.currency', 'Currency', required=True),

        'sale_hr_ids':fields.one2many('sale.hr.line','sale_order_hr_id',string='HR Cost'),

        'sale_bq_ids':fields.one2many('sale.bq.line','sale_order_bq_id',string='BQ Cost'),

        'attn_id':fields.many2one('res.partner','Attn'),

        'scope_of_work':fields.text('Scope of Works'),

        'scope_amount':fields.float('Scope Amount', digits_compute=dp.get_precision('Account')),
        'subject': fields.text('Subject'),
        'retention_required': fields.boolean('Retention Required'),
        'retention_type':fields.selection([('P','Percent'),('A','Amount')], 'Retention Type'),
        'retention_percent': fields.float('Retention Percent'),
        'retention_amount': fields.float('Retention Amount'),
        'capped_amount': fields.float('Capped Amount'),
        'retention_day': fields.integer('Retention Months'),
        'retention_date': fields.date('Retention Months'),
        'operation_manager': fields.many2one('res.users', 'Operation Manager'),
        'project_manager': fields.many2one('res.users', 'Project Manager'),
        'claim_officer': fields.many2one('res.users', 'Claim Officer'),
        'project_coordinator': fields.many2one('res.users', 'Project Coordinator'),
        'resident_technical_officer': fields.many2one('res.users', 'Resident Technical Officer'),
        'head_of_department': fields.many2one('res.users', 'Head of Department'),
        'user_ids': fields.one2many('project.user.sale', 'sale_id', 'Other Member'),
        'total_amount_word':fields.char('Total Amount', size=255),

        'amount_hr_total': fields.function(_amount_hr_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Amount',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['sale_hr_ids'], 10),
                                              'sale.hr.line': (_get_order_hr, ['price_unit','add_percent','product_uom_qty'], 10),
                                          },
                                          multi='hr', help="The amount of HR", track_visibility='always'),

        'amount_hr_total_word': fields.function(_amount_hr_all, type='char',size=255,
                                          string='Total Amount',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['sale_hr_ids'], 10),
                                              'sale.hr.line': (_get_order_hr, ['price_unit','add_percent','product_uom_qty'], 10),
                                          },
                                          multi='hr', help="The amount of HR", track_visibility='always'),


        'amount_bq_total': fields.function(_amount_bq_all, digits_compute=dp.get_precision('Account'),
                                          string='Total Amount',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['sale_bq_ids'], 10),
                                              'sale.bq.line': (_get_order_bq, ['price_unit','add_percent','product_uom_qty'], 10),
                                          },
                                          multi='hr', help="The amount of HR", track_visibility='always'),

        'amount_bq_total_word': fields.function(_amount_bq_all, type='char',size=255,
                                          string='Total Amount',
                                          store={
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['sale_bq_ids'], 10),
                                              'sale.bq.line': (_get_order_bq, ['price_unit','add_percent','product_uom_qty'], 10),
                                          },
                                          multi='hr', help="The amount of HR", track_visibility='always'),

        'tgb_remarks':fields.text('Remarks'),
        
        'project_costing_id':fields.many2one('project.costing','Project Costing'),

        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Project Order'),
            ('manual', 'Project Order to Billing'),
            ('invoice_except', 'Billing Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or project order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the project order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),

        'amount_untaxed': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),

        'amount_untaxed_word': fields.function(_amount_all_wrapper, type='char', size=255, string='Total Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),


        'amount_tax': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),

        'user_id_title': fields.function(_get_user_id_title, string='Title', type='char',size=255,
            store=False,),

        'parent_order_id':fields.many2one('sale.order','Parent order ref'),

    }

    _defaults = {
        'lump_sum_invoiced':False,
        'lump_sum_type':'text',
        'currency_id': _get_default_currency,
        'retention_type':'P',
        'thankyou_text':'Thank you for inviting us to quote the above mentioned captioned, we are pleased to submit here with our Quotation for your evaluation and confirmation as follows:',
        'thankyou_text2':'We hope that the above will meet in-line with your requirements and should you require further information, please do not hesitate to contact the undersign',
        'validity':'30 days from the date of Quotation.',
        'term':'Upon Presentation of our Invoice.',
        'exclusion':'GST and all those items not mentioned in this Quotation.',
        'billing_time':0,
        'is_variation':False,
        'order_type':'big',
        'is_construction':True,
    }

sale_order()


class sale_order_line(osv.Model):
    _name='sale.order.line'
    _inherit = 'sale.order.line'

    def onchange_bill_percent(self,cr,uid,ids,bill_percent,context={}):
        self.write(cr,uid,ids,{'bill_percent':bill_percent})
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        default = dict(default or {})
        default.update({'billed_percent':0})
        return super(sale_order_line, self).copy(cr, uid, id, default, context=context)

    def _fnct_line_invoiced(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, False)
        for this in self.browse(cr, uid, ids, context=context):
            res[this.id] = this.invoice_lines and this.billed_percent>=100
        return res


    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = {}
        if not line.invoiced:
            if not account_id:
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = line.product_id.categ_id.property_account_income_categ.id
                    if not account_id:
                        raise osv.except_osv(_('Error!'),
                                _('Please define income account for this product: "%s" (id:%d).') % \
                                    (line.product_id.name, line.product_id.id,))
                else:
                    prop = self.pool.get('ir.property').get(cr, uid,
                            'property_account_income_categ', 'product.category',
                            context=context)
                    account_id = prop and prop.id or False
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            uos_id = self._get_line_uom(cr, uid, line, context=context)
            pu = 0.0
            if uosqty:
                pu = round((line.price_unit * line.product_uom_qty / uosqty)*line.bill_percent/100,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
            fpos = line.order_id.fiscal_position or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
            bill_percent = line.bill_percent
            if not account_id:
                raise osv.except_osv(_('Error!'),
                            _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
            res = {
                'name': line.name,
                'sequence': line.sequence,
                'origin': line.order_id.name,
                'account_id': account_id,
                'price_unit': pu,
                'quantity': uosqty,
                'discount': line.discount,
                'uos_id': uos_id,
                'product_id': line.product_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
                'add_percent':line.add_percent
            }

        return res



    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {}
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id,
                                        line.order_id.partner_id)
            cur = line.order_id.currency_id
            res[line.id]['add_amount'] = cur_obj.round(cr, uid, cur, taxes['total']*line.add_percent/100)
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'] + res[line.id]['add_amount'])
        return res

    def _order_lines_from_invoice(self, cr, uid, ids, context=None):
        # direct access to the m2m table is the less convoluted way to achieve this (and is ok ACL-wise)
        cr.execute("""SELECT DISTINCT sol.id FROM sale_order_invoice_rel rel JOIN
                                                  sale_order_line sol ON (sol.order_id = rel.order_id)
                                    WHERE rel.invoice_id = ANY(%s)""", (list(ids),))
        return [i[0] for i in cr.fetchall()]


    _columns = {
        'order_id': fields.many2one('sale.order', 'Order Reference',  ondelete='cascade', select=True, required=False,readonly=False),
        'name': fields.text('Description', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account'),
                                          multi="total_line"),
        'add_amount': fields.function(_amount_line, string='Add Amount', digits_compute=dp.get_precision('Account'),
                                          multi="total_line"),
        'add_percent':fields.float('Add %',digits_compute=dp.get_precision('Account')),
        'billed_percent':fields.float('% Billed',digits_compute=dp.get_precision('Account')),
        'bill_percent':fields.float('% Bill',digits_compute=dp.get_precision('Account')),
        'sale_order_hr_id':fields.many2one('sale.order','Sale HR id',ondelete='cascade',),
        'invoice_lines': fields.many2many('account.invoice.line', 'sale_order_line_invoice_rel', 'order_line_id', 'invoice_id', 'Invoice Lines', readonly=True, copy=False),
        'invoiced': fields.function(_fnct_line_invoiced, string='Invoiced', type='boolean',
            store={
                'account.invoice': (_order_lines_from_invoice, ['state'], 10),
                'sale.order.line': (lambda self,cr,uid,ids,ctx=None: ids, ['invoice_lines'], 10)
            }),
        'line_type':fields.selection([('normal','Normal'),('variation','Variation'),('additional','Additional')],'Line type'),
    }

    _defaults={
        'billed_percent':0,
        'line_type':'normal',
    }



class sale_bq_line(osv.Model):
    _name='sale.bq.line'

    def invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        create_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            if not line.invoiced:
                vals = self._prepare_order_line_invoice_line(cr, uid, line, context)
                if vals:
                    inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
                    self.write(cr, uid, [line.id], {'invoiced':True}, context=context)
                    create_ids.append(inv_id)
        return create_ids




    def _prepare_order_line_invoice_line(self, cr, uid, line, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = {}
        prop = self.pool.get('ir.property').get(cr, uid,
                'property_account_income_categ', 'product.category',
                context=context)
        account_id = prop and prop.id or False
        uosqty = 0
        pu = 0.0
        fpos = line.sale_order_bq_id.fiscal_position or False
        account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
        if not account_id:
            raise osv.except_osv(_('Error!'),
                        _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
        res = {
            'name': line.name,
            'origin': line.sale_order_bq_id.name,
            'account_id': account_id,
            'price_unit': line.price_unit,
            'quantity': line.product_uom_qty,
            'add_percent':line.add_percent,
        }

        return res



    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {}
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, [], price, line.product_uom_qty, False,
                                        line.sale_order_bq_id.partner_id)
            cur = line.sale_order_bq_id.currency_id
            res[line.id]['add_amount'] = cur_obj.round(cr, uid, cur, taxes['total']*line.add_percent/100)
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'] + res[line.id]['add_amount'])
        return res

    _columns = {

        'invoiced':fields.boolean('Invoiced'),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True,),
        'name': fields.text('Description', required=True),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account'),
                                          multi="total_line"),
        'add_amount': fields.function(_amount_line, string='Add Amount', digits_compute=dp.get_precision('Account'),
                                          multi="total_line"),
        'add_percent':fields.float('Add %',digits_compute=dp.get_precision('Account')),
        'sale_order_bq_id':fields.many2one('sale.order','Sale bq id',ondelete='cascade',),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'), ),
        'state': fields.selection(
                [('cancel', 'Cancelled'),('draft', 'Draft'),('confirmed', 'Confirmed'),('exception', 'Exception'),('done', 'Done')],
                'Status', required=True, readonly=True, copy=False,
                help='* The \'Draft\' status is set when the related sales order in draft status. \
                    \n* The \'Confirmed\' status is set when the related sales order is confirmed. \
                    \n* The \'Exception\' status is set when the related sales order is set as exception. \
                    \n* The \'Done\' status is set when the sales order line has been picked. \
                    \n* The \'Cancelled\' status is set when a user cancel the sales order related.'),

        'uom_id':fields.many2one('product.uom','UOM',)
    }

    _defaults = {
        'state': 'draft',
        'invoiced':False,
    }

class lump_sum_line(osv.Model):
    _name='lump.sum.line'

    _columns = {

        'invoiced':fields.boolean('Invoiced'),
        'name': fields.text('Description', required=True),
        'order_id':fields.many2one('sale.order','Sale bq id',ondelete='cascade',),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'qty': fields.float('Quantity', required=True, digits_compute= dp.get_precision('Account'), ),
        'state': fields.selection(
                [('cancel', 'Cancelled'),('draft', 'Draft'),('confirmed', 'Confirmed'),('exception', 'Exception'),('done', 'Done')],
                'Status', required=True, readonly=True, copy=False,
                help='* The \'Draft\' status is set when the related sales order in draft status. \
                    \n* The \'Confirmed\' status is set when the related sales order is confirmed. \
                    \n* The \'Exception\' status is set when the related sales order is set as exception. \
                    \n* The \'Done\' status is set when the sales order line has been picked. \
                    \n* The \'Cancelled\' status is set when a user cancel the sales order related.'),
    }

    _defaults = {
        'state': 'draft',
        'invoiced':False,
    }



class sale_hr_line(osv.Model):
    _name='sale.hr.line'


    def invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        create_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            if not line.invoiced:
                vals = self._prepare_order_line_invoice_line(cr, uid, line, context)
                if vals:
                    inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
                    self.write(cr, uid, [line.id], {'invoiced':True}, context=context)
                    create_ids.append(inv_id)
        return create_ids




    def _prepare_order_line_invoice_line(self, cr, uid, line, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = {}
        prop = self.pool.get('ir.property').get(cr, uid,
                'property_account_income_categ', 'product.category',
                context=context)
        account_id = prop and prop.id or False
        uosqty = 0
        pu = 0.0
        fpos = line.sale_order_hr_id.fiscal_position or False
        account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
        if not account_id:
            raise osv.except_osv(_('Error!'),
                        _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
        res = {
            'name': line.name,
            'origin': line.sale_order_hr_id.name,
            'account_id': account_id,
            'price_unit': line.price_unit,
            'quantity': line.product_uom_qty,
            'add_percent':line.add_percent,
        }

        return res



    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {}
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, [], price, line.product_uom_qty, False,
                                        line.sale_order_hr_id.partner_id)
            cur = line.sale_order_hr_id.currency_id
            res[line.id]['add_amount'] = cur_obj.round(cr, uid, cur, taxes['total']*line.add_percent/100)
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'] + res[line.id]['add_amount'])
        return res

    _columns = {

        'invoiced':fields.boolean('Invoiced'),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True,),
        'name': fields.text('Description', required=True),
        'remark': fields.text('Remarks', required=False),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account'),
                                          multi="total_line"),
        'add_amount': fields.function(_amount_line, string='Add Amount', digits_compute=dp.get_precision('Account'),
                                          multi="total_line"),
        'add_percent':fields.float('Add %',digits_compute=dp.get_precision('Account')),
        'sale_order_hr_id':fields.many2one('sale.order','Sale HR id',ondelete='cascade',),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'), ),
        'state': fields.selection(
                [('cancel', 'Cancelled'),('draft', 'Draft'),('confirmed', 'Confirmed'),('exception', 'Exception'),('done', 'Done')],
                'Status', required=True, readonly=True, copy=False,
                help='* The \'Draft\' status is set when the related sales order in draft status. \
                    \n* The \'Confirmed\' status is set when the related sales order is confirmed. \
                    \n* The \'Exception\' status is set when the related sales order is set as exception. \
                    \n* The \'Done\' status is set when the sales order line has been picked. \
                    \n* The \'Cancelled\' status is set when a user cancel the sales order related.'),
    }

    _defaults = {
        'state': 'draft',
        'invoiced':False,
    }


class project_user_sale(osv.Model):
    _name = 'project.user.sale'
    _columns = {
        'user_id': fields.many2one('res.users', 'User'),
        'sale_id': fields.many2one('sale.order', 'Sale'),
        'name': fields.char('Name'),
    }

