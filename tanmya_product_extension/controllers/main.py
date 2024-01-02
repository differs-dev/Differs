import logging
import pprint
from odoo.fields import Command

from datetime import date, datetime, timedelta
import pytz

import requests
from requests.exceptions import ConnectionError, HTTPError
from werkzeug import urls

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

import os
import json

from ingenico.connect.sdk.factory import Factory
from ingenico.connect.sdk.domain.sessions.session_request import SessionRequest
from ingenico.connect.sdk.merchant.products.find_products_params import FindProductsParams
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

_logger = logging.getLogger(__name__)


class MobileApiController(http.Controller):

    @http.route('/mobile/payment/session', type='json', auth='none')
    def createSession(self, **data):
        print("create session called")
        # get session from ingenico platform

        with self.__get_client() as client:
            order = request.env['sale.order'].sudo().get_user_cart()

            query = FindProductsParams()
            query.country_code = order.partner_id.country_id.code if order else 'fr'
            query.currency_code = order.currency_id.name if order else 'EUR'
            query.locale = "en_US"
            query.amount = order.amount_total if order else 10000
            query.is_recurring = True
            query.add_hide("fields")

            response = client.merchant("DiFFERs").products().find(query)

            return response.to_dictionary()

    def __get_client(self):
        api_key_id = os.getenv("connect.api.apiKeyId", "3D84DF105C91D12A726C")
        secret_api_key = os.getenv("connect.api.secretApiKey",
                                   "YcpaJfKPjmRxUlaIZOQSQZCShTTKQTZwjxG4DPdh9Zrghb5iTTJwVMyV1GpFmZ9Obb6DMqvQAvmJhk7znwa7Mg==")
        configuration_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                               'conf.ini'))
        return Factory.create_client_from_file(configuration_file_name=configuration_file_name,
                                               api_key_id=api_key_id, secret_api_key=secret_api_key)

    @http.route('/mobile/payment/pay', type='json', auth='public')
    def mobilePay(self, **data):
        try:
            print("mobile pay")
            # get user sale order
            order = request.env['sale.order'].sudo().get_user_cart()
            if not order:
                return {
                    'state': 'error',
                    'state_message': "Cannot Find Client Order!",
                }
            
            # if data['delivery_area'] == 'out_of_area':
            #     shipping_method_delivery_service = request.env['product.product'].sudo().search([('name', '=', 'Delivery Out Of Area.')])
            #     order.add_to_cart(shipping_method_delivery_service.id, 1)
    
            #     order.amount_total += 200
            # order.amount_total += data['method_cost']
            _logger.info('------------------ amount_total with delivery charges -------------------------')
            _logger.info(order.amount_total)
            ogone_acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'ogone')], limit=1)
            if not ogone_acquirer:
                return {
                    'state': 'error',
                    'state_message': "Ogone acquirer not set on this server",
                }
    
            logged_in = not request.env.user._is_public()
    
            if not logged_in:
                return {
                    'state': 'error',
                    'state_message': "Access Denied!",
                }
            _logger.info('------ computing payment reference -------')
            reference = request.env['payment.transaction']._compute_reference(
                ogone_acquirer.provider,
                prefix=None,
                **{},
                **{'sale_order_ids': [Command.set([order.id])]}
            )
            _logger.info(reference)
            _logger.info(order.amount_total)
            # Create the transaction
            tx_sudo = request.env['payment.transaction'].sudo().create({
                'acquirer_id': ogone_acquirer.id,
                'reference': reference,
                'amount': order.amount_total,
                'currency_id': order.currency_id.id,
                'partner_id': order.partner_id.id,
                'token_id': None,
                'operation': f'online_direct',
                'tokenize': False,
                'landing_route': '/mobile/payment/validate',
                'sale_order_ids': [Command.set([order.id])],
            })
    
            tx_sudo = tx_sudo._send_payment_mobile_request(data)
            _logger.info('------- payment request was send ------')
            
            # Monitor the transaction to make it available in the portal
            PaymentPostProcessing.monitor_transactions(tx_sudo)
            values = tx_sudo._get_processing_values()
            
            _logger.info(tx_sudo.state)
            if tx_sudo.state != 'error':
                order.write({
                   'delivery_period1': data['delivery_period'],
                   'delivery_area': data['delivery_area'],
                   'delivery_date': data['delivery_date'],
                })
                _logger.info('------------------- delivery data -------------------------')
                _logger.info(data['delivery_area'])
                _logger.info(data['delivery_date'])
                _logger.info(data['delivery_period'])
                extra_charge = 0
                _logger.info('------------------ amount_total without delivery charges -------------------------')
                _logger.info(order.amount_total)
                shipping_method_service = request.env['delivery.carrier'].sudo().search([('id', '=', data['shipping_method_id'])]).product_id
                order.add_to_cart(shipping_method_service.id, 1)
                _logger.info(' ----------------------- shipping method -------------------------- ')
                _logger.info(shipping_method_service)
                
            message = ''
            if tx_sudo.state_message:
                message = tx_sudo.state_message
            elif tx_sudo.state == 'pending':
                message = tx_sudo.acquirer_id.pending_msg
            elif tx_sudo.state == 'done':
                order.with_context(send_email=True).action_confirm()
                order.payment_automation()
                message = tx_sudo.acquirer_id.done_msg
            elif tx_sudo.state == 'cancel':
                message = tx_sudo.acquirer_id.cancel_msg
            else:
                message = "Unkown Transaction State"
    
            values.update({
                'state': tx_sudo.state,
                'state_message': message,
                'last_state_change': tx_sudo.last_state_change,
                'order': tx_sudo.sale_order_ids
            })
            _logger.info(
                "transaction state is:\n%s" % tx_sudo.state_message
            )  # Log the payment request data without the password
            return values
        except e:
            request.env.cr.rollback()

    @http.route('/mobile/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def shop_payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :
         - UDPATE ME
        """
        print("validation payment called")
        raise ValidationError(_("payment validation %s %s" % (transaction_id, sale_order_id)))
