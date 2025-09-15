from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_is_qc_required = fields.Boolean(string='QC Required', compute='_compute_qc_flag', store=True)
    x_qc_check_id = fields.Many2one('tpart.qc.check', string='QC Check', copy=False)

    @api.depends('move_ids.product_id.x_qc_required')
    def _compute_qc_flag(self):
        for pick in self:
            pick.x_is_qc_required = any(line.product_id.x_qc_required for line in pick.move_ids)