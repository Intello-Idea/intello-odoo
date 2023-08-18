# -*- coding: utf-8 -*-
{
    'name': "custom_event",
    'description': """ Module to customize events """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','website_event','event'],
    'data': [
        'views/templates.xml',
        'views/res_groups.xml'
    ],

    'assets': {
        'web.assets_frontend': [
            'custom_event/static/src/js/custom_event.js',
        ]
    }
}
