import logging
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class View(models.Model):
    _inherit = 'ir.ui.view'

    @api.constrains('type', 'groups_id', 'inherit_id')
    def _check_groups(self):
        for view in self:
            _logger.info('///////////////////////////////////////')
            _logger.info(view.name)
            _logger.info('////////////////////////////////////////')
            if (view.type == 'qweb' and
                    view.groups_id and
                    view.inherit_id and
                    view.mode != 'primary'):
                raise ValidationError(
                    _("Inherited Qweb view cannot have 'Groups' define on the record. Use 'groups' attributes inside the view definition"))

