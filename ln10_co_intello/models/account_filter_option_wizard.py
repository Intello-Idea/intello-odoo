# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ReportAccountWizard(models.TransientModel):
    _inherit = 'report.account.auxiliary.wizard'

    @api.model
    def book_principal(self):
        return self.env['accounting.book'].search([('book_principal', '=', True)])

    is_multi_book = fields.Boolean()
    book_id = fields.Many2one("accounting.book", string="Book", default=book_principal)

    @api.model
    def default_get(self, fields):

        res = super(ReportAccountWizard, self).default_get(fields)
        books = self.env["accounting.book"].search([])
        try:
            select_type = self.env['ir.config_parameter'].sudo().search([])
            sell = select_type.get_param('res.config.settings.multi_book')
            res.update({'is_multi_book': sell})
            return res
        except:
            print("No existe el campo multi book")
