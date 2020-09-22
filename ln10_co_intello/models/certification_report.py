from odoo import fields, models, api, exceptions
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from datetime import date
from odoo import exceptions


class ReportCertificationReport(models.AbstractModel):
    _inherit = "l10n_co_reports.certification_report"

    @api.model
    def book_principal(self):
        return self.env['accounting.book'].search([('book_principal', '=', True)]).id

    def _get_domain(self, options):
        common_domain = super(ReportCertificationReport, self)._get_domain(options)
        common_domain += [('book.id', '=', self.book_principal())]
        return common_domain
