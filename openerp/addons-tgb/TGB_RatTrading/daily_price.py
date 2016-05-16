# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import fields, osv
from lxml import etree
from openerp.tools.translate import _

from openerp.fields import Field, SpecialValue, FailedValue
from datetime import datetime
import openerp.addons.decimal_precision as dp

class rat_daily_price(osv.osv):
    _name = 'rat.daily.price'
    _order = 'id desc'
    _columns = {
        'name': fields.char(string='Name', size=255),
        'created_by': fields.many2one('res.users', string='Created By'),
        'date_import': fields.datetime(string='Date'),
        'price_detail_ids': fields.one2many('rat.daily.price.detail', 'parent_id', 'Price Detail'),
    }

    _defaults={
        'date_import':fields.datetime.now,
        'created_by':lambda obj, cr, uid, context: uid,
    }

    def create_product_list(self,cr,uid,ids,context=None):
        for id in self.browse(cr,uid,ids):
            current_products = self.pool.get('rat.daily.price.detail').search(cr,uid,[('parent_id','=',id.id)])
            self.pool.get('rat.daily.price.detail').unlink(cr,uid,current_products)
            product_ids = self.pool.get('product.product').search(cr,uid,[])
            now = datetime.now()
            if product_ids and len(product_ids)>0:
                for id in ids:
                    for product in product_ids:
                        price = self.pool.get('product.product').browse(cr,uid,product).lst_price
                        new_line = self.pool.get('rat.daily.price.detail').create(cr,uid,{'parent_id':id,
                                                                                           'product_id':product,
                                                                                            'date':now,
                                                                                           'price':price
                                                                                             })
        return True

    def get_weekly_item(self,cr,uid,ids,context=None):
        for id in self.browse(cr,uid,ids):
            current_products = self.pool.get('rat.daily.price.detail').search(cr,uid,[('parent_id','=',id.id)])
            self.pool.get('rat.daily.price.detail').unlink(cr,uid,current_products)
            product_ids = self.pool.get('product.product').search(cr,uid,[('product_weekly_item','=',True)])
            now = datetime.now()
            if product_ids and len(product_ids)>0:
                for id in ids:
                    for product in product_ids:
                        price = self.pool.get('product.product').browse(cr,uid,product).lst_price
                        new_line = self.pool.get('rat.daily.price.detail').create(cr,uid,{'parent_id':id,
                                                                                           'product_id':product,
                                                                                            'date':now,
                                                                                           'price':price
                                                                                             })
        return True


    def get_weekly_item2(self,cr,uid,ids,context=None):
        for id in self.browse(cr,uid,ids):
            current_products = self.pool.get('rat.daily.price.detail').search(cr,uid,[('parent_id','=',id.id)])
            self.pool.get('rat.daily.price.detail').unlink(cr,uid,current_products)
            product_ids = self.pool.get('product.product').search(cr,uid,[('product_weekly_item2','=',True)])
            now = datetime.now()
            if product_ids and len(product_ids)>0:
                for id in ids:
                    for product in product_ids:
                        price = self.pool.get('product.product').browse(cr,uid,product).lst_price
                        new_line = self.pool.get('rat.daily.price.detail').create(cr,uid,{'parent_id':id,
                                                                                           'product_id':product,
                                                                                            'date':now,
                                                                                           'price':price
                                                                                             })
        return True

    def get_weekly_item3(self,cr,uid,ids,context=None):
        for id in self.browse(cr,uid,ids):
            current_products = self.pool.get('rat.daily.price.detail').search(cr,uid,[('parent_id','=',id.id)])
            self.pool.get('rat.daily.price.detail').unlink(cr,uid,current_products)
            product_ids = self.pool.get('product.product').search(cr,uid,[('product_weekly_item3','=',True)])
            now = datetime.now()
            if product_ids and len(product_ids)>0:
                for id in ids:
                    for product in product_ids:
                        price = self.pool.get('product.product').browse(cr,uid,product).lst_price
                        new_line = self.pool.get('rat.daily.price.detail').create(cr,uid,{'parent_id':id,
                                                                                           'product_id':product,
                                                                                            'date':now,
                                                                                           'price':price
                                                                                             })
        return True


    def confirm_price(self,cr,uid,ids,context=None):
        for work in self.browse(cr,uid,ids):
            all_product_ids = self.pool.get('product.template').search(cr,uid,[])
            self.pool.get('product.template').write(cr,uid,all_product_ids,{'product_multi_active':False})
            for product in work.price_detail_ids:
                self.pool.get('product.product').write(cr,uid,product.product_id.id,{'lst_price':product.price})
                self.pool.get('product.template').write(cr,uid,product.product_id.product_tmpl_id.id,{'product_multi_active':True})


class rat_daily_price_detail(osv.osv):
    _name = 'rat.daily.price.detail'
    _columns = {
        'parent_id': fields.many2one('rat.daily.price', 'Parent Id'),
        'product_id': fields.many2one('product.product', string='Product', required=True),
        'date': fields.datetime(string='Date'),
        'price':fields.float('Price', digits_compute=dp.get_precision('Product Price')),
    }

    _defaults={
        'date':fields.datetime.now,
    }





        # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
