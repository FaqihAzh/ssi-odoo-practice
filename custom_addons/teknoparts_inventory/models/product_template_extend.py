from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_is_spare_part = fields.Boolean(string='Is Spare Part')
    x_part_id = fields.Many2one('tpart.part', string='Spare Part', copy=False)
    x_qc_required = fields.Boolean(string='QC Required', default=False)

    @api.onchange('x_is_spare_part')
    def _onchange_is_spare_part(self):
        if not self.x_is_spare_part:
            self.x_part_id = False
            self.x_qc_required = False