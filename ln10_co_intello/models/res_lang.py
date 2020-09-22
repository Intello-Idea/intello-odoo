# -*- coding: utf-8 -*-
from odoo import api, fields, models

class Lang(models.Model):
    _inherit = "res.lang"

    code_lang = fields.Many2one('ln10_co_intello.diancodes', ondelete='cascade', string='DIAN Code', domain=[('type', '=', 'lang')])