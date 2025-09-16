from odoo import models, fields, _

class OpnameTemplateXlsx(models.AbstractModel):
    _name = 'report.teknoparts_inventory.opname_template_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, docs):
        sheet = workbook.add_worksheet('Opname')
        header = ['Part Number', 'Name', 'Brand', 'System Qty', 'Real Qty', 'Difference']
        bold = workbook.add_format({'bold': True})
        for col, title in enumerate(header):
            sheet.write(0, col, title, bold)

        for row, line in enumerate(docs.line_ids, start=1):
            sheet.write(row, 0, line.part_id.part_number)
            sheet.write(row, 1, line.part_id.name)
            sheet.write(row, 2, line.part_id.brand)
            sheet.write(row, 3, line.system_qty)
            sheet.write(row, 4, line.real_qty)
            sheet.write(row, 5, line.difference)