{
    "name": "Odoo Web3 & Stripe Payments",
    "version": "1.0.0",
    "summary": "Integrate Web3 wallets (web3.py) and Stripe in a single payments add-on",
    "category": "Accounting/Payment",
    "author": "AI Generated",
    "website": "https://example.org",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/cron.xml",
        "views/payment_templates.xml",
        "views/payment_views.xml",
    ],
    "installable": True,
    "application": False,
}
