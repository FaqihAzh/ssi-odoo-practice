from odoo import fields, models, _

class QcCheckWizard(models.TransientModel):
    _name = 'tpart.qc.check.wizard'
    _description = 'Quick QC Check'

    picking_id = fields.Many2one('stock.picking', required=True)
    part_id = fields.Many2one('tpart.part', required=True)
    qty_check = fields.Integer(string='Qty to Check', required=True)

    def action_create_qc(self):
        self.ensure_one()
        qc = self.env['tpart.qc.check'].create({
            'receipt_id': self.picking_id.id,
            'part_id': self.part_id.id,
            'qty_check': self.qty_check,
        })
        self.picking_id.x_qc_check_id = qc.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tpart.qc.check',
            'res_id': qc.id,
            'view_mode': 'form',
            'target': 'current',
        }