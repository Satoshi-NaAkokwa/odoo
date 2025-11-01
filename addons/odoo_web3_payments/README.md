# odoo_web3_payments

Small Odoo 17 add-on integrating Web3 wallets (via web3.py) and Stripe payments.

Setup (Codespaces / local dev):

1. Install Python deps (see list below). In Codespaces use the devcontainer environment.

    ```bash
    pip install -r requirements.txt
    ```

2. Important environment variables (example in `.env.example`):

    - STRIPE_API_KEY=sk_test_...
    - STRIPE_WEBHOOK_SECRET=whsec_...
    - WEB3_RPC_URL=https://rpc.ankr.com/eth_goerli
    - WEB3_CHAIN=ethereum
    - WEB3_CONFIRMATIONS=1

3. Start Odoo for development using the repository entrypoint. Example:

    ```bash
    ./odoo-bin -d devdb --addons-path=addons -i odoo_web3_payments
    ```

Notes
- The Web3 service polls JSON-RPC for confirmations — that is suitable for short checks. For production use background workers.
- Stripe service wraps the official stripe package and expects API keys in env vars.
