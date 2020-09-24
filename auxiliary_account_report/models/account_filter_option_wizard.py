# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ReportAccountWizard(models.TransientModel):
    _name = 'report.account.auxiliary.wizard'
    _description = 'Report Account Wizard'

    #book_id = fields.Many2one(comodel_name="accouting.book", string="Book")

    accounts = fields.Selection([('se', "Select all"), ('cs', 'Customize selection')], string="Accounts to render", default="se")
    accounts_value = fields.Many2many(comodel_name="account.account", string="Accounts value", ondelete='cascade')
    time_frame = fields.Selection([('tm', "This month"), ('tq', 'This quarter'), ('ty', 'This financial year'), ('lm', "Last month"), ('lq', 'Last quarter'), ('ly', 'Last financial year'), ('co', 'Custom')], string="Time Frame", default="tm")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    analytical_account = fields.Selection([('0', "don't show"), ('1', 'Unfold 1'), ('2', 'Unfold 2'), ('3', 'Unfold 3')], string="Analytical account", default="0")
    analytical_account_value = fields.Many2many(comodel_name="account.analytic.account", string="Analytical Account Value", ondelete='cascade')
    associated = fields.Selection([('0', "don't show"), ('1', 'Unfold 1'), ('2', 'Unfold 2'), ('3', 'Unfold 3')], string="Analytical associated", default="0")
    associated_value = fields.Many2many(comodel_name="res.partner", string="Analytical associated value", ondelete='cascade')
    analytical_tag = fields.Selection([('0', "don't show"), ('1', 'Unfold 1'), ('2', 'Unfold 2'), ('3', 'Unfold 3')], string="Analytical tag", default="0")
    analytical_tag_value = fields.Many2many(comodel_name="account.analytic.tag", string="Analytical tag value", ondelete='cascade')

