# -*- coding: utf-8 -*-
{
    'name': "Base Factura Electronica - Intello Idea",

    'description': 'Base de factura electronica para integrar con diferentes proveedores tecnológicos',
    # Long description of module's purpose

    'summary': 'Base para integración facturacion electronica',
    # Short (1 phrase/line) summary of the module's purpose, used as
    # subtitle on modules listing or apps.openerp.com""",

    'author': "Intello Idea",
    'website': "http://www.intelloidea.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup', 'ln10_co_intello'],
    'application': False,

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/fe_views.xml',
        'views/electronic_document_views.xml',
        'views/res_config_settings_views.xml',
        'views/template_mail_views.xml',
        'views/account_view.xml',
        'report/report_invoice.xml'
    ],

    # only loaded in demonstration mode
    # 'demo': [
    # ],
}