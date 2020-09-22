# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Book(models.Model):
    _name = 'accounting.book'
    _description = 'accounting book for location colombia'

    name = fields.Char(string="Name", required=True)
    id_book = fields.Integer(string="ID Book", required=True)
    initials = fields.Char(string="Initials", required=True, size=3)
    book_principal = fields.Boolean(default=False)
    detail = fields.One2many('multi.book.account', 'book')
    detail_own_accounts = fields.One2many('own.accounts', 'book')
    month_block = fields.One2many('account.month.block', 'book')

    _sql_constraints = [
        ('id book Unique', 'UNIQUE(id_book)', "you can't have two books with the same id!"),
        ('id book Initials', 'UNIQUE(initials)', "you can't have two books with the same initials!")]

    @api.onchange('book_principal')
    def _change_detail(self):
        self.detail = None
        self.detail_own_accounts = None

    @api.model
    def create(self, vals):
        principal = self.env['accounting.book'].search([('book_principal', '=', True)])

        if self.book_principal and principal:
            raise ValidationError("Solo puedes tener un libro principal")
        else:
            book = super(Book, self).create(vals)
            self.create_menus(book)
            return book

    def write(self, vals):
        principal = self.env['accounting.book'].search([('book_principal', '=', True)])

        if "book_principal" in vals:
            book_principal = vals["book_principal"]
        else:
            book_principal = self.book_principal

        if principal and book_principal and (principal.id != self.id):
            raise ValidationError("Solo puedes tener un libro principal")
        else:
            old_book_name = self.name
            book = super(Book, self).write(vals)
            self.write_menus(self.name, old_book_name)
            return book

    def unlink(self):
        old_book_name = self.name
        book_id = self.id
        unlink_book = super(Book, self).unlink()
        self.unlink_menus(old_book_name, book_id)
        return {'type': 'ir.actions.client', 'tag': 'reload', }

    def reload(self):

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.onchange('detail', 'detail_own_accounts')
    def _bok_duplicate(self):
        detail = self.detail
        detail_own = self.detail_own_accounts
        for d in detail:
            for do in detail_own:
                if d == do:
                    raise ValidationError("No puedes seleccionar cuentas que ya es una cuenta base")

    def create_menus(self, book):
        select_type = self.env['ir.config_parameter'].sudo()
        check = select_type.get_param('res.config.settings.multi_book')

        parent_move = self.env.ref("ln10_co_intello.menu_journal_entries")
        parent_move_line = self.env.ref("ln10_co_intello.menu_journal_item")

        if book:
            action_move = self.env['ir.actions.act_window'].create({
                "id": "action_move_" + str(book.id),
                "name": book.name,
                "res_model": "account.move",
                "view_mode": "tree,kanban,form",
                "context": "{'book_default':" + str(book.id) + "}",
                "domain": "[('book.name', '='," + "'" + book.name + "'" + ")]",
                "view_id": self.env.ref("account.view_move_tree").id,
            })
            action_move_line = self.env['ir.actions.act_window'].create({
                "id": "action_move_line_" + str(book.id),
                "name": book.name,
                "context": "{'journal_type':'general', 'search_default_posted':1}",
                "res_model": "account.move.line",
                "view_mode": "tree,pivot,graph,form,kanban",
                "domain": "[('move_id.book.name', '='," + "'" + book.name + "'" + "), ('display_type', 'not in', ('line_section', 'line_note'))]",
                "view_id": self.env.ref("account.view_move_line_tree").id,
            })

            menu_item_move = self.env['ir.ui.menu'].create({
                "id": "menu_move_" + str(book.id),
                "name": book.name,
                "sequence": book.id_book,
                "parent_id": None,
                "action": None
            })
            menu_item_move_line = self.env['ir.ui.menu'].create({
                "id": "menu_move_line_" + str(book.id),
                "name": book.name,
                "sequence": book.id_book,
                "parent_id": None,
                "action": None
            })

            menu_item_move.parent_id = parent_move.id
            menu_item_move_line.parent_id = parent_move_line.id

            if check:
                menu_item_move.action = action_move
                menu_item_move_line.action = action_move_line

            self.link_book_menu_action(book, menu_item_move, action_move)
            self.link_book_menu_action(book, menu_item_move_line, action_move_line)

    def write_menus(self, book_name, old_book_name):

        action = self.env['ir.actions.act_window'].search([('name', '=', old_book_name)])
        for act in action:
            if act.res_model == "account.move.line":
                domain = "[('move_id.book.name', '='," + "'" + book_name + "'" + "), ('display_type', 'not in', ('line_section', 'line_note'))]"
            else:
                domain = "[('book.name', '='," + "'" + book_name + "'" + ")]"

            act.update({
                "name": book_name,
                "domain": domain
            })

        menu_item = self.env['ir.ui.menu'].search([('name', '=', old_book_name)])
        for menu in menu_item:
            menu.update({
                "name": book_name,
                "sequence": self.id_book,
            })

    def unlink_menus(self, old_book_name, book):

        action = self.env['ir.actions.act_window'].search([('name', '=', old_book_name)])
        action.unlink()

        menu_item = self.env['ir.ui.menu'].search([('name', '=', old_book_name)])
        menu_item.unlink()

        account = self.env["account.book.menu"].search([('book_id', '=', book)])
        account.unlink()

    def link_book_menu_action(self, book, menu, action):
        self.env["account.book.menu"].create({
            "book_id": book.id,
            "id_book": book.id,
            "menu_item_id": menu.id,
            "action_id": action.id,
        })


class AccountBookMenu(models.Model):
    _name = "account.book.menu"
    _description = "Menu and action for accounting book"

    book_id = fields.Integer()
    id_book = fields.Many2one('accounting.book')
    menu_item_id = fields.Many2one('ir.ui.menu')
    action_id = fields.Many2one('ir.actions.act_window')


class MultiBookAccounting(models.Model):
    _name = "multi.book.account"
    _description = "Multi Book Accounting"

    book = fields.Many2one('accounting.book', string="Book", domain="[('book_principal', '=', False)]")

    year = fields.Integer(string="Year")
    count_account_base = fields.Many2one('account.account', string="Count account Base")
    count_approved_account = fields.Many2one('account.account', string="Count account approved")

    _sql_constraints = [
        ('id count account base', 'UNIQUE(count_account_base)', "you can't have two books with the same initials!")]

    @api.constrains('year')
    def _constraint_year(self):
        if self.year < 2000:
            raise ValidationError("El año debe ser mayor a 2000")

    @api.constrains('count_account_base', 'count_approved_account')
    def _constraint_account(self):
        if self.count_account_base == self.count_approved_account:
            raise ValidationError("Las cuenta base " + str(self.count_account_base.code) +
                                  " no puede ser igual a la cuenta homologa " + str(self.count_approved_account.code))

    @api.onchange('count_account_base')
    def _repeat_count_approved(self):
        books = self.env['own.accounts'].search([])
        for lib in books.accounting_account:
            if self.count_account_base.code == lib.code:
                raise ValidationError("No puedes seleccionar cuentas propias")


class OwnAccounts(models.Model):
    _name = "own.accounts"
    _description = "Own Accounts"

    book = fields.Many2one('accounting.book', string="Book")
    accounting_account = fields.Many2one('account.account', string="Own Account")

    _sql_constraints = [
        ('id book Detail_own', 'UNIQUE(accounting_account)', "This own account is already being used by another book")]

    @api.onchange('accounting_account')
    def _repeat_book(self):
        books = self.env['multi.book.account'].search([])
        for lib in books.count_account_base:
            if self.accounting_account.code == lib.code:
                raise ValidationError("No puedes seleccionar cuentas que ya es una cuenta base")
        for lib_2 in books.count_approved_account:
            if self.accounting_account.code == lib_2.code:
                raise ValidationError("No puedes seleccionar cuentas que ya es una cuenta homologada")
