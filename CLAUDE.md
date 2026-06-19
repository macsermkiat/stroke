# CLAUDE.md

## What this is
A Flask web app for the Ph.D thesis "Explainable AI and Causal Analysis in Stroke".
It serves stroke-risk models behind a handful of routes (`app.py` is a flat single module):

- `/` (GET) — landing page, renders `index2.html`.
- `/TAN` (GET/POST) — TAN Bayesian network risk estimate via pysmile.
- `/BN` (GET/POST) — full Bayesian network risk estimate via pysmile.
- `/logreg` (GET/POST) — Logistic Regression + EBM + XGBoost predictions (`logreg.py`).
- `/ite` (GET/POST) — DragonNet causal ITE estimates (`ite.py` / `Dragon.py`).

Templates are the `*2.html` variants under `templates/`.

## Run / test
- Install: `pip install -r requirements.txt` (use a venv).
- Copy `.env.example` → `.env` and set `SMILE_LICENSE` / `SMILE_KEY`. Never commit `.env`.
- Dev server: `flask --app app run`. Prod-like: `gunicorn app:app` (see `Procfile`).
- Tests: `pytest -q` — no test suite is committed yet.

## Gotchas
- **License loading**: `app.py` calls `load_dotenv()` then reads `SMILE_LICENSE` /
  `SMILE_KEY` from the environment and calls `pysmile.License(...)` at the top of the
  module, before any `pysmile.Network()` is created. There is no hardcoded license.
  Never commit license values; `smile_license/` and `.env` are gitignored.
- **Eager network load**: networks load at import time — `initial_load()` is defined and
  called at module level (it reads `TAN.xdsl` and `Stroke-best-update.xdsl` and caches
  static node data into module globals). This was migrated off the removed
  `@app.before_first_request` API (gone in Flask 2.3/3.x).
- **Pinned deps**: model artifacts (`*.pkl`, `*.h5`, `*.json`, `*.xdsl`) are committed,
  and dependencies are pinned conservatively (TensorFlow 2.15, scikit-learn 1.3) so the
  2021-era pickles/.h5 still load. `runtime.txt` pins Python 3.11.9. Do not bump these
  blindly — newer versions may fail to load the saved artifacts.
- **Shared-singleton concurrency hazard**: `tan_net` / `bn_net` are module-level pysmile
  singletons mutated per request (`clear_all_evidence` / `set_evidence` /
  `update_beliefs`) with no lock today. `--workers 2` gives process isolation (each
  worker its own network copy); avoid many threads per worker, and add a lock if you
  introduce threading.
