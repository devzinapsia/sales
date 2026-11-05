This module adds a **Price list** field to each sale order line
(``line_pricelist_id``), independent of the order's own price list
(``pricelist_id``).

A new line takes the order's price list. The user can then pick a
different, active price list on that specific line only, without affecting
the order's price list or any other line.

The line's price list is used by every price computation of the line, the
same way Odoo uses the order's price list: when the line's price list,
product, quantity or unit of measure changes, and when the **Update
Prices** button is used. This includes quantity tiers, discount rules,
taxes included in the price with fiscal position mapping, and the
conversion to the order's currency when the line's price list uses a
different currency.

This makes it possible, for example, to add the same product twice on the
same order with two different prices, each coming from a different price
list.
