# Stroke
Ph.D thesis "Explainable AI and Causal Analysis in Stroke"  

Demo MVP version is here
🧠 https://stroke-0l38.onrender.com 🚧

## Run locally
1. `python -m venv .venv && . .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in `SMILE_LICENSE` / `SMILE_KEY`
   (from your BayesFusion academic license — see `smile_license/`).
4. `flask --app app run`  (dev)  or  `gunicorn app:app` (prod-like)

## Environment variables
| Var | Purpose |
|-----|---------|
| `SMILE_LICENSE` | BayesFusion pysmile license text |
| `SMILE_KEY` | pysmile license key bytes (comma-separated hex) |

## Deploy (render.com)
- Build: `pip install -r requirements.txt`
- Start: defined in `Procfile`
- Python version: pinned in `runtime.txt`
- Set `SMILE_LICENSE` and `SMILE_KEY` as **secret** environment variables.
