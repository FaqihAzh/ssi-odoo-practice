from odoo import api, fields, models

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_part_id = fields.Many2one('tpart.part', string='Spare Part')
    x_brand = fields.Selection(related='x_part_id.brand', store=True, readonly=True)
    x_model_hp = fields.Char(related='x_part_id.model_hp', store=True, readonly=True)

    # otomatis isi part_id saat product dipilih
    @api.onchange('product_id')
    def _onchange_product_auto_part(self):
        if self.product_id and self.product_id.x_part_id:
            self.x_part_id = self.product_id.x_part_id