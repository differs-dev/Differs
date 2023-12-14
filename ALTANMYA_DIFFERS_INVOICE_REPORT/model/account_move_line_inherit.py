from odoo import api, fields, models, _


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    referance_from_sale= fields.Char("reffff",compute="_compute_ref_from_sale")



    @api.depends('product_id')
    def _compute_ref_from_sale(self):
        for rec in self:
            for lines in rec:
                print("lineeees", lines.sale_line_ids.order_id.name)
                if lines.sale_line_ids.order_id.name :
                    rec.referance_from_sale = lines.sale_line_ids.order_id.name
                else:
                    rec.referance_from_sale=""
















