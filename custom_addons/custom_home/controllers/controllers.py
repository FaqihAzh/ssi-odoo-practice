# -*- coding: utf-8 -*-
# from odoo import http


# class CustomHome(http.Controller):
#     @http.route('/custom_home/custom_home', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_home/custom_home/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_home.listing', {
#             'root': '/custom_home/custom_home',
#             'objects': http.request.env['custom_home.custom_home'].search([]),
#         })

#     @http.route('/custom_home/custom_home/objects/<model("custom_home.custom_home"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_home.object', {
#             'object': obj
#         })

