==========================
Sale order line price list
==========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

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

**Table of contents**

.. contents::
   :local:

Configuration
=============

The **Price list** column of the order lines is shown to the users of the
price list feature (*Sales > Configuration > Settings > Pricelists*), the
same ones who see the order's own **Pricelist** field.

The field only offers active price lists of the order's own company (or
price lists shared across all companies) - it is not restricted to the
price lists normally assignable to the order's customer, since it is a
manual override for specific cases.

Usage
=====

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

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/devzinapsia/sales/issues>`_.

Credits
=======

Authors
-------

* Zinapsia
