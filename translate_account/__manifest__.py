{
    'name': 'Translate Account',
    'summary': 'Translate',
    'version': '0.1',
    'license': 'AGPL-3',
    'description': """
    
""",
    'category': 'Module',
    'author': "Intello Idea",
    'website': "http://www.intelloidea.com",
    'depends': ["base", "account"],
    'data': ['security/ir.model.access.csv',
             'data/base_language_import_data.xml',
             'views/translate_account_view.xml',
             ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=2:softtabstop=2:shiftwidth=2:
