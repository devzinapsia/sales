from odoo import _, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def action_open_mass_price_update(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Mass price update"),
            'res_model': 'sales_base.pricelist.mass.update',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pricelist_id': self.id},
        }
