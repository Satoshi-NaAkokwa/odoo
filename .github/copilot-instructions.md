## Copilot / AI agent quick instructions for Odoo

This file gives concise, actionable guidance to AI coding agents working in this repository. Focus on small, verifiable changes and follow the project's module patterns.

- Repo layout (big picture):
  - `odoo/` — the core Python package (server, ORM, CLI). The entrypoint is `odoo-bin` at the repo root which calls `odoo.cli.main()`.
  - `addons/` — hundreds of individual modules. Each module is a self-contained app with a manifest (`__manifest__.py`), `models/`, `controllers/`, `views/`, `data/`, and `tests/` where applicable.
  - `setup.py` and `requirements.txt` — declare runtime dependencies and Python compatibility (project targets Python >= 3.10).

- Architecture & patterns to respect:
  - Odoo is a single-process Python web application using its own ORM. Business logic belongs in `models/*` as `class X(models.Model)`, controllers in `controllers/*`, and UI/layout in XML `views/*` and QWeb templates.
  - Modules interoperate through the ORM and recordsets; prefer using recordset APIs (`self.env['model.name'].search(...)`, `record.write(...)`) instead of raw SQL unless there is a clear perf reason.
  - Static assets, translations and data files are declared in the manifest and loaded at module install/update time.

- Common developer workflows (what to run locally):
  - Start the server (dev):
    - Use the repo `odoo-bin` entrypoint. Example: `./odoo-bin -d testdb --addons-path=addons -i my_module` (this repo provides `odoo-bin` which calls into `odoo.cli`).
    - You can pass a config file with `-c <config>` and typical flags like `-d <dbname>`, `-i <module>`, `--addons-path`.
  - Install dependencies: follow `requirements.txt` or use `pip install -r requirements.txt` inside the appropriate virtualenv/container.
  - Tests: module tests live under `addons/<module>/tests`. Run them by targeting the package, for example `python -m unittest discover addons/<module>/tests` or run `pytest` if the environment has pytest configured. Start with small, module-level tests.

- Project-specific conventions and examples:
  - Module structure: `addons/<module>/models/*.py` for business code, `controllers/*.py` for HTTP endpoints, `views/*.xml` for form/tree/search views, and `security/ir.model.access.csv` for access rules.
  - Naming: models use dotted names (`module.model`) and classes inherit from `odoo.models.Model`.
  - Data loading: example manifests declare `data: ['data/some.xml', 'security/ir.model.access.csv']` — modify manifests when adding schema/data files.

- Integration points & external dependencies:
  - Many payment, google, ldap, and third-party integrations exist under `addons/` (e.g., `payment_*`, `google_*`). Follow existing connector patterns: a lightweight controller + model + external client wrapper.
  - Database: Odoo uses PostgreSQL. Connection and DB management are handled by the server — do not add alternate DB backends.

- PR & code change guidance for AI edits:
  - Small, self-contained: prefer one-module changes. Update the module `__manifest__.py` when adding files that must be installed/loaded.
  - Avoid touching core `odoo/` internals unless the change requires it; prefer adding or extending behavior in `addons/` modules.
  - Respect access control: when adding record operations, update `security/ir.model.access.csv` and check existing access rules.
  - Include or update tests in `addons/<module>/tests` covering the new behavior (happy path + at least one edge case).

- Useful files to inspect for patterns:
  - `odoo-bin` — CLI entrypoint
  - `setup.py`, `requirements.txt` — dependency and Python targets
  - Any representative module, e.g. `addons/sale/`, `addons/account/`, `addons/payment_*/` (look at `models/`, `controllers/`, `views/`, `tests/`).

If anything here is unclear or you want the instructions to be more prescriptive (e.g., exact test command, recommended linters, or CI hooks to target), tell me which area and I'll refine the file.
