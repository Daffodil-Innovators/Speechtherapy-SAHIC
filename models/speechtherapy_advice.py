from odoo import models, fields


class Advice(models.Model):
    _name = 'speechtherapy.advice'
    _description = 'Advice'

    name = fields.Char("Advice Name")
    active = fields.Boolean(default=True)
