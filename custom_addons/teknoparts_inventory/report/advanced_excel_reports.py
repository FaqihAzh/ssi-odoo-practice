# -*- coding: utf-8 -*-
from odoo import models, fields, _
from datetime import datetime
import base64
import io


class AdvancedPartsDetailedXlsx(models.AbstractModel):
    _name = 'report.tpart.advanced.xlsx.detailed'  # SHORTENED NAME
    _description = 'Advanced Parts Detailed Excel Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        # Get parts from data
        part_ids = data.get('part_ids', [])
        parts = self.env['tpart.part'].browse(part_ids)

        # Get wizard settings from context
        context = self.env.context
        include_images = context.get('include_images', False)
        include_stock_history = context.get('include_stock_history', False)
        include_qc_history = context.get('include_qc_history', False)
        group_by_brand = context.get('group_by_brand', False)
        group_by_category = context.get('group_by_category', False)
        show_summary = context.get('show_summary', True)

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        subheader_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E2F3',
            'align': 'center',
            'border': 1
        })

        cell_format = workbook.add_format({
            'border': 1,
            'valign': 'top'
        })

        number_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00'
        })

        # Create main sheet
        sheet = workbook.add_worksheet('Parts Detailed Report')

        # Set column widths
        sheet.set_column('A:A', 15)  # Part Number
        sheet.set_column('B:B', 25)  # Name
        sheet.set_column('C:C', 12)  # Brand
        sheet.set_column('D:D', 15)  # Model HP
        sheet.set_column('E:E', 15)  # Category
        sheet.set_column('F:F', 12)  # Type
        sheet.set_column('G:G', 10)  # Stock
        sheet.set_column('H:H', 10)  # Reserved
        sheet.set_column('I:I', 10)  # Available
        sheet.set_column('J:J', 12)  # State
        sheet.set_column('K:K', 12)  # Warranty
        sheet.set_column('L:L', 15)  # Created Date

        # Title and metadata
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sheet.merge_range('A1:L1', 'TEKNOWRAPPARTS - DETAILED PARTS REPORT',
                          workbook.add_format({
                              'bold': True,
                              'font_size': 16,
                              'align': 'center',
                              'bg_color': '#4472C4',
                              'color': 'white'
                          }))

        sheet.write('A2', f'Generated: {current_time}', cell_format)
        sheet.write('A3', f'Total Parts: {len(parts)}', cell_format)

        # Headers
        headers = [
            'Part Number', 'Part Name', 'Brand', 'Model HP', 'Category',
            'Type', 'Stock', 'Reserved', 'Available', 'State', 'Warranty (M)', 'Created Date'
        ]

        start_row = 4
        for col, header in enumerate(headers):
            sheet.write(start_row, col, header, header_format)

        # Data rows
        row = start_row + 1

        # Group data if needed
        if group_by_brand:
            grouped_parts = {}
            for part in parts:
                brand = part.brand or 'Unknown'
                if brand not in grouped_parts:
                    grouped_parts[brand] = []
                grouped_parts[brand].append(part)

            for brand, brand_parts in grouped_parts.items():
                # Brand header
                sheet.merge_range(f'A{row + 1}:L{row + 1}', f'BRAND: {brand.upper()}', subheader_format)
                row += 1

                for part in brand_parts:
                    self._write_part_row(sheet, row, part, cell_format, number_format)
                    row += 1
                row += 1  # Space between brands

        elif group_by_category:
            grouped_parts = {}
            for part in parts:
                category = part.category_id.name if part.category_id else 'Uncategorized'
                if category not in grouped_parts:
                    grouped_parts[category] = []
                grouped_parts[category].append(part)

            for category, cat_parts in grouped_parts.items():
                # Category header
                sheet.merge_range(f'A{row + 1}:L{row + 1}', f'CATEGORY: {category.upper()}', subheader_format)
                row += 1

                for part in cat_parts:
                    self._write_part_row(sheet, row, part, cell_format, number_format)
                    row += 1
                row += 1  # Space between categories
        else:
            # No grouping
            for part in parts:
                self._write_part_row(sheet, row, part, cell_format, number_format)
                row += 1

        # Summary statistics if requested
        if show_summary:
            self._add_summary_sheet(workbook, parts)

        # Stock history sheet if requested
        if include_stock_history:
            self._add_stock_history_sheet(workbook, parts)

        # QC history sheet if requested
        if include_qc_history:
            self._add_qc_history_sheet(workbook, parts)

    def _write_part_row(self, sheet, row, part, cell_format, number_format):
        """Write a single part row to the sheet"""
        sheet.write(row, 0, part.part_number or '', cell_format)
        sheet.write(row, 1, part.name or '', cell_format)
        sheet.write(row, 2, dict(part._fields['brand'].selection).get(part.brand, part.brand) if part.brand else '',
                    cell_format)
        sheet.write(row, 3, part.model_hp or '', cell_format)
        sheet.write(row, 4, part.category_id.name or '', cell_format)
        sheet.write(row, 5, dict(part._fields['part_type'].selection).get(part.part_type,
                                                                          part.part_type) if part.part_type else '',
                    cell_format)
        sheet.write(row, 6, part.qty_on_hand, number_format)
        sheet.write(row, 7, part.qty_reserved, number_format)
        sheet.write(row, 8, part.qty_available, number_format)
        sheet.write(row, 9, dict(part._fields['state'].selection).get(part.state, part.state) if part.state else '',
                    cell_format)
        sheet.write(row, 10, part.warranty_month, cell_format)
        sheet.write(row, 11, part.create_date.strftime('%Y-%m-%d %H:%M') if part.create_date else '', cell_format)

    def _add_summary_sheet(self, workbook, parts):
        """Add summary statistics sheet"""
        sheet = workbook.add_worksheet('Summary')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'color': 'white',
            'align': 'center'
        })

        cell_format = workbook.add_format({'border': 1})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0'})

        # Title
        sheet.merge_range('A1:D1', 'SUMMARY STATISTICS', header_format)

        row = 3

        # Basic stats
        sheet.write(row, 0, 'Total Parts:', header_format)
        sheet.write(row, 1, len(parts), number_format)
        row += 1

        # Summary by Brand
        sheet.write(row, 0, 'SUMMARY BY BRAND:', header_format)
        row += 2

        brand_stats = {}
        for part in parts:
            brand = part.brand or 'Unknown'
            if brand not in brand_stats:
                brand_stats[brand] = {'count': 0, 'total_stock': 0}
            brand_stats[brand]['count'] += 1
            brand_stats[brand]['total_stock'] += part.qty_on_hand

        sheet.write(row, 0, 'Brand', header_format)
        sheet.write(row, 1, 'Part Count', header_format)
        sheet.write(row, 2, 'Total Stock', header_format)
        row += 1

        for brand, stats in brand_stats.items():
            sheet.write(row, 0, brand, cell_format)
            sheet.write(row, 1, stats['count'], number_format)
            sheet.write(row, 2, stats['total_stock'], number_format)
            row += 1

        # Summary by Category
        row += 2
        sheet.write(row, 0, 'SUMMARY BY CATEGORY:', header_format)
        row += 2

        category_stats = {}
        for part in parts:
            category = part.category_id.name if part.category_id else 'Uncategorized'
            if category not in category_stats:
                category_stats[category] = {'count': 0, 'total_stock': 0}
            category_stats[category]['count'] += 1
            category_stats[category]['total_stock'] += part.qty_on_hand

        sheet.write(row, 0, 'Category', header_format)
        sheet.write(row, 1, 'Part Count', header_format)
        sheet.write(row, 2, 'Total Stock', header_format)
        row += 1

        for category, stats in category_stats.items():
            sheet.write(row, 0, category, cell_format)
            sheet.write(row, 1, stats['count'], number_format)
            sheet.write(row, 2, stats['total_stock'], number_format)
            row += 1

        # Summary by State
        row += 2
        sheet.write(row, 0, 'SUMMARY BY STATE:', header_format)
        row += 2

        state_stats = {}
        for part in parts:
            state = dict(part._fields['state'].selection).get(part.state, part.state) if part.state else 'Unknown'
            if state not in state_stats:
                state_stats[state] = 0
            state_stats[state] += 1

        sheet.write(row, 0, 'State', header_format)
        sheet.write(row, 1, 'Count', header_format)
        row += 1

        for state, count in state_stats.items():
            sheet.write(row, 0, state, cell_format)
            sheet.write(row, 1, count, number_format)
            row += 1

    def _add_stock_history_sheet(self, workbook, parts):
        """Add stock movement history sheet"""
        sheet = workbook.add_worksheet('Stock History')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'color': 'white',
            'align': 'center',
            'border': 1
        })

        cell_format = workbook.add_format({'border': 1})

        # Headers
        headers = ['Part Number', 'Part Name', 'Date', 'Reference', 'From → To', 'Quantity', 'Status']

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # Set column widths
        sheet.set_column('A:A', 15)  # Part Number
        sheet.set_column('B:B', 25)  # Part Name
        sheet.set_column('C:C', 12)  # Date
        sheet.set_column('D:D', 20)  # Reference
        sheet.set_column('E:E', 25)  # Location
        sheet.set_column('F:F', 10)  # Quantity
        sheet.set_column('G:G', 12)  # Status

        row = 1
        for part in parts:
            if part.stock_move_line_ids:
                for move in part.stock_move_line_ids:
                    sheet.write(row, 0, part.part_number or '', cell_format)
                    sheet.write(row, 1, part.name or '', cell_format)
                    sheet.write(row, 2, move.date.strftime('%Y-%m-%d') if move.date else '', cell_format)
                    sheet.write(row, 3, move.reference or '', cell_format)
                    sheet.write(row, 4, f"{move.location_id.name} → {move.location_dest_id.name}", cell_format)
                    sheet.write(row, 5, move.qty_done, cell_format)
                    sheet.write(row, 6, move.state or '', cell_format)
                    row += 1

    def _add_qc_history_sheet(self, workbook, parts):
        """Add QC history sheet"""
        sheet = workbook.add_worksheet('QC History')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'color': 'white',
            'align': 'center',
            'border': 1
        })

        cell_format = workbook.add_format({'border': 1})

        # Headers
        headers = ['Part Number', 'Part Name', 'QC Number', 'Date', 'Qty Check', 'Qty Pass', 'Qty Fail', 'Pass Rate %',
                   'Notes']

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # Set column widths
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 12)
        sheet.set_column('I:I', 30)

        row = 1
        for part in parts:
            qc_checks = self.env['tpart.qc.check'].search([('part_id', '=', part.id)])
            for qc in qc_checks:
                pass_rate = (qc.qty_pass / max(qc.qty_check, 1)) * 100 if qc.qty_check > 0 else 0

                sheet.write(row, 0, part.part_number or '', cell_format)
                sheet.write(row, 1, part.name or '', cell_format)
                sheet.write(row, 2, qc.name or '', cell_format)
                sheet.write(row, 3, qc.date.strftime('%Y-%m-%d') if qc.date else '', cell_format)
                sheet.write(row, 4, qc.qty_check, cell_format)
                sheet.write(row, 5, qc.qty_pass, cell_format)
                sheet.write(row, 6, qc.qty_fail, cell_format)
                sheet.write(row, 7, f"{pass_rate:.1f}%", cell_format)
                sheet.write(row, 8, qc.note or '', cell_format)
                row += 1


