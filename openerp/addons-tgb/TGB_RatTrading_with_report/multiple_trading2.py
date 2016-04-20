# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import fields, osv
from lxml import etree
from openerp.tools.translate import _

from openerp.fields import Field, SpecialValue, FailedValue


class wizard_rat_trading2(osv.osv):
    _name = 'wizard.rat.trading2'
    _columns = {
        'name': fields.char(string='Name', size=255),
        'created_by': fields.many2one('res.users', string='Created By'),
        'date_import': fields.datetime(string='Date'),
        'trading_detail_ids': fields.one2many('wizard.rat.trading.detail2', 'parent_id', 'Detail Quotation'),
    }

    _defaults={
        'date_import':fields.datetime.now,
        'created_by':lambda obj, cr, uid, context: uid,
    }
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}
        res = super(wizard_rat_trading2, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type,
                                                                     context=context, toolbar=toolbar, submenu=False)
        return res

    def default_get(self, cr, uid, fields, context=None):
        res = super(wizard_rat_trading2, self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id', False)
        return True

    def on_change_create_by(self,cr,uid,ids,created_by,context=None):
        customer_ids = self.pool.get('res.partner').search(cr,uid,[('customer','=',True)])
        if customer_ids and len(customer_ids)>0:
            for id in ids:
                for customer in customer_ids:
                    new_line = self.pool.get('wizard.rat.trading.detail2').create(cr,uid,{'parent_id':id,
                                                                                         'customer_id':customer,
                                                                                         })
        return True

    def create_customer_lines(self,cr,uid,ids,context=None):
        customer_ids = self.pool.get('res.partner').search(cr,uid,[('customer','=',True)])
        if customer_ids and len(customer_ids)>0:
            for id in ids:
                for customer in customer_ids:
                    new_line = self.pool.get('wizard.rat.trading.detail2').create(cr,uid,{'parent_id':id,
                                                                                         'customer_id':customer,
                                                                                         })

        return True



    def confirm_quotation(self,cr,uid,ids,context=None):
        for this in self.browse(cr,uid,ids):
            new_orders = []
            for item in this.trading_detail_ids:
                val_new_order={}
                val_new_order = self.pool.get('sale.order')._defaults
                val_new_order['partner_id'] = item.customer_id.id
                val_new_order['date_order'] = this.date_import
                val_new_order['company_id'] = self.pool.get('sale.order')._get_default_company(cr,uid)
                val_new_order['user_id'] = uid
                val_new_order['name'] =  '/'
                val_new_order['partner_invoice_id'] = self.pool.get('res.partner').address_get(cr, uid, [item.customer_id.id], ['invoice'])['invoice']
                val_new_order['partner_shipping_id'] = self.pool.get('res.partner').address_get(cr, uid, [item.customer_id.id], ['delivery'])['delivery']
                val_new_order['note'] = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.sale_note,
                val_new_order['section_id'] = self.pool.get('sale.order')._get_default_section_id(cr, uid)

                if not val_new_order['section_id']:
                    val_new_order['section_id'] = None
                new_order = self.pool.get('sale.order').create(cr,uid,val_new_order)
                new_orders.append(new_order)
                product_list_ids = self.pool.get('product.product').search(cr,uid,[])

                for product in product_list_ids:
                    if item['product_'+str(product)] !=0:
                        order = self.pool.get('sale.order').browse(cr,uid,new_order)
                        val_new_line = self.pool.get('sale.order.line')._defaults
                        val_new_line['order_id'] = new_order
                        val_new_line['product_uom'] = self.pool.get('sale.order.line')._get_uom_id(cr,uid)
                        val_new_line['product_id'] = product
                        val_new_line['product_uom_qty'] = item['product_'+str(product)]
                        fiscal_position = order.fiscal_position
                        # product_value = self.pool.get('sale.order.line').product_id_change(cr,uid,order.pricelist_id,product,item['product_'+str(product)],val_new_line['product_uom'],0,False,'',item.customer_id.id)['value']
                        product_value = self.pool.get('sale.order.line').product_id_change(cr, uid, [], order.pricelist_id.id, product,
                                                            qty=float(item['product_'+str(product)]),
                                                            uom=val_new_line['product_uom'],
                                                            qty_uos=0,
                                                            uos=False,
                                                            name='',
                                                            partner_id=item.customer_id.id,
                                                            date_order=this.date_import,
                                                            fiscal_position=fiscal_position,
                                                            flag=False,  # Force name update
                                                            context=dict(context or {}, company_id=order.company_id.id)
                                                            )['value']

                        val_new_line.update(product_value)
                        newline_id = self.pool.get('sale.order.line').create(cr,uid,val_new_line)


        # raise osv.except_osv(_('Warning!'),_("Not Implemented Yet!") )
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'sale', 'action_quotations')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of invoices to display
        if len(new_orders)>1:
            result['domain'] = "[('id','in',["+','.join(map(str, new_orders))+"])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'sale', 'view_order_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = new_orders and new_orders[0] or False
        return result

class wizard_rat_trading_detail2(osv.osv):
    _name = 'wizard.rat.trading.detail2'
    _columns = {
        'parent_id': fields.many2one('wizard.rat.trading2', 'Parent Id'),
        'customer_id': fields.many2one('res.partner', string='Customer',domain=[('customer', '=',True)], required=True),
    }

    _dynamic_fields_list = {}
    #

    @classmethod
    def _add_field(cls, name, field):
        """ Add the given ``field`` under the given ``name`` in the class """
        # add field as an attribute and in cls._fields (for reflection)
        if not isinstance(getattr(cls, name, field), Field):
            _logger.warning("In model %r, field %r overriding existing value", cls._name, name)
        setattr(cls, name, field)
        cls._fields[name] = field

        # basic setup of field
        field.set_class_name(cls, name)

        # cls._columns will be updated once fields are set up

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}
        res = super(wizard_rat_trading_detail2, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type,
                                                                     context=context, toolbar=toolbar, submenu=False)

        eview = etree.fromstring(res['arch'])
        summary = eview.xpath("//field[@name='customer_id']")
        summary = summary[0]

        template_ids = self.pool.get('product.template').search(cr,uid,[('product_multi_active','=',True)])
        product_list_ids = self.pool.get('product.product').search(cr,uid,[('product_tmpl_id','in',template_ids)])

        cls = type(self)
        from openerp import fields
        def add(name, field):
            """ add ``field`` with the given ``name`` if it does not exist yet """
            if name not in cls._fields:
                cls._add_field(name, field)



        for product in self.pool.get('product.product').browse(cr,uid,product_list_ids):

            summary.addnext(etree.Element('field', {'name': 'product_'+str(product.id),
                                                    'string': product.name,
                                                    # 'on_change':"onchange_product(product_%s)"%str(product.id),
                                                    }))

            res['fields']['product_'+str(product.id)] = {'digits': (16, 0), 'change_default': False, 'help': '', 'searchable': True,
                                      'views': {}, 'required': False, 'manual': False, 'readonly': False, 'depends': (),
                                      'company_dependent': False, 'sortable': True, 'type': 'float', 'store': True,
                                      'string': product.name}
            product_name = 'product_'+str(product.id)
            self._dynamic_fields_list[product_name] = product.name
        this_module = self.pool.get('ir.module.module').search(cr,uid,[('name','=','TGB_RatTrading')])
        if this_module and len(this_module)>0:
            self.pool.get('ir.module.module').button_immediate_upgrade(cr,uid,this_module[0])
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
            add(key, fields.Float(string=cls._dynamic_fields_list[key], automatic=True,))

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





        # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
