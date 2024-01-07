from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from itertools import groupby
import logging
import pytz
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class SaleOrderInerit(models.Model):
    _inherit = 'sale.order'

    cart_products_qty = fields.Integer(string='Cart Quantity', compute='_compute_cart_qty')
    order_review = fields.Many2one('tanmya.review', string='Order Review')
    is_order_bought_again = fields.Boolean(string='Is Order Bought Again')

    #################################
    delivery_address = fields.Many2one('additional.address', compute='_compute_delivery_address')
    # delivery_period = fields.Selection([('before_5_30', 'Before 5:30 PM'),
    #                                     ('after_5_30', 'After 5:30 PM')],
    #                                    string='Delivery Period')
    delivery_period1 = fields.Char(string='Delivery Period')
    delivery_area = fields.Selection([('drive_out_of_area', 'Drive Out Of Area'),
                                      ('out_of_area', 'Out Of Area')],
                                     string='Delivery Area')
    delivery_date = fields.Date(string='Delivery Date')

    @api.onchange('partner_id.main_address_id')
    def _compute_delivery_address(self):
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.main_address_id:
                    if rec.partner_id.main_address_id > 0:
                        rec.delivery_address = rec.partner_id.main_address_id
                    else:
                        rec.delivery_address = False

    # Create new cart (sale_order record)
    @api.model
    def init_new_cart(self):
        user_id = self.env.uid
        if user_id:
            user = self.env['res.users'].sudo().search([('id', '=', user_id)])
            if user:
                sale_order_vals = {
                    'partner_id': user.partner_id.id,
                    'company_id': 1,
                    'date_order': datetime.now(),
                    'state': 'draft',
                }
                new_sale_order = self.env['sale.order'].sudo().create(sale_order_vals)
                return new_sale_order
        return False

    # Get last cart(sale_order record) for specific user
    @api.model
    def get_user_cart(self):
        user_id = self.env.uid
        if user_id:
            user = self.env['res.users'].sudo().search([('id', '=', user_id)])
            if self.env.user.preferred_language == 'fr':
                user_lang = 'fr_FR'
            else:
                user_lang = 'en_US'
            user_sale_order = self.env['sale.order'].with_context(lang=user_lang).sudo().search([('partner_id', '=', user.partner_id.id),
                                                                    ('state', '=', 'draft')],
                                                                   order='date_order desc', limit=1)
            _logger.info(f'user sale order : {user_sale_order}')
            user_sale_order_not_localized = self.env['sale.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                    ('state', '=', 'draft')],
                                                                   order='date_order desc', limit=1)
            _logger.info(f'user sale order not localized : {user_sale_order_not_localized}')
            total_service_lines = 0
            order_lines = self.env['sale.order.line'].sudo().search([('order_id', '=', user_sale_order.id)])
            for line in order_lines:
                if line.product_id.detailed_type == 'service':
                    total_service_lines += 1

            _logger.info(f'reason is : {total_service_lines} != {len(order_lines)}')
            if user_sale_order and ((total_service_lines != len(order_lines)) or len(order_lines) == 0):
                return user_sale_order
            else:
                return self.init_new_cart()

        print("Invalid User ID!")
        return False

        # Get last cart(sale_order record) for specific user

    @api.model
    def get_user_cart_qun(self):
        _logger.info('------------------------ get user cart qun ------------------------')
        user_id = self.env.uid
        if user_id:
            user = self.env['res.users'].sudo().search([('id', '=', user_id)])
            user_sale_order = self.env['sale.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                    ('state', '=', 'draft')],
                                                                   order='date_order desc', limit=1).order_line
            
            if user_sale_order:
                _logger.info('orders length')
                _logger.info(len(user_sale_order.filtered(lambda r: r.product_id.detailed_type != 'service')))
                return len(user_sale_order.filtered(lambda r: r.product_id.detailed_type != 'service'))
            else:
                return '0'

        print("Invalid User ID!")
        return False

    # Delete user cart
    @api.model
    def delete_user_cart(self):
        user_sale_order = self.get_user_cart()
        if user_sale_order:
            user_sale_order.unlink()
            return True
        return False

    @api.model
    def check_product_in_cart(self, product_id: int):
        user_sale_order = self.get_user_cart()
        if user_sale_order:
            order_lines = self.env['sale.order.line'].sudo().search([('order_id', '=', user_sale_order.id)])
            for line in order_lines:
                if line.product_id.id == product_id:
                    return True
        return False
 
    
    # Add new product(recipe or ingredient) to cart
    @api.model
    def add_to_cart(self, product_id: int, product_qty: int):
        user_sale_order = self.get_user_cart()
        if not user_sale_order:
            user_sale_order = self.init_new_cart()

        if user_sale_order and product_id:
            product = self.env['product.product'].sudo().search([('id', '=', product_id)])
            if product.recipe_status == 'public' or product.product_tmpl_id.detailed_type == 'service':
                price = product.lst_price
            else:
                price = product.product_tmpl_id.compute_variant_price_from_pricelist(product.id)
            _logger.info('price in add to cart')
            _logger.info(price)
            sale_order_line_vals = {
                'order_id': user_sale_order.id,
                'name': product.product_tmpl_id.name,
                # 'price_unit': product.lst_price,
                'price_unit': price,
                'product_id': int(product_id),
                'product_uom_qty': float(product_qty) or 1.0,
                'product_uom': product.uom_id.id,
                'order_partner_id': user_sale_order.partner_id.id,
                'customer_lead': 0}
            new_sale_order_line = self.env['sale.order.line'].sudo().create(sale_order_line_vals)
            if new_sale_order_line:
                return True

        return False
    @api.model
    def add_mass_to_cart(self, products_ids, products_qty):
        user_sale_order = self.get_user_cart()
        if not user_sale_order:
            user_sale_order = self.init_new_cart()
        i = 0
        if user_sale_order and products_ids:
            sale_order_line_vals = []
            for prod in products_ids:
                product = self.env['product.product'].sudo().search([('id', '=', prod)])
                if not self.check_product_in_cart(int(prod)):
                    if product.recipe_status == 'public' or product.product_tmpl_id.detailed_type == 'service':
                        price = product.lst_price
                    else:
                        price = product.product_tmpl_id.compute_variant_price_from_pricelist(product.id)
                    _logger.info('price in add to cart')
                    _logger.info(price)
                    _logger.info(products_qty[i])
                    _logger.info(float(products_qty[i]))
                    sale_order_line_vals.append({
                        'order_id': user_sale_order.id,
                        'name': product.product_tmpl_id.name,
                        # 'price_unit': product.lst_price,
                        'price_unit': price,
                        'product_id': int(prod),
                        'product_uom_qty': float(products_qty[i]) or 1.0,
                        'product_uom': product.uom_id.id,
                        # 'product_uom': 1,
                        'order_partner_id': user_sale_order.partner_id.id,
                        'customer_lead': 0})
                i += 1
            _logger.info('vals ::::::::::::::::::')
            _logger.info(sale_order_line_vals)
            new_sale_order_line = self.env['sale.order.line'].sudo().create(sale_order_line_vals)
                # if new_sale_order_line:
            return True

        return False

    # Delete product from cart
    @api.model
    def delete_from_cart(self, line_id: int):
        if line_id:
            line = self.env['sale.order.line'].sudo().search([('id', '=', line_id)])
            line.unlink()
            return True
        return False

    # Edit quantity of any product in cart
    @api.model
    def cart_update(self, line_id=0, add_qty=0):
        if line_id:
            line = self.env['sale.order.line'].sudo().search([('id', '=', line_id)])
            line.product_uom_qty += add_qty
            if line.product_uom_qty <= 0:
                line.unlink()
            return self.get_cart_details(5)

        return False

    @api.model
    def cart_update_no_details(self, line_id=0, add_qty=0):
        if line_id:
            line = self.env['sale.order.line'].sudo().search([('id', '=', line_id)])
            line.product_uom_qty += add_qty
            if line.product_uom_qty <= 0:
                line.unlink()
            return self.get_cart_total()

        return False
        
    @api.depends('order_line.product_uom_qty', 'order_line.product_id')
    def _compute_cart_qty(self):
        for order in self:
            order.cart_products_qty = int(sum(order.mapped('order_line.product_uom_qty')))

    def get_variant_attributes(self, product_id):
        product = self.env['product.product'].sudo().browse(product_id)
        product_attributes = ''
        if product:
            if product.product_template_attribute_value_ids:
                if len(product.product_template_attribute_value_ids) > 0:
                    product_attributes = product.product_template_attribute_value_ids[0].attribute_id.name + ': ' + \
                                         product.product_template_attribute_value_ids[0].product_attribute_value_id.name
        return product_attributes

    @api.model
    def get_cart_total(self):
        user_sale_order = self.get_user_cart()
        if user_sale_order:
            sale_order_details = {
                'id': user_sale_order.id,
                'amount_total': user_sale_order.amount_total,
            }
            return sale_order_details
        return False
    
    # Get details of user cart
    @api.model
    def get_cart_details(self, offset):
        _logger.info('------------------------ get cart details --------------------------')
        user_sale_order = self.get_user_cart()
        if user_sale_order:
            order_line = []
            coupon_discount = 0.0
            i = 1
            for line in user_sale_order.order_line:
                if i < (offset - 4):
                    i += 1
                    continue
                if i > offset:
                    break
                if line.product_id.detailed_type != 'service':
                    # product = self.env['product.product'].sudo().search([('product_tmpl_id', '=', line.product_id.id)])
                    # if product.recipe_status == 'public':
                    #     price = product.lst_price
                    # else:
                    #     price = product.product_tmpl_id.compute_variant_price_from_pricelist(product.id)
                    _logger.info('price of the product in the cart is ')
                    _logger.info(line.product_id.name)
                    _logger.info(line.price_unit)
                    line_details = {
                        'id': line.id,
                        'product': {
                            'kit_template': line.product_id.kit_template.id,
                            'name': line.product_id.name,
                            # this line was changed from this :  line.product_id.image_1920 to this ''.
                            'image': line.product_id.image_1920 or '',
                            'product_attributes': self.get_variant_attributes(line.product_id.id)},
                        'price': line.price_unit,
                        # 'price': price,
                        'quantity': line.product_uom_qty,
                        'uom': line.product_uom.name,
                        'currency': line.currency_id.name,
                        'price_total': line.price_total,
                    }
                    if line.price_unit < 0:
                        coupon_discount += line.price_unit * line.product_uom_qty
                    order_line.append(line_details)
                    i += 1
            sale_order_details = {
                'id': user_sale_order.id,
                'amount_total': user_sale_order.amount_total,
                'order_line': order_line,
                'cart_quantity': user_sale_order.cart_products_qty,
                'state': user_sale_order.state,
                'date_order': user_sale_order.date_order,
                'coupon_discount': coupon_discount,
                'total_number_of_lines': len(user_sale_order.order_line)
            }
            _logger.info('------------------------ end get cart details --------------------------')
            return sale_order_details
        return False

    def get_sale_order_details(self, sale_order):
        if sale_order:
            order_line = []
            total_without_charges = 0
            delivery_charge = 0
            for line in sale_order.order_line:
                line_details = {
                    'id': line.id,
                    'product': {
                        'kit_template': line.product_id.kit_template.id,
                        'name': line.product_id.name,
                        'image': line.product_id.image_1920 or ''},
                    'price': line.price_unit,
                    'quantity': line.product_uom_qty,
                    'uom': line.product_uom.name,
                    'currency': line.currency_id.name,
                    'price_total': line.price_total,
                }
                if line.product_id.detailed_type != 'service':
                    total_without_charges += line.price_total
                elif line.product_id.detailed_type == 'service':
                    related_delivery_method = self.env['delivery.carrier'].sudo().search([('product_id', '=', line.product_id.id)])
                    if related_delivery_method:
                        delivery_charge += line.price_total
                    _logger.info('delivery product')
                    _logger.info(line.product_id.name)
                    _logger.info(line.price_total)
                order_line.append(line_details)
            _logger.info('delivery_area: ------------------------------------')
            _logger.info(sale_order.delivery_area)
            _logger.info(total_without_charges)
            # if sale_order.delivery_area == 'out_of_area':
            # delivery_charge = (sale_order.amount_total - total_without_charges)
            
            sale_order_details = {
                'id': sale_order.id,
                'amount_total': sale_order.amount_total,
                'order_line': order_line,
                'cart_quantity': sale_order.cart_products_qty,
                'state': sale_order.state,
                'date_order': sale_order.date_order,
                'delivery_charge': delivery_charge
            }
            return sale_order_details

    @api.model
    def get_user_carts_history(self, limit=None, offset=0):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            user_sale_orders = self.env['sale.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                     ('state', '=', 'sale')],
                                                                    limit=limit,
                                                                    offset=offset,
                                                                    order='date_order desc')
            if user_sale_orders:
                user_carts = []
                for sale_order in user_sale_orders:
                    if sale_order.picking_ids:
                        if sale_order.picking_ids[0].state == 'done':
                            user_carts.append(self.get_sale_order_details(sale_order))
                return user_carts
        return []

    @api.model
    def get_user_carts_history_length(self):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            user_sale_orders = self.env['sale.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                     ('state', '=', 'sale')],
                                                                    order='date_order desc')
            if user_sale_orders:
                user_carts = []
                for sale_order in user_sale_orders:
                    if sale_order.picking_ids:
                        if sale_order.picking_ids[0].state == 'done':
                            user_carts.append(self.get_sale_order_details(sale_order))
                return len(user_carts)
        return 0

    @api.model
    def get_user_carts_ongoing(self, limit=None, offset=0, current_ids=[]):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            user_sale_orders = self.env['sale.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                     ('state', '=', 'sale'),
                                                                     ('invoice_ids.payment_state', '=', 'paid'),
                                                                     ('id', 'not in', current_ids)],
                                                                    limit=limit,
                                                                    offset=offset,
                                                                    order='date_order desc')
            _logger.info('user sale orders')
            _logger.info(user_sale_orders)
            if user_sale_orders:
                user_carts = []
                for sale_order in user_sale_orders:
                    _logger.info('sale order info are : -------------')
                    _logger.info(sale_order.amount_total)
                    _logger.info(sale_order.delivery_area)
                    # if sale_order.delivery_area == 'out_of_area':
                    #     sale_order.amount_total += 200
                    if sale_order.picking_ids:
                        if sale_order.picking_ids[0].state != 'done':
                            user_carts.append(self.get_sale_order_details(sale_order))
                return user_carts
        return []

    @api.model
    def get_user_carts_ongoing_length(self):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            user_sale_orders = self.env['sale.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                     ('state', '=', 'sale'),
                                                                     ('invoice_ids.payment_state', '=', 'paid')],
                                                                    order='date_order desc')
            if user_sale_orders:
                user_carts = []
                for sale_order in user_sale_orders:
                    _logger.info('sale order info are : -------------')
                    _logger.info(sale_order.amount_total)
                    _logger.info(sale_order.delivery_area)
                    # if sale_order.delivery_area == 'out_of_area':
                    #     sale_order.amount_total += 200
                    if sale_order.picking_ids:
                        if sale_order.picking_ids[0].state != 'done':
                            user_carts.append(self.get_sale_order_details(sale_order))
                return len(user_carts)
        return 0
    
    @api.model
    def create_cash_statement(self, invoice_name, payaction):
        last_payment = self.env['account.payment'].sudo().browse(payaction['res_id'])
        last_journal = self.env['account.bank.statement'].sudo().search([
            ('journal_id', '=', last_payment.journal_id.id)],
            order='id desc', limit=1)
        lastpaymentid = last_payment.id
        journal_id = last_payment.journal_id.id
        date = last_payment.date
        nn = last_payment.name
        partner_id = last_payment.partner_id.id
        amount = last_payment.amount
        currency_id = last_payment.currency_id.id

        starting_balance = 0.00

        if last_journal:
            starting_balance = last_journal.balance_end_real
        ending_balance = starting_balance + amount
        computed_balance = amount
        line_payment_ref = last_payment.ref
        statement = self.env['account.bank.statement'].sudo().create({
            'journal_id': journal_id,
            'date': date,
            # 'balance_start': starting_balance,
            'balance_end_real': ending_balance,
            # 'balance_end': computed_balance,
            'state': 'open',
            'line_ids': [
                (0, 0, {
                    'payment_id': lastpaymentid,
                    'payment_ref': invoice_name,
                    'partner_id': last_payment.partner_id.id,
                    'amount': amount,
                    'date': date
                })
            ]
        })
        line_date = date
        line_partner_id = partner_id
        line_amount = amount
        line_journal_id = journal_id
        line_statement_id = statement.id
        line_counterpart_account_id = statement.journal_id.profit_account_id.id
        statement.button_post()
        statement.action_bank_reconcile_bank_statements()
        annos = self.env['account.reconcile.model'].sudo().browse(2)
        annos._apply_rules(statement.line_ids)
        #         _logger.info('------------------------++++++++++++++++++++++++++++++++++++++++++++++++++')
        #         _logger.info(annos.name)
        #         _logger.info(statement.state)
        #         _logger.info(statement.line_ids[0].payment_ref)
        #         _logger.info(statement.line_ids[0].partner_id.name)
        #         _logger.info(statement.line_ids[0].amount)
        #         _logger.info(statement.all_lines_reconciled)
        #         for line in statement.line_ids:
        #             _logger.info(line.is_reconciled)
        #         _logger.info('------------------------++++++++++++++++++++++++++++++++++++++++++++++++++')
        statement.button_validate_or_action()

    @api.model
    def payment_automation(self):
        for rec in self:
            odoobot = rec.env['res.users'].sudo().browse(1)

            odoobot_tz = odoobot.env.user.tz
            if not odoobot_tz:
                odoobot_tz = 'Europe/Paris'

            tt = datetime.now(pytz.timezone(odoobot_tz)).strftime('%z')
            diff_hour = int(tt[1:3]) + int(tt[3:]) / 60
            seq_transaction = 0
            rec_date_order = datetime.strptime('01/08/2015', '%d/%m/%Y').date()

            rec_date_order = rec.date_order
            rec_date_order2 = rec_date_order + timedelta(hours=3)  # diff_hour
            rec_date_order_invoice = datetime(rec_date_order2.year, rec_date_order2.month, rec_date_order2.day)

            if rec.state == 'sale':
            #     try:
            #         super(SaleOrderInerit, rec)._action_cancel()
            #     except:
            #         super(SaleOrderInerit, rec).action_cancel()
            #     rec.action_draft()
                # # rec._modify_corder()
                # try:
                #     rec.saletype = False
                # except:
                #     pass
                # rec.action_confirm()

                rec.date_order = rec_date_order
                super(SaleOrderInerit, rec)._create_invoices(final=True)
                rec.invoice_ids.invoice_date = rec_date_order_invoice

                rec.invoice_ids.action_post()
                inv_name = None
                for ii in rec.invoice_ids:
                    inv_name = ii.name

                ctx = dict(
                    active_ids=rec.invoice_ids.ids,
                    active_orders=rec.ids,
                    active_model='account.move')

                register_payment_wizard = self.env['account.payment.register'].sudo().with_context(ctx).create(
                    {
                        'amount': rec.invoice_ids.amount_residual,
                        'currency_id': rec.invoice_ids.currency_id.id,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'payment_method_line_id': 1,
                        'payment_date': rec_date_order_invoice
                    })
                pay_action = register_payment_wizard.action_create_payments()

                ##############################################
                qry = f"""
                        update account_move aa
                        set date='{rec_date_order_invoice}'
                        where aa.ref='{inv_name}' or aa.name='{inv_name}'
                        """
                self._cr.execute(qry)
                qry = f"""
                        update account_move_line aa
                        set date=(select MM.date from account_move  MM where  MM.id=aa.move_id)
                        where aa.ref='{inv_name}' or aa.move_name='{inv_name}'
                        """
                self._cr.execute(qry)
                self.create_cash_statement(inv_name, pay_action)
                if seq_transaction % 10 == 0:
                    self._cr.commit()
                ###############################################

    @api.model
    def add_order_review(self, review_vals, order_id):
        # review_vals = {
        #     'review_text': 'review_text',
        #     'rating': 'rating',
        # }
        if review_vals:
            review_vals['user_id'] = self.env.uid
            review_vals['review_date'] = datetime.now()
            order_review = self.env['tanmya.review'].sudo().create(review_vals)
            user_sale_order = self.env['sale.order'].sudo().search([('id', '=', order_id)])
            if user_sale_order:
                user_sale_order.order_review = order_review.id
                return True
        return False

    @api.model
    def get_order_review(self, order_id):
        sale_order = self.env['sale.order'].sudo().search([('id', '=', order_id)])
        if sale_order:
            if sale_order.order_review:
                sale_order_review = {
                    'review_text': sale_order.order_review.review_text,
                    'rating': sale_order.order_review.rating,
                    'review_date': str(sale_order.order_review.review_date),
                }
                return [sale_order_review]
        return []

    @api.model
    def check_if_order_is_bought_again(self, order_id):
        order = self.env['sale.order'].sudo().search([('id', '=', order_id)])
        _logger.info('is_order_bought_again ? ')
        _logger.info(order.is_order_bought_again)
        if order.is_order_bought_again:
            return True
        
        else:
            return False

    @api.model
    def buy_order_again(self, order_id):
        old_order = self.env['sale.order'].sudo().search([('id', '=', order_id)])
        old_order.is_order_bought_again = True
        user_order = self.get_user_cart()
        for line in old_order.order_line:
            if line.product_id.detailed_type != 'service':
                # new_line = line.copy()
                line_vals = line.copy_data()[0]
                line_vals['order_id'] = user_order.id
                new_line = self.env['sale.order.line'].sudo().create(line_vals)
                user_order.order_line = [(4, new_line.id)]

    @api.model
    def apply_coupon_automation(self, cuopon_code):
        user_sale_order = self.get_user_cart()
        if user_sale_order:
            sale_coupon_wizard = self.env['sale.coupon.apply.code'].sudo().with_context(
                active_id=user_sale_order.id).create({'coupon_code': cuopon_code})
            if sale_coupon_wizard:
                error_status = {}
                old_total_price = user_sale_order.amount_total
                try:
                    error_status = sale_coupon_wizard.differs_process_coupon()
                    error_status['old_total_price'] = old_total_price
                    _logger.info('------------- error status ---------------------')
                    _logger.info(error_status)
                    return error_status
                except UserError as e:
                    print(e)
                    error_status['old_total_price'] = old_total_price
                    _logger.info('------------- error status ---------------------')
                    _logger.info(error_status)
                    return error_status


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    check_notification = fields.Boolean(string='Check Notification', default=False)

    def write(self, data):
        res = super(StockPicking, self).write(data)
        if data.get('state') == 'done':
            _logger.info(f'picking data : {data}')
        return res
    
    @api.depends('move_lines.state', 'move_lines.date', 'move_type')
    def _compute_scheduled_date(self):
        for picking in self:
            if self.sale_id.delivery_date:
                picking.scheduled_date = self.sale_id.delivery_date
            else:
                moves_dates = picking.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')).mapped('date')
                if picking.move_type == 'direct':
                    picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
                else:
                    picking.scheduled_date = max(moves_dates, default=picking.scheduled_date or fields.Datetime.now())

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        _logger.info('validate button triggered !!!!!!!!!!!!!!!!!!!!!!!!!!!')
        order = self.env['sale.order'].sudo().search([('name', '=', self.origin)])
        _logger.info(f'order name {order.name}')
        if order:
            order_user = self.env['res.users'].sudo().search([('partner_id', '=', order.partner_id.id)])
            if not order_user:
                return temp
            order_picking_ids = order.picking_ids
            if order_picking_ids and len(order_picking_ids) > 1:
                first_pick = self.env['stock.picking'].sudo().search(
                    [('id', 'in', order_picking_ids.ids),
                     ('location_dest_id', '=', 5),
                     ('state', '!=', 'cancel')])
                if first_pick and len(first_pick) == 1 and \
                        first_pick.state == 'done' and not first_pick.check_notification:
                    # Send notification when order is delivered
                    if order_user.preferred_language == 'en':
                        notification_vals = {
                            'title': 'Order delivered',
                            'content': f'Order #{order.name} was successfully delivered to you.'
                                       'Click here to place a new order',
                            'fr_title': 'commande livrée',
                            'fr_content': f'La commande  #{order.name} vous a été livrée avec succès'
                                       ' Cliquez ici pour passer une nouvelle commande',
                            'payload': 'order_delivered',
                            'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                            'notification_date': datetime.now(),
                            'user_ids': [(6, 0, [order_user.id])],
                        }
                    else:
                        notification_vals = {
                            'title': 'Order delivered',
                            'content': f'Order #{order.name} was successfully delivered to you.'
                                       'Click here to place a new order',
                            'fr_title': 'commande livrée',
                            'fr_content': f'La commande  #{order.name} vous a été livrée avec succès'
                                       ' Cliquez ici pour passer une nouvelle commande',
                            'payload': 'order_delivered',
                            'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                            'notification_date': datetime.now(),
                            'user_ids': [(6, 0, [order_user.id])],
                        }
                    notification = self.env['firebase.notification'].sudo().create(notification_vals)
                    if notification:
                        notification.send()
                        first_pick.check_notification = True
        return res

