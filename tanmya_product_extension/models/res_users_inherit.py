from odoo.tools import partition, collections, frozendict, lazy_property, image_process
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import AccessDenied, UserError, AccessError
from firebase_admin import credentials
from firebase_admin import auth
import firebase_admin
import logging
import time


logger = logging.getLogger('odoo.log')
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    firebase_uid = fields.Char(string='Firebase UserID')
    adults = fields.Integer(string='Adults')
    children = fields.Integer(string='Children')
    pets = fields.Integer(string='Pets')

    gluten = fields.Boolean(string='Gluten')
    dairy = fields.Boolean(string='Dairy')
    pork = fields.Boolean(string='Pork')
    pescatarian = fields.Boolean(string='Pescatarian')
    vegetarian = fields.Boolean(string='Vegetarian')
    vegan = fields.Boolean(string='Vegan')

    products_preferences_ids = fields.One2many('products.preferences',
                                               'customer_preferences_id',
                                               string='Products Preferences')

    @api.model
    def add_product_preference(self, product_id: int, product_status: str):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            for preference in user.products_preferences_ids:
                if preference.product_id.id == product_id:
                    preference.write({'status': product_status})
                    return True

            products_preferences_vals = {
                'product_id': product_id,
                'status': product_status
            }
            product_preference = self.env['products.preferences'].sudo().create(products_preferences_vals)
            if product_preference:
                user.products_preferences_ids = [(4, product_preference.id)]
                return True
        return False

    @api.model
    def delete_product_preference(self, product_id: int):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            for line in user.products_preferences_ids:
                if line.product_id.id == product_id:
                    line.unlink()
                    return True
        return False

    @api.model
    def get_user_preferences(self, products_type: int):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        user_preferences = []
        if user:
            products_preferences = []
            if products_type == 2:
                products_preferences = self.env['products.preferences'].sudo().search(
                    [('id', 'in', user.products_preferences_ids.ids),
                     ('product_id.kit_template', '!=', None)])
            else:
                products_preferences = self.env['products.preferences'].sudo().search(
                    [('id', 'in', user.products_preferences_ids.ids),
                     ('product_id.kit_template', '=', None)])

            for product_preference in products_preferences:
                user_preference = {
                    'id': product_preference.product_id.id,
                    'image_128': product_preference.product_id.image_128,
                    'image_1920': product_preference.product_id.image_1920,
                    'name': product_preference.product_id.name,
                    'price': product_preference.product_id.list_price,
                    'uom': product_preference.product_id.uom_id.name,
                    'kit_template': product_preference.product_id.kit_template.id,
                    'hours_preparation_time': product_preference.product_id.hours_preparation_time,
                    'minutes_preparation_time': product_preference.product_id.minutes_preparation_time,
                    'preference_status': product_preference.status,
                }
                user_preferences.append(user_preference)

        return user_preferences

    @classmethod
    def check_firebase_id_token(cls, id_token):
        cred_info = {
            "type": "service_account",
            "project_id": "differs-2d6ab",
            "private_key_id": "1bef2dff29a2296f3134c8b291743c9249b7cd81",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDEx7KWK4XsA41A\n0Oan8yMmPf6/77eTti73/Ma1dZRLcUyt1ebOM1h07qE8rWZu2h3MHKJcN0A3MDxj\nLznAOljWrs+BgFcx4swv4+rJJGJHQVb2hjnFNpD/SZpU1zCqOLM5UCe70yWR9hAw\n9nmRH1euah6MbiSLl0MO463x0hShK89LxTP0Mn0bsEGTJb8R+iVv/Nc8hNBqGqpz\nMVxJrYFT76SLfwk6GpPqsXZ7kMjHrdL0UEyRCrtfdzOg9BCdrsmL5dL6jOuEahSQ\nwAqrgrFG+sidk+I1f6/gP7Sq81CCrYz19aCq0TVzmmFsDygiVs6mcwYW9YM3MjtQ\n8eF/TYnFAgMBAAECggEAF6qU1e7CGpKKyILXWtepII5QNzFTeNZua7DhDS3o+fHU\ncQvKyH3wY4/XoH6SVT6yWrwO4txaQsjwWlVxsqbRzHAV0NNoqT1HpXLZ5/sSPtOi\n699Uz10yryFhCFchKTfMhlYXkUVhvV5EsD7UfBmy5+0nY2hTyN4WWJIVd4H2rTNr\ncTUiarjFJeTDejn1ev0dZ5ydf0Ehxy8zpry/miV4ib11ThTBDV1eNb+tPFQLSrV4\nnX8Tr41q//n16WdaVuvh51fzMRFPHPWtvm6SSmwmFCmGVlBeNJp5/WZRun0YgzgY\nicZWCc0NY52LYxVRrKbYBQCqne33j8FGqFF2Yf8++QKBgQD2JSV6v7m1uG6N+TXy\nHh/ut5aAl0XofFBnrOvnxKdtuvQoagkuwA9W9mSdRM0y+IcRjLVRtvv9YYGUJCG6\nlM0BkMmWMNX3xwu80amsZng/0J45NLNYk6EWbPCudKc4Do77u3nlHrkWtdaAnyfB\nSSwOW9dJxcl6gpUfnhx3N0FozwKBgQDMqJYfMaPZrzIRLIAlp5J8uLlRpd/39pey\nPqAwzd81mKhelve7niWf+qt15IznHMBnRr8fiF6OyYHOaHLbH//1vI90rxDIiKlp\nWLP/h0ioJaGo0ER9x0NlKcQbbVrfmuEwkzAP/QVfnN2y62lLHLTlMVE9sb7rvkPo\nQ9D5qV3hKwKBgECp95OsxJvxzNFtc/ecZGUxQ8+abhoqdnEWI49qwVV5dOUdHjZy\n7FS7PCl4xrOqSMmafpPuD3s8X29MorPCnazYnazgPYXve6zqI7oP3W1eYALFToxp\nlDsw+XXLXZbDdFq7oMVJcfR+ZtC5fxcvIuzOwds2o7yUi5qXzgCfuoZPAoGAKOPO\nCrF6UTXlxPSlLeDLLcwiiqOfmgVUzbIhg16+qBC2Ix/6oyu3zLzioQ1m8Y4XCwth\niEVQzyqHmtvXhtxf4ZMo/mEz8z0KzBeC7xzycVYDdJ0X8iFr37x2iBxTObXSJEhk\nI+2jszS+Ps82HGHB6sDtwGvQ/3zmSHO0Pw2Nyj0CgYEAk2jcds2AemRJtqHW/74p\nDxWgwQl1OsjdLk02Egn9/RRcaubIx2Ud2SsQ+AT4MOGC3USfamIglXgxWVBYwe1Y\nVB/ElGnkz/GijLWnUtjXCXkxPSRtjVLegipZurE5ksu+pajYRm7SSOGIpUkpc4h6\nLKal9qhFZVyLHOVYpwmlVWw=\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-tx29x@differs-2d6ab.iam.gserviceaccount.com",
            "client_id": "104484343744146204081",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-tx29x%40differs-2d6ab.iam.gserviceaccount.com"
        }
        try:
            cred = credentials.Certificate(cred_info)
            app = None
            try:
                app = firebase_admin.get_app()
            except ValueError:
                app = firebase_admin.initialize_app(cred)

            decoded_token = auth.verify_id_token(id_token, app=app)
            if decoded_token:
                return decoded_token
            return False

        except Exception as e:
            logger.info(e)
            return False

    @classmethod
    def get_firebase_user(cls, id_token):
        decoded_token = cls.check_firebase_id_token(id_token)
        try:
            if decoded_token:
                firebase_uid = decoded_token['uid']
                firebase_user = auth.get_user(firebase_uid)
                return firebase_user
            return False
        except Exception as e:
            logger.info(e)
            return False

    @api.model
    def _get_firebase_user_domain(self, fuid):
        return [('firebase_uid', '=', fuid)]

    @api.model
    def _get_new_user_vals(self, firebase_uid, email, phone_name):
        phone_name_list = phone_name.split(',')
        phone_parts = phone_name_list[0].split(' ')
        user_vals = {
            'firebase_uid': firebase_uid,
            'name': phone_name_list[1],
            'sel_groups_1_9_10': 9,   # 1 internal, 9 portal and 10 public user
            'login': email,
            'email': email,
            'mobile': phone_name_list[0],
            'phone': phone_parts[1] + ' ' + phone_parts[2],
            'password': '123',
            'company_id': 1
        }
        return user_vals

    def time_convert(self, sec):
        mins = sec // 60
        sec = sec % 60
        hours = mins // 60
        mins = mins % 60
        return "Time Lapsed = {0}:{1}:{2}".format(int(hours), int(mins), sec)

    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        tic = time.time()
        try:
            return super(ResUsers, cls).authenticate(db, login, password, user_agent_env)

        except AccessDenied:
            firebase_user = cls.get_firebase_user(login)
            if firebase_user:
                # logger.info('#############')
                firebase_user_password = '123'
                user = False
                with cls.pool.cursor() as cr:
                    self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                    user = self.sudo().search(self._get_firebase_user_domain(firebase_user.uid), limit=1)
                    user = user.with_user(user)
                    if user:
                        try:
                            auth_res = super(ResUsers, cls).authenticate(db, user.login, firebase_user_password,
                                                                         user_agent_env)
                            return auth_res
                        except AccessDenied:
                            _logger.info('-------------------------Existing User----------------------------')
                            _logger.info(db)
                            _logger.info(user.login)
                            _logger.info(firebase_user_password)
                            _logger.info(user_agent_env)
                            _logger.info('------------------------------------------------------------------')
                    else:
                        vals = self._get_new_user_vals(firebase_user.uid, firebase_user.email, password)
                        new_user = self.sudo().create(vals)
                        new_user = user.with_user(new_user)
                        if new_user:
                            try:
                                auth_res = super(ResUsers, cls).authenticate(db, new_user.login, firebase_user_password,
                                                                             user_agent_env)
                                return auth_res
                            except AccessDenied:
                                _logger.info('-------------------------New User----------------------------')
                                _logger.info(db)
                                _logger.info(new_user.login)
                                _logger.info(firebase_user_password)
                                _logger.info(user_agent_env)
                                _logger.info('------------------------------------------------------------------')
            else:
                raise AccessError(_("User authentication failed due to invalid authentication values"))

