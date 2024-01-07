from odoo import api, fields, models, _


class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    fax = fields.Char(string='Fax')
