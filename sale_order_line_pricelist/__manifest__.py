{
    'name': "Sale order line price list",
    'summary': "Allow each sale order line to use its own price list",
    'version': '19.0.1.0.1',
    'category': 'Sales/Sales',
    'author': "Zinapsia",
    'website': "https://www.zinapsia.com",
    'license': 'AGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'auto_install': True,
    'installable': True,
    'application': False,
}
