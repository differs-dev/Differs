from odoo import api, SUPERUSER_ID


def approval_pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env['approval.category'].search([('name','=','Recipe Approval')]):
        return
    else:

        # cr = self._cr
        # cr.execute("select max(sequence) from approval_category;")
        # max_sequence = cr.fetchone()
        # if max_sequence:
        #     max_sequence = max_sequence[0] + 10
        # else:
        #     max_sequence = 500

        recipe_approval_vals = {
            'name' : 'Recipe Approval',
            'description' : 'Approval type for approve on publish recipe for public or not.',
            'automated_sequence' : True,
            'sequence_code' : 'RECIPE_APPR',
            'company_id' : 1,
            'sequence' : 500,
            'has_product' : 'required',
            # 'approver_ids' : [(4,2)]
        }
        env['approval.category'].create(recipe_approval_vals)
        print(env['approval.category'].search([('name','=','Recipe Approval')]))