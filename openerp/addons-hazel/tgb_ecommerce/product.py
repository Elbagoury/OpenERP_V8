# -*- coding: utf-8 -*-


from openerp.osv import fields, osv
occasion_list = []
occasion_text = ['Happy Birthday',
                 'Speedy Recovery',
                 'Get Well Soon',
                 'Official Opening',
                 'Best wishes',
                 'Annual Dinner & Dance',
                 'New Bord',
                 'WDS&C',
                 'WDS&HC',
                 'Sympathy']
for text in occasion_text:
    occasion_list.append((text,text))

class crm_phonecall_status(osv.osv):
    _name = 'crm.phonecall.status'
    _columns = {
        'name': fields.char('Status', size=128, required=True),
    }

class crm_phonecall(osv.osv):
    _inherit = 'crm.phonecall'

    def action_save(self, cr, uid, ids, context=None):
        return True

    def action_show_form(self, cr, uid, ids, context=None):

        return {
            'name': 'Call form',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.phonecall',
            'res_id': ids[0],
            'target': 'new',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': context,
        }

    def _get_phone_id(self, cr, uid, ids, field_name, arg, context=None):
        r = dict.fromkeys(ids, False)
        for call in self.browse(cr, uid, ids):
            r[call.id] = call.id
        return r

    def _get_default_status(self, cr, uid, context=None):
        res = self.pool.get('crm.phonecall.status').search(cr,uid,[])
        if res:
            return res[0]
        return None

    _columns = {
        'mode': fields.selection([('Phone', 'Phone'),
                                  ('Email', 'Email'),
                                  ('Fax', 'Fax'),
                                  ('Walk-in', 'Walk-in'),
                                  ('Website', 'Website')], 'Mode', required=True),
        'call_priority': fields.selection([('Low', 'Low'),
                                    ('Medium', 'Medium'),
                                  ('High', 'High'),], 'Priority', required=True),
        'call_type': fields.selection([('Order Taken', 'Order Taken'),
                                  ('Complain', 'Complain'),
                                  ('Other', 'Other'),], 'Type', required=True),
        'phone_id': fields.function(_get_phone_id, string='Call id', type='integer', readonly=True),
        'call_status': fields.many2one('crm.phonecall.status', 'Status', required=True),

        # Complain field
        'complain_do_no': fields.char('D/O No', size=128),
        'complain_customer_ac': fields.char('Customer A/C', size=128),
        'complain_delivery_date': fields.datetime('Delivery Date/Time'),
        'complain_order_take': fields.many2one('res.users', 'Taken by'),
        'complain_order_asst': fields.many2one('res.users', 'Asst by'),
        'complain_order_arr': fields.many2one('res.users', 'Arr by'),
        'complain_order_qc': fields.many2one('res.users', 'Qc by'),
        'complain_order_delivery': fields.many2one('res.users', 'Delivery by'),
        'complain_date': fields.date('Date of Complain'),
        'complain_problem': fields.text('Nature of Problems'),
        'complain_problem_cause': fields.text('Cause of Problems'),
        'complain_date_solve': fields.date('Date Solved'),
        'complain_solution': fields.text('Solutions Offer to Customer'),
        'complain_amount': fields.float('Invoice amount'),
        'complain_customer_pay': fields.boolean('Customer will pay'),
        'complain_customer_pay_amount': fields.float('S$'),
        'complain_charge_to': fields.boolean('Charge to'),
        'complain_charge_person': fields.many2one('res.users','Charge to'),
        'complain_charge_to_amount': fields.float('S$'),
        'complain_forfeit': fields.boolean('Forfeit No-Complain Reward'),
        'complain_forfeit_amount': fields.float('S$'),
        'complain_perform': fields.boolean('Will perform'),
        'complain_perform_amount': fields.float('S$'),
        'complain_write_off': fields.boolean('Write-off by Company'),
        'complain_write_off_amount': fields.float('S$'),
        'complain_record_signature': fields.binary('Record by'),
        'complain_record_date': fields.date('Date'),
        'complain_acknowledge_signature': fields.binary('Acknowledge by'),
        'complain_acknowledge_date': fields.date('Date'),
        'complain_remarks': fields.text('Remarks'),

        # Order fields
        'order_no': fields.char('No.', size=128),
        'order_typed_by': fields.many2one('res.users', 'Typed by'),
        'order_term': fields.char('Terms', size=128),
        'order_no_do': fields.boolean('No. D/O'),
        'order_combine': fields.boolean('Combine Inv/E-Inv'),
        'order_customer': fields.boolean('Customer'),
        'order_lead': fields.boolean('Lead'),
        'order_add': fields.boolean('Add'),
        'order_statement': fields.boolean('Statement'),
        'order_stock': fields.boolean('Stock'),
        'order_delivery_address': fields.boolean('Delivery Address'),
        'order_charge_card': fields.boolean('Charge card'),
        'order_instruction': fields.boolean('Instruction'),
        'order_name_address': fields.text("Receipient's name & address"),
        'order_to': fields.char('To', size=128),
        'order_refer_to_do':fields.char('Refer to D/O', size=128),
        'order_tel': fields.char('Tel', size=128),
        'order_tel_check': fields.boolean('Tel check'),
        'order_occasion': fields.selection(occasion_list, 'Occasion'),
        'order_message': fields.text('Order message'),
        'order_message_refer_do': fields.char('Refer to D/O', size=128),
        'order_from': fields.text('Order message'),
        'order_flower_setting': fields.char('Flower Settings', size=128),
        'order_flower': fields.char('Flower', size=128),
        'order_flower_stock': fields.char('Stock', size=128),
        'order_deco': fields.char('Deco', size=128),
        'order_flower_setting2': fields.char('Flower Settings', size=128),
        'order_flower2': fields.char('Flower', size=128),
        'order_flower_stock2': fields.char('Stock', size=128),
        'order_deco2': fields.char('Deco', size=128),
        'order_store_use': fields.text('For Store Use'),
        'order_amount': fields.float('Amount'),
        'order_invoice': fields.float('Invoice(w/GST)'),
        'order_reference': fields.char('Reference',size=128, help="Refer order by otherwise stated"),
        'order_rebate_ac': fields.char('Rebate AC',size=128, help="If coupon to diff/not below addr"),
        'order_bill_attn': fields.char('Bill Attn',size=128, help="Refer order by otherwise stated"),
        'order_company': fields.char('Company', size=256),
        'order_company_address': fields.text('Address'),
        'order_company_caller_id': fields.char('Caller Id', size=128),
        'order_company_tel': fields.char('Tel', size=128),
        'order_for_info': fields.char('For Info', size=256),
        'order_order_by': fields.char('Order By', size=128),
        'order_remarks': fields.text('Remarks'),
        'order_charge_card2': fields.boolean('Charge Card'),
        'order_fax':fields.char('Fax', size=128),
        'order_att_flower_catalog': fields.boolean('Att. Flower Catalog'),
        'order_no_rebate_slip': fields.boolean('No Rebate Slip'),
        'order_collect_cash': fields.boolean('Collect Cash After Delivery'),
        'order_cod':fields.boolean('C.O.D'),
        'order_charge': fields.float('Charge'),
        'order_offset_coupon': fields.char('Offset Coupon', size=128),

        'end_date': fields.datetime('End time'),
    }
    _defaults = {
        'call_status': _get_default_status,
        'call_priority': 'Low',
        'call_type': 'Other',
    }
    
    def bt_print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
            
        datas = {'ids': ids}
        datas['model'] = 'crm.phonecall'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':ids[0],'active_ids':ids})
        return {'type': 'ir.actions.report.xml', 'report_name': 'order_form_report', 'datas': datas}


