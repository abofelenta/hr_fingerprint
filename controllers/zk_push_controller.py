import logging
import pprint
from datetime import datetime
from odoo.http import request, Response
from odoo import models, fields, api , http

_logger = logging.getLogger(__name__)

class ZKPushProtocolController(http.Controller):

    def _log_request_data(self, endpoint, kwargs, data=None):
        """تسجيل تفاصيل الطلب الوارد"""
        log_data = {
            'endpoint': endpoint,
            'method': request.httprequest.method,
            'client_ip': request.httprequest.remote_addr,
            'headers': dict(request.httprequest.headers),
            'parameters': kwargs,
            'data': data.decode('utf-8') if data else None
        }
        _logger.debug(f"Incoming request data:\n{pprint.pformat(log_data)}")

    def update_or_get_device(self, serial_number , params=None):
        """
        update or get device by serial number
        :param serial_number: Serial number of the device
        :param params: Additional parameters for updating the device
        """
        device = request.env['hr.fingerprint.device'].sudo().search([('serial_number', '=', serial_number)], limit=1)
        # if params and params.get('table') == 'options' and device is not None 
        if params and params.get('table') == 'options' and device:
            data = request.httprequest.data.decode('utf-8')
            parsed_data = {}
            for item in data.split(','):
                if '=' in item:
                    key, value = item.split('=', 1)  # التقسيم على أول "=" فقط
                    parsed_data[key.strip()] = value.strip()
            device.write({
                'serial_number': serial_number,
                'name':  parsed_data.get('~DeviceName', device.name),
                'mac_address':  parsed_data.get('MAC', device.mac_address),
                'transaction_count':  parsed_data.get('TransactionCount', device.transaction_count),
                'max_att_log_count':  parsed_data.get('~MaxAttLogCount', device.max_att_log_count),
                'user_count':  parsed_data.get('UserCount', device.user_count),
                'max_user_count':  parsed_data.get('~MaxUserCount', device.max_user_count),
                'photo_fun_on':  parsed_data.get('PhotoFunOn', device.photo_fun_on),
                'max_user_photo_count':  parsed_data.get('~MaxUserPhotoCount', device.max_user_photo_count),
                'finger_fun_on':  parsed_data.get('FingerFunOn', device.finger_fun_on),
                'fp_version':  parsed_data.get('FPVersion', device.fp_version),
                'max_finger_count':  parsed_data.get('~MaxFingerCount', device.max_finger_count),
                'fp_count':  parsed_data.get('FPCount', device.fp_count),
                'face_fun_on':  parsed_data.get('FaceFunOn', device.face_fun_on),
                'face_version':  parsed_data.get('FaceVersion', device.face_version),
                'max_face_count':  parsed_data.get('~MaxFaceCount', device.max_face_count),
                'face_count':  parsed_data.get('FaceCount', device.face_count),
                'fv_fun_on':  parsed_data.get('FvFunOn', device.fv_fun_on),
                'fv_version':  parsed_data.get('FvVersion', device.fv_version),
                'max_fv_count':  parsed_data.get('~MaxFvCount', device.max_fv_count),
                'fv_count':  parsed_data.get('FvCount', device.fv_count),
                'pv_fun_on':  parsed_data.get('PvFunOn', device.pv_fun_on),
                'pv_version':  parsed_data.get('PvVersion', device.pv_version),
                'max_pv_count':  parsed_data.get('~MaxPvCount', device.max_pv_count),
                'pv_count':  parsed_data.get('PvCount', device.pv_count),
                'language':  parsed_data.get('Language', device.language),
                'ip_address':  parsed_data.get('IPAddress', device.ip_address),
                'platform':  parsed_data.get('~Platform', device.platform),
                'oem_vendor':  parsed_data.get('~OEMVendor', device.oem_vendor),
                # 'fw_version':  parsed_data.get('FWVersion', device.fw_version),
                'push_version':  parsed_data.get('PushVersion', device.push_version),
                'reg_device_type':  parsed_data.get('RegDeviceType', device.reg_device_type),
            })
        return device
    
    def _handle_data_upload(self, device, params):
        """
        Handle data upload from the device
        :param device: The device object
        :param params: Dictionary containing parameters from the request
        """
        table = params.get('table')
        stamp = params.get('Stamp')
        data = request.httprequest.data.decode('utf-8')
        _logger.info(f"AAAAAAAAAAAAAAAA: {data}")
        
        print(f"Table: {table}, Stamp: {stamp}")
        if table == 'ATTLOG':
            # attendance data processing
            device.process_attendance_data(data, stamp)
        elif table == 'OPERLOG':
            # operation log processing
            device.process_operation_log(data, stamp)
        elif table == 'USER':
            # user data processing
            for line in data.split('\n'):
                device.create_or_update_user_info(line)
        elif table == 'BIODATA':
            # biometric data processing
            device.process_biometric_file(data)
        elif table == 'FP':
            # fingerprint data processing
            device.process_fingerprint_data(data)
        elif table == 'USERPIC':
            # user picture data processing
            device.user_pic_data(data)
        elif table == 'BIOPHOTO' :
            _logger.info(f"333333333333333333: {line}")
            device.user_bio_photo_data(line)
        else:
            _logger.warning(f"Unknown table type: {table} for device {device.serial_number}")
        return Response(f"OK", content_type='text/plain')
    
    @http.route('/iclock/cdata', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def handle_cdata(self, **kwargs):
        """
        Handle device communication data upload
        :param kwargs: Dictionary containing parameters from the request
        1. If GET request, initialize the device and return its configuration.
        2. If POST request, process the data upload from the device.
        """
        try:
            serial_number = kwargs.get('SN')
            if not serial_number:
                return Response("Serial number required", status=400)

            device = self.update_or_get_device(serial_number , kwargs)
            if not device:
                return Response("Device not found", status=400)
            
            device.update_communication_time()
            return self._handle_data_upload(device, kwargs)
        except Exception as e:
            _logger.error(f"Error in cdata: {str(e)}", exc_info=True)
            return Response("ERROR", status=500)

    @http.route('/iclock/getrequest', type='http', auth='none', methods=['GET'], csrf=False)
    def handle_getrequest(self, **kwargs):
        """Send pending commands to device"""
        try:
            print(f"kwargs: {kwargs}")
            serial_number = kwargs.get('SN')
            if not serial_number:
                return Response("Serial number required", status=400)
            device = request.env['hr.fingerprint.device'].sudo().search([('serial_number', '=', serial_number)], limit=1)
            if not device:
                return Response("Device not found", status=400)
            # Search for commands not done (pending or sent)
            commands = request.env['zk.device.command'].sudo().search([
                ('device_id', '=', device.id),
                ('state', '!=', 'done')
            ])
            command_list = [cmd.generated_command for cmd in commands if cmd.generated_command]
            # command_list = ['C:212:SET OPTION VOLUME=74\nC:21:SET OPTION PvFunOn=1\n']
            print(f"Serial Number: {serial_number}, Commands: {command_list}")
            if command_list:
                # Optionally, mark as sent
                commands.write({'state': 'done'})
                return Response('\n'.join(command_list), content_type='text/plain')
            return  Response("OK", content_type='text/plain')  # Example response, replace with actual logic
        except Exception as e:
            print(f"Error in getrequest: {str(e)}")
        # commands=[]
        # request.env['zk.device.command'].sudo().search([('state', '=', "done")])
        # print(f"Serial Number11: {serial_number} ")
        # # return "C:523:SET OPTION AudioPrompt=FALSE\nC:5231:SET OPTION Volume=20\nC:52341:RESTART"  # Example response, replace with actual logic
        # # return "C:1123:SET OPTION VoicePrompt=1\nC:1231:SET OPTION Volume=20\nC:127:GET OPTION VoicePrompt\r\n"  # Example response, replace with actual logic
        return ""  # Example response, replace with actual logic
        return "C:22:RELOAD OPTIONS\nC:55:INFO"  # Example response, replace with actual logic
        return "C:127:GET OPTION FaceFunOn=1\r\n"  # Example response, replace with actual logic
        return "C:123:SET OPTION VoicePrompt=0\nC:1231:SET OPTION Volume=20\nC:1232:REBOOT"  # Example response, replace with actual logic
        #     if not serial_number:
        #         return Response("Serial number required", status=400)
            
        #     device = self.update_or_get_device(serial_number)
        #     print(f"Device: {device}")
        #     if not device:
        #         return Response("Device not found", status=400)
            
        #     commands = device.get_pending_commands()
        #     return Response('\r\n'.join(commands) or "OK", content_type='text/plain')
        # except Exception as e:
        #     _logger.error(f"Error in getrequest: {str(e)}", exc_info=True)
        #     return Response("ERROR", status=500)

    @http.route('/iclock/devicecmd', type='http', auth='public', csrf=False)
    def handle_devicecmd(self, **kwargs):
        """
        Handle device command responses
        :param kwargs: Dictionary containing parameters from the request
        This endpoint processes responses from the device for commands sent earlier.
        """
        sn = kwargs.get('SN')
        try:
            content = request.httprequest.data.decode('utf-8').strip()
            print(f"[DEVICE CMD FEEDBACK] SN: {sn} → Response: {content}")
            if not sn:
                return Response("Serial number required", status=400)

            # مثال: الرد يحتوي على ID=123&Return=0
            for line in content.split('\n'):
                if 'ID=' in line:
                    print(f"Serial Number: {line}")
                    cmd_id = line.split('ID=')[1].split('&')[0]
                    print(f"Command ID: {cmd_id}")
                    print(f"Serial Number: {line}")
                    command = request.env['zk.device.command'].sudo().search([
                        ('cmd_id', '=', cmd_id),
                        ('device_id.serial_number', '=', sn)
                    ], limit=1)
                    if command:
                        if 'Return=0' in line:
                            command.write({
                                'state': 'done',
                                'execution_date': fields.Datetime.now()
                            })
                        else:
                            command.write({'state': 'failed'})
            return Response("OK", content_type='text/plain')
        except Exception as e:
            print(f"Error in devicecmd: {str(e)}")
    
    @http.route('/iclock/edata', type='http', auth='none', methods=['POST'], csrf=False)
    def handle_edata(self, **kwargs):
        """ 
        Handle attendance data upload from device
        :param kwargs: Dictionary containing parameters from the request
        """
        try:
            data = request.httprequest.data.decode('utf-8')
            self._log_request_data('/iclock/edata', kwargs, data)
            
            serial_number = kwargs.get('SN')
            if not serial_number:
                return Response("Serial number required", status=400)

            device = self.update_or_get_device(serial_number)
            if not device:
                return Response("Device not found", status=400)

            device.process_attendance_data(data, kwargs.get('Stamp'))
            _logger.info(f"Processed attendance records from device {serial_number}")
            return Response("OK", content_type='text/plain')
        except Exception as e:
            _logger.error(f"Error in edata: {str(e)}", exc_info=True)
            return Response("ERROR", status=500)
        