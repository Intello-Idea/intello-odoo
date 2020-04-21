# -*- coding: utf-8 -*-
{
    'name': "Auxiliary Account Report",

    'description': 'Reporte auxiliar de cuentas contables con agrupaciones analiticas',
    # Long description of module's purpose

    'summary': 'Reporte auxiliar de cuentas',
    # Short (1 phrase/line) summary of the module's purpose, used as
    # subtitle on modules listing or apps.openerp.com""",

    'author': "Intello Idea",
    'website': "http://www.intelloidea.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting &amp; Finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_reports'],
    'application': False,

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/account_financial_report_data.xml',
        'wizard/account_filter_option_wizard_views.xml'

    ],

    # only loaded in demonstration mode
    # 'demo': [
    # ],
}