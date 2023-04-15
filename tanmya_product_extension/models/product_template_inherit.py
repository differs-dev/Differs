from odoo import api, fields, models, _


class ProductTemplateInherit(models.Model):
    _inherit = "product.template",

    website_description = fields.Char('Description for the website')
    
    # Nutrition Value Fields
    calories = fields.Char(string='Calories')
    carbs = fields.Char(string='Carbs')
    protein = fields.Char(string='Protin')
    fat = fields.Char(string='Fat')
    fiber = fields.Char(string='Fiber')
    iron = fields.Char(string='Iron')
