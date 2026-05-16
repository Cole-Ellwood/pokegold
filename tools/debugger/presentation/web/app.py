"""FastAPI application for the debugger web UI.

Serves JSON API endpoints for debugger queries plus Jinja2-rendered
HTML pages for interactive inspection.  No Node.js / npm — pure
Python + HTML templates.

Dependencies: ``pip install fastapi uvicorn jinja2``
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


def create_app(project_root: Path | None = None) -> Any:
    """Create the FastAPI application."""
    if not HAS_FASTAPI:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn jinja2")

    from fastapi import FastAPI

    app = FastAPI(
        title="Pokemon Gold Debugger",
        description="Web UI for the unified debugger",
        version="0.1.0",
    )

    root = project_root or Path(__file__).resolve().parents[4]

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return _render_page("index", {
            "title": "Pokemon Gold Debugger",
            "project_root": str(root),
        })

    @app.get("/api/status")
    async def api_status() -> dict[str, Any]:
        from ...kernel.symbol_service import SymbolService
        try:
            svc = SymbolService.from_project(variant="pokegold", start=root)
            sym_count = svc.count()
        except Exception:
            sym_count = 0

        rom_path = root / "pokegold.gbc"
        return {
            "project_root": str(root),
            "rom_exists": rom_path.exists(),
            "rom_size": rom_path.stat().st_size if rom_path.exists() else 0,
            "symbol_count": sym_count,
        }

    @app.get("/api/symbols/{name}")
    async def api_symbol(name: str) -> dict[str, Any]:
        from ...kernel.symbol_service import SymbolService
        try:
            svc = SymbolService.from_project(variant="pokegold", start=root)
        except FileNotFoundError:
            return {"error": "Symbol files not found"}

        sym = svc.resolve(name)
        if sym is None:
            candidates = svc.prefix_search(name)
            return {"error": f"Symbol '{name}' not found", "candidates": candidates[:10]}
        return {
            "name": sym.name,
            "bank": sym.bank,
            "address": sym.address,
            "bank_hex": f"${sym.bank:02X}",
            "address_hex": f"${sym.address:04X}",
        }

    @app.get("/api/runs")
    async def api_runs() -> dict[str, Any]:
        runs_dir = root / "audit" / "boss_ai_debugger" / "runs"
        runs: list[dict[str, Any]] = []
        if runs_dir.exists():
            for run_dir in sorted(runs_dir.iterdir()):
                meta_path = run_dir / "metadata.json"
                if meta_path.exists():
                    try:
                        meta = json.loads(meta_path.read_text(encoding="utf-8"))
                        runs.append({
                            "name": run_dir.name,
                            "profile": meta.get("profile", ""),
                            "timestamp": meta.get("timestamp", ""),
                        })
                    except (json.JSONDecodeError, OSError):
                        pass
        return {"runs": runs}

    @app.get("/api/runs/{run_name}")
    async def api_run_detail(run_name: str) -> dict[str, Any]:
        run_dir = root / "audit" / "boss_ai_debugger" / "runs" / run_name
        if not run_dir.exists():
            return {"error": f"Run '{run_name}' not found"}

        result: dict[str, Any] = {"name": run_name}
        for fname in ("metadata.json", "summary.json", "review_queue.json"):
            fpath = run_dir / fname
            if fpath.exists():
                try:
                    result[fname.replace(".json", "")] = json.loads(
                        fpath.read_text(encoding="utf-8")
                    )
                except (json.JSONDecodeError, OSError):
                    pass
        return result

    @app.get("/battle", response_class=HTMLResponse)
    async def battle_page() -> str:
        return _render_page("battle", {"title": "Battle Inspector"})

    @app.get("/coverage", response_class=HTMLResponse)
    async def coverage_page() -> str:
        return _render_page("coverage", {"title": "Coverage Report"})

    @app.get("/runs", response_class=HTMLResponse)
    async def runs_page() -> str:
        return _render_page("runs", {"title": "Experiment Runs"})

    return app


def _render_page(name: str, context: dict[str, Any]) -> str:
    """Render a page template (falls back to inline HTML if no template file)."""
    template_path = TEMPLATES_DIR / f"{name}.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
        for key, val in context.items():
            template = template.replace(f"{{{{ {key} }}}}", str(val))
        return template

    title = context.get("title", "Debugger")
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{title} — Pokemon Gold Debugger</title>
    <style>
        body {{ font-family: monospace; margin: 2em; background: #1a1a2e; color: #e0e0e0; }}
        h1 {{ color: #e94560; }}
        a {{ color: #0f3460; }}
        nav {{ margin-bottom: 2em; }}
        nav a {{ color: #16213e; background: #e94560; padding: 0.5em 1em;
                 text-decoration: none; margin-right: 0.5em; }}
        .card {{ background: #16213e; padding: 1em; margin: 1em 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/battle">Battle</a>
        <a href="/coverage">Coverage</a>
        <a href="/runs">Runs</a>
    </nav>
    <h1>{title}</h1>
    <div class="card" id="content">Loading...</div>
    <script>
        fetch('/api/status')
            .then(r => r.json())
            .then(data => {{
                document.getElementById('content').innerHTML =
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            }})
            .catch(e => {{
                document.getElementById('content').textContent = 'API error: ' + e;
            }});
    </script>
</body>
</html>"""


if HAS_FASTAPI:
    app = create_app()
else:
    app = None


def main(port: int = 8765, host: str = "127.0.0.1") -> None:
    """Run the web server."""
    if not HAS_FASTAPI:
        print("FastAPI not installed. Run: pip install fastapi uvicorn jinja2")
        return

    import uvicorn
    uvicorn.run(create_app(), host=host, port=port)


__all__ = ["create_app", "app", "main"]
