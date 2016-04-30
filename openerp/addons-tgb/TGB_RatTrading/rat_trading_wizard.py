# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import fields, osv
from lxml import etree
from openerp.tools.translate import _
from openerp.fields import Field, SpecialValue, FailedValue
import os

import openerp.addons.decimal_precision as dp
import xlsxwriter
import base64
import xlrd
from base64 import b64decode

class rat_trading_wizard(osv.osv):
    _name = 'rat.trading.wizard'

    def _total_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids):
            res[order.id] = {}
            total = 0
            list_product = map(lambda x: x.field_name, order.product_list_ids)
            for item in order.trading_detail_ids:
                field = ''
                for product_id in list_product:
                    field += str(product_id) + ','
                field = field[:len(field) - 1]
                sql = """ select %s from rat_trading_detail where id = %s
                """ % (field, item.id)
                cr.execute(sql)
                result = cr.fetchall()
                for sql_res in result[0]:
                    if sql_res:
                        total += sql_res
            # for item in rat_trading_detail.read(cr, uid, detail_ids, []):
            # # for item in order.trading_detail_ids:
            #     for field in self.pool.get('ir.model.fields').browse(cr,uid,field_list_ids):
            #         if field.name not in default_fields:
            #             print 'Testttttttttttttt       %s' % field.name
            #
            #     for product in product_list_ids:
            #         print 'itemm ', 'product_'+str(product)
            #         if item['product_'+str(product)] !=0:
            #             total+= item['product_'+str(product)]
            res[order.id] = total
        return res

    _columns = {
        'name': fields.char(string='Name', size=255, readonly=True, states={'draft': [('readonly', False)],}, ),
        'created_by': fields.many2one('res.users', string='Created By', readonly=True,
                                      states={'draft': [('readonly', False)],}, ),
        'date_import': fields.datetime(string='Date', readonly=True, states={'draft': [('readonly', False)],}, ),
        'trading_detail_ids': fields.one2many('rat.trading.detail', 'parent_id', 'Detail Quotation', readonly=True,
                                              states={'draft': [('readonly', False)],}, ),
        'product_list_ids': fields.one2many('rat.trading.product', 'parent_id', 'Product List'),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('done', 'Done'),
        ], 'Status', readonly=True, track_visibility='onchange', ),
        'total_amount': fields.function(_total_amount, digits_compute=dp.get_precision('Account'),
                                        string='Total Quantity',
                                        help="The amount of overview", track_visibility='always'),
        'report_generated':fields.boolean('Templates Generated',),
        'template_data':fields.binary("Template",readonly=True),
        'template_name':fields.char("Filename",size=100,readonly=True),
        'import_data':fields.binary('Import templates',),
    }

    def update_total_amount(self, cr, uid, ids, context=None):
        return True

    def create_customer_lines_monday(self, cr, uid, ids, context=None):
        customer_ids = self.pool.get('res.partner').search(cr, uid,
                                                           [('customer', '=', True), ('customer_monday', '=', True)])
        if customer_ids and len(customer_ids) > 0:
            for id in ids:
                for customer in customer_ids:
                    new_line = self.pool.get('rat.trading.detail').create(cr, uid, {'parent_id': id,
                                                                                    'customer_id': customer,
                                                                                    })
        return True

    def create_customer_lines_wednesday(self, cr, uid, ids, context=None):
        customer_ids = self.pool.get('res.partner').search(cr, uid,
                                                           [('customer', '=', True), ('customer_wednesday', '=', True)])
        if customer_ids and len(customer_ids) > 0:
            for id in ids:
                for customer in customer_ids:
                    new_line = self.pool.get('rat.trading.detail').create(cr, uid, {'parent_id': id,
                                                                                    'customer_id': customer,
                                                                                    })
        return True

    def create_customer_lines_friday(self, cr, uid, ids, context=None):
        customer_ids = self.pool.get('res.partner').search(cr, uid,
                                                           [('customer', '=', True), ('customer_friday', '=', True)])
        if customer_ids and len(customer_ids) > 0:
            for id in ids:
                for customer in customer_ids:
                    new_line = self.pool.get('rat.trading.detail').create(cr, uid, {'parent_id': id,
                                                                                    'customer_id': customer,
                                                                                    })
        return True

    def create_customer_lines(self, cr, uid, ids, context=None):
        customer_ids = self.pool.get('res.partner').search(cr, uid, [('customer', '=', True)])
        if customer_ids and len(customer_ids) > 0:
            for id in ids:
                for customer in customer_ids:
                    new_line = self.pool.get('rat.trading.detail').create(cr, uid, {'parent_id': id,
                                                                                    'customer_id': customer,
                                                                                    })
        return True

    def save_quotation(self, cr, uid, ids, context=None):
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if context == None: context = {}
        return super(rat_trading_wizard, self).write(cr, uid, ids, vals, context=context)

    def create(self, cr, uid, vals, context=None):
        if context == None: context = {}
        new_wizard = super(rat_trading_wizard, self).create(cr, uid, vals, context=context)
        for key in rat_trading_detail._dynamic_fields_list.keys():
            self.pool.get('rat.trading.product').create(cr, uid, {'parent_id': new_wizard,
                                                                  'field_name': key,
                                                                  'product_name':rat_trading_detail._dynamic_fields_list[key]})
        return new_wizard

    def generate_excel(self, cr, uid, ids, context=None):
        if isinstance(ids, (list)):
            ids = ids[0]
        order = self.browse(cr,uid,ids)
        list_product = map(lambda x: {x.field_name:x.product_name}, order.product_list_ids)
        fields_list = map(lambda x: x.field_name, order.product_list_ids)
        current_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_path, 'static/templates/multiple_quotation.xlsx')
        workbook = xlsxwriter.Workbook(path)
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, 'Customer Name')
        worksheet.write(0, 1, 'Customer Id')
        for col in range(0, len(list_product)):
            worksheet.write(0, col+2, list_product[col].values()[0])
        row = 0
        for detail in order.trading_detail_ids:
            row += 1
            if detail.parent_id:
                worksheet.write(row, 0, detail.customer_id.name)
                worksheet.write(row, 1, str(detail.customer_id.id))
            for col in range(0, len(list_product)):
                worksheet.write(row, col+2, detail[list_product[col].keys()[0]])
        workbook.close()
        with open(path, 'rb') as f:
            data = f.read()
        self.write(cr,uid,ids,{'template_data':base64.encodestring(data),'template_name': str(order.name) + '_template'+'.xlsx','report_generated':True})
        return True

    def import_xls(self, cr, uid, ids, context=None):
        print 'here we in import_xls'
        if isinstance(ids, (list)):
            ids = ids[0]
        order = self.browse(cr,uid,ids)
        list_product = map(lambda x: {x.field_name:x.product_name}, order.product_list_ids)
        detail_ids = map(lambda x: x.id, order.trading_detail_ids)
        print 'unlink ids', detail_ids
        self.pool.get('rat.trading.detail').unlink(cr,uid,detail_ids)
        if order.import_data:
            workbook = xlrd.open_workbook(file_contents=b64decode(order.import_data))
            sheet = workbook.sheet_by_index(0)
            header = sheet.row_values(0)
            print header
            field_pos = {}
            for i in range(2,len(header),2):
                for field in list_product:
                    if field.values()[0] == header[i]:
                        field_pos.update({i:field.keys()[0], i+1: field.keys()[0]+'_price'})
            for r in range(1, sheet.nrows):
                row = sheet.row_values(r)
                partner_id = row[1]
                detail_vals = {'customer_id':partner_id,
                               'parent_id':order.id}
                print 'partner_id ', partner_id
                for i in xrange(2,len(row),2):
                    if field_pos.get(i):
                        detail_vals.update({field_pos[i]:row[i]})
                    if field_pos.get(i+1):
                        detail_vals.update({field_pos[i+1]:row[i+1]})
                new_detail = self.pool.get('rat.trading.detail').create(cr,uid,detail_vals)
                print 'create new detail', new_detail
        return True



    def confirm_quotation(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids):
            new_orders = []
            for item in this.trading_detail_ids:
                val_new_order = {}
                val_new_order = self.pool.get('sale.order')._defaults
                val_new_order.update(self.pool.get('sale.order').default_get(cr, uid, ['warehouse_id', 'company_id']))
                val_new_order['partner_id'] = item.customer_id.id
                val_new_order['date_order'] = this.date_import
                val_new_order['user_id'] = uid
                val_new_order['name'] = '/'
                val_new_order['partner_invoice_id'] = \
                    self.pool.get('res.partner').address_get(cr, uid, [item.customer_id.id], ['invoice'])['invoice']
                val_new_order['partner_shipping_id'] = \
                    self.pool.get('res.partner').address_get(cr, uid, [item.customer_id.id], ['delivery'])['delivery']
                val_new_order['note'] = self.pool.get('res.users').browse(cr, uid, uid,
                                                                          context=context).company_id.sale_note,
                val_new_order['section_id'] = self.pool.get('sale.order')._get_default_section_id(cr, uid)

                if not val_new_order['section_id']:
                    val_new_order['section_id'] = None
                print 'val_new_order ', val_new_order
                new_order = self.pool.get('sale.order').create(cr, uid, val_new_order)
                template_ids = self.pool.get('product.template').search(cr, uid, [('product_multi_active', '=', True)])
                product_list_ids = self.pool.get('product.product').search(cr, uid,
                                                                           [('product_tmpl_id', 'in', template_ids)])
                have_lines = False
                for product in product_list_ids:
                    if item['product_' + str(product)] != 0:
                        have_lines = True
                        order = self.pool.get('sale.order').browse(cr, uid, new_order)
                        val_new_line = self.pool.get('sale.order.line')._defaults
                        val_new_line['order_id'] = new_order
                        val_new_line['product_uom'] = self.pool.get('sale.order.line')._get_uom_id(cr, uid)
                        val_new_line['product_id'] = product
                        val_new_line['product_uom_qty'] = item['product_' + str(product)]
                        val_new_line['price_unit'] = item['product_' + str(product) + '_price']
                        fiscal_position = order.fiscal_position
                        # product_value = self.pool.get('sale.order.line').product_id_change(cr,uid,order.pricelist_id,product,item['product_'+str(product)],val_new_line['product_uom'],0,False,'',item.customer_id.id)['value']
                        product_value = \
                            self.pool.get('sale.order.line').product_id_change(cr, uid, [], order.pricelist_id.id,
                                                                               product,
                                                                               qty=float(
                                                                                   item['product_' + str(product)]),
                                                                               uom=val_new_line['product_uom'],
                                                                               qty_uos=0,
                                                                               uos=False,
                                                                               name='',
                                                                               partner_id=item.customer_id.id,
                                                                               date_order=this.date_import,
                                                                               fiscal_position=fiscal_position,
                                                                               flag=False,  # Force name update
                                                                               context=dict(context or {},
                                                                                            company_id=order.company_id.id)
                                                                               )['value']

                        product_value['price_unit'] = item['product_' + str(product) + '_price']

                        val_new_line.update(product_value)
                        newline_id = self.pool.get('sale.order.line').create(cr, uid, val_new_line)
                if have_lines:
                    new_orders.append(new_order)
                else:
                    # self.pool.get('sale.order').unlink(cr,uid,new_order)
                    print 'Nothing to do if we have no lines'
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'sale', 'action_quotations')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        # compute the number of invoices to display
        if len(new_orders) > 0:
            self.write(cr, uid, ids, {'state': 'done'})
        if len(new_orders) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, new_orders)) + "])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'sale', 'view_order_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = new_orders and new_orders[0] or False
        return result

    _defaults = {
        'date_import': fields.datetime.now,
        'created_by': lambda obj, cr, uid, context: uid,
        'state': 'draft',
        'report_generated':False,
    }


