This module adds a "Mass price update" tool to product pricelists.

From a pricelist's form view, it opens a wizard that lets you increase or
decrease, by a percentage or a fixed amount, the price of every
Product-level rule (``product.pricelist.item`` with *Apply On* set to
*Product*) in that pricelist. Optionally, the starting price for each
product can be copied from another ("reference") pricelist instead of
using the current price, before the adjustment is applied.

Before writing any price, the wizard shows a preview of the resulting
prices so changes can be reviewed and confirmed or discarded.
