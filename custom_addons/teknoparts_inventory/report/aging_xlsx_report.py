from odoo import models, fields, _


class ReportAgingXlsx(models.AbstractModel):
    _name = 'report.teknoparts_inventory.aging_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, parts):
        sheet = workbook.add_worksheet('Aging Report')

        # Header format
        header = ['Part Number', 'Name', 'Brand', 'Category', 'Type',
                  'Aging (Days)', 'On Hand', 'Warranty (Mth)', 'Create Date']
        bold_fmt = workbook.add_format({'bold': True, 'bg_color': '#B8CCE4'})

        # Write headers
        for col, title in enumerate(header):
            sheet.write(0, col, title, bold_fmt)

        row = 1
        today = fields.Date.context_today(self)

        # Debug: Write all parts first (remove aging filter temporarily)
        for o in parts:
            if o.create_date:
                aging = (today - o.create_date.date()).days

                # Write data for all parts (you can add back aging > 90 filter later)
                sheet.write(row, 0, o.part_number or '')
                sheet.write(row, 1, o.name or '')
                sheet.write(row, 2, dict(o._fields['brand'].selection).get(o.brand, o.brand) if o.brand else '')
                sheet.write(row, 3, o.category_id.name or '')
                sheet.write(row, 4,
                            dict(o._fields['part_type'].selection).get(o.part_type, o.part_type) if o.part_type else '')
                sheet.write(row, 5, aging)
                sheet.write(row, 6, o.qty_on_hand)
                sheet.write(row, 7, o.warranty_month)
                sheet.write(row, 8, str(o.create_date.date()) if o.create_date else '')
                row += 1

        # Auto-adjust column width
        for col in range(len(header)):
            sheet.set_column(col, col, 15)