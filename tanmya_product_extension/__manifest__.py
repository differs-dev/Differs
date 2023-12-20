{
    'name': 'ALTANMYA Differs Extension',
    'version': '2.0',
    'summary': 'Add more features for products',
    'description': "",
    'category': 'Inventory/Differs Extension',
    'author': 'ALTANMYA - TECHNOLOGY SOLUTIONS',
    'company': 'ALTANMYA - TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP',
    'website': "http://tech.altanmya.net",
    'depends': ['website','website_sale','stock','sale_management','base',
                'approvals', 'sale_coupon', 'altanmya_firebase_notificator'],
    'data': ['security/ir.model.access.csv',
             'views/views.xml',
             'views/templates.xml',
             'views/product_category.xml',
             'views/sale_order_inherit.xml',
             'views/product_pricelist_views.xml'
            ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'approval_pre_init_hook',
    'sequence': 1
}
