from lxml import etree
import json
from odoo import api, fields, models


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    partner_id = fields.Many2one('res.partner', string='Vendor')

    def action_move_create(self):
        parameter = self.env['ir.config_parameter'].sudo()
        check_status = parameter.get_param('res.config.settings.extend_expense')

        action = super(HrExpense, self).action_move_create()
        if check_status:
            action[self.id].line_ids.update({
                'partner_id': self.partner_id,
            })
        return action

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        parameter = self.env['ir.config_parameter'].sudo()
        check_status = parameter.get_param('res.config.settings.extend_expense')

        res = super(HrExpense, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='partner_id']"):
            if check_status:
                node.set("invisible", "0")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['invisible'] = False
                node.set("modifiers", json.dumps(modifiers))
            else:
                node.set("invisible", "1")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['invisible'] = True
                node.set("modifiers", json.dumps(modifiers))

        res['arch'] = etree.tostring(doc)

        return res
