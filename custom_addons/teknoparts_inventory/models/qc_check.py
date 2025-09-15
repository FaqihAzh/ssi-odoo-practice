from odoo import api, fields, models, _

class TpartQcCheck(models.Model):
    _name = 'tpart.qc.check'
    _description = 'QC Check Spare-part'
    _inherit = ['mail.thread']
    _order = 'date desc'

    name = fields.Char(string='Reference', readonly=True, copy=False)
    receipt_id = fields.Many2one('stock.picking', string='Receipt',
                                 domain=[('picking_type_code','=','incoming')])
    part_id = fields.Many2one('tpart.part', string='Part', required=True)
    qty_check = fields.Integer(string='Qty to Check', required=True)
    qty_pass = fields.Integer(string='Qty Pass')
    qty_fail = fields.Integer(string='Qty Fail')
    note = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft', tracking=True)
    date = fields.Date(default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)

    # -------- SEQUENCE ----------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tpart.qc.check') or _('New')
        return super().create(vals_list)

    # -------- ONCHANGE ----------
    @api.onchange('qty_pass', 'qty_fail')
    def _onchange_qty(self):
        if self.qty_pass + self.qty_fail != self.qty_check:
            return {'warning': {
                'title': 'Sum mismatch',
                'message': 'Pass + Fail harus sama dengan Qty to Check'
            }}

    # -------- ACTION BUTTONS ----------
    def action_done(self):
        self.write({'state': 'done'})
        # todo: generate stock.move ke rak good/scrap

    def action_cancel(self):
        self.write({'state': 'cancel'})