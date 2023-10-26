# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from lxml import etree, objectify

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

from odoo.addons.payment import utils as payment_utils

try:
    from urllib.parse import urlencode
    from urllib.request import build_opener, Request, HTTPHandler
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib import urlencode
    from urllib2 import build_opener, Request, HTTPHandler, HTTPError, URLError
import json

_logger = logging.getLogger(__name__)

from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Cipher import AES
import base64

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    _checkout_url = 'v1/checkouts'
    key = "LTdkfot%6__@#DRTGce034cxs342dc!@".encode('utf-8')
    iv = bytes("Er5tgf#efctgvvfd", 'utf-8')
    
    def encrypto(self, plain_text):
        cipher = AES.new(self.key, AES.MODE_CFB, iv = self.iv, segment_size = 64)
        b = plain_text.encode("UTF-8")
        return cipher.encrypt(b)

    def decrypto(self, enc_text):
        base64_bytes = enc_text.encode('utf-8')
        message_bytes = base64.b64decode(base64_bytes)
        cipher = AES.new(self.key, AES.MODE_CFB, iv = self.iv, segment_size = 64)

        dec_text = cipher.decrypt(message_bytes)
        dec_text = [c.decode("utf-8") for c in [b'%c' % i for i in dec_text] if c.decode("utf-8").isprintable()]
        return ''.join(dec_text)
    
    def _send_payment_mobile_request(self, data):
        """ Override of payment to send a payment request to Ogone.
        Note: self.ensure_one()
        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        if self.provider != 'ogone':
            return

        # Make the payment request
        base_url = self.acquirer_id.get_base_url()
        data = {
            # DirectLink parameters
            'PSPID': self.acquirer_id.ogone_pspid,
            'ORDERID': self.reference,
            'USERID': self.acquirer_id.ogone_userid,
            'PSWD': self.acquirer_id.ogone_password,
            'AMOUNT': payment_utils.to_minor_currency_units(self.amount, None, 2),
            'CURRENCY': self.currency_id.name,
            'CN': self.decrypto(data['cn']),  # Cardholder Name
            'CVC': self.decrypto(data['cv']),
            'CARDNO': self.decrypto(data['co']),
            'ED': self.decrypto(data['cd']),
            'ECI': '7',
            'BRAND': data['brand'],
            'PM': "CreditCard",
            'EMAIL': self.partner_email or '',
            'OWNERADDRESS': self.partner_address or '',
            'OWNERZIP': self.partner_zip or '',
            'OWNERTOWN': self.partner_city or '',
            'OWNERCTY': self.partner_country_id.code or '',
            'OWNERTELNO': self.partner_phone or '',
            'OPERATION': 'SAL',  # direct sale
        }

        data['SHASIGN'] = self.acquirer_id._ogone_generate_signature(data, incoming=False)

        _logger.info(
            "making payment request:\n%s",
            pprint.pformat({k: v for k, v in data.items() if k != 'PSWD'})
        )  # Log the payment request data without the password

        response_content = self.acquirer_id._ogone_make_request(data)

        _logger.info('|||||||||| ogone response content ||||||||||||')
        _logger.info(response_content)
        try:
            tree = objectify.fromstring(response_content)
        except etree.XMLSyntaxError:
            raise ValidationError("Ogone: " + "Received badly structured response from the API.")

        # Handle the feedback data
        _logger.info(
            "received payment request response as an etree:\n%s",
            etree.tostring(tree, pretty_print=True, encoding='utf-8')
        )

        feedback_data = {'ORDERID': tree.get('orderID'), 'tree': tree}
        _logger.info("entering _handle_feedback_data with data:\n%s", pprint.pformat(feedback_data))
        return self._handle_feedback_data('ogone', feedback_data)
