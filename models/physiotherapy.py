from odoo import api, fields, models, _
from odoo.exceptions import UserError


class dslPhysiotherapy(models.Model):
    _inherit = 'dsl.physiotherapy'

    physiotherapist_id = fields.Many2one(
        'dsl.physiotherapist',
        string='Speechtherapist',
    )

    clinician_id = fields.Many2one(
        'dsl.clinician',
        string='Clinician', store=True
    )
    test1 = fields.Char("Test")
    speechtherapy_type_id = fields.Many2one(
        'speech.therapy.type',
        string="Speechtherapy Type"
    )
    queue_number = fields.Integer(string="Queue Number", readonly=True)
    session_start_time = fields.Datetime(string="Session Start Time", readonly=True)
    session_end_time = fields.Datetime(string="Session End Time", readonly=True)
    session_duration = fields.Float(
        string="Session Duration", compute="_compute_session_duration"
    )
    current_session_time = fields.Float(
        string="Current Session Time", compute="_compute_current_session_time"
    )
    dsl_show_in_wc = fields.Boolean(string="Show in Waiting Screen", default=True)

    session_duration_display = fields.Char(
        string="Session Duration",
        compute="_compute_session_duration_display"
    )

    advice_ids = fields.Many2many(
        'speechtherapy.advice', 
        string="Advice", 
        help="Select the required advice for the patient"
    )


    @api.depends('patient_id')
    def _get_speech_therapy_history(self):
        for rec in self:
            if not rec.patient_id:
                rec.speech_therapy_history = ""
                continue

            # Define the domain for searching therapy records
            domain = [('patient_id', '=', rec.patient_id.id)]
            if isinstance(rec.id, int):
                domain.append(('id', '!=', rec.id))

            # Search for therapy records
            therapies = self.search(domain, order='date desc', limit=10)

            # If no therapies found, set empty string and continue
            if not therapies:
                rec.speech_therapy_history = ""
                continue

            # Build the table with header if therapies exist
            history = """
            <table style='width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px; background-color: #f9fafb; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <thead>
                    <tr style='background-color: #4b5e7e; color: white;'>
                        <th style='padding: 12px; text-align: left;'>Name</th>
                        <th style='padding: 12px; text-align: left;'>Therapy Type</th>
                        <th style='padding: 12px; text-align: left;'>Price</th>
                        <th style='padding: 12px; text-align: left;'>State</th>
                    </tr>
                </thead>
                <tbody>
            """
            for therapy in therapies:
                history += """
                    <tr style='border-bottom: 1px solid #e5e7eb;'>
                        <td style='padding: 12px; color: #1f2937;'>%s</td>
                        <td style='padding: 12px; color: #1f2937;'>%s</td>
                        <td style='padding: 12px; color: #1f2937;'>%s</td>
                        <td style='padding: 12px;'>
                            <span style='padding: 4px 8px; border-radius: 12px; background-color: %s; color: white; font-size: 12px;'>
                                %s
                            </span>
                        </td>
                    </tr>
                """ % (
                    therapy.name,
                    therapy.speechtherapy_type_id.name,
                    therapy.speechtherapy_type_id.price,
                    '#10b981' if therapy.state == 'completed' else '#f59e0b' if therapy.state == 'in_progress' else '#ef4444',
                    dict(therapy._fields['state'].selection).get(therapy.state)
                )
            history += """
                </tbody>
            </table>
            """
            rec.speech_therapy_history = history

    speech_therapy_history = fields.Html(compute='_get_speech_therapy_history', store=True, string='Speech Therapy History', readonly=True)
        

class dslPhysiotherapyExt(models.Model):
    _inherit = "dsl.physiotherapy"

    state = fields.Selection([
        ('pre_appointment', 'Pre-Appointment'),
        ('doctor_consultation', 'Doctor Consultation'),
        ('payment_pending', 'Payment Pending'),
        ('payment_done', 'Payment Done'),
        ('in_queue', 'In Queue'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', readonly=True, default='pre_appointment')

    # related field to check payment status in view
    invoice_payment_state = fields.Selection(
        related="invoice_id.payment_state",
        string="Invoice Payment Status",
        store=False
    )

    @api.depends('session_start_time', 'session_end_time')
    def _compute_session_duration_display(self):
        for record in self:
            if record.session_start_time and record.session_end_time:
                duration = record.session_end_time - record.session_start_time
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    record.session_duration_display = f"{hours}h {minutes}m"
                else:
                    record.session_duration_display = f"{minutes}m {seconds}s"
            else:
                record.session_duration_display = "0m"

    @api.depends('session_start_time', 'session_end_time')
    def _compute_session_duration(self):
        for record in self:
            if record.session_start_time and record.session_end_time:
                duration = record.session_end_time - record.session_start_time
                record.session_duration = duration.total_seconds() / 60
            else:
                record.session_duration = 0

    @api.depends('session_start_time')
    def _compute_current_session_time(self):
        for record in self:
            if record.session_start_time and not record.session_end_time:
                duration = fields.Datetime.now() - record.session_start_time
                record.current_session_time = duration.total_seconds() / 3600
            else:
                record.current_session_time = 0

    def action_refer_to_doctor(self):
        if self.state != 'pre_appointment':
            raise UserError(_('Can only refer from pre-appointment stage.'))
        if not self.physiotherapist_id:
            raise UserError(_('Please select a Speechtherapist.'))
        self.state = 'doctor_consultation'

    def action_doctor_consultation_done(self):
        if self.state != 'doctor_consultation':
            raise UserError(_('Invalid state for doctor consultation.'))
        if not self.speechtherapy_type_id:
            raise UserError(_('Please select a speech therapy type before completing consultation.'))
        self.state = 'payment_pending'

    def action_create_invoice_and_pay(self):
        """Reception creates invoice only, payment is done manually inside invoice"""
        self.ensure_one()

        if self.state != 'payment_pending':
            raise UserError(_('Invalid state for payment.'))
        if not self.speechtherapy_type_id:
            raise UserError(_('Please select a speech therapy type before creating invoice.'))

        if not self.speechtherapy_type_id.product_id:
            # Attempt to create product if missing
            product = self.env['product.product'].create({
                'name': self.speechtherapy_type_id.name,
                'list_price': self.speechtherapy_type_id.price,
                'type': 'service',
                'taxes_id': [(5, 0, 0)],  # Remove all taxes
            })
            self.speechtherapy_type_id.product_id = product
            if not self.speechtherapy_type_id.product_id:
                raise UserError(
                    _('Failed to create or link product for Speech Therapy Type: %s') % self.speechtherapy_type_id.name)

        product = self.speechtherapy_type_id.product_id

        # Ensure product has no taxes
        if product.taxes_id:
            product.taxes_id = [(5, 0, 0)]  # Remove all taxes

        # Build invoice line data - Pass the product record, not just the ID
        product_data = [{
            'product_id': product,
            'name': product.name,
            'price_unit': self.speechtherapy_type_id.price,
            'quantity': 1,
            'tax_ids': [(5, 0, 0)],
        }]

        pricelist_context = {}
        if self.pricelist_id:
            pricelist_context = {'dsl_pricelist_id': self.pricelist_id.id}

        invoice = self.with_context(pricelist_context).dsl_create_invoice(
            partner=self.patient_id.partner_id,
            patient=self.patient_id,
            product_data=product_data,
            inv_data={
                'hospital_invoice_type': 'physiotherapy',
                'currency_id': self.env.ref('base.BDT').id,
            }
        )
        invoice.action_post()
        self.invoice_id = invoice.id

        # Change state to show "View Invoice" button
        self.state = 'payment_pending'  # Keep same state but now invoice exists

        # Stay on current page - don't open invoice automatically
        return True

    def action_view_invoice(self):
        """Open the created invoice"""
        if not self.invoice_id:
            raise UserError(_('No invoice found!'))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }

    def action_add_to_queue(self):
        """Add patient to queue only if invoice is paid"""
        self.ensure_one()

        if not self.invoice_id:
            raise UserError(_('No invoice found! Please create invoice first.'))
        if self.invoice_id.payment_state != 'paid':
            raise UserError(_('Invoice must be paid before adding to queue.'))

        today_count = self.env['dsl.physiotherapy'].search_count([
            ('create_date', '>=', fields.Date.today()),
            ('queue_number', '>', 0)
        ])
        self.queue_number = today_count + 1
        self.state = 'in_queue'

    def action_start_therapy(self):
        if self.state != 'in_queue':
            raise UserError(_('Patient must be in queue to start therapy.'))
        self.session_start_time = fields.Datetime.now()
        self.state = 'in_progress'

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'res_id': self.id},
        }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'dsl.physiotherapy',
        #     'res_id': self.id,
        #     'view_mode': 'form',
        #     'target': 'current',
        #     'context': self.env.context,
        # }

    def action_end_therapy(self):
        if self.state != 'in_progress':
            raise UserError(_('Therapy session must be in progress to end.'))
        self.session_end_time = fields.Datetime.now()
        self.state = 'done'
        self._compute_session_duration()

    def action_cancel(self):
        if self.state == 'done':
            raise UserError(_('Cannot cancel a completed session.'))
        self.state = 'cancel'
        if self.invoice_id and self.invoice_id.state not in ('cancel', 'paid'):
            self.invoice_id.button_cancel()


