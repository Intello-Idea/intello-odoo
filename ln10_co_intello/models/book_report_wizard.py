from odoo import fields, models, api, exceptions
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class BookReportWizard(models.TransientModel):
    _name = "book.report.wizard"
    _description = "report for books"

    @api.model
    def book_principal(self):
        principal_book = self.env['accounting.book'].search([('book_principal', '=', True)])
        if not principal_book:
            raise exceptions.UserError("No existe un Libro principal.")
        else:
            return principal_book
    
    book_id = fields.Many2one("accounting.book", string="Book", default=book_principal)
