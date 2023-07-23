from datetime import date, datetime, timedelta
from odoo import api, fields, models, tools
import logging
from odoo.exceptions import ValidationError
import time
import base64

_logger = logging.getLogger(__name__)


class Tanmyaprodcategory(models.Model):
    _name = "tanmya.product.category"

    name = fields.Char(string='Category name')
    image = fields.Image(string='Image')
    publish = fields.Boolean(string='Publish')
    type = fields.Selection([('by_ingredients', 'By Ingredients'),
                             ('by_cuisine', 'By Cuisine')],
                            string='Category Type',
                            default='by_ingredients')

    @api.model
    def get_categories_by_ingredients(self, search_word='', limit=None, offset=0):
        categories = False
        categories_by_ing = []
        categories = self.env['tanmya.product.category'].sudo().search(
            [('type', 'in', ['by_ingredients', 'by_cuisine'])],
            limit=limit,
            offset=offset)
        categories_details = []
        _logger.info('---------------------------------------- search word ----------------------------------------------')
        _logger.info(search_word)
        _logger.info(search_word.capitalize())
        _logger.info(search_word.upper())
        _logger.info(search_word.lower())
        for ca_type in categories:
            if ca_type.type == 'by_ingredients':
                if search_word == '':
                    categories_by_ing = self.env['tanmya.product.category'].sudo().search(
                        [('type', '=', 'by_ingredients')],
                        limit=limit,
                        offset=offset)
                else:
                    # categories_by_ing = self.env['tanmya.product.category'].sudo().search(
                    #     ['|', '|', '|','&',
                    #      ('name', 'like', search_word),
                    #      ('name', 'like', search_word.capitalize()),
                    #      ('name', 'like', search_word.upper()),
                    #      ('name', 'like', search_word.lower()),
                    #      ('type', '=', 'by_ingredients')],
                    #     limit=limit,
                    #     offset=offset)
                    query = f"""select  id from tanmya_product_category where name like '%{search_word}%' and type = 'by_ingredients' ;"""
                    self.env.cr.execute(query)
                    categories_by_ing = self.env.cr.dictfetchall()
                    categories_ids = []
                    for cat in categories_by_ing:
                        categories_ids.append(cat['id'])
                    _logger.info('--------------------------ids------------------------------')
                    _logger.info(categories_ids)
                    categories_by_ing = self.env['tanmya.product.category'].sudo().search(
                        [('id', 'in', categories_ids)],
                        limit=limit,
                        offset=offset)
                    _logger.info(categories_by_ing)

        if categories_by_ing:
            for category in categories_by_ing:
                category_details = {
                    'id': category.id,
                    'name': category.name,
                    'image': category.image
                }
                categories_details.append(category_details)
        else:
            return categories_details
        return categories_details

    @api.model
    def get_categories_by_cuisine(self, search_word='', limit=None, offset=0):
        categories = False
        categories_by_cui = []
        categories = self.env['tanmya.product.category'].sudo().search(
            [('type', 'in', ['by_ingredients', 'by_cuisine'])],
            limit=limit,
            offset=offset)
        categories_details = []
        for ca_type in categories:
            if ca_type.type == 'by_cuisine':
                if search_word == '':
                    categories_by_cui = self.env['tanmya.product.category'].sudo().search(
                        [('type', '=', 'by_cuisine')],
                        limit=limit,
                        offset=offset)
                else:
                    categories_by_cui = self.env['tanmya.product.category'].sudo().search(
                        ['|', '|', '|', '&',
                         ('name', 'like', search_word),
                         ('name', 'like', search_word.capitalize()),
                         ('name', 'like', search_word.upper()),
                         ('name', 'like', search_word.lower()),
                         ('type', '=', 'by_cuisine')],
                        limit=limit,
                        offset=offset)

        if categories_by_cui:
            for category in categories_by_cui:
                category_details = {
                    'id': category.id,
                    'name': category.name,
                    'image': category.image
                }
                categories_details.append(category_details)
        else:
            return categories_details

        return categories_details

    @api.model
    def get_categories_details(self, search_word='', limit=None, offset=0):
        categories = False
        if search_word == '':
            categories = self.env['tanmya.product.category'].sudo().search([],
                                                                           limit=limit,
                                                                           offset=offset)
            _logger.info(categories)
        else:
            categories = self.env['tanmya.product.category'].sudo().search(['|', '|', '|',
                                                                            ('name', 'like', search_word),
                                                                            ('name', 'like', search_word.capitalize()),
                                                                            ('name', 'like', search_word.upper()),
                                                                            ('name', 'like', search_word.lower())],
                                                                           limit=limit,
                                                                           offset=offset)
        categories_details = []
        if categories:
            for category in categories:
                category_details = {
                    'id': category.id,
                    'name': category.name,
                    'image': category.image
                }
                categories_details.append(category_details)

        return categories_details

    @api.model
    def get_product_categories_details(self, search_word='', limit=None, offset=0):
        categories = False
        if search_word == '':
            categories = self.env['product.category'].sudo().search([], limit=limit, offset=offset)
        else:
            categories = self.env['product.category'].sudo().search(['|', '|', '|',
                                                                     ('name', 'like', search_word),
                                                                     ('name', 'like', search_word.capitalize()),
                                                                     ('name', 'like', search_word.upper()),
                                                                     ('name', 'like', search_word.lower())],
                                                                    limit=limit,
                                                                    offset=offset)
        categories_details = []
        if categories:
            for category in categories:
                category_details = {
                    'id': category.id,
                    'name': category.name,
                    'image': category.image
                }
                categories_details.append(category_details)

        return categories_details

    @api.model
    def get_recipe_categories(self, categories_ids: list):
        if categories_ids:
            categories = self.env['tanmya.product.category'].sudo().search([('id', 'in', categories_ids)])
            categories_details = []
            for category in categories:
                category_details = {
                    'id': category.id,
                    'name': category.name,
                    'image': category.image
                }
                categories_details.append(category_details)
            return categories_details
        return []


class Tanmyacustomerpots(models.Model):
    _name = "tanmya.customer.pot"
    name = fields.Char(string='Reciept name')
    portaluser = fields.Many2one('res.users')
    items = fields.One2many('tanmya.customer.line', 'parent_id', string="Items")
    image_1920 = fields.Image(string="Image")
    iscustom = fields.Boolean(string='Is custom', default=True)
    product_id = fields.Many2one('product.product', string="product")

    def get_price(self):
        self.ensure_one()
        price = 0
        for line in self.items:
            price += line.product_id.list_price * line.qty
        return price


class Tanmyacustomerpotslines(models.Model):
    _name = "tanmya.customer.line"
    product_id = fields.Many2one('product.product')
    parent_id = fields.Many2one('tanmya.customer.pot', string='Pot Reference', required=True, ondelete='cascade',
                                index=True,
                                copy=False)
    qty = fields.Float('Quantity')


class TanmyaProducExt(models.Model):
    _inherit = 'product.product'

    kit_template = fields.Many2one("sale.order.template", string="Pot Template", check_company=True)
    favorite = fields.Boolean(string='Add to favorite')
    prod_category = fields.Many2many("tanmya.product.category", string="category")
    image_1920_1 = fields.Image(string="Image1")
    image_1920_2 = fields.Image(string="Image2")

    owner_id = fields.Many2one('res.users', string='Recipe Owner ID')
    recipe_status = fields.Selection([('private', 'Private'),
                                      ('pending', 'Pending'),
                                      ('public', 'Public')],
                                     string='Recipe Status', default='private')
    nutritional_value = fields.Char(string='Nutritional Value :', default='', readonly=True)
    hours_preparation_time = fields.Char(string='Hours Preparation Time')
    minutes_preparation_time = fields.Char(string='Minutes Preparation Time')
    difficulty_level = fields.Selection([('easy', 'Easy'),
                                         ('medium', 'Medium'),
                                         ('hard', 'Hard')],
                                        string='Difficulty Level', default='easy')
    instructions = fields.Text(string='Recipe Instructions')
    description = fields.Text(string='Description')
    servings = fields.Integer(string='Persons Servings')

    # Nutrition Value Fields
    calories = fields.Char(string='Recipe Calories')
    carbs = fields.Char(string='Recipe Carbs')
    protein = fields.Char(string='Recipe Protin')
    fat = fields.Char(string='Recipe Fat')
    fiber = fields.Char(string='Recipe Fiber')
    iron = fields.Char(string='Recipe Iron')

    # Recipe Reviews
    reviews_ids = fields.One2many('tanmya.review', 'recipe_id', string='Recipe Reviews')

    @api.constrains('calories', 'carbs', 'protein', 'fat', 'fiber', 'iron')
    def _check_nutrition_value(self):
        text = str(self.calories)
        for char in text:
            if not char.isdigit():
                if char == ',' or char == '.':
                    pass
                else:
                    raise ValidationError("Calories filed should contains numbers only")
        if len(self.calories) > 3:
            raise ValidationError("Calories filed should contains 3 characters maximum")
        ####################################################
        text = str(self.carbs)
        for char in text:
            if not char.isdigit():
                if char == ',' or char == '.':
                    pass
                else:
                    raise ValidationError("Carbs filed should contains numbers only")
        if len(self.carbs) > 3:
            raise ValidationError("Carbs filed should contains 3 characters maximum")
        ####################################################
        text = str(self.protein)
        for char in text:
            if not char.isdigit():
                if char == ',' or char == '.':
                    pass
                else:
                    raise ValidationError("Protein filed should contains numbers only")
        if len(self.protein) > 3:
            raise ValidationError("Protein filed should contains 3 characters maximum")
        ####################################################
        text = str(self.fat)
        for char in text:
            if not char.isdigit():
                if char == ',' or char == '.':
                    pass
                else:
                    raise ValidationError("Fat filed should contains numbers only")
        if len(self.fat) > 3:
            raise ValidationError("Fat filed should contains 3 characters maximum")
        ####################################################
        text = str(self.fiber)
        for char in text:
            if not char.isdigit():
                if char == ',' or char == '.':
                    pass
                else:
                    raise ValidationError("Fiber filed should contains numbers only")
        if len(self.fiber) > 3:
            raise ValidationError("Fiber filed should contains 3 characters maximum")
        ####################################################
        text = str(self.iron)
        for char in text:
            if not char.isdigit():
                if char == ',' or char == '.':
                    pass
                else:
                    raise ValidationError("Iron filed should contains numbers only")
        if len(self.iron) > 3:
            raise ValidationError("Iron filed should contains 3 characters maximum")

    @api.depends('list_price', 'price_extra', 'kit_template')
    @api.depends_context('uom')
    def _compute_product_lst_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse(self._context['uom'])

        for product in self:
            if product.kit_template:
                totalprice = 0
                product.lst_price = self._compute_kit_price(product.kit_template, to_uom)
            else:
                if to_uom:
                    list_price = product.uom_id._compute_price(product.list_price, to_uom)
                else:
                    list_price = product.list_price
                product.lst_price = list_price + product.price_extra

    def _compute_kit_price(self, kit, to_uom):
        totalprice = 0
        for item in kit.sale_order_template_line_ids:
            if item.product_id.kit_template:
                totalprice += self._compute_kit_price(item.product_id.kit_template)
            else:
                if to_uom:
                    list_price = item.product_id.uom_id._compute_price(item.product_id.list_price, to_uom)
                else:
                    list_price = item.product_id.list_price
                totalprice += (list_price + item.product_id.price_extra) * item.product_uom_qty

        return totalprice

    def time_convert(self, sec):
        mins = sec // 60
        sec = sec % 60
        hours = mins // 60
        mins = mins % 60
        return "Time Lapsed = {0}:{1}:{2}".format(int(hours), int(mins), sec)

    @api.model
    def add_recipe(self, vals: dict):
        try:
            # Create new Kit Template "sale.order.template" record
            sale_order_template_vals = {
                'name': vals.get('recipe_name'),
                'active': True
            }
            sale_order_template_id = self.env['sale.order.template'].sudo().create(sale_order_template_vals)

            # Create "sale.order.template.line" record for each ingredient
            if (len(vals.get('ingredients_names')) == len(vals.get('ingredients_qty'))
                    == len(vals.get('ingredients_products'))):
                print('Ingredients Details Is Correct')

            for i in range(len(vals.get('ingredients_names'))):
                sale_order_template_line_vals = {
                    'name': vals.get('ingredients_names')[i],
                    'sale_order_template_id': sale_order_template_id.id,
                    'product_id': vals.get('ingredients_products')[i],
                    'product_uom_qty': vals.get('ingredients_qty')[i],
                    'product_uom_id': vals.get('uom_id')
                }
                self.env['sale.order.template.line'].sudo().create(sale_order_template_line_vals)
            _logger.info('--------------------- images debug --------------------------')
            _logger.info(vals.get('recipe_image'))
            _logger.info(vals.get('recipe_image1'))
            _logger.info(vals.get('recipe_image2'))
            _logger.info('--------------------- end of debug ----------------------------')
            # Create Recipe
            recipe_vals = {
                'owner_id': vals.get('owner_id'),
                'image_1920': vals.get('recipe_image'),
                'image_1920_1': vals.get('recipe_image1'),
                'image_1920_2': vals.get('recipe_image2'),
                'name': vals.get('recipe_name'),
                'hours_preparation_time': vals.get('hours_time'),
                'minutes_preparation_time': vals.get('minutes_time'),
                'difficulty_level': vals.get('difficulty_level'),
                'description': vals.get('description'),
                'prod_category': [(6, 0, vals.get('categories'))],
                'calories': vals.get('calories'),
                'carbs': vals.get('carbs'),
                'protein': vals.get('protein'),
                'fat': vals.get('fat'),
                'fiber': vals.get('fiber'),
                'iron': vals.get('iron'),
                'instructions': vals.get('instructions'),
                'servings': vals.get('servings'),
                'kit_template': sale_order_template_id.id,
            }
            _logger.info('Add Recipe before creating the product')
            recipe_id = self.env['product.product'].sudo().create(recipe_vals)
            _logger.info('Add Recipe Completed!')
            _logger.info(recipe_id.id)
            return recipe_id.id

        except Exception as err:
            _logger.info('Error in add recipe!')
            _logger.info(err)
            _logger.info('End Of exception in recipe')
            return False

    @api.model
    def publish_recipe(self, recipe_vals: dict):
        recipe_id = self.add_recipe(recipe_vals)
        _logger.info(f"recipe added with this value: {recipe_vals} and we get this recipe {recipe_id}")
        if recipe_id:
            appr_category_id = self.env['approval.category'].sudo().search(
                [('name', '=', 'Recipe Approval'),
                 ('description', '=', 'Approval type for approve on publish recipe for public or not.'),
                 ('has_product', '=', 'required')]).id
            recipe = self.env['product.product'].sudo().search([('id', '=', recipe_id)])
            _logger.info('//////////////////////////////////// zaid last day 2 //////////////////////////////////////')
            _logger.info(recipe)
            _logger.info('////////////////////////////////////////////////////////////////////////////////////////')
            if appr_category_id:
                appr_request_vals = {
                    'category_id': appr_category_id,
                    'date_start': datetime.now(),
                    'date_end': datetime.now(),
                    'request_owner_id': recipe.owner_id.id
                }
                appr_request_id = self.env['approval.request'].sudo().create(appr_request_vals)

                appr_product_line_vals = {
                    'approval_request_id': appr_request_id.id,
                    'description': recipe.name,
                    'product_id': recipe.id,
                    'product_uom_id': 1,
                }
                appr_product_line = self.env['approval.product.line'].sudo().create(appr_product_line_vals)
                if appr_product_line:
                    recipe.recipe_status = 'pending'

    @api.model
    def edit_recipe(self, recipe_id: int, vals: dict):
        check = False
        try:
            recipe = self.env['product.product'].sudo().search([('id', '=', recipe_id)])

            if recipe:
                sale_order_template = None
                # update sale order template fields
                if vals.get('recipe_name'):
                    sale_order_template = recipe.kit_template
                    new_sale_order_vals = {
                        'name': vals.get('recipe_name'),
                    }
                    self.env['sale.order.template'].sudo().search([('id', '=', sale_order_template.id)]).write(
                        new_sale_order_vals)

                # update sale order template lines fields
                if vals.get('ingredients_products'):
                    if len(vals.get('ingredients_products')) > 0:
                        for line in sale_order_template.sale_order_template_line_ids:
                            line.unlink()
                        for i in range(len(vals.get('ingredients_products'))):
                            sale_order_template_line_vals = {
                                'name': vals.get('ingredients_names')[i],
                                'sale_order_template_id': sale_order_template.id,
                                'product_id': vals.get('ingredients_products')[i],
                                'product_uom_qty': vals.get('ingredients_qty')[i],
                                'product_uom_id': vals.get('uom_id')
                            }
                            self.env['sale.order.template.line'].sudo().create(sale_order_template_line_vals)

                # update recipe fields
                new_recipe_vals = {}
                if type(vals.get('recipe_image')) == str:
                    new_recipe_vals['image_1920'] = vals.get('recipe_image')
                if type(vals.get('recipe_image1')) == str:
                    new_recipe_vals['image_1920_1'] = vals.get('recipe_image1')
                if type(vals.get('recipe_image2')) == str:
                    new_recipe_vals['image_1920_2'] = vals.get('recipe_image2')

                if vals.get('recipe_name'):
                    new_recipe_vals['name'] = vals.get('recipe_name')

                if vals.get('hours_time') != '-1':
                    new_recipe_vals['hours_preparation_time'] = vals.get('hours_time')
                if vals.get('minutes_time') != '-1':
                    new_recipe_vals['minutes_preparation_time'] = vals.get('minutes_time')

                if vals.get('difficulty_level'):
                    new_recipe_vals['difficulty_level'] = vals.get('difficulty_level')

                if vals.get('description'):
                    new_recipe_vals['description'] = vals.get('description')

                if len(vals.get('categories')) > 0:
                    new_recipe_vals['prod_category'] = [(6, 0, vals.get('categories'))]

                if vals.get('calories') != '':
                    new_recipe_vals['calories'] = vals.get('calories')
                if vals.get('carbs') != '':
                    new_recipe_vals['carbs'] = vals.get('carbs')
                if vals.get('protein') != '':
                    new_recipe_vals['protein'] = vals.get('protein')
                if vals.get('fat') != '':
                    new_recipe_vals['fat'] = vals.get('fat')
                if vals.get('fiber') != '':
                    new_recipe_vals['fiber'] = vals.get('fiber')
                if vals.get('iron') != '':
                    new_recipe_vals['iron'] = vals.get('iron')

                if vals.get('instructions'):
                    new_recipe_vals['instructions'] = vals.get('instructions')
                if vals.get('servings') != 1:
                    new_recipe_vals['servings'] = vals.get('servings')

                recipe.write(new_recipe_vals)

                print('Edit Recipe Completed!')
                check = True
                return check

        except:
            print('Error In Edit Recipe!')
            return check

        return check

    @api.model
    def delete_recipe(self, recipe_id: int):
        check = False
        try:
            print(recipe_id)
            kit_template_id = self.env['product.product'].sudo().search([('id', '=', recipe_id)]).kit_template.id
            self.env['sale.order.template'].sudo().search([('id', '=', kit_template_id)]).unlink()
            self.env['product.product'].sudo().search([('id', '=', recipe_id)]).unlink()

            print('Recipe Has Been Deleted !')
            check = True
            return check

        except:
            print('Error In Delete Recipe!!')
            return check

        return check

    @api.model
    def get_user_id(self):
        uid = self.env.uid
        return uid

    def get_preference_state(self, product_id):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        for rec in user.products_preferences_ids:
            if rec.product_id.id == product_id:
                return rec.status

        return 'dislike'

    @api.model
    def get_products_details(self, search_word='', category_id=-1, order_by='name', limit=None, offset=0,
                             is_publish=True):
        search_word1 = search_word.capitalize()
        search_word2 = search_word.lower()
        search_word3 = search_word.upper()
        _logger.info(category_id)
        if category_id > 0:
            products = self.env['product.template'].sudo().search(['|', '|', '|',
                                                                   ('name', 'like', search_word),
                                                                   ('name', 'like', search_word1),
                                                                   ('name', 'like', search_word2),
                                                                   ('name', 'like', search_word3),
                                                                   ('categ_id', '=', category_id),
                                                                   ('is_published', '=', is_publish)],
                                                                  limit=limit,
                                                                  offset=offset,
                                                                  order=order_by)

            products_details = []
            for product in products:
                product_details = {
                    'id': product.id,
                    'name': product.name,
                    'image_128': product.image_1920,
                    'list_price': product.list_price,
                    'calories': product.calories,
                    'carbs': product.carbs,
                    'protein': product.protein,
                    'fat': product.fat,
                    'fiber': product.fiber,
                    'iron': product.iron,
                    'uom': product.uom_id.name,
                    'description': product.description,
                    'preference_state': self.get_preference_state(product.id),
                    'additional_description': product.website_description,
                    'composition': product.x_studio_composition,
                    'conservation_et_utilisation': product.x_studio_conservation_et_utilisation,
                    'product_more_info': product.x_studio_product_more_info
                }
                products_details.append(product_details)

        else:
            products = self.env['product.product'].sudo().search(['|', '|', '|',
                                                                  ('name', 'like', search_word),
                                                                  ('name', 'like', search_word1),
                                                                  ('name', 'like', search_word2),
                                                                  ('name', 'like', search_word3),
                                                                  ('kit_template', '=', None),
                                                                  ('is_published', '=', is_publish)],
                                                                 limit=limit,
                                                                 offset=offset,
                                                                 order=order_by)

            products_details = []
            for product in products:
                product_details = {
                    'id': product.id,
                    'name': product.name,
                    'image_128': product.image_1920,
                    'list_price': product.list_price,
                    'uom': product.uom_id.name,
                    'calories': product.calories,
                    'carbs': product.carbs,
                    'protein': product.protein,
                    'fat': product.fat,
                    'fiber': product.fiber,
                    'iron': product.iron,
                    'description': product.description,
                    'preference_state': self.get_preference_state(product.id),
                    'additional_description': product.website_description,
                    'composition': product.x_studio_composition,
                    'conservation_et_utilisation': product.x_studio_conservation_et_utilisation,
                    'product_more_info': product.x_studio_product_more_info
                }
                products_details.append(product_details)
        return products_details

    @api.model
    def get_ingredients_details(self, recipe_id: int):
        sale_order = self.env['product.product'].sudo().search([('id', '=', recipe_id)]).kit_template
        ingredients_details = []
        for line in sale_order.sale_order_template_line_ids:
            ingredient_details = {
                'name': line.name,
                'product_qty': line.product_uom_qty,
                'product_uom': line.product_uom_id.name,
                'product_id': line.product_id.id,
                'list_price': line.product_id.product_tmpl_id.list_price
            }
            ingredients_details.append(ingredient_details)
        return ingredients_details

    @api.model
    def get_user_info(self, user_id: int):
        if user_id:
            user = self.env['res.users'].sudo().search([('id', '=', user_id)])
            if user:
                partner = self.env['res.partner'].sudo().search([('id', '=', user.partner_id.id)])
                if partner:
                    return [partner.name, partner.email, partner.image_1920, partner.mobile or '']

    @api.model
    def get_count_user_recipes(self, user_id: int):
        recipe_count = 0
        if user_id:
            recipes = self.env['product.product'].sudo().search([('owner_id', '=', user_id),
                                                                 ('recipe_status', '=', 'public')])
            recipe_count = int(len(recipes))
        return recipe_count

    @api.model
    def get_count_all_user_recipes(self, user_id: int):
        recipe_count_1 = 0
        if user_id:
            recipes = self.env['product.product'].sudo().search([('owner_id', '=', user_id)])
            recipe_count_1 = int(len(recipes))
        return recipe_count_1

    @api.model
    def get_total_user_recipes_rates(self, user_id):
        if user_id:
            recipes = self.env['product.product'].sudo().search([('owner_id', '=', user_id),
                                                                 ('recipe_status', '=', 'public')])
            recipe_count = int(len(recipes))
            user_recipes_rates = 0.0
            rates_sum = 0
            for recipe in recipes:
                rates_sum += self.get_recipe_total_rates(recipe.id)
            if recipe_count != 0:
                user_recipes_rates = rates_sum / recipe_count
            return user_recipes_rates

    @api.model
    def add_review(self, recipe_id: int, review_text: str, rating: str):
        if recipe_id:
            recipe = self.env['product.product'].sudo().search([('id', '=', recipe_id)])
            if recipe:
                review_vals = {
                    'recipe_id': recipe_id,
                    'user_id': self.env.uid,
                    'review_text': review_text,
                    'review_date': datetime.now(),
                    'rating': rating
                }
                review = self.env['tanmya.review'].sudo().create(review_vals)

                # Send notification when a user adds a review on consumer recipe
                if review:
                    if recipe.owner_id.preferred_language == 'en':
                        notification_vals = {
                            'title': 'Recipe reviewed',
                            'content': f'{review.user_id.name} just reviewed your recipe. Click here to see details.',
                            'payload': 'recipe_reviewed',
                            'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                            'notification_date': datetime.now(),
                            'user_ids': [(6, 0, [recipe.owner_id.id])],
                            'recipe_id': recipe_id,
                        }
                    elif recipe.owner_id.preferred_language == 'fr':
                        notification_vals = {
                            'fr_title': 'Recette revue',
                            'fr_content': f'{review.user_id.name} viens de revoir ta recette. Cliquez ici pour voir les détails.',
                            'payload': 'recipe_reviewed',
                            'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                            'notification_date': datetime.now(),
                            'user_ids': [(6, 0, [recipe.owner_id.id])],
                            'recipe_id': recipe_id,
                        }
                    notification = self.env['firebase.notification'].sudo().create(notification_vals)
                    if notification:
                        #                         notification.send_notifications()
                        notification.send()

    @api.model
    def get_recipe_reviews(self, reviews_ids=None, limit=None, offset=0):
        if reviews_ids:
            reviews = self.env['tanmya.review'].sudo().search([('id', 'in', reviews_ids)],
                                                              limit=limit,
                                                              offset=offset,
                                                              order='review_date desc')
            reviews_details = []
            for review in reviews:
                review_details = {
                    'review_text': review.review_text,
                    'review_date': review.review_date,
                    'rating': review.rating,
                    'user_name': review.user_id.partner_id.name,
                    'user_image': review.user_id.partner_id.image_1920,
                }
                reviews_details.append(review_details)
            return reviews_details
        return []

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
    def get_recipes_details(self, state='public', owner_id=-1, limit=None, offset=0):
        recipes = False
        if owner_id == -1 or not owner_id:
            recipes = self.env['product.product'].sudo().search([('kit_template', '!=', None),
                                                                 ('recipe_status', '=', state)],
                                                                limit=limit,
                                                                offset=offset)
        else:
            recipes = self.env['product.product'].sudo().search([('kit_template', '!=', None),
                                                                 ('recipe_status', '=', state),
                                                                 ('owner_id', '=', owner_id)],
                                                                limit=limit,
                                                                offset=offset)
        recipes_details = []
        if recipes:
            for recipe in recipes:
                recipe_details = {
                    'id': recipe.id,
                    'name': recipe.product_tmpl_id.name,
                    'image_1920': recipe.image_1920,
                    'image_1920_1': recipe.image_1920_1,
                    'image_1920_2': recipe.image_1920_2,
                    'kit_template': [recipe.kit_template.id, recipe.kit_template.name],
                    'list_price': recipe.product_tmpl_id.list_price,
                    'owner_id': [recipe.owner_id.id, recipe.owner_id.name],
                    'hours_preparation_time': recipe.hours_preparation_time,
                    'minutes_preparation_time': recipe.minutes_preparation_time,
                    'difficulty_level': recipe.difficulty_level,
                    'instructions': recipe.instructions,
                    'description': recipe.description,
                    'servings': recipe.servings,
                    'calories': recipe.calories,
                    'protein': recipe.protein,
                    'carbs': recipe.carbs,
                    'fat': recipe.fat,
                    'fiber': recipe.fiber,
                    'iron': recipe.iron,
                    'prod_category': recipe.prod_category.ids,
                    'reviews_ids': recipe.reviews_ids.ids,
                    'preference_state': self.get_preference_state(recipe.id),
                    'total_rates': self.get_recipe_total_rates(recipe.id),
                    'recipe_status': recipe.recipe_status
                }
                recipes_details.append(recipe_details)
        return recipes_details

    @api.model
    def get_product_count(self, search_word=''):
        search_word1 = search_word.capitalize()
        search_word2 = search_word.lower()
        search_word3 = search_word.upper()
        return self.env['product.product'].sudo().search_count(['|', '|', '|',
                                                                ('name', 'like', search_word),
                                                                ('name', 'like', search_word1),
                                                                ('name', 'like', search_word2),
                                                                ('name', 'like', search_word3), ])

    @api.model
    def get_recipes(self, search_word='', order_by='name', limit=None, offset=0, category_id=-1):
        if category_id > 0:
            recipes = self.env['product.product'].sudo().search(['|', '|', '|',
                                                                 ('name', 'like', search_word),
                                                                 ('name', 'like', search_word.capitalize()),
                                                                 ('name', 'like', search_word.lower()),
                                                                 ('name', 'like', search_word.upper()),
                                                                 ('kit_template', '!=', None),
                                                                 ('prod_category', 'like', category_id),
                                                                 ('recipe_status', '=', 'public')],
                                                                order=order_by,
                                                                limit=limit,
                                                                offset=offset)
        else:
            recipes = self.env['product.product'].sudo().search(['|', '|', '|',
                                                                 ('name', 'like', search_word),
                                                                 ('name', 'like', search_word.capitalize()),
                                                                 ('name', 'like', search_word.lower()),
                                                                 ('name', 'like', search_word.upper()),
                                                                 ('kit_template', '!=', None),
                                                                 ('recipe_status', '=', 'public')],
                                                                order=order_by,
                                                                limit=limit,
                                                                offset=offset)
        recipes_details = []
        for recipe in recipes:
            recipe_details = {
                'id': recipe.id,
                'name': recipe.product_tmpl_id.name,
                'image_1920': recipe.image_1920,
                'image_1920_1': recipe.image_1920_1,
                'image_1920_2': recipe.image_1920_2,
                'kit_template': [recipe.kit_template.id, recipe.kit_template.name],
                'list_price': recipe.product_tmpl_id.list_price,
                'owner_id': [recipe.owner_id.id, recipe.owner_id.name],
                'hours_preparation_time': recipe.hours_preparation_time,
                'minutes_preparation_time': recipe.minutes_preparation_time,
                'difficulty_level': recipe.difficulty_level,
                'instructions': recipe.instructions,
                'description': recipe.description,
                'servings': recipe.servings,
                'calories': recipe.calories,
                'protein': recipe.protein,
                'carbs': recipe.carbs,
                'fat': recipe.fat,
                'fiber': recipe.fiber,
                'iron': recipe.iron,
                'prod_category': recipe.prod_category.ids,
                'reviews_ids': recipe.reviews_ids.ids,
                'preference_state': self.get_preference_state(recipe.id),
                'total_rates': self.get_recipe_total_rates(recipe.id)
            }
            recipes_details.append(recipe_details)

        return recipes_details

    @api.model
    def get_recipe_details(self, recipe_id: int):
        if recipe_id:
            recipe = self.env['product.product'].sudo().browse(recipe_id)
            if recipe:
                recipe_details = {
                    'id': recipe.id,
                    'name': recipe.product_tmpl_id.name,
                    'image_1920': recipe.image_1920,
                    'image_1920_1': recipe.image_1920_1,
                    'image_1920_2': recipe.image_1920_2,
                    'kit_template': [recipe.kit_template.id, recipe.kit_template.name],
                    'list_price': recipe.product_tmpl_id.list_price,
                    'owner_id': [recipe.owner_id.id, recipe.owner_id.name],
                    'hours_preparation_time': recipe.hours_preparation_time,
                    'minutes_preparation_time': recipe.minutes_preparation_time,
                    'difficulty_level': recipe.difficulty_level,
                    'instructions': recipe.instructions,
                    'description': recipe.description,
                    'servings': recipe.servings,
                    'calories': recipe.calories,
                    'protein': recipe.protein,
                    'carbs': recipe.carbs,
                    'fat': recipe.fat,
                    'fiber': recipe.fiber,
                    'iron': recipe.iron,
                    'prod_category': recipe.prod_category.ids,
                    'reviews_ids': recipe.reviews_ids.ids,
                    'preference_state': recipe.get_preference_state(recipe.id),
                    'total_rates': recipe.get_recipe_total_rates(recipe.id),
                    'recipe_status': recipe.recipe_status
                }
                return recipe_details
        return False
