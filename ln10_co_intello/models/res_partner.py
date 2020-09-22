# -*- coding: utf-8 -*-

from lxml import etree

from odoo import fields, models, api, exceptions
from odoo.tools.translate import _

import re

'''
class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    tax_type_src_id = fields.Many2one('ln10_co_intello.taxestype', string='Tax Type on Product', required=True)
    tax_type_dest_id = fields.Many2one('ln10_co_intello.taxestype', string='Tax Type to Apply')

    _sql_constraints = [
        ('tax_type_src_dest_uniq',
         'unique (position_id,tax_type_src_id,tax_type_dest_id)',
         'A tax fiscal position could be defined only one time on same taxes type.')
    ]
'''


class Partner(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    name = fields.Char(index=True)
    label_name = fields.Char(compute='_compute_label_name')
    first_name = fields.Char(default='')
    second_name = fields.Char(default='')
    surname = fields.Char(default='')
    second_surname = fields.Char(default='')

    term_extra_client = fields.Many2one('account.payment.term', string="Extra Client Term")
    term_extra_provider = fields.Many2one('account.payment.term', string="Extra Provider Term")
    quota_client = fields.Float(string='Quota Client')
    quota_provider = fields.Float(string='Quota Provider')
    extra_quota_client = fields.Float(string="Extra Quota Client")
    extra_quota_provider = fields.Float(string="Extra Quota Provider")

    street_01 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'principal')])
    street_02 = fields.Integer(default='')
    street_03 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'letter')])
    street_04 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'qualifiying')])
    street_05 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'qualifiying')])
    street_06 = fields.Integer(default='')
    street_07 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'letter')])
    street_08 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'qualifiying')])
    street_09 = fields.Integer(default='')
    street_10 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'qualifiying')])
    street_11 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'additional')])
    street_12 = fields.Char(default='')
    street_13 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'additional')])
    street_14 = fields.Char(default='')
    street_15 = fields.Many2one('ln10_co_intello.nomenclaturedian', ondelete='set null',
                                domain=[('type', '=', 'additional')])
    street_16 = fields.Char(default='')

    dian_address = fields.Char(default='')

    # document_type = fields.One2many('ln10_co_intello.documenttype', 'key_dian', string='Document Type')
    document_type = fields.Many2one('ln10_co_intello.documenttype', ondelete='set null', string='Document Type')
    verification_code = fields.Char(compute='_compute_verification_codes', string='Verification Code',
                                    help='Redundancy check to verify the vat number has been typed in correctly.')

    payment_type = fields.Selection(string='Payment Type', selection=[('1', 'Cash'), ('2', 'Credit')], default='1')

    # person_type = fields.Many2one('ln10_co_intello.persontype', ondelete='set null', string='Person Type')
    person_type = fields.Many2one('ln10_co_intello.diancodes', ondelete='cascade', string='Person Type',
                                  domain=[('type', '=', 'persontype')])
    # fiscal_regime = fields.Many2one('ln10_co_intello.fiscalregime', ondelete='set null', string='Fiscal Regime')
    fiscal_regime = fields.Many2one('ln10_co_intello.diancodes', ondelete='cascade', string='Fiscal Regime',
                                    domain=[('type', '=', 'fiscalregime')])
    # fiscal_responsibility = fields.Many2one('ln10_co_intello.fiscalresponsibility', ondelete='set null', string='Fiscal Responsibility')
    # fiscal_responsibility = fields.Many2many('ln10_co_intello.fiscalresponsibility', column1='partner_id', column2='id', ondelete='set null', string='Fiscal Responsibility', domain="[('active', '=', True)]")
    fiscal_responsibility = fields.Many2many('ln10_co_intello.diancodes', relation='model_fiscal', column1='partner_id',
                                             column2='id', ondelete='cascade', string='Fiscal Responsibility',
                                             domain=[('type', '=', 'fiscalresponsibility')])
    payment_method = fields.Many2many('ln10_co_intello.diancodes', relation='model_payment', column1='partner_id',
                                      column2='id', ondelete='cascade', string='Payment Method',
                                      domain=[('type', '=', 'paymentmethod')])

    commercial_registration = fields.Char(string="Commercial Registration")
    code_ciiu_primary = fields.Many2one('ln10_co_intello.ciiucodes', ondelete='cascade', string='Primary CIIU Code',
                                        domain="[('industry_id', '=?', industry_id)]")
    code_ciiu_secondary = fields.Many2many('ln10_co_intello.ciiucodes', column1='partner_id', column2='id',
                                           ondelete='cascade', string='Secondary CIIU Code')
    state_is_set = fields.Boolean(default=False)

    def _vat_with_code(self):
        if self.verification_code and self.vat:
            vat = self.vat + " - " + self.verification_code
            return vat

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

    @api.onchange('vat')
    def _compute_verification_codes(self):
        multiplication_factors = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]

        # for partner in self.filtered(lambda partner: partner.vat and partner.country_id == self.env.ref('base.co') and
        #                              len(partner.vat) <= len(multiplication_factors)):

        for partner in self:
            if partner.vat and partner.vat != '':
                if len(partner.vat) <= len(multiplication_factors):
                    number = 0
                    padded_vat = partner.vat

                    while len(padded_vat) < len(multiplication_factors):
                        padded_vat = '0' + padded_vat

                    # if there is a single non-integer in vat the verification code should be False
                    try:
                        for index, vat_number in enumerate(padded_vat):
                            number += int(vat_number) * multiplication_factors[index]

                        number %= 11

                        if number < 2:
                            partner.verification_code = number
                        else:
                            partner.verification_code = 11 - number
                    except ValueError:
                        partner.verification_code = ' '
            else:
                partner.verification_code = ' '

    @api.constrains('document_type', 'vat', 'verification_code')
    def _check_document_type_with_digit_and_digit(self):
        for partner in self:
            if partner.document_type.with_digit:
                if partner.verification_code.strip() == '':
                    raise exceptions.ValidationError(
                        "The VAT number is not correct, verification code couldn't be calculated")

    def _validate_mail(self):
        if self.email:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email)
            if match == None:
                raise exceptions.ValidationError(
                    'Not a valid E-mail, is not the correct structure like something@example.com')

    @api.onchange('email')
    def validate_mail(self):
        self._validate_mail()

    @api.constrains('email')
    def _check_valid_mail(self):
        self._validate_mail()

    _sql_constraints = [
        ('document_type_number_uniq', 'UNIQUE(document_type,vat)', 'Duplicate Document Type and VAT is not allowed!')]

    # ,'name_document_number_uniq', 'UNIQUE(name,vat)', 'Duplicate Name and VAT is not allowed!']

    @api.constrains('code_ciiu_primary', 'code_ciiu_secondary')
    def _check_ciiu_primary_not_in_secondary(self):
        for r in self:
            if r.code_ciiu_primary and r.code_ciiu_primary in r.code_ciiu_secondary:
                raise exceptions.ValidationError("Primary CIIU Code can't be a Secondary Activity Code")

    @api.onchange('industry_id')
    def _onchange_industry_id(self):
        if self.industry_id and self.industry_id != self.code_ciiu_primary.industry_id:
            self.code_ciiu_primary = False

    @api.onchange('code_ciiu_primary')
    def _onchange_primary_ciiu(self):
        if self.code_ciiu_primary.industry_id:
            self.industry_id = self.code_ciiu_primary.industry_id

    @api.onchange('state_id')
    def _change_domain_state(self):
        domain = {'city_id': []}
        if not self.state_id:
            pass
        else:
            domain = {'city_id': [('country_id', '=', self.country_id.id), ('state_id', '=', self.state_id.id)]}
        return {'domain': domain}

    @api.model
    def _fields_view_get_address(self, arch):
        arch = super(Partner, self)._fields_view_get_address(arch)
        # render the partner address accordingly to address_view_id
        doc = etree.fromstring(arch)
        # if doc.xpath("//field[@name='city_id']"):
        #    return arch

        replacement_xml = """
            <div>
                <field name='city' placeholder="%(placeholder)s" class="o_address_city"
                    attrs="{
                        'invisible': [('country_enforce_cities', '=', True)],
                        'readonly': [('type', '=', 'contact')%(parent_condition)s]
                    }"
                />
            </div>
        """
        replacement_xml_city_id = """
                    <div>
                        <field name='city_id' placeholder="%(placeholder)s" string="%(placeholder)s" class="o_address_city"
                            context="{'default_country_id': country_id,
                                      'default_name': city,
                                      'default_zipcode': zip,
                                      'default_state_id': state_id}"
                            domain="[('country_id','=',country_id)]"
                            attrs="{
                                'invisible': [('country_enforce_cities', '=', False)],
                                'readonly': [('type', '=', 'contact')%(parent_condition)s]
                            }"
                        />
                    </div>
                """

        replacement_data = {
            'placeholder': _('City'),
        }

        def _arch_location(node):
            in_subview = False
            view_type = False
            parent = node.getparent()
            while parent is not None and (not view_type or not in_subview):
                if parent.tag == 'field':
                    in_subview = True
                elif parent.tag in ['list', 'tree', 'kanban', 'form']:
                    view_type = parent.tag
                parent = parent.getparent()
            return {
                'view_type': view_type,
                'in_subview': in_subview,
            }

        for city_node in doc.xpath("//field[@name='city']"):
            location = _arch_location(city_node)
            replacement_data['parent_condition'] = ''
            if location['view_type'] == 'form' or not location['in_subview']:
                replacement_data['parent_condition'] = ", ('parent_id', '!=', False)"

            replacement_formatted = replacement_xml % replacement_data
            for replace_node in etree.fromstring(replacement_formatted).getchildren():
                city_node.addprevious(replace_node)
            parent = city_node.getparent()
            parent.remove(city_node)

        for city_node in doc.xpath("//field[@name='city_id']"):
            location = _arch_location(city_node)
            replacement_data['parent_condition'] = ''
            if location['view_type'] == 'form' or not location['in_subview']:
                replacement_data['parent_condition'] = ", ('parent_id', '!=', False)"

            replacement_formatted = replacement_xml_city_id % replacement_data
            for replace_node in etree.fromstring(replacement_formatted).getchildren():
                city_node.addprevious(replace_node)
            parent = city_node.getparent()
            parent.remove(city_node)

        arch = etree.tostring(doc, encoding='unicode')
        return arch

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
            self.state_is_set = False

        if self.state_id and self.state_id != self.city_id.state_id:
            self.city_id = False
            self.city = ''
            self.zip = ''
            self.state_is_set = False

        if self.state_id:
            self.state_is_set = True

            if self.state_id.country_id:
                self.country_id = self.state_id.country_id

    @api.model
    def _filter_customer(self):
        action = self.env.ref("crm.quick_create_opportunity_form")

        print(action.partner_id)

    def validate_fields_invoice(self):
        if self.property_account_position_id and self.person_type and self.fiscal_regime and self.fiscal_responsibility and self.commercial_registration and self.industry_id and self.code_ciiu_primary and self.code_ciiu_secondary:
            pass
        else:
            raise exceptions.Warning("Compruebe los siguientes campos")

    @api.constrains('fiscal_responsibility')
    @api.onchange('fiscal_responsibility')
    def validate_responsibility_fiscal(self):
        """
        Metodo que validad, si tiene seleccionada la responsabilidad fiscal "No responsable de IVA", no pueda
        tener ninguna otra; pero si tiene otra diferente a la mencionada pueda agrgar mas.
        @author Julián Valdés - Intello Idea
        """
        if len(self.fiscal_responsibility) > 1:
            for responsibility in self.fiscal_responsibility:
                if responsibility.key_dian == "R-99-PN":
                    raise exceptions.ValidationError(_(
                        'The company has the fiscal responsibility "Not responsible for IVA", therefore it cannot have more.'))


class PartnerQuota(models.Model):
    _inherit = 'res.partner'

    extra_quota_client_spent = fields.Float(string="Extra quota client spent", readonly="1",
                                            compute='_compute_extra_quota_client_spent')
    quota_client_spent = fields.Float(string='Quota client spent', readonly="1", compute='_compute_quota_client_spent')
    quota_total = fields.Float(string='Quota total', compute="_validation")
    quota_total_remaining = fields.Float(string="Quota total remaining", compute='_compute_remaining')

    @api.depends('quota_client', "extra_quota_client")
    def _validation(self):
        self.quota_total = self.quota_client + self.extra_quota_client

    def _compute_quota_client_spent(self):
        self.env.cr.execute("""
                SELECT SUM(u.total)
                FROM (
                 SELECT so.amount_total as total
                 FROM sale_order so
                 WHERE so.company_id = %s
                   AND so.state IN ('sale')
                   AND so.partner_id = %s
                   AND NOT EXISTS(
                         SELECT 1
                         FROM account_move am
                         WHERE AM.company_id = so.company_id
                           AND AM.invoice_origin = so."name"
                     )

                 UNION ALL

                 SELECT am.amount_residual as total
                 FROM account_move am
                 WHERE am.company_id = %s
                   AND am.type IN ('out_invoice')
                   AND am.amount_residual > 0
                   AND am.partner_id = %s
                   AND am.state NOT IN ('cancel')
             ) u""", (self.env.company.id, self.id, self.env.company.id, self.id))
        amount_total_spent = self.env.cr.fetchall()

        for amount_total in amount_total_spent:
            self.quota_client_spent = amount_total[0]

    def _compute_extra_quota_client_spent(self):
        print("extra_quota_client_spent")
        sales = self.env["account.move"].search(
            ['|', ("partner_id", "=", self.id), ('type', '=', 'out_invoice'), ('state', '=', 'posted')])
        amount_total = 0

        extra_quota_client = None
        for sale in sales:
            print(sale.amount_total)
            amount_total = amount_total + sale.amount_total

        if amount_total <= self.quota_client:
            self.update({
                'extra_quota_client_spent': 0
            })
            extra_quota_client = 0
        else:
            if amount_total <= self.quota_client + self.extra_quota_client:
                self.update({
                    'extra_quota_client_spent': (amount_total - self.quota_client)
                })
                extra_quota_client = (amount_total - self.quota_client)

        self.extra_quota_client_spent = extra_quota_client

    def _compute_remaining(self):
        print("_compute_remaining")
        self.quota_total_remaining = self.quota_total - (self.quota_client_spent + self.extra_quota_client_spent)

    @api.model
    def default_get(self, fields):
        print("default_get")
        res = super(Partner, self).default_get(fields)

        sales = self.env["account.move"].search(
            ['|', ("partner_id", "=", self.id), ('type', '=', 'out_invoice'), ('state', '=', 'posted')])
        amount_total = 0
        quota_client = None
        extra_quota_client = None
        for sale in sales:
            print(sale.amount_total)
            amount_total = amount_total + sale.amount_total

        if amount_total <= self.quota_client:
            self.update({
                'quota_client_spent': amount_total,
                'extra_quota_client_spent': 0
            })
            quota_client = amount_total
            extra_quota_client = 0
        else:
            if amount_total <= self.quota_client + self.extra_quota_client:
                self.update({
                    'quota_client_spent': self.quota_client,
                    'extra_quota_client_spent': (amount_total - self.quota_client)
                })
                quota_client = self.quota_client
                extra_quota_client = (amount_total - self.quota_client)

        res.update({'quota_client_spent': quota_client,
                    'extra_quota_client_spent': extra_quota_client})
        return res
