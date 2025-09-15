from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TpartQcCheck(models.Model):
    _name = 'tpart.qc.check'
    _description = 'QC Check Spare-part'
    _inherit = ['mail.thread']
    _order = 'date desc'
    _rec_name = 'name'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='New')
    receipt_id = fields.Many2one('stock.picking', string='Receipt',
                                 domain=[('picking_type_code', '=', 'incoming')])
    part_id = fields.Many2one('tpart.part', string='Part', required=True)
    qty_check = fields.Integer(string='Qty to Check', required=True, default=1)
    qty_pass = fields.Integer(string='Qty Pass', default=0)
    qty_fail = fields.Integer(string='Qty Fail', default=0)
    note = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft', tracking=True)
    date = fields.Date(string='QC Date', default=fields.Date.context_today, required=True)
    user_id = fields.Many2one('res.users', string='QC Inspector',
                              default=lambda self: self.env.user, required=True)

    # -------- CONSTRAINTS ----------
    @api.constrains('qty_pass', 'qty_fail', 'qty_check')
    def _check_qty_consistency(self):
        for rec in self:
            if rec.qty_pass + rec.qty_fail != rec.qty_check:
                raise ValidationError(_('Qty Pass + Qty Fail must equal Qty to Check'))

    @api.constrains('qty_check')
    def _check_qty_positive(self):
        for rec in self:
            if rec.qty_check <= 0:
                raise ValidationError(_('Qty to Check must be greater than 0'))

    # -------- SEQUENCE ----------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('tpart.qc.check') or 'New'
        return super().create(vals_list)

    # -------- ONCHANGE ----------
    @api.onchange('qty_pass', 'qty_fail')
    def _onchange_qty(self):
        if self.qty_pass + self.qty_fail > self.qty_check:
            return {'warning': {
                'title': _('Quantity Error'),
                'message': _('Pass + Fail quantities cannot exceed total quantity to check')
            }}

    # -------- ACTION BUTTONS ----------
    def action_done(self):
        """Mark QC as done and process results"""
        for rec in self:
            if rec.qty_pass + rec.qty_fail != rec.qty_check:
                raise ValidationError(_('Please complete all quantity checks before validating'))
            rec.write({'state': 'done'})
        return True

    def action_cancel(self):
        """Cancel QC check"""
        self.write({'state': 'cancel'})
        return True

    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.write({'state': 'draft'})
        return True