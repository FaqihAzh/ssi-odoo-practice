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
                             default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False))
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
    @api.depends('product_id')
    def _compute_qty(self):
        for rec in self:
            if rec.product_id and rec.product_id.product_variant_ids:
                product = rec.product_id.product_variant_ids[0]
                rec.qty_on_hand = product.qty_available or 0.0
                rec.qty_reserved = product.outgoing_qty or 0.0
                rec.qty_available = rec.qty_on_hand - rec.qty_reserved
            else:
                rec.qty_on_hand = 0.0
                rec.qty_reserved = 0.0
                rec.qty_available = 0.0

    # -------- ONCHANGE ----------
    @api.onchange('brand')
    def _onchange_brand(self):
        self.model_hp = False  # reset

    # -------- STATE BUTTON ----------
    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})
            rec._create_or_update_product()
            # Link back to product
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
        """Create product.template record linked to this part"""
        Product = self.env['product.template']
        for rec in self:
            if rec.product_id:
                continue

            # Get default UOM if not set
            uom = rec.uom_id or self.env.ref('uom.product_uom_unit', raise_if_not_found=False)

            vals = {
                'name': rec.name,
                'default_code': rec.part_number,
                'type': 'product',
                'categ_id': self.env.ref('product.product_category_all', raise_if_not_found=False).id,
                'list_price': 0.0,
                'standard_price': 0.0,
                'x_is_spare_part': True,
                'x_part_id': rec.id,
                'x_qc_required': True,
            }

            if rec.barcode:
                vals['barcode'] = rec.barcode
            if uom:
                vals['uom_id'] = uom.id
                vals['uom_po_id'] = uom.id

            try:
                product = Product.create(vals)
                rec.product_id = product.id
            except Exception as e:
                # Log error but don't break the flow
                import logging
                _logger = logging.getLogger(__name__)
                _logger.error(f"Error creating product for part {rec.name}: {e}")

    def open_form_detail(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tpart.part',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # -------- STOCK MOVE HISTORY ----------
    stock_move_line_ids = fields.One2many(
        'stock.move.line', 'product_id',
        string='Stock Moves',
        compute='_compute_stock_moves',
        store=False
    )

    @api.depends('product_id')
    def _compute_stock_moves(self):
        for rec in self:
            if rec.product_id and rec.product_id.product_variant_ids:
                product = rec.product_id.product_variant_ids[0]
                rec.stock_move_line_ids = self.env['stock.move.line'].search([
                    ('product_id', '=', product.id)
                ])
            else:
                rec.stock_move_line_ids = False
