# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo import exceptions


class ReportAccountWizard(models.TransientModel):
    _name = 'report.account.auxiliary.wizard'
    _description = 'Report Account Wizard'

    # book_id = fields.Many2one(comodel_name="accouting.book", string="Book")

    accounts = fields.Selection([('se', "Select all"), ('cs', 'Customize selection')], string="Accounts to render",
                                default="se")
    accounts_value = fields.Many2many(comodel_name="account.account", string="Accounts value", ondelete='cascade')
    time_frame = fields.Selection(
        [('tm', "This month"), ('tq', 'This quarter'), ('ty', 'This financial year'), ('lm', "Last month"),
         ('lq', 'Last quarter'), ('ly', 'Last financial year'), ('co', 'Custom')], string="Time Frame", default="tm")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    analytical_account = fields.Selection(
        [('0', "don't show"), ('1', 'Unfold 1'), ('2', 'Unfold 2'), ('3', 'Unfold 3')], string="Analytical account",
        default="0")
    analytical_account_value = fields.Many2many(comodel_name="account.analytic.account",
                                                string="Analytical Account Value", ondelete='cascade')
    associated = fields.Selection([('0', "don't show"), ('1', 'Unfold 1'), ('2', 'Unfold 2'), ('3', 'Unfold 3')],
                                  string="Analytical associated", default="0")
    associated_value = fields.Many2many(comodel_name="res.partner", string="Analytical associated value",
                                        ondelete='cascade')
    analytical_tag = fields.Selection([('0', "don't show"), ('1', 'Unfold 1'), ('2', 'Unfold 2'), ('3', 'Unfold 3')],
                                      string="Analytical tag", default="0")
    analytical_tag_value = fields.Many2many(comodel_name="account.analytic.tag", string="Analytical tag value",
                                            ondelete='cascade')
    all = fields.Boolean(string='Accounts with balance greater than 0', default=True)


class ReportAccountWizard(models.TransientModel):
    _inherit = 'report.account.auxiliary.wizard'

    load_data_account = fields.Boolean(string="Load data")
    load_data_associated = fields.Boolean(string="Load data")
    load_data_tag = fields.Boolean(string="Load data")

    @api.onchange('load_data_account')
    def _load_data_account(self):
        if self.load_data_account:
            account_move_line_account = self.env["account.move.line"].search([("move_id.state","=","posted")]).analytic_account_id
            list_no_repeat = set(account_move_line_account)
            self.analytical_account_value = account_move_line_account
        else:
            self.analytical_account_value = ()

    @api.onchange('load_data_associated')
    def _load_data_associated(self):
        if self.load_data_associated:
            account_move_line_associated = self.env["account.move.line"].search([("move_id.state","=","posted")]).partner_id
            self.associated_value = account_move_line_associated
        else:
            self.associated_value = ()


    @api.onchange('load_data_tag')
    def _load_data_tag(self):
        if self.load_data_tag:
            account_move_line_tag = self.env["account.move.line"].search([("move_id.state","=","posted")]).analytic_tag_ids
            self.analytical_tag_value = account_move_line_tag
        else:
            self.analytical_tag_value = ()

    @api.onchange('analytical_account')
    def _value_load_data_account(self):
        if self.analytical_account == '0':
            self.load_data_account = False
        else:
            if self.analytical_account == self.associated:
                self.associated = "0"
            else:
                if self.analytical_account == self.analytical_tag:
                    self.analytical_tag = "0"

    @api.onchange('associated')
    def _value_load_data_associated(self):
        if self.associated == '0':
            self.load_data_associated = False
        else:
            if self.associated == self.analytical_tag:
                self.analytical_tag = "0"
            else:
                if self.associated == self.analytical_account:
                    self.analytical_account = "0"


    @api.onchange('analytical_tag')
    def _value_load_data_analytical_tag(self):
        if self.analytical_tag == '0':
            self.load_data_tag = False
        else:
            if self.analytical_tag == self.associated:
                self.associated = "0"
            else:
                if self.analytical_tag == self.analytical_account:
                    self.analytical_account = "0"



