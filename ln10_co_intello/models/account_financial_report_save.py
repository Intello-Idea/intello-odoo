from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountFinancialReportSave(models.Model):
    _name = "account.financial.report.save"
    _description = "save all menu item and actions of account financial"

    menu_id = fields.Many2one("ir.ui.menu")
    action_client = fields.Many2one("ir.actions.client")
    action_window = fields.Many2one("ir.actions.act_window")
