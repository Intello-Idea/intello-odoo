from odoo import fields, models, api, exceptions
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    selected_book = 0
    book_principal = 0

    @api.model
    def _get_options_domain(self, options):
        domain = []
        global selected_book
        global book_principal

        model = self

        principal_book = self.env['accounting.book'].search([('book_principal', '=', True)])
        if not principal_book:
            raise exceptions.UserError("No existe un Libro principal.")

        parameter = self.env['ir.config_parameter'].sudo()
        multibook = parameter.get_param('res.config.settings.multi_book')
        if multibook and self.report_is_multibook(model):
            book_w = self.env['book.report.wizard'].search([])[-1]
            domain = super(AccountReport, self)._get_options_domain(options)
            domain += [("move_id.book.id", "=", book_w.book_id.id)]

            selected_book = book_w.book_id.id
            book_principal = principal_book.id
        else:
            domain = super(AccountReport, self)._get_options_domain(options)
            domain += [("move_id.book.id", "=", principal_book.id)]

            selected_book = principal_book.id
            book_principal = principal_book.id

        return domain

    @api.model
    def _get_options(self, previous_options=None):
        # name = self.name
        global selected_book
        global book_principal

        model = self

        principal_book = self.env['accounting.book'].search([('book_principal', '=', True)])
        if not principal_book:
            raise exceptions.UserError("No existe un Libro principal.")

        parameter = self.env['ir.config_parameter'].sudo()
        multibook = parameter.get_param('res.config.settings.multi_book')
        if multibook and self.report_is_multibook(model) and (model != self.env['account.auxiliary.report']):
            book_w = self.env['book.report.wizard'].search([])[-1]
            rslt = super(AccountReport, self)._get_options(previous_options)
            rslt["book_id"] = book_w.book_id.id

            selected_book = book_w.book_id.id
            book_principal = principal_book.id
        else:
            rslt = super(AccountReport, self)._get_options(previous_options)
            rslt["book_id"] = principal_book.id

            selected_book = principal_book.id
            book_principal = principal_book.id

        return rslt

    def report_is_multibook(self, model):
        report_mul_book = []
        report_mul_book.append(self.env["account.financial.html.report"])
        report_mul_book.append(self.env["account.partner.ledger"])
        report_mul_book.append(self.env["account.general.ledger"])
        report_mul_book.append(self.env["account.coa.report"])
        report_mul_book.append(self.env["account.consolidated.journal"])
        report_mul_book.append(self.env["account.auxiliary.report"])

        for repo in report_mul_book:
            if type(repo) == type(model):
                return True
        return False


class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = "account.general.ledger"

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = super(AccountGeneralLedgerReport, self)._get_lines(options, line_id)
        for line in lines:
            line.update({
                'name': self.book_and_name(line['name'].split(" ", )[0], line['name']),
                'title_hover': self.book_and_name(line['name'].split(" ", )[0], line['name']),
            })
        return lines

    def book_and_name(self, code, name):

        if selected_book != 0 and (selected_book != book_principal):
            account = self.env['account.account'].search(
                [('code', '=', code)])
            if account:
                account_name = self.env['book.account.name'].search(
                    [('book.id', '=', selected_book), ('account_id', '=', account.id)])
                if account_name:
                    name = code + " " + account_name.name

        return name


class AccountChartOfAccountReport(models.AbstractModel):
    _inherit = "account.coa.report"

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = super(AccountChartOfAccountReport, self)._get_lines(options, line_id)
        for line in lines:
            line.update({
                'name': self.book_and_name(line['name'].split(" ", )[0], line['name']),
                'title_hover': self.book_and_name(line['name'].split(" ", )[0], line['name']),
            })
        return lines

    def book_and_name(self, code, name):

        if selected_book != 0 and (selected_book != book_principal):
            account = self.env['account.account'].search(
                [('code', '=', code)])
            if account:
                account_name = self.env['book.account.name'].search(
                    [('book.id', '=', selected_book), ('account_id', '=', account.id)])
                if account_name:
                    name = code + " " + account_name.name

        return name


class report_account_consolidated_journal(models.AbstractModel):
    _inherit = "account.consolidated.journal"

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = super(report_account_consolidated_journal, self)._get_lines(options, line_id)
        for line in lines:
            line.update({
                'name': self.book_and_name(line['name'].split(" ", )[0], line['name']),
                'title_hover': self.book_and_name(line['name'].split(" ", )[0], line['name']),
            })
        return lines

    def book_and_name(self, code, name):

        if selected_book != 0 and (selected_book != book_principal):
            account = self.env['account.account'].search(
                [('code', '=', code)])
            if account:
                account_name = self.env['book.account.name'].search(
                    [('book.id', '=', selected_book), ('account_id', '=', account.id)])
                if account_name:
                    name = code + " " + account_name.name

        return name
