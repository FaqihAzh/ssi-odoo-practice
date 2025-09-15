from odoo import api, models

class QcFailureReport(models.AbstractModel):
    _name = 'report.teknoparts_inventory.qc_failure_template'
    _description = 'QC Failure per Supplier'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tpart.qc.check'].browse(docids)
        return {'docs': docs}