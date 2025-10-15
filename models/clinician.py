from odoo import fields, models, api

class DSLClinician(models.Model):
    _name = 'dsl.clinician'
    _description = 'Clinician'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(string='Clinician ID', readonly=True, copy=False)
    image_1920 = fields.Binary(string="Image", max_width=1920, max_height=1920)
    image_128 = fields.Binary(string="Image 128", compute='_compute_images', store=True)
    
    partner_id = fields.Many2one('res.partner', string="Contact")
    user_id = fields.Many2one('res.users', string="Linked User", domain=[('share', '=', False)], required=True)
    
    # Education and Designation
    degree = fields.Char(string='Education')
    designation = fields.Char(string='Designation')
    
    # Contact Information
    phone = fields.Char(related='partner_id.phone', store=True, readonly=False)
    mobile = fields.Char(related='partner_id.mobile', store=True, readonly=False)
    email = fields.Char(related='partner_id.email', store=True, readonly=False)
    
    # Address fields
    street = fields.Char(related='partner_id.street', store=True, readonly=False)
    street2 = fields.Char(related='partner_id.street2', store=True, readonly=False)
    city = fields.Char(related='partner_id.city', store=True, readonly=False)
    state_id = fields.Many2one('res.country.state', related='partner_id.state_id', store=True, readonly=False)
    zip = fields.Char(related='partner_id.zip', store=True, readonly=False)
    country_id = fields.Many2one('res.country', related='partner_id.country_id', store=True, readonly=False)
    
    # Personal Info
    signature = fields.Binary(string='Signature')
    
    # Bangla Information
    name_bangla = fields.Char(string='Name in Bangla')
    designation_bangla = fields.Char(string='Designation in Bangla')
    
    active = fields.Boolean(default=True)
    
    @api.model
    def create(self, vals):
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('dsl.clinician') or '/'
        return super(DSLClinician, self).create(vals)
    
    @api.depends('image_1920')
    def _compute_images(self):
        for record in self:
            if record.image_1920:
                record.image_128 = record.image_1920
            else:
                record.image_128 = False
    
    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Auto-populate partner and all related data when user is selected"""
        if self.user_id and self.user_id.partner_id:
            self.partner_id = self.user_id.partner_id