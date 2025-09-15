{
    'name': 'Custom Home',
    'version': '17.0.1.0.0',
    'category': 'Web',
    'summary': 'Beautiful Dashboard Overlay for Odoo',
    'description': '''
        Custom Dashboard
        - Beautiful overlay dashboard interface
        - Quick access to main applications  
        - Does not interfere with other Odoo pages
        - Modern glassmorphism design
        - Responsive and mobile-friendly
    ''',
    'author': 'Faqih Azhar',
    'depends': ['base', 'web'],
    'data': [
        'views/dashboard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}