from odoo import fields, models, api, exceptions
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class AccountAuxiliaryReport(models.AbstractModel):
    _inherit = "account.auxiliary.report"

    @api.model
    def _get_lines(self, options, line_id=None):
        book_w = self.env['report.account.auxiliary.wizard'].search([])[-1]
        options["book_id"] = book_w.book_id.id

        global selected_book
        selected_book = book_w.book_id.id
        global book_principal
        book_principal = self.env['accounting.book'].search([('book_principal', '=', True)]).id

        lines = super(AccountAuxiliaryReport, self)._get_lines(options, line_id)
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
