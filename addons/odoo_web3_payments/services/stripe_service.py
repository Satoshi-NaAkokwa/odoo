# -*- coding: utf-8 -*-
"""Stripe service wrapper.

Environment variables used:
- STRIPE_API_KEY
- STRIPE_WEBHOOK_SECRET

This class is a lightweight wrapper around the `stripe` package.
"""

import os
import logging

_logger = logging.getLogger(__name__)


class StripeService:
    def __init__(self, env):
        self.env = env
        try:
            import stripe
        except Exception:  # pragma: no cover - import errors surfaced in tests
            stripe = None
        self.stripe = stripe
        self.api_key = os.environ.get('STRIPE_API_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        if self.stripe and self.api_key:
            self.stripe.api_key = self.api_key

    def create_checkout_session(
        self,
        amount_cents,
        currency='usd',
        success_url=None,
        cancel_url=None,
        metadata=None,
    ):
        """Create a Stripe Checkout Session for a one-off payment.

        amount_cents: integer amount in cents
        currency: currency code
        """
        if not self.stripe:
            raise RuntimeError('stripe package not available')
        if not self.api_key:
            raise RuntimeError('STRIPE_API_KEY not configured')

        session = self.stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {'name': 'Odoo Payment'},
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url or 'https://example.org/success',
            cancel_url=cancel_url or 'https://example.org/cancel',
            metadata=metadata or {},
        )
        return session

    def construct_event(self, payload, sig_header):
        """Verify webhook signature and return the Stripe event.

        Raises an exception if verification fails.
        """
        if not self.stripe:
            raise RuntimeError('stripe package not available')
        if self.webhook_secret:
            return self.stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        # If no webhook secret, rely on raw payload (less safe)
        return self.stripe.Event.construct_from(payload, self.stripe.api_key)
