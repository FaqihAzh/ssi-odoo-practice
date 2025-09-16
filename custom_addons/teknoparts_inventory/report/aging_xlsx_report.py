from odoo import models, fields, _

class ReportAgingXlsx(models.AbstractModel):
    _name = 'report.teknoparts_inventory.aging_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, parts):
        sheet = workbook.add_worksheet('Aging')
        header = ['Part Number', 'Name', 'Brand', 'Category', 'Type',
                  'Aging (Days)', 'On Hand', 'Warranty (Mth)']
        bold_fmt = workbook.add_format({'bold': True, 'bg_color': '#B8CCE4'})
        for col, title in enumerate(header):
            sheet.write(0, col, title, bold_fmt)

        row = 1
        today = fields.Date.context_today(self)
        for o in parts:
            aging = (today - o.create_date.date()).days
            if aging > 90:
                sheet.write(row, 0, o.part_number)
                sheet.write(row, 1, o.name)
                sheet.write(row, 2, o.brand)
                sheet.write(row, 3, o.category_id.name or '')
                sheet.write(row, 4, o.part_type)
                sheet.write(row, 5, aging)
                sheet.write(row, 6, o.qty_on_hand)
                sheet.write(row, 7, o.warranty_month)
                row += 1