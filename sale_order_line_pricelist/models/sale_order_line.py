from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Price list",
        compute='_compute_line_pricelist_id',
        store=True,
        readonly=False,
        precompute=True,
        domain="[('active', '=', True), '|', ('company_id', '=', False), "
               "('company_id', '=', company_id)]",
        help="Price list used to compute this line's unit price. Follows "
             "the order's price list unless it is changed on this line, for "
             "example to sell the same product twice at different prices.",
    )
    line_pricelist_manual = fields.Boolean(
        string="Line price list set manually",
        help="Technical field: set when the line's price list was chosen on "
             "the line itself. Such a line keeps its price list when the "
             "order's price list changes; the other lines follow it.",
    )

    @api.depends('order_id.pricelist_id', 'display_type')
    def _compute_line_pricelist_id(self):
        for line in self:
            if line.display_type:
                line.line_pricelist_id = False
            elif line.line_pricelist_manual and line.line_pricelist_id:
                # Chosen on the line itself: keep it.
                line.line_pricelist_id = line.line_pricelist_id
            else:
                line.line_pricelist_id = line.order_id.pricelist_id

    def _has_foreign_line_pricelist(self):
        """Whether this line is priced from a price list of another currency
        than the order's one."""
        self.ensure_one()
        pricelist_currency = self.line_pricelist_id.currency_id
        return bool(
            pricelist_currency
            and self.currency_id
            and pricelist_currency != self.currency_id
        )

    @api.depends('line_pricelist_id')
    def _compute_pricelist_item_id(self):
        # Core always looks the rule up in the order's price list: look it up
        # in the line's own price list instead, so that every core pricing
        # path (product/quantity change, discount, "Update Prices") uses it.
        super()._compute_pricelist_item_id()
        for line in self:
            pricelist = line.line_pricelist_id
            if (
                not pricelist
                or pricelist == line.order_id.pricelist_id
                or not line.product_id
                or line.display_type
            ):
                continue
            line.pricelist_item_id = pricelist._get_product_rule(
                product=line.product_id,
                **line._get_pricelist_kwargs(),
            )

    def _get_pricelist_kwargs(self):
        kwargs = super()._get_pricelist_kwargs()
        # Fixed prices of a price list rule are expressed in that price
        # list's currency and core never converts them (the order's price
        # list always shares the order's currency): compute in the line's
        # price list currency, the price methods below convert the result.
        if self._has_foreign_line_pricelist():
            kwargs['currency'] = self.line_pricelist_id.currency_id
        return kwargs

    def _convert_from_line_pricelist_currency(self, price):
        self.ensure_one()
        if not self._has_foreign_line_pricelist():
            return price
        return self.line_pricelist_id.currency_id._convert(
            price,
            self.currency_id,
            self.order_id.company_id or self.env.company,
            self._get_order_date() or fields.Date.context_today(self),
        )

    def _get_pricelist_price(self):
        price = super()._get_pricelist_price()
        return self._convert_from_line_pricelist_currency(price)

    def _get_pricelist_price_before_discount(self):
        price = super()._get_pricelist_price_before_discount()
        return self._convert_from_line_pricelist_currency(price)

    @api.onchange('line_pricelist_id')
    def _onchange_line_pricelist_id(self):
        for line in self:
            line.line_pricelist_manual = bool(
                line.line_pricelist_id
                and line.line_pricelist_id != line.order_id.pricelist_id
            )
            if not line.product_id or line.display_type:
                continue
            line._reset_price_unit()
            line._compute_discount()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Lines created by code with an explicit price list (imports, other
        # modules...) get the same marker the onchange sets from the UI.
        for line, vals in zip(lines, vals_list):
            if 'line_pricelist_manual' not in vals and vals.get('line_pricelist_id'):
                line._sync_line_pricelist_manual()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if 'line_pricelist_id' in vals and 'line_pricelist_manual' not in vals:
            self._sync_line_pricelist_manual()
        return res

    def _sync_line_pricelist_manual(self):
        for line in self:
            manual = bool(
                line.line_pricelist_id
                and line.line_pricelist_id != line.order_id.pricelist_id
            )
            if line.line_pricelist_manual != manual:
                line.line_pricelist_manual = manual
