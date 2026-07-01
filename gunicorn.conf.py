"""Gunicorn configuration.

Render injects the port to listen on via $PORT and requires the process to
bind 0.0.0.0. Gunicorn auto-loads this file from the working directory, so the
app binds to the right address even if the start command omits --bind
(e.g. a dashboard-set start command). Falls back to 8000 for local runs.
"""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
