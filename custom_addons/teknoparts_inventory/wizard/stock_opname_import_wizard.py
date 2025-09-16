from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockOpnameImportWizard(models.TransientModel):
    _name = 'tpart.stock.opname.import.wizard'
    _description = 'Import Hasil Opname'

    location_id = fields.Many2one('stock.location', readonly=True)
    file = fields.Binary(string='Excel File', required=True)

    def action_import(self):
        # TODO: parsing pakai pandas / openpyxl
        raise UserError('Fitur import akan segera datang :)')