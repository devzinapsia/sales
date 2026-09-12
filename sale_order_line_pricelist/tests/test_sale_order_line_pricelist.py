from unittest.mock import patch

from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderLinePricelist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': "Test customer"})
        cls.product = cls.env['product.product'].create({
            'name': "Test product",
            'list_price': 10.0,
        })

        cls.company_currency = cls.env.company.currency_id
        cls.order_pricelist = cls.env['product.pricelist'].create({
            'name': "Order price list",
            'currency_id': cls.company_currency.id,
        })
        cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.order_pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'fixed_price': 100.0,
        })

        cls.alt_pricelist = cls.env['product.pricelist'].create({
            'name': "Alternate price list",
            'currency_id': cls.company_currency.id,
        })
        cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.alt_pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'fixed_price': 250.0,
        })

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
        cls.foreign_pricelist = cls.env['product.pricelist'].create({
            'name': "Foreign price list",
            'currency_id': cls.foreign_currency.id,
        })
        cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.foreign_pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'fixed_price': 100.0,
        })

        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.order_pricelist.id,
        })

    def test_new_line_defaults_to_order_pricelist(self):
        with Form(self.order) as order_form:
            with order_form.order_line.new() as line:
                line.product_id = self.product
        line = self.order.order_line[-1]
        self.assertEqual(line.line_pricelist_id, self.order_pricelist)

    def test_changing_line_pricelist_recomputes_price_only_for_that_line(self):
        line_a = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.order_pricelist.id,
            'price_unit': self.product.list_price,
        })
        line_b = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.order_pricelist.id,
            'price_unit': self.product.list_price,
        })

        line_a.line_pricelist_id = self.alt_pricelist
        line_a._onchange_line_pricelist_id()

        self.assertEqual(line_a.price_unit, 250.0)
        self.assertEqual(line_b.price_unit, self.product.list_price)
        self.assertEqual(self.order.pricelist_id, self.order_pricelist)

    def test_same_product_two_lines_different_pricelist_do_not_merge(self):
        line_a = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.order_pricelist.id,
        })
        line_a._onchange_line_pricelist_id()
        line_b = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.alt_pricelist.id,
        })
        line_b._onchange_line_pricelist_id()

        product_lines = self.order.order_line.filtered(
            lambda sol: sol.product_id == self.product
        )
        self.assertEqual(len(product_lines), 2)
        self.assertEqual(line_a.price_unit, 100.0)
        self.assertEqual(line_b.price_unit, 250.0)

    def test_price_converted_to_order_currency(self):
        line = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.foreign_pricelist.id,
        })
        line._onchange_line_pricelist_id()

        # Foreign price list: fixed_price=100 in a currency worth 2x the
        # company currency (rate=0.5) => 200 in the order's currency.
        self.assertEqual(line.price_unit, 200.0)

    def test_no_price_found_keeps_previous_price_and_warns(self):
        line = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.order_pricelist.id,
            'price_unit': 42.0,
        })
        line.line_pricelist_id = self.alt_pricelist

        with patch.object(
            type(self.env['product.pricelist']),
            '_get_product_price',
            side_effect=Exception("boom"),
        ):
            result = line._onchange_line_pricelist_id()

        self.assertEqual(line.price_unit, 42.0)
        self.assertIn('warning', result)

    def test_update_prices_button_recomputes_each_line_from_its_own_pricelist(self):
        line_same_pricelist = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.order_pricelist.id,
            'price_unit': self.order_pricelist.item_ids.fixed_price,
        })
        line_other_pricelist = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.alt_pricelist.id,
            'price_unit': self.alt_pricelist.item_ids.fixed_price,
        })

        # Change both price lists' own price, then trigger the "Update
        # Prices" button: each line should be repriced from its own price
        # list, not both from the order's.
        self.order.pricelist_id.item_ids.fixed_price = 999.0
        self.alt_pricelist.item_ids.fixed_price = 777.0
        self.order.action_update_prices()

        self.assertEqual(line_same_pricelist.price_unit, 999.0)
        self.assertEqual(line_other_pricelist.price_unit, 777.0)
        self.assertEqual(line_other_pricelist.line_pricelist_id, self.alt_pricelist)

    def test_line_pricelist_persists_after_reload(self):
        line = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'line_pricelist_id': self.alt_pricelist.id,
        })
        line.flush_recordset()
        line.invalidate_recordset()

        reloaded_line = self.env['sale.order.line'].browse(line.id)
        self.assertEqual(reloaded_line.line_pricelist_id, self.alt_pricelist)
