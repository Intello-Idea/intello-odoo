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
    'depends': ['base', 'base_address_city', 'l10n_co'],
    'application': True,

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/library_menu.xml',
        'data/ln10co_document_type.xml',
        'data/ln10_co_intello.diancodes.csv',
        'data/ln10_co_intello.ciiucodes.csv',
        # 'data/ln10co_person_type.xml',
        # 'data/ln10co_fiscal_regime.xml',
        # 'data/ln10co_fiscal_responsibility.xml',
        'views/ln10co_intello.xml',
        'views/res_partner.xml',
    ],

    # only loaded in demonstration mode
    # 'demo': [
    # ],
}