"""Unit tests for services.

These tests import service modules directly from file paths to avoid
importing the full Odoo package during unit runs.
"""

import unittest


from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SERVICES_DIR = BASE / 'services'

def _load_module(name, path):
    spec = spec_from_file_location(name, str(path))
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


class TestServices(unittest.TestCase):
    def test_stripe_service_missing_pkg(self):
        """
        StripeService should raise if stripe package is missing or API key
        is unset.
        """
        stripe_mod = _load_module(
            'stripe_service', SERVICES_DIR / 'stripe_service.py'
        )

        svc = stripe_mod.StripeService(env=None)
        with self.assertRaises(RuntimeError):
            svc.create_checkout_session(100)

    def test_web3_service_polling(self):
        """Web3Service should return a receipt after polling with mocks."""
        web3_mod = _load_module(
            'web3_service', SERVICES_DIR / 'web3_service.py'
        )
        # Patch Web3 inside the module
        class DummyWeb3:
            class Eth:
                def __init__(self):
                    self.block_number = 101
                    self.get_transaction_receipt = (
                        lambda _tx: type('R', (), {'blockNumber': 100})()
                    )

            def __init__(self, *_args, **_kwargs):
                self.eth = DummyWeb3.Eth()

            @staticmethod
            def HTTPProvider(_rpc):
                return None

            @staticmethod
            def is_connected():
                return True

        web3_mod.Web3 = DummyWeb3
        svc = web3_mod.Web3Service(env=None)
        receipt = svc.wait_for_confirmation('0xdeadbeef', timeout=5)
        self.assertIsNotNone(receipt)


if __name__ == '__main__':
    unittest.main()
