# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'

    def differs_process_coupon(self):
        """
        Apply the entered coupon code if valid, raise an UserError otherwise.
        """
        sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        error_status = self.apply_coupon(sales_order, self.coupon_code)
        return error_status