class product_occasion(osv.osv):
    _name = 'product.occasion'

    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'messages': fields.one2many('occasion.message', 'occasion_id', string='Default message')
    }


class occasion_message(osv.osv):
    _name = 'occasion.message'

    _columns = {
        'occasion_id': fields.many2one('product.occasion', required=True),
        'message': fields.text('Message'),
    }


class res_microsite(osv.osv):
    _name = 'res.microsite'
    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'product_ids': fields.one2many('product.microsite', 'site'),
    }


class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'occasion_ids': fields.many2many('product.occasion', string='Occasion'),
        'microsite': fields.one2many('product.microsite', 'product_id'),
        'featured': fields.boolean('Featured'),
        'chinese_name': fields.text('Chinese name'),
        'specs': fields.text('Specs'),
    }

    def get_default_message(self, cr, uid, ids, context=None):
        res = {}
        for product in self.browse(cr, uid, ids):
            res[product.id] = []
            for occasion in product.occasion_ids:
                for message in occasion.messages:
                    res[product.id].append(message.message)
        return res

    _defaults = {
        'featured': False,
    }


class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'wp_ref': fields.char('Wordpress Reference', size=256),
        'occasion_ids': fields.many2many('product.occasion', string='Interest'),
    }


class product_microsite(osv.osv):
    _name = 'product.microsite'

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'site': fields.many2one('res.microsite', 'Microsite', required=True),
        'price': fields.float('Price', digits=(16, 2)),
    }
