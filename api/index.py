"""WSGI entrypoint for deployment platforms like Vercel."""
from app import app as flask_app

# Vercel expects a module-level variable named ``app`` that exposes the
# WSGI callable. Re-export the Flask application created in ``app.py`` so the
# deployment platform can discover it without any additional configuration.
app = flask_app

__all__ = ["app"]
