from odoo import fields, models

class TpartCategory(models.Model):
    _name = 'tpart.category'
    _description = 'Part Category'

    name = fields.Char(required=True)
    parent_id = fields.Many2one('tpart.category', ondelete='restrict')