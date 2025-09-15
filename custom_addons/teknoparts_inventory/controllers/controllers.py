# -*- coding: utf-8 -*-
# from odoo import http


# class TeknopartsInventory(http.Controller):
#     @http.route('/teknoparts_inventory/teknoparts_inventory', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/teknoparts_inventory/teknoparts_inventory/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('teknoparts_inventory.listing', {
#             'root': '/teknoparts_inventory/teknoparts_inventory',
#             'objects': http.request.env['teknoparts_inventory.teknoparts_inventory'].search([]),
#         })

#     @http.route('/teknoparts_inventory/teknoparts_inventory/objects/<model("teknoparts_inventory.teknoparts_inventory"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('teknoparts_inventory.object', {
#             'object': obj
#         })

