# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions
import re

class Partner(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    name = fields.Char(index=True)
    label_name = fields.Char(compute='_compute_label_name')
    first_name = fields.Char(default='')
    second_name = fields.Char(default='')
    surname = fields.Char(default='')
    second_surname = fields.Char(default='')

    # document_type = fields.One2many('ln10_co_intello.documenttype', 'key_dian', string='Document Type')
    document_type = fields.Many2one('ln10_co_intello.documenttype', ondelete='set null', string='Document Type')
    verification_code = fields.Char(compute='_compute_verification_code', string='Verification Code', help='Redundancy check to verify the vat number has been typed in correctly.')

    @api.depends('name')
    def _compute_label_name(self):
        self.label_name = self.name

    @api.onchange('first_name', 'second_name', 'surname', 'second_surname')
    def _compute_full_name(self):
        names = (self.first_name, self.second_name, self.surname, self.second_surname)
        full_name = ''

        for x in names:
            if x:
                if full_name != '':
                    full_name = full_name + ' ' + x.strip().capitalize()
                else:
                    full_name = x.strip().capitalize()

        self.name = full_name.strip()

        # self.name = ' '.join(names).strip().replace('  ', ' ')

    @api.depends('vat')
    def _compute_verification_code(self):
        multiplication_factors = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]

        # for partner in self.filtered(lambda partner: partner.vat and partner.country_id == self.env.ref('base.co') and
        #                              len(partner.vat) <= len(multiplication_factors)):
        if self.vat:
            if len(self.vat) <= len(multiplication_factors):
                number = 0
                padded_vat = self.vat

                while len(padded_vat) < len(multiplication_factors):
                    padded_vat = '0' + padded_vat

                # if there is a single non-integer in vat the verification code should be False
                try:
                    for index, vat_number in enumerate(padded_vat):
                        number += int(vat_number) * multiplication_factors[index]

                    number %= 11

                    if number < 2:
                        self.verification_code = number
                    else:
                        self.verification_code = 11 - number
                except ValueError:
                    self.verification_code = ' '

    @api.constrains('document_type', 'vat', 'verification_code')
    def _check_document_type_with_digit_and_digit(self):
        if self.document_type.with_digit:
            print('Si')
            print(self.verification_code)
            if self.verification_code.strip() == '':
                raise exceptions.ValidationError("The VAT number isn correct, verification code couldn't be calculated")

    def _validate_mail(self):
        if self.email:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email)
            if match == None:
                raise exceptions.ValidationError('Not a valid E-mail, is not the correct structure like something@example.com')

    @api.onchange('email')
    def validate_mail(self):
        self._validate_mail()

    @api.constrains('email')
    def _check_valid_mail(self):
        self._validate_mail()

    _sql_constraints = [('document_type_number_uniq', 'UNIQUE(document_type,vat)', 'Duplicate Document Type and VAT is not allowed!')]
