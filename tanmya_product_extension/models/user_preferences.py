from odoo import api, fields, models, tools


class ProductsPreferences(models.Model):
    _name = 'products.preferences'

    product_id = fields.Many2one('product.product', string='Product ID')
    template_id = fields.Many2one('product.template', string='Product Template ID')
    status = fields.Selection([('like', 'Like'),
                               ('dislike', 'Dislike'),
                               # ('neutral','Neutral')
                               ],
                              string='Status', default='dislike')
    customer_preferences_id = fields.Many2one('res.users', 'User Preferences ID')


class IngredientsDetails(models.Model):
    _name = 'ingredients.details'
    _auto = False

    id = fields.Many2one('sale.order.template.line', string='ID', readonly=True)
    sale_order_template_id = fields.Many2one('sale.order.template', string='Sale Order Template ID', readonly=True)
    product_id = fields.Many2one('product.product', string='Product ID', readonly=True)
    product_uom_qty = fields.Float(string='Quantity', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template ID', readonly=True)
    name = fields.Char(string='Name', readonly=True)
    list_price = fields.Float(string='Price', readonly=True)

    def name_get(self):
        lst = []
        for v in self:
            nm = self.env['product.product'].browse(v.product_id).name_get()[0][1]
            lst.append((v.id, nm))
        return lst

    def init(self):
        tools.drop_view_if_exists(self._cr, 'INGREDIENTS_DETAILS')
        self._cr.execute("""CREATE OR REPLACE VIEW INGREDIENTS_DETAILS AS
                            SELECT  C.ID,
                                    C.SALE_ORDER_TEMPLATE_ID,
                                    C.PRODUCT_ID,
                                    C.PRODUCT_UOM_QTY,
                                    C.PRODUCT_TMPL_ID,
                                    D.NAME,
                                    D.LIST_PRICE
                            FROM
                                (SELECT A.ID,
                                        A.SALE_ORDER_TEMPLATE_ID,
                                        A.PRODUCT_ID,
                                        A.PRODUCT_UOM_QTY,
                                        B.PRODUCT_TMPL_ID
                                    FROM SALE_ORDER_TEMPLATE_LINE A
                                    JOIN PRODUCT_PRODUCT B ON A.PRODUCT_ID = B.ID) C
                            JOIN PRODUCT_TEMPLATE D ON D.ID = C.PRODUCT_TMPL_ID;""")

    @api.model
    def get_recipe_ingredients(self, order_template_id: int):
        if order_template_id:
            ingredients = self.env['ingredients.details'].sudo().search([('sale_order_template_id', '=', order_template_id)])
            if ingredients:
                recipe_ingredients = []
                for ingredient in ingredients:
                    ingredient_details = {
                         'id': ingredient.id,
                         'product_id': ingredient.product_id,
                         'product_uom_qty': ingredient.product_uom_qty,
                         'name': ingredient.name,
                         'product_tmpl_id': ingredient.product_tmpl_id,
                         'list_price': ingredient.list_price
                    }
                    recipe_ingredients.append(ingredient_details)
                return recipe_ingredients
        return []


class ApprovalRequestExt(models.Model):
    _inherit = 'approval.request'

    def action_approve(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'approved'})

        if self.category_id.name == 'Recipe Approval':
            for line in self.product_line_ids:
                line.product_id.recipe_status = 'public'

        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()


class RecipeReviews(models.Model):
    _name = 'tanmya.review'

    recipe_id = fields.Many2one('product.product', string='Recipe ID')
    user_id = fields.Many2one('res.users', string='User ID')
    review_text = fields.Text(string='Review Text')
    review_date = fields.Date(string='Review Date')
    rating = fields.Char(string='Recipe Rating')

    
class IngredientsPreferences(models.Model):
    _name = 'ingredients.preferences'
