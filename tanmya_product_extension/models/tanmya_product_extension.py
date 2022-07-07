from odoo import api, fields, models, tools
from datetime import date, datetime,timedelta
import pytz


class Tanmyaprodcategory(models.Model):
    _name = "tanmya.product.category"
    name=fields.Char(string='Category name')
    image=fields.Image(string='Image')

class Tanmyacustomerpots(models.Model):
    _name = "tanmya.customer.pot"
    name=fields.Char(string='Reciept name')
    portaluser=fields.Many2one('res.users')
    items=fields.One2many('tanmya.customer.line','parent_id',string="Items")
    image_1920 = fields.Image(string="Image")
    iscustom=fields.Boolean(string='Is custom',default=True)
    product_id=fields.Many2one('product.product',string="product")


    def get_price(self):
        self.ensure_one()
        price=0
        for line in self.items:
            price+= line.product_id.list_price*line.qty
        return price

class Tanmyacustomerpotslines(models.Model):
    _name = "tanmya.customer.line"
    product_id =fields.Many2one('product.product')
    parent_id = fields.Many2one('tanmya.customer.pot', string='Pot Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    qty=fields.Float('Quantity')

class TanmyaProductemplateExt(models.Model):
    _inherit = 'product.product'
    kit_template = fields.Many2one("sale.order.template", string="Pot Template", check_company=True)
    favorite = fields.Boolean(string='Add to favorite')
    prod_category = fields.Many2many("tanmya.product.category",string="category")
    image_1920_1 = fields.Image(string="Image1")
    image_1920_2 = fields.Image(string="Image2")

    owner_id = fields.Many2one('res.users', string='Recipe Owner ID', readonly=True)
    recipe_status = fields.Selection([('private','Private Recipe'),
                                      ('public','Public Recipe')],
                                      string='Public Recipe', default='private')
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


    @api.depends('list_price', 'price_extra','kit_template')
    @api.depends_context('uom')
    def _compute_product_lst_price(self):
        to_uom = None
        if 'uom' in self._context:
            to_uom = self.env['uom.uom'].browse(self._context['uom'])

        for product in self:
            if product.kit_template:
                totalprice=0
                # for item in product.kit_template.sale_order_template_line_ids:
                #     if to_uom:
                #         list_price = item.product_id.uom_id._compute_price(product.list_price, to_uom)
                #     else:
                #         list_price = item.product_id.list_price
                #     totalprice+=(list_price+ item.product_id.price_extra)*item.product_uom_qty

                product.lst_price =self._compute_kit_price(product.kit_template,to_uom)

            else:
                if to_uom:
                    list_price = product.uom_id._compute_price(product.list_price, to_uom)
                else:
                    list_price = product.list_price
                product.lst_price = list_price + product.price_extra

    def _compute_kit_price(self,kit,to_uom):
        totalprice = 0
        for item in kit.sale_order_template_line_ids:
            if item.product_id.kit_template:
                totalprice+=self._compute_kit_price(item.product_id.kit_template)
            else:
                if to_uom:
                    list_price = item.product_id.uom_id._compute_price(item.product_id.list_price, to_uom)
                else:
                    list_price = item.product_id.list_price
                totalprice += (list_price + item.product_id.price_extra) * item.product_uom_qty

        return totalprice

    @api.model
    def add_recipe(self, vals:dict):
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

            # Create Recipe
            recipe_vals = {
                # 'owner_id': self.env.uid,
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
            recipe_id = self.env['product.product'].sudo().create(recipe_vals)
            print('Add Recipe Completed!')
            return recipe_id.id

        except:
            print('Error in add recipe!')
            return False

    @api.model
    def publish_recipe(self, recipe_vals: dict):
        recipe_id = self.add_recipe(recipe_vals)

        if recipe_id:
            appr_category_id = self.env['approval.category'].search(
                [('name', '=', 'Recipe Approval'),
                 ('description', '=', 'Approval type for approve on publish recipe for public or not.'),
                 ('has_product', '=', 'required')]).id
            recipe = self.env['product.product'].search([('id', '=', recipe_id)])

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
                appr_product_line = self.env['approval.product.line'].create(appr_product_line_vals)

    @api.model
    def edit_recipe(self, recipe_id:int, vals:dict):
        check = False
        try:
            recipe = self.env['product.product'].search([('id','=',recipe_id)])

            # update sale order template fields
            sale_order_template = None
            if recipe:
                sale_order_template = recipe.kit_template
                new_sale_order_vals = {
                    'name': recipe.name,
                }
                self.env['sale.order.template'].search([('id','=',sale_order_template.id)]).write(new_sale_order_vals)

            # update sale order template lines fields
            if vals.get('ingredients_names'):
                if len(vals.get('ingredients_names')) > 0:
                    for line in sale_order_template.sale_order_template_line_ids:
                        line.unlink()
            for i in range(len(ingredients_names)):
                sale_order_template_line_vals = {
                    'name': vals.get('ingredients_names')[i],
                    'sale_order_template_id': sale_order_template.id,
                    'product_id': vals.get('ingredients_products')[i],
                    'product_uom_qty': vals.get('ingredients_qty')[i],
                    'product_uom_id': vals.get('uom_id')
                }
                self.env['sale.order.template.line'].sudo().create(sale_order_template_line_vals)

            # update recipe fields
            new_recipe_vals = {
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
            }
            recipe.write(new_recipe_vals)

            print('Edit Recipe Completed!')
            check = True
            return check

        except:
            print('Error In Edit Recipe!')
            return check

        return check

    @api.model
    def delete_recipe(self, recipe_id:int):
        check = False
        try:
            print(recipe_id)
            kit_template_id = self.env['product.product'].sudo().search([('id','=',recipe_id)]).kit_template.id
            self.env['sale.order.template'].sudo().search([('id', '=', kit_template_id)]).unlink()
            self.env['product.product'].sudo().search([('id','=',recipe_id)]).unlink()

            print('Recipe Has Been Deleted !')
            check = True
            return check
        except:
            print('Error In Delete Recipe!!')
            return check

        return check

    @api.model
    def get_user_id(self, user_email:str):
        user_id = self.env['res.users'].sudo().search([('login','=',user_email)]).id
        return user_id

    @api.model
    def get_ingredients_details(self, recipe_id:int):
        sale_order = self.env['product.product'].search([('id','=',recipe_id)]).kit_template
        names = []
        qty = []
        for line in sale_order.sale_order_template_line_ids:
            names.append(line.name)
            qty.append(line.product_uom_qty)
        return [names, qty]






