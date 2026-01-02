# -*- coding: utf-8 -*-
{
    'name': 'Service Follow-up',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'summary': 'Track post-appointment follow-ups with customer feedback and automated reminders',
    'description': """
Service Follow-up Management
=============================
Track post-appointment follow-ups, log customer feedback (rating 1-10 + text),
and automatically remind the assigned user if no reply after 2 days.

Features:
---------
* Track follow-ups with appointment dates and customer info
* Log customer ratings (1-10) and feedback text
* State workflow: draft → sent → replied → closed
* Automated reminders via activities after 2 days without reply
* Chatter integration for communication history
* Daily scheduled action for reminder automation
    """,
    'author': 'onuriscoding',
    'website': 'https://github.com/onuriscoding/odoo-addon-service-followup',
    'license': 'LGPL-3',
    'depends': [
            'base',
            'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/followup_views.xml',
        'data/ir_cron.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
