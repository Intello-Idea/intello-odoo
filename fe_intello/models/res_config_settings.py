from odoo import api, fields, models


class ResConfigSettingsMod(models.TransientModel):
    _inherit = 'res.config.settings'

    fe_online = fields.Boolean('Online',
                               help='If this field is active it allows a synchronous connection with the DIAN')
    fe_active = fields.Boolean('Is Active', help='If this field is active, electronic invoicing is working')
    fe_own_gr = fields.Boolean('Own Graphic Representation',
                               help='If this field is active, the graphic representation that will be used is its own')
    fe_send_mail = fields.Boolean('Send Mail',
                                  help="If this field is active, the invoice will be sent to the customer's email")

    def set_values(self):
        super(ResConfigSettingsMod, self).set_values()
        parameter = self.env['ir.config_parameter'].sudo()
        parameter.set_param('res.config.settings.fe_online', self.fe_online)
        parameter.set_param('res.config.settings.fe_active', self.fe_active)
        parameter.set_param('res.config.settings.fe_own_gr', self.fe_own_gr)
        parameter.set_param('res.config.settings.fe_send_mail', self.fe_send_mail)

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsMod, self).get_values()
        parameter = self.env['ir.config_parameter'].sudo()
        fe_online = parameter.get_param('res.config.settings.fe_online')
        fe_active = parameter.get_param('res.config.settings.fe_active')
        fe_own_gr = parameter.get_param('res.config.settings.fe_own_gr')
        fe_send_mail = parameter.get_param('res.config.settings.fe_send_mail')
        res.update(
            {'fe_online': fe_online, 'fe_active': fe_active, 'fe_own_gr': fe_own_gr, 'fe_send_mail': fe_send_mail})
        return res

    @api.onchange('fe_active')
    def _deactivate_fe(self):
        """Metodo que borra el campo de is_online de factura electronica cuando
            fe_active es falso"""

        if not self.fe_active:
            self.fe_online = None
