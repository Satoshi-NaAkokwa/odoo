# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PaymentTransactionExtended(models.Model):
    """
    Store external payment transaction metadata.

    Fields:
    - chain: blockchain name (ethereum, polygon, etc.)
    - wallet_address: user's wallet
    - tx_hash: blockchain transaction hash
    - stripe_session_id: Stripe session / payment intent id
    - status: draft/processing/confirmed/failed
    - amount: monetary amount
    - currency: currency code
    - metadata: extra JSON/text
    - invoice_id: optional link to `account.move`
    """

    _name = "payment.transaction.extended"
    _description = "External payment transaction (Web3 / Stripe)"

    name = fields.Char(
        string="Reference",
        required=True,
        default='/',
    )
    chain = fields.Char(string="Chain")
    wallet_address = fields.Char(string="Wallet Address")
    tx_hash = fields.Char(string="Transaction Hash")
    stripe_session_id = fields.Char(string="Stripe Session ID")
    status = fields.Selection([
        ("draft", "Draft"),
        ("processing", "Processing"),
        ("confirmed", "Confirmed"),
        ("failed", "Failed"),
    ], string="Status", default="draft", index=True)
    amount = fields.Monetary(string="Amount")
    currency_id = fields.Many2one('res.currency', string='Currency')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    metadata = fields.Text(string="Metadata")
    partner_id = fields.Many2one('res.partner', string='Partner')
    create_date = fields.Datetime(string='Created on', readonly=True)

    @api.model
    def create(self, vals):
        # ensure a currency is set for monetary computations
        if 'currency_id' not in vals:
            company = self.env.company
            vals['currency_id'] = company.currency_id.id if company else False
        # set a sequence-based name if none provided
        if not vals.get('name'):
            try:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'payment.transaction.extended') or '/'
            except Exception:
                vals['name'] = '/'
        return super().create(vals)

    @api.model
    def cron_check_web3_confirmations(self, limit=50):
        """Cron job: check pending web3 transactions and mark them
        confirmed when seen on-chain.

        Uses the Web3Service but schedules work using queue_job if available.
        """
        # defer heavy imports to the worker method to avoid import-time errors

        pending = self.search(
            [('status', '=', 'processing'), ('tx_hash', '!=', False)],
            limit=limit,
        )

        for rec in pending:
            # schedule per-record processing: prefer queue_job if present
            try:
                # if queue_job is installed the model will have `with_delay`
                if hasattr(self, 'with_delay'):
                    rec.with_delay()._process_single_confirmation(rec.id)
                else:
                    # fallback: spawn a short-lived thread
                    import threading

                    thread = threading.Thread(
                        target=self._process_single_confirmation,
                        args=(rec.id,),
                    )
                    thread.daemon = True
                    thread.start()
            except Exception:
                _logger.exception(
                    'Error scheduling confirmation for %s', rec.id,
                )

    def _process_single_confirmation(self, record_id):
        """Process a single record: poll JSON-RPC and update its status.

        This method is intentionally self-contained so it can be called either
        by a queue job or a background thread.
        """
        try:
            from ..services.web3_service import Web3Service
        except Exception:
            _logger.exception('web3_service import failed')
            return

        svc = Web3Service(self.env)
        rec = self.browse(record_id)
        if not rec or not rec.tx_hash:
            return
        try:
            receipt = svc.wait_for_confirmation(rec.tx_hash, timeout=60)
            if receipt:
                rec.sudo().write(
                    {'status': 'confirmed', 'metadata': str(receipt)}
                )
        except Exception:
            _logger.exception('Error while checking tx %s', rec.tx_hash)
