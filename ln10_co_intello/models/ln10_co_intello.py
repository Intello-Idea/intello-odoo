# -*- coding: utf-8 -*-
from odoo import fields, models

class DocumentType(models.Model):
    _name = 'ln10_co_intello.documenttype'

    key_dian = fields.Integer(required=True, string="DIAN Key")
    name = fields.Char(requiered=True, index=True, string="Name")
    with_digit = fields.Boolean(default=False, string="With Verification Digit")

    _sql_constraints = [('keyDian_uniq', 'UNIQUE(key_dian)', 'Duplicate Key DIAN value is not allowed!'),
                        ('name_uniq', 'UNIQUE(name)', 'Duplicate Name is not allowed!')]
