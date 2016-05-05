# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools.translate import _

class sale_order(orm.Model):
    _inherit = 'sale.order'

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
        id = self.copy(cr, uid, ids[0], context=context)
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
            new_id = self.pool.get('progressive.billing').create(cr,uid,{'number':number,
                              'sale_order_id':project.id,
                                                                })

            for line in project.order_line:
                self.pool.get('progressive.billing.line').create(cr,uid,{'billing_id':new_id,
                                                                         'description':line.name,
                                                                         'contract_sum':line.price_subtotal,
                                                                         'total_work_up_to_date':line.billed_percent,
                                                                         'total_work_previous_date':line.billed_percent*line.price_subtotal/100,
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
            for line in o.order_line:
                if line.invoiced:
                    continue
                elif (line.state in states):
                    lines.append(line.id)
            created_lines = obj_sale_order_line.invoice_line_create(cr, uid, lines)
            if created_lines:
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
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'TGB_construction', 'project_view_order_form')
        view_id = view_ref and view_ref[1] or False,


        for quotation in self.browse(cr,uid,ids):
            if not quotation.project_id:
                subject = quotation.subject
                partner_id = quotation.partner_id
                if not subject:
                    subject = partner_id.name + ' Project'
                project_id = self.pool.get('project.project').create(cr,uid,{'name':subject,
                                                            'partner_id':partner_id.id})
                written = self.write(cr,uid,quotation.id,{'project_id':project_id,
                                                'project_confirm_id':project_id})
                print 'written', written
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

        result = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_construction_project_billing_action')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of invoices to display
        inv_ids = []
        for so in self.browse(cr, uid, ids, context=context):
            inv_ids += [invoice.id for invoice in so.invoice_ids]
        #choose the view_mode accordingly
        if len(inv_ids)>1:
            result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'TGB_construction', 'tgb_invoice_form_new')
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
            res[order.id]['amount_hr_total_word'] = num2words(res[order.id]['amount_hr_total'])
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
            res[order.id]['amount_bq_total_word'] = num2words(res[order.id]['amount_bq_total'])
        return res


    def onchange_scope_amount(self,cr,uid,ids,scope_amount,context={}):
        from num2words import num2words
        total_amount_word = num2words(scope_amount)
        return {'value':{'total_amount_word':total_amount_word}}



    def _amount_grand_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'total_scope_of_work': order.scope_amount,
                'total_detail': order.amount_untaxed,
                'total_hr': order.amount_hr_total,
                'total_grand': order.scope_amount+order.amount_untaxed+order.amount_hr_total,
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
            res[order.id]['amount_untaxed_word']= num2words(res[order.id]['amount_untaxed'])
        return res


    def make_deposit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context.update({
            'active_model': self._name,
            'active_ids': ids,
            'active_id': len(ids) and ids[0] or False
        })
        print 'gonna return'
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.sale.deposit.wiz',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }



    _columns = {
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
        'retention_day': fields.integer('Retention Days'),
        'retention_date': fields.date('Retention Date'),
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
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['user_id'], 10),
            },),

    }

    _defaults = {
        'currency_id': _get_default_currency,
        'retention_type':'A',
        'thankyou_text':'Thank you for inviting us to quote the above mentioned captioned, we are pleased to submit here with our Quotation for your evaluation and confirmation as follows:',
        'thankyou_text2':'We trust that the above will met in-line with your requirement and should you require further information, please do not hesitate to contact the undersign',
        'validity':'30 days from the date of Quotation.',
        'term':'30 days from the date of our Invoice.',
        'exclusion':'GST and all those items not mentioned in this Quotation.',
        'billing_time':0,
    }

sale_order()


class sale_order_line(osv.Model):
    _name='sale.order.line'
    _inherit = 'sale.order.line'

    def onchange_bill_percent(self,cr,uid,ids,bill_percent,context={}):
        self.write(cr,uid,ids,{'bill_percent':bill_percent})
        print 'bill_percent', bill_percent, ids
        return True

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
    }

    _defaults={
        'billed_percent':0,
    }



class sale_bq_line(osv.Model):
    _name='sale.bq.line'

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
    }

    _defaults = {
        'state': 'draft',
    }



class sale_hr_line(osv.Model):
    _name='sale.hr.line'

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
    }


class project_user_sale(osv.Model):
    _name = 'project.user.sale'
    _columns = {
        'user_id': fields.many2one('res.users', 'User'),
        'sale_id': fields.many2one('sale.order', 'Sale'),
        'name': fields.char('Name'),
    }


class project_scr(osv.Model):
    _name = 'project.scr'
    _columns = {
        'sale_id': fields.many2one('sale.order', 'Sale'),
        'name': fields.char('SCR number'),
        'date': fields.date('Date'),
        'amount': fields.float('Amount'),
    }


