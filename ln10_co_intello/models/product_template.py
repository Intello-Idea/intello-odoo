from odoo import fields, models, api, exceptions

class ProductTemplate(models.Model):
    _inherit = "product.template"

    previous_code = fields.Char(string="Previous code")
