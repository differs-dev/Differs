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
    kit_template = fields.Many2one(
        "sale.order.template", string="Pot Template",
        # domain="['&','',('|', ('company_id', '=', False), ('company_id', '=', id))]",
        check_company=True,
    )
    favorite =fields.Boolean(string='Add to favorite')
    prod_category =fields.Many2one("tanmya.product.category",string="category")

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

    # ispublished =fields.Boolean(compute="_ispublished")
    #
    # def _ispublished(self):
    #     for p in self.sale_order_template_line_ids:
    #         pass
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