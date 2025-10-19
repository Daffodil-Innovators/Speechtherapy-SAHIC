{
    'name': 'Extended Speechtherapy Hospital Management System',
    'summary': 'Speechtherapy Hospital Management System to manage Speechtherapy related flows.',
    'description': """
    Hospital Speechtherapy dsl hms hospital management system medical health care management 
    """,
    'version': '1.0.1',
    'category': 'Medical',
    'author': 'Daffodil Software Limited',
    'support': 'https://daffodil-bd.com',
    'website': 'https://daffodil-bd.com',
    'license': 'AGPL-3',
    'depends': ['dsl_hms_physiotherapy', 'dsl_hms_next_patient_screen'],
    'data': [

        'data/physio_waiting_screen.xml',
        'data/report_paperformat.xml',

        'security/ir.model.access.csv',

        # Wizard 
        'wizard/physiotherapy_report_wizard.xml',

        # Reports
        'reports/report_action.xml',
        'reports/physiotherapy_summary.xml',
        'reports/physiotherapy_daily_report.xml',
        'reports/physiotherapy_history.xml',
        'reports/advice_sheet.xml',
        'reports/general_history_report.xml',

        # Extra views
        'views/physiotherpist.xml',
        'views/general_history.xml',
        'views/invoice_flow.xml',
        'views/menuitem_inherit.xml',
        'views/speech_therapy_type.xml',
        'views/physio_waiting_template.xml',
        'views/menu_invisible.xml',
        'views/speechtherapy_advice.xml',
        # 'views/physiotherapy_extension_views.xml',
        'views/clinician.xml',

        # Menus
        'views/menus.xml',

        # Assets
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/dashboard.xml',
    ],
    'images': [],
    'installable': True,
    'application': False,
    'sequence': 2,
    'contributors': [
        'Md. Farhan Afsar <https://github.com/Farhan-Afsar>',
    ],
}
