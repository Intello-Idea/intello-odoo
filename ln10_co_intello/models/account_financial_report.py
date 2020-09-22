from odoo import fields, models, api, exceptions


class AccountFinancialReportLine(models.Model):
    _inherit = 'account.financial.html.report.line'

    selected_book = 0
    book_principal = 0

    def _get_aml_domain(self):
        domain = []
        global selected_book
        global book_principal

        principal_book = self.env['accounting.book'].search([('book_principal', '=', True)])
        if not principal_book:
            raise exceptions.UserError("No existe un Libro principal.")

        parameter = self.env['ir.config_parameter'].sudo()
        multibook = parameter.get_param('res.config.settings.multi_book')
        if multibook:
            book_w = self.env['book.report.wizard'].search([])[-1]
            domain = super(AccountFinancialReportLine, self)._get_aml_domain()
            domain += [("move_id.book.id", "=", book_w.book_id.id)]

            selected_book = book_w.book_id.id
            book_principal = principal_book.id
        else:
            domain = super(AccountFinancialReportLine, self)._get_aml_domain()
            domain += [("move_id.book.id", "=", principal_book.id)]

            selected_book = principal_book.id
            book_principal = principal_book.id

        return domain

    def _get_lines(self, financial_report, currency_table, options, linesDicts):

        lines = super(AccountFinancialReportLine, self)._get_lines(financial_report, currency_table, options,
                                                                   linesDicts)
        for line in lines:
            line.update({
                'name': self.book_and_name(line['name'].split(" ", )[0], line['name']),
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
