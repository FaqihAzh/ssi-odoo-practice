from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class DashboardController(http.Controller):

    @http.route('/web/dashboard', type='http', auth='user', website=True)
    def dashboard_home(self, **kw):
        """Route untuk dashboard overlay"""
        try:
            return request.render('custom_home.dashboard_template')
        except Exception as e:
            _logger.error(f"Error rendering dashboard: {e}")
            return request.redirect('/web')

    @http.route('/web/dashboard/data', type='json', auth='user')
    def dashboard_data(self, **kw):
        """API endpoint untuk data dashboard"""
        try:
            user = request.env.user
            company = user.company_id

            dashboard_data = {
                'user_name': user.name,
                'company_name': company.name,
                'stats': self._get_dashboard_stats(),
                'recent_activities': self._get_recent_activities(),
                'notifications': self._get_user_notifications(),
            }

            return dashboard_data

        except Exception as e:
            _logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e)}

    @http.route('/web/dashboard/quick_action', type='json', auth='user')
    def dashboard_quick_action(self, action_name, **kw):
        """Handle quick actions dari dashboard"""
        try:
            result = {'success': False}

            if action_name == 'create_sale_order':
                result = {
                    'success': True,
                    'action': {
                        'type': 'ir.actions.act_window',
                        'name': 'New Sale Order',
                        'res_model': 'sale.order',
                        'view_mode': 'form',
                        'target': 'current',
                    }
                }

            elif action_name == 'create_purchase_order':
                result = {
                    'success': True,
                    'action': {
                        'type': 'ir.actions.act_window',
                        'name': 'New Purchase Order',
                        'res_model': 'purchase.order',
                        'view_mode': 'form',
                        'target': 'current',
                    }
                }

            elif action_name == 'create_invoice':
                result = {
                    'success': True,
                    'action': {
                        'type': 'ir.actions.act_window',
                        'name': 'New Invoice',
                        'res_model': 'account.move',
                        'view_mode': 'form',
                        'context': {'default_move_type': 'out_invoice'},
                        'target': 'current',
                    }
                }

            return result

        except Exception as e:
            _logger.error(f"Error in quick action {action_name}: {e}")
            return {'success': False, 'error': str(e)}

    @http.route('/web/dashboard/app_access', type='json', auth='user')
    def check_app_access(self, app_name, **kw):
        """Check user access untuk aplikasi tertentu"""
        try:
            user = request.env.user

            app_groups = {
                'sale': 'sales_team.group_sale_salesman',
                'purchase': 'purchase.group_purchase_user',
                'stock': 'stock.group_stock_user',
                'account': 'account.group_account_user',
                'mrp': 'mrp.group_mrp_user',
                'hr': 'hr.group_hr_user',
                'crm': 'sales_team.group_sale_salesman',
                'project': 'project.group_project_user',
            }

            if app_name in app_groups:
                group_id = request.env.ref(app_groups[app_name], raise_if_not_found=False)
                if group_id and group_id in user.groups_id:
                    return {'has_access': True}

            return {'has_access': False}

        except Exception as e:
            _logger.error(f"Error checking app access for {app_name}: {e}")
            return {'has_access': True}  # Default allow jika error

    def _get_dashboard_stats(self):
        """Get basic statistics untuk dashboard"""
        try:
            stats = {}

            if self._user_has_group('sales_team.group_sale_salesman'):
                sales_count = request.env['sale.order'].search_count([
                    ('state', 'in', ['draft', 'sent'])
                ])
                stats['pending_sales'] = sales_count

            # Purchase stats
            if self._user_has_group('purchase.group_purchase_user'):
                purchase_count = request.env['purchase.order'].search_count([
                    ('state', 'in', ['draft', 'sent', 'to approve'])
                ])
                stats['pending_purchases'] = purchase_count

            # Inventory stats
            if self._user_has_group('stock.group_stock_user'):
                low_stock_count = request.env['stock.quant'].search_count([
                    ('quantity', '<=', 5),
                    ('location_id.usage', '=', 'internal')
                ])
                stats['low_stock_products'] = low_stock_count

            # Invoice stats
            if self._user_has_group('account.group_account_user'):
                draft_invoices = request.env['account.move'].search_count([
                    ('state', '=', 'draft'),
                    ('move_type', 'in', ['out_invoice', 'in_invoice'])
                ])
                stats['draft_invoices'] = draft_invoices

            return stats

        except Exception as e:
            _logger.error(f"Error getting dashboard stats: {e}")
            return {}

    def _get_recent_activities(self):
        """Get recent activities untuk dashboard"""
        try:
            activities = []

            # Recent sales orders
            recent_sales = request.env['sale.order'].search([
                ('create_date', '>=', request.env['ir.fields'].Datetime.now().strftime('%Y-%m-%d'))
            ], limit=5, order='create_date desc')

            for sale in recent_sales:
                activities.append({
                    'type': 'sale',
                    'title': f'New Sale Order: {sale.name}',
                    'partner': sale.partner_id.name,
                    'amount': sale.amount_total,
                    'date': sale.create_date.strftime('%H:%M'),
                })

            # Recent purchases
            recent_purchases = request.env['purchase.order'].search([
                ('create_date', '>=', request.env['ir.fields'].Datetime.now().strftime('%Y-%m-%d'))
            ], limit=3, order='create_date desc')

            for purchase in recent_purchases:
                activities.append({
                    'type': 'purchase',
                    'title': f'New Purchase Order: {purchase.name}',
                    'partner': purchase.partner_id.name,
                    'amount': purchase.amount_total,
                    'date': purchase.create_date.strftime('%H:%M'),
                })

            return sorted(activities, key=lambda x: x['date'], reverse=True)[:8]

        except Exception as e:
            _logger.error(f"Error getting recent activities: {e}")
            return []

    def _get_user_notifications(self):
        """Get notifications untuk user"""
        try:
            notifications = []

            # Check pending approvals
            if self._user_has_group('purchase.group_purchase_manager'):
                pending_approvals = request.env['purchase.order'].search_count([
                    ('state', '=', 'to approve')
                ])
                if pending_approvals > 0:
                    notifications.append({
                        'type': 'warning',
                        'message': f'{pending_approvals} purchase order(s) need approval',
                        'action': 'purchase.purchase_rfq'
                    })

            # Check overdue invoices
            if self._user_has_group('account.group_account_user'):
                overdue_invoices = request.env['account.move'].search_count([
                    ('state', '=', 'posted'),
                    ('move_type', '=', 'out_invoice'),
                    ('invoice_date_due', '<', request.env['ir.fields'].Date.today()),
                    ('payment_state', '!=', 'paid')
                ])
                if overdue_invoices > 0:
                    notifications.append({
                        'type': 'error',
                        'message': f'{overdue_invoices} overdue invoice(s)',
                        'action': 'account.action_move_out_invoice_type'
                    })

            return notifications

        except Exception as e:
            _logger.error(f"Error getting notifications: {e}")
            return []

    def _user_has_group(self, group_xml_id):
        """Helper method untuk check user group"""
        try:
            group = request.env.ref(group_xml_id, raise_if_not_found=False)
            if group:
                return group in request.env.user.groups_id
            return False
        except:
            return False

    @http.route('/web/dashboard/search', type='json', auth='user')
    def dashboard_search(self, query, **kw):
        """Global search dari dashboard"""
        try:
            if not query or len(query) < 2:
                return {'results': []}

            results = []

            # Search customers
            partners = request.env['res.partner'].search([
                ('name', 'ilike', query),
                ('is_company', '=', True)
            ], limit=5)

            for partner in partners:
                results.append({
                    'type': 'partner',
                    'title': partner.name,
                    'subtitle': 'Customer',
                    'action': f'base.action_partner_form',
                    'res_id': partner.id
                })

            # Search products
            products = request.env['product.product'].search([
                ('name', 'ilike', query)
            ], limit=5)

            for product in products:
                results.append({
                    'type': 'product',
                    'title': product.name,
                    'subtitle': f'Product - {product.default_code or "No Code"}',
                    'action': 'product.product_normal_action_sell',
                    'res_id': product.id
                })

            return {'results': results[:10]}

        except Exception as e:
            _logger.error(f"Error in dashboard search: {e}")
            return {'results': []}