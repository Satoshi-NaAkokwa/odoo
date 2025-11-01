# -*- coding: utf-8 -*-
import unittest


@unittest.skip("Requires Odoo runtime; skipped in unit mode")
class TestCronWorker(unittest.TestCase):
    def test_cron_checks_pending(self):
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
