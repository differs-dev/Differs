from odoo import api, fields, models, _


class ProductTemplateInherit(models.Model):
    _inherit = "product.template",

    website_description = fields.Char('Description for the website')
