{
    'name': 'Altanmya product extension 2',
    'version': '2',
    'summary': 'Add more features for products',
    'description': "",
    'category': 'Website',
    'author': 'Altanmya',
    'company': 'Altanmya',
    'website': "https://www.altanmya.net",
    'depends': ['website','website_sale','stock','sale_management','base'],
    'data': ['security/ir.model.access.csv',
             'views/views.xml',
             'views/templates.xml',
             'views/product_category.xml'
            ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'approval_pre_init_hook'
}
