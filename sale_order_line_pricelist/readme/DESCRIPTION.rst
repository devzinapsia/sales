This module adds a **Price list** field to each sale order line
(``line_pricelist_id``), independent of the order's own price list
(``pricelist_id``).

By default, a new line takes the order's price list, exactly like today.
The user can then pick a different, active price list on that specific
line only, without affecting the order's price list or any other line.
Changing a line's price list recomputes that line's unit price right
away, converting it to the order's currency when the two price lists use
different currencies.

This makes it possible, for example, to add the same product twice on the
same order with two different prices, each coming from a different price
list.