class rat_trading_detail(osv.osv):
    _name = 'rat.trading.detail'
    _columns = {
        'parent_id': fields.many2one('wizard.rat.trading', 'Parent Id'),
        'customer_id': fields.many2one('res.partner', string='Customer', domain=[('customer', '=', True)],
                                       required=True),
    }
    _dynamic_fields_list = {}
    _temp_product_list_ids = []

    def default_get(self, cr, uid, fields, context=None):
        res = super(rat_trading_detail, self).default_get(cr, uid, fields, context=context)
        template_ids = self.pool.get('product.template').search(cr, uid, [('product_multi_active', '=', True)])
        product_list_ids = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', 'in', template_ids)])
        for product in self.pool.get('product.product').browse(cr, uid, product_list_ids):
            if 'product_' + str(product.id) + '_price' in fields:
                res.update({'product_' + str(product.id) + '_price': product.lst_price})
        return res

    def get_product_list(self, cr, uid, wizard_id, context=None):
        if not context:
            context = {}
        product_list_ids = []
        if wizard_id:
            product_list_ids = self.pool.get('rat.trading.product').search(cr, uid, [('parent_id', '=', wizard_id)])
            product_list_ids = map(lambda x: int(x.field_name[8:len(x.field_name)]),
                                   self.pool.get('rat.trading.product').browse(cr, uid, product_list_ids))
            print 'product_list_idsproduct_list_idsproduct_list_ids', product_list_ids
        if len(product_list_ids) > 0:
            return product_list_ids
        template_ids = self.pool.get('product.template').search(cr, uid, [('product_multi_active', '=', True)])
        product_list_ids = self.pool.get('product.product').search(cr, uid,
                                                                   [('product_tmpl_id', 'in', template_ids)])
        return product_list_ids

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}
        res = super(rat_trading_detail, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type,
                                                              context=context, toolbar=toolbar, submenu=False)
        eview = etree.fromstring(res['arch'])
        summary = eview.xpath("//field[@name='customer_id']")
        summary = summary[0]

        # template_ids = self.pool.get('product.template').search(cr, uid, [('product_multi_active', '=', True)])
        # product_list_ids = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', 'in', template_ids)])
        new_product_list_ids = self.get_product_list(cr, uid, context.get('default_form_id'))
        self._temp_product_list_ids = new_product_list_ids
        cls = type(self)

        # TODO Save old method
        # from openerp import fields
        # def add(name, field):
        #     """ add ``field`` with the given ``name`` if it does not exist yet """
        #     if name not in cls._fields:
        #         cls._add_field(name, field)
        # for product in self.pool.get('product.product').browse(cr,uid,product_list_ids):
        #
        #     summary.addnext(etree.Element('field', {'name': 'product_'+str(product.id)+'_price',
        #                                             'string': 'Price',
        #                                             }))
        #     if not product.default_code:
        #         raise osv.except_osv(_("Error"), _('%s is not assigned default code yet.')% product.name)
        #     summary.addnext(etree.Element('field', {'name': 'product_'+str(product.id),
        #                                             'string': product.default_code,
        #                                             'sum':'Total',
        #                                             }))
        #     cls._defaults['product_'+str(product.id)+'_price'] = product.lst_price
        #
        #     res['fields']['product_'+str(product.id)] = {'digits': (16, 0), 'change_default': False, 'help': '', 'searchable': True,
        #                               'views': {}, 'required': False, 'manual': False, 'readonly': False, 'depends': (),
        #                               'company_dependent': False, 'sortable': True, 'type': 'float', 'store': True,
        #                               'string': product.name}
        #     res['fields']['product_'+str(product.id)+'_price'] = {'digits': (16, 2), 'change_default': False, 'help': '', 'searchable': True,
        #                               'views': {}, 'required': False, 'manual': False, 'readonly': False, 'depends': (),
        #                               'company_dependent': False, 'sortable': True, 'type': 'float', 'store': True,
        #                               'string': 'price'}
        #
        #     product_name = 'product_'+str(product.id)
        #     self._dynamic_fields_list[product_name] = product.name
        # this_module = self.pool.get('ir.module.module').search(cr,uid,[('name','=','TGB_RatTrading')])
        # if this_module and len(this_module)>0:
        #     self.pool.get('ir.module.module').button_immediate_upgrade(cr,uid,this_module[0])

        for product in self.pool.get('product.product').browse(cr, uid, new_product_list_ids):
            summary.addnext(etree.Element('field', {'name': 'product_' + str(product.id) + '_price',
                                                    'string': 'Price',
                                                    }))
            # if not product.default_code:
            #     raise osv.except_osv(_("Error"), _('%s is not assigned default code yet.')% product.name)
            print 'product ', product, product.default_code
            field_string = product.default_code or product.name_template or '  '
            summary.addnext(etree.Element('field', {'name': 'product_' + str(product.id),
                                                    'string': field_string,
                                                    'sum': 'Total',
                                                    }))
            cls._defaults['product_' + str(product.id) + '_price'] = product.lst_price

            res['fields']['product_' + str(product.id)] = {'digits': (16, 0), 'change_default': False, 'help': '',
                                                           'searchable': True,
                                                           'views': {}, 'required': False, 'manual': False,
                                                           'readonly': False, 'depends': (),
                                                           'company_dependent': False, 'sortable': True,
                                                           'type': 'float', 'store': True,
                                                           'string': product.name}
            res['fields']['product_' + str(product.id) + '_price'] = {'digits': (16, 2), 'change_default': False,
                                                                      'help': '', 'searchable': True,
                                                                      'views': {}, 'required': False, 'manual': False,
                                                                      'readonly': False, 'depends': (),
                                                                      'company_dependent': False, 'sortable': True,
                                                                      'type': 'float', 'store': True,
                                                                      'string': 'price'}
            product_name = 'product_' + str(product.id)
            self._dynamic_fields_list[product_name] = product.default_code
        this_module = self.pool.get('ir.module.module').search(cr, uid, [('name', '=', 'TGB_RatTrading')])
        if this_module and len(this_module) > 0:
            self.pool.get('ir.module.module').button_immediate_upgrade(cr, uid, this_module[0])
        res['arch'] = etree.tostring(eview)
        return res

    @classmethod
    def _add_magic_fields(cls):
        """ Introduce magic fields on the current class

        * id is a "normal" field (with a specific getter)
        * create_uid, create_date, write_uid and write_date have become
          "normal" fields
        * $CONCURRENCY_CHECK_FIELD is a computed field with its computing
          method defined dynamically. Uses ``str(datetime.datetime.utcnow())``
          to get the same structure as the previous
          ``(now() at time zone 'UTC')::timestamp``::

              # select (now() at time zone 'UTC')::timestamp;
                        timezone
              ----------------------------
               2013-06-18 08:30:37.292809

              >>> str(datetime.datetime.utcnow())
              '2013-06-18 08:31:32.821177'
        """

        def add(name, field):
            """ add ``field`` with the given ``name`` if it does not exist yet """
            if name not in cls._fields:
                cls._add_field(name, field)

        # cyclic import
        from openerp import fields

        # this field 'id' must override any other column or field
        cls._add_field('id', fields.Id(automatic=True))

        add('display_name', fields.Char(string='Display Name', automatic=True,
                                        compute='_compute_display_name'))

        for key in cls._dynamic_fields_list:
            add(key, fields.Float(string=cls._dynamic_fields_list[key], automatic=True, ))
            add(key + '_price', fields.Float(string='price', automatic=True, ))

        if cls._log_access:
            add('create_uid', fields.Many2one('res.users', string='Created by', automatic=True))
            add('create_date', fields.Datetime(string='Created on', automatic=True))
            add('write_uid', fields.Many2one('res.users', string='Last Updated by', automatic=True))
            add('write_date', fields.Datetime(string='Last Updated on', automatic=True))
            last_modified_name = 'compute_concurrency_field_with_access'
        else:
            last_modified_name = 'compute_concurrency_field'

        cls._add_field(cls.CONCURRENCY_CHECK_FIELD, fields.Datetime(
            string='Last Modified on', compute=last_modified_name, automatic=True))


class rat_trading_product(osv.osv):
    _name = 'rat.trading.product'
    _columns = {
        'parent_id': fields.many2one('rat.trading.wizard', 'Parent Id'),
        'field_name': fields.char('field name', size=100),
        'product_id':fields.many2one('product.product', 'Product id'),
        'product_name':fields.char('Name' ,size=255),
    }
