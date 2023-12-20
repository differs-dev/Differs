from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"
    is_mobile_list = fields.Boolean("Use this list in mobile app?")

    @api.constrains('is_mobile_list')
    def check_if_mobile_has_list(self):
        lists = self.env['product.pricelist'].sudo().search([])
        for list in lists:
            if list.is_mobile_list and list.id != self.id:
                raise ValidationError("Another price list is a mobile pricelist,
                please deactivate 'Use this list in mobile app?' if you want to use this list ")
