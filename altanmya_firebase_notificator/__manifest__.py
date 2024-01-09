{
    'name': 'ALTANMYA Firebase Notificator',
    'version': '1.0',
    'summary': 'Sending push notification to any mobile user (Android, IOS)',
    'description': "Sending push notification to any mobile user (Android, IOS).",
    'category': 'Mail',
    'author': 'ALTANMYA - TECHNOLOGY SOLUTIONS',
    'company': 'ALTANMYA - TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP',
    'website': "http://tech.altanmya.net",
    'depends': ['base', 'web', 'mail', 'stock'],
    'data': [
            'security/ir.model.access.csv',
            'views/notification_views.xml',
            'views/settings_views.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': -100,
}
