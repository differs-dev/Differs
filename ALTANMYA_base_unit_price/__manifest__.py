# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'ALTANMYA Base Price Unit',
    'version': '1.0',
    'category': '',
    'summary': 'Base Price Unit',
    'depends': ['website', 'website_sale', 'portal'],
    'author': 'ALTANMYA - TECHNOLOGY SOLUTIONS',
    'company': 'ALTANMYA - TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP',
    'website': "http://tech.altanmya.net",
    'data': [
        'views/product_item_base_unit_price.xml',
        'views/website_cookies.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ALTANMYA_base_unit_price/static/src/js/website_cookies.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
