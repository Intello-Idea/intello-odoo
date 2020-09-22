# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions
from odoo.tools.translate import _


class Company(models.Model):
    _inherit = "res.company"

    street_01 = fields.Many2one('ln10_co_intello.nomenclaturedian', compute='_compute_address',
                                related='partner_id.street_01',
                                inverse='_inverse_street_01', ondelete='set null', domain=[('type', '=', 'principal')])
    street_02 = fields.Integer(default='', compute='_compute_address', related='partner_id.street_02',
                               inverse='_inverse_street_02')
    street_03 = fields.Many2one('ln10_co_intello.nomenclaturedian', compute='_compute_address',
                                related='partner_id.street_03',
                                inverse='_inverse_street_03', ondelete='set null', domain=[('type', '=', 'letter')])
    street_04 = fields.Many2one('ln10_co_intello.nomenclaturedian', compute='_compute_address',
                                related='partner_id.street_04',
                                inverse='_inverse_street_04', ondelete='set null',
                                domain=[('type', '=', 'qualifiying')])
    street_05 = fields.Many2one('ln10_co_intello.nomenclaturedian', compute='_compute_address',
                                related='partner_id.street_05',
                                inverse='_inverse_street_05', ondelete='set null',
                                domain=[('type', '=', 'qualifiying')])
    street_06 = fields.Integer(default='', compute='_compute_address', related='partner_id.street_06',
                               inverse='_inverse_street_06')
    street_07 = fields.Many2one('ln10_co_intello.nomenclaturedian', related='partner_id.street_07',
                                compute='_compute_address',
                                inverse='_inverse_street_07', ondelete='set null', domain=[('type', '=', 'letter')])
    street_08 = fields.Many2one('ln10_co_intello.nomenclaturedian', compute='_compute_address',
                                related='partner_id.street_08',
                                inverse='_inverse_street_08', ondelete='set null',
                                domain=[('type', '=', 'qualifiying')])
    street_09 = fields.Integer(default='', compute='_compute_address', related='partner_id.street_09',
                               inverse='_inverse_street_09')
    street_10 = fields.Many2one('ln10_co_intello.nomenclaturedian', compute='_compute_address',
                                related='partner_id.street_10',
                                inverse='_inverse_street_10', ondelete='set null',
                                domain=[('type', '=', 'qualifiying')])
    street_11 = fields.Many2one('ln10_co_intello.nomenclaturedian', compute='_compute_address',
                                related='partner_id.street_11',
                                inverse='_inverse_street_11', ondelete='set null', domain=[('type', '=', 'additional')])
    street_12 = fields.Char(default='', compute='_compute_address', related='partner_id.street_12',
                            inverse='_inverse_street_12')
    street_13 = fields.Many2one('ln10_co_intello.nomenclaturedian', compute='_compute_address',
                                related='partner_id.street_13',
                                inverse='_inverse_street_13', ondelete='set null', domain=[('type', '=', 'additional')])
    street_14 = fields.Char(default='', compute='_compute_address', related='partner_id.street_14',
                            inverse='_inverse_street_14')
    street_15 = fields.Many2one('ln10_co_intello.nomenclaturedian', related='partner_id.street_15',
                                compute='_compute_address',
                                inverse='_inverse_street_15', ondelete='set null', domain=[('type', '=', 'additional')])
    street_16 = fields.Char(default='', compute='_compute_address', related='partner_id.street_16',
                            inverse='_inverse_street_16')

    dian_address = fields.Char(default='', related='partner_id.street_16', inverse='_inverse_dian_address')

    document_type = fields.Many2one('ln10_co_intello.documenttype', related='partner_id.document_type',
                                    ondelete='set null', string='Document Type', readonly=False)
    verification_code = fields.Char(compute='_compute_verification_codes', related='partner_id.verification_code',
                                    inverse='_inverse_verification_code', string='Verification Code',
                                    help='Redundancy check to verify the vat number has been typed in correctly.',
                                    readonly=False)

    country_enforce_cities = fields.Boolean(related='country_id.enforce_cities', readonly=True)
    state_id = fields.Many2one('res.country.state', compute='_compute_address', inverse='_inverse_state',
                               string="Fed. State", domain="[('country_id', '=?', country_id)]")
    city_id = fields.Many2one('res.city', string='City of Address')

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if not self.country_id:
            self.state_id = False

        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        if not self.state_id:
            self.city_id = False
            self.city = ''
            self.zip = ''

        if self.state_id and self.state_id != self.city_id.state_id:
            self.city_id = False
            self.city = ''
            self.zip = ''

        if self.state_id.country_id:
            self.country_id = self.state_id.country_id

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name
            self.zip = self.city_id.zipcode
            self.state_id = self.city_id.state_id

    @api.onchange('street_01', 'street_02', 'street_03', 'street_04', 'street_05', 'street_06', 'street_07',
                  'street_08', 'street_09', 'street_10', 'street_11', 'street_12', 'street_13', 'street_14',
                  'street_15', 'street_16')
    def _compute_full_address(self):
        address = (self.street_01, self.street_02, self.street_03, self.street_04, self.street_05, self.street_06,
                   self.street_07, self.street_08, self.street_09, self.street_10, self.street_11, self.street_12,
                   self.street_13, self.street_14, self.street_15, self.street_16)
        full_address = ''
        short_address = ''

        pos = 0
        for z in address:
            pos += 1
            if z:
                try:
                    x = z.name
                    y = z.abbreviation
                except AttributeError:
                    x = str(z)
                    y = str(z)

                if pos == 6:
                    x = 'No. ' + x

                if pos == 9:
                    x = '- ' + x

                if full_address != '':
                    full_address = full_address + ' ' + x.strip()
                    short_address = short_address + ' ' + y.strip().upper()
                else:
                    full_address = x.strip()
                    short_address = y.strip().upper()

        self.street = full_address.strip()
        self.dian_address = short_address.strip()

        self.partner_id.street = full_address.strip()
        self.partner_id.dian_address = short_address.strip()

    @api.onchange('vat')
    def _compute_verification_codes(self):
        multiplication_factors = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]

        # for partner in self.filtered(lambda partner: partner.vat and partner.country_id == self.env.ref('base.co') and
        #                              len(partner.vat) <= len(multiplication_factors)):
        if self.vat and self.vat != '':
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
        else:
            self.verification_code = ' '

        self.partner_id.vat = self.vat
        self.partner_id.verification_code = self.verification_code

    @api.constrains('document_type', 'vat', 'verification_code')
    def _check_document_type_with_digit_and_digit(self):
        if self.document_type.with_digit:
            if self.verification_code.strip() == '':
                raise exceptions.ValidationError(
                    "The VAT number is not correct, verification code couldn't be calculated")

    def _inverse_street_01(self):
        for company in self:
            company.partner_id.street_01 = company.street_01

    def _inverse_street_02(self):
        for company in self:
            company.partner_id.street_02 = company.street_02

    def _inverse_street_03(self):
        for company in self:
            company.partner_id.street_03 = company.street_03

    def _inverse_street_04(self):
        for company in self:
            company.partner_id.street_04 = company.street_04

    def _inverse_street_05(self):
        for company in self:
            company.partner_id.street_05 = company.street_05

    def _inverse_street_06(self):
        for company in self:
            company.partner_id.street_06 = company.street_06

    def _inverse_street_07(self):
        for company in self:
            company.partner_id.street_07 = company.street_07

    def _inverse_street_08(self):
        for company in self:
            company.partner_id.street_08 = company.street_08

    def _inverse_street_09(self):
        for company in self:
            company.partner_id.street_09 = company.street_09

    def _inverse_street_10(self):
        for company in self:
            company.partner_id.street_10 = company.street_10

    def _inverse_street_11(self):
        for company in self:
            company.partner_id.street_11 = company.street_11

    def _inverse_street_12(self):
        for company in self:
            company.partner_id.street_12 = company.street_12

    def _inverse_street_13(self):
        for company in self:
            company.partner_id.street_13 = company.street_13

    def _inverse_street_14(self):
        for company in self:
            company.partner_id.street_14 = company.street_14

    def _inverse_street_15(self):
        for company in self:
            company.partner_id.street_15 = company.street_15

    def _inverse_street_16(self):
        for company in self:
            company.partner_id.street_16 = company.street_16

    def _inverse_dian_address(self):
        for company in self:
            company.partner_id.dian_address = company.dian_address

    def _inverse_verification_code(self):
        for company in self:
            company.partner_id.verification_code = company.verification_code

    @api.model
    def create(self, vals):
        if not vals.get('favicon'):
            vals['favicon'] = self._get_default_favicon()
        if not vals.get('name') or vals.get('partner_id'):
            self.clear_caches()
            return super(Company, self).create(vals)
        partner = self.env['res.partner'].create({
            'name': vals['name'],
            'is_company': True,
            'image_1920': vals.get('logo'),
            'email': vals.get('email'),
            'phone': vals.get('phone'),
            'website': vals.get('website'),
            'vat': vals.get('vat'),
            'document_type': vals.get('document_type'),
            'verification_code': vals.get('verification_code'),
        })
        vals['partner_id'] = partner.id
        self.clear_caches()
        company = super(Company, self).create(vals)
        # The write is made on the user to set it automatically in the multi company group.
        self.env.user.write({'company_ids': [(4, company.id)]})

        # Make sure that the selected currency is enabled
        if vals.get('currency_id'):
            currency = self.env['res.currency'].browse(vals['currency_id'])
            if not currency.active:
                currency.write({'active': True})
        return company
