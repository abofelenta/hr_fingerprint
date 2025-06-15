from odoo import api, fields, models


class FingerprintMachineAttendance(models.Model):
    """Model to hold data from the Fingerprint device"""
    _name = 'fingerprint.attendance'
    _description = 'Attendance'
    _order = 'punching_time desc'
    rec_name = 'user_id.name'
    
    device_id = fields.Many2one(
        'hr.fingerprint.device', 
        string='Fingerprint Device',
        readonly=True,
    )
    
    user_id = fields.Many2one(
        'hr.fingerprint.user',
        string='User'
    )
    is_used = fields.Boolean(string="Is Used", default=False)
    punch_type = fields.Selection([
            ('0', 'Check In'), 
            ('1', 'Check Out'),
            ('2', 'Break Out'), 
            ('3', 'Break In'),
            ('4', 'Overtime In'), 
            ('5', 'Overtime Out'),
            ('255', 'Duplicate')
        ],
        string='Punching Type',
        help='Punching type of the attendance'
    )
    attendance_type = fields.Selection([
            ('1', 'Finger'), 
            ('15', 'Face'),
            ('2', 'Type_2'),
            ('25', 'palm'), 
            ('3', 'Password'),
            ('4', 'Card'), 
            ('255', 'Duplicate')
        ],
        string='Category',
        help="Attendance detecting methods"
    )

    punching_time = fields.Datetime(
        string='Punching Time',
        help="Punching time in the device"
    )
    

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'user_id' in vals:
                user = self.env['hr.fingerprint.user'].browse(vals['user_id'])
                vals['user_id'] = user.id if user.exists() else False

        return super().create(vals_list)      
  