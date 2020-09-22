from odoo import api, fields, models


class ResConfigSettingsMod(models.TransientModel):
    _inherit = 'res.config.settings'

    extend_expense = fields.Boolean('Extend Expense', )

    def set_values(self):
        super(ResConfigSettingsMod, self).set_values()
        parameter = self.env['ir.config_parameter'].sudo()
        parameter.set_param('res.config.settings.extend_expense', self.extend_expense)

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsMod, self).get_values()
        parameter = self.env['ir.config_parameter'].sudo()
        extend_expense = parameter.get_param('res.config.settings.extend_expense')
        res.update({'extend_expense': extend_expense})
        return res
