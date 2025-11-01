# -*- coding: utf-8 -*-
"""Web3 service wrapper using web3.py.

This service provides simple helpers for sending and confirming transactions via a JSON-RPC
endpoint. Configuration is read from environment variables:

- WEB3_RPC_URL: HTTP provider URL
- WEB3_CHAIN: friendly chain name (e.g., ethereum, polygon)
- WEB3_CONFIRMATIONS: number of confirmations to wait for (default 1)

The service is intentionally thin: heavy-lifting (gas, signing) should be done by wallet clients.
"""

import os
import logging

# Lazy-import web3 to avoid side effects during unit tests where the full Odoo
# repo is on sys.path (which can shadow stdlib modules like `calendar`).
# Tests can inject a dummy `Web3` at the module level before instantiating the service.
Web3 = None  # type: ignore[assignment]


class _TransactionNotFound(Exception):
    pass


TransactionNotFound = _TransactionNotFound

_logger = logging.getLogger(__name__)


class Web3Service:
    """Thin wrapper around web3.py provider operations used by controllers/services.

    Usage:
        svc = Web3Service(env)
        receipt = svc.wait_for_confirmation(tx_hash)
    """

    def __init__(self, env):
        self.env = env
        rpc = os.environ.get('WEB3_RPC_URL', 'https://rpc.ankr.com/eth_goerli')
        self.chain = os.environ.get('WEB3_CHAIN', 'ethereum')
        self.confirmations = int(os.environ.get('WEB3_CONFIRMATIONS', '1'))
        # Resolve Web3 lazily to allow tests to inject a stub without importing
        # the heavy web3.py dependency (which pulls in importlib/email and can
        # conflict with our repo layout during unit runs).
        global Web3, TransactionNotFound
        if Web3 is None:
            try:
                from web3 import Web3 as _Web3  # type: ignore
                from web3.exceptions import TransactionNotFound as _TNF  # type: ignore
                Web3 = _Web3
                TransactionNotFound = _TNF  # type: ignore
            except Exception as exc:  # pragma: no cover - exercised in integration
                raise RuntimeError("web3.py not available: %s" % exc) from exc

        self.w3 = Web3(Web3.HTTPProvider(rpc))  # type: ignore[misc]

    def is_connected(self):
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def get_block_number(self):
        return self.w3.eth.block_number

    def get_tx_receipt(self, tx_hash):
        try:
            return self.w3.eth.get_transaction_receipt(tx_hash)
        except TransactionNotFound:
            return None

    def wait_for_confirmation(self, tx_hash, timeout=120):
        """Poll for transaction receipt with retry/backoff.

        This method uses a simple exponential backoff between polls.
        It is suitable for short confirmation checks. For production use a
        proper background job or queue worker.
        """
        import time

        start = time.time()
        attempt = 0
        while time.time() - start < timeout:
            attempt += 1
            receipt = self.get_tx_receipt(tx_hash)
            if receipt:
                # receipt.blockNumber might be None for pending
                if receipt.blockNumber is None:
                    sleep_for = min(2 ** attempt, 10)
                    time.sleep(sleep_for)
                    continue
                current = self.get_block_number()
                confirmations = max(0, current - receipt.blockNumber + 1)
                _logger.info("TX %s confirmations=%s", tx_hash, confirmations)
                if confirmations >= self.confirmations:
                    return receipt
            # exponential backoff with cap
            sleep_for = min(2 ** attempt, 10)
            time.sleep(sleep_for)
        return None
