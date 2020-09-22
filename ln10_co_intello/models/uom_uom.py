# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions
from odoo.tools.translate import _

class UoM(models.Model):
    _inherit = 'uom.uom'

    dian_code = fields.Many2one('ln10_co_intello.diancodes', ondelete='cascade', string='DIAN Code', domain=[('type', '=', 'uom')])
