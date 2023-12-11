# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'ALTANMYA DIFFERS INVOICE REPORT',
    'version': '1.0',
    'sequence': -100,
    'category': 'ALTANMYA DIFFERS INVOICE REPORT',
    'depends': ['account', 'base'],
    'data': [
        'view/res_company_inherit_view.xml',
        'reports/invoice_report.xml',
        'reports/report_action.xml',

    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
