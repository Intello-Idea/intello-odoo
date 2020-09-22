# -*- coding: utf-8 -*-
{
    'name': "Colombian Location - Intello",

    'description': 'Adjust Colombian Location, to have complete definitions that we need to send e-invoice with DIAN.',
    # Long description of module's purpose

    'summary': 'Adjust Colombian Location',
    # Short (1 phrase/line) summary of the module's purpose, used as
    # subtitle on modules listing or apps.openerp.com""",

    'author': "Intello Idea",
    'website': "http://www.intelloidea.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_address_city', 'l10n_co', 'auxiliary_account_report',
                'translate_account','sale', 'extend_expense'],
    'application': True,

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/accounting.book.csv',
        'data/ln10_co_intello.diancodes.csv',
        'data/ln10_co_intello.ciiucodes.csv',
        'data/ln10_co_intello.nomenclaturedian.csv',
        'data/ln10_co_intello.taxestype.csv',
        'data/ln10co_document_type.xml',
        'data/res.country.state.csv',
        'data/res.city.csv',

        'views/ln10co_intello.xml',
        'views/res_partner.xml',
        'views/account_view.xml',
        'views/uom_uom_views.xml',
        'views/res_company.xml',
        'views/res_country_views.xml',
        'views/res_city_view.xml',
        'views/accounting_book_views.xml',
        'data/accounting_book.xml',
        'views/product_template_view.xml',
        'views/res_lang_views.xml',
        'views/res_currency_views.xml',
        'views/product_pricelist_view.xml',
        'wizard/account_filter_option_wizard_views.xml',
        'wizard/account_print_journal_wizard.xml',
        'wizard/book_report_wizard.xml',
        'views/res_config_settings.xml',
        'wizard/account_move_reversal_view.xml',
        'report/report_invoice.xml'
    ],

    # only loaded in demonstration mode
    # 'demo': [
    # ],
}
