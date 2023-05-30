from odoo.addons.website_sale.controllers import main
from odoo import fields, models, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.tools.json import scriptsafe as json_scriptsafe


class WebsiteSalext(main.WebsiteSale):

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page (without redirection).
        """
        order = request.website.sale_get_order(force_create=1)

        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=1)
            else:
                return {}
        fact_quant = add_qty
        pcav = kw.get('product_custom_attribute_values')
        nvav = kw.get('no_variant_attribute_values')
        produc = http.request.env['product.product'].sudo().browse(product_id)
        if produc.kit_template:
            arr_sub = kw.get('subproducts')
            sub_products = {int((sub.split(":")[0])[5:]): float(sub.split(":")[1]) for sub in arr_sub}
            for item in produc.kit_template.sale_order_template_line_ids:
                qqq = fact_quant * sub_products[item.product_id.id]
                value = order._cart_update(
                    product_id=item.product_id.id,
                    line_id=line_id,
                    # cart_quantity=int(sub_products[item.product_id.id]),
                    add_qty=fact_quant * sub_products[item.product_id.id],
                    set_qty=set_qty,
                    product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
                    no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None
                )

            if not order.cart_quantity:
                request.website.sale_reset()
                return value

            order = request.website.sale_get_order()
            # value['cart_quantity'] = order.cart_quantity

            if not display:
                return value

            value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
                'website_sale_order': order,
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()
            })
            value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template(
                "website_sale.short_cart_summary", {
                    'website_sale_order': order,
                })
            return value
        else:
            # order = request.website.sale_get_order(force_create=1)
            # print('one product is added ----not a kit---json entered inherited-----------')
            # if order.state != 'draft':
            #     request.website.sale_reset()
            #     if kw.get('force_create'):
            #         order = request.website.sale_get_order(force_create=1)
            #     else:
            #         return {}
            #
            # pcav = kw.get('product_custom_attribute_values')
            # nvav = kw.get('no_variant_attribute_values')
            value = order._cart_update(
                product_id=product_id,
                line_id=line_id,
                add_qty=add_qty,
                set_qty=set_qty,
                product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
                no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None
            )

            if not order.cart_quantity:
                request.website.sale_reset()
                return value

            order = request.website.sale_get_order()
            value['cart_quantity'] = order.cart_quantity

            if not display:
                return value

            value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
                'website_sale_order': order,
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()
            })
            value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template(
                "website_sale.short_cart_summary", {
                    'website_sale_order': order,
                })
            return value

    @http.route(['''/favorites'''], type='http', auth="public", website=True)
    def get_favorites(self, **kw):
        values = {'pi': 3.14}
        return request.render("tanmya_product_extension.tanm_portal_addfavorites", values)

    # def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
    #     """
    #     This route is called :
    #         - When changing quantity from the cart.
    #         - When adding a product from the wishlist.
    #         - When adding a product to cart on the same page (without redirection).
    #     """
    #     print(product_id)
    #     # print('@@@@@@@@##########@@@@@@@@@@@')
    #     print(kw)
    #     produc = http.request.env['product.product'].sudo().browse(product_id)
    #     if produc.kit_template:
    #         order = request.website.sale_get_order(force_create=1)
    #         print('one product is added ----is a kit---json entered inherited-----------')
    #         if order.state != 'draft':
    #             request.website.sale_reset()
    #             if kw.get('force_create'):
    #                 order = request.website.sale_get_order(force_create=1)
    #             else:
    #                 return {}
    #
    #         pcav = kw.get('product_custom_attribute_values')
    #         nvav = kw.get('no_variant_attribute_values')
    #         arr_sub=kw.get('subproducts')
    #         sub_products= {int((sub.split(":")[0])[5:]) : sub.split(":")[1] for sub in arr_sub }
    #         for item in produc.kit_template.sale_order_template_line_ids:
    #             value = order._cart_update(
    #                 product_id=item.product_id.id,
    #                 line_id=line_id,
    #                 # cart_quantity=int(sub_products[item.product_id.id]),
    #                 add_qty= sub_products[item.product_id.id],
    #                 # set_qty=set_qty,
    #                 product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
    #                 no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None
    #             )
    #             value['cart_quantity'] = sub_products[item.product_id.id]
    #             print(sub_products[item.product_id.id])
    #
    #         if not order.cart_quantity:
    #             request.website.sale_reset()
    #             return value
    #
    #         order = request.website.sale_get_order()
    #         # value['cart_quantity'] = order.cart_quantity
    #
    #         if not display:
    #             return value
    #
    #         value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
    #             'website_sale_order': order,
    #             'date': fields.Date.today(),
    #             'suggested_products': order._cart_accessories()
    #         })
    #         value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template("website_sale.short_cart_summary", {
    #             'website_sale_order': order,
    #         })
    #         return value
    #     else:
    #         order = request.website.sale_get_order(force_create=1)
    #         print('one product is added ----not a kit---json entered inherited-----------')
    #         if order.state != 'draft':
    #             request.website.sale_reset()
    #             if kw.get('force_create'):
    #                 order = request.website.sale_get_order(force_create=1)
    #             else:
    #                 return {}
    #
    #         pcav = kw.get('product_custom_attribute_values')
    #         nvav = kw.get('no_variant_attribute_values')
    #         value = order._cart_update(
    #             product_id=product_id,
    #             line_id=line_id,
    #             add_qty=add_qty,
    #             set_qty=set_qty,
    #             product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
    #             no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None
    #         )
    #
    #         if not order.cart_quantity:
    #             request.website.sale_reset()
    #             return value
    #
    #         order = request.website.sale_get_order()
    #         value['cart_quantity'] = order.cart_quantity
    #
    #         if not display:
    #             return value
    #
    #         value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
    #             'website_sale_order': order,
    #             'date': fields.Date.today(),
    #             'suggested_products': order._cart_accessories()
    #         })
    #         value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template("website_sale.short_cart_summary", {
    #             'website_sale_order': order,
    #         })
    #         return value
    #


class Website(models.Model):
    _inherit = 'website'

    def serverdate(self):
        return fields.Date.today()
