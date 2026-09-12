from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPricelistMassUpdate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_a = cls.env['product.template'].create({'name': "Product A"})
        cls.product_b = cls.env['product.template'].create({'name': "Product B"})
        cls.category = cls.env['product.category'].create({'name': "Test category"})

        cls.pricelist = cls.env['product.pricelist'].create({'name': "Main pricelist"})
        cls.item_a = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': cls.product_a.id,
            'fixed_price': 100.0,
        })
        cls.item_b = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': cls.product_b.id,
            'fixed_price': 50.0,
        })
        cls.item_category = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '2_product_category',
            'categ_id': cls.category.id,
            'fixed_price': 10.0,
        })
        cls.item_global = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '3_global',
            'fixed_price': 5.0,
        })

        cls.reference_pricelist = cls.env['product.pricelist'].create({'name': "Reference pricelist"})
        cls.reference_item_a = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.reference_pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': cls.product_a.id,
            'fixed_price': 80.0,
        })

    def _create_wizard(self, **vals):
        return self.env['sales_base.pricelist.mass.update'].create({
            'pricelist_id': self.pricelist.id,
            **vals,
        })

    def test_percentage_increase_no_reference(self):
        wizard = self._create_wizard(adjustment_type='percentage', percentage=10)
        wizard.action_preview()
        lines = {line.product_tmpl_id: line for line in wizard.preview_line_ids}
        self.assertAlmostEqual(lines[self.product_a].new_price, 110.0)
        self.assertAlmostEqual(lines[self.product_b].new_price, 55.0)

    def test_percentage_decrease_no_reference(self):
        wizard = self._create_wizard(adjustment_type='percentage', percentage=-10)
        wizard.action_preview()
        lines = {line.product_tmpl_id: line for line in wizard.preview_line_ids}
        self.assertAlmostEqual(lines[self.product_a].new_price, 90.0)
        self.assertAlmostEqual(lines[self.product_b].new_price, 45.0)

    def test_fixed_amount_increase(self):
        wizard = self._create_wizard(adjustment_type='fixed', fixed_amount=20)
        wizard.action_preview()
        lines = {line.product_tmpl_id: line for line in wizard.preview_line_ids}
        self.assertAlmostEqual(lines[self.product_a].new_price, 120.0)
        self.assertAlmostEqual(lines[self.product_b].new_price, 70.0)

    def test_fixed_amount_decrease(self):
        wizard = self._create_wizard(adjustment_type='fixed', fixed_amount=-20)
        wizard.action_preview()
        lines = {line.product_tmpl_id: line for line in wizard.preview_line_ids}
        self.assertAlmostEqual(lines[self.product_a].new_price, 80.0)
        self.assertAlmostEqual(lines[self.product_b].new_price, 30.0)

    def test_reference_pricelist_mixed(self):
        wizard = self._create_wizard(
            reference_pricelist_id=self.reference_pricelist.id,
            adjustment_type='fixed',
            fixed_amount=10,
        )
        wizard.action_preview()
        lines = {line.product_tmpl_id: line for line in wizard.preview_line_ids}

        # product_a exists in the reference pricelist: its price (80.0) is used as base.
        self.assertAlmostEqual(lines[self.product_a].reference_price, 80.0)
        self.assertAlmostEqual(lines[self.product_a].new_price, 90.0)

        # product_b doesn't exist in the reference pricelist: its own current price is used as base.
        self.assertFalse(lines[self.product_b].reference_price)
        self.assertAlmostEqual(lines[self.product_b].new_price, 60.0)

    def test_round_to_integer(self):
        wizard = self._create_wizard(adjustment_type='fixed', fixed_amount=0.05)

        wizard.round_to_integer = False
        wizard.action_preview()
        line_a = wizard.preview_line_ids.filtered(lambda l: l.product_tmpl_id == self.product_a)
        self.assertAlmostEqual(line_a.new_price, 100.05)

        wizard.action_back()
        wizard.round_to_integer = True
        wizard.action_preview()
        line_a = wizard.preview_line_ids.filtered(lambda l: l.product_tmpl_id == self.product_a)
        self.assertEqual(line_a.new_price, 100.0)

    def test_only_product_level_items_are_touched(self):
        wizard = self._create_wizard(adjustment_type='percentage', percentage=10)
        wizard.action_preview()
        wizard.action_confirm()

        self.assertAlmostEqual(self.item_a.fixed_price, 110.0)
        self.assertAlmostEqual(self.item_b.fixed_price, 55.0)
        self.assertAlmostEqual(self.item_category.fixed_price, 10.0)
        self.assertAlmostEqual(self.item_global.fixed_price, 5.0)

    def test_no_product_level_items_raises_user_error(self):
        empty_pricelist = self.env['product.pricelist'].create({'name': "Empty pricelist"})
        self.env['product.pricelist.item'].create({
            'pricelist_id': empty_pricelist.id,
            'applied_on': '3_global',
            'fixed_price': 1.0,
        })
        wizard = self._create_wizard(pricelist_id=empty_pricelist.id, adjustment_type='percentage', percentage=10)
        with self.assertRaises(UserError):
            wizard.action_preview()

    def test_confirm_writes_real_pricelist_items(self):
        wizard = self._create_wizard(adjustment_type='fixed', fixed_amount=25)
        wizard.action_preview()
        wizard.action_confirm()
        self.item_a.invalidate_recordset()
        self.assertAlmostEqual(self.item_a.fixed_price, 125.0)
        self.assertAlmostEqual(self.item_b.fixed_price, 75.0)

    def test_confirm_posts_chatter_message(self):
        message_count_before = len(self.pricelist.message_ids)
        wizard = self._create_wizard(adjustment_type='percentage', percentage=10)
        wizard.action_preview()
        wizard.action_confirm()
        self.assertGreater(len(self.pricelist.message_ids), message_count_before)

    def test_back_from_preview_does_not_touch_real_prices(self):
        wizard = self._create_wizard(adjustment_type='percentage', percentage=10)
        wizard.action_preview()
        wizard.action_back()

        self.assertEqual(wizard.state, 'config')
        self.assertFalse(wizard.preview_line_ids)
        self.assertAlmostEqual(self.item_a.fixed_price, 100.0)
        self.assertAlmostEqual(self.item_b.fixed_price, 50.0)
