# -*- coding: utf-8 -*-

import logging                                  # modul logging untuk menulis error/diagnostic ke log
from odoo import api, fields, models, _         # import API Odoo dasar
from odoo.exceptions import ValidationError     # import exception Odoo standar bila perlu raise

_logger = logging.getLogger(__name__)          # logger modul, dipakai untuk mencatat error

class TpartPart(models.Model):
    _name = 'tpart.part'                        # technical model name
    _description = 'Spare Part HP'              # deskripsi model
    _inherit = ['mail.thread', 'mail.activity.mixin']  # menambahkan fitur chatter & activities
    _rec_name = 'name'                          # field yang dipakai sebagai nama record
    _order = 'name'                             # default order by name

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
        ('other', 'Other'),
    ], string='Brand', required=True)
    model_hp = fields.Char(string='Model HP', help="Contoh: iPhone 15, Galaxy S23")
    category_id = fields.Many2one('tpart.category', string='Category')
    part_type = fields.Selection([
        ('original', 'Original'),
        ('oem', 'OEM'),
        ('refurb', 'Refurbished'),
    ], string='Type', required=True)
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
    )
    warranty_month = fields.Integer(string='Warranty (Month)', default=0)
    active = fields.Boolean(default=True)
    image = fields.Image()

    # -------- RELASI KE PRODUCT ----------
    product_id = fields.Many2one(
        'product.template',
        string='Linked Product',
        readonly=True,
        copy=False,
        ondelete='set null'
    )

    # -------- COMPUTE QTY ----------
    qty_on_hand = fields.Float(
        compute='_compute_qty',
        string='On Hand',
        store=False
    )
    qty_reserved = fields.Float(
        compute='_compute_qty',
        string='Reserved',
        store=False
    )
    qty_available = fields.Float(
        compute='_compute_qty',
        string='Available',
        store=False
    )

    # -------- STATE ----------
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('obsolete', 'Obsolete'),
    ], default='draft', tracking=True)

    # -------- SQL CONSTRAINT ----------
    _sql_constraints = [
        (
            'unique_part_number_type',
            'unique(part_number, part_type)',
            'Kombinasi Part Number & Type harus unik!'
        )
    ]

    # -------- COMPUTE QTY IMPLEMENTATION ----------
    @api.depends(
        'product_id',
        'product_id.product_variant_ids.qty_available',
        'product_id.product_variant_ids.outgoing_qty'
    )
    def _compute_qty(self):
        """
        Menghitung qty berdasarkan product.template yang ter-link.
        Kami mengambil variant pertama (apabila ada multiple variant),
        lalu membaca qty yang tersedia dan outgoing (reserve).
        """
        for rec in self:
            # default nilai 0
            rec.qty_on_hand = 0.0
            rec.qty_reserved = 0.0
            rec.qty_available = 0.0

            if rec.product_id and rec.product_id.product_variant_ids:
                # ambil variant pertama (umumnya jika template single-variant)
                variant = rec.product_id.product_variant_ids[0]
                # product.product memiliki field qty_available & outgoing_qty di stock module
                rec.qty_on_hand = float(variant.qty_available or 0.0)
                rec.qty_reserved = float(getattr(variant, 'outgoing_qty', 0.0) or 0.0)
                rec.qty_available = rec.qty_on_hand - rec.qty_reserved

    # -------- ONCHANGE ----------
    @api.onchange('brand')
    def _onchange_brand(self):
        # ketika brand berubah, reset model_hp agar user mengisi lagi sesuai brand baru
        self.model_hp = False

    # -------- STATE BUTTON ----------
    def action_approve(self):
        """
        Tombol untuk approve part:
        - set state -> 'approved'
        - create product.template bila belum ada
        - set beberapa flag di product (custom fields x_... )
        """
        for rec in self:
            rec.write({'state': 'approved'})
            rec._create_or_update_product()

            # jika product berhasil dibuat / di-link, update beberapa field kustom di product
            if rec.product_id:
                try:
                    rec.product_id.write({
                        'x_is_spare_part': True,
                        'x_part_id': rec.id,
                        'x_qc_required': True,
                    })
                except Exception as e:
                    _logger.exception("Gagal update product custom fields: %s", e)

    def action_set_obsolete(self):
        # tandai part sebagai obsolete
        self.write({'state': 'obsolete'})

    # -------- DUPLICATE KE PRODUCT.TEMPLATE ----------
    def _create_or_update_product(self):
        """
        Membuat product.template yang ter-link ke spare part ini bila belum ada.
        Bila sudah ada (rec.product_id), method ini tidak membuat produk baru.
        """
        Product = self.env['product.template']
        for rec in self:
            # jika sudah ada product yang ter-link, skip pembuatan
            if rec.product_id:
                continue

            # ambil UoM default jika tidak diisi
            uom = rec.uom_id or self.env.ref('uom.product_uom_unit', raise_if_not_found=False)

            # siapkan vals dasar untuk product.template
            vals = {
                'name': rec.name,
                'default_code': rec.part_number,
                'type': 'product',  # stockable product
                'categ_id': self.env.ref('product.product_category_all', raise_if_not_found=False).id if self.env.ref('product.product_category_all', raise_if_not_found=False) else False,
                'list_price': 0.0,
                'standard_price': 0.0,
                # custom flags supaya product dapat dikenali sebagai spare part
                'x_is_spare_part': True,
                'x_part_id': rec.id,
                'x_qc_required': True,
            }

            if rec.barcode:
                vals['barcode'] = rec.barcode
            if uom:
                vals['uom_id'] = uom.id
                vals['uom_po_id'] = uom.id

            # coba buat product, log error kalau gagal (tidak menghentikan flow)
            try:
                product = Product.create(vals)
                rec.product_id = product.id
            except Exception as e:
                _logger.error("Error creating product for part %s: %s", rec.name, e)

    # -------- OPEN FORM ACTION ----------
    def open_form_detail(self):
        # buka form view record ini (dipakai di button/action)
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tpart.part',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # -------- STOCK MOVE HISTORY (COMPUTED) ----------
    # Pilihan: gunakan Many2many computed karena stock.move.line.product_id bukan field yang menunjuk balik ke tpart.part.
    stock_move_line_ids = fields.Many2many(
        'stock.move.line',
        string='Stock Moves',
        compute='_compute_stock_moves',
        store=False
    )

    @api.depends('product_id', 'product_id.product_variant_ids')
    def _compute_stock_moves(self):
        """
        Ambil stock.move.line yang berkaitan dengan variant product (jika ada).
        Mengembalikan recordset kosong bila tidak terkait product.
        """
        StockMoveLine = self.env['stock.move.line']
        for rec in self:
            if rec.product_id and rec.product_id.product_variant_ids:
                variant = rec.product_id.product_variant_ids[0]
                rec.stock_move_line_ids = StockMoveLine.search([('product_id', '=', variant.id)])
            else:
                rec.stock_move_line_ids = StockMoveLine.browse()  # empty recordset