class AdvancedPartsSummaryXlsx(models.AbstractModel):
    _name = 'report.tpart.advanced.xlsx.summary'  # SHORTENED NAME
    _description = 'Advanced Parts Summary Excel Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        # Get parts from data
        part_ids = data.get('part_ids', [])
        parts = self.env['tpart.part'].browse(part_ids)

        # Create summary sheet
        sheet = workbook.add_worksheet('Parts Summary')

        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'bg_color': '#4472C4',
            'color': 'white',
            'align': 'center'
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E2F3',
            'align': 'center',
            'border': 1
        })

        cell_format = workbook.add_format({'border': 1})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

        # Title
        sheet.merge_range('A1:H1', 'PARTS SUMMARY REPORT', title_format)

        # Basic summary headers
        headers = ['Part Number', 'Name', 'Brand', 'Category', 'Stock', 'State', 'Warranty', 'Created']

        start_row = 3
        for col, header in enumerate(headers):
            sheet.write(start_row, col, header, header_format)

        # Set column widths
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 12)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 12)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 12)

        # Data rows
        row = start_row + 1
        for part in parts:
            sheet.write(row, 0, part.part_number or '', cell_format)
            sheet.write(row, 1, part.name or '', cell_format)
            sheet.write(row, 2, dict(part._fields['brand'].selection).get(part.brand, part.brand) if part.brand else '',
                        cell_format)
            sheet.write(row, 3, part.category_id.name or '', cell_format)
            sheet.write(row, 4, part.qty_on_hand, number_format)
            sheet.write(row, 5, dict(part._fields['state'].selection).get(part.state, part.state) if part.state else '',
                        cell_format)
            sheet.write(row, 6, part.warranty_month, cell_format)
            sheet.write(row, 7, part.create_date.strftime('%Y-%m-%d') if part.create_date else '', cell_format)
            row += 1


