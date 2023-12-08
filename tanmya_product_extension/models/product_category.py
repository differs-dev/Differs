from datetime import date, datetime, timedelta
from odoo import api, fields, models, tools
import logging
import time

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = "product.category"

    image = fields.Image(string='Image')

    def does_category_has_childs(self):
        if len(self.child_id.ids) > 0:
            return True
        else:
            return False

