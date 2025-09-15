from odoo import fields, models, api
from odoo.exceptions import ValidationError


class TpartCategory(models.Model):
    _name = 'tpart.category'
    _description = 'Part Category'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)
    parent_id = fields.Many2one('tpart.category', string='Parent Category', ondelete='restrict')
    child_ids = fields.One2many('tpart.category', 'parent_id', string='Child Categories')
    part_ids = fields.One2many('tpart.part', 'category_id', string='Parts')
    part_count = fields.Integer(string='Parts Count', compute='_compute_part_count')

    @api.depends('part_ids')
    def _compute_part_count(self):
        for category in self:
            category.part_count = len(category.part_ids)

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError('You cannot create recursive categories.')