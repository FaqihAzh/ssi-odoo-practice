from odoo import api, models, _

class KartuStockReport(models.AbstractModel):
    _name = 'report.teknoparts_inventory.kartu_stock_template'
    _description = 'Kartu Stock per Part'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tpart.part'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'tpart.part',
            'docs': docs,
        }