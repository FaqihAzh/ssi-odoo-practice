{
    'name': 'TeknoParts Inventory – Spare-part HP',
    'version': '17.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Gudang spare-part handphone, QC, recondition, opname',
    'description': """
        Long description diisi nanti
    """,
    'author': 'YourName',
    'website': 'https://www.faqihazh.my.id',
    'depends': ['base', 'product', 'stock', 'purchase', 'sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/part_rule.xml',
        'security/picking_rule.xml',
        'data/sequence.xml',
        'wizard/qc_check_wizard.xml',
        'views/part_views.xml',
        'views/qc_check_views.xml',
        'views/inherit_existing.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}