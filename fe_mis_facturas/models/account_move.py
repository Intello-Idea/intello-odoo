from odoo import api, fields, models, _, exceptions


class AccountMove(models.Model):
    _inherit = 'account.move'

    def send_document(self):
        super(AccountMove, self).send_document()
        fe_methods = self.env['fe.mf.methods']
        fe_methods.send_electronic_document(self)

    def send_gr_document(self, b64):
        fe_methods = self.env['fe.mf.methods']
        fe_methods.send_rg_electronic_document(b64, self)
        self.update_electronic_document_status(6)

