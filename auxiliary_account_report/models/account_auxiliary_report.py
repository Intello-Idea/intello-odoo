# -*- coding: utf-8 -*-
import locale
from odoo import models, api, _, fields, exceptions
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta, date
import calendar, math


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
        data = self.movements_according_account(range_date, accounts, analytical)
        lines = self.information_render_report(data)
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

    def movements_according_account(self, range_date, account_obje, analytical_filter):
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
                initial_balance = list(self.env['account.move.line'].search([('date', '<', range_date[0]), ('account_id', '=', account.id), ('parent_state', '=', "posted")]))
                list_move = list(self.env['account.move.line'].search([('date', '>=', range_date[0]), ('date', '<=', range_date[1]), ('account_id', '=', account.id), ('parent_state', '=', "posted")]))
                if len(list_move) > 0:
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
                    initial_balance = list(self.env['account.move.line'].search([('date', '<', range_date[0]), ('account_id', '=', account.id), (analytical_filter[0]['field_name'], '=', filter.id), ('parent_state', '=', "posted")]))
                    list_move = list(self.env['account.move.line'].search([('date', '>=', range_date[0]), ('date', '<=', range_date[1]), ('account_id', '=', account.id), (analytical_filter[0]['field_name'], '=', filter.id), ('parent_state', '=', "posted")]))

                    if len(list_move) > 0:
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
                        initial_balance = list(self.env['account.move.line'].search(
                            [('date', '<', range_date[0]), ('account_id', '=', account.id),
                             (analytical_filter[0]['field_name'], '=', filter1.id), (analytical_filter[1]['field_name'], '=', filter2.id), ('parent_state', '=', "posted")]))
                        list_move = list(self.env['account.move.line'].search(
                            [('date', '>=', range_date[0]), ('date', '<=', range_date[1]), ('account_id', '=', account.id),
                             (analytical_filter[0]['field_name'], '=', filter1.id), (analytical_filter[1]['field_name'], '=', filter2.id), ('parent_state', '=', "posted")]))
                        if len(list_move) > 0:
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
                            initial_balance = list(self.env['account.move.line'].search(
                                [('date', '<', range_date[0]), ('account_id', '=', account.id),
                                 (analytical_filter[0]['field_name'], '=', filter1.id), (analytical_filter[1]['field_name'], '=', filter2.id), (analytical_filter[2]['field_name'], '=', filter3.id), ('parent_state', '=', "posted")]))
                            list_move = list(self.env['account.move.line'].search(
                                [('date', '>=', range_date[0]), ('date', '<=', range_date[1]), ('account_id', '=', account.id),
                                 (analytical_filter[0]['field_name'], '=', filter1.id), (analytical_filter[1]['field_name'], '=', filter2.id), (analytical_filter[2]['field_name'], '=', filter3.id), ('parent_state', '=', "posted")]))
                            if len(list_move) > 0:
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

    def information_render_report(self, data):
        return_list = []

        if data[0]['number_filters'] == 0:
            count = 0
            for line in data:
                count += 1
                dic_head = {'id': "head"+str(line['account'].id),
                       'name': str(line['account'].code) +" "+ str(line['account'].name if len(line['account'].name) < 14 else  line['account'].name[:11]+"..."), 'level': 2,
                       'title_hover': str(line['account'].code) +" "+ str(line['account'].name), 'style': 'background: #b8b5ff; font-weight: bold;',
                       'columns': [{'name': '', 'class': 'number'},
                                   {'name': self.format_value(float(line['total_balance']['debit'])), 'class': 'number'},
                                   {'name': self.format_value(float(line['total_balance']['credit'])), 'class': 'number'},
                                   {'name': self.format_value(float(line['total_balance']['balance'])), 'class': 'number'},
                                   {'name': '', 'class': 'number'}],
                       'unfoldable': True, 'unfolded': True, 'colspan': 4}
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
                                'level': 4, 'name': str(move.name),
                                'columns': [{'name': str(move.journal_id.name)}, {'name': str(move.date), 'class': 'date'},
                                            {'name': str(move.move_id.reverse_entry_id.journal_id.name if move.move_id.reverse_entry_id.journal_id.name != False else "")},
                                            {'name': str(move.move_id.reverse_entry_id.name if move.move_id.reverse_entry_id.name != False else "")},
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

        elif data[0]['number_filters'] == 1:
            count = 0

            for line in data:
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
                            'unfoldable': True, 'unfolded': True, 'colspan': 4}
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
                                'unfoldable': True, 'unfolded': True, 'colspan': 4, 'parent_id': dic_head['id']}
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
                                    'level': 6, 'name': str(move.name),
                                    'columns': [{'name': str(move.journal_id.name)},
                                                {'name': str(move.date), 'class': 'date'},
                                                {'name': str(
                                                    move.move_id.reverse_entry_id.journal_id.name if move.move_id.reverse_entry_id.journal_id.name != False else "")},
                                                {'name': str(
                                                    move.move_id.reverse_entry_id.name if move.move_id.reverse_entry_id.name != False else "")},
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

        elif data[0]['number_filters'] == 2:

            count = 0
            for line in data:
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
                            'unfoldable': True, 'unfolded': True, 'colspan': 4}
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
                                'unfoldable': True, 'unfolded': True, 'colspan': 4, 'parent_id': dic_head['id']}
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
                                        'unfoldable': True, 'unfolded': True, 'colspan': 4, 'parent_id': dic_head_f_1['id']}
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
                                        'level': 8, 'name': str(move.name),
                                        'columns': [{'name': str(move.journal_id.name)},
                                                    {'name': str(move.date), 'class': 'date'},
                                                    {'name': str(
                                                        move.move_id.reverse_entry_id.journal_id.name if move.move_id.reverse_entry_id.journal_id.name != False else "")},
                                                    {'name': str(
                                                        move.move_id.reverse_entry_id.name if move.move_id.reverse_entry_id.name != False else "")},
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

        elif data[0]['number_filters'] == 3:

            count = 0
            for line in data:
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
                            'unfoldable': True, 'unfolded': True, 'colspan': 4}
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
                                'unfoldable': True, 'unfolded': True, 'colspan': 4, 'parent_id': dic_head['id']}
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
                                        'unfoldable': True, 'unfolded': True, 'colspan': 4, 'parent_id': dic_head_f_1['id']}
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
                                            'unfoldable': True, 'unfolded': True, 'colspan': 4,
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
                                            'level': 10, 'name': str(move.name),
                                            'columns': [{'name': str(move.journal_id.name)},
                                                        {'name': str(move.date), 'class': 'date'},
                                                        {'name': str(
                                                            move.move_id.reverse_entry_id.journal_id.name if move.move_id.reverse_entry_id.journal_id.name != False else "")},
                                                        {'name': str(
                                                            move.move_id.reverse_entry_id.name if move.move_id.reverse_entry_id.name != False else "")},
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


        return return_list








