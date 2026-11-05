#. Open or create a sale order.
#. In the order lines grid, the **Price list** column shows, for each
   line, the price list used to compute its unit price - it starts out
   equal to the order's own price list.
#. To price a specific line from a different price list, pick another
   price list in that line's **Price list** column. The line's unit price
   (and discount, if the price list rule is a discount) is recalculated
   immediately from the new price list. Later changes of the line's
   product, quantity or unit of measure keep using that price list.
#. This lets the same product appear more than once on the same order,
   each line priced from a different price list.

Notes:

* If the chosen price list has no rule for that product, the price is
  taken from the product's own sales price - same fallback Odoo already
  applies for the order's own price list.
* If the chosen price list uses a different currency than the order, the
  unit price is converted to the order's currency at the exchange rate of
  the order date.
* Changing a line's **Price list** never changes the order's own
  **Pricelist** field, nor any other line's price.

Changing the order's price list:

* Lines whose price list was not changed on the line follow the order: they
  switch to the order's new price list. Lines with a price list chosen on
  the line keep it. Picking the order's price list again on a line makes it
  follow the order again.
* As in standard Odoo, changing the order's price list does not reprice the
  lines by itself: use the **Update Prices** button next to it. Each line
  is then repriced from its own price list.
