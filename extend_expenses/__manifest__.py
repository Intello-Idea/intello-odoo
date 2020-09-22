{
    'name': "Expense Extended",
    'summary': """Expense extended for intello idea""",
    'description': """
        Module for Expense and plus for location colombia
    """,
    'author': "Intello Idea SAS",
    'website': "http://intelloidea.com/",
    'category': 'Accounting',
    'version': '1.0',

    'depends': ['base', 'hr_expense'],
    'data': ['views/inherit_hr_expense_views.xml', 'views/res_config_settings_view.xml',
             ]
}
