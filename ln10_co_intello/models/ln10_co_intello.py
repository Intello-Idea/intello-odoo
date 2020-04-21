# -*- coding: utf-8 -*-
from odoo import fields, models, api

class DocumentType(models.Model):
    _name = 'ln10_co_intello.documenttype'
    _description = "Colombian Document Type"

    key_dian = fields.Integer(required=True, string="DIAN Key")
    name = fields.Char(required=True, index=True, string="Name")
    with_digit = fields.Boolean(default=False, string="With Verification Digit")

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
                             ('establishment', 'Establishment')],
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
                             ('additional', 'Additional')], string="Nomenclature Type")

    _sql_constraints = [('abbreviation_uniq', 'UNIQUE(abbreviation)', 'Duplicate Abbreviation value is not allowed!'),
                        ('name_uniq', 'UNIQUE(name)', 'Duplicate Name value is not allowed!')]

'''
    @api.multi
    def name_get(self, context=None):
        if context is None:
            context = {}
        res = []
        if context.get('display_code', False):
            for record in self:
                res.append(record.code)
        else:
            # Do a for and set here the standard display name, for example if the standard display name were name, you should do the next for
            for record in self:
                res.append(record.name)
        return res
'''
'''
    @api.multi
    def name_get(self):
        result = []
        for record in self:
            record_name = record.movie + ' - ' + record.seat_number
            result.append((record.id, record_name))
        return result

    def name_get(self, cr, uid, ids, context=None):
        if u'compute_name' in context:
            # check value from frontend and call custom method
            return getattr(self, context[u'compute_name'])(cr, uid, ids, context)
        else:
            # call base method
            return super(TestProject, self).name_get(cr, uid, ids, context=context)

    def _get_my_name(self, cr, uid, ids, context):
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            res.append((record.id, record.prj_id.name))
        return res
'''
'''
class PersonType(models.Model):
    _name = 'ln10_co_intello.persontype'

    key_dian = fields.Integer(required=True, string="DIAN Key")
    name = fields.Char(required=True, index=True, string="Name")

    _sql_constraints = [('keyDian_uniq', 'UNIQUE(key_dian)', 'Duplicate Key DIAN value is not allowed!'),
                        ('name_uniq', 'UNIQUE(name)', 'Duplicate Name is not allowed!')]

class FiscalRegime(models.Model):
    _name = 'ln10_co_intello.fiscalregime'

    key_dian = fields.Char(required=True, string="DIAN Key")
    name = fields.Char(required=True, index=True, string="Name")

    _sql_constraints = [('keyDian_uniq', 'UNIQUE(key_dian)', 'Duplicate Key DIAN value is not allowed!'),
                        ('name_uniq', 'UNIQUE(name)', 'Duplicate Name is not allowed!')]

class FiscalResponsibility(models.Model):
    _name = 'ln10_co_intello.fiscalresponsibility'

    key_dian = fields.Char(required=True, string="DIAN Key")
    name = fields.Char(required=True, index=True, string="Name")
    active = fields.Boolean(default=True)

    _sql_constraints = [('keyDian_uniq', 'UNIQUE(key_dian)', 'Duplicate Key DIAN value is not allowed!'),
                        ('name_uniq', 'UNIQUE(name)', 'Duplicate Name is not allowed!')]
'''