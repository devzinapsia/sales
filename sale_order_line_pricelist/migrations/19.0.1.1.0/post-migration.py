def migrate(cr, version):
    if not version:
        return
    # Section and note lines never carry a price list.
    cr.execute("""
        UPDATE sale_order_line
           SET line_pricelist_id = NULL
         WHERE display_type IS NOT NULL
           AND line_pricelist_id IS NOT NULL
    """)
    # Before 19.0.1.1.0 there was no way to tell a price list chosen on the
    # line from one copied from the order: a line whose price list differs
    # from its order's is an override and must keep it when the order's
    # price list changes; the others follow the order from now on.
    cr.execute("""
        UPDATE sale_order_line sol
           SET line_pricelist_manual = TRUE
          FROM sale_order so
         WHERE sol.order_id = so.id
           AND sol.display_type IS NULL
           AND sol.line_pricelist_id IS NOT NULL
           AND sol.line_pricelist_id IS DISTINCT FROM so.pricelist_id
    """)
