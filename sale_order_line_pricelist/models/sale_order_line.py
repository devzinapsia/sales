from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Price list",
        domain="[('active', '=', True), '|', ('company_id', '=', False), "
               "('company_id', '=', company_id)]",
        help="Price list used to compute this line's unit price. Defaults "
             "to the order's price list but can be overridden per line, for "
             "example to sell the same product twice at different prices.",
    )

    @api.onchange('order_id')
    def _onchange_order_id_line_pricelist_id(self):
        # A brand-new line is created with `order_id` already set (the
        # one2many widget passes it along), which Odoo treats as a changed
        # field on the very first onchange call for that line. This is the
        # only reliable hook to seed the default: a plain `default=` on the
        # field never sees the order, since the order id only ever reaches
        # the new line as a literal field value, not as `default_order_id`
        # in the onchange context.
        for line in self:
            if not line.line_pricelist_id:
                line.line_pricelist_id = line.order_id.pricelist_id

    @api.onchange('line_pricelist_id')
    def _onchange_line_pricelist_id(self):
        for line in self:
            if not line.line_pricelist_id or not line.product_id:
                continue
            try:
                price = line.line_pricelist_id._get_product_price(
                    line.product_id,
                    line.product_uom_qty or 1.0,
                    uom=line.product_uom_id,
                    date=line._get_order_date(),
                )
            except Exception:
                return {'warning': {
                    'title': _("Price not found"),
                    'message': _(
                        "Could not compute a price for %(product)s in "
                        "price list %(pricelist)s. The unit price was left "
                        "unchanged.",
                        product=line.product_id.display_name,
                        pricelist=line.line_pricelist_id.display_name,
                    ),
                }}

            order_currency = line.order_id.currency_id
            pricelist_currency = line.line_pricelist_id.currency_id
            if (
                pricelist_currency
                and order_currency
                and pricelist_currency != order_currency
            ):
                price = pricelist_currency._convert(
                    price,
                    order_currency,
                    line.order_id.company_id,
                    line.order_id.date_order or fields.Date.context_today(line),
                )

            line.price_unit = price
