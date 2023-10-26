from datetime import date, datetime, timedelta
from odoo import api, fields, models, tools
import logging
import time

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = "product.category"

    image = fields.Image(string='Image')