class ImmediateStockPicking(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.immediate_transfer_line_ids:
            if line.to_immediate is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for picking in pickings_to_do:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(
                            _("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            picking.move_lines._set_quantities_to_reservation()

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate)
            pickings_to_validate = pickings_to_validate - pickings_not_to_do
            temp = pickings_to_validate.with_context(skip_immediate=True).button_validate()

            if len(pickings_to_validate) > 0:
                pick = pickings_to_validate[0]
                if pick:
                    order = self.env['sale.order'].sudo().search([('name', '=', pick.origin)])
                    if order:
                        order_user = self.env['res.users'].sudo().search([('partner_id', '=', order.partner_id.id)])
                        if not order_user:
                            return temp
                        order_picking_ids = order.picking_ids
                        if order_picking_ids and len(order_picking_ids) > 1:
                            first_pick = self.env['stock.picking'].sudo().search(
                                [('id', 'in', order_picking_ids.ids),
                                 ('location_dest_id', '=', 5),
                                 ('state', '!=', 'cancel')])
                            if first_pick and len(first_pick) == 1 and \
                                    first_pick.state == 'done' and not first_pick.check_notification:
                                # Send notification when order is delivered
                                if order_user.preferred_language == 'en':
                                    notification_vals = {
                                        'title': 'Order delivered',
                                        'content': f'Order #{order.name} was successfully delivered to you.'
                                                   'Click here to place a new order',
                                        'fr_title': 'commande livrée',
                                        'fr_content': f'La commande  #{order.name} vous a été livrée avec succès'
                                                   ' Cliquez ici pour passer une nouvelle commande',
                                        'payload': 'order_delivered',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'notification_date': datetime.now(),
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                else:
                                    notification_vals = {
                                        'title': 'Order delivered',
                                        'content': f'Order #{order.name} was successfully delivered to you.'
                                                   'Click here to place a new order',
                                        'fr_title': 'commande livrée',
                                        'fr_content': f'La commande  #{order.name} vous a été livrée avec succès'
                                                   ' Cliquez ici pour passer une nouvelle commande',
                                        'payload': 'order_delivered',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'notification_date': datetime.now(),
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                notification = self.env['firebase.notification'].sudo().create(notification_vals)
                                if notification:
                                    notification.send()
                                    first_pick.check_notification = True
                            second_pick = self.env['stock.picking'].sudo().search(
                                [('id', 'in', order_picking_ids.ids),
                                 ('location_dest_id', '=', 11),
                                 ('state', '!=', 'cancel')])
                            if second_pick and len(second_pick) == 1 and \
                                    second_pick.state == 'done' and not second_pick.check_notification:
                                # Send notification when order is on its way to customer
                                if order_user.preferred_language == 'en':
                                    notification_vals = {
                                        'title': 'Order on its way',
                                        'content': 'Your order is on its way to you.',
                                        'fr_title': 'Commande en cours',
                                        'fr_content': 'Votre commande est en route vers vous.',
                                        'payload': 'order_on_its_way',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'notification_date': datetime.now(),
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                else:
                                    notification_vals = {
                                        'title': 'Order on its way',
                                        'content': 'Your order is on its way to you.',
                                        'fr_title': 'Commande en cours',
                                        'fr_content': 'Votre commande est en route vers vous.',
                                        'payload': 'order_on_its_way',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'notification_date': datetime.now(),
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                notification = self.env['firebase.notification'].sudo().create(notification_vals)
                                if notification:
                                    notification.send()
                                    second_pick.check_notification = True

            return temp
        return True


class StockBackOrderConfirmation1(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.backorder_confirmation_line_ids:
            if line.to_backorder is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for pick_id in pickings_not_to_do:
            moves_to_log = {}
            for move in pick_id.move_lines:
                if float_compare(move.product_uom_qty,
                                 move.quantity_done,
                                 precision_rounding=move.product_uom.rounding) > 0:
                    moves_to_log[move] = (move.quantity_done, move.product_uom_qty)
            pick_id._log_less_quantities_than_expected(moves_to_log)

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(
                skip_backorder=True)
            if pickings_not_to_do:
                pickings_to_validate = pickings_to_validate.with_context(
                    picking_ids_not_to_backorder=pickings_not_to_do.ids)
            temp = pickings_to_validate.button_validate()

            if len(pickings_to_validate) > 0:
                pick = self.env['stock.picking'].sudo().browse(pickings_to_validate[0])
                if not isinstance(pickings_to_validate[0], int):
                    origin = pickings_to_validate[0].origin
                else:
                    origin = pick.origin
                _logger.info(f'pick 1 : {pickings_to_validate[0]}')
                if pick:
                    _logger.info(f'pick : {pick}')
                    order = self.env['sale.order'].sudo().search([('name', '=', origin)])
                    if order:
                        order_user = self.env['res.users'].sudo().search([('partner_id', '=', order.partner_id.id)])
                        if not order_user:
                            return temp
                        order_picking_ids = order.picking_ids
                        if order_picking_ids and len(order_picking_ids) > 1:
                            first_pick = self.env['stock.picking'].sudo().search(
                                [('id', 'in', order_picking_ids.ids),
                                 ('location_dest_id', '=', 5),
                                 ('state', '!=', 'cancel')])
                            _logger.info(f'first pick : {first_pick}')
                            if first_pick and len(first_pick) == 1 and \
                                    first_pick.state == 'done' and not first_pick.check_notification:
                                # Send notification when order is delivered
                                _logger.info(f'first pick state : {first_pick.state}')
                                _logger.info(first_pick.check_notification)
                                if order_user.preferred_language == 'en':
                                    notification_vals = {
                                        'title': 'Order delivered',
                                        'content': f'Order #{order.name} was successfully delivered to you.'
                                                   'Click here to place a new order',
                                        'fr_title': 'commande livrée',
                                        'fr_content': f'La commande  #{order.name} vous a été livrée avec succès'
                                                   'Cliquez ici pour passer une nouvelle commande',
                                        'notification_date': datetime.now(),
                                        'payload': 'order_delivered',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                else:
                                    notification_vals = {
                                        'title': 'Order delivered',
                                        'content': f'Order #{order.name} was successfully delivered to you.'
                                                   'Click here to place a new order',
                                        'fr_title': 'commande livrée',
                                        'fr_content': f'La commande  #{order.name} vous a été livrée avec succès'
                                                   ' Cliquez ici pour passer une nouvelle commande',
                                        'notification_date': datetime.now(),
                                        'payload': 'order_delivered',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                notification = self.env['firebase.notification'].sudo().create(notification_vals)
                                if notification:
                                    notification.send()
                                    first_pick.check_notification = True
                            second_pick = self.env['stock.picking'].sudo().search(
                                [('id', 'in', order_picking_ids.ids),
                                 ('location_dest_id', '=', 11),
                                 ('state', '!=', 'cancel')])
                            _logger.info(f'second pick : {second_pick}')
                            if second_pick and len(second_pick) == 1 and \
                                    second_pick.state == 'done' and not second_pick.check_notification:
                                # Send notification when order is on its way to customer
                                _logger.info(f'second pick state : {second_pick.state}')
                                _logger.info(second_pick.check_notification)
                                if order_user.preferred_language == 'en':
                                    notification_vals = {
                                        'title': 'Order on its way',
                                        'content': 'Your order is on its way to you.',
                                        'fr_title': 'Commande en cours',
                                        'fr_content': 'Votre commande est en route vers vous.',
                                        'notification_date': datetime.now(),
                                        'payload': 'order_on_its_way',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                else:
                                    notification_vals = {
                                        'title': 'Order on its way',
                                        'content': 'Your order is on its way to you.',
                                        'fr_title': 'Commande en cours',
                                        'fr_content': 'Votre commande est en route vers vous.',
                                        'notification_date': datetime.now(),
                                        'payload': 'order_on_its_way',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                notification = self.env['firebase.notification'].sudo().create(notification_vals)
                                if notification:
                                    notification.send()
                                    second_pick.check_notification = True

            return temp
        return True

    def process_cancel_backorder(self):
        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            temp = self.env['stock.picking'] \
                .browse(pickings_to_validate) \
                .with_context(skip_backorder=True, picking_ids_not_to_backorder=self.pick_ids.ids) \
                .button_validate()

            if len(pickings_to_validate) > 0:
                pick = self.env['stock.picking'].sudo().browse(pickings_to_validate[0])
                if pick:
                    order = self.env['sale.order'].sudo().search([('name', '=', pick.origin)])
                    if order:
                        order_user = self.env['res.users'].sudo().search([('partner_id', '=', order.partner_id.id)])
                        if not order_user:
                            return temp
                        order_picking_ids = order.picking_ids
                        if order_picking_ids and len(order_picking_ids) > 1:
                            first_pick = self.env['stock.picking'].sudo().search(
                                [('id', 'in', order_picking_ids.ids),
                                 ('location_dest_id', '=', 5),
                                 ('state', '!=', 'cancel')])
                            if first_pick and len(first_pick) == 1 and \
                                    first_pick.state == 'done' and not first_pick.check_notification:
                                # Send notification when order is delivered
                                if order_user.preferred_language == 'en':
                                    notification_vals = {
                                        'title': 'Order delivered',
                                        'content': f'Order #{order.name} was successfully delivered to you.'
                                                   'Click here to place a new order',
                                        'fr_title': 'commande livrée',
                                        'fr_content': f'La commande  #{order.name} vous a été livrée avec succès'
                                                       'Cliquez ici pour passer une nouvelle commande',
                                        'notification_date': datetime.now(),
                                        'payload': 'order_delivered',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                else:
                                    notification_vals = {
                                        'title': 'Order delivered',
                                        'content': f'Order #{order.name} was successfully delivered to you.'
                                                   'Click here to place a new order',
                                        'fr_title': 'commande livrée',
                                        'fr_content': f'La commande  #{order.name} vous a été livrée avec succès'
                                                       'Cliquez ici pour passer une nouvelle commande',
                                        'notification_date': datetime.now(),
                                        'payload': 'order_delivered',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                notification = self.env['firebase.notification'].sudo().create(notification_vals)
                                if notification:
                                    notification.send()
                                    first_pick.check_notification = True
                            second_pick = self.env['stock.picking'].sudo().search(
                                [('id', 'in', order_picking_ids.ids),
                                 ('location_dest_id', '=', 11),
                                 ('state', '!=', 'cancel')])
                            if second_pick and len(second_pick) == 1 and \
                                    second_pick.state == 'done' and not second_pick.check_notification:
                                # Send notification when order is on its way to customer
                                if order_user.preferred_language == 'en':
                                    notification_vals = {
                                        'title': 'Order on its way',
                                        'content': 'Your order is on its way to you.',
                                        'fr_title': 'Commande en cours',
                                        'fr_content': 'Votre commande est en route vers vous.',
                                        'notification_date': datetime.now(),
                                        'payload': 'order_on_its_way',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                else:
                                    notification_vals = {
                                        'title': 'Order on its way',
                                        'content': 'Your order is on its way to you.',
                                        'fr_title': 'Commande en cours',
                                        'fr_content': 'Votre commande est en route vers vous.',
                                        'notification_date': datetime.now(),
                                        'payload': 'order_on_its_way',
                                        'target_action': 'FLUTTER_NOTIFICATION_CLICK',
                                        'user_ids': [(6, 0, [order_user.id])],
                                    }
                                notification = self.env['firebase.notification'].sudo().create(notification_vals)
                                if notification:
                                    notification.send()
                                    second_pick.check_notification = True

            return temp
        return True
