//odoo.define('tanmya_product_extension.TicketScreen_Popup', function(require) {
//  'use strict';
//
//  const WebsiteSale = require('WebsiteSale.WebsiteSale');
//  const PosWebsiteSale = (WebsiteSale) =>
//       class extends WebsiteSale {
//
//         function _handleAddf($form) {
//        var self = this;
//        this.$form = $form;
//
//        var productSelector = [
//            'input[type="hidden"][name="product_id"]',
//            'input[type="radio"][name="product_id"]:checked'
//        ];
//
//        var productReady = this.selectOrCreateProduct(
//            $form,
//            parseInt($form.find(productSelector.join(', ')).first().val(), 10),
//            $form.find('.product_template_id').val(),
//            false
//        );
//
//        return productReady.then(function (productId) {
//            $form.find(productSelector.join(', ')).val(productId);
//
//            self.rootProduct = {
//                product_id: productId,
//                zozooo: 777777777777777,
//                quantity: parseFloat($form.find('input[name="add_qty"]').val() || 1),
//                product_custom_attribute_values: self.getCustomVariantValues($form.find('.js_product')),
//                variant_values: self.getSelectedVariantValues($form.find('.js_product')),
//                no_variant_attribute_values: self.getNoVariantAttributeValues($form.find('.js_product'))
//            };
//
//            return self._onProductReady();
//        });
//    }
//
//       };
//   Registries.Component.extend(WebsiteSale, PosWebsiteSale);
//   return WebsiteSale;
//});