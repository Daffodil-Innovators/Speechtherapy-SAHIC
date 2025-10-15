from odoo import api, fields, models, _

class SpeechTherapyType(models.Model):
    _name = "speech.therapy.type"
    _description = "Speech Therapy Type"

    name = fields.Char(string="Therapy Name", required=True)
    price = fields.Float(string="Price", required=True)  
    note = fields.Char(string="Note")
    active = fields.Boolean(default=True)
    product_id = fields.Many2one(
        'product.product',
        string="Linked Product",
        readonly=True
    )

    @api.model
    def create(self, vals):
        rec = super(SpeechTherapyType, self).create(vals)
        if not rec.product_id:
            product = self.env['product.product'].create({
                'name': rec.name,
                'list_price': rec.price,
                'type': 'service',
                'taxes_id': [(5, 0, 0)],  
            })
            rec.product_id = product.id
        return rec

    def write(self, vals):
        res = super(SpeechTherapyType, self).write(vals)
        for rec in self:
            if not rec.product_id:
                product = self.env['product.product'].create({
                    'name': rec.name,
                    'list_price': rec.price,
                    'type': 'service',
                    'taxes_id': [(5, 0, 0)],  
                })
                rec.product_id = product.id
            else:
                if 'name' in vals:
                    rec.product_id.name = rec.name
                if 'price' in vals:
                    rec.product_id.list_price = rec.price
                if rec.product_id.taxes_id:
                    rec.product_id.taxes_id = [(5, 0, 0)]
        return res