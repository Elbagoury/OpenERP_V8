from openerp.osv import orm, fields
from openerp.tools.translate import _
import datetime
class wiz_student_report(orm.TransientModel):
    _name = 'employee.job.report'
    _columns = {
        'start_date': fields.date('Start Date'),
        'end_date': fields.date('End Date'),
    }

    def employee_report(self, cr, uid, ids, context=None):
        data = []
        datas = {
            'model': 'employee.job.report', # wizard model name
            'form': data,
            'context':context
        }
        return {
               'type': 'ir.actions.report.xml',
                'report_type': 'qweb-pdf',
               'report_name': 'tgb_shonan.report_employee_qweb',#module name.report template name
               'datas': datas,
           }

from openerp.report import report_sxw
from openerp.osv import osv

class EmployeeReportDocument(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(EmployeeReportDocument, self).__init__(cr, uid, name, context=context)
        ids = context.get('active_ids')
        self.localcontext.update({
            'get_employee': self.get_employee,
        })
        self.context = context

    def get_employee(self, report):
        res = {}
        sale_obj = self.pool.get('sale.order.line')
        sale_orders = sale_obj.search(self.cr,self.uid, [('order_id.date_order', '>=', report.start_date + ' 00:00:00'),
                                                ('order_id.date_order', '<=', report.end_date + ' 23:59:59'),
                                               ('order_id.state','!=','draft'),('order_id.state','!=','cancel')])
        if sale_orders:
            orders = sale_obj.browse(self.cr, self.uid, sale_orders)
        for order in orders:
           for line in order.employee_ids:
               if line.employee_id.id not in res:
                  res[line.employee_id.id] = {'name': line.employee_id.name, 'hour': 0, 'amount':0}
               res[line.employee_id.id]['hour'] += (order.total_time * line.percentage) / 100
               res[line.employee_id.id]['amount'] += (order.price_subtotal * line.percentage) / 100
        res_list = []
        for key, item in res.items():
            res_list.append(item)
        return res_list


class report_invoice_document(osv.AbstractModel):
    _name = 'report.tgb_shonan.report_employee_qweb'
    _inherit = 'report.abstract_report'
    _template = 'tgb_shonan.report_employee_qweb'
    _wrapped_report_class = EmployeeReportDocument
