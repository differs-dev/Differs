from odoo import api, fields, models, _
import logging
import re
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    description = fields.Char('Description', translate=True)
    mobile_description = fields.Char('Description for the mobile', sanitize_attributes=False,
                                     translate=True, sanitize_form=False, compute='compute_mobile_desc')
    #     website_description = fields.Char('Description for the website', sanitize_attributes=False,
    #                                       translate=True, sanitize_form=False)

    # Nutrition Value Fields
    calories = fields.Char(string='Calories')
    carbs = fields.Char(string='Carbs')
    protein = fields.Char(string='Protin')
    fat = fields.Char(string='Fat')
    fiber = fields.Char(string='Fiber')
    iron = fields.Char(string='Iron')
    en_name = fields.Char('English Name', compute='compute_name')
    fr_name = fields.Char('Frensh Name', compute='compute_name')

    def compute_name(self):
        for rec in self:
            _logger.info('self.env.user.preferred_language : ')
            _logger.info(rec.id)
            _logger.info(self.env.user.preferred_language)
            # self._cr.execute(f"select src, lang, value from ir_translation WHERE type IN ('model', 'model_terms') AND res_id = {product.id} AND name = 'product.template,name'")
            # names = self._cr.fetchall()
            name_translated = self.env['ir.translation'].search([
            ('name', '=', 'product.template,name'),
            ('res_id', '=', rec.id),
            ('type', 'in', ['model', 'model_terms']),
            ])
            rec.en_name = name_translated.filtered(lambda l: l.lang == 'en_US').value 
            rec.fr_name = name_translated.filtered(lambda l: l.lang == 'fr_FR').value
            _logger.info(rec.en_name)
            _logger.info(rec.fr_name)

    @api.depends('website_description')
    def compute_mobile_desc(self):
        for rec in self:
            soup = BeautifulSoup(str(rec.website_description), 'html.parser')
            # Extract text
            rec.mobile_description = soup.get_text()

    def compute_price_from_pricelist(self, product_id):
        price_list = self.env['product.pricelist'].with_context(lang='en_US').sudo().search([('name', 'like', 'X1.5')])
        product = self.env['product.product'].sudo().search([('product_tmpl_id', '=', product_id)])
        _logger.info(product)
        if product :
            price = price_list.get_product_price(product.product_variant_ids[0], 1, False)
            _logger.info('variant price')
            _logger.info(price)
            return price
        else:
            return 0.0
            
    def compute_variant_price_from_pricelist(self, product_id):
        price_list = self.env['product.pricelist'].with_context(lang='en_US').sudo().search([('name', 'like', 'X1.5')])
        product = self.env['product.product'].sudo().search([('id', '=', product_id)])
        _logger.info(product)
        if product :
            price = price_list.get_product_price(product, 1, False)
            return price
        else:
            return 0.0

    def convert_list_to_string(self, nut_list):
        result = ''
        i = 0
        for char in nut_list:
            if len(result) < 3:
                if i > 0: 
                    result += ',' + char
                else:
                    result += char
                i += 1
        return result

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
        product_variants = self.env['product.product'].with_context(lang=self.env.user.preferred_language).sudo().search([('product_tmpl_id', '=', product_tmpl_id)])
        products_variants_details = []
        if product_variants:
            for product in product_variants:
                price = self.compute_variant_price_from_pricelist(product.id)
                product_variant_details = {
                    'id': product.id,
                    'name': product.name,
                    #                     'image_128': product.image_1920,
                    'image_128': '',
                    # 'list_price': product.lst_price,
                    'list_price': price,
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
    def get_products_templates_details(self, search_word='', category_id=-1, order_by='name',
                                       limit=None, offset=0, is_publish=True):
        search_word1 = search_word.capitalize()
        search_word2 = search_word.lower()
        search_word3 = search_word.upper()
        _logger.info('user lang :::')
        _logger.info(self.env.user.preferred_language)
        if self.env.user.preferred_language == 'fr':
            user_lang = 'fr_FR'
        else:
            user_lang = 'en_US'
        _logger.info('------------------------------=== user lang ===----------------------------------------')
        _logger.info(user_lang)
        _logger.info('search')
        _logger.info(search_word)
        _logger.info(category_id)
        if category_id > 0:
            products = self.env['product.template'].with_context(lang=user_lang).sudo().search(['|', '|', '|',
                                                                   ('name', 'like', search_word),
                                                                   ('name', 'like', search_word1),
                                                                   ('name', 'like', search_word2),
                                                                   ('name', 'like', search_word3),
                                                                   ('categ_id', 'like', category_id),
                                                                   ('is_published', '=', is_publish)],
                                                                  limit=limit,
                                                                  offset=offset,
                                                                  order=order_by)
            _logger.info(products)
            products_details = []
            for product in products:
                prod_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', product.id)], limit=1)
                price1 = self.compute_price_from_pricelist(product.id)
                calories_re = re.findall(r'\d+', str(product.calories))
                if len(calories_re) > 0:
                    calories = self.convert_list_to_string(calories_re)
                else:
                    calories = product.calories
                carbs_re = re.findall(r'\d+', str(product.carbs))
                if len(carbs_re) > 0:
                    carbs = self.convert_list_to_string(carbs_re)
                else:
                    carbs = product.carbs

                protein_re = re.findall(r'\d+', str(product.protein))
                if len(protein_re) > 0:
                    protein = self.convert_list_to_string(protein_re)
                else:
                    protein = product.protein
                    
                fat_re = re.findall(r'\d+', str(product.fat))
                if len(fat_re) > 0:
                    fat = self.convert_list_to_string(fat_re)
                else:
                    fat = product.fat

                fiber_re = re.findall(r'\d+', str(product.fiber))
                if len(fiber_re) > 0:
                    fiber = self.convert_list_to_string(fiber_re)
                else:
                    fiber = product.fiber
                    
                iron_re = re.findall(r'\d+', str(product.iron))
                if len(iron_re) > 0:
                    iron = self.convert_list_to_string(iron_re)
                else:
                    iron = product.iron
                
                product_details = {
                    'id': product.id,
                    'name': product.name,
                    'image_128': product.image_1920,
                    # 'list_price': product.list_price,
                    'list_price': price1,
                    'uom': product.uom_id.name,
                    'calories': calories,
                    'carbs': carbs,
                    'protein': protein,
                    'fat': fat,
                    'fiber': fiber,
                    'iron': iron,
                    'description': product.description,
                    'preference_state': self.get_preference_state(2, product.id),
                    'product_variants': self.get_products_variants_details(product.id),
                    'additional_description': product.mobile_description,
                    'composition': product.x_studio_composition,
                    'conservation_et_utilisation': product.x_studio_conservation_et_utilisation,
                    'product_more_info': product.x_studio_product_more_info
                }
                products_details.append(product_details)

        else:
            products = self.env['product.template'].with_context(lang=user_lang).sudo().search(['|', '|', '|',
                                                                   ('name', 'like', search_word),
                                                                   ('name', 'like', search_word1),
                                                                   ('name', 'like', search_word2),
                                                                   ('name', 'like', search_word3),
                                                                   ('is_published', '=', is_publish)],
                                                                  limit=limit,
                                                                  offset=offset,
                                                                  order=order_by)
            products_details = []
            for product in products:
                prod_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', product.id)], limit=1)
                price1 = self.compute_price_from_pricelist(product.id)
                prod_name = self.env['product.template'].sudo().search_read([('id', '=', product.id)], limit=1)[0]['name']
                self._cr.execute(f"select src, lang, value from ir_translation WHERE type IN ('model', 'model_terms') AND res_id = {product.id} AND name = 'product.template,name'")
                names = self._cr.fetchall()
                if self.env.user.preferred_language == 'fr':
                    product_name = product.fr_name
                else:
                    product_name = product.en_name
                
                calories_re = re.findall(r'\d+', str(product.calories))
                if len(calories_re) > 0:
                    calories = self.convert_list_to_string(calories_re)
                else:
                    calories = product.calories
                carbs_re = re.findall(r'\d+', str(product.carbs))
                if len(carbs_re) > 0:
                    carbs = self.convert_list_to_string(carbs_re)
                else:
                    carbs = product.carbs

                protein_re = re.findall(r'\d+', str(product.protein))
                if len(protein_re) > 0:
                    protein = self.convert_list_to_string(protein_re)
                else:
                    protein = product.protein
                    
                fat_re = re.findall(r'\d+', str(product.fat))
                if len(fat_re) > 0:
                    fat = self.convert_list_to_string(fat_re)
                else:
                    fat = product.fat

                fiber_re = re.findall(r'\d+', str(product.fiber))
                if len(fiber_re) > 0:
                    fiber = self.convert_list_to_string(fiber_re)
                else:
                    fiber = product.fiber
                    
                iron_re = re.findall(r'\d+', str(product.iron))
                if len(iron_re) > 0:
                    iron = self.convert_list_to_string(iron_re)
                else:
                    iron = product.iron
                
                self.env.cr.execute(f"""select name from product_template where id = {product.id}""")
                name = self.env.cr.fetchone()
                
                # calories = re.findall(r'\d+', str(product.calories))
                # carbs = re.findall(r'\d+', str(product.carbs))
                # protein = re.findall(r'\d+', str(product.protein))
                # fat = re.findall(r'\d+', str(product.fat))
                # fiber = re.findall(r'\d+', str(product.fiber))
                # iron = re.findall(r'\d+', str(product.iron))
                product_details = {
                    'id': product.id,
                    'name': product.name,
                    'image_128': product.image_1920,
                    # 'list_price': product.list_price,
                    'list_price': price1,
                    'uom': product.uom_id.name,
                    'calories': calories,
                    'carbs': carbs,
                    'protein': protein,
                    'fat': fat,
                    'fiber': fiber,
                    'iron': iron,
                    'description': product.description,
                    'preference_state': self.get_preference_state(2, product.id),
                    'product_variants': self.get_products_variants_details(product.id),
                    'additional_description': product.mobile_description,
                    'composition': product.x_studio_composition,
                    'conservation_et_utilisation': product.x_studio_conservation_et_utilisation,
                    'product_more_info': product.x_studio_product_more_info
                }
                products_details.append(product_details)
        # _logger.info('--------------------------------- products_details ----------------------------------')
        # _logger.info(products_details)
        return products_details
