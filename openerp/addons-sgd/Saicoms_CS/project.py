# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class project_project(osv.osv):
    _inherit = 'project.project'
    def _get_attached_docs(self, cr, uid, ids, field_name, arg, context):
        res = {}
        print 'ids', ids
        attachment = self.pool.get('ir.attachment')
        task = self.pool.get('project.task')
        for id in ids:
            project_attachments = attachment.search(cr, uid, [('res_model', '=', 'project.project'), ('res_id', '=', id)], context=context, count=True)
            task_ids = task.search(cr, uid, [('project_id', '=', id)], context=context)
            task_attachments = attachment.search(cr, uid, [('res_model', '=', 'project.task'), ('res_id', 'in', task_ids)], context=context, count=True)
            res[id] = (project_attachments or 0) + (task_attachments or 0)
        return res
    _columns = {
        'is_saicoms_cs':fields.boolean('Is saicoms CS Project'),
    }
    _defaults={
        'is_saicoms_cs':False,
    }
project_project()

class project_task(osv.osv):
    _inherit = 'project.task'

    def create(self,cr,uid,vals,context=None):
        if vals.get('project_id'):
            project_id = self.pool.get('project.project').browse(cr,uid,vals.get('project_id'))
            vals.update({'is_saicoms_cs':project_id.is_saicoms_cs})
        print 'context',context
        if context.get('is_sms_task'):
            vals.update({'is_sms_task':True})
        if context.get('is_mail_task'):
            vals.update({'is_mail_task':True})
        return super(project_task, self).create(cr, uid, vals, context=context)
    _columns = {
        'is_saicoms_cs':fields.boolean('Is saicoms CS Project'),
        'is_mail_task':fields.boolean('Is Mail Task'),
        'is_sms_task':fields.boolean('Is SMS Task'),
    }
    _defaults={
        'is_saicoms_cs':False,
        'is_mail_task':False,
        'is_sms_task':False,
    }
project_task()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

