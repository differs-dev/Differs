from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _
import requests
import json
import time


class FirebaseUser(models.Model):
    _inherit = "res.users"

    firebase_account_id = fields.One2many("firebase.account", "user_id", string="Firebase User Account")
    notification_ids = fields.Many2many('firebase.notification', 'user_ids', string='Notifications')

    @api.model
    def get_notifications_count(self):
        return len(self.notification_ids)


class FirebaseAccount(models.Model):
    _name = "firebase.account"

    user_id = fields.Many2one('res.users', string="User")
    device = fields.Selection([('android', 'Android'), ('ios', 'IOS')],
                              string='Device OS')
    token = fields.Char(string="Firebase App Token",
                        default="ea4p9ezLTgqY5SZjP-ARRw:APA91bH2S5CeEGqJF7eT5w8zX6dsvY78Gm7TZN3PEK1-yZiV8akAHpK_bG2u3"
                                "WD-R28MPNPwGQ0LO3JAFX-nwQoeEPj-0rJUHetVHoKlOL-CJ9hKjX9feEl-iNFIQg3zkIshMlNylI_u")
    _sql_constraints = [('token', 'unique(token, device, user_id)', 'Token for each user')]


class FirebaseSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    firebase_key = fields.Char(string='Firebase Server Key', default="AAAAYG0uuDs:APA91bFLYnsM3kZtYevBH08XL2BQ1KH7KgB"
                                                                     "WpiAOPzxfV6k0AUXA89f7AOZgb5IMXJKrWUVSnBX5KdwlaGX"
                                                                     "HT7n2KmVhgG_JcZm_3H8_Lh1ybvq15RUmq_7NBLmFZKsj7W"
                                                                     "j0nqSntLaX",
                               help="Secret firebase server key")

    def set_values(self):
        res = super(FirebaseSetting, self).set_values()
        config_parameters = self.env['ir.config_parameter']
        config_parameters.sudo().set_param("altanmya_firebase_notificator.firebase_key", self.firebase_key)
        return res

    @api.model
    def get_values(self):
        res = super(FirebaseSetting, self).get_values()
        firebase_key = self.env['ir.config_parameter'].sudo().get_param('altanmya_firebase_notificator.firebase_key')
        if not firebase_key:
            firebase_key = "AAAAYG0uuDs:APA91bFLYnsM3kZtYevBH08XL2BQ1KH7KgBWpiAOPzxfV6k0AUXA89f7AOZgb5IM" \
                           "XJKrWUVSnBX5KdwlaGXHT7n2KmVhgG_JcZm_3H8_Lh1ybvq15RUmq_7NBLmFZKsj7Wj0nqSntLaX"
        res.update(firebase_key=firebase_key)
        return res