#         finally:
#             toc = time.time()
#             tic_toc = self.time_convert(toc - tic)
#             _logger.info('---------------------------------------------------------')
#             _logger.info("Authentication execution time is: ")
#             _logger.info(tic_toc)
#             _logger.info('---------------------------------------------------------')

    @api.model
    def set_address_info(self, vals):
        uid = self.env.uid
        user = self.env['res.users'].sudo().search([('id', '=', uid)])
        if user:
            if vals.get('country', False):
                country_id = self.env['res.country'].sudo().search([('name', '=', vals.get('country'))]).id
                vals['country_id'] = country_id
                del vals['country']
            user.write(vals)
            return True
        return False

    @api.model
    def get_address_info(self):
        uid = self.env.uid
        user = self.env['res.users'].sudo().search([('id', '=', uid)])
        address_info = False
        address_info_list = []
        if user:
            address_info = {
                'zip': user.partner_id.zip,
                'country': user.partner_id.country_id.name,
                'city': user.partner_id.city,
                'address_title': user.partner_id.address_title,
                'building_name': user.partner_id.building_name,
                'apartment_name': user.partner_id.apartment_name,
                'street': user.partner_id.street,
                'partner_latitude': user.partner_id.partner_latitude,
                'partner_longitude': user.partner_id.partner_longitude
            }
            address_info_list.append(address_info)
        return address_info_list

    @api.model
    def add_new_address(self, address_vals):
        """
        @param address_vals:
        {
            'address_title': 'address_title',
            'building_name': 'building_name',
            'apartment_name': 'apartment_name',
            'partner_latitude': 'partner_latitude',
            'partner_longitude': 'partner_longitude'
        }
        @return: True if address added
                 Fals if not
        """
        if address_vals:
            new_address = self.env['additional.address'].sudo().create(address_vals)
            if new_address:
                user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
                user.partner_id.address_ids = [(4, new_address.id)]
                return True
        return False

    @api.model
    def get_addresses_details(self):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        address_info = False
        addresses_info_list = self.get_address_info()
        if user:
            for address in user.partner_id.address_ids:
                address_info = {
                    'address_title': address.address_title,
                    'building_name': address.building_name,
                    'apartment_name': address.apartment_name,
                    'street': address.street,
                    'partner_latitude': address.latitude,
                    'partner_longitude': address.longitude
                }
                addresses_info_list.append(address_info)
        return addresses_info_list

    @api.model
    def update_user_info(self, new_vals):
        # new_vals = {
        #     'name': 'new_name',
        #     'login': 'new_email',
        #     'email': 'new_email',
        #     'phone': 'new_phone',
        #     'image_1920': 'imoage_1920' }
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            # user.sudo().write(new_vals)
            user.write(new_vals)
            return True
        return False


class ResPartner(models.Model):
    _inherit = 'res.partner'

    address_title = fields.Char(string='Address Title')
    building_name = fields.Char(string='Building Name')
    apartment_name = fields.Char(string='Apartment Name')

    address_ids = fields.One2many('additional.address', 'partner_id', string='Partner Addresses')


class AdditionalAddress(models.Model):
    _name = 'additional.address'

    partner_id = fields.Many2one('res.partner', string='Partner ID')
    address_title = fields.Char(string='Address Title')
    building_name = fields.Char(string='Building Name')
    apartment_name = fields.Char(string='Apartment Name')
    street = fields.Char(string='Street Name')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