class AdvancedKartuStockMultipleXlsx(models.AbstractModel):
    _name = 'report.tpart.advanced.xlsx.kartu'  # SHORTENED NAME
    _description = 'Advanced Multiple Kartu Stock Excel Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        # Get parts from data
        part_ids = data.get('part_ids', [])
        parts = self.env['tpart.part'].browse(part_ids)

        # Create separate sheet for each part or combined based on settings
        context = self.env.context
        page_break_per_part = context.get('page_break_per_part', False)

        if page_break_per_part:
            # Create separate sheet for each part
            for part in parts:
                self._create_kartu_stock_sheet(workbook, part)
        else:
            # Create combined sheet
            self._create_combined_kartu_stock_sheet(workbook, parts)

    def _create_kartu_stock_sheet(self, workbook, part):
        """Create individual kartu stock sheet for a part"""
        sheet_name = f"KS_{part.part_number}"[:31]  # Excel sheet name limit
        sheet = workbook.add_worksheet(sheet_name)

        # Formats
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center'
        })

        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4472C4', 'color': 'white', 'border': 1
        })

        cell_format = workbook.add_format({'border': 1})

        # Title
        sheet.merge_range('A1:F1', f'KARTU STOCK - {part.name}', title_format)

        # Part info
        sheet.write('A3', 'Part Number:', header_format)
        sheet.write('B3', part.part_number or '', cell_format)
        sheet.write('A4', 'Brand/Model:', header_format)
        sheet.write('B4', f"{part.brand} / {part.model_hp}", cell_format)
        sheet.write('A5', 'Category:', header_format)
        sheet.write('B5', part.category_id.name or '', cell_format)

        # Stock movement headers
        movement_headers = ['Date', 'Reference', 'From', 'To', 'Qty', 'Status']
        start_row = 7

        for col, header in enumerate(movement_headers):
            sheet.write(start_row, col, header, header_format)

        # Movement data
        row = start_row + 1
        for move in part.stock_move_line_ids:
            sheet.write(row, 0, move.date.strftime('%Y-%m-%d') if move.date else '', cell_format)
            sheet.write(row, 1, move.reference or '', cell_format)
            sheet.write(row, 2, move.location_id.name or '', cell_format)
            sheet.write(row, 3, move.location_dest_id.name or '', cell_format)
            sheet.write(row, 4, move.qty_done, cell_format)
            sheet.write(row, 5, move.state or '', cell_format)
            row += 1

    def _create_combined_kartu_stock_sheet(self, workbook, parts):
        """Create combined kartu stock sheet for all parts"""
        sheet = workbook.add_worksheet('Combined Kartu Stock')

        # Formats
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center',
            'bg_color': '#4472C4', 'color': 'white'
        })

        part_header_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'bg_color': '#D9E2F3', 'border': 1
        })

        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4472C4', 'color': 'white', 'border': 1
        })

        cell_format = workbook.add_format({'border': 1})

        # Title
        sheet.merge_range('A1:G1', 'COMBINED KARTU STOCK REPORT', title_format)

        row = 3
        for part in parts:
            # Part header
            sheet.merge_range(f'A{row}:G{row}',
                              f'{part.name} [{part.part_number}] - Stock: {part.qty_on_hand}',
                              part_header_format)
            row += 1

            # Movement headers
            headers = ['Date', 'Reference', 'From', 'To', 'Qty', 'Status', 'Notes']
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)
            row += 1

            # Movement data
            if part.stock_move_line_ids:
                for move in part.stock_move_line_ids[:10]:  # Limit to recent 10 moves
                    sheet.write(row, 0, move.date.strftime('%Y-%m-%d') if move.date else '', cell_format)
                    sheet.write(row, 1, move.reference or '', cell_format)
                    sheet.write(row, 2, move.location_id.name or '', cell_format)
                    sheet.write(row, 3, move.location_dest_id.name or '', cell_format)
                    sheet.write(row, 4, move.qty_done, cell_format)
                    sheet.write(row, 5, move.state or '', cell_format)
                    sheet.write(row, 6, '', cell_format)
                    row += 1
            else:
                sheet.write(row, 0, 'No stock movements found', cell_format)
                row += 1

            row += 1  # Space between parts