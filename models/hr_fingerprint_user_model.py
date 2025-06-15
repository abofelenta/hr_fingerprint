import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please install pyzk library: pip install pyzk")

class HrFingerprintUser(models.Model):
    _name = 'hr.fingerprint.user'
    _description = 'Fingerprint User'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'  # Display name in the UI 

    _sql_constraints = [
        ('unique_uid_per_device', 'unique(uid, device_id)', 'UID must be unique per device!'),
        ('unique_user_id_per_device', 'unique(user_id, device_id)', 'User ID must be unique per device!'),
    ]  
    name = fields.Char(string='Name', required=True)  

    device_id = fields.Many2one(
        'hr.fingerprint.device', 
        string='Device', 
        required=True, 
        ondelete='cascade',
    ) 
    connection_device_mode = fields.Selection(related='device_id.connection_mode', string='Connection Mode', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', 
        string="Partner", 
        compute='_compute_partner_id', 
        store=True
    )
    user_id = fields.Char(
        string='User ID', 
        required=True,
        index=True,
        help='User ID in the fingerprint device'
    )
    uid = fields.Char(
        string='UID', 
        help='Unique ID for the user in the fingerprint device'
    )
    privilege = fields.Selection([
        ('0', 'User'),
        ('2', 'Enroller'),
        ('6', 'Admin'),
        ('14', 'Super Admin')
    ], string='Privilege', default='0',)
    
    password = fields.Char(string='Password',)
    group_id = fields.Char(string='Group ID')
    card = fields.Char(string='Card Number',)
    active_user = fields.Boolean(default=True)
    
    image = fields.Char(string='Image', attachment=True)
    image_filename = fields.Char(string='Image File Name', help="File name of the user photo")
    image_size = fields.Integer(string='Image Size (bytes)', help="Size of the user photo in bytes")
    start_datetime = fields.Datetime(string='Start Validity', help="Start date and time for user validity")
    end_datetime = fields.Datetime(string='End Validity', help="End date and time for user validity")
    
    template_ids = fields.One2many('hr.fingerprint.template', 'user_id', string='Fingerprints' , help="Fingerprints associated with this user")
    biometric_data_ids = fields.One2many(
        'hr.fingerprint.user.biometric', 'user_id', string='Biometric Data'
    )
    attendance_ids = fields.One2many(
        'fingerprint.attendance', 'user_id', string='Attendances',
    )

    @api.depends('user_id')
    def _compute_partner_id(self):
        for record in self:
            partner = self.env['res.partner'].sudo().search([('fingerprint_user_number', '=',record.user_id)], limit=1)
            if partner:
                record.partner_id = partner.id
            else:
                record.partner_id = False   

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for val in vals_list:

                
# Model to hold biometric data for users 
class HRFingerprintUserBiometric(models.Model):
    _name = 'hr.fingerprint.user.biometric'
    _description = 'Biometric Data'
    
    # "BIOPHOTO PIN=12	FileName=12.jpg	Type=9	Size=265592	Content=/9j/4AAQSkZJRgABAQAAAQABAAD/"
    user_id = fields.Many2one('hr.fingerprint.user', 'User', required=True)
    index = fields.Integer(string='Index')
    valid = fields.Boolean(string='Valid')
    duress = fields.Boolean(string='Duress')
    version_major = fields.Integer(string="Major Ver")
    version_minor = fields.Integer(string="Minor Ver")
    no = fields.Integer()
    type = fields.Integer(string='Biometric Type')  # 2: Palm, 8: Face
    # type = fields.Selection([
    #     (1, 'Finger'),
    #     (1, 'Palm'),
    #     (2, 'Face'),
    #     (2, 'Face'),
    # ], string='Biometric Type')
    major_ver = fields.Integer()
    minor_ver = fields.Integer()
    format = fields.Integer()
    template = fields.Text(string='Biometric Template')