class PhysiotherapyExtension(models.Model):
    _inherit = 'dsl.physiotherapy'

    # Medical History - Prenatal
    history_miscarriage = fields.Boolean(string="History of Miscarriages")
    medication_use = fields.Boolean(string="Use of Medication")
    viral_infections = fields.Boolean(string="Viral Infections")
    other_illnesses = fields.Boolean(string="Other Illnesses")
    xray_prenatal = fields.Boolean(string="X-Ray")
    excessive_vomiting = fields.Boolean(string="Excessive Vomiting")
    prenatal_others = fields.Text(string="Others")

    # Birth History
    birth_weight = fields.Char(string="Birth Weight")
    premature_delivery = fields.Boolean(string="Premature Delivery")
    post_term_delivery = fields.Boolean(string="Post Term Delivery")
    labour_type = fields.Selection([
        ('normal', 'Normal'),
        ('prolonged', 'Prolonged'),
        ('instrumental', 'Instrumental Delivery'),
        ('caesarian', 'Caesarian birth')
    ], string="Labour Type")
    birth_injuries = fields.Text(string="Birth Injuries")
    anesthesia_type = fields.Selection([
        ('general', 'General'),
        ('spinal', 'Spinal')
    ], string="Anesthesia Type")
    birth_cry = fields.Selection([
        ('normal', 'Normal'),
        ('delayed', 'Delayed')
    ], string="Birth Cry")
    hypoxia = fields.Boolean(string="Hypoxia")
    jaundice_days = fields.Boolean(string="Jaundice (First 3-4 Days)")
    rh_incompatibility = fields.Boolean(string="Rh. Incompatibility")
    congenital_deformities = fields.Boolean(string="Congenital Deformities")
    birth_history_others = fields.Text(string="Others")

    # Post Natal History
    head_injury = fields.Boolean(string="Head Injury")
    convulsions = fields.Boolean(string="Convulsions")
    ear_infections = fields.Boolean(string="Ear Infections")
    illnesses_mumps = fields.Boolean(string="Mumps")
    illnesses_chicken_pox = fields.Boolean(string="Chicken Pox")
    illnesses_influenza = fields.Boolean(string="Influenza")
    illnesses_typhoid = fields.Boolean(string="Typhoid")
    illnesses_whooping_cough = fields.Boolean(string="Whooping Cough")
    illnesses_tb = fields.Boolean(string="T.B")
    illnesses_meningitis = fields.Boolean(string="Meningitis")
    illnesses_high_fever = fields.Boolean(string="High Fever")
    accidents = fields.Boolean(string="Accidents")
    emotional_trauma = fields.Boolean(string="Emotional Trauma")
    postnatal_others = fields.Text(string="Others")

    # Development History - Milestones
    dev_head_control = fields.Char(string="Head Control")
    dev_turning_over = fields.Char(string="Turning Over")
    dev_sitting = fields.Char(string="Sitting")
    dev_crawling = fields.Char(string="Crawling")
    dev_walking = fields.Char(string="Walking")
    dev_bowel_bladder = fields.Char(string="Bowel & Bladder Control")
    dev_feeds_himself = fields.Char(string="Feeds Himself")
    dev_dresses_himself = fields.Char(string="Dresses Himself")

    # Motor Control
    gross_motor_dysfunction = fields.Boolean(string="Gross Motor Dysfunction")
    paralysis_weakness = fields.Boolean(string="Paralysis or Weakness of Limbs")
    limping = fields.Boolean(string="Limping")
    toe_walking = fields.Boolean(string="Toe-Walking")
    stiffness = fields.Boolean(string="Stiffness")
    dragging_foot = fields.Boolean(string="Dragging of Foot")
    fine_motor_grasping = fields.Boolean(string="Grasping")
    fine_motor_holding = fields.Boolean(string="Holding Objects")
    fine_motor_tracing = fields.Boolean(string="Tracing & Copying")
    fine_motor_drawing = fields.Boolean(string="Picture Drawing")

    # Handedness
    handedness = fields.Selection([
        ('right', 'Right Handed'),
        ('left', 'Left Handed'),
        ('mixed', 'Mixed Laterality')
    ], string="Handedness")

    # Psychomotor Behavior
    psycho_tremors = fields.Boolean(string="Tremors")
    psycho_overflow = fields.Boolean(string="Overflow Movements")
    psycho_tic = fields.Boolean(string="Tic")
    psycho_extraneous = fields.Boolean(string="Extraneous Movements")

    # Examination of Speech Mechanism
    exam_lips = fields.Text(string="Lips")
    exam_teeth = fields.Text(string="Teeth")
    exam_tongue = fields.Text(string="Tongue")
    exam_hard_soft_plate = fields.Text(string="Hard & Soft Plate")
    exam_uvula = fields.Text(string="Uvula")
    exam_jaws = fields.Text(string="Jaws")

    # Sensory Development
    sensory_hearing = fields.Text(string="Hearing")
    sensory_vision = fields.Text(string="Vision")

    # Social Maturity
    social_recognizes_parents = fields.Boolean(string="Recognizes Parents")
    social_refuses_strangers = fields.Boolean(string="Refuses to Go to Strangers")
    social_eye_contact = fields.Boolean(string="Makes Eye Contact")
    social_play_alone = fields.Boolean(string="Prefer to Play by Himself")
    social_parallel_play = fields.Boolean(string="Indulges in Parallel Play")
    social_peers_elders = fields.Boolean(string="Socializes with Peers and Elders")
    social_looks_after = fields.Boolean(string="Looks After Himself")
    social_play_pets = fields.Boolean(string="Prefers to Play with Pets")
    social_quarrelsome = fields.Boolean(string="Quarrelsome for Petty Matters")
    social_temper = fields.Boolean(string="Exhibits Temper Tantrums")
    social_engrossed = fields.Boolean(string="Gets Engrossed in One Activity")
    social_shifts_frequently = fields.Boolean(string="Shifts Frequently")
    social_irritable = fields.Boolean(string="Irritable")
    social_distractive = fields.Boolean(string="Distractive")
    social_aggressive = fields.Boolean(string="Aggressive")
    social_withdrawn = fields.Boolean(string="Withdrawn")
    social_restless = fields.Boolean(string="Restless")
    social_bizarre_movements = fields.Boolean(string="Bizarre Movements")
    social_others = fields.Text(string="Any Others")

    # Language Development
    lang_babbling = fields.Char(string="Babbling")
    lang_first_word = fields.Char(string="First Word")
    lang_first_sentence = fields.Char(string="First Sentence")
    lang_receptive = fields.Text(string="Receptive Language")
    lang_expressive = fields.Text(string="Expressive Language")

    # Additional Information
    misarticulations = fields.Text(string="Misarticulations")
    exposure_languages = fields.Text(string="Exposure to Languages")
    speech_stimulation_home = fields.Text(string="Speech Stimulation at Home")
    educational_background = fields.Text(string="Educational Background")

    # Sensory Input
    sensory_tactile = fields.Text(string="Tactile")
    sensory_visual = fields.Text(string="Visual")
    sensory_alfactory = fields.Text(string="Alfactory")
    sensory_gustatory = fields.Text(string="Gustatory")
    sensory_vestibular = fields.Text(string="Vestibular")
    sensory_proprioceptive = fields.Text(string="Proprioceptive")
    sensory_auditory = fields.Text(string="Auditory")

    # Summary and Diagnosis
    summary_findings = fields.Text(string="Summary of Findings")
    provisional_diagnosis = fields.Text(string="Provisional Diagnosis")
    recommendations = fields.Text(string="Recommendations")