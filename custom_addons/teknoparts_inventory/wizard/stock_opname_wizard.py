from odoo import api, fields, models, _

class StockOpnameWizard(models.TransientModel):
    _name = 'tpart.stock.opname.wizard'
    _description = 'Stock Opname Wizard'

    location_id = fields.Many2one('stock.location', string='Location', required=True,
                                 domain=[('usage', '=', 'internal')])
    line_ids = fields.One2many('tpart.stock.opname.line.wizard', 'wizard_id', string='Lines')

    def action_generate_lines(self):
        """Isi otomatis baris per part yang ada di location."""
        self.line_ids.unlink()
        quants = self.env['stock.quant'].search([('location_id', '=', self.location_id.id)])
        for q in quants:
            if q.product_id.x_part_id:   # hanya spare-part
                self.env['tpart.stock.opname.line.wizard'].create({
                    'wizard_id': self.id,
                    'part_id': q.product_id.x_part_id.id,
                    'system_qty': q.quantity,
                })
        return {"type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new"}

    def action_export_excel(self):
        return self.env.ref('teknoparts_inventory.action_opname_template_xlsx').report_action(self)

    def action_import_excel(self):
        return {"type": "ir.actions.act_window",
                "res_model": 'tpart.stock.opname.import.wizard',
                "view_mode": "form",
                "target": "new",
                'context': {'default_location_id': self.location_id.id}}

class StockOpnameLineWizard(models.TransientModel):
    _name = 'tpart.stock.opname.line.wizard'
    _description = 'Stock Opname Line Wizard'

    wizard_id = fields.Many2one('tpart.stock.opname.wizard')
    part_id = fields.Many2one('tpart.part', string='Part', readonly=True)
    system_qty = fields.Float(string='System Qty', readonly=True)
    real_qty = fields.Float(string='Real Qty', default=0)
    difference = fields.Float(string='Selisih', compute='_compute_diff')

    @api.depends('system_qty', 'real_qty')
    def _compute_diff(self):
        for rec in self:
            rec.difference = rec.real_qty - rec.system_qty