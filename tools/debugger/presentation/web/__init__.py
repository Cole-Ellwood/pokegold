"""Web UI: FastAPI backend + Jinja2 templates.

Provides browser-based inspection of debugger state: decision
waterfalls, battle visualizer, run comparison, coverage reports.

Start: ``python -m tools.debugger web --port 8765``
"""

__all__ = ["app", "create_app"]

from .app import app, create_app
