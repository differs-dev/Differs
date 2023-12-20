from odoo import api, fields, models, tools


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"
    is_mobile_list = fields.Boolean("Use this list in mobile app?")
  
