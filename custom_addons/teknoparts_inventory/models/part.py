from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class TpartPart(models.Model):
    _name = 'tpart.part'
    _description = 'Spare Part HP'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'name'

    # -------- BASIC ----------
    name = fields.Char(string='Nama Part', required=True, tracking=True)
    part_number = fields.Char(string='Part Number', required=True, tracking=True)
    barcode = fields.Char(string='Barcode')
    brand = fields.Selection([
        ('apple', 'Apple'),
        ('samsung', 'Samsung'),
        ('xiaomi', 'Xiaomi'),
        ('oppo', 'Oppo'),
        ('vivo', 'Vivo'),
        ('other', 'Other')
    ], string='Brand', required=True)
    model_hp = fields.Char(string='Model HP', help="Contoh: iPhone 15, Galaxy S23")
    category_id = fields.Many2one('tpart.category', string='Category')
    part_type = fields.Selection([
        ('original', 'Original'),
        ('oem', 'OEM'),
        ('refurb', 'Refurbished')
    ], string='Type', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure',
                             default=lambda self: self.env.ref('uom.product_uom_unit'))
    warranty_month = fields.Integer(string='Warranty (Month)', default=0)
    active = fields.Boolean(default=True)
    image = fields.Image()

    # -------- RELASI KE PRODUCT ----------
    product_id = fields.Many2one('product.template', string='Linked Product',
                                 readonly=True, copy=False)

    # -------- COMPUTE QTY ----------
    qty_on_hand = fields.Float(compute='_compute_qty', string='On Hand')
    qty_reserved = fields.Float(compute='_compute_qty', string='Reserved')
    qty_available = fields.Float(compute='_compute_qty', string='Available')

    # -------- STATE ----------
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('obsolete', 'Obsolete')
    ], default='draft', tracking=True)

    # -------- SQL CONSTRAINT ----------
    _sql_constraints = [
        ('unique_part_number_type', 'unique(part_number, part_type)',
         'Kombinasi Part Number & Type harus unik!')
    ]

    # -------- COMPUTE ----------
    @api.depends()
    def _compute_qty(self):
        for rec in self:
            product = rec.product_id.product_variant_id
            rec.qty_on_hand = product.qty_available if product else 0
            rec.qty_reserved = product.outgoing_qty if product else 0
            rec.qty_available = rec.qty_on_hand - rec.qty_reserved

    # -------- ONCHANGE ----------
    @api.onchange('brand')
    def _onchange_brand(self):
        self.model_hp = False  # reset

    # -------- STATE BUTTON ----------
    def action_approve(self):
        self.write({'state': 'approved'})
        self._create_or_update_product()
        # tambahan: isi link balik
        for rec in self:
            if rec.product_id:
                rec.product_id.write({
                    'x_is_spare_part': True,
                    'x_part_id': rec.id,
                    'x_qc_required': True,  # default QC
                })

    def action_set_obsolete(self):
        self.write({'state': 'obsolete'})

    # -------- DUPLICATE KE PRODUCT.TEMPLATE ----------
    def _create_or_update_product(self):
        Product = self.env['product.template']
        for rec in self:
            if rec.product_id:
                continue
            product = Product.create({
                'name': rec.name,
                'default_code': rec.part_number,
                'barcode': rec.barcode,
                'type': 'product',
                'uom_id': rec.uom_id.id,
                'uom_po_id': rec.uom_id.id,
                'list_price': 0,
                'standard_price': 0,
                'x_is_spare_part': True,
                'x_part_id': rec.id,
            })
            rec.product_id = product

    def open_form_detail(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tpart.part',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }