# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import date

class DSLPhysioDashboard(http.Controller):

    @http.route('/dsl_physio/dashboard/metrics', type='json', auth='user')
    def physio_metrics(self):
        """Return physiotherapy counts and totals for dashboard."""
        user = request.env.user
        physio = request.env['dsl.physiotherapist'].sudo().search([('user_id', '=', user.id)], limit=1)
        model = request.env['dsl.physiotherapy'].sudo()

        # Today's date range
        today_str = date.today().strftime('%Y-%m-%d')
        today_domain = [
            ('date', '>=', today_str + ' 00:00:00'),
            ('date', '<=', today_str + ' 23:59:59')
        ]

        # ----- Global Metrics -----
        global_today = model.search_count(today_domain)
        global_total = model.search_count([])
        global_invoices = model.search([]).mapped('invoice_id')
        global_collected = sum(
             inv.amount_total if inv.payment_state == 'paid' else 
            (inv.amount_total - inv.amount_residual) if inv.payment_state == 'partial' else 0
            for inv in global_invoices 
        )

        # ----- My Metrics -----
        my_today = my_total = my_collected = 0
        if physio:
            my_today = model.search_count([('physiotherapist_id', '=', physio.id)] + today_domain)
            my_total = model.search_count([('physiotherapist_id', '=', physio.id)])
            my_invoices = model.search([('physiotherapist_id', '=', physio.id)]).mapped('invoice_id')
            my_collected = sum(
                 inv.amount_total if inv.payment_state == 'paid' else 
            (inv.amount_total - inv.amount_residual) if inv.payment_state == 'partial' else 0
            for inv in my_invoices 
            )

        return {
            "my_today": my_today,
            "my_total": my_total,
            "my_collected": my_collected,
            "global_today": global_today,
            "global_total": global_total,
            "global_collected": global_collected,
            "is_physio": bool(physio),
            "current_physio_id": physio.id if physio else False,
        }

    @http.route('/dsl_physio/physiotherapist/summary', type='json', auth='user')
    def physiotherapist_summary(self, date_from=False, date_to=False):
        """Return physiotherapist-wise summary of physiotherapy sessions."""
        model = request.env['dsl.physiotherapy'].sudo()

        domain = []
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))

        records = model.search(domain)

        physio_data = {}
        for record in records:
            if not record.physiotherapist_id:
                continue

            physio = record.physiotherapist_id
            physio_key = f"physio_{physio.id}"

            if physio_key not in physio_data:
                physio_data[physio_key] = {
                    'physiotherapist_id': physio.id,
                    'physiotherapist_name': physio.name,
                    'session_count': 0,
                    'total_amount': 0.0,
                    'collected_amount': 0.0,
                    'patient_count': set(),
                }

            physio_data[physio_key]['session_count'] += 1

            if record.patient_id:
                physio_data[physio_key]['patient_count'].add(record.patient_id.id)

            if record.invoice_id:
                physio_data[physio_key]['total_amount'] += record.invoice_id.amount_total
                if record.invoice_id.payment_state == 'paid':
                    physio_data[physio_key]['collected_amount'] += record.invoice_id.amount_total
                elif record.invoice_id.payment_state == 'partial':
                    physio_data[physio_key]['collected_amount'] += (record.invoice_id.amount_total - record.invoice_id.amount_residual)
                    
        for physio_key in physio_data:
            physio_data[physio_key]['patient_count'] = len(physio_data[physio_key]['patient_count'])

        totals = {
            'total_sessions': sum(p['session_count'] for p in physio_data.values()),
            'total_patients': sum(p['patient_count'] for p in physio_data.values()),
            'total_amount': sum(p['total_amount'] for p in physio_data.values()),
            'total_collected': sum(p['collected_amount'] for p in physio_data.values()),
        }

        return {"rows": list(physio_data.values()), "totals": totals}

    @http.route('/dsl_physio/invoice_ids', type='json', auth='user')
    def get_invoice_ids(self, kind='all_posted', physio_id=None):
        """Return invoice IDs for opening account.move lists."""
        model = request.env['dsl.physiotherapy'].sudo()

        domain = []
        if physio_id:
            domain = [('physiotherapist_id', '=', physio_id)]

        physio_records = model.search(domain)
        invoices = physio_records.mapped('invoice_id')

        if kind in ['my_posted', 'all_posted']:
            invoices = invoices.filtered(lambda inv: inv.state == 'posted')
        elif kind == 'draft':
            invoices = invoices.filtered(lambda inv: inv.state == 'draft')

        totals = sum(inv.amount_total for inv in invoices)

        return {"ids": invoices.ids, "totals": totals}