class project_attachment(osv.Model):
    _name = 'project.attachment'
    _columns = {
        'sale_id': fields.many2one('sale.order', 'Sale'),
        'stock_picking_id': fields.many2one('stock.picking', 'Stock Picking'),
        'stock_picking_in_id': fields.many2one('stock.picking.in', 'Stock Picking In'),
        'stock_picking_out_id': fields.many2one('stock.picking.out', 'Stock Picking Out'),
        'name': fields.char('File name'),
        'attachment': fields.many2one('ir.attachment', 'Attachment'),
    }


class customer_purchase_order(osv.Model):
    _name = 'customer.purchase.order'
    _columns = {
        'name': fields.char('Document No'),
        'sequence': fields.integer('Seq No'),
        'project_id': fields.many2one('project.project', 'Project No', required=True),
        'partner_id': fields.many2one('res.partner', 'Customer', required=True),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'customer_job_no': fields.char('Customer Job No'),
        'subject': fields.text('Subject'),
        'customer_po_date': fields.date('Customer Po Date', required=True),
        'customer_po_no': fields.char('Customer Po No', required=True),
        'material_source': fields.many2one('construction.material.source', 'Material Source'),
        'ref_no': fields.char('Ref No'),
        'cumulative_amount': fields.float('Cumulative amount'),
        'current_po_amount': fields.float('Current Po Amount'),
        'scr_ids': fields.one2many('customer.po.scr', 'cpo_id', 'SCR'),
    }
    _defaults = {
        'customer_po_date': fields.date.context_today,
    }


class customer_purchase_order(osv.Model):
    _name = 'customer.purchase.order'
    _columns = {
        'name': fields.char('Document No'),
        'sequence': fields.integer('Seq No'),
        'project_id': fields.many2one('project.project', 'Project No', required=True),
        'partner_id': fields.many2one('res.partner', 'Customer', required=True, domain=[('customer', '=', True)]),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'customer_job_no': fields.char('Customer Job No'),
        'subject': fields.char('Subject', size=500),
        'customer_po_date': fields.date('Customer Po Date', required=True),
        'customer_po_no': fields.char('Customer Po No', required=True),
        'material_source': fields.many2one('construction.material.source', 'Material Source'),
        'ref_no': fields.char('Ref No'),
        'cumulative_amount': fields.float('Cumulative amount'),
        'current_po_amount': fields.float('Current Po Amount'),
        'scr_ids': fields.one2many('customer.po.scr', 'cpo_id', 'SCR'),
    }
    _defaults = {
        'customer_po_date': fields.date.context_today,
    }


class construction_material_source(osv.Model):
    _name = 'construction.material.source'
    _columns = {
        'name': fields.char('Name'),
    }


class project_scr(osv.Model):
    _name = 'customer.po.scr'
    _columns = {
        'cpo_id': fields.many2one('customer.purchase.order', 'Customer PO'),
        'name': fields.char('SCR number'),
        'date': fields.date('Date'),
        'amount': fields.float('Amount'),
    }


class project_cost_allowcation(osv.Model):
    _name = 'project.cost.allocation'
    _columns = {
        'name': fields.char('Voucher No'),
        'date': fields.date('Cost Allocation Date', required=True),
        'project_id': fields.many2one('project.project', 'Project No', required=True),
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'default_type': fields.char('Default Type'),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'exchange_rate': fields.char('Exchange Rate'),
        'ref_no': fields.char('Ref No'),
        'total_add_amount': fields.float('Total Add Amount'),
        'total_add_amount_home': fields.float('Total Add Amount'),
        'total_reduce_amount': fields.float('Total Add Amount'),
        'total_reduce_amount_home': fields.float('Total Add Amount'),
        'created_uid2': fields.many2one('res.users', 'Created By'),
        'created_date2': fields.date('Create Date'),
        'detail_ids': fields.one2many('project.cost.detail', 'pro_cost_id', 'Detail'),
        'internal_remark_code': fields.char('Internal Remark Code'),
        'external_remark_code': fields.char('External Remark Code'),
        'internal_remark': fields.text('Internal Remark'),
        'external_remark': fields.text('External Remark'),
    }
    _defaults = {
        'date': fields.date.context_today,
        'exchange_rate': 1,
    }


class project_type(osv.Model):
    _name = 'construction.project.type'
    _columns = {
        'name': fields.char('Type'),
    }


class project_scr(osv.Model):
    _name = 'project.cost.detail'
    _columns = {
        'name': fields.char('Name'),
        'pro_cost_id': fields.many2one('project.cost.allocation', 'Project Cost Allocation'),
        'type': fields.many2one('construction.project.type','Type'),
        'item_type': fields.char('Item Type'),
        'product_id': fields.many2one('product.product', 'Item Code/Remarks', required=True),
        'uom_id': fields.related('product_id','uom_id',type='many2one',relation='product.uom', string= 'UOM',readonly=True),
        'total_amount': fields.float('Total Amount'),
        'total_amount_home': fields.float('Total Home Amount'),
    }
