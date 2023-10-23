from odoo.tools import partition, collections, frozendict, lazy_property, image_process
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import AccessDenied, UserError, AccessError
from firebase_admin import credentials
from firebase_admin import auth
from odoo.http import request
import firebase_admin
import logging
import time

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    firebase_uid = fields.Char(string='Firebase UserID')
    adults = fields.Integer(string='Adults')
    children = fields.Integer(string='Children')
    pets = fields.Integer(string='Pets')
    firebase_token_ids = fields.One2many('res.users.token', 'user_id')
    last_firebase_token_id = fields.Many2one('res.users.token', compute="_compute_last_token")
    firebase_token = fields.Char(string="Firebase Token", related="last_firebase_token_id.firebase_token")
    firebase_token_expired_date = fields.Date(string="Expire in", related="last_firebase_token_id.firebase_token_expired_date")

    def _compute_last_token(self):
        for record in self:
            last_token = record.env['res.users.token'].sudo().search([
                ('user_id', '=', record.id),
            ], order='create_date desc', limit=1)

            record.last_firebase_token_id = last_token.id

    gluten = fields.Boolean(string='Gluten')
    dairy = fields.Boolean(string='Dairy')
    pork = fields.Boolean(string='Pork')
    pescatarian = fields.Boolean(string='Pescatarian')
    vegetarian = fields.Boolean(string='Vegetarian')
    vegan = fields.Boolean(string='Vegan')

    products_preferences_ids = fields.One2many('products.preferences',
                                               'customer_preferences_id',
                                               string='Products Preferences')
    preferred_language = fields.Char(string='User Language', default='fr')

    def get_recipe_total_rates(self, recipe_id):
        if recipe_id:
            recipe = self.env['product.product'].sudo().search([('id', '=', recipe_id)])
            if recipe:
                if recipe.reviews_ids:
                    total_rates = 0
                    rates_count = len(recipe.reviews_ids)
                    for review in recipe.reviews_ids:
                        total_rates += float(review.rating)
                    if rates_count != 0:
                        return total_rates / rates_count
                    return total_rates
                else:
                    return 0.0


    @api.model
    def add_product_preference(self, variant_template: int, product_id: int, product_status: str):
        # variant_template : the product_id related to product variant or product template
        # 1 for product variant and 2 for product template
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            for preference in user.products_preferences_ids:
                if variant_template == 1:
                    if preference.template_id.id == product_id:
                        preference.write({'status': product_status})
                        return True
                elif variant_template == 2:
                    if preference.template_id.id == product_id:
                        preference.write({'status': product_status})
                        return True
            product_preferences_vals = {}
            if variant_template == 1:
                _logger.info('product id 1')
                _logger.info(product_id)
                product_preferences_vals = {
                    'product_id': product_id,
                    'status': product_status
                }
            elif variant_template == 2:
                _logger.info('product id 2')
                _logger.info(product_id)
                product_preferences_vals = {
                    'template_id': product_id,
                    'product_id': product_id,
                    'status': product_status
                }
            _logger.info('prefernced prod')
            _logger.info(product_preferences_vals)
            product_preference = self.env['products.preferences'].sudo().create(product_preferences_vals)
            _logger.info(product_preference)
            if product_preference:
                user.products_preferences_ids = [(4, product_preference.id)]
                _logger.info('products_preferences_ids ll')
                _logger.info(user.products_preferences_ids)
                return True
        return False

    @api.model
    def update_user_language(self, new_lang, user_id):
        '''
        new_lang param is the lang 'en' or 'fr' that was sent from the caller
        '''
        user = self.env['res.users'].sudo().search([('id', '=', user_id)])
        user.preferred_language = new_lang
        _logger.info('preferred_language ')
        _logger.info(new_lang)
        _logger.info(self.preferred_language)

    @api.model
    def delete_product_preference(self, variant_template: int, product_id: int):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            _logger.info('-------------- dislike product triggered ------------------')
            for line in user.products_preferences_ids:
                if variant_template == 1:
                    if line.product_id.id == product_id:
                        line.unlink()
                        return True
                elif variant_template == 2:
                    if line.template_id.id == product_id:
                        line.unlink()
                        return True
            _logger.info('---------------- product disliked succeessfully ----------------')
        return False

    
    def get_preference_state(self, variant_template, product_id):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        for rec in user.products_preferences_ids:
            if variant_template == 1:
                if rec.product_id.id == product_id:
                    return rec.status
            elif variant_template == 2:
                if rec.template_id.id == product_id:
                    return rec.status
        return 'dislike'

    def get_variant_attributes(self, product_id):
        product = self.env['product.product'].sudo().browse(product_id)
        product_attributes = ''
        if product:
            if product.product_template_attribute_value_ids:
                if len(product.product_template_attribute_value_ids) > 0:
                    product_attributes = product.product_template_attribute_value_ids[0].attribute_id.name + ': ' + \
                                         product.product_template_attribute_value_ids[0].product_attribute_value_id.name
        return product_attributes
    
    def get_products_variants_details(self, product_tmpl_id):
        product_variants = self.env['product.product'].sudo().search([('product_tmpl_id', '=', product_tmpl_id)])
        products_variants_details = []
        if product_variants:
            for product in product_variants:
                product_variant_details = {
                    'id': product.id,
                    'name': product.name,
                    #                     'image_128': product.image_1920,
                    'image_128': '',
                    'list_price': product.lst_price,
                    'uom': product.uom_id.name,
                    'calories': product.calories,
                    'carbs': product.carbs,
                    'protein': product.protein,
                    'fat': product.fat,
                    'fiber': product.fiber,
                    'iron': product.iron,
                    'description': product.description,
                    'preference_state': self.get_preference_state(1, product.id),
                    'additional_description': product.mobile_description,
                    'composition': product.x_studio_composition,
                    'conservation_et_utilisation': product.x_studio_conservation_et_utilisation,
                    'product_more_info': product.x_studio_product_more_info,
                    'product_attributes': self.get_variant_attributes(product.id),
                }
                products_variants_details.append(product_variant_details)
        return products_variants_details
         
    @api.model
    def get_user_preferences(self, products_type: int, limit=None, offset=0):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        user_preferences = []
        if user:
            products_preferences = []
            if products_type == 2:
                products_preferences = self.env['products.preferences'].sudo().search(
                    [('id', 'in', user.products_preferences_ids.ids),
                     ('product_id', '!=', False),
                     ('product_id.kit_template', '!=', None)],
                    limit=limit, offset=offset)
                _logger.info('recipes_preferences are :')
                _logger.info(products_preferences)
                for product_preference in products_preferences:
                    user_preference = {
                        'id': product_preference.product_id.id,
                        # 'image_128': product_preference.product_id.image_1920,
                        'image_1920': product_preference.product_id.image_1920,
                        'image_1920_1': product_preference.product_id.image_1920_1,
                        'image_1920_2': product_preference.product_id.image_1920_2,
                        'name': product_preference.product_id.name,
                        'list_price': product_preference.product_id.list_price,

                        'hours_preparation_time': product_preference.product_id.hours_preparation_time,
                        'minutes_preparation_time': product_preference.product_id.minutes_preparation_time,
                        'difficulty_level': product_preference.product_id.difficulty_level,
                        'instructions': product_preference.product_id.instructions,
                        'description': product_preference.product_id.description,
                        'servings': product_preference.product_id.servings,
                        'calories': product_preference.product_id.calories,
                        'protein': product_preference.product_id.protein,
                        'carbs': product_preference.product_id.carbs,
                        'fat': product_preference.product_id.fat,
                        'fiber': product_preference.product_id.fiber,
                        'iron': product_preference.product_id.iron,
                        'prod_category': product_preference.product_id.prod_category.ids,
                        'reviews_ids': product_preference.product_id.reviews_ids.ids,
                        'owner_id': [product_preference.product_id.owner_id.id, product_preference.product_id.owner_id.name],
                        'total_rates': self.get_recipe_total_rates(product_preference.product_id.id),
                        
                        'uom': product_preference.product_id.uom_id.name,
                        'kit_template': product_preference.product_id.kit_template.id,
                        # 'hours_preparation_time': product_preference.product_id.hours_preparation_time,
                        # 'minutes_preparation_time': product_preference.product_id.minutes_preparation_time,
                        'recipe_status': product_preference.status,
                    }
                    user_preferences.append(user_preference)
                    _logger.info('user_preferences of recipes are ::')
                    _logger.info(user_preferences)
            else:
                products_preferences = self.env['products.preferences'].sudo().search(
                    [('id', 'in', user.products_preferences_ids.ids),
                     # ('template_id', '!=', False)
                    ('product_id.kit_template', '=', None)
                    ],
                    limit=limit, offset=offset)
                _logger.info('products_preferences are :')
                _logger.info(products_preferences)
                for product_preference in products_preferences:
                    _logger.info('product_id : ')
                    _logger.info(product_preference.product_id.id)
                    _logger.info(product_preference.template_id.id)
                    user_preference = {
                        'id': product_preference.product_id.id,
                        'image_128': product_preference.product_id.image_1920,
                        'image_1920': product_preference.product_id.image_1920,
                        'name': product_preference.product_id.name,
                        'list_price': product_preference.product_id.list_price,
                        'uom': product_preference.product_id.uom_id.name,
                        'preference_state': product_preference.status,
                        'calories': product_preference.product_id.calories,
                        'carbs': product_preference.product_id.carbs,
                        'protein': product_preference.product_id.protein,
                        'fat': product_preference.product_id.fat,
                        'fiber': product_preference.product_id.fiber,
                        'iron': product_preference.product_id.iron,
                        'description': product_preference.product_id.description,
                        'product_variants': self.get_products_variants_details(product_preference.product_id.id),
                        'additional_description': product_preference.product_id.mobile_description,
                        'composition': product_preference.product_id.x_studio_composition,
                        'conservation_et_utilisation': product_preference.product_id.x_studio_conservation_et_utilisation,
                        'product_more_info': product_preference.product_id.x_studio_product_more_info,

                    }
                    user_preferences.append(user_preference)
                    _logger.info('user prefs of products are :')
                    _logger.info(user_preferences)
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
            _logger.info('token expiration')
            _logger.info(e)
            return False


    def update_firebase_token(self, user_id, id_token):
        rec = self.env['res.users.token'].sudo().create({'user_id': user_id, 'firebase_token': id_token })  # populated by defaults
        _logger.info('token record ')
        _logger.info(rec)

    @classmethod
    def get_firebase_user(cls, id_token, password):
        with cls.pool.cursor() as cr:
            self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
            # get user with this firebase token
            _logger.info(f"get user with this firebase token")
            _logger.info(id_token)
            db_token = self.env['res.users.token'].sudo().search([('firebase_token', '=', id_token)], limit=1)
            _logger.info('db_token ')
            _logger.info(db_token)
            firebase_user = self.env['res.users'].sudo().browse(db_token.user_id.id)
            _logger.info('firebase user')
            _logger.info(firebase_user)
            # if user exist and token is not expire
            if firebase_user and firebase_user.last_firebase_token_id and firebase_user.last_firebase_token_id.firebase_token_expired_date >= fields.Date.today():
                firebase_user = firebase_user.with_user(firebase_user)
                _logger.info(f"user exist and expire in {firebase_user.firebase_token_expired_date}")
                return firebase_user.login, firebase_user.id
            
            # user not exist or token expired, so check firebase token
            decoded_token = cls.check_firebase_id_token(id_token)
            _logger.info(f"user not exist {firebase_user}")
            try:
                if decoded_token:
                    # get user by firebase user id
                    firebase_user = self.env['res.users'].sudo().search([('firebase_uid', '=', decoded_token['uid'])])
                    if not firebase_user:
                        firebase_user = self.env['res.users'].sudo().search([('login', '=', decoded_token['email'])])
                    _logger.info(f"user by firebase id is {firebase_user}")
                    # user exist, so update token
                    if firebase_user:
                        firebase_user.update_firebase_token(firebase_user.id, id_token)
                        _logger.info(f"update firebase successfully ")
                        return firebase_user.login, firebase_user.id
                    # user not exist, so create one
                    else:
                        _logger.info("fire base user not exist and we create new one ")

                        # existing users modifications :
                        data = password.split(',')
                        _logger.info('data is ')
                        _logger.info(password)
                        _logger.info(password.split('-'))
                        # login = 'anashaidarbakkar@gmail.com'
                        login_1 = ''
                        if len(data) >= 1:
                            login_1 = data[0]
                        _logger.info('/////////////////////// data is ///////////////////////////')
                        _logger.info(data)
                        _logger.info(login_1)
                        existing_user = self.sudo().search([('login', '=', login_1)])
                        _logger.info('existing user')
                        _logger.info(existing_user)
                        if existing_user:
                            _logger.info('it does exist!')
                            firebase_user = existing_user.with_user(existing_user)
                            _logger.info('firebase user')
                            _logger.info(firebase_user)
                            firebase_user.sudo().write({
                                'firebase_uid': decoded_token['uid'],
                                'firebase_token_ids': [(0, 0, {'firebase_token': id_token})],
                            })
                            firebase_user.update_firebase_token(firebase_user.id, id_token)
                            _logger.info('updated info')
                            _logger.info(firebase_user.id)
                            _logger.info(id_token)
                            _logger.info(firebase_user)
                        else:
                            _logger.info('creating new user')
                            vals = self._get_new_user_vals(decoded_token['uid'], decoded_token['email'], password, id_token)
                            _logger.info(vals)
                            firebase_user = self.sudo().create(vals)
                            firebase_user = firebase_user.with_user(firebase_user)
                    
                        return firebase_user.login, firebase_user.id

                return False, False
            except Exception as e:
                _logger.info(e)
                return False, False

    @api.model
    def _get_firebase_user_domain(self, fuid):
        return [('firebase_uid', '=', fuid)]

    @api.model
    def change_password(self, email, new_password):
        _logger.info('change password called')
        _logger.info('email : ')
        _logger.info(email)
        user_id = self.env.user.id
        user_login = self.env.user.login
        if email != '':
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
            cred = credentials.Certificate(cred_info)
            app = None
            try:
                app = firebase_admin.get_app()
            except ValueError:
                app = firebase_admin.initialize_app(cred)
            user = auth.get_user_by_email(email)
            auth.update_user(user.uid, password= new_password)  # Set a new password here
            user = self.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            user_id = user.id
            user_login = user.login
        
        _logger.info(user_id)
        _logger.info(user_login)
        wizard = self.env['change.password.wizard'].sudo().create({})
        _logger.info(wizard)
        change_pw = self.env['change.password.user'].sudo().create({
            'user_id': user_id,
            'user_login': user_login,
            'new_passwd': new_password,
            'wizard_id': wizard.id
        })
        change_pw.change_password_button()
        _logger.info(change_pw)

    @api.model
    def _get_new_user_vals(self, firebase_uid, email, phone_name, token):
        phone_name_list = phone_name.split(',')
        _logger.info('vals with pass')
        _logger.info(phone_name_list)
        phone_parts = ''
        mobile = ''
        if len(phone_name_list) > 0:
            phone_parts = phone_name_list[0].split(' ')
            mobile = phone_name_list[0]
        password = '123'
        if len(phone_name_list) >= 3:
            password = phone_name_list[2]
        name = ''
        if len(phone_name_list) >= 2:
            name = phone_name_list[1]
        phone = ''
        if len(phone_parts) >= 3:
            phone = phone_parts[1] + ' ' + phone_parts[2]
        _logger.info('login is !!')
        _logger.info(email)
        existed = self.env['res.users'].sudo().search([('login', '=', email)])
        _logger.info(existed)
        user_vals = {
            'firebase_uid': firebase_uid,
            'firebase_token_ids': [(0, 0, {'firebase_token': token})],
            'name': name,
            'sel_groups_1_9_10': 9,  # 1 internal, 9 portal and 10 public user
            'login': email,
            'email': email,
            'mobile': mobile,
            'phone': phone,
            'password': password,
            'company_id': 1
        }
        _logger.info('///////////////////////// user values /////////////////////////')
        _logger.info(user_vals)
        return user_vals

    # this method to call before the user logout from the mobile app
    @api.model
    def delete_device_firebase_notification_token(self, firebase_device_token):
        user_firebase_notification_account = self.env['firebase.account'].sudo().search([('user_id', '=', self.env.uid),
                                                                                         ('token', '=',
                                                                                          firebase_device_token)])
        if user_firebase_notification_account:
            user_firebase_notification_account.unlink()

    @api.model
    def set_device_firebase_notification_token(self, firebase_device_token):
        user_firebase_notification_account = self.env['firebase.account'].sudo().search(
            [('token', '=', firebase_device_token),
             ('user_id', '!=', self.env.uid)])

        user_firebase_notification_account1 = self.env['firebase.account'].sudo().search(
            [('user_id', '=', self.env.uid),
             ('token', '=', firebase_device_token)])

        _logger.info('users Y broo!')
        _logger.info(user_firebase_notification_account)
        _logger.info(user_firebase_notification_account1)

        # new editions by anas
        if user_firebase_notification_account1:
            return True
        if user_firebase_notification_account or not user_firebase_notification_account1:
            _logger.info('firebase device token : ')
            _logger.info(user_firebase_notification_account)
            _logger.info(user_firebase_notification_account1)
            if user_firebase_notification_account:
                user_firebase_notification_account.unlink()
            firebase_notification_account_vals = {
                'user_id': self.env.uid,
                'token': firebase_device_token,
            }
            _logger.info('vals for notifications ')
            _logger.info(firebase_notification_account_vals)
            self.env['firebase.account'].sudo().create(firebase_notification_account_vals)
            return True
        return False

    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        try:
            _logger.info(f"authenticate .... {cls} {login}")
            return super(ResUsers, cls).authenticate(db, login, password, user_agent_env)
        except AccessDenied:
            login, user_id = cls.get_firebase_user(login, password)
            _logger.info('-------------------- firebase info -------------------------')
            _logger.info(login)
            _logger.info(user_id)
            if login:
                firebase_user_password = '123'
                if password != '123':
                    firebase_user_password = password
                    _logger.info('new firebase password')
                    _logger.info(firebase_user_password)
                try:
                    _logger.info('try to login 1')
                    return super(ResUsers, cls).authenticate(db, login, firebase_user_password,
                                                            user_agent_env)
                # except Exception as e:
                #     _logger.info('the EXCEPTION')
                #     _logger.info(e)
                #     print(e)
                except AccessDenied:
                    _logger.info('try to login 2')
                    _logger.info( 'AccessDenied Existing User')
                    with cls.pool.cursor() as cr:
                        self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                        _logger.info('token or email')
                        _logger.info(login)
                        existing_user = self.env['res.users'].sudo().search([('login', '=', login)])
                        login1 = login
                        _logger.info(existing_user)
                        self.env.cr.execute(f"""select password from res_users a where a.id = {existing_user.id}""")
                        rr = self.env.cr.fetchall()
                        _logger.info('rr')
                        _logger.info(rr)
                        data = password.split(',')
                        _logger.info('data is ')
                        _logger.info(data)
                        if len(data) > 2:
                            pass_word = data[2]
                            _logger.info('pass word')
                            _logger.info(pass_word)
                        elif len(data) > 1:
                            pass_word = data[1]
                            _logger.info('pass word')
                            _logger.info(pass_word)
                        else:
                            pass_word = '123'
                        user_password = existing_user.password
                        _logger.info(user_password)
                    return super(ResUsers, cls).authenticate(db, login, pass_word,
                                                            user_agent_env)
                    # _logger.info(login)
                    return user_id
            else:
                raise AccessError(_("User authentication failed due to invalid authentication values"))

    @api.model
    def get_user_delivery_methods(self):
        """
        This function is used to get the delivery methods that is related to the user using the zip code
        params : user_zip_code A char representing the user delivery addres zip code
        this function returns a list of delivery methods objects each one is a dictionary.
        """
        _logger.info('User Delivery Methods')
        user_delivery_address = self.get_address_info()
        user_zip_code = ''
        _logger.info('user_delivery_address ')
        _logger.info(user_delivery_address)
        if len(user_delivery_address) >= 1:
            _logger.info('user zip code is ')
            user_zip_code = user_delivery_address[0].get('zip')
            _logger.info(user_zip_code)
        user_delivery_methods = self.env['delivery.carrier'].sudo().search_read([('zip_to', '=', user_zip_code)])
        _logger.info('------------------- user delivery methods ----------------------')
        _logger.info(user_delivery_methods)
        return user_delivery_methods
    
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
        _logger.info('--------------------------- address info ---------------------------------')
        _logger.info(user)
        if user:
            address_info = {
                'id': -1,
                'zip': user.partner_id.zip,
                'country': user.partner_id.country_id.name,
                'city': user.partner_id.city,
                'address_title': user.partner_id.address_title,
                'building_name': user.partner_id.building_name,
                'apartment_name': user.partner_id.apartment_name,
                'street': user.partner_id.street,
                'partner_latitude': user.partner_id.partner_latitude,
                'partner_longitude': user.partner_id.partner_longitude,
                'phone': user.partner_id.phone
            }
            address_info_list.append(address_info)
            _logger.info('address_info_list  ')
            _logger.info(address_info_list)
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
        @return: new_address.id if address added
                 Fals if not
        """
        if address_vals:
            if address_vals.get('country', False):
                country_id = self.env['res.country'].sudo().search([('name', '=', address_vals.get('country'))]).id
                address_vals['country_id'] = country_id
                del address_vals['country']

            new_address = self.env['additional.address'].sudo().create(address_vals)
            if new_address:
                user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
                user.partner_id.address_ids = [(4, new_address.id)]
                return new_address.id
        return False

    def search_in_address(self, address_vals, search_word):
        search_word1 = search_word.capitalize()
        search_word2 = search_word.lower()
        search_word3 = search_word.upper()
        result = False
        for key, val in address_vals.items():
            if key != 'id' and key != 'partner_latitude' and key != 'partner_longitude':
                if search_word in str(val) or search_word1 in str(val) or search_word2 in str(
                        val) or search_word3 in str(
                    val):
                    result = True
                    break
        return result

    @api.model
    def get_addresses_details(self, search_word=''):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        address_info = False
        addresses_info_list = self.get_address_info()
        _logger.info('addresses are')
        _logger.info(addresses_info_list)
        _logger.info(user.partner_id.address_ids)
        # self.get_user_delivery_methods()
        if user:
            for address in user.partner_id.address_ids:
                address_info = {
                    'id': address.id,
                    'zip': address.zip,
                    'city': address.city,
                    'country': address.country_id.name,
                    'phone': address.phone,
                    'address_title': address.address_title,
                    'building_name': address.building_name,
                    'apartment_name': address.apartment_name,
                    'street': address.street,
                    'partner_latitude': address.partner_latitude,
                    'partner_longitude': address.partner_longitude
                }
                addresses_info_list.append(address_info)
            _logger.info(addresses_info_list)

            if search_word and search_word != '':
                target_addresses = []
                for address in addresses_info_list:
                    if self.search_in_address(address, search_word):
                        target_addresses.append(address)
                return target_addresses
        return addresses_info_list

    @api.model
    def get_address_details(self):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user.partner_id.main_address_id == -1:
            address = self.get_address_info()
            _logger.info('address info 22')
            _logger.info(address)
            return address

        elif user.partner_id.main_address_id == -2:
            address_info = {
                'id': -2,
                'zip': '',
                'city': '',
                'country': '',
                'phone': '',
                'address_title': '',
                'building_name': '',
                'apartment_name': '',
                'street': '',
                'partner_latitude': 0.0,
                'partner_longitude': 0.0
            }
            return [address_info]

        else:
            address = self.env['additional.address'].sudo().search([('id', '=', user.partner_id.main_address_id)])
            address_info = {
                'id': address.id,
                'zip': address.zip,
                'city': address.city,
                'country': address.country_id.name,
                'phone': address.phone,
                'address_title': address.address_title,
                'building_name': address.building_name,
                'apartment_name': address.apartment_name,
                'street': address.street,
                'partner_latitude': address.partner_latitude,
                'partner_longitude': address.partner_longitude
            }
            return [address_info]

    @api.model
    def update_address_info(self, address_id, vals):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        _logger.info('---------------------- update address info ---------------------------------')
        _logger.info(user)
        # address_id = user.partner_id.main_address_id
        _logger.info('reached here')
        if vals.get('country', False):
            _logger.info('before exiting the function')
            country_id = self.env['res.country'].sudo().search([('name', '=', vals.get('country'))]).id
            vals['country_id'] = country_id
            del vals['country']
        if address_id == -1:
            _logger.info(vals, address_id)
            _logger.info('done writing the vals of -1')
            _logger.info(vals)
            user.write(vals)
            return True
        else:
            address = self.env['additional.address'].sudo().search([('id', '=', address_id)])
            _logger.info('done writing the vals of else')
            _logger.info(vals)
            address.write(vals)
            return True

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

    @api.model
    def set_main_address_id(self, address_id):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        user.write({'main_address_id': address_id})

    @api.model
    def cancel_main_address(self, address_id):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user.main_address_id == address_id:
            user.write({'main_address_id': -2})

    @api.model
    def delete_address(self, address_id):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if address_id == -1:
            address_vals = {
                'zip': None,
                'city': None,
                'country_id': None,
                'mobile': None,
                'address_title': None,
                'building_name': None,
                'apartment_name': None,
                'street': None,
                'partner_latitude': None,
                'partner_longitude': None
            }
            user.write(address_vals)
        else:
            address = self.env['additional.address'].sudo().search([('id', '=', address_id)])
            address.unlink()

    @api.model
    def delete_user_account(self):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        request.session.logout(keep_db=True)
        query = f"""DELETE from res_users where id = {self.env.uid};"""
        self._cr.execute(query)

class ResUsersToken(models.Model):
    _name = 'res.users.token'

    user_id = fields.Many2one('res.users', string='User', ondelete='cascade')

    firebase_token = fields.Char(string="Firebase Token")
    firebase_token_expired_date = fields.Date(string="Expire in", default=lambda self: fields.Date.add(fields.Date.today(), days=3))

class ResPartner(models.Model):
    _inherit = 'res.partner'

    address_title = fields.Char(string='Address Title')
    building_name = fields.Char(string='Building Name')
    apartment_name = fields.Char(string='Apartment Name')
    address_ids = fields.One2many('additional.address', 'partner_id', string='Partner Addresses')
    main_address_id = fields.Integer(string='Main Address ID', default=-1)


class AdditionalAddress(models.Model):
    _name = 'additional.address'

    partner_id = fields.Many2one('res.partner', string='Partner ID')
    address_title = fields.Char(string='Address Title')
    building_name = fields.Char(string='Building Name')
    apartment_name = fields.Char(string='Apartment Name')
    street = fields.Char(string='Street Name')
    partner_latitude = fields.Float(string='Latitude')
    partner_longitude = fields.Float(string='Longitude')
    zip = fields.Char(string='ZIP Code')
    country_id = fields.Many2one('res.country', string='Country')
    city = fields.Char(string='City')
    phone = fields.Char(string='Phone Number')

    def name_get(self):
        result = []
        for address in self:
            result.append((address.id, address.address_title))
        return result
