from openerp import models, api
from openerp import fields as fields2
from openerp.osv import fields, osv
from base64 import b64decode
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import csv

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class res_partner(models.Model):
    _inherit = 'res.partner'

    _columns = {
        "sequence_id": fields.many2one("ir.sequence", 'Sequence'),
        'customer_type': fields.selection([('software', 'Software'),
                                           ('prototypes', 'Prototypes')], string='Customer Type', )
    }
    _defaults = {
        'customer_type': 'software',
    }

    def create(self, cr, uid, vals, context=None):
        if not vals.get('sequence_id'):
            sequence_id = self.pool.get('ir.sequence').create(cr, uid, {
                'name': '%s Sequence Number' % vals.get('name', ''),
                'code': 'sale.order',
                'prefix': '%(y)s' + '/%s/' % vals.get('name', '').lower(),
            })
            vals['sequence_id'] = sequence_id
        return super(res_partner, self).create(cr, uid, vals, context)


class res_company(models.Model):
    _inherit = 'res.company'
    _columns = {
        'currency_rate': fields.float('Currency rate', digits=(16, 6)),
    }
    _defaults = {
        'currency_rate': 1,
    }


class sale_order(models.Model):
    _inherit = 'sale.order'

    def start_order(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'is_start': True})

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            partner = self.pool.get('res.partner').browse(cr, uid, vals.get('partner_id'))
            if partner.sequence_id:
                vals['name'] = self.pool.get('ir.sequence').next_by_id(cr, uid, partner.sequence_id.id) or '/'
            else:
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.order') or '/'
        if vals.get('partner_id') and any(f not in vals for f in
                                          ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id',
                                           'fiscal_position']):
            defaults = self.onchange_partner_id(cr, uid, [], vals['partner_id'], context=context)['value']
            if not vals.get('fiscal_position') and vals.get('partner_shipping_id'):
                delivery_onchange = self.onchange_delivery_id(cr, uid, [], vals.get('company_id'), None,
                                                              vals['partner_id'], vals.get('partner_shipping_id'),
                                                              context=context)
                defaults.update(delivery_onchange['value'])
            vals = dict(defaults, **vals)
        ctx = dict(context or {}, mail_create_nolog=True)
        new_id = super(sale_order, self).create(cr, uid, vals, context=ctx)
        self.message_post(cr, uid, [new_id], body=_("Quotation created"), context=ctx)
        return new_id

    _columns = {
        'email': fields.related('partner_id', 'email', type='char', string='Email'),
        'phone': fields.related('partner_id', 'phone', type='char', string='Phone'),
        'fax': fields.related('partner_id', 'fax', type='char', string='Fax'),
        'mobile': fields.related('partner_id', 'mobile', type='char', string='Mobile'),
        'sign_type': fields.selection([('sign', 'Sign'),
                                       ('image', 'Image')], string='Signature Type', readonly=True,
                                      states={'draft': [('readonly', False)], 'progress': [('readonly', False)],
                                              'manual': [('readonly', False)]}, ),

        'currency_term': fields.selection([('usd', 'USD Dollar'),
                                           ('sgd', 'SGD Dollar')], string='Currency Term', readonly=True,
                                          states={'draft': [('readonly', False)], 'progress': [('readonly', False)],
                                                  'manual': [('readonly', False)]}, ),
        'type': fields.selection([('software', 'Software'),
                                  ('prototypes', 'Prototypes')], string='Quotation Type', readonly=True,
                                 states={'draft': [('readonly', False)], 'progress': [('readonly', False)],
                                         'manual': [('readonly', False)]}, ),
        'currency_rate': fields.float('Currency rate', digits=(16, 6), readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'file': fields.binary('Import File', readonly=True,
                              states={'draft': [('readonly', False)]}),
        'employee': fields.many2one('hr.employee', 'Assign To', readonly=True,
                                    states={'draft': [('readonly', False)], 'progress': [('readonly', False)],
                                            'manual': [('readonly', False)]}, ),

        'requestor': fields.many2one('res.partner', string='Requestor', readonly=True,
                                     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, ),
        'is_start': fields.boolean('Is start'),
    }
    signature_image = fields2.Binary(string='Signature', readonly=True,
                                     states={'draft': [('readonly', False)], 'progress': [('readonly', False)],
                                             'manual': [('readonly', False)]}, )
    signature_image2 = fields2.Binary(string='Signature', readonly=True,
                                      states={'draft': [('readonly', False)], 'progress': [('readonly', False)],
                                              'manual': [('readonly', False)]}, )

    def set_done(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state': 'done'})

    def _get_currency_rate(self, cr, uid, context=None):
        rate = 1
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        if company_id:
            rate = company_id.currency_rate
        return rate

    def import_lines(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context):
            try:
                if order.file and order.state in ['draft']:
                    csv_reader = csv.reader(StringIO(b64decode(order.file)), delimiter=',', quotechar='"')
                    count = 0
                    for row in csv_reader:
                        count += 1
                        if count == 1:
                            continue
                        description = row[0]
                        quantity = float(row[1])
                        material = row[2].lower()
                        self.pool.get('sale.order.line').create(cr, uid, {
                            'order_id': order.id,
                            'name': description,
                            'product_uom_qty': quantity,
                            'material': material,
                        })
            except Exception as e:
                raise osv.except_osv(_('Error!'), _("Error while importing %s " % e))
            self.write(cr, uid, [order.id], {'file': None})

    _defaults = {
        'sign_type': 'sign',
        'currency_term': 'sgd',
        'currency_rate': _get_currency_rate,
        'is_start': False,
    }


selection = [(v, str(v)) for v in range(10, 101)]


class hr_employee_order(models.Model):
    _name = 'hr.employee.order'
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'order_line_id': fields.many2one('sale.order.line', 'Order Line'),
        'percentage': fields.float('Percentage'),
    }


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    @api.depends('product_uom_qty', 'rate', 'adjust', 'p_hour', 'p_min', 'a_hour', 'a_min', 'j_hour', 'j_min', 'm_hour',
                 'm_min', 'product_id', 'temp_price_unit')
    def _amount_line(self):
        if self.order_id.type != 'software':
            total_time = 0
            time_type = ['p', 'a', 'j', 'm']
            for t_type in time_type:
                total_time += getattr(self, '%s_hour' % t_type)
                total_time += getattr(self, '%s_min' % t_type) / 60
            total_time *= self.product_uom_qty
            price_unit = total_time * self.rate

            sub_total = price_unit + self.adjust
            self.price_subtotal = sub_total
            self.total_time = total_time
            self.price_unit = price_unit
        else:
            tax_obj = self.pool.get('account.tax')
            cur_obj = self.pool.get('res.currency')
            if not self.temp_price_unit:
                self.temp_price_unit = self.product_id.list_price
            self.price_unit = self.temp_price_unit
            price = self.temp_price_unit * (1 - (self.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(self.env.cr, self.env.uid, self.tax_id, price, self.product_uom_qty,
                                        self.product_id, self.order_id.partner_id)
            cur = self.order_id.pricelist_id.currency_id
            self.price_subtotal = cur_obj.round(self.env.cr, self.env.uid, cur, taxes['total'])
            self.margin = self.temp_price_unit - self.product_id.standard_price
            if self.product_id.standard_price:
                self.margin_percent = self.temp_price_unit / self.product_id.standard_price * 100

    _columns = {
        'product_id': fields.many2one('product.product', string='Product', required=False),
        'product_id_text': fields.char('Product ID', size=128, readonly=True),
        'order_number': fields.related('order_id', 'name', string='Order No', type='char', size=128, readonly=True),
        'quotation_number': fields.char('Quotation No', size=128),
        'p_hour': fields.float('P Hour', readonly=True, states={'draft': [('readonly', False)]}),
        'p_min': fields.float('P Min', readonly=True, states={'draft': [('readonly', False)]}),
        'a_hour': fields.float('A Hour', readonly=True, states={'draft': [('readonly', False)]}),
        'a_min': fields.float('A Min', readonly=True, states={'draft': [('readonly', False)]}),
        'j_hour': fields.float('J Hour', readonly=True, states={'draft': [('readonly', False)]}),
        'j_min': fields.float('J Min', readonly=True, states={'draft': [('readonly', False)]}),
        'm_hour': fields.float('M Hour', readonly=True, states={'draft': [('readonly', False)]}),
        'm_min': fields.float('M Min', readonly=True, states={'draft': [('readonly', False)]}),
        'rate': fields.selection(selection=selection, string='Rate', readonly=True,
                                 states={'draft': [('readonly', False)]}),
        'adjust': fields.float('Adjustment', readonly=True, states={'draft': [('readonly', False)]}),
        'material': fields.selection(
            [('metal', 'Metal'), ('plastic', 'Plastic'), ('copper', 'Copper')],
            'Material', readonly=True, states={'draft': [('readonly', False)]}),
        'price_unit': fields.float(compute="_amount_line", string='Price Unit',
                                   digits_compute=dp.get_precision('Account')),
        'remarks': fields.text('Remarks'),
        'price_subtotal': fields.float(compute="_amount_line", string='Subtotal',
                                       digits_compute=dp.get_precision('Account')),
        'total_time': fields.float(compute="_amount_line", string='Total time',
                                   digits_compute=dp.get_precision('Account')),
        'employee_ids': fields.one2many('hr.employee.order', 'order_line_id', string='Assign To', readonly=True,
                                        states={'confirmed': [('readonly', False)],'manual': [('readonly', False)]}),
        'margin': fields.float(compute="_amount_line", string='Margin',
                               digits_compute=dp.get_precision('Account')),
        'margin_percent': fields.float(compute="_amount_line", string='Margin',
                                       digits_compute=dp.get_precision('Account')),
        'temp_price_unit': fields.float('Price Unit', digits_compute=dp.get_precision('Account'))

    }

    def create(self, cr, uid, vals, context={}):
        vals['product_id_text'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.order.line')
        return super(sale_order_line, self).create(cr, uid, vals, context=context)


class product_product(osv.Model):
    _inherit = 'product.product'

    def _sales_count(self, cr, uid, ids, field_name, arg, context=None):
        r = dict.fromkeys(ids, 0)
        return r

    _columns = {
        'sales_count': fields.function(_sales_count, string='# Sales', type='integer'),
    }
