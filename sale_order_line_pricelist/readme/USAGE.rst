#. Open or create a sale order.
#. In the order lines grid, the **Price list** column shows, for each
   line, the price list used to compute its unit price - it starts out
   equal to the order's own price list.
#. To price a specific line from a different price list, pick another
   price list in that line's **Price list** column. The line's unit price
   is recalculated immediately from the new price list.

   * If the chosen price list has no rule for that product, the price is
     taken from the product's own sales price, converted to the order's
     currency if needed - same fallback Odoo already applies for the
     order's own price list.
   * If the chosen price list uses a different currency than the order,
     the resulting unit price is converted to the order's currency using
     the current exchange rate.

#. This lets the same product appear more than once on the same order,
   each line priced from a different price list.

Changing a line's **Price list** never changes the order's own
**Pricelist** field, nor any other line's price.
