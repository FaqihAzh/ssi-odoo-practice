from odoo import fields, models, _, api
from odoo.exceptions import UserError

class QcCheckWizard(models.TransientModel):
    _name = 'tpart.qc.check.wizard'
    _description = 'Quick QC Check'

    picking_id = fields.Many2one('stock.picking', required=True)
    part_id = fields.Many2one('tpart.part', string='Part', required=True,
                              domain="[('state','=','approved')]")
    qty_check = fields.Integer(string='Qty to Check', required=True)
    qty_pass = fields.Integer(string='Qty Pass', default=0)
    qty_fail = fields.Integer(string='Qty Fail', default=0)

    @api.onchange('qty_pass', 'qty_fail')
    def _onchange_qty(self):
        if self.qty_pass + self.qty_fail != self.qty_check:
            return {'warning': {
                'title': 'Sum mismatch',
                'message': 'Pass + Fail must equal Qty to Check'
            }}

    def action_create_qc(self):
        self.ensure_one()
        if self.qty_pass + self.qty_fail != self.qty_check:
            raise UserError(_('Pass + Fail must equal Qty to Check'))
        qc = self.env['tpart.qc.check'].create({
            'receipt_id': self.picking_id.id,
            'part_id': self.part_id.id,
            'qty_check': self.qty_check,
            'qty_pass': self.qty_pass,
            'qty_fail': self.qty_fail,
        })
        self.picking_id.x_qc_check_id = qc.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tpart.qc.check',
            'res_id': qc.id,
            'view_mode': 'form',
            'target': 'current',
        }