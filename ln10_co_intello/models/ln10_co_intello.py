# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
import inspect


class DocumentType(models.Model):
    _name = 'ln10_co_intello.documenttype'
    _description = "Colombian Document Type"

    key_dian = fields.Integer(required=True, string="DIAN Key")
    name = fields.Char(required=True, index=True, string="Name")
    with_digit = fields.Boolean(default=False, string="With Verification Digit")
    code_short = fields.Char('Code Short')

    _sql_constraints = [('keyDian_uniq', 'UNIQUE(key_dian)', 'Duplicate Key DIAN value is not allowed!'),
                        ('name_uniq', 'UNIQUE(name)', 'Duplicate Name is not allowed!')]


class DianCodes(models.Model):
    _name = 'ln10_co_intello.diancodes'
    _description = "Colombian DIAN Codes"

    key_dian = fields.Char(required=True, string="DIAN Key")
    name = fields.Char(required=True, index=True, string="Name")
    type = fields.Selection([('persontype', 'Person Type'),
                             ('fiscalregime', 'Fiscal Regime'),
                             ('fiscalresponsibility', 'Fiscal Responsibility'),
                             ('paymentmethod', 'Payment Method'),
                             ('representation', 'Representation'),
                             ('customs', 'Customs'),
                             ('establishment', 'Establishment'),
                             ('uom', 'Unit of Measure'),
                             ('lang', 'Language'),
                             ('fiscalposition', 'Fiscal Position'),
                             ('creditnote', 'Credit Note Concept'),
                             ('debitnote', 'Debit Note Concept')],

                            required=True, string="Code Type")

    '''
    _sql_constraints = [('keyDian_uniq', 'UNIQUE(type,key_dian)', 'Duplicate Key DIAN value is not allowed!')]
    ,('name_uniq', 'UNIQUE(type,name)', 'Duplicate Name is not allowed!')]
    '''


class CIIUCodes(models.Model):
    _name = 'ln10_co_intello.ciiucodes'
    _description = "Colombian CIIU Codes"

    code = fields.Char(required=True, string="Code")
    name = fields.Char(required=True, index=True, string="Name")
    industry_id = fields.Many2one('res.partner.industry', 'Industry')

    _sql_constraints = [('code_uniq', 'UNIQUE(code)', 'Duplicate Code value is not allowed!'),
                        ('name_uniq', 'UNIQUE(name)', 'Duplicate Name value is not allowed!')]


class NomenclatureDIAN(models.Model):
    _name = 'ln10_co_intello.nomenclaturedian'
    _description = "Colombian DIAN Nomenclature"

    abbreviation = fields.Char(required=True, string="Abbreviation")
    name = fields.Char(required=True, index=True, string="Name")
    type = fields.Selection([('principal', 'Principal'),
                             ('qualifiying', 'Qualifiying'),
                             ('additional', 'Additional'),
                             ('letter', 'Letters')], string="Nomenclature Type")

    _sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Duplicate Name value is not allowed!')]


class InvoiceResolution(models.Model):
    _name = 'account.dian.resolution'
    _description = 'Invoice Resolution'

    name = fields.Char(compute="_compute_name_resolution")
    resolution = fields.Char('Resolution Number', required=True, )

    date = fields.Date(string="Resolution Date")
    ini_date = fields.Date('Initial Date')
    fin_date = fields.Date('Final Date')
    prefix = fields.Char('Prefix')
    ini_number = fields.Integer('Init Number', default=1)
    fin_number = fields.Integer('Final Number', default=1)
    type = fields.Selection([('normal', 'Normal'), ('electronic', 'Electronic'), ], default="normal")

    @api.onchange('fin_date', 'ini_date')
    def _verify_date(self):

        if self.fin_date and self.ini_date:
            if self.ini_date > self.fin_date:
                raise exceptions.Warning(_("The start date cannot be greater than the end date"))

    @api.onchange('fin_number', 'ini_number')
    def _verify_number(self):

        if self.ini_number == 0:
            raise exceptions.Warning(_("The initial number cannot be equal to zero"))

        if self.ini_number > self.fin_number:
            raise exceptions.Warning(_("The initial number cannot be greater than the final number"))

    @api.model
    def _compute_name_resolution(self):
        for name in self:
            if name.prefix:
                name.name = name.prefix + " del " + str(name.ini_number) + " hasta " + str(
                    name.fin_number) + " - " + str(name.date)
            else:
                name.name = "Del " + str(name.ini_number) + " hasta " + str(name.fin_number) + " - " + str(name.date)
