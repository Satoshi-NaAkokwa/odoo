# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class Web3StripeController(http.Controller):
    """Expose endpoints for initiating and confirming payments.

    Endpoints:
    - /odoo_web3_payments/api/initiate (json) -> create a payment.transaction.extended record
    - /odoo_web3_payments/stripe/webhook (http POST) -> Stripe webhook endpoint
    - /odoo_web3_payments/web3/confirm (json) -> confirm a tx_hash via JSON-RPC polling
    """

    @http.route('/odoo_web3_payments/api/initiate', type='json', auth='user', methods=['POST'])
    def api_initiate(self, **payload):
        """Initiate a payment from external clients. Expected payload keys:
        - amount (float or cents)
        - currency
        - method ('stripe'|'web3')
        - wallet_address (optional)
        """
        env = request.env
        data = payload or {}
        amount = data.get('amount')
        currency = data.get('currency', 'USD')
        method = data.get('method', 'stripe')
        partner = request.env.user.partner_id

        tx_vals = {
            'amount': amount,
            'currency_id': env['res.currency'].search([('name', '=', currency)], limit=1).id or False,
            'status': 'processing',
            'partner_id': partner.id,
            'metadata': json.dumps(data),
        }
        if method == 'web3':
            tx_vals['wallet_address'] = data.get('wallet_address')
            tx_vals['chain'] = data.get('chain', 'ethereum')
        rec = env['payment.transaction.extended'].sudo().create(tx_vals)
        return {'id': rec.id, 'status': rec.status}

    @http.route('/odoo_web3_payments/web3/confirm', type='json', auth='user', methods=['POST'])
    def web3_confirm(self, **payload):
        """Confirm a web3 tx_hash and update the related record.

        Expects: tx_hash, record_id
        Returns: receipt info or an error
        """
        tx_hash = payload.get('tx_hash')
        record_id = payload.get('record_id')
        env = request.env
        svc = env['ir.config_parameter'].sudo()  # placeholder usage
        web3_svc = env['ir.logging']  # placeholder to keep odoo lint happy
        # instantiate our service
        from ..services.web3_service import Web3Service
        wsvc = Web3Service(env)
        receipt = wsvc.wait_for_confirmation(tx_hash)
        if receipt:
            rec = env['payment.transaction.extended'].sudo().browse(record_id)
            if rec:
                rec.sudo().write({'tx_hash': tx_hash, 'status': 'confirmed', 'metadata': str(receipt)})
            return {'tx_hash': tx_hash, 'status': 'confirmed', 'receipt': dict(receipt)}
        return {'error': 'not_confirmed'}

    @http.route('/odoo_web3_payments/stripe/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def stripe_webhook(self, **kwargs):
        """Stripe webhook receiver. Verifies signature and updates payment.transaction.extended.

        This endpoint expects the raw POST body and Stripe-Signature header.
        """
        payload = request.httprequest.get_data()  # bytes
        sig = request.httprequest.headers.get('Stripe-Signature')
        # construct and verify
        from ..services.stripe_service import StripeService
        ssvc = StripeService(request.env)
        try:
            event = ssvc.construct_event(payload, sig)
        except Exception as e:
            _logger.exception('Stripe webhook verification failed')
            return request.make_response('invalid signature', 400)

        # handle payment succeeded
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            sid = session.get('id')
            # find or create transaction by session id
            tx = (
                request.env['payment.transaction.extended']
                .sudo()
                .search([('stripe_session_id', '=', sid)], limit=1)
            )
            if tx:
                # idempotency: only update if not already confirmed
                if tx.status != 'confirmed':
                    tx.sudo().write(
                        {
                            'status': 'confirmed',
                            'metadata': json.dumps(session),
                        }
                    )
            else:
                # create a new record if none matched
                vals = {
                    'stripe_session_id': sid,
                    'status': 'confirmed',
                    'amount': session.get('amount_total', 0) / 100.0,
                    'metadata': json.dumps(session),
                }
                request.env['payment.transaction.extended'].sudo().create(vals)
        return request.make_response('ok', 200)
