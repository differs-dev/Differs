from odoo import api, fields, models, tools


class CustomerPreferences(models.Model):
    _name = 'customer.preferences'


    customer_id = fields.Many2one('res.users', string='Customer ID')

    adults = fields.Integer(string='Adults')
    children = fields.Integer(string='Children')
    pets = fields.Integer(string='Pets')

    gluten = fields.Boolean(string='Gluten')
    dairy = fields.Boolean(string='Dairy')
    pork = fields.Boolean(string='Pork')
    pescatarian = fields.Boolean(string='Pescatarian')
    vegetarian = fields.Boolean(string='Vegetarian')
    vegan = fields.Boolean(string='Vegan')

    ingredients = fields.One2many('ingredients.preferences',
                                  'customer_preferences_id',
                                  string='Ingredients Preferences')

class IngredientsPreferences(models.Model):
    _name = 'ingredients.preferences'


    ingredients_id = fields.Many2one('product.product', string='Ingredients ID')
    status = fields.Selection([('like','Like'),
                               ('dislike','Dislike'),
                               ('neutral','Neutral')], string='Status')
    customer_preferences_id = fields.Many2one('customer.preferences', 'Customer Preferences ID')

class IngredientsDetails(models.Model):
    _name = 'ingredients.details'
    _auto = False

    id = fields.Many2one('sale.order.template.line', string='ID', readonly=True)
    sale_order_template_id = fields.Many2one('sale.order.template',string='Sale Order Template ID', readonly=True)
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
        self._cr.execute("""CREATE VIEW INGREDIENTS_DETAILS AS
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