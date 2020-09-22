from odoo import fields, models


class City(models.Model):
    _inherit = 'res.city'

    key_dian = fields.Char("DIAN Code", help='The DIAN City code.', size=5)
