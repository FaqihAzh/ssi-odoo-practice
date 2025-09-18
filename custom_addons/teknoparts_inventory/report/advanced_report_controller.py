# ============================================================================
# FILE: custom_addons/teknoparts_inventory/report/advanced_report_controller.py
# ============================================================================
# -*- coding: utf-8 -*-
from odoo import api, models, _
from datetime import datetime


class AdvancedPartsDetailedPdfReport(models.AbstractModel):
    _name = 'report.tpart.advanced.pdf.detailed'  # SHORTENED NAME
    _description = 'Advanced Parts Detailed PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Get parts from data
        part_ids = data.get('part_ids', []) if data else docids
        parts = self.env['tpart.part'].browse(part_ids)

        # Get wizard if available
        wizard_id = self.env.context.get('wizard_id')
        wizard = self.env['tpart.advanced.print.wizard'].browse(wizard_id) if wizard_id else None

        return {
            'doc_ids': part_ids,
            'doc_model': 'tpart.part',
            'docs': parts,
            'data': data,
            'wizard': wizard,
            'datetime': datetime,  # Add datetime for template
            'context_today': datetime.now().strftime('%Y-%m-%d'),
        }


class AdvancedPartsSummaryPdfReport(models.AbstractModel):
    _name = 'report.tpart.advanced.pdf.summary'  # SHORTENED NAME
    _description = 'Advanced Parts Summary PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Get parts from data
        part_ids = data.get('part_ids', []) if data else docids
        parts = self.env['tpart.part'].browse(part_ids)

        # Calculate summary statistics
        brand_stats = {}
        category_stats = {}
        state_stats = {}

        for part in parts:
            # Brand stats
            brand = part.brand or 'Unknown'
            brand_stats[brand] = brand_stats.get(brand, 0) + 1

            # Category stats
            category = part.category_id.name if part.category_id else 'Uncategorized'
            category_stats[category] = category_stats.get(category, 0) + 1

            # State stats
            state = part.state or 'Unknown'
            state_stats[state] = state_stats.get(state, 0) + 1

        return {
            'doc_ids': part_ids,
            'doc_model': 'tpart.part',
            'docs': parts,
            'data': data,
            'brand_stats': brand_stats,
            'category_stats': category_stats,
            'state_stats': state_stats,
            'total_stock': sum(part.qty_on_hand for part in parts),
            'in_stock_count': len([p for p in parts if p.qty_on_hand > 0]),
            'out_of_stock_count': len([p for p in parts if p.qty_on_hand == 0]),
            'datetime': datetime,
        }