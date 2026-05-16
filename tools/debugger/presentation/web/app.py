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

    @app.get("/api/damage")
    async def api_damage(
        level: int = 50, bp: int = 60, move_type: int = 0,
        atk: int = 100, dfn: int = 80, is_physical: bool = True,
    ) -> dict[str, Any]:
        try:
            from tools.damage_debugger.oracle import BattleInputs, predict_damage
            inp = BattleInputs(
                attacker_level=level, move_bp=bp, move_type=move_type,
                is_physical=is_physical, attacker_atk=atk, defender_def=dfn,
                attacker_types=(move_type, move_type),
                defender_types=(0xFF, 0xFF),
            )
            exact = predict_damage(inp)
            return {
                "exact": exact,
                "low": max(1, exact * 217 // 255) if exact > 0 else 0,
                "high": exact,
                "inputs": {"level": level, "bp": bp, "atk": atk, "def": dfn},
            }
        except ImportError:
            return {"error": "damage oracle not available"}

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
    pages = {
        "index": _INDEX_HTML,
        "battle": _BATTLE_HTML,
        "coverage": _COVERAGE_HTML,
        "runs": _RUNS_HTML,
    }
    body = pages.get(name, _INDEX_HTML)
    return _BASE_HTML.format(title=title, body=body)


_BASE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>{title} - Pokemon Gold Debugger</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Consolas', 'Monaco', monospace; background: #0d1117; color: #c9d1d9; }}
        nav {{ background: #161b22; padding: 0.75em 2em; border-bottom: 1px solid #30363d;
               display: flex; gap: 1em; align-items: center; }}
        nav .brand {{ color: #e94560; font-weight: bold; font-size: 1.1em; margin-right: 1em; }}
        nav a {{ color: #58a6ff; text-decoration: none; padding: 0.3em 0.8em; border-radius: 4px; }}
        nav a:hover {{ background: #21262d; }}
        main {{ max-width: 1100px; margin: 2em auto; padding: 0 2em; }}
        h1 {{ color: #e94560; margin-bottom: 1em; font-size: 1.4em; }}
        .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px;
                 padding: 1.2em; margin-bottom: 1em; }}
        .card h2 {{ color: #58a6ff; font-size: 1em; margin-bottom: 0.8em; }}
        .stat {{ display: inline-block; margin-right: 2em; }}
        .stat .label {{ color: #8b949e; font-size: 0.85em; }}
        .stat .value {{ color: #c9d1d9; font-size: 1.3em; font-weight: bold; }}
        .ok {{ color: #3fb950; }} .err {{ color: #f85149; }}
        input {{ background: #0d1117; border: 1px solid #30363d; color: #c9d1d9;
                 padding: 0.5em; border-radius: 4px; width: 300px; font-family: inherit; }}
        button {{ background: #21262d; color: #c9d1d9; border: 1px solid #30363d;
                  padding: 0.5em 1em; border-radius: 4px; cursor: pointer; font-family: inherit; }}
        button:hover {{ background: #30363d; }}
        pre {{ background: #0d1117; padding: 1em; border-radius: 4px; overflow-x: auto;
               border: 1px solid #30363d; font-size: 0.85em; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ text-align: left; padding: 0.5em 1em; border-bottom: 1px solid #21262d; }}
        th {{ color: #8b949e; font-size: 0.85em; }}
        #results {{ margin-top: 1em; }}
    </style>
</head>
<body>
    <nav>
        <span class="brand">PkGold Debug</span>
        <a href="/">Status</a>
        <a href="/battle">Battle</a>
        <a href="/coverage">Coverage</a>
        <a href="/runs">Runs</a>
    </nav>
    <main>
        {body}
    </main>
</body>
</html>"""

_INDEX_HTML = """
<h1>Debugger Status</h1>
<div class="card" id="status">Loading...</div>
<div class="card">
    <h2>Symbol Lookup</h2>
    <input id="sym-input" placeholder="e.g. wBattleMonHP" />
    <button onclick="lookupSymbol()">Resolve</button>
    <div id="sym-result"></div>
</div>
<script>
fetch('/api/status').then(r=>r.json()).then(d=>{
    let h = '';
    h += '<div class="stat"><span class="label">ROM</span><br>'
       + '<span class="value '+(d.rom_exists?'ok':'err')+'">'
       + (d.rom_exists ? (d.rom_size/1024).toFixed(0)+'K' : 'missing')+'</span></div>';
    h += '<div class="stat"><span class="label">Symbols</span><br>'
       + '<span class="value">'+d.symbol_count+'</span></div>';
    h += '<div class="stat"><span class="label">Root</span><br>'
       + '<span class="value" style="font-size:0.8em">'+d.project_root+'</span></div>';
    document.getElementById('status').innerHTML = h;
});
function lookupSymbol() {
    const name = document.getElementById('sym-input').value;
    if (!name) return;
    fetch('/api/symbols/'+encodeURIComponent(name)).then(r=>r.json()).then(d=>{
        if (d.error) {
            let h = '<p class="err">'+d.error+'</p>';
            if (d.candidates) h += '<p>Did you mean: '+d.candidates.join(', ')+'</p>';
            document.getElementById('sym-result').innerHTML = h;
        } else {
            document.getElementById('sym-result').innerHTML =
                '<pre>'+d.name+' = '+d.bank_hex+':'+d.address_hex+'</pre>';
        }
    });
}
document.getElementById('sym-input').addEventListener('keydown', e=>{
    if(e.key==='Enter') lookupSymbol();
});
</script>"""

_BATTLE_HTML = """
<h1>Battle Inspector</h1>
<div class="card">
    <h2>Damage Calculator</h2>
    <p style="color:#8b949e">Use <code>python -m tools.debugger battle damage SPECIES:LV SPECIES:LV MOVE --explain</code> from CLI</p>
</div>
<div class="card">
    <h2>Metamorphic Relations</h2>
    <p style="color:#8b949e">Run <code>python -m tools.debugger metamorphic --count 50</code> to check damage invariants against the oracle</p>
</div>"""

_COVERAGE_HTML = """
<h1>Coverage Report</h1>
<div class="card">
    <h2>Static Analysis</h2>
    <p style="color:#8b949e">Run <code>python -m tools.debugger static analyze</code> for dead code, bank pressure, and clobber inference</p>
</div>"""

_RUNS_HTML = """
<h1>Experiment Runs</h1>
<div class="card" id="runs-list">Loading...</div>
<script>
fetch('/api/runs').then(r=>r.json()).then(d=>{
    if (!d.runs || d.runs.length === 0) {
        document.getElementById('runs-list').innerHTML = '<p style="color:#8b949e">No runs recorded yet.</p>';
        return;
    }
    let h = '<table><tr><th>Run</th><th>Profile</th><th>Time</th></tr>';
    d.runs.forEach(r => {
        h += '<tr><td><a href="/api/runs/'+r.name+'">'+r.name+'</a></td>'
           + '<td>'+r.profile+'</td><td>'+r.timestamp+'</td></tr>';
    });
    h += '</table>';
    document.getElementById('runs-list').innerHTML = h;
});
</script>"""


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
