/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from '@web/core/registry';

export const fingerprintIoTNotificationService = {
    dependencies: ['multi_tab', 'bus_service', 'orm', 'notification', 'action'],

    async start(_, { multi_tab, bus_service, orm, notification, action }) {
        const iotChannel = await orm.call("iot.channel", "get_iot_channel", [0]);

        if (!iotChannel) return;

        const notifySuccess = async (message, content) => {
            if ('operation' in message && message.action_type == 'save_fingerprint_device_info') {
                notification.add(_t(content, message.device_identifier, message.operation || ''), {
                    type: 'success',
                });
                await action.doAction({ type: 'ir.actions.act_window_close' });
                await action.doAction({ type: 'ir.actions.client', tag: 'reload' })
            }
            else if (message.action_type === 'live_capture') {
                notification.add(_t(content, message.device_identifier, message.fingerprint_type, message.punch_type), {
                    type: 'success',
                });
            }
            else {
                notification.add(_t(content, message.device_identifier), {
                    type: 'success',
                });
            }
        };

        const handleNotification = (message) => {
            if (!multi_tab.isOnMainTab()) return;

            const actionMessages = {
                save_fingerprint_device_info: 'A %s device has been saved successfully %s.',
                fetch_user: 'Fetched users data successfully from %s device.',
                download_attendance: 'Downloaded attendance data successfully from %s device.',
                download_template: 'Downloaded template data successfully from %s device.',
                // clear_data: 'Cleared all data successfully from %s device.',
                shutdown_device: 'The device %s has been successfully turned off.',
                reboot_device: 'The device %s has been successfully reboot.',
                live_capture: 'Fingerprint registered from %s device. [Type: %s, Punch: %s]',
            };

            const logPrefix = 'Fingerprint Notification:';
            console.log(`${logPrefix} ${message.action_type}`, message);

            if (actionMessages[message.action_type]) {
                notifySuccess(message, actionMessages[message.action_type]);
            }
        };

        bus_service.subscribe('fingerprint_iot_devices', handleNotification);
    },
};

registry.category('services').add('fingerprint_iot_notification_service', fingerprintIoTNotificationService);
