from odoo import api, fields, models


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    value = fields.Float('Value', default="1")

    @api.onchange('value')
    def calculate_currency(self):
        self.rate = 1 / self.value

    @api.onchange('rate')
    def calculate_rate(self):
        self.value = 1 / self.rate
