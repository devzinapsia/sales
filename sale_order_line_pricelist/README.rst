=========================
Sale order line price list
=========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

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

**Table of contents**

.. contents::
   :local:

Configuration
=============

No configuration is needed. The **Price list** column is available on
every sale order line, to any user who can edit sale orders.

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

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/devzinapsia/sales/issues>`_.

Credits
=======

Authors
-------

* Zinapsia
