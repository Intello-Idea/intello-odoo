# -*- coding: utf-8 -*-
from odoo import fields, models, api

class Partner(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
    first_name = fields.Char(default='')
    second_name = fields.Char(default='')
    surname = fields.Char(default='')
    second_surname = fields.Char(default='')

    @api.onchange('first_name', 'second_name', 'surname', 'second_surname')
    def _compute_full_name(self):
        names = (self.first_name, self.second_name, self.surname, self.second_surname)
        full_name = ''
        for x in names:
            if x != '':
                if full_name != '':
                    full_name = full_name + ' ' + x.capitalize()
                else:
                    full_name = x.capitalize()

        self.name = full_name.strip()
        # self.name = ' '.join(names).strip().replace('  ', ' ')
