from odoo import fields, models, api


class Menu(models.Model):
    _inherit = "website.menu"

    class_icon = fields.Char('Class icon')

