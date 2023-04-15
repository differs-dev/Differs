from odoo import api, fields, models, _


class ProductTemplateInherit(models.Model):
    _inherit = "product.template",

    website_description = fields.Char('Description for the website')
    
    # Nutrition Value Fields
    calories = fields.Char(string='Recipe Calories')
    carbs = fields.Char(string='Recipe Carbs')
    protein = fields.Char(string='Recipe Protin')
    fat = fields.Char(string='Recipe Fat')
    fiber = fields.Char(string='Recipe Fiber')
    iron = fields.Char(string='Recipe Iron')
