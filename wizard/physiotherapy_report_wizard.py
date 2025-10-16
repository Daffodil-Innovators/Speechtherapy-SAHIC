from odoo import models, fields
from datetime import datetime
from dateutil import relativedelta


class PhysiotherapyReportWizard(models.TransientModel):
    _name = "physiotherapy.report.wizard"
    _description = "Physiotherapy Summary Report Wizard"

    def _default_from_date(self):
        today = datetime.today()
        return today.replace(day=1)

    def _default_to_date(self):
        today = datetime.today()
        last_day = today.replace(day=1) + relativedelta.relativedelta(months=1, days=-1)
        return last_day

    from_date = fields.Date(string="From Date", required=True, default=_default_from_date)
    to_date = fields.Date(string="To Date", required=True, default=_default_to_date)
    state = fields.Selection([
        ('pre_appointment', 'Pre-Appointment'),
        ('doctor_consultation', 'Doctor Consultation'),
        ('payment_pending', 'Payment Pending'),
        ('payment_done', 'Payment Done'),
        ('in_queue', 'In Queue'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string="State")

    def action_print_report(self):
        domain = [
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
        ]
        if self.state:
            domain.append(('state', '=', self.state))

        records = self.env['dsl.physiotherapy'].search(domain, order="date asc")

        return self.env.ref(
            'dsl_hms_physiotherapy_extension.action_report_dsl_physiotherapy_summary'
        ).report_action(records)
