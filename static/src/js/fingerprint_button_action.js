// File: hr_fingerprint/static/src/js/fingerprint_button_action.js

/** OWL Component Example using Odoo 18 style **/
import { _t } from "@web/core/l10n/translation";
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { Component, onWillStart, useState, onMounted } from '@odoo/owl';
import { standardFieldProps } from '@web/views/fields/standard_field_props';
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { handleBiometricIoTConnectionFallbacks } from "./iot_implement_action";

export class FingerprintButtonAction extends Component {
    static template = 'hr_fingerprints.FingerprintButtonAction';
    static props = {
        // ...standardFieldProps,
        ...standardWidgetProps,
        action: { type: String, optional: true },
        icon: { type: String, optional: true },
        text: { type: String, optional: true },
    };

    setup() {
        super.setup();
        this.dialog = useService('dialog');
        this.http = useService('http');
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.iotBoxesBeforeConnection = [];
        this.action = useService("action");
    }
    get connection_mode() {
        return this.props.record.data.connection_mode;
    }

    async onClickFingerprintButton() {
        if (this.connection_mode == 'iot') {
            await this.handleIoTMode();
        }
        else {
            await this.handlePushOrDirectMode2();
        }
    }

    async handleIoTMode() {
        const args = [
            this.props.record.data.iot_device_id,
            this.props.action,
            this.props.record.data.name
        ];
        await handleBiometricIoTConnectionFallbacks(this.env, this.orm, args);
    }

    async handlePushOrDirectMode2() {
        if (this.props.action === 'save_fingerprint_device_info') {
            if (this.connection_mode == 'push' && !this.props.record.data.serial_number) {
                this.notification.add(_t("Please set the serial number for the device."), {
                    type: "warning",
                });
                return;
            }

            if (this.connection_mode == 'direct' && !this.props.record.data.ip_address) {
                this.notification.add(_t("Please set the ip address for the device."), {
                    type: "warning",
                });
                return;
            }

            try {
                const deviceId = await this.orm.create("hr.fingerprint.device",
                    [{
                        name: this.props.record.data.name,
                        connection_mode: this.connection_mode,
                        ip_address: this.props.record.data.ip_address,
                        connection_timeout: this.props.record.data.connection_timeout,
                        port: this.props.record.data.port,
                        protocol: this.props.record.data.protocol,
                        serial_number: this.props.record.data.serial_number,
                    }], { context: { action_type: this.props.action } }
                );

                if (!deviceId) {
                    this.notification.add(_t("Error when creating the device record."), {
                        type: "danger",
                    });
                    return;
                }

                this.notification.add(_t("Device created successfully."), {
                    type: "success",
                });

                await this.action.doAction({ type: 'ir.actions.act_window_close' });
                // await this.action.doAction({ type: 'ir.actions.client', tag: 'reload' });
            } catch (error) {
                this.notification.add(_t("An unexpected error occurred."), {
                    type: "danger",
                });
            }
        } else {
            console.log(this.props.record.resId, "YYYYYYYYYYYYYYYYYYYYYYYY")
            const result = await this.orm.call("hr.fingerprint.device", "action_type_processing", [this.props.record.resId], { context: { action_type: this.props.action } })
            this.notification.add(result.message, {
                type: result.status === "success" ? "success" : "danger",
                title: result.status === "success" ? "نجاح" : "خطأ",
            });
        }

    }
    async handleNotification() {
        const actionMessages = {
            save_fingerprint_device_info: 'A %s device has been saved successfully %s.',
            fetch_user: 'Fetched users data successfully from %s device.',
            download_attendance: 'Downloaded attendance data successfully from %s device.',
            download_template: 'Downloaded template data successfully from %s device.',
            clear_data: 'Cleared all data successfully from %s device.',
            shutdown_device: 'The device %s has been successfully turned off.',
            reboot_device: 'The device %s has been successfully reboot.',
            live_capture: 'Fingerprint registered from %s device. [Type: %s, Punch: %s]',
        };
        this.notification.add(_t("User fetched successfully."), {
            type: "success",
        });
    }

}
export const fingerprintButtonAction = {
    component: FingerprintButtonAction,
    extractProps: ({ attrs }) => {
        const { action, icon, text } = attrs;
        console.log("My Options: ", action);
        return {
            action,
            icon: icon || '',
            text,
        };
    },
};

registry.category('view_widgets').add('fingerprint_button_action', fingerprintButtonAction);
