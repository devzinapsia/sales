{
    'name': "Sales base",
    'summary': "Base module for Zinapsia sales tools: mass price update on pricelists",
    'version': '19.0.1.0.1',
    'category': 'Sales/Sales',
    'author': "Zinapsia",
    'website': "https://www.zinapsia.com",
    'license': 'AGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_pricelist_views.xml',
        'views/pricelist_mass_update_views.xml',
    ],
    'auto_install': True,
    'installable': True,
    'application': False,
}
