from odoo import models, fields, _

class AgingXlsx(models.AbstractModel):
    _name = 'report.teknoparts_inventory.aging_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, parts):
        sheet = workbook.add_worksheet('Aging')
        header = ['Part Number', 'Name', 'Aging (Days)', 'Qty On Hand']
        for col, title in enumerate(header):
            sheet.write(0, col, title)
        row = 1
        for part in parts:
            aging = (fields.Date.today() - part.create_date.date()).days
            if aging > 90:
                sheet.write(row, 0, part.part_number)
                sheet.write(row, 1, part.name)
                sheet.write(row, 2, aging)
                sheet.write(row, 3, part.qty_on_hand)
                row += 1