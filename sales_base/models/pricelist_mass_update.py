from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import formatLang


class PricelistMassUpdate(models.TransientModel):
    _name = 'sales_base.pricelist.mass.update'
    _description = "Mass price update wizard for pricelists"

    state = fields.Selection(
        selection=[('config', "Config"), ('preview', "Preview")],
        default='config',
        required=True,
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        required=True,
        readonly=True,
    )
    reference_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Reference price list to copy from",
        domain="[('id', '!=', pricelist_id)]",
    )
    adjustment_type = fields.Selection(
        selection=[('percentage', "Percentage"), ('fixed', "Fixed amount")],
        string="Adjustment type",
        required=True,
        default='percentage',
    )
    percentage = fields.Float(string="Percentage")
    fixed_amount = fields.Float(string="Fixed amount")
    round_to_integer = fields.Boolean(string="Round to whole numbers", default=False)
    preview_line_ids = fields.One2many(
        comodel_name='sales_base.pricelist.mass.update.line',
        inverse_name='wizard_id',
        string="Preview lines",
        readonly=True,
    )

    def _get_product_level_items(self, pricelist):
        return self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('applied_on', '=', '1_product'),
        ])

    def _compute_new_price(self, base_price):
        self.ensure_one()
        if self.adjustment_type == 'percentage':
            new_price = base_price * (1 + self.percentage / 100)
        else:
            new_price = base_price + self.fixed_amount
        if self.round_to_integer:
            return round(new_price)
        return self.pricelist_id.currency_id.round(new_price)

    def action_preview(self):
        self.ensure_one()
        items = self._get_product_level_items(self.pricelist_id)
        if not items:
            raise UserError(_(
                "There are no Product-level items to update in pricelist %(pricelist)s.",
                pricelist=self.pricelist_id.display_name,
            ))

        reference_items_by_template = {}
        if self.reference_pricelist_id:
            reference_items = self._get_product_level_items(self.reference_pricelist_id)
            reference_items_by_template = {
                item.product_tmpl_id.id: item for item in reference_items
            }

        line_vals = []
        for item in items:
            current_price = item.fixed_price
            reference_item = reference_items_by_template.get(item.product_tmpl_id.id)
            reference_price = reference_item.fixed_price if reference_item else False
            base_price = reference_price if reference_item else current_price
            line_vals.append((0, 0, {
                'pricelist_item_id': item.id,
                'product_tmpl_id': item.product_tmpl_id.id,
                'current_price': current_price,
                'reference_price': reference_price,
                'new_price': self._compute_new_price(base_price),
            }))

        self.preview_line_ids = [(5, 0, 0)] + line_vals
        self.state = 'preview'
        return self._get_window_action()

    def action_back(self):
        self.ensure_one()
        self.preview_line_ids = [(5, 0, 0)]
        self.state = 'config'
        return self._get_window_action()

    def action_confirm(self):
        self.ensure_one()
        for line in self.preview_line_ids:
            line.pricelist_item_id.fixed_price = line.new_price

        self._post_confirmation_message()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Mass price update"),
                'message': _(
                    "%(count)s product prices were updated.",
                    count=len(self.preview_line_ids),
                ),
                'type': 'success',
            },
        }

    def _get_adjustment_description(self):
        self.ensure_one()
        currency = self.pricelist_id.currency_id
        if self.adjustment_type == 'percentage':
            description = _("Percentage: %s%%", self.percentage)
        else:
            description = _("Fixed amount: %s", formatLang(self.env, self.fixed_amount, currency_obj=currency))
        if self.reference_pricelist_id:
            description += _(
                " (based on reference price list %s)",
                self.reference_pricelist_id.display_name,
            )
        return description

    def _post_confirmation_message(self):
        self.ensure_one()
        currency = self.pricelist_id.currency_id
        rows = "".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                line.product_tmpl_id.display_name,
                formatLang(self.env, line.current_price, currency_obj=currency),
                formatLang(self.env, line.new_price, currency_obj=currency),
            )
            for line in self.preview_line_ids
        )
        body = _(
            "<p>Mass price update applied. %(adjustment)s</p>"
            "<table class=\"table table-sm\">"
            "<thead><tr><th>Product</th><th>Previous price</th><th>New price</th></tr></thead>"
            "<tbody>%(rows)s</tbody>"
            "</table>",
            adjustment=self._get_adjustment_description(),
            rows=rows,
        )
        self.pricelist_id.message_post(body=body)

    def _get_window_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Mass price update"),
            'view_id': self.env.ref('sales_base.pricelist_mass_update_view_form').id,
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',
            'view_mode': 'form',
        }
