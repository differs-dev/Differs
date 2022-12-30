# # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
from psycopg2 import Error as psycopg2_error
from odoo.exceptions import UserError
from collections import OrderedDict
from odoo import http, tools, _
from odoo.http import request
from datetime import datetime
import werkzeug
import psycopg2
import logging
import hashlib
import odoo


class BaseUnitPrice(http.Controller):
    pass

