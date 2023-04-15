from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo import api, fields, models
from itertools import groupby
import logging
import pytz

_logger = logging.getLogger(__name__)


class SaleOrderInerit(models.Model):
    _inherit = 'sale.order'

    cart_products_qty = fields.Integer(string='Cart Quantity', compute='_compute_cart_qty')
    order_review = fields.Many2one('tanmya.review', string='Order Review')

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
            user_sale_order = self.env['sale.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                    ('state', '=', 'draft')],
                                                                   order='date_order desc', limit=1)
            if user_sale_order:
                return user_sale_order
            else:
                return self.init_new_cart()

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

    # Add new product(recipe or ingredient) to cart
    @api.model
    def add_to_cart(self, product_id: int, product_qty: int):
        user_sale_order = self.get_user_cart()
        if not user_sale_order:
            user_sale_order = self.init_new_cart()

        if user_sale_order and product_id:
            product = self.env['product.product'].sudo().search([('id', '=', product_id)])
            sale_order_line_vals = {
                'order_id': user_sale_order.id,
                'name': product.product_tmpl_id.name,
                'price_unit': product.product_tmpl_id.list_price,
                'product_id': product_id,
                'product_uom_qty': float(product_qty) or 1.0,
                'product_uom': product.uom_id.id,
                'order_partner_id': user_sale_order.partner_id.id,
                'customer_lead': 0}
            new_sale_order_line = self.env['sale.order.line'].sudo().create(sale_order_line_vals)
            if new_sale_order_line:
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
            if line.product_uom_qty == 0:
                line.unlink()
            return self.get_cart_details()

        return False

    @api.depends('order_line.product_uom_qty', 'order_line.product_id')
    def _compute_cart_qty(self):
        for order in self:
            order.cart_products_qty = int(sum(order.mapped('order_line.product_uom_qty')))

    # Get details of user cart
    @api.model
    def get_cart_details(self):
        user_sale_order = self.get_user_cart()
        if user_sale_order:
            order_line = []
            for line in user_sale_order.order_line:
                line_details = {
                    'id': line.id,
                    'product': {
                        'kit_template': line.product_id.kit_template.id,
                        'name': line.product_id.name,
                        'image': line.product_id.image_128 or ''},
                    'price': line.price_unit,
                    'quantity': line.product_uom_qty,
                    'uom': line.product_uom.name,
                    'currency': line.currency_id.name,
                    'price_total': line.price_total,
                }
                order_line.append(line_details)
            sale_order_details = {
                'id': user_sale_order.id,
                'amount_total': user_sale_order.amount_total,
                'order_line': order_line,
                'cart_quantity': user_sale_order.cart_products_qty,
                'state': user_sale_order.state,
                'date_order': user_sale_order.date_order,
            }
            return sale_order_details
        return False

    def get_sale_order_details(self, sale_order):
        if sale_order:
            order_line = []
            for line in sale_order.order_line:
                line_details = {
                    'id': line.id,
                    'product': {
                        'kit_template': line.product_id.kit_template.id,
                        'name': line.product_id.name,
                        'image': line.product_id.image_128 or ''},
                    'price': line.price_unit,
                    'quantity': line.product_uom_qty,
                    'uom': line.product_uom.name,
                    'currency': line.currency_id.name,
                    'price_total': line.price_total,
                }
                order_line.append(line_details)
            sale_order_details = {
                'id': sale_order.id,
                'amount_total': sale_order.amount_total,
                'order_line': order_line,
                'cart_quantity': sale_order.cart_products_qty,
                'state': sale_order.state,
                'date_order': sale_order.date_order,
            }
            return sale_order_details

    @api.model
    def get_user_carts_history(self):
        user = self.env['res.users'].sudo().search([('id', '=', self.env.uid)])
        if user:
            user_sale_orders = self.env['sale.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                    ('state', '=', 'sale')],
                                                                    order='date_order desc')
            if user_sale_orders:
                user_carts = []
                for sale_order in user_sale_orders:
                    user_carts.append(self.get_sale_order_details(sale_order))
                return user_carts
        return []

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
                try:
                    super(SaleOrderInerit, rec)._action_cancel()
                except:
                    super(SaleOrderInerit, rec).action_cancel()
                rec.action_draft()
                # rec._modify_corder()
                try:
                    rec.saletype = False
                except:
                    pass
                rec.action_confirm()

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
    def buy_order_again(self, order_id):
        old_order = self.env['sale.order'].sudo().search([('id', '=', order_id)])
        user_order = self.get_user_cart()
        for line in old_order.order_line:
            # new_line = line.copy()
            line_vals = line.copy_data()[0]
            line_vals['order_id'] = user_order.id
            new_line = self.env['sale.order.line'].sudo().create(line_vals)
            user_order.order_line = [(4, new_line.id)]
