from odoo import api, fields, models, _


class ProductTemplateInherit(models.Model):
    _inherit = "product.template",

    description = fields.Char('Description', translate=True)
#     website_description = fields.Char('Description for the website', sanitize_attributes=False,
#                                       translate=True, sanitize_form=False)
    
    # Nutrition Value Fields
    calories = fields.Char(string='Calories')
    carbs = fields.Char(string='Carbs')
    protein = fields.Char(string='Protin')
    fat = fields.Char(string='Fat')
    fiber = fields.Char(string='Fiber')
    iron = fields.Char(string='Iron')
