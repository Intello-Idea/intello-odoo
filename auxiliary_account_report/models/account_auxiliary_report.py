# -*- coding: utf-8 -*-
import locale

from docutils.nodes import generated
from odoo import models, api, _, fields, exceptions
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta, date
import calendar, math
from odoo.tools.misc import xlsxwriter
import io
import locale
from operator import itemgetter
import translators as ts




from passlib.handlers.fshp import fshp


class AccountAuxiliaryReport(models.AbstractModel):
    _name = "account.auxiliary.report"
    _description = "Auxiliary Report"
    _inherit = "account.report"

    def option_wizard(self):
        if len(self.env['report.account.auxiliary.wizard'].search([])) != 0:
            return self.env['report.account.auxiliary.wizard'].search([])[-1]
        else:
            raise exceptions.ValidationError("Please try again, setting parameters")


    ####################################################################
    ####       METODOS PRINCIPALES DE LOS REPORTES DINAMICOS       #####
    ####################################################################

    @api.model
    def _get_templates(self):
        templates = super(AccountAuxiliaryReport, self)._get_templates()
        templates['line_template'] = 'account_reports.line_template_general_ledger_report'
        return templates

    @api.model
    def _get_columns_name(self, options):
        return [
            {'name': _('')},
            {'name': _('Type document')},
            {'name': _('Date'), 'class': 'date'},
            {'name': _('Type base document')},
            {'name': _('Base document number')},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'},
            {'name': _('Description')}
        ]

    @api.model
    def _get_report_name(self):
        return _("account-assistant"+str(date.today().strftime("%d-%m-%y")))

    @api.model
    def _get_lines(self, options, line_id=None):
        filter = self.option_wizard()
        accounts = self.get_data_accounts(filter)
        #print(accounts)
        range_date = self.get_date_filter(filter)
        #print(range_date)
        analytical = self.get_analytical_order(filter)
        #print(analytical)
        if 'book_id' in options.keys():
            dom = ('move_id.book.id', '=', options['book_id'])
        else:
            dom = None
        data = self.movements_according_account(range_date = range_date, account_obje = accounts, analytical_filter = analytical, domain = dom)
        lines = self.information_render_report(data, acc_all = filter.all)
        return lines

    ####################################################################
    ####                             QUERIS                        #####
    ####################################################################

    def get_data_accounts(self, opt_wizard):
        """
        method that brings all the accounts that should appear in the report
        """
        if opt_wizard.accounts == "se":
            return self.env['account.account'].search([])
        else:
            return opt_wizard.accounts_value

    def get_date_filter(self, opt_wizard):
        """
        method that returns the date range according to the filter
        """
        end_date = None
        start_date = None
        today = date.today()
        if opt_wizard.time_frame == 'tm':
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        elif opt_wizard.time_frame == 'tq':
            q=math.ceil(today.month/3.)
            if q == 1:
                start_date = date(today.year, 1, 1)
                end_date = date(today.year, 3, calendar.monthrange(today.year, 3)[1])
            elif q == 2:
                start_date = date(today.year, 4, 1)
                end_date = date(today.year, 6, calendar.monthrange(today.year, 6)[1])
            elif q == 3:
                start_date = date(today.year, 7, 1)
                end_date = date(today.year, 9, calendar.monthrange(today.year, 9)[1])
            elif q == 4:
                start_date = date(today.year, 10, 1)
                end_date = date(today.year, 12, calendar.monthrange(today.year, 12)[1])
        elif opt_wizard.time_frame == 'ty':
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, calendar.monthrange(today.year, 12)[1])
        elif opt_wizard.time_frame == 'lm':
            start_date = date(today.year, today.month-1, 1)
            end_date = date(today.year, today.month-1, calendar.monthrange(today.year, today.month-1)[1])
        elif opt_wizard.time_frame == 'lq':
            q = math.ceil(today.month / 3.)-1
            if q == 1:
                start_date = date(today.year, 1, 1)
                end_date = date(today.year, 3, calendar.monthrange(today.year, 3)[1])
            elif q == 2:
                start_date = date(today.year, 4, 1)
                end_date = date(today.year, 6, calendar.monthrange(today.year, 6)[1])
            elif q == 3:
                start_date = date(today.year, 7, 1)
                end_date = date(today.year, 9, calendar.monthrange(today.year, 9)[1])
            elif q == 4:
                start_date = date(today.year, 10, 1)
                end_date = date(today.year, 12, calendar.monthrange(today.year, 12)[1])
        elif opt_wizard.time_frame == 'ly':
            start_date = date(today.year-1, 1, 1)
            end_date = date(today.year-1, 12, calendar.monthrange(today.year-1, 12)[1])
        else:
            start_date = opt_wizard.start_date
            end_date = opt_wizard.end_date

        #print(start_date, "  -->  ", end_date)
        return [start_date, end_date]

    def get_analytical_order(self, opt_wizard):
        """
        method that fetches analytical filters and sorts them
        """
        list = [{'analytical': 'analytical_account', 'position': opt_wizard.analytical_account, 'data': opt_wizard.analytical_account_value, 'field_name': 'analytic_account_id'},
                {'analytical': 'associated', 'position': opt_wizard.associated, 'data': opt_wizard.associated_value, 'field_name': 'partner_id'},
                {'analytical': 'analytical_tag', 'position': opt_wizard.analytical_tag, 'data': opt_wizard.analytical_tag_value, 'field_name': 'analytic_tag_ids'}]
        pop = []
        for x in list:
            if int(x['position']) == 0:
                pop.append(x)
        for x in pop:
            list.remove(x)

        if len(list) == 0:
            return list
        else:
            return sorted(list, key=lambda i: i['position'])

    def movements_according_account(self, range_date, account_obje, analytical_filter, domain):
        """
        the movements to be shown in the report are compared according to the accounts
        """
        return_list = []

        list_accounts = list(account_obje)
        list_accounts.sort(key=lambda list_accounts: list_accounts.code)

        if len(analytical_filter) == 0:
            #print("Sin FIltro")
            for account in list_accounts:
                dic = {}

                domain_or = [('date', '<', range_date[0]), ('account_id', '=', account.id),('parent_state', '=', "posted")]
                domain_total = [('date', '>=', range_date[0]), ('date', '<=', range_date[1]), ('account_id', '=', account.id), ('parent_state', '=', "posted")]

                if not domain is None:
                    domain_or.append(domain)
                    domain_total.append(domain)

                initial_balance = list(self.env['account.move.line'].search(domain_or))
                list_move = list(self.env['account.move.line'].search(domain_total))
                #print(list_move)
                dic = {'number_filters': 0, 'account': account, 'move': list_move,
                       'initial_balance': self.calculate_initial_end_balance(initial_balance),
                       'total_balance': self.calculate_balance(self.calculate_initial_end_balance(initial_balance),
                                                               self.calculate_initial_end_balance(list_move))}
                return_list.append(dic)

        elif len(analytical_filter) == 1:
            #print("Filtro 1")
            list_dic = []
            for account in list_accounts:
                dic = {}
                list_detail = []
                for filter in analytical_filter[0]['data']:

                    domain_or = [('date', '<', range_date[0]), ('account_id', '=', account.id), (analytical_filter[0]['field_name'], '=', filter.id), ('parent_state', '=', "posted")]
                    domain_total = [('date', '>=', range_date[0]), ('date', '<=', range_date[1]), ('account_id', '=', account.id), (analytical_filter[0]['field_name'], '=', filter.id), ('parent_state', '=', "posted")]
                    if not domain is None:
                        domain_or.append(domain)
                        domain_total.append(domain)

                    initial_balance = list(self.env['account.move.line'].search(domain_or))
                    list_move = list(self.env['account.move.line'].search(domain_total))
                    #print(list_move)
                    dic_detail = {'filter1': filter, 'move': list_move,
                                      'initial_balance': self.calculate_initial_end_balance(initial_balance),
                                      'total_balance': self.calculate_balance(
                                          self.calculate_initial_end_balance(initial_balance),
                                          self.calculate_initial_end_balance(list_move))}
                    list_detail.append(dic_detail)


                list_bala = self.calculate_balance_group(list_detail)

                initial_balance = {'debit': list_bala[0]['debit'], 'credit': list_bala[0]['credit'], 'balance': list_bala[0]['balance']}
                total_balance = {'debit': list_bala[1]['debit'], 'credit': list_bala[1]['credit'], 'balance': list_bala[1]['balance']}

                if len(list_detail) > 0:
                    dic = {'number_filters': 1, 'account': account, 'detail': list_detail, 'initial_balance': initial_balance, 'total_balance': total_balance}
                    list_dic.append(dic)

            for i in list_dic:
                if i not in return_list:
                    return_list.append(i)

        elif len(analytical_filter) == 2:
            #print("Filtro 2")
            list_dic = []
            for account in list_accounts:
                dic = {}
                filter1_detail = []
                for filter1 in analytical_filter[0]['data']:
                    filter2_detail = []
                    for filter2 in analytical_filter[1]['data']:

                        domain_or = [('date', '<', range_date[0]), ('account_id', '=', account.id),
                             (analytical_filter[0]['field_name'], '=', filter1.id), (analytical_filter[1]['field_name'], '=', filter2.id), ('parent_state', '=', "posted")]
                        domain_total = [('date', '>=', range_date[0]), ('date', '<=', range_date[1]), ('account_id', '=', account.id),
                             (analytical_filter[0]['field_name'], '=', filter1.id), (analytical_filter[1]['field_name'], '=', filter2.id), ('parent_state', '=', "posted")]

                        if not domain is None:
                            domain_or.append(domain)

                        initial_balance = list(self.env['account.move.line'].search(domain_or))
                        list_move = list(self.env['account.move.line'].search(domain_total))

                        #print(list_move)
                        dic = {'filter2': filter2, 'move': list_move,
                               'initial_balance': self.calculate_initial_end_balance(initial_balance),
                               'total_balance': self.calculate_balance(
                                   self.calculate_initial_end_balance(initial_balance),
                                   self.calculate_initial_end_balance(list_move))}
                        filter2_detail.append(dic)

                    balance_filter_2 = self.calculate_balance_group(filter2_detail)

                    initial_balance_filter_2 = {'debit': balance_filter_2[0]['debit'],
                                                'credit': balance_filter_2[0]['credit'],
                                                'balance': balance_filter_2[0]['balance']}
                    total_balance_filter_2 = {'debit': balance_filter_2[1]['debit'],
                                              'credit': balance_filter_2[1]['credit'],
                                              'balance': balance_filter_2[1]['balance']}

                    if len(filter2_detail) > 0:
                        dic = {'filter1': filter1, 'detail': filter2_detail,
                               'initial_balance': initial_balance_filter_2, 'total_balance': total_balance_filter_2}
                        filter1_detail.append(dic)

                balance_filter_1 = self.calculate_balance_group(filter1_detail)

                initial_balance_filter_1 = {'debit': balance_filter_1[0]['debit'],
                                            'credit': balance_filter_1[0]['credit'],
                                            'balance': balance_filter_1[0]['balance']}
                total_balance_filter_1 = {'debit': balance_filter_1[1]['debit'],
                                          'credit': balance_filter_1[1]['credit'],
                                          'balance': balance_filter_1[1]['balance']}
                if len(filter1_detail) > 0:
                    dic = {'number_filters': 2, 'account': account, 'detail': filter1_detail,
                           'initial_balance': initial_balance_filter_1, 'total_balance': total_balance_filter_1}

                    list_dic.append(dic)

            for i in list_dic:
                if i not in return_list:
                    return_list.append(i)

        elif len(analytical_filter) == 3:
            #print("Filtro 3")
            list_dic = []
            for account in list_accounts:
                dic = {}
                filter1_detail = []
                for filter1 in analytical_filter[0]['data']:
                    filter2_detail = []
                    for filter2 in analytical_filter[1]['data']:
                        filter3_detail = []
                        for filter3 in analytical_filter[2]['data']:

                            domain_or = [('date', '<', range_date[0]), ('account_id', '=', account.id),
                                 (analytical_filter[0]['field_name'], '=', filter1.id), (analytical_filter[1]['field_name'], '=', filter2.id), (analytical_filter[2]['field_name'], '=', filter3.id), ('parent_state', '=', "posted")]
                            domain_total = [('date', '>=', range_date[0]), ('date', '<=', range_date[1]), ('account_id', '=', account.id),
                                 (analytical_filter[0]['field_name'], '=', filter1.id), (analytical_filter[1]['field_name'], '=', filter2.id), (analytical_filter[2]['field_name'], '=', filter3.id), ('parent_state', '=', "posted")]
                            if not domain is None:
                                domain_or.append(domain)

                            initial_balance = list(self.env['account.move.line'].search(domain_or))
                            list_move = list(self.env['account.move.line'].search(domain_total))

                            #print(list_move)
                            dic = {'filter3': filter3, 'move': list_move,
                                   'initial_balance': self.calculate_initial_end_balance(initial_balance),
                                   'total_balance': self.calculate_balance(
                                       self.calculate_initial_end_balance(initial_balance),
                                       self.calculate_initial_end_balance(list_move))}

                            filter3_detail.append(dic)

                        balance_filter_3 = self.calculate_balance_group(filter3_detail)
                        initial_balance_filter_3 = {'debit': balance_filter_3[0]['debit'],
                                                    'credit': balance_filter_3[0]['credit'],
                                                    'balance': balance_filter_3[0]['balance']}
                        total_balance_filter_3 = {'debit': balance_filter_3[1]['debit'],
                                                  'credit': balance_filter_3[1]['credit'],
                                                  'balance': balance_filter_3[1]['balance']}

                        if len(filter3_detail) > 0:
                            dic = {'filter2': filter2, 'detail': filter3_detail,
                                   'initial_balance': initial_balance_filter_3, 'total_balance': total_balance_filter_3}
                            filter2_detail.append(dic)

                    balance_filter_2 = self.calculate_balance_group(filter2_detail)
                    initial_balance_filter_2 = {'debit': balance_filter_2[0]['debit'],
                                                'credit': balance_filter_2[0]['credit'],
                                                'balance': balance_filter_2[0]['balance']}
                    total_balance_filter_2 = {'debit': balance_filter_2[1]['debit'],
                                              'credit': balance_filter_2[1]['credit'],
                                              'balance': balance_filter_2[1]['balance']}
                    if len(filter2_detail) > 0:
                        dic = {'filter1': filter1, 'detail': filter2_detail,
                               'initial_balance': initial_balance_filter_2,
                               'total_balance': total_balance_filter_2}
                        filter1_detail.append(dic)

                balance_filter_1 = self.calculate_balance_group(filter1_detail)
                initial_balance_filter_1 = {'debit': balance_filter_1[0]['debit'],
                                            'credit': balance_filter_1[0]['credit'],
                                            'balance': balance_filter_1[0]['balance']}
                total_balance_filter_1 = {'debit': balance_filter_1[1]['debit'],
                                          'credit': balance_filter_1[1]['credit'],
                                          'balance': balance_filter_1[1]['balance']}
                if len(filter1_detail) > 0:
                    dic = {'number_filters': 3, 'account': account, 'detail': filter1_detail,
                           'initial_balance': initial_balance_filter_1, 'total_balance': total_balance_filter_1}

                    list_dic.append(dic)

            for i in list_dic:
                if i not in return_list:
                    return_list.append(i)

        #print(return_list, "\n ============================================ \n")

        return return_list

    def calculate_initial_end_balance(self, list_move):
        debit = 0
        credit = 0
        balance = 0
        for x in range(len(list_move)):
            debit += list_move[x].debit
            credit += list_move[x].credit
            balance += list_move[x].balance
        return {'debit': debit, 'credit': credit, 'balance': balance}

    def calculate_balance(self, initial, total):
        debit = initial['debit']+total['debit']
        credit = initial['credit']+total['credit']
        balance = initial['balance']+total['balance']
        return {'debit': debit, 'credit': credit, 'balance': balance}

    def calculate_balance_group(self, list_detail):
        debit_balance = 0
        debit_total = 0
        credit_balance = 0
        credit_total = 0
        balance_balance = 0
        balance_total = 0
        for detail in list_detail:
            debit_balance += detail['initial_balance']['debit']
            credit_balance += detail['initial_balance']['credit']
            balance_balance += detail['initial_balance']['balance']
            debit_total += detail['total_balance']['debit']
            credit_total += detail['total_balance']['credit']
            balance_total += detail['total_balance']['balance']

        return [{'debit': debit_balance, 'credit': credit_balance, 'balance': balance_balance}, {'debit': debit_total, 'credit': credit_total, 'balance': balance_total}]

    def information_render_report(self, data, acc_all):
        return_list = []

        if data[0]['number_filters'] == 0:
            count = 0
            if acc_all:
                for line in data:
                    if line['total_balance']['balance'] != 0:
                        print("entro")
                        count += 1
                        dic_head = {'id': "head"+str(line['account'].id),
                               'name': str(line['account'].code) +" "+ str(line['account'].name if len(line['account'].name) < 14 else  line['account'].name[:11]+"..."), 'level': 2,
                               'title_hover': str(line['account'].code) +" "+ str(line['account'].name), 'style': 'background: #b8b5ff; font-weight: bold;',
                               'columns': [{'name': '', 'class': 'number'},
                                           {'name': self.format_value(float(line['total_balance']['debit'])), 'class': 'number'},
                                           {'name': self.format_value(float(line['total_balance']['credit'])), 'class': 'number'},
                                           {'name': self.format_value(float(line['total_balance']['balance'])), 'class': 'number'},
                                           {'name': '', 'class': 'number'}],
                               'unfoldable': True, 'unfolded': False, 'colspan': 4}
                        return_list.append(dic_head)
                        return_list.append({'id': 'initial_' + str(count), 'level':3,
                                            'name': 'Initial Balance', 'style': 'font-weight: bold;',
                                            'parent_id': dic_head['id'],
                                            'columns': [{'name': '', 'class': 'number'}, {'name': self.format_value(line['initial_balance']['debit']), 'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['credit']), 'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['balance']), 'class': 'number'},
                                                        {'name': ''}],
                                            'colspan': 4})
                        for move in line['move']:
                            dic_move = {'id': move.id, 'caret_options': 'account.move', 'class': 'top-vertical-align',
                                        'level': 4, 'name': str(move.move_name),
                                        'columns': [{'name': str(move.journal_id.name)}, {'name': str(move.date), 'class': 'date'},
                                                    {'name': str(move.move_id.reversed_entry_id.journal_id.name if move.move_id.reversed_entry_id.journal_id.name != False else "")},
                                                    {'name': str(move.move_id.reversed_entry_id.name if move.move_id.reversed_entry_id.name != False else "")},
                                                    {'name': self.format_value(float(move.debit)), 'class': 'number'},
                                                    {'name': self.format_value(float(move.credit)), 'class': 'number'},
                                                    {'name': self.format_value(float(move.balance)), 'class': 'number'},
                                                    {'name': str(move.ref), 'class': 'whitespace_#print'}],
                                        'parent_id': dic_head['id']}

                            return_list.append(dic_move)
                        return_list.append({'id': 'totals_' + str(count), 'level': 3, 'name': 'Total',
                                             'style': 'background: #b8b5ff; font-weight: bold;', 'parent_id': dic_head['id'],
                                             'columns': [{'name': '', 'class': 'number'},
                                                         {'name': self.format_value(line['total_balance']['debit']), 'class': 'number'},
                                                         {'name': self.format_value(line['total_balance']['credit']), 'class': 'number'},
                                                         {'name': self.format_value(line['total_balance']['balance']), 'class': 'number'}, {'name': ''}],
                                             'colspan': 4})
            else:
                for line in data:
                    count += 1
                    dic_head = {'id': "head" + str(line['account'].id),
                                'name': str(line['account'].code) + " " + str(
                                    line['account'].name if len(line['account'].name) < 14 else line['account'].name[
                                                                                                :11] + "..."),
                                'level': 2,
                                'title_hover': str(line['account'].code) + " " + str(line['account'].name),
                                'style': 'background: #b8b5ff; font-weight: bold;',
                                'columns': [{'name': '', 'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['debit'])),
                                             'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['credit'])),
                                             'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['balance'])),
                                             'class': 'number'},
                                            {'name': '', 'class': 'number'}],
                                'unfoldable': True, 'unfolded': False, 'colspan': 4}
                    return_list.append(dic_head)
                    return_list.append({'id': 'initial_' + str(count), 'level': 3,
                                        'name': 'Initial Balance', 'style': 'font-weight: bold;',
                                        'parent_id': dic_head['id'],
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['debit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['credit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['balance']),
                                                     'class': 'number'},
                                                    {'name': ''}],
                                        'colspan': 4})
                    for move in line['move']:
                        dic_move = {'id': move.id, 'caret_options': 'account.move', 'class': 'top-vertical-align',
                                    'level': 4, 'name': str(move.move_name),
                                    'columns': [{'name': str(move.journal_id.name)},
                                                {'name': str(move.date), 'class': 'date'},
                                                {'name': str(
                                                    move.move_id.reversed_entry_id.journal_id.name if move.move_id.reversed_entry_id.journal_id.name != False else "")},
                                                {'name': str(
                                                    move.move_id.reversed_entry_id.name if move.move_id.reversed_entry_id.name != False else "")},
                                                {'name': self.format_value(float(move.debit)), 'class': 'number'},
                                                {'name': self.format_value(float(move.credit)), 'class': 'number'},
                                                {'name': self.format_value(float(move.balance)), 'class': 'number'},
                                                {'name': str(move.ref), 'class': 'whitespace_#print'}],
                                    'parent_id': dic_head['id']}

                        return_list.append(dic_move)
                    return_list.append({'id': 'totals_' + str(count), 'level': 3, 'name': 'Total',
                                        'style': 'background: #b8b5ff; font-weight: bold;', 'parent_id': dic_head['id'],
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(line['total_balance']['debit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['total_balance']['credit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['total_balance']['balance']),
                                                     'class': 'number'}, {'name': ''}],
                                        'colspan': 4})

        elif data[0]['number_filters'] == 1:

            count = 0
            if acc_all:
                for line in data:
                    if line['total_balance']['balance'] != 0:
                        count += 1
                        dic_head = {'id': "head" + str(line['account'].id),
                                    'name': str(line['account'].code) + " " + str(
                                        line['account'].name if len(line['account'].name) < 14 else line['account'].name[
                                                                                                    :11] + "..."), 'level': 2,
                                    'title_hover': str(line['account'].code) + " " + str(line['account'].name),
                                    'style': 'background:  #b8b5ff; font-weight: bold;',
                                    'columns': [{'name': '', 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['debit'])),
                                                 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['credit'])),
                                                 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['balance'])),
                                                 'class': 'number'},
                                                {'name': '', 'class': 'number'}],
                                    'unfoldable': True, 'unfolded': False, 'colspan': 4}
                        return_list.append(dic_head)
                        return_list.append({'id': 'initial_' + str(count), #'class': 'o_account_reports_initial_balance',
                                            'name': 'Initial Balance Account', 'style': 'font-weight: bold;',
                                            'parent_id': dic_head['id'], 'level':3,
                                            'columns': [{'name': '', 'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['debit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['credit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['balance']),
                                                         'class': 'number'},
                                                        {'name': ''}],
                                            'colspan': 4})
                        count_fil = 0
                        for filter_data in line['detail']:
                            count_fil += 1
                            dic_head_f = {'id': filter_data['filter1'].name + str(filter_data['filter1'].id)+str(count),
                                        'name': str(filter_data['filter1'].name if len(filter_data['filter1'].name) < 14 else filter_data['filter1'].name[:11] + "..."),
                                        'title_hover': str(filter_data['filter1'].name), 'level':4, 'style': 'background: #adabd4;',
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(float(filter_data['total_balance']['debit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(float(filter_data['total_balance']['credit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(float(filter_data['total_balance']['balance'])),
                                                     'class': 'number'},
                                                    {'name': '', 'class': 'number'}],
                                        'unfoldable': True, 'unfolded': False, 'colspan': 4, 'parent_id': dic_head['id']}
                            return_list.append(dic_head_f)
                            return_list.append({'id': 'initial_' + str(count_fil), #'class': 'o_account_reports_initial_balance',
                                                'name': 'Initial Balance',
                                                'parent_id': dic_head_f['id'], 'level': 5,
                                                'columns': [{'name': '', 'class': 'number'},
                                                            {'name': self.format_value(filter_data['initial_balance']['debit']),
                                                             'class': 'number'},
                                                            {'name': self.format_value(filter_data['initial_balance']['credit']),
                                                             'class': 'number'},
                                                            {'name': self.format_value(filter_data['initial_balance']['balance']),
                                                             'class': 'number'},
                                                            {'name': ''}],
                                                'colspan': 4})

                            for move in filter_data['move']:
                                dic_move = {'id': move.id, 'caret_options': 'account.move', 'class': 'top-vertical-align',
                                            'level': 6, 'name': str(move.move_name),
                                            'columns': [{'name': str(move.journal_id.name)},
                                                        {'name': str(move.date), 'class': 'date'},
                                                        {'name': str(
                                                            move.move_id.reversed_entry_id.journal_id.name if move.move_id.reversed_entry_id.journal_id.name != False else "")},
                                                        {'name': str(
                                                            move.move_id.reversed_entry_id.name if move.move_id.reversed_entry_id.name != False else "")},
                                                        {'name': self.format_value(float(move.debit)), 'class': 'number'},
                                                        {'name': self.format_value(float(move.credit)), 'class': 'number'},
                                                        {'name': self.format_value(float(move.balance)), 'class': 'number'},
                                                        {'name': str(move.ref), 'class': 'whitespace_#print'}],
                                            'parent_id': dic_head_f['id']}

                                return_list.append(dic_move)
                            return_list.append(
                                {'id': 'totals_' + str(count), 'name': 'Total',
                                 'style': 'background: #adabd4;', 'parent_id': dic_head_f['id'], 'level':5,
                                 'columns': [{'name': '', 'class': 'number'},
                                             {'name': self.format_value(filter_data['total_balance']['debit']), 'class': 'number'},
                                             {'name': self.format_value(filter_data['total_balance']['credit']), 'class': 'number'},
                                             {'name': self.format_value(filter_data['total_balance']['balance']), 'class': 'number'},
                                             {'name': ''}],
                                 'colspan': 4})

                        return_list.append(
                            {'id': 'totals_' + str(count),  'name': 'Total Account',
                             'style': 'background: #b8b5ff; font-weight: bold;', 'parent_id': dic_head['id'], 'level':3,
                             'columns': [{'name': '', 'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['debit']), 'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['credit']), 'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['balance']), 'class': 'number'},
                                         {'name': ''}],
                             'colspan': 4})
            else:
                for line in data:
                    count += 1
                    dic_head = {'id': "head" + str(line['account'].id),
                                'name': str(line['account'].code) + " " + str(
                                    line['account'].name if len(line['account'].name) < 14 else line['account'].name[
                                                                                                :11] + "..."),
                                'level': 2,
                                'title_hover': str(line['account'].code) + " " + str(line['account'].name),
                                'style': 'background:  #b8b5ff; font-weight: bold;',
                                'columns': [{'name': '', 'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['debit'])),
                                             'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['credit'])),
                                             'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['balance'])),
                                             'class': 'number'},
                                            {'name': '', 'class': 'number'}],
                                'unfoldable': True, 'unfolded': False, 'colspan': 4}
                    return_list.append(dic_head)
                    return_list.append({'id': 'initial_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                        'name': 'Initial Balance Account', 'style': 'font-weight: bold;',
                                        'parent_id': dic_head['id'], 'level': 3,
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['debit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['credit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['balance']),
                                                     'class': 'number'},
                                                    {'name': ''}],
                                        'colspan': 4})
                    count_fil = 0
                    for filter_data in line['detail']:
                        count_fil += 1
                        dic_head_f = {'id': filter_data['filter1'].name + str(filter_data['filter1'].id) + str(count),
                                      'name': str(
                                          filter_data['filter1'].name if len(filter_data['filter1'].name) < 14 else
                                          filter_data['filter1'].name[:11] + "..."),
                                      'title_hover': str(filter_data['filter1'].name), 'level': 4,
                                      'style': 'background: #adabd4;',
                                      'columns': [{'name': '', 'class': 'number'},
                                                  {'name': self.format_value(
                                                      float(filter_data['total_balance']['debit'])),
                                                   'class': 'number'},
                                                  {'name': self.format_value(
                                                      float(filter_data['total_balance']['credit'])),
                                                   'class': 'number'},
                                                  {'name': self.format_value(
                                                      float(filter_data['total_balance']['balance'])),
                                                   'class': 'number'},
                                                  {'name': '', 'class': 'number'}],
                                      'unfoldable': True, 'unfolded': False, 'colspan': 4, 'parent_id': dic_head['id']}
                        return_list.append(dic_head_f)
                        return_list.append(
                            {'id': 'initial_' + str(count_fil),  # 'class': 'o_account_reports_initial_balance',
                             'name': 'Initial Balance',
                             'parent_id': dic_head_f['id'], 'level': 5,
                             'columns': [{'name': '', 'class': 'number'},
                                         {'name': self.format_value(filter_data['initial_balance']['debit']),
                                          'class': 'number'},
                                         {'name': self.format_value(filter_data['initial_balance']['credit']),
                                          'class': 'number'},
                                         {'name': self.format_value(filter_data['initial_balance']['balance']),
                                          'class': 'number'},
                                         {'name': ''}],
                             'colspan': 4})

                        for move in filter_data['move']:
                            dic_move = {'id': move.id, 'caret_options': 'account.move', 'class': 'top-vertical-align',
                                        'level': 6, 'name': str(move.move_name),
                                        'columns': [{'name': str(move.journal_id.name)},
                                                    {'name': str(move.date), 'class': 'date'},
                                                    {'name': str(
                                                        move.move_id.reversed_entry_id.journal_id.name if move.move_id.reversed_entry_id.journal_id.name != False else "")},
                                                    {'name': str(
                                                        move.move_id.reversed_entry_id.name if move.move_id.reversed_entry_id.name != False else "")},
                                                    {'name': self.format_value(float(move.debit)), 'class': 'number'},
                                                    {'name': self.format_value(float(move.credit)), 'class': 'number'},
                                                    {'name': self.format_value(float(move.balance)), 'class': 'number'},
                                                    {'name': str(move.ref), 'class': 'whitespace_#print'}],
                                        'parent_id': dic_head_f['id']}

                            return_list.append(dic_move)
                        return_list.append(
                            {'id': 'totals_' + str(count), 'name': 'Total',
                             'style': 'background: #adabd4;', 'parent_id': dic_head_f['id'], 'level': 5,
                             'columns': [{'name': '', 'class': 'number'},
                                         {'name': self.format_value(filter_data['total_balance']['debit']),
                                          'class': 'number'},
                                         {'name': self.format_value(filter_data['total_balance']['credit']),
                                          'class': 'number'},
                                         {'name': self.format_value(filter_data['total_balance']['balance']),
                                          'class': 'number'},
                                         {'name': ''}],
                             'colspan': 4})

                    return_list.append(
                        {'id': 'totals_' + str(count), 'name': 'Total Account',
                         'style': 'background: #b8b5ff; font-weight: bold;', 'parent_id': dic_head['id'], 'level': 3,
                         'columns': [{'name': '', 'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['debit']), 'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['credit']), 'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['balance']), 'class': 'number'},
                                     {'name': ''}],
                         'colspan': 4})

        elif data[0]['number_filters'] == 2:

            count = 0
            if acc_all:
                for line in data:
                    if line['total_balance']['balance'] != 0:
                        count += 1

                        dic_head = {'id': "head" + str(line['account'].id),
                                    'name': str(line['account'].code) + " " + str(
                                        line['account'].name if len(line['account'].name) < 14 else line['account'].name[:11] + "..."),
                                    'level': 2, 'style': 'background: #b8b5ff; font-weight: bold;',
                                    'title_hover': str(line['account'].code) + " " + str(line['account'].name),
                                    'columns': [{'name': '', 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['debit'])),
                                                 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['credit'])),
                                                 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['balance'])),
                                                 'class': 'number'},
                                                {'name': '', 'class': 'number'}],
                                    'unfoldable': True, 'unfolded': False, 'colspan': 4}
                        return_list.append(dic_head)
                        return_list.append({'id': 'initial_' + str(count), #'class': 'o_account_reports_initial_balance',
                                            'name': 'Initial Balance Account',
                                            'style': 'font-weight: bold;',
                                            'parent_id': dic_head['id'], 'level': 3,
                                            'columns': [{'name': '', 'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['debit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['credit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['balance']),
                                                         'class': 'number'},
                                                        {'name': ''}],
                                            'colspan': 4})
                        count_f_1 = 0
                        for line_filter1 in line['detail']:
                            count_f_1 += 1
                            dic_head_f_1 = {'id': str(line_filter1['filter1'].id )+ str(count),
                                        'name': str(line_filter1['filter1'].name if len(line_filter1['filter1'].name) < 15 else line_filter1['filter1'].name[:12] + "..."),
                                        'level': 4, 'title_hover': str(line_filter1['filter1'].name), 'style': 'background: #adabd4;',
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(float(line_filter1['total_balance']['debit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(float(line_filter1['total_balance']['credit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(float(line_filter1['total_balance']['balance'])),
                                                     'class': 'number'},
                                                    {'name': '', 'class': 'number'}],
                                        'unfoldable': True, 'unfolded': False, 'colspan': 4, 'parent_id': dic_head['id']}
                            return_list.append(dic_head_f_1)
                            return_list.append({'id': 'initial_' + str(count)+str(count_f_1), #'class': 'o_account_reports_initial_balance',
                                                'name': 'Initial Balance',
                                                #'style': 'background: #dddcf9; font-weight: bold;',
                                                'parent_id': dic_head_f_1['id'], 'level': 5,
                                                'columns': [{'name': '', 'class': 'number'},
                                                            {'name': self.format_value(line_filter1['initial_balance']['debit']),
                                                             'class': 'number'},
                                                            {'name': self.format_value(line_filter1['initial_balance']['credit']),
                                                             'class': 'number'},
                                                            {'name': self.format_value(line_filter1['initial_balance']['balance']),
                                                             'class': 'number'},
                                                            {'name': ''}], 'colspan': 4})
                            count_f_2 = 0
                            for line_filter2 in line_filter1['detail']:
                                count_f_2 += 1
                                dic_head_f_2 = {'id': str(line_filter2['filter2'].id) + str(count),
                                                'name': str(line_filter2['filter2'].name if len(line_filter2['filter2'].name) < 15 else  line_filter2['filter2'].name[:12] + "..."),
                                                'level': 6, 'title_hover': str(line_filter2['filter2'].name), 'style': 'background: #b2b1c7;',
                                                'columns': [{'name': '', 'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter2['total_balance']['debit'])),
                                                             'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter2['total_balance']['credit'])),
                                                             'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter2['total_balance']['balance'])),
                                                             'class': 'number'},
                                                            {'name': '', 'class': 'number'}],
                                                'unfoldable': True, 'unfolded': False, 'colspan': 4, 'parent_id': dic_head_f_1['id']}
                                return_list.append(dic_head_f_2)
                                return_list.append(
                                    {'id': 'initial_' + str(count) + str(count_f_1) + str(count_f_2), #'class': 'o_account_reports_initial_balance',
                                     'name': 'Initial Balance',
                                     #'style': 'background: #dddcf9;',
                                     'parent_id': dic_head_f_2['id'], 'level': 7,
                                     'columns': [{'name': '', 'class': 'number'},
                                                 {'name': self.format_value(line_filter2['initial_balance']['debit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter2['initial_balance']['credit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter2['initial_balance']['balance']),
                                                  'class': 'number'},
                                                 {'name': ''}], 'colspan': 4})

                                for move in line_filter2['move']:
                                    dic_move = {'id': move.id, 'caret_options': 'account.move', 'class': 'top-vertical-align',
                                                'level': 8, 'name': str(move.move_name),
                                                'columns': [{'name': str(move.journal_id.name)},
                                                            {'name': str(move.date), 'class': 'date'},
                                                            {'name': str(
                                                                move.move_id.reversed_entry_id.journal_id.name if move.move_id.reversed_entry_id.journal_id.name != False else "")},
                                                            {'name': str(
                                                                move.move_id.reversed_entry_id.name if move.move_id.reversed_entry_id.name != False else "")},
                                                            {'name': self.format_value(float(move.debit)), 'class': 'number'},
                                                            {'name': self.format_value(float(move.credit)), 'class': 'number'},
                                                            {'name': self.format_value(float(move.balance)), 'class': 'number'},
                                                            {'name': str(move.ref), 'class': 'whitespace_#print'}],
                                                'parent_id': dic_head_f_2['id']}

                                    return_list.append(dic_move)

                                return_list.append(
                                    {'id': 'totals_' + str(count), #'class': 'o_account_reports_initial_balance',
                                     'name': 'Total', 'level': 7,
                                     'style': 'background: #b2b1c7;',
                                     'parent_id': dic_head_f_2['id'],
                                     'columns': [{'name': '', 'class': 'number'},
                                                 {'name': self.format_value(line_filter2['total_balance']['debit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter2['total_balance']['credit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter2['total_balance']['balance']),
                                                  'class': 'number'},
                                                 {'name': ''}],
                                     'colspan': 4})

                            return_list.append(
                                {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                 'name': 'Total', 'level': 5,
                                 'style': 'background: #adabd4;',
                                 'parent_id': dic_head_f_1['id'],
                                 'columns': [{'name': '', 'class': 'number'},
                                             {'name': self.format_value(line_filter1['total_balance']['debit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter1['total_balance']['credit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter1['total_balance']['balance']),
                                              'class': 'number'},
                                             {'name': ''}],
                                 'colspan': 4})

                        return_list.append(
                            {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                             'name': 'Total', 'level': 3,
                             'style': 'background: #b8b5ff; font-weight: bold;',
                             'parent_id': dic_head['id'],
                             'columns': [{'name': '', 'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['debit']),
                                          'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['credit']),
                                          'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['balance']),
                                          'class': 'number'},
                                         {'name': ''}],
                             'colspan': 4})
            else:
                for line in data:
                    count += 1

                    dic_head = {'id': "head" + str(line['account'].id),
                                'name': str(line['account'].code) + " " + str(
                                    line['account'].name if len(line['account'].name) < 14 else line['account'].name[
                                                                                                :11] + "..."),
                                'level': 2, 'style': 'background: #b8b5ff; font-weight: bold;',
                                'title_hover': str(line['account'].code) + " " + str(line['account'].name),
                                'columns': [{'name': '', 'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['debit'])),
                                             'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['credit'])),
                                             'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['balance'])),
                                             'class': 'number'},
                                            {'name': '', 'class': 'number'}],
                                'unfoldable': True, 'unfolded': False, 'colspan': 4}
                    return_list.append(dic_head)
                    return_list.append({'id': 'initial_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                        'name': 'Initial Balance Account',
                                        'style': 'font-weight: bold;',
                                        'parent_id': dic_head['id'], 'level': 3,
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['debit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['credit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['balance']),
                                                     'class': 'number'},
                                                    {'name': ''}],
                                        'colspan': 4})
                    count_f_1 = 0
                    for line_filter1 in line['detail']:
                        count_f_1 += 1
                        dic_head_f_1 = {'id': str(line_filter1['filter1'].id) + str(count),
                                        'name': str(
                                            line_filter1['filter1'].name if len(line_filter1['filter1'].name) < 15 else
                                            line_filter1['filter1'].name[:12] + "..."),
                                        'level': 4, 'title_hover': str(line_filter1['filter1'].name),
                                        'style': 'background: #adabd4;',
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(
                                                        float(line_filter1['total_balance']['debit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(
                                                        float(line_filter1['total_balance']['credit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(
                                                        float(line_filter1['total_balance']['balance'])),
                                                     'class': 'number'},
                                                    {'name': '', 'class': 'number'}],
                                        'unfoldable': True, 'unfolded': False, 'colspan': 4,
                                        'parent_id': dic_head['id']}
                        return_list.append(dic_head_f_1)
                        return_list.append({'id': 'initial_' + str(count) + str(count_f_1),
                                            # 'class': 'o_account_reports_initial_balance',
                                            'name': 'Initial Balance',
                                            # 'style': 'background: #dddcf9; font-weight: bold;',
                                            'parent_id': dic_head_f_1['id'], 'level': 5,
                                            'columns': [{'name': '', 'class': 'number'},
                                                        {'name': self.format_value(
                                                            line_filter1['initial_balance']['debit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(
                                                            line_filter1['initial_balance']['credit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(
                                                            line_filter1['initial_balance']['balance']),
                                                         'class': 'number'},
                                                        {'name': ''}], 'colspan': 4})
                        count_f_2 = 0
                        for line_filter2 in line_filter1['detail']:
                            count_f_2 += 1
                            dic_head_f_2 = {'id': str(line_filter2['filter2'].id) + str(count),
                                            'name': str(line_filter2['filter2'].name if len(
                                                line_filter2['filter2'].name) < 15 else line_filter2['filter2'].name[
                                                                                        :12] + "..."),
                                            'level': 6, 'title_hover': str(line_filter2['filter2'].name),
                                            'style': 'background: #b2b1c7;',
                                            'columns': [{'name': '', 'class': 'number'},
                                                        {'name': self.format_value(
                                                            float(line_filter2['total_balance']['debit'])),
                                                            'class': 'number'},
                                                        {'name': self.format_value(
                                                            float(line_filter2['total_balance']['credit'])),
                                                            'class': 'number'},
                                                        {'name': self.format_value(
                                                            float(line_filter2['total_balance']['balance'])),
                                                            'class': 'number'},
                                                        {'name': '', 'class': 'number'}],
                                            'unfoldable': True, 'unfolded': False, 'colspan': 4,
                                            'parent_id': dic_head_f_1['id']}
                            return_list.append(dic_head_f_2)
                            return_list.append(
                                {'id': 'initial_' + str(count) + str(count_f_1) + str(count_f_2),
                                 # 'class': 'o_account_reports_initial_balance',
                                 'name': 'Initial Balance',
                                 # 'style': 'background: #dddcf9;',
                                 'parent_id': dic_head_f_2['id'], 'level': 7,
                                 'columns': [{'name': '', 'class': 'number'},
                                             {'name': self.format_value(line_filter2['initial_balance']['debit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter2['initial_balance']['credit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter2['initial_balance']['balance']),
                                              'class': 'number'},
                                             {'name': ''}], 'colspan': 4})

                            for move in line_filter2['move']:
                                dic_move = {'id': move.id, 'caret_options': 'account.move',
                                            'class': 'top-vertical-align',
                                            'level': 8, 'name': str(move.move_name),
                                            'columns': [{'name': str(move.journal_id.name)},
                                                        {'name': str(move.date), 'class': 'date'},
                                                        {'name': str(
                                                            move.move_id.reversed_entry_id.journal_id.name if move.move_id.reversed_entry_id.journal_id.name != False else "")},
                                                        {'name': str(
                                                            move.move_id.reversed_entry_id.name if move.move_id.reversed_entry_id.name != False else "")},
                                                        {'name': self.format_value(float(move.debit)),
                                                         'class': 'number'},
                                                        {'name': self.format_value(float(move.credit)),
                                                         'class': 'number'},
                                                        {'name': self.format_value(float(move.balance)),
                                                         'class': 'number'},
                                                        {'name': str(move.ref), 'class': 'whitespace_#print'}],
                                            'parent_id': dic_head_f_2['id']}

                                return_list.append(dic_move)

                            return_list.append(
                                {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                 'name': 'Total', 'level': 7,
                                 'style': 'background: #b2b1c7;',
                                 'parent_id': dic_head_f_2['id'],
                                 'columns': [{'name': '', 'class': 'number'},
                                             {'name': self.format_value(line_filter2['total_balance']['debit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter2['total_balance']['credit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter2['total_balance']['balance']),
                                              'class': 'number'},
                                             {'name': ''}],
                                 'colspan': 4})

                        return_list.append(
                            {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                             'name': 'Total', 'level': 5,
                             'style': 'background: #adabd4;',
                             'parent_id': dic_head_f_1['id'],
                             'columns': [{'name': '', 'class': 'number'},
                                         {'name': self.format_value(line_filter1['total_balance']['debit']),
                                          'class': 'number'},
                                         {'name': self.format_value(line_filter1['total_balance']['credit']),
                                          'class': 'number'},
                                         {'name': self.format_value(line_filter1['total_balance']['balance']),
                                          'class': 'number'},
                                         {'name': ''}],
                             'colspan': 4})

                    return_list.append(
                        {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                         'name': 'Total', 'level': 3,
                         'style': 'background: #b8b5ff; font-weight: bold;',
                         'parent_id': dic_head['id'],
                         'columns': [{'name': '', 'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['debit']),
                                      'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['credit']),
                                      'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['balance']),
                                      'class': 'number'},
                                     {'name': ''}],
                         'colspan': 4})

        elif data[0]['number_filters'] == 3:

            count = 0
            if acc_all:
                for line in data:
                    if line['total_balance']['balance'] != 0:
                        count += 1

                        dic_head = {'id': "head" + str(line['account'].id),
                                    'name': str(line['account'].code) + " " + str(
                                        line['account'].name if len(line['account'].name) < 14 else line['account'].name[:11] + "..."),
                                    'level': 2, 'style': 'background: #b8b5ff; font-weight: bold;',
                                    'title_hover': str(line['account'].code) + " " + str(line['account'].name),
                                    'columns': [{'name': '', 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['debit'])),
                                                 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['credit'])),
                                                 'class': 'number'},
                                                {'name': self.format_value(float(line['total_balance']['balance'])),
                                                 'class': 'number'},
                                                {'name': '', 'class': 'number'}],
                                    'unfoldable': True, 'unfolded': False, 'colspan': 4}
                        return_list.append(dic_head)
                        return_list.append({'id': 'initial_' + str(count), #'class': 'o_account_reports_initial_balance',
                                            'name': 'Initial Balance Account',
                                            'style': 'font-weight: bold;',
                                            'parent_id': dic_head['id'], 'level': 3,
                                            'columns': [{'name': '', 'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['debit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['credit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(line['initial_balance']['balance']),
                                                         'class': 'number'},
                                                        {'name': ''}],
                                            'colspan': 4})
                        count_f_1 = 0
                        for line_filter1 in line['detail']:
                            count_f_1 += 1
                            dic_head_f_1 = {'id': str(line_filter1['filter1'].id )+ str(count),
                                        'name': str(line_filter1['filter1'].name if len(line_filter1['filter1'].name) < 15 else line_filter1['filter1'].name[:12] + "..."),
                                        'level': 4, 'title_hover': str(line_filter1['filter1'].name), 'style': 'background: #adabd4;',
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(float(line_filter1['total_balance']['debit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(float(line_filter1['total_balance']['credit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(float(line_filter1['total_balance']['balance'])),
                                                     'class': 'number'},
                                                    {'name': '', 'class': 'number'}],
                                        'unfoldable': True, 'unfolded': False, 'colspan': 4, 'parent_id': dic_head['id']}
                            return_list.append(dic_head_f_1)
                            return_list.append({'id': 'initial_' + str(count)+str(count_f_1), #'class': 'o_account_reports_initial_balance',
                                                'name': 'Initial Balance',
                                                #'style': 'background: #dddcf9; font-weight: bold;',
                                                'parent_id': dic_head_f_1['id'], 'level': 5,
                                                'columns': [{'name': '', 'class': 'number'},
                                                            {'name': self.format_value(line_filter1['initial_balance']['debit']),
                                                             'class': 'number'},
                                                            {'name': self.format_value(line_filter1['initial_balance']['credit']),
                                                             'class': 'number'},
                                                            {'name': self.format_value(line_filter1['initial_balance']['balance']),
                                                             'class': 'number'},
                                                            {'name': ''}], 'colspan': 4})
                            count_f_2 = 0
                            for line_filter2 in line_filter1['detail']:
                                count_f_2 += 1
                                dic_head_f_2 = {'id': str(line_filter2['filter2'].id) + str(count),
                                                'name': str(line_filter2['filter2'].name if len(line_filter2['filter2'].name) < 15 else  line_filter2['filter2'].name[:12] + "..."),
                                                'level': 6, 'title_hover': str(line_filter2['filter2'].name), 'style': 'background: #b2b1c7;',
                                                'columns': [{'name': '', 'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter2['total_balance']['debit'])),
                                                             'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter2['total_balance']['credit'])),
                                                             'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter2['total_balance']['balance'])),
                                                             'class': 'number'},
                                                            {'name': '', 'class': 'number'}],
                                                'unfoldable': True, 'unfolded': False, 'colspan': 4, 'parent_id': dic_head_f_1['id']}
                                return_list.append(dic_head_f_2)
                                return_list.append(
                                    {'id': 'initial_' + str(count) + str(count_f_1) + str(count_f_2), #'class': 'o_account_reports_initial_balance',
                                     'name': 'Initial Balance',
                                     #'style': 'background: #dddcf9;',
                                     'parent_id': dic_head_f_2['id'], 'level': 7,
                                     'columns': [{'name': '', 'class': 'number'},
                                                 {'name': self.format_value(line_filter2['initial_balance']['debit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter2['initial_balance']['credit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter2['initial_balance']['balance']),
                                                  'class': 'number'},
                                                 {'name': ''}], 'colspan': 4})

                                count_f_3 = 0
                                for line_filter3 in line_filter2['detail']:
                                    count_f_3 += 1
                                    dic_head_f_3 = {'id': str(line_filter3['filter3'].id) + str(count),
                                                    'name': str(line_filter3['filter3'].name if len(
                                                        line_filter3['filter3'].name) < 15 else line_filter3['filter3'].name[
                                                                                                :12] + "..."),
                                                    'level': 8, 'title_hover': str(line_filter3['filter3'].name),
                                                    'style': 'background: #e4e3fa;',
                                                    'columns': [{'name': '', 'class': 'number'},
                                                                {'name': self.format_value(
                                                                    float(line_filter3['total_balance']['debit'])),
                                                                    'class': 'number'},
                                                                {'name': self.format_value(
                                                                    float(line_filter3['total_balance']['credit'])),
                                                                    'class': 'number'},
                                                                {'name': self.format_value(
                                                                    float(line_filter3['total_balance']['balance'])),
                                                                    'class': 'number'},
                                                                {'name': '', 'class': 'number'}],
                                                    'unfoldable': True, 'unfolded': False, 'colspan': 4,
                                                    'parent_id': dic_head_f_2['id']}
                                    return_list.append(dic_head_f_3)
                                    return_list.append(
                                        {'id': 'initial_' + str(count) + str(count_f_1) + str(count_f_2) +str(count_f_3),
                                         # 'class': 'o_account_reports_initial_balance',
                                         'name': 'Initial Balance',
                                         # 'style': 'background: #dddcf9;',
                                         'parent_id': dic_head_f_3['id'], 'level': 9,
                                         'columns': [{'name': '', 'class': 'number'},
                                                     {'name': self.format_value(line_filter3['initial_balance']['debit']),
                                                      'class': 'number'},
                                                     {'name': self.format_value(line_filter3['initial_balance']['credit']),
                                                      'class': 'number'},
                                                     {'name': self.format_value(line_filter3['initial_balance']['balance']),
                                                      'class': 'number'},
                                                     {'name': ''}], 'colspan': 4})

                                    for move in line_filter3['move']:
                                        dic_move = {'id': move.id, 'caret_options': 'account.move', 'class': 'top-vertical-align',
                                                    'level': 10, 'name': str(move.move_name),
                                                    'columns': [{'name': str(move.journal_id.name)},
                                                                {'name': str(move.date), 'class': 'date'},
                                                                {'name': str(
                                                                    move.move_id.reversed_entry_id.journal_id.name if move.move_id.reversed_entry_id.journal_id.name != False else "")},
                                                                {'name': str(
                                                                    move.move_id.reversed_entry_id.name if move.move_id.reversed_entry_id.name != False else "")},
                                                                {'name': self.format_value(float(move.debit)), 'class': 'number'},
                                                                {'name': self.format_value(float(move.credit)), 'class': 'number'},
                                                                {'name': self.format_value(float(move.balance)), 'class': 'number'},
                                                                {'name': str(move.ref), 'class': 'whitespace_#print'}],
                                                    'parent_id': dic_head_f_3['id']}

                                        return_list.append(dic_move)

                                    return_list.append(
                                        {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                         'name': 'Total', 'level': 9,
                                         'style': 'background: #e4e3fa;',
                                         'parent_id': dic_head_f_3['id'],
                                         'columns': [{'name': '', 'class': 'number'},
                                                     {'name': self.format_value(line_filter3['total_balance']['debit']),
                                                      'class': 'number'},
                                                     {'name': self.format_value(line_filter3['total_balance']['credit']),
                                                      'class': 'number'},
                                                     {'name': self.format_value(line_filter3['total_balance']['balance']),
                                                      'class': 'number'},
                                                     {'name': ''}],
                                         'colspan': 4})


                                return_list.append(
                                    {'id': 'totals_' + str(count), #'class': 'o_account_reports_initial_balance',
                                     'name': 'Total', 'level': 7,
                                     'style': 'background: #b2b1c7;',
                                     'parent_id': dic_head_f_2['id'],
                                     'columns': [{'name': '', 'class': 'number'},
                                                 {'name': self.format_value(line_filter2['total_balance']['debit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter2['total_balance']['credit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter2['total_balance']['balance']),
                                                  'class': 'number'},
                                                 {'name': ''}],
                                     'colspan': 4})

                            return_list.append(
                                {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                 'name': 'Total', 'level': 5,
                                 'style': 'background: #adabd4;',
                                 'parent_id': dic_head_f_1['id'],
                                 'columns': [{'name': '', 'class': 'number'},
                                             {'name': self.format_value(line_filter1['total_balance']['debit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter1['total_balance']['credit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter1['total_balance']['balance']),
                                              'class': 'number'},
                                             {'name': ''}],
                                 'colspan': 4})

                        return_list.append(
                            {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                             'name': 'Total Account', 'level': 3,
                             'style': 'background: #b8b5ff; font-weight: bold;',
                             'parent_id': dic_head['id'],
                             'columns': [{'name': '', 'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['debit']),
                                          'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['credit']),
                                          'class': 'number'},
                                         {'name': self.format_value(line['total_balance']['balance']),
                                          'class': 'number'},
                                         {'name': ''}],
                             'colspan': 4})
            else:
                for line in data:
                    count += 1

                    dic_head = {'id': "head" + str(line['account'].id),
                                'name': str(line['account'].code) + " " + str(
                                    line['account'].name if len(line['account'].name) < 14 else line['account'].name[
                                                                                                :11] + "..."),
                                'level': 2, 'style': 'background: #b8b5ff; font-weight: bold;',
                                'title_hover': str(line['account'].code) + " " + str(line['account'].name),
                                'columns': [{'name': '', 'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['debit'])),
                                             'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['credit'])),
                                             'class': 'number'},
                                            {'name': self.format_value(float(line['total_balance']['balance'])),
                                             'class': 'number'},
                                            {'name': '', 'class': 'number'}],
                                'unfoldable': True, 'unfolded': False, 'colspan': 4}
                    return_list.append(dic_head)
                    return_list.append({'id': 'initial_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                        'name': 'Initial Balance Account',
                                        'style': 'font-weight: bold;',
                                        'parent_id': dic_head['id'], 'level': 3,
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['debit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['credit']),
                                                     'class': 'number'},
                                                    {'name': self.format_value(line['initial_balance']['balance']),
                                                     'class': 'number'},
                                                    {'name': ''}],
                                        'colspan': 4})
                    count_f_1 = 0
                    for line_filter1 in line['detail']:
                        count_f_1 += 1
                        dic_head_f_1 = {'id': str(line_filter1['filter1'].id) + str(count),
                                        'name': str(
                                            line_filter1['filter1'].name if len(line_filter1['filter1'].name) < 15 else
                                            line_filter1['filter1'].name[:12] + "..."),
                                        'level': 4, 'title_hover': str(line_filter1['filter1'].name),
                                        'style': 'background: #adabd4;',
                                        'columns': [{'name': '', 'class': 'number'},
                                                    {'name': self.format_value(
                                                        float(line_filter1['total_balance']['debit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(
                                                        float(line_filter1['total_balance']['credit'])),
                                                     'class': 'number'},
                                                    {'name': self.format_value(
                                                        float(line_filter1['total_balance']['balance'])),
                                                     'class': 'number'},
                                                    {'name': '', 'class': 'number'}],
                                        'unfoldable': True, 'unfolded': False, 'colspan': 4,
                                        'parent_id': dic_head['id']}
                        return_list.append(dic_head_f_1)
                        return_list.append({'id': 'initial_' + str(count) + str(count_f_1),
                                            # 'class': 'o_account_reports_initial_balance',
                                            'name': 'Initial Balance',
                                            # 'style': 'background: #dddcf9; font-weight: bold;',
                                            'parent_id': dic_head_f_1['id'], 'level': 5,
                                            'columns': [{'name': '', 'class': 'number'},
                                                        {'name': self.format_value(
                                                            line_filter1['initial_balance']['debit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(
                                                            line_filter1['initial_balance']['credit']),
                                                         'class': 'number'},
                                                        {'name': self.format_value(
                                                            line_filter1['initial_balance']['balance']),
                                                         'class': 'number'},
                                                        {'name': ''}], 'colspan': 4})
                        count_f_2 = 0
                        for line_filter2 in line_filter1['detail']:
                            count_f_2 += 1
                            dic_head_f_2 = {'id': str(line_filter2['filter2'].id) + str(count),
                                            'name': str(line_filter2['filter2'].name if len(
                                                line_filter2['filter2'].name) < 15 else line_filter2['filter2'].name[
                                                                                        :12] + "..."),
                                            'level': 6, 'title_hover': str(line_filter2['filter2'].name),
                                            'style': 'background: #b2b1c7;',
                                            'columns': [{'name': '', 'class': 'number'},
                                                        {'name': self.format_value(
                                                            float(line_filter2['total_balance']['debit'])),
                                                            'class': 'number'},
                                                        {'name': self.format_value(
                                                            float(line_filter2['total_balance']['credit'])),
                                                            'class': 'number'},
                                                        {'name': self.format_value(
                                                            float(line_filter2['total_balance']['balance'])),
                                                            'class': 'number'},
                                                        {'name': '', 'class': 'number'}],
                                            'unfoldable': True, 'unfolded': False, 'colspan': 4,
                                            'parent_id': dic_head_f_1['id']}
                            return_list.append(dic_head_f_2)
                            return_list.append(
                                {'id': 'initial_' + str(count) + str(count_f_1) + str(count_f_2),
                                 # 'class': 'o_account_reports_initial_balance',
                                 'name': 'Initial Balance',
                                 # 'style': 'background: #dddcf9;',
                                 'parent_id': dic_head_f_2['id'], 'level': 7,
                                 'columns': [{'name': '', 'class': 'number'},
                                             {'name': self.format_value(line_filter2['initial_balance']['debit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter2['initial_balance']['credit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter2['initial_balance']['balance']),
                                              'class': 'number'},
                                             {'name': ''}], 'colspan': 4})

                            count_f_3 = 0
                            for line_filter3 in line_filter2['detail']:
                                count_f_3 += 1
                                dic_head_f_3 = {'id': str(line_filter3['filter3'].id) + str(count),
                                                'name': str(line_filter3['filter3'].name if len(
                                                    line_filter3['filter3'].name) < 15 else line_filter3[
                                                                                                'filter3'].name[
                                                                                            :12] + "..."),
                                                'level': 8, 'title_hover': str(line_filter3['filter3'].name),
                                                'style': 'background: #e4e3fa;',
                                                'columns': [{'name': '', 'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter3['total_balance']['debit'])),
                                                                'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter3['total_balance']['credit'])),
                                                                'class': 'number'},
                                                            {'name': self.format_value(
                                                                float(line_filter3['total_balance']['balance'])),
                                                                'class': 'number'},
                                                            {'name': '', 'class': 'number'}],
                                                'unfoldable': True, 'unfolded': False, 'colspan': 4,
                                                'parent_id': dic_head_f_2['id']}
                                return_list.append(dic_head_f_3)
                                return_list.append(
                                    {'id': 'initial_' + str(count) + str(count_f_1) + str(count_f_2) + str(count_f_3),
                                     # 'class': 'o_account_reports_initial_balance',
                                     'name': 'Initial Balance',
                                     # 'style': 'background: #dddcf9;',
                                     'parent_id': dic_head_f_3['id'], 'level': 9,
                                     'columns': [{'name': '', 'class': 'number'},
                                                 {'name': self.format_value(line_filter3['initial_balance']['debit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter3['initial_balance']['credit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter3['initial_balance']['balance']),
                                                  'class': 'number'},
                                                 {'name': ''}], 'colspan': 4})

                                for move in line_filter3['move']:
                                    dic_move = {'id': move.id, 'caret_options': 'account.move',
                                                'class': 'top-vertical-align',
                                                'level': 10, 'name': str(move.move_name),
                                                'columns': [{'name': str(move.journal_id.name)},
                                                            {'name': str(move.date), 'class': 'date'},
                                                            {'name': str(
                                                                move.move_id.reversed_entry_id.journal_id.name if move.move_id.reversed_entry_id.journal_id.name != False else "")},
                                                            {'name': str(
                                                                move.move_id.reversed_entry_id.name if move.move_id.reversed_entry_id.name != False else "")},
                                                            {'name': self.format_value(float(move.debit)),
                                                             'class': 'number'},
                                                            {'name': self.format_value(float(move.credit)),
                                                             'class': 'number'},
                                                            {'name': self.format_value(float(move.balance)),
                                                             'class': 'number'},
                                                            {'name': str(move.ref), 'class': 'whitespace_#print'}],
                                                'parent_id': dic_head_f_3['id']}

                                    return_list.append(dic_move)

                                return_list.append(
                                    {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                     'name': 'Total', 'level': 9,
                                     'style': 'background: #e4e3fa;',
                                     'parent_id': dic_head_f_3['id'],
                                     'columns': [{'name': '', 'class': 'number'},
                                                 {'name': self.format_value(line_filter3['total_balance']['debit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter3['total_balance']['credit']),
                                                  'class': 'number'},
                                                 {'name': self.format_value(line_filter3['total_balance']['balance']),
                                                  'class': 'number'},
                                                 {'name': ''}],
                                     'colspan': 4})

                            return_list.append(
                                {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                                 'name': 'Total', 'level': 7,
                                 'style': 'background: #b2b1c7;',
                                 'parent_id': dic_head_f_2['id'],
                                 'columns': [{'name': '', 'class': 'number'},
                                             {'name': self.format_value(line_filter2['total_balance']['debit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter2['total_balance']['credit']),
                                              'class': 'number'},
                                             {'name': self.format_value(line_filter2['total_balance']['balance']),
                                              'class': 'number'},
                                             {'name': ''}],
                                 'colspan': 4})

                        return_list.append(
                            {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                             'name': 'Total', 'level': 5,
                             'style': 'background: #adabd4;',
                             'parent_id': dic_head_f_1['id'],
                             'columns': [{'name': '', 'class': 'number'},
                                         {'name': self.format_value(line_filter1['total_balance']['debit']),
                                          'class': 'number'},
                                         {'name': self.format_value(line_filter1['total_balance']['credit']),
                                          'class': 'number'},
                                         {'name': self.format_value(line_filter1['total_balance']['balance']),
                                          'class': 'number'},
                                         {'name': ''}],
                             'colspan': 4})

                    return_list.append(
                        {'id': 'totals_' + str(count),  # 'class': 'o_account_reports_initial_balance',
                         'name': 'Total Account', 'level': 3,
                         'style': 'background: #b8b5ff; font-weight: bold;',
                         'parent_id': dic_head['id'],
                         'columns': [{'name': '', 'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['debit']),
                                      'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['credit']),
                                      'class': 'number'},
                                     {'name': self.format_value(line['total_balance']['balance']),
                                      'class': 'number'},
                                     {'name': ''}],
                         'colspan': 4})


        return return_list

    def get_xlsx(self, options, response=None):
        if self.auxiliary_wizard_filters():
            generated_file = self.print_xlsx_filters(options,self.auxiliary_wizard_filters())
            return generated_file
        else:
            generated_file = self.print_xlsx_normal(options)
            return generated_file

    def change_structure_lines(self, lines):
        account_delete = []
        col_account = ""
        for line in lines:
            if "title_hover" in line:
                col_account = line.get("name", "")
                index = lines.index(line)
                account_delete.append(index)
            else:
                keys = list(line.keys())
                items = list(line.items())
                i = keys.index("name")
                items.insert(i, ('account', col_account))
                line.clear()
                line.update(dict(items))
        delete = 0
        for index in account_delete:
            lines.pop(index - delete)
            delete = delete + 1
        return lines

    def change_structure_lines_filters(self, lines, colums_filters):
        account_delete = []

        for line in lines:
            if line["level"] == 2:
                col_account = line.get("name", "")
                index = lines.index(line)
                account_delete.append(index)
            else:
                keys = list(line.keys())
                items = list(line.items())
                i = keys.index("name")
                items.insert(i, ('account', col_account))
                line.clear()
                line.update(dict(items))
        delete = 0
        for index in account_delete:
            lines.pop(index - delete)
            delete = delete + 1
        #Clean list delete
        account_delete = []

        col_1 = ""
        col_2 = ""
        col_3 = ""
        """columns filters"""
        for col in colums_filters:
            if col["column"] == "1":
                for line in lines:
                    if line["level"] == 4:
                        col_1 = line.get("name", "")
                        index = lines.index(line)
                        account_delete.append(index)
                    else:
                        if line["level"] == 5 and line["name"] == "Total":
                            keys = list(line.keys())
                            items = list(line.items())
                            i = keys.index("name")
                            items.insert(i, (col["name"], col_1))
                            col_1 = ""
                            line.clear()
                            line.update(dict(items))
                        else:
                            keys = list(line.keys())
                            items = list(line.items())
                            i = keys.index("name")
                            items.insert(i, (col["name"], col_1))
                            line.clear()
                            line.update(dict(items))
                delete = 0
                for index in account_delete:
                    lines.pop(index - delete)
                    delete = delete + 1
                    # Clean list delete
                account_delete = []
            if col["column"] == "2":
                for line in lines:
                    if line["level"] == 6:
                        col_2 = line.get("name", "")
                        index = lines.index(line)
                        account_delete.append(index)
                    else:
                        if line["level"] == 7 and line["name"] == "Total":
                            keys = list(line.keys())
                            items = list(line.items())
                            i = keys.index("name")
                            items.insert(i, (col["name"], col_2))
                            col_2 = ""
                            line.clear()
                            line.update(dict(items))
                        else:
                            keys = list(line.keys())
                            items = list(line.items())
                            i = keys.index("name")
                            items.insert(i, (col["name"], col_2))
                            line.clear()
                            line.update(dict(items))
                delete = 0
                for index in account_delete:
                    lines.pop(index - delete)
                    delete = delete + 1
                    # Clean list delete
                account_delete = []
            if col["column"] == "3":
                for line in lines:
                    if line["level"] == 8:
                        col_3 = line.get("name", "")
                        index = lines.index(line)
                        account_delete.append(index)
                    else:
                        if line["level"] == 9 and line["name"] == "Total":
                            keys = list(line.keys())
                            items = list(line.items())
                            i = keys.index("name")
                            items.insert(i, (col["name"], col_3))
                            col_3 = ""
                            line.clear()
                            line.update(dict(items))
                        else:
                            keys = list(line.keys())
                            items = list(line.items())
                            i = keys.index("name")
                            items.insert(i, (col["name"], col_3))
                            line.clear()
                            line.update(dict(items))
                delete = 0
                for index in account_delete:
                    lines.pop(index - delete)
                    delete = delete + 1
                    # Clean list delete
                account_delete = []

        # Clean list delete
        delete = 0
        for line in lines:
            if line["level"] == 5:
                index = lines.index(line)
                account_delete.append(index)
            if line["level"] == 7:
                index = lines.index(line)
                account_delete.append(index)
            if line["level"] == 9:
                index = lines.index(line)
                account_delete.append(index)
        for index in account_delete:
            lines.pop(index - delete)
            delete = delete + 1
        account_delete = []
        return lines




    def _get_cell_type_value_money(self, cell):
            try:
                type_value = float(cell["name"])
                return ('monetary', cell['name'])
            except:
                return ('text', cell['name'])

    def auxiliary_wizard_filters(self):
        columns = []
        wizard = self.env['report.account.auxiliary.wizard'].search([])[-1]
        if wizard["analytical_account"] != "0":
            name = "Analytical account"
            columns.append({"name": name,
                            "column":wizard["analytical_account"]})
        if wizard["associated"] != "0":
            name =  "Associated"
            columns.append({"name":name,
                            "column": wizard["associated"]})
        if wizard["analytical_tag"] != "0":
            name = "Analytical tag"
            columns.append({"name":name,
                            "column": wizard["analytical_tag"]})

        from operator import itemgetter
        new_columns = sorted(columns, key=itemgetter('column'))

        index = 0
        for column in new_columns:
            index = index + 1
            column["column"] = str(index)

        return new_columns

    def print_xlsx_normal(self, options):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        money_format = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': '$#,##0'})

        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        super_col_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
        level_0_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})

        # Set the first column width to 20
        sheet.set_column(0, 2, 20)
        # Set the first column width to 20
        sheet.set_column(3, 3, 10)

        super_columns = self._get_super_columns(options)
        y_offset = bool(super_columns.get('columns')) and 1 or 0

        sheet.write(y_offset, 0, '', title_style)

        # Todo in master: Try to put this logic elsewhere
        x = super_columns.get('x_offset', 0)
        for super_col in super_columns.get('columns', []):
            cell_content = super_col.get('string', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
            x_merge = super_columns.get('merge')
            if x_merge and x_merge > 1:
                sheet.merge_range(0, x, 0, x + (x_merge - 1), cell_content, super_col_style)
                x += x_merge
            else:
                sheet.write(0, x, cell_content, super_col_style)
                x += 1

        header = self.get_header(options)
        # first column header
        header[0].insert(0, {'name': "Account"})
        # second column header
        header[0][1] = ({'name': "Document"})
        for row in header:
            x = 0
            for column in row:
                colspan = column.get('colspan', 1)
                header_label = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                if colspan == 1:
                    sheet.write(y_offset, x, header_label, title_style)
                else:
                    sheet.merge_range(y_offset, x, y_offset, x + colspan - 1, header_label, title_style)
                x += colspan
            y_offset += 1
        ctx = self._set_context(options)
        ctx.update({'no_format': True, 'print_mode': True, 'prefetch_fields': False})
        # deactivating the prefetching saves ~35% on get_lines running time
        lines = self.with_context(ctx)._get_lines(options)

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        lines = self.change_structure_lines(lines)
        # write all data rows
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = default_style
                col1_style = default_col1_style

            # write the FIRST column, with a specific style to manage the indentation
            sheet.write(y + y_offset, 0, lines[y].get('account'), style)

            # write the SECOND column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 1, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, 1, cell_value, style)

            # write all the remaining cells
            for x in range(2, len(lines[y]['columns']) + 2):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 2])
                cell_type_money, cell_value_money = self._get_cell_type_value_money(lines[y]['columns'][x - 2])

                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value,
                                         date_default_style)
                else:
                    if cell_type_money == "monetary":
                        sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value_money,
                                           money_format)
                    else:
                        sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file

    def print_xlsx_filters(self, options, colums_filters):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        money_format = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': '$#,##0'})

        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        super_col_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
        level_0_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})

        # Set the first and second column width to 20
        sheet.set_column(0, 2, 20)
        # Set the 3 column width to 20
        sheet.set_column(3, 3, 10)

        super_columns = self._get_super_columns(options)
        y_offset = bool(super_columns.get('columns')) and 1 or 0

        sheet.write(y_offset, 0, '', title_style)

        # Todo in master: Try to put this logic elsewhere
        x = super_columns.get('x_offset', 0)
        for super_col in super_columns.get('columns', []):
            cell_content = super_col.get('string', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
            x_merge = super_columns.get('merge')
            if x_merge and x_merge > 1:
                sheet.merge_range(0, x, 0, x + (x_merge - 1), cell_content, super_col_style)
                x += x_merge
            else:
                sheet.write(0, x, cell_content, super_col_style)
                x += 1

        header = self.get_header(options)
        # first column header
        index_header = 0
        header[0].insert(index_header, {'name': "Account"})

        for column in colums_filters:
            index_header = index_header + 1
            header[0].insert(index_header, {'name': column["name"]})
        # second column header
        index_header = index_header + 1
        header[0][index_header] = ({'name': "Document"})
        size_header_fixed = index_header + 1
        lg = self.env.args[2]["lang"][:2]
        for row in header:
            x = 0
            for column in row:
                colspan = column.get('colspan', 1)
                header_label = column.get('name', '')
                traslate = ts.google(header_label,"auto",lg)
                if colspan == 1:
                    sheet.write(y_offset, x, traslate, title_style)
                else:
                    sheet.merge_range(y_offset, x, y_offset, x + colspan - 1, traslate, title_style)
                x += colspan
            y_offset += 1
        ctx = self._set_context(options)
        ctx.update({'no_format': True, 'print_mode': True, 'prefetch_fields': False})
        # deactivating the prefetching saves ~35% on get_lines running time
        lines = self.with_context(ctx)._get_lines(options)

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        lines = self.change_structure_lines_filters(lines, colums_filters)
        # write all data rows
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = default_style
                col1_style = default_col1_style

            index_body = 0
            # write the FIRST column, with a specific style to manage the indentation
            sheet.write(y + y_offset, index_body, lines[y].get('account'), style)

            # write the columns filters

            for column in colums_filters:
                index_body = index_body + 1
                columna = lines[y].get(column.get('name'))
                sheet.write(y + y_offset, index_body,lines[y].get(column.get('name')), style)

            index_body = index_body + 1
            # write the SECOND column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, index_body, cell_value, date_default_col1_style)
                index_body = index_body + 1
            else:
                sheet.write(y + y_offset, index_body, cell_value, style)
                index_body = index_body + 1

            if lines[y]["level"] == 3:
                sheet.merge_range(y + y_offset, 0, y + y_offset, len(colums_filters),lines[y]["account"],style)

            # write all the remaining cells

            for x in range(index_body, len(lines[y]['columns']) + index_body):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - index_body])
                cell_type_money, cell_value_money = self._get_cell_type_value_money(lines[y]['columns'][x - index_body])

                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value,
                                         date_default_style)
                else:
                    if cell_type_money == "monetary":
                        sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value_money,
                                           money_format)
                    else:
                        sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file




