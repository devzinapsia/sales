===========
Sales base
===========

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

This module adds a "Mass price update" tool to product pricelists.

From a pricelist's form view, it opens a wizard that lets you increase or
decrease, by a percentage or a fixed amount, the price of every
Product-level rule (``product.pricelist.item`` with *Apply On* set to
*Product*) in that pricelist. Optionally, the starting price for each
product can be copied from another ("reference") pricelist instead of
using the current price, before the adjustment is applied.

Before writing any price, the wizard shows a preview of the resulting
prices so changes can be reviewed and confirmed or discarded.

**Table of contents**

.. contents::
   :local:

Configuration
=============

No configuration is needed. The "Mass price update" button is available to
any user in the Sales Manager group (``sales_team.group_sale_manager``),
on every pricelist form view.

Usage
=====

#. Open a pricelist (*Sales > Configuration > Pricelists*).
#. Click the **Mass price update** button in the header.
#. Optionally pick a **Reference price list to copy from**: for every
   product that also exists as a Product-level rule in that reference
   pricelist, its price there is used as the starting point instead of the
   product's current price in this pricelist.
#. Choose the adjustment: **Percentage** (positive to increase, negative
   to decrease) or **Fixed amount** (positive to add, negative to
   subtract).
#. Optionally tick **Round to whole numbers** to round the resulting
   prices to 0 decimals.
#. Click **Preview changes** to see the resulting price for every
   Product-level rule in the pricelist.
#. Click **Confirm** to apply the new prices, or **Back** to change the
   configuration without touching any price.

After confirming, a summary of the change is posted as a message on the
pricelist's chatter.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/devzinapsia/sales/issues>`_.

Credits
=======

Authors
-------

* Zinapsia
