# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, Response
import logging
import base64
from datetime import datetime

attendance_type = {
    '1': 'Finger',
    '15': 'Face',
    '2': 'Type_2',
    '25': 'palm',
    '3': 'Password',
    '4': 'Card',
    '255': 'Duplicate',
}
punch_type = {
    '0': 'Check In',
    '1': 'Check Out',
    '2': 'Break Out',
    '3': 'Break In',
    '4': 'Overtime In',
    '5': 'Overtime Out',
    '255': 'Duplicate',
}
class FingerprintsController(http.Controller):
    def _search_iot_device(self, identifier):
        
        return request.env['iot.device'].sudo().search([('identifier', '=', identifier)], limit=1)
    
    def _get_fingerprint_device(self, iot_device_id):
        return request.env['hr.fingerprint.device'].sudo().search([('iot_device_id', '=', iot_device_id)], limit=1)
    
    def _prepare_device_data(self, iot_device, data):
        """إعداد بيانات جهاز البصمة بشكل مسبق"""
        return {
            'name': data.get('device_name'),
            'connection_mode': 'iot',
            'connection_type': iot_device.connection,
            'ip_address': iot_device.ip_address,
            'port': iot_device.port,
            'password': iot_device.password,
            'protocol': iot_device.protocol,
            'serial_number': data.get('serial_number'),
            'firmware_version': data.get('firmware_version'),
            'platform': data.get('platform'),
            'iot_device_id': iot_device.id,
            'subnet_mask': data.get('subnet_mask', 'Unknown'),
            'gateway': data.get('gateway', 'Unknown'),
            'connection_status': 'connected' if iot_device.connected else 'disconnected',
        }
    
    def _process_users_bulk(self, device_id, users_data):
        """معالجة بيانات المستخدمين بشكل مجمع"""
        existing_users = request.env['hr.fingerprint.user'].sudo().search([
            ('device_id', '=', device_id)
        ])
        existing_user_map = {u.user_id: u for u in existing_users}
        
        to_create = []
        to_update = []
        
        for user in users_data:
            user_vals = {
                'uid': str(user.get('uid')),
                'user_id': user.get('user_id'),
                'name': user.get('name'),
                'privilege': str(user.get('privilege', '0')),
                'password': user.get('password', ''),
                'group_id': user.get('group_id', ''),
                'card': str(user.get('card', '0')),
                'device_id': device_id
            }
            
            if user.get('user_id') in existing_user_map:
                to_update.append((existing_user_map[user.get('user_id')], user_vals))
            else:
                to_create.append(user_vals)
        
        # إنشاء المستخدمين الجدد بشكل مجمع
        if to_create:
            request.env['hr.fingerprint.user'].sudo().create(to_create)
        
        # تحديث المستخدمين الحاليين بشكل مجمع
        for user_rec, vals in to_update:
            user_rec.write(vals)
    
    def _process_attendance_bulk(self, device_id, attendance_data):
        """معالجة بيانات الحضور بشكل مجمع"""
        attendance_vals_list = []
        if isinstance(attendance_data, dict):
            attendance_data = [attendance_data]
        
        for att in attendance_data:
            attendance_vals_list.append({
                'device_id': device_id,
                'user_id': att.get('user_id'),
                'punching_time': datetime.fromisoformat(att.get('timestamp')),
                'attendance_type': str(att.get('status')),
                'punch_type': str(att.get('punch')),
            })

        print(attendance_data,"attendance_dataattendance_data")    
        
        if attendance_vals_list:
            request.env['fingerprint.attendance'].sudo().create(attendance_vals_list)
    
    def _process_templates_bulk(self, device_id, templates_data):
        """معالجة قوالب البصمات بشكل مجمع"""

        # الحصول على جميع المستخدمين مرة واحدة
        fingerprint_users = request.env['hr.fingerprint.user'].sudo().search([
            ('device_id', '=', device_id)
        ])
        user_map = {str(user.uid): user for user in fingerprint_users}
        
        # الحصول على القوالب الموجودة مسبقاً
        existing_templates = request.env['hr.fingerprint.template'].sudo().search([
            ('user_id', 'in', fingerprint_users.ids)
        ])
        template_map = {(t.user_id.id, t.fingerprint_id): t for t in existing_templates}
        
        to_create = []
        to_update = []
        
        for template in templates_data:
            try:
                uid = str(template.get('uid'))
                fid = int(template.get('fid'))
                user = user_map.get(uid)
                if not user:
                    continue
                
                template_vals = {
                    'device_id': device_id,
                    'user_id': user.id,
                    'fingerprint_id': fid,
                    'size': int(template.get('size', 0)),
                    'valid': int(template.get('valid', 1)),
                    'template': template.get('template', ''),
                    'mark': template.get('mark', ''),
                }
                
                if (user.id, fid) in template_map:
                    to_update.append((template_map[(user.id, fid)], template_vals))
                else:
                    to_create.append(template_vals)
                    
            except Exception as e:
                logging.exception("Failed to process fingerprint template")
                continue
        
        # إنشاء القوالب الجديدة بشكل مجمع
        if to_create:
            request.env['hr.fingerprint.template'].sudo().create(to_create)
        
        # تحديث القوالب الحالية بشكل مجمع
        for template_rec, vals in to_update:
            template_rec.write(vals)
    
    @http.route('/hr_fingerprints/biometric/result', type='json', auth='public')
    def listen_iot_biometric_device(self, **kwargs):

        action = kwargs.get('action')        
        device_identifier = kwargs.get('device_identifier')
        data = kwargs.get('data', {})
        
        if not device_identifier:
            return {'status': 'error', 'message': 'Device identifier is missing'}
        
        iot_device = self._search_iot_device(device_identifier)
        if not iot_device:
            return {'status': 'error', 'message': 'IoT device not found'}
        
        iot_channel = request.env['iot.channel'].sudo().get_iot_channel()
        
        try:
            if action == 'save_fingerprint_device_info':

                fingerprint_device = self._get_fingerprint_device(iot_device.id)
                
                device_data = self._prepare_device_data(iot_device, data)
                if fingerprint_device:
                    fingerprint_device.write(device_data)
                    operation = 'updated'
                else:
                    fingerprint_device = request.env['hr.fingerprint.device'].sudo().create(device_data)
                    operation = 'created'
                
                request.env['bus.bus']._sendone(iot_channel, 'fingerprint_iot_devices', {
                    'action_type': 'save_fingerprint_device_info',
                    'device_identifier': device_identifier,
                    'operation': operation,
                })
            
            elif action == 'fetch_user':
                fingerprint_device = self._get_fingerprint_device(iot_device.id)
                if fingerprint_device:
                    self._process_users_bulk(fingerprint_device.id, data)
                    request.env['bus.bus']._sendone(iot_channel, 'fingerprint_iot_devices', {
                        'action_type': 'fetch_user',
                        'device_identifier': device_identifier,
                    })
            
            elif action == 'download_attendance':
                fingerprint_device = self._get_fingerprint_device(iot_device.id)
                if fingerprint_device:
                    self._process_attendance_bulk(fingerprint_device.id, data)
                    request.env['bus.bus']._sendone(iot_channel, 'fingerprint_iot_devices', {
                        'action_type': 'download_attendance',
                        'device_identifier': device_identifier,
                    })
            
            elif action == 'download_template':
                fingerprint_device = self._get_fingerprint_device(iot_device.id)
                if fingerprint_device:
                    self._process_templates_bulk(fingerprint_device.id, data)
                    request.env['bus.bus']._sendone(iot_channel, 'fingerprint_iot_devices', {
                        'action_type': 'download_template',
                        'device_identifier': device_identifier,
                    })

            # elif action == 'clear_data':
            #     request.env['bus.bus']._sendone(iot_channel, 'fingerprint_iot_devices', {
            #         'action_type': 'clear_data',
            #         'device_identifier': device_identifier,
            #     })      
            elif action == 'shutdown_device':
                request.env['bus.bus']._sendone(iot_channel, 'fingerprint_iot_devices', {
                    'action_type': 'shutdown_device',
                    'device_identifier': device_identifier,
                })      
            elif action == 'reboot_device':
                request.env['bus.bus']._sendone(iot_channel, 'fingerprint_iot_devices', {
                    'action_type': 'reboot_device',
                    'device_identifier': device_identifier,
                })

            elif action == 'live_capture':
                print("live_capture")  
                fingerprint_device = self._get_fingerprint_device(iot_device.id)
                if fingerprint_device and fingerprint_device.auto_sync_time:
                    self._process_attendance_bulk(fingerprint_device.id, data)
                    request.env['bus.bus']._sendone(iot_channel, 'fingerprint_iot_devices', {
                        'action_type': 'live_capture',
                        'device_identifier': device_identifier,
                        'fingerprint_type': attendance_type[str(data.get('status', '1'))],  
                        'punch_type': punch_type[str(data.get('punch', '0'))],  
                    })      
            
            request.env.cr.commit()
            return {'status': 'success', 'message': 'Data processed successfully'}
        
        except Exception as e:
            logging.exception("Error processing biometric data")
            request.env.cr.rollback()
            return {'status': 'error', 'message': str(e)}
        
        