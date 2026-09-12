from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_update_prices_lines(self):
        # The "Update Prices" button (and any other caller of this hook)
        # recomputes price_unit from the order's own pricelist_id, with no
        # awareness of a line's own price list override. Left unfiltered,
        # it would silently reprice those lines from the order's pricelist
        # while the "Price list" column kept showing the line's override,
        # leaving the two inconsistent.
        lines = super()._get_update_prices_lines()
        return lines.filtered(
            lambda line: not line.line_pricelist_id
            or line.line_pricelist_id == line.order_id.pricelist_id
        )
