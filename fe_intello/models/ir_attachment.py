# -*- coding: utf-8 -*-
from odoo import fields, models, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    fe_filename = fields.Char('Fe filename')
    fe_file_code = fields.Char('Fe file code')
