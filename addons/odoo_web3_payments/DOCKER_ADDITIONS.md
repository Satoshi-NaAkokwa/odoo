Docker additions (Codespaces)

Add the following environment variables to your Codespace or Dockerfile; this is illustrative — do not commit secrets.

Example `.devcontainer/devcontainer.json` / Dockerfile additions:

ENV STRIPE_API_KEY=sk_test_your_key_here
ENV STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
ENV WEB3_RPC_URL=https://rpc.ankr.com/eth_goerli

Expose the Odoo port and mount your workspace. Use the repository `odoo-bin` entrypoint in your container start command.
