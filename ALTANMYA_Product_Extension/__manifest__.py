# -*- coding: utf-8 -*-
###################################################################################
#
#    ALTANMYA - TECHNOLOGY SOLUTIONS
#    Copyright (C) 2022-TODAY ALTANMYA - TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP.
#    ALTANMYA - Additional Features on Product.
#    Author: ALTANMYA for Technology(<https://tech.altanmya.net>)
#
#    This program is Licensed software: you can not modify
#   #
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'ALTANMYA product extension',
    'version': '0.1',
    'summary': 'Add more features for products',
    'description': "",
    'category': 'Website',
    'author': 'ALTANMYA - TECHNOLOGY SOLUTIONS',
    'company': 'ALTANMYA - TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP',
    'website': "https://www.altanmya.net",
    'depends': ['website','website_sale','stock','sale_management'],
    'data': ['security/ir.model.access.csv','views/views.xml','views/templates.xml'],
    'demo': [],
    'qweb': [],
    # 'assets': {
    #     'web.assets_frontend': [
    #        'tanmya_product_extension/static/src/js/website_sale_ext.js',],},
    'installable': True,
    'auto_install': False,
    'application': False,
}
