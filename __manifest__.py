# -*- coding: utf-8 -*-
{
    'name': "hr_fingerprints",

    'summary': "Integration with Diferent biometric devices via direct connection or IoT Box",

    'description': """
        This application allows handling fingerprint functions 
        across different devices connected either via IoT or directly.
    """,

    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'hr_attendance', 'iot',"contacts"],
    'external_dependencies': {
        'python': ['pyzk'],
    },

    'version': '0.1',

    'data': [
        'wizard/add_fingerprint_device_views.xml',
        'security/ir.model.access.csv',
        'views/main_menu.xml',
        'views/hr_fingerprint_devices_view.xml',
        "views/zk_devices_command_views.xml",
        'views/hr_fingerprint_users_view.xml',
        'views/hr_fingerprint_templates_view.xml',
        'views/fingerprint_machine_attendance.xml',
        'views/iot_devices_view.xml',
        'views/hr_partner_view.xml',
        'views/hr_employee_views.xml',
        # 'data/cron_jobs.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_fingerprints/static/src/js/fingerprint_bus_service.js',
            'hr_fingerprints/static/src/js/iot_implement_action.js',
            'hr_fingerprints/static/src/js/fingerprint_button_action.js',
            'hr_fingerprints/static/src/xml/fingerprint_button_action.xml',
            # 'hr_fingerprints/static/src/js/device_menu_actions.js',
            # 'hr_fingerprints/static/src/js/active_device_widget.js',
            # 'hr_fingerprints/static/src/xml/active_device_widget.xml',
            # 'hr_fingerprints/static/src/js/fingerprint_iot_notification_service.js',
            # 'hr_fingerprints/static/src/js/fetch_device_info.js',
            # 'hr_fingerprints/static/src/js/save_fingerprint_device_button.js',
            # "hr_fingerprints/static/src/js/connection_status.js",
            # 'hr_fingerprints/static/src/xml/fetch_device_info.xml',
            # 'hr_fingerprints/static/src/xml/save_fingerprint_device_button.xml',
        ],
        "web.assets_qweb": [
            # "hr_fingerprints/static/src/xml/connection_status.xml",
        ],
    },

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

