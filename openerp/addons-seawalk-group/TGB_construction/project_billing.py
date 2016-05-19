# -*- coding: utf-8 -*-

import openerp
from openerp import models, fields, api,_

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class project_billing(osv.osv):
    _inherit ='account.invoice'

    @api.depends('origin')
    def _get_sale_subject(self):
        print 'sale subject'

    hr_invoice_line = openerp.fields.One2many('hr.invoice.line', 'invoice_id', string='Invoice Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    origin = openerp.fields.Char(string='Source Document',
        help="Reference of the document that produced this invoice.",
        readonly=True, states={'draft': [('readonly', False)]})

    sale_subject = openerp.fields.Text(string='Subject', compute='_get_sale_subject', store=True)

    _columns = {
        'tgb_term':fields.char('Terms', size=255),
        'customer_po':fields.char('Customer PO',size=255),
        'delivery_ref':fields.char('Delivery Order Ref',size=255),
        'scope_of_work':fields.text('Scope of Works'),
        'scope_amount':fields.float('Scope Amount', digits_compute=dp.get_precision('Account')),
        'sale_order_id':fields.many2one('sale.order','Origin Sale Order'),
        'billing_time':fields.integer('Billing Claim',readonly=True),
        'is_progressive':fields.boolean('Is Progressive Invoice'),
        'progressive_id':fields.many2one('progressive.billing','Progressive Billing'),
        }

    _defaults={
        'tgb_term':'30 days upon the presentation of our invoice',
        'billing_time':0,
        'is_progressive':False,

    }

project_billing()


class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id','add_percent')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(price, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = taxes['total'] + self.add_amount
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)

    @api.one
    @api.depends('price_unit', 'quantity', 'invoice_id.currency_id','add_percent','invoice_line_tax_id',
        'invoice_id.partner_id', 'invoice_id.currency_id',)
    def _compute_add_amount(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(price, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        price_subtotal = taxes['total']
        self.add_amount = price_subtotal*self.add_percent/100

    price_subtotal = openerp.fields.Float(string='Amount', digits= dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_price')

    add_percent = openerp.fields.Float(string='Add (%)', digits= dp.get_precision('Account'),
        default=0.0)

    billed_percent = openerp.fields.Float(string='Bill (%)', digits= dp.get_precision('Account'),
        default=0.0)

    add_amount = openerp.fields.Float(string='Add Amount', digits= dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_add_amount')

    _defaults={
    }



class hr_invoice_line(osv.osv):
    _name = 'hr.invoice.line'

    @api.model
    def _default_account(self):
        # XXX this gets the default account for the user's company,
        # it should get the default account for the invoice's company
        # however, the invoice's company does not reach this point
        if self._context.get('type') in ('out_invoice', 'out_refund'):
            return self.env['ir.property'].get('property_account_income_categ', 'product.category')
        else:
            return self.env['ir.property'].get('property_account_expense_categ', 'product.category')


    @api.depends('price_unit', 'quantity', 'invoice_id.currency_id','add_percent','add_amount')
    def _compute_price(self):
        price = self.price_unit
        self.price_subtotal = price* self.quantity
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)

    @api.depends('price_unit', 'quantity', 'invoice_id.currency_id','add_percent')
    def _compute_add_amount(self):
        price = self.price_unit
        price_subtotal = price* self.quantity
        self.add_amount = price_subtotal*self.add_percent/100



    name = openerp.fields.Text(string='Description', required=True)

    price_subtotal = openerp.fields.Float(string='Amount', digits= dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_price')

    add_percent = openerp.fields.Float(string='Add (%)', digits= dp.get_precision('Account'),
        default=0.0)

    invoice_id = openerp.fields.Many2one('account.invoice', string='Invoice Reference',
        ondelete='cascade', index=True)

    price_unit = openerp.fields.Float(string='Unit Price', required=True,
        digits= dp.get_precision('Product Price'),
        default=0)



    quantity = openerp.fields.Float(string='Quantity', digits= dp.get_precision('Product Unit of Measure'),
        required=True, default=1)

    account_id = openerp.fields.Many2one('account.account', string='Account',
        required=True, domain=[('type', 'not in', ['view', 'closed'])],
        default=_default_account,
        help="The income or expense account related to the selected product.")

    add_amount = openerp.fields.Float(string='Add Amount', digits= dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_add_amount')






