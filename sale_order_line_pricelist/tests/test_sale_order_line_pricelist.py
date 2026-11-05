from odoo import Command
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderLinePricelist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The line price list column and the order price list are only
        # shown to users of the price list feature.
        cls.env.user.group_ids += cls.env.ref('product.group_product_pricelist')

        cls.partner = cls.env['res.partner'].create({'name': "Test customer"})
        cls.product = cls.env['product.product'].create({
            'name': "Test product",
            'list_price': 10.0,
            'taxes_id': [Command.clear()],
        })
        cls.other_product = cls.env['product.product'].create({
            'name': "Other product",
            'list_price': 33.0,
            'taxes_id': [Command.clear()],
        })

        cls.company_currency = cls.env.company.currency_id
        cls.order_pricelist = cls._create_pricelist("Order price list", [(100.0, 0)])
        # Alternate list with a quantity tier: 250 per unit, 200 from 10.
        cls.alt_pricelist = cls._create_pricelist("Alternate price list", [(250.0, 0), (200.0, 10)])
        cls.new_order_pricelist = cls._create_pricelist("New order price list", [(50.0, 0)])

        # A second currency at a known, fixed rate: 1 company-currency unit
        # equals 0.5 units of this currency, i.e. this currency is worth
        # twice the company currency.
        cls.foreign_currency = cls.env['res.currency'].create({
            'name': "TC1",
            'symbol': "T1",
        })
        cls.env['res.currency.rate'].create({
            'currency_id': cls.foreign_currency.id,
            'rate': 0.5,
            'name': '2000-01-01',
        })
        cls.foreign_pricelist = cls._create_pricelist(
            "Foreign price list", [(100.0, 0)], currency=cls.foreign_currency,
        )

    @classmethod
    def _create_pricelist(cls, name, fixed_prices, currency=None):
        return cls.env['product.pricelist'].create({
            'name': name,
            'currency_id': (currency or cls.company_currency).id,
            'item_ids': [
                Command.create({
                    'applied_on': '1_product',
                    'product_tmpl_id': cls.product.product_tmpl_id.id,
                    'compute_price': 'fixed',
                    'fixed_price': price,
                    'min_quantity': min_qty,
                })
                for price, min_qty in fixed_prices
            ],
        })

    def _create_order(self):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.order_pricelist.id,
        })

    def _add_line(self, order, product=None, pricelist=None, qty=None):
        """Add a line through the order form, the way a user does: product
        (and quantity) first, the line's price list last."""
        with Form(order) as order_form:
            with order_form.order_line.new() as line:
                line.product_id = product or self.product
                if qty:
                    line.product_uom_qty = qty
                if pricelist:
                    line.line_pricelist_id = pricelist
        return order.order_line[-1]

    def test_new_line_defaults_to_order_pricelist(self):
        order = self._create_order()
        line = self._add_line(order)
        self.assertEqual(line.line_pricelist_id, self.order_pricelist)
        self.assertFalse(line.line_pricelist_manual)
        self.assertEqual(line.price_unit, 100.0)

    def test_line_created_by_code_follows_order_pricelist(self):
        order = self._create_order()
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
        })
        self.assertEqual(line.line_pricelist_id, self.order_pricelist)
        self.assertFalse(line.line_pricelist_manual)

        overridden = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.alt_pricelist.id,
        })
        self.assertTrue(overridden.line_pricelist_manual)
        self.assertEqual(overridden.price_unit, 250.0)

    def test_changing_line_pricelist_recomputes_price_only_for_that_line(self):
        order = self._create_order()
        line_a = self._add_line(order)
        line_b = self._add_line(order)

        with Form(order) as order_form:
            with order_form.order_line.edit(0) as line:
                line.line_pricelist_id = self.alt_pricelist

        self.assertEqual(line_a.price_unit, 250.0)
        self.assertTrue(line_a.line_pricelist_manual)
        self.assertEqual(line_b.price_unit, 100.0)
        self.assertEqual(order.pricelist_id, self.order_pricelist)

    def test_line_pricelist_chosen_before_product(self):
        order = self._create_order()
        with Form(order) as order_form:
            with order_form.order_line.new() as line:
                line.line_pricelist_id = self.alt_pricelist
                line.product_id = self.product
        self.assertEqual(order.order_line.line_pricelist_id, self.alt_pricelist)
        self.assertEqual(order.order_line.price_unit, 250.0)

    def test_quantity_change_uses_line_pricelist_tiers(self):
        order = self._create_order()
        line = self._add_line(order, pricelist=self.alt_pricelist)
        self.assertEqual(line.price_unit, 250.0)

        with Form(order) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.product_uom_qty = 10
        self.assertEqual(line.price_unit, 200.0)

    def test_product_change_keeps_line_pricelist(self):
        order = self._create_order()
        line = self._add_line(order, pricelist=self.alt_pricelist)

        with Form(order) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.product_id = self.other_product
        # No rule for that product in the alternate list: its sales price.
        self.assertEqual(line.line_pricelist_id, self.alt_pricelist)
        self.assertEqual(line.price_unit, 33.0)

    def test_same_product_two_lines_different_pricelist_do_not_merge(self):
        order = self._create_order()
        line_a = self._add_line(order)
        line_b = self._add_line(order, pricelist=self.alt_pricelist)

        product_lines = order.order_line.filtered(
            lambda sol: sol.product_id == self.product
        )
        self.assertEqual(len(product_lines), 2)
        self.assertEqual(line_a.price_unit, 100.0)
        self.assertEqual(line_b.price_unit, 250.0)

    def test_price_converted_to_order_currency(self):
        order = self._create_order()
        line = self._add_line(order, pricelist=self.foreign_pricelist)
        # Foreign price list: fixed_price=100 in a currency worth 2x the
        # company currency (rate=0.5) => 200 in the order's currency.
        self.assertEqual(line.price_unit, 200.0)

    def test_order_pricelist_change_moves_following_lines_only(self):
        order = self._create_order()
        following = self._add_line(order)
        overridden = self._add_line(order, pricelist=self.alt_pricelist)

        with Form(order) as order_form:
            order_form.pricelist_id = self.new_order_pricelist

        self.assertEqual(following.line_pricelist_id, self.new_order_pricelist)
        self.assertEqual(overridden.line_pricelist_id, self.alt_pricelist)
        # Same as core: changing the order's price list alone doesn't
        # reprice anything, the "Update Prices" button does.
        self.assertEqual(following.price_unit, 100.0)
        self.assertEqual(overridden.price_unit, 250.0)

    def test_order_pricelist_change_before_saving_keeps_overrides(self):
        order = self._create_order()
        with Form(order) as order_form:
            with order_form.order_line.new() as line:
                line.product_id = self.product
            with order_form.order_line.new() as line:
                line.product_id = self.product
                line.line_pricelist_id = self.alt_pricelist
            order_form.pricelist_id = self.new_order_pricelist
        following, overridden = order.order_line
        self.assertEqual(following.line_pricelist_id, self.new_order_pricelist)
        self.assertEqual(overridden.line_pricelist_id, self.alt_pricelist)

    def test_line_set_back_to_order_pricelist_follows_order_again(self):
        order = self._create_order()
        line = self._add_line(order, pricelist=self.alt_pricelist)
        with Form(order) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.line_pricelist_id = self.order_pricelist
        self.assertFalse(line.line_pricelist_manual)

        with Form(order) as order_form:
            order_form.pricelist_id = self.new_order_pricelist
        self.assertEqual(line.line_pricelist_id, self.new_order_pricelist)

    def test_update_prices_button_recomputes_each_line_from_its_own_pricelist(self):
        order = self._create_order()
        following = self._add_line(order)
        overridden = self._add_line(order, pricelist=self.alt_pricelist)

        self.order_pricelist.item_ids.fixed_price = 999.0
        self.alt_pricelist.item_ids.filtered(lambda i: not i.min_quantity).fixed_price = 777.0
        order.action_update_prices()

        self.assertEqual(following.price_unit, 999.0)
        self.assertEqual(overridden.price_unit, 777.0)
        self.assertEqual(overridden.line_pricelist_id, self.alt_pricelist)

    def test_update_prices_after_order_pricelist_change(self):
        order = self._create_order()
        following = self._add_line(order)
        overridden = self._add_line(order, pricelist=self.alt_pricelist)

        with Form(order) as order_form:
            order_form.pricelist_id = self.new_order_pricelist
        order.action_update_prices()

        self.assertEqual(following.price_unit, 50.0)
        self.assertEqual(overridden.price_unit, 250.0)

    def test_section_line_has_no_pricelist(self):
        order = self._create_order()
        with Form(order) as order_form:
            with order_form.order_line.new() as line:
                line.display_type = 'line_section'
                line.name = "Section"
        self.assertFalse(order.order_line.line_pricelist_id)

    def test_line_pricelist_discount(self):
        self.env.user.group_ids += self.env.ref('sale.group_discount_per_so_line')
        discount_pricelist = self.env['product.pricelist'].create({
            'name': "Discount price list",
            'currency_id': self.company_currency.id,
            'item_ids': [Command.create({
                'applied_on': '3_global',
                'compute_price': 'percentage',
                'percent_price': 20,
            })],
        })
        order = self._create_order()
        line = self._add_line(order, pricelist=discount_pricelist)
        # Discount rule shown as a discount, on top of the sales price.
        self.assertEqual(line.price_unit, 10.0)
        self.assertEqual(line.discount, 20.0)

        with Form(order) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.line_pricelist_id = self.order_pricelist
        # Back to a fixed price rule: no discount left behind.
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(line.discount, 0.0)

    def test_tax_included_price_mapped_by_fiscal_position(self):
        tax_included = self.env['account.tax'].create({
            'name': "Test tax 21% included",
            'type_tax_use': 'sale',
            'amount': 21.0,
            'price_include_override': 'tax_included',
        })
        fiscal_position = self.env['account.fiscal.position'].create({
            'name': "Test exempt",
        })
        tax_exempt = self.env['account.tax'].create({
            'name': "Test tax 0%",
            'type_tax_use': 'sale',
            'amount': 0.0,
            'fiscal_position_ids': [Command.set(fiscal_position.ids)],
            'original_tax_ids': [Command.set(tax_included.ids)],
        })
        self.assertTrue(tax_exempt)
        self.product.taxes_id = [Command.set(tax_included.ids)]
        self.alt_pricelist.item_ids.filtered(lambda i: not i.min_quantity).fixed_price = 121.0

        order = self._create_order()
        order.fiscal_position_id = fiscal_position
        line = self._add_line(order, pricelist=self.alt_pricelist)
        # Same as core for the order's own list: the 21% included in the
        # price list price is removed when the tax is mapped to 0%.
        self.assertAlmostEqual(line.price_unit, 100.0)

    def test_line_pricelist_persists_after_reload(self):
        order = self._create_order()
        line = self._add_line(order, pricelist=self.alt_pricelist)
        line.invalidate_recordset()
        reloaded_line = self.env['sale.order.line'].browse(line.id)
        self.assertEqual(reloaded_line.line_pricelist_id, self.alt_pricelist)
        self.assertTrue(reloaded_line.line_pricelist_manual)

    # ------------------------------------------------------------------
    # Price lists in another currency than the order's one
    # ------------------------------------------------------------------

    @classmethod
    def _create_currency(cls, name, rates):
        """Create a currency with `rates`, a list of (date, rate) where rate
        is the amount of this currency for 1 unit of company currency."""
        return cls.env['res.currency'].create({
            'name': name,
            'symbol': name,
            'rate_ids': [
                Command.create({'name': date, 'rate': rate})
                for date, rate in rates
            ],
        })

    def _create_foreign_rule_pricelist(self, currency, **rule_vals):
        return self.env['product.pricelist'].create({
            'name': "Foreign rule price list",
            'currency_id': currency.id,
            'item_ids': [Command.create({
                'applied_on': '1_product',
                'product_tmpl_id': self.product.product_tmpl_id.id,
                **rule_vals,
            })],
        })

    def test_foreign_pricelist_uses_rate_of_order_date(self):
        currency = self._create_currency("TC2", [('2025-01-01', 0.5)])
        pricelist = self._create_pricelist("TC2 list", [(100.0, 0)], currency=currency)
        order = self._create_order()
        order.date_order = '2025-03-01 12:00:00'
        line = self._add_line(order, pricelist=pricelist)
        self.assertEqual(line.price_unit, 200.0)

        # A newer rate (e.g. today's) is not used: the rate is the one of
        # the order date, also when the prices are updated.
        self.env['res.currency.rate'].create({
            'currency_id': currency.id, 'name': '2025-06-01', 'rate': 0.25,
        })
        order.action_update_prices()
        self.assertEqual(line.price_unit, 200.0)

        # Moving the order date and updating the prices takes the new rate.
        order.date_order = '2025-07-01 12:00:00'
        order.action_update_prices()
        self.assertEqual(line.price_unit, 400.0)

    def test_foreign_pricelist_percentage_rule(self):
        # 10% off the sales price (10, company currency): computed in the
        # price list currency (10 -> 5 -> 4.5) and converted back: 9.
        pricelist = self._create_foreign_rule_pricelist(
            self.foreign_currency, compute_price='percentage', percent_price=10,
        )
        order = self._create_order()
        line = self._add_line(order, pricelist=pricelist)
        self.assertAlmostEqual(line.price_unit, 9.0)
        self.assertEqual(line.discount, 0.0)

    def test_foreign_pricelist_formula_rounds_and_adds_surcharge_in_its_currency(self):
        # Sales price 10 = 5 in the price list currency; -10% = 4.5,
        # rounded to 1.0 = 5, + 5 surcharge = 10 => 20 in the order's
        # currency (it would be 14 if computed in the order's currency).
        pricelist = self._create_foreign_rule_pricelist(
            self.foreign_currency,
            compute_price='formula',
            base='list_price',
            price_discount=10,
            price_round=1.0,
            price_surcharge=5.0,
        )
        order = self._create_order()
        line = self._add_line(order, pricelist=pricelist)
        self.assertAlmostEqual(line.price_unit, 20.0)

    def test_foreign_pricelist_discount(self):
        self.env.user.group_ids += self.env.ref('sale.group_discount_per_so_line')
        pricelist = self._create_foreign_rule_pricelist(
            self.foreign_currency, compute_price='percentage', percent_price=10,
        )
        order = self._create_order()
        line = self._add_line(order, pricelist=pricelist)
        # Shown as a discount: the sales price back in the order's currency
        # and the rule's percentage.
        self.assertAlmostEqual(line.price_unit, 10.0)
        self.assertAlmostEqual(line.discount, 10.0)

    def test_foreign_order_with_company_currency_line_pricelist(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.foreign_pricelist.id,
        })
        self.assertEqual(order.currency_id, self.foreign_currency)
        following = self._add_line(order)
        overridden = self._add_line(order, pricelist=self.order_pricelist)
        self.assertEqual(following.price_unit, 100.0)
        # 100 in company currency = 50 in the order's currency (rate 0.5).
        self.assertEqual(overridden.price_unit, 50.0)

    def test_order_pricelist_change_to_foreign_currency(self):
        order = self._create_order()
        following = self._add_line(order)
        overridden = self._add_line(order, pricelist=self.alt_pricelist)

        with Form(order) as order_form:
            order_form.pricelist_id = self.foreign_pricelist
        self.assertEqual(order.currency_id, self.foreign_currency)
        self.assertEqual(following.line_pricelist_id, self.foreign_pricelist)
        self.assertEqual(overridden.line_pricelist_id, self.alt_pricelist)
        # Same as core: nothing is repriced until "Update Prices".
        self.assertEqual(following.price_unit, 100.0)
        self.assertEqual(overridden.price_unit, 250.0)

        order.action_update_prices()
        self.assertEqual(following.price_unit, 100.0)
        # 250 in company currency = 125 in the order's new currency.
        self.assertEqual(overridden.price_unit, 125.0)

    def test_foreign_pricelist_order_date_before_first_rate(self):
        # No rate on or before the order date: core takes the oldest rate.
        currency = self._create_currency("TC3", [('2025-01-01', 0.5)])
        pricelist = self._create_pricelist("TC3 list", [(100.0, 0)], currency=currency)
        order = self._create_order()
        order.date_order = '2024-06-01 12:00:00'
        line = self._add_line(order, pricelist=pricelist)
        self.assertEqual(line.price_unit, 200.0)

    def test_foreign_pricelist_without_any_rate_converts_one_to_one(self):
        # Core converts at 1:1, without any warning, when a currency has no
        # rate at all: documents why its rates must be loaded.
        currency = self._create_currency("TC4", [])
        pricelist = self._create_pricelist("TC4 list", [(100.0, 0)], currency=currency)
        order = self._create_order()
        line = self._add_line(order, pricelist=pricelist)
        self.assertEqual(line.price_unit, 100.0)
