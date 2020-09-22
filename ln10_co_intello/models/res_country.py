# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions
from odoo.tools.translate import _


class CountryState(models.Model):
    _inherit = 'res.country.state'

    key_dian = fields.Char(string='DIAN State Code', help='The DIAN state code.', size=2)


class Country(models.Model):
    _inherit = "res.country"

    @api.model
    def change_state_country(self):
        country = self.env['res.country'].search([('code', '=', 'CO'), ('phone_code', '=', '57')])
        if country:
            country.update({
                'enforce_cities': True,
            })

            state_amazonas = self.env['res.country.state'].search(
                [('code', '=', "AMA"), ('country_id.id', '=', country.id)])
            if state_amazonas:
                state_amazonas.update({
                    'name': 'Amazonas',
                })
