from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _
import requests
import logging
import time
import json
import firebase_admin
from firebase_admin import messaging
from firebase_admin import credentials
from firebase_admin import auth
from datetime import datetime
from time import sleep
 
_logger = logging.getLogger(__name__)


class FirebaseNotification(models.Model):
    _name = 'firebase.notification'

    title = fields.Char(string='English Notification Title', required=True, default="Default Title")
    fr_title = fields.Char(string='Frensh Notification Title', required=True, default="Default Frensh Title")
    read_state = fields.Boolean(string='Read by user', required=True, default=False)
    content = fields.Text(string='English Notification Content', required=True, default="Default Content")
    fr_content = fields.Text(string='Frensh Notification Content', required=True, default="Default Frensh Content")
    icon = fields.Char(string='Notification Icon URL')
    image = fields.Char(string='Notification Image URL')
    target_action = fields.Char(string='Target Action', default="FLUTTER_NOTIFICATION_CLICK")
    payload = fields.Char(string='payload', default=" ", required=True)
    notification_date = fields.Datetime(string='Notification Date')
    user_ids = fields.Many2many('res.users', 'notification_ids',
                                domain=[('firebase_account_id', '!=', False)],
                                string='Receivers')
    recipe_id = fields.Integer(string='Recipe ID')

    def send_notifications(self):
        tokens = self.user_ids.mapped('firebase_account_id').mapped('token')
        key = self.env['ir.config_parameter'].sudo().get_param('altanmya_firebase_notificator.firebase_key')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'key={key}',
        }
        url = 'https://fcm.googleapis.com/fcm/send'
        _logger.info('notification user ')
        _logger.info(self.user_ids)
        _logger.info(self.user_ids.preferred_language)
        if len(tokens) > 1:
            data = {
                "notification": {
                    'title': self.fr_title,
                    'body': self.fr_content,
                    'icon': self.icon,
                    'image': self.image,
                    'title_loc_key': "notification_title",
                    'body_loc_key': "title",
                    'click_action': self.target_action,
                    'payload': self.payload,
                    'sound': None,
                    'badge': None,
                },
                'dry_run': False,
                'priority': 'high',
                'content_available': True,
                'registration_ids': tokens,
            }

        else:
            if self.user_ids.preferred_language == 'en':
                data = {
                    "notification": {
                        'title': self.title,
                        'body': self.content,
                        'icon': self.icon,
                        #                     'image': self.image,
                        'title_loc_key': "notification_title",
                        'body_loc_key': "title",
                        'click_action': self.target_action,
                        'payload': self.payload,
                        'sound': None,
                        'badge': None,
                    },
                    'dry_run': False,
                    'priority': 'high',
                    'content_available': True,
                    'to': tokens[0] if type(tokens) == list and len(tokens) > 0 else tokens,
                }
            elif self.user_ids.preferred_language == 'fr':
                data = {
                    "notification": {
                        'title': self.fr_title,
                        'body': self.fr_content,
                        'icon': self.icon,
                        #                     'image': self.image,
                        'title_loc_key': "notification_title",
                        'body_loc_key': "title",
                        'click_action': self.target_action,
                        'payload': self.payload,
                        'sound': None,
                        'badge': None,
                    },
                    'dry_run': False,
                    'priority': 'high',
                    'content_available': True,
                    'to': tokens[0] if type(tokens) == list and len(tokens) > 0 else tokens,
                }
            else:
                data = {
                    "notification": {
                        'title': self.fr_title,
                        'body': self.fr_content,
                        'icon': self.icon,
                        #                     'image': self.image,
                        'title_loc_key': "notification_title",
                        'body_loc_key': "title",
                        'click_action': self.target_action,
                        'payload': self.payload,
                        'sound': None,
                        'badge': None,
                    },
                    'dry_run': False,
                    'priority': 'high',
                    'content_available': True,
                    'to': tokens[0] if type(tokens) == list and len(tokens) > 0 else tokens,
                }
        resp = requests.post(url, headers=headers, json=data)
        raise ValidationError(_(resp.text.encode('utf8')))

    def get_firebase_app(self):
        cred_info = {
            "type": "service_account",
            "project_id": "differs-2d6ab",
            "private_key_id": "1bef2dff29a2296f3134c8b291743c9249b7cd81",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDEx7KWK4XsA41A\n0Oan8yMmPf6/77eTti73/Ma1dZRLcUyt1ebOM1h07qE8rWZu2h3MHKJcN0A3MDxj\nLznAOljWrs+BgFcx4swv4+rJJGJHQVb2hjnFNpD/SZpU1zCqOLM5UCe70yWR9hAw\n9nmRH1euah6MbiSLl0MO463x0hShK89LxTP0Mn0bsEGTJb8R+iVv/Nc8hNBqGqpz\nMVxJrYFT76SLfwk6GpPqsXZ7kMjHrdL0UEyRCrtfdzOg9BCdrsmL5dL6jOuEahSQ\nwAqrgrFG+sidk+I1f6/gP7Sq81CCrYz19aCq0TVzmmFsDygiVs6mcwYW9YM3MjtQ\n8eF/TYnFAgMBAAECggEAF6qU1e7CGpKKyILXWtepII5QNzFTeNZua7DhDS3o+fHU\ncQvKyH3wY4/XoH6SVT6yWrwO4txaQsjwWlVxsqbRzHAV0NNoqT1HpXLZ5/sSPtOi\n699Uz10yryFhCFchKTfMhlYXkUVhvV5EsD7UfBmy5+0nY2hTyN4WWJIVd4H2rTNr\ncTUiarjFJeTDejn1ev0dZ5ydf0Ehxy8zpry/miV4ib11ThTBDV1eNb+tPFQLSrV4\nnX8Tr41q//n16WdaVuvh51fzMRFPHPWtvm6SSmwmFCmGVlBeNJp5/WZRun0YgzgY\nicZWCc0NY52LYxVRrKbYBQCqne33j8FGqFF2Yf8++QKBgQD2JSV6v7m1uG6N+TXy\nHh/ut5aAl0XofFBnrOvnxKdtuvQoagkuwA9W9mSdRM0y+IcRjLVRtvv9YYGUJCG6\nlM0BkMmWMNX3xwu80amsZng/0J45NLNYk6EWbPCudKc4Do77u3nlHrkWtdaAnyfB\nSSwOW9dJxcl6gpUfnhx3N0FozwKBgQDMqJYfMaPZrzIRLIAlp5J8uLlRpd/39pey\nPqAwzd81mKhelve7niWf+qt15IznHMBnRr8fiF6OyYHOaHLbH//1vI90rxDIiKlp\nWLP/h0ioJaGo0ER9x0NlKcQbbVrfmuEwkzAP/QVfnN2y62lLHLTlMVE9sb7rvkPo\nQ9D5qV3hKwKBgECp95OsxJvxzNFtc/ecZGUxQ8+abhoqdnEWI49qwVV5dOUdHjZy\n7FS7PCl4xrOqSMmafpPuD3s8X29MorPCnazYnazgPYXve6zqI7oP3W1eYALFToxp\nlDsw+XXLXZbDdFq7oMVJcfR+ZtC5fxcvIuzOwds2o7yUi5qXzgCfuoZPAoGAKOPO\nCrF6UTXlxPSlLeDLLcwiiqOfmgVUzbIhg16+qBC2Ix/6oyu3zLzioQ1m8Y4XCwth\niEVQzyqHmtvXhtxf4ZMo/mEz8z0KzBeC7xzycVYDdJ0X8iFr37x2iBxTObXSJEhk\nI+2jszS+Ps82HGHB6sDtwGvQ/3zmSHO0Pw2Nyj0CgYEAk2jcds2AemRJtqHW/74p\nDxWgwQl1OsjdLk02Egn9/RRcaubIx2Ud2SsQ+AT4MOGC3USfamIglXgxWVBYwe1Y\nVB/ElGnkz/GijLWnUtjXCXkxPSRtjVLegipZurE5ksu+pajYRm7SSOGIpUkpc4h6\nLKal9qhFZVyLHOVYpwmlVWw=\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-tx29x@differs-2d6ab.iam.gserviceaccount.com",
            "client_id": "104484343744146204081",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-tx29x%40differs-2d6ab.iam.gserviceaccount.com"
        }
        app = None
        try:
            cred = credentials.Certificate(cred_info)
            try:
                app = firebase_admin.get_app()
                return app
            except ValueError:
                app = firebase_admin.initialize_app(cred)
        except Exception as e:
            _logger.info(e)
            return app

    def send(self):
        tokens = self.user_ids.mapped('firebase_account_id').mapped('token')
        firebase_app = self.get_firebase_app()
        _logger.info('notification user')
        _logger.info(self.user_ids.name)
        _logger.info(self.user_ids.preferred_language)
        if len(self.user_ids) == 1:
            if self.user_ids.preferred_language == 'en':
                title = self.title
                content = self.content
            else:
                title = self.fr_title
                content = self.fr_content
                _logger.info(title)
                _logger.info(content)
        else:
            title = self.fr_title
            content = self.fr_content
        if tokens:
            if type(tokens) == list and len(tokens) == 1:
                if not self.notification_date:
                    self.notification_date = datetime.now()
                messages = [
                    messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=content,
                        ),
                        android=messaging.AndroidConfig(priority='high',
                                                        notification=messaging.AndroidNotification(sound='default',
                                                                                                   click_action=self.target_action,
                                                                                                   color='#61B559',
                                                                                                   title=title,
                                                                                                   body=content
                                                                                                   )),
                        data={'ios_click_action': self.target_action,
                              'recipe_id': str(self.recipe_id),
                              'payload': self.payload},
                        apns=messaging.APNSConfig(payload=messaging.APNSPayload(
                            aps=messaging.Aps(sound='default', alert=messaging.ApsAlert(
                                title=title,
                                body=content
                            )))),
                        token=tokens[0],
                    )]
                response = messaging.send_all(messages=messages, app=firebase_app, dry_run=False)
                odoo_notification_title = ''
                odoo_notification_message = ''
                odoo_notification_type = ''
                if response.success_count > 0:
                    odoo_notification_title = 'Successfully!'
                    odoo_notification_message = f'The notification have been sent to {response.success_count} user.'
                    odoo_notification_type = 'success'
                else:
                    odoo_notification_title = 'Failed !!'
                    odoo_notification_message = f'The notification have not been sent to {response.failure_count} user.'
                    odoo_notification_type = 'danger'
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': odoo_notification_title,
                        'message': odoo_notification_message,
                        'type': odoo_notification_type,  # types: success,warning,danger,info
                        'sticky': False,  # True/False will display for few seconds if false
                    }
                }
                return notification

            else:
                responses = []
                successful_responses = []
                for user in self.user_ids:
                    tokens = user.mapped('firebase_account_id').mapped('token')
                    if user.preferred_language == 'en':
                        title = self.title
                        content = self.content
                    else:
                        title = self.fr_title
                        content = self.fr_content

                    if not self.notification_date:
                        self.notification_date = datetime.now()
                    message = messaging.MulticastMessage(
                        notification=messaging.Notification(
                            title=title,
                            body=content,
                        ),
                        android=messaging.AndroidConfig(priority='high',
                                                        notification=messaging.AndroidNotification(sound='default',
                                                                                                   click_action=self.target_action,
                                                                                                   color='#61B559',
                                                                                                   title=title,
                                                                                                   body=content
                                                                                                   )),
                        data={'ios_click_action': self.target_action,
                              'recipe_id': str(self.recipe_id),
                              'payload': self.payload},
                        apns=messaging.APNSConfig(payload=messaging.APNSPayload(aps=messaging.Aps(sound='default',
                                                                                                  alert=messaging.ApsAlert(
                                                                                                      title=title,
                                                                                                      body=content
                                                                                                  )))),
                        tokens=tokens,
                    )
                    response = messaging.send_multicast(message, app=firebase_app)
                    responses.append(response)
                    if response.success_count > 0:
                        successful_responses.append(responses)

                odoo_notification_title = ''
                odoo_notification_message = ''
                odoo_notification_type = ''
                if len(responses) == len(successful_responses):
                    odoo_notification_title = 'Successfully!'
                    odoo_notification_message = f'The notification have been sent to {response.success_count} user.'
                    odoo_notification_type = 'success'
                else:
                    odoo_notification_title = 'Failed !!'
                    odoo_notification_message = f'The notification have not been sent to {response.failure_count} user.'
                    odoo_notification_type = 'danger'
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': odoo_notification_title,
                        'message': odoo_notification_message,
                        'type': odoo_notification_type,  # types: success,warning,danger,info
                        'sticky': False,  # True/False will display for few seconds if false
                    }
                }
                return notification

    @api.model
    def get_notifications_by_user(self, user_id: int):
        res = self.env['firebase.notification'].sudo().search_read([('user_ids', 'in', user_id), ('read_state', '!=', True)])
        _logger.info('notifications are : ')
        _logger.info(res)
        return res

    @api.model
    def get_notifications_length(self, user_id: int):
        res = len(self.env['firebase.notification'].sudo().search_read(
            [('user_ids', 'in', user_id), ('read_state', '=', False)]))
        _logger.info('notifications length : ')
        _logger.info(res)
        return res

    @api.model
    def update_notification_state(self, user_id: int):
        res = self.env['firebase.notification'].sudo().search([('user_ids', 'in', user_id)])
        for i in res:
            i.write({'read_state': True})
         
    @api.model
    def update_read_notification_state(self, notification_id: int):
        res = self.env['firebase.notification'].sudo().search([('id', '=', notification_id)])
        for i in res:
            i.write({'read_state': True})

