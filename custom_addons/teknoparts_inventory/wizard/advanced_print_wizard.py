# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class AdvancedPartPrintWizard(models.TransientModel):
    _name = 'tpart.advanced.print.wizard'
    _description = 'Advanced Parts Print Wizard'

    # -------- FILTER OPTIONS --------
    filter_type = fields.Selection([
        ('all', 'All Parts'),
        ('selected', 'Selected Parts Only'),
        ('custom', 'Custom Filter')
    ], string='Filter Type', default='all', required=True)

    selected_part_ids = fields.Many2many('tpart.part', string='Selected Parts')

    # Custom Filters
    brand_ids = fields.Many2many('tpart.part', relation='wizard_brand_rel',
                                 string='Brands',
                                 domain=lambda self: [('brand', '!=', False)])
    category_ids = fields.Many2many('tpart.category', string='Categories')
    part_type_ids = fields.Many2many('tpart.part', relation='wizard_type_rel',
                                     string='Part Types',
                                     domain=lambda self: [('part_type', '!=', False)])

    state_filter = fields.Selection([
        ('all', 'All States'),
        ('draft', 'Draft Only'),
        ('approved', 'Approved Only'),
        ('obsolete', 'Obsolete Only')
    ], string='State Filter', default='all')

    # Stock Filters
    stock_filter = fields.Selection([
        ('all', 'All Stock Levels'),
        ('in_stock', 'In Stock (> 0)'),
        ('out_of_stock', 'Out of Stock (= 0)'),
        ('low_stock', 'Low Stock (< Min Qty)'),
        ('custom_range', 'Custom Stock Range')
    ], string='Stock Filter', default='all')

    stock_min = fields.Float(string='Min Stock Qty', default=0)
    stock_max = fields.Float(string='Max Stock Qty', default=9999)

    # Date Filters
    date_filter = fields.Selection([
        ('all', 'All Dates'),
        ('created_today', 'Created Today'),
        ('created_this_week', 'Created This Week'),
        ('created_this_month', 'Created This Month'),
        ('created_custom', 'Custom Date Range')
    ], string='Date Filter', default='all')

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    # -------- SORTING OPTIONS --------
    sort_by = fields.Selection([
        ('name', 'Part Name'),
        ('part_number', 'Part Number'),
        ('brand', 'Brand'),
        ('create_date', 'Created Date'),
        ('qty_on_hand', 'Stock Quantity'),
        ('category_id', 'Category')
    ], string='Sort By', default='name')

    sort_order = fields.Selection([
        ('asc', 'Ascending'),
        ('desc', 'Descending')
    ], string='Sort Order', default='asc')

    # -------- OUTPUT OPTIONS --------
    output_format = fields.Selection([
        ('pdf_detailed', 'PDF - Detailed Report'),
        ('pdf_summary', 'PDF - Summary Report'),
        ('excel_detailed', 'Excel - Detailed Report'),
        ('excel_summary', 'Excel - Summary Report'),
        ('excel_kartu_stock', 'Excel - Kartu Stock Multiple')
    ], string='Output Format', default='pdf_detailed', required=True)

    # Report Options
    include_images = fields.Boolean(string='Include Part Images', default=True)
    include_stock_history = fields.Boolean(string='Include Stock History', default=False)
    include_qc_history = fields.Boolean(string='Include QC History', default=False)
    include_purchase_history = fields.Boolean(string='Include Purchase History', default=False)

    group_by_category = fields.Boolean(string='Group by Category', default=False)
    group_by_brand = fields.Boolean(string='Group by Brand', default=False)

    # Page Options
    page_break_per_part = fields.Boolean(string='Page Break per Part', default=False)
    show_barcode = fields.Boolean(string='Show Barcode', default=True)

    # Summary Statistics
    show_summary = fields.Boolean(string='Include Summary Statistics', default=True)
    summary_total_parts = fields.Integer(string='Total Parts', compute='_compute_summary', store=False)
    summary_total_value = fields.Float(string='Total Stock Value', compute='_compute_summary', store=False)
    summary_by_brand = fields.Text(string='Summary by Brand', compute='_compute_summary', store=False)

    # Preview Options
    preview_limit = fields.Integer(string='Preview Limit (rows)', default=10)
    preview_data = fields.Text(string='Preview', readonly=True)

    # -------- COMPUTE METHODS --------
    @api.depends('filter_type', 'selected_part_ids', 'brand_ids', 'category_ids',
                 'state_filter', 'stock_filter', 'date_filter')
    def _compute_summary(self):
        for wizard in self:
            parts = wizard._get_filtered_parts()
            wizard.summary_total_parts = len(parts)

            # Calculate total value (assuming standard_price exists)
            total_value = sum(part.qty_on_hand * (part.product_id.standard_price or 0)
                              for part in parts if part.product_id)
            wizard.summary_total_value = total_value

            # Summary by brand
            brand_summary = {}
            for part in parts:
                brand = part.brand or 'Unknown'
                if brand not in brand_summary:
                    brand_summary[brand] = 0
                brand_summary[brand] += 1

            wizard.summary_by_brand = '\n'.join([f"{k}: {v} parts"
                                                 for k, v in brand_summary.items()])

    @api.onchange('filter_type')
    def _onchange_filter_type(self):
        if self.filter_type == 'selected':
            # Get currently selected parts from context
            active_ids = self.env.context.get('active_ids', [])
            if active_ids:
                self.selected_part_ids = [(6, 0, active_ids)]

    @api.onchange('date_filter')
    def _onchange_date_filter(self):
        today = fields.Date.context_today(self)
        if self.date_filter == 'created_today':
            self.date_from = today
            self.date_to = today
        elif self.date_filter == 'created_this_week':
            # Get start of week (Monday)
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            self.date_from = monday
            self.date_to = today
        elif self.date_filter == 'created_this_month':
            self.date_from = today.replace(day=1)
            self.date_to = today

    # -------- HELPER METHODS --------
    def _get_filtered_parts(self):
        """Get parts based on current filter settings"""
        domain = []

        # Base filter
        if self.filter_type == 'selected' and self.selected_part_ids:
            domain.append(('id', 'in', self.selected_part_ids.ids))
        elif self.filter_type == 'custom':
            # Brand filter
            if self.brand_ids:
                brands = [part.brand for part in self.brand_ids if part.brand]
                if brands:
                    domain.append(('brand', 'in', list(set(brands))))

            # Category filter
            if self.category_ids:
                domain.append(('category_id', 'in', self.category_ids.ids))

            # Part type filter
            if self.part_type_ids:
                types = [part.part_type for part in self.part_type_ids if part.part_type]
                if types:
                    domain.append(('part_type', 'in', list(set(types))))

        # State filter
        if self.state_filter != 'all':
            domain.append(('state', '=', self.state_filter))

        # Stock filter
        if self.stock_filter == 'in_stock':
            domain.append(('qty_on_hand', '>', 0))
        elif self.stock_filter == 'out_of_stock':
            domain.append(('qty_on_hand', '=', 0))
        elif self.stock_filter == 'custom_range':
            domain.append(('qty_on_hand', '>=', self.stock_min))
            domain.append(('qty_on_hand', '<=', self.stock_max))

        # Date filter
        if self.date_filter == 'created_custom' and self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_filter == 'created_custom' and self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        elif self.date_filter in ['created_today', 'created_this_week', 'created_this_month']:
            if self.date_from:
                domain.append(('create_date', '>=', self.date_from))
            if self.date_to:
                domain.append(('create_date', '<=', self.date_to))

        # Get parts with domain
        parts = self.env['tpart.part'].search(domain)

        # Apply sorting
        if self.sort_by:
            order = f"{self.sort_by} {self.sort_order}"
            parts = parts.search([('id', 'in', parts.ids)], order=order)

        return parts

    # -------- ACTION METHODS --------
    def action_preview(self):
        """Preview the data before printing"""
        parts = self._get_filtered_parts()

        if not parts:
            raise UserError(_('No parts found with current filter settings.'))

        # Create preview text
        preview_parts = parts[:self.preview_limit] if self.preview_limit else parts
        preview_lines = []

        for part in preview_parts:
            line = f"• {part.name} [{part.part_number}] - {part.brand} - Stock: {part.qty_on_hand}"
            preview_lines.append(line)

        if len(parts) > self.preview_limit:
            preview_lines.append(f"... and {len(parts) - self.preview_limit} more parts")

        self.preview_data = '\n'.join(preview_lines)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_print(self):
        """Execute the print based on selected format"""
        parts = self._get_filtered_parts()

        if not parts:
            raise UserError(_('No parts found with current filter settings.'))

        # Prepare context with wizard settings
        context = {
            'wizard_id': self.id,
            'include_images': self.include_images,
            'include_stock_history': self.include_stock_history,
            'include_qc_history': self.include_qc_history,
            'include_purchase_history': self.include_purchase_history,
            'group_by_category': self.group_by_category,
            'group_by_brand': self.group_by_brand,
            'page_break_per_part': self.page_break_per_part,
            'show_barcode': self.show_barcode,
            'show_summary': self.show_summary,
        }

        # Route to appropriate report
        if self.output_format == 'pdf_detailed':
            return {
                'type': 'ir.actions.report',
                'report_name': 'tpart.advanced.pdf.detailed',
                'report_type': 'qweb-pdf',
                'data': {'part_ids': parts.ids},
                'context': context,
            }
        elif self.output_format == 'pdf_summary':
            return {
                'type': 'ir.actions.report',
                'report_name': 'tpart.advanced.pdf.summary',
                'report_type': 'qweb-pdf',
                'data': {'part_ids': parts.ids},
                'context': context,
            }
        elif self.output_format == 'excel_detailed':
            return {
                'type': 'ir.actions.report',
                'report_name': 'tpart.advanced.xlsx.detailed',
                'report_type': 'xlsx',
                'data': {'part_ids': parts.ids},
                'context': context,
            }
        elif self.output_format == 'excel_summary':
            return {
                'type': 'ir.actions.report',
                'report_name': 'tpart.advanced.xlsx.summary',
                'report_type': 'xlsx',
                'data': {'part_ids': parts.ids},
                'context': context,
            }
        elif self.output_format == 'excel_kartu_stock':
            return {
                'type': 'ir.actions.report',
                'report_name': 'tpart.advanced.xlsx.kartu',
                'report_type': 'xlsx',
                'data': {'part_ids': parts.ids},
                'context': context,
            }

    def action_reset_filters(self):
        """Reset all filters to default"""
        self.write({
            'filter_type': 'all',
            'selected_part_ids': [(5, 0, 0)],
            'brand_ids': [(5, 0, 0)],
            'category_ids': [(5, 0, 0)],
            'part_type_ids': [(5, 0, 0)],
            'state_filter': 'all',
            'stock_filter': 'all',
            'date_filter': 'all',
            'date_from': False,
            'date_to': False,
            'stock_min': 0,
            'stock_max': 9999,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }