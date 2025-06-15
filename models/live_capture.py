# -*- coding: utf-8 -*-

import logging
import threading
import time
import odoo
# from odoo import api, SUPERUSER_ID


_logger = logging.getLogger(__name__)

# قاموس لتخزين الخيوط النشطة والإشارات للتوقف
active_threads = {}

def start_live_capture_for_all_devices():
    """بدء تشغيل المزامنة المباشرة لجميع الأجهزة المفعلة"""
    _logger.info("Starting live capture for all enabled devices")
    print("Starting live capture for all enabled devices")
    
    # انتظر قليلاً للتأكد من اكتمال بدء تشغيل الخادم
    time.sleep(5)
    
    # الحصول على قائمة قواعد البيانات
    db_list = odoo.service.db.list_dbs(True)
    print(db_list,"db_list")
    
    for db_name in db_list:
        try:
            # إنشاء اتصال جديد بقاعدة البيانات - استخدام الطريقة المتوافقة مع Odoo 18
            registry = odoo.modules.registry.Registry(db_name)
            print(registry,"registryregistryregistryregistry")
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                print(env,"envenvenvenvenv")
                
                if 'hr.fingerprint.device' not in env:
                    continue
                
                # البحث عن الأجهزة التي تم تفعيل المزامنة التلقائية لها
                devices = env['hr.fingerprint.device'].search([
                    ('auto_sync_time', '=', True),
                    ('connection_mode', '=', 'direct'),
                    ('connection_type', '=', 'network')
                ])
                print(devices,"devicesdevicesdevicesdevices")
                
                for device in devices:
                    device.toggle_auto_sync_time()
        
        except Exception as e:
            _logger.error(f"Error starting live capture for database {db_name}: {e}")
    