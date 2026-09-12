from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_update_prices_lines(self):
        # A line with its own price list override must be repriced from
        # that price list, not from the order's - see _recompute_prices()
        # below, which reprices these lines separately right after.
        lines = super()._get_update_prices_lines()
        return lines.filtered(
            lambda line: not line.line_pricelist_id
            or line.line_pricelist_id == line.order_id.pricelist_id
        )

    def _recompute_prices(self):
        super()._recompute_prices()
        overridden_lines = self.order_line.filtered(
            lambda line: line.line_pricelist_id
            and line.line_pricelist_id != line.order_id.pricelist_id
        )
        for line in overridden_lines:
            try:
                line.price_unit = line._get_price_from_pricelist(line.line_pricelist_id)
            except Exception:
                # Leave the line's price unchanged, same as the onchange
                # does when no price can be computed from its price list.
                continue
