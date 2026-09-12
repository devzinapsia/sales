from odoo import fields, models


class PricelistMassUpdateLine(models.TransientModel):
    _name = 'sales_base.pricelist.mass.update.line'
    _description = "Mass price update wizard preview line"

    wizard_id = fields.Many2one(
        comodel_name='sales_base.pricelist.mass.update',
        required=True,
        ondelete='cascade',
    )
    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        string="Pricelist item",
        required=True,
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string="Product",
    )
    current_price = fields.Float(string="Current price")
    new_price = fields.Float(string="New price")
