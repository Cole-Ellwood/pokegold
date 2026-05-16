"""MCP server for the Pokemon Gold hack debugger.

Thin wrappers around the kernel + analysis layers. Launch:
    python -m tools.debugger mcp --stdio    (Claude Code)
    python -m tools.debugger mcp --http     (desktop app, port 7777)

The MCP tools are the *natural* CLI for the kernel + bus. Building them
early means every later phase ships a Claude-usable surface for free.

This is a stub that implements the tool dispatch table. The actual MCP
protocol transport (stdio JSON-RPC or HTTP) will be wired when the
mcp Python package is available. For now, the tools are callable as
a Python API that any CLI or agent can invoke.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]


@dataclass
class ToolResult:
    """Structured result from an MCP tool call."""
    ok: bool
    data: Any = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"ok": self.ok}
        if self.data is not None:
            d["data"] = self.data
        if self.error:
            d["error"] = self.error
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def _get_svc(variant: str = "pokegold"):
    from ..kernel.symbol_service import SymbolService
    return SymbolService.from_project(variant=variant, start=ROOT)


def tool_read_symbol(name: str, variant: str = "pokegold") -> ToolResult:
    """Read a named symbol's value (address + bank)."""
    try:
        svc = _get_svc(variant)
    except FileNotFoundError as e:
        return ToolResult(ok=False, error=str(e))
    sym = svc.resolve(name)
    if sym is None:
        candidates = svc.prefix_search(name)
        return ToolResult(
            ok=False,
            error=f"Symbol '{name}' not found",
            data={"suggestions": [str(c) for c in candidates[:10]]},
        )
    return ToolResult(ok=True, data={
        "name": sym.name,
        "bank": sym.bank,
        "address": sym.address,
        "hex": f"${sym.bank:02x}:{sym.address:04x}",
    })


def tool_query_symbol(prefix: str, variant: str = "pokegold") -> ToolResult:
    """Autocomplete symbol names."""
    try:
        svc = _get_svc(variant)
    except FileNotFoundError as e:
        return ToolResult(ok=False, error=str(e))
    matches = svc.prefix_search(prefix)
    return ToolResult(ok=True, data={
        "matches": [
            {"name": m.name, "bank": m.bank, "address": m.address}
            for m in matches[:50]
        ],
        "total": len(matches),
    })


def tool_lookup_label(bank: int, addr: int, variant: str = "pokegold") -> ToolResult:
    """Reverse symbol lookup: bank:addr -> label name."""
    try:
        svc = _get_svc(variant)
    except FileNotFoundError as e:
        return ToolResult(ok=False, error=str(e))
    label = svc.render(bank, addr)
    return ToolResult(ok=True, data={"label": label, "bank": bank, "address": addr})


def tool_run_audit(name: str) -> ToolResult:
    """Run a specific tools/audit script and return structured output."""
    import subprocess

    audit_dir = ROOT / "tools" / "audit"
    script = audit_dir / f"check_{name}.py"
    if not script.exists():
        script = audit_dir / f"{name}.py"
    if not script.exists():
        available = sorted(s.stem for s in audit_dir.glob("check_*.py"))
        return ToolResult(ok=False, error=f"Audit '{name}' not found", data={
            "available": available,
        })

    try:
        result = subprocess.run(
            ["python", str(script)],
            capture_output=True, text=True, timeout=120,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        return ToolResult(ok=False, error=f"Audit '{name}' timed out (120s)")

    return ToolResult(
        ok=result.returncode == 0,
        data={
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        },
    )


def tool_run_smoke() -> ToolResult:
    """Shortcut to the verification floor (clobber_smoke)."""
    import subprocess

    try:
        result = subprocess.run(
            ["python", "-m", "tools.damage_debugger.clobber_smoke"],
            capture_output=True, text=True, timeout=300,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        return ToolResult(ok=False, error="clobber_smoke timed out (300s)")
    except FileNotFoundError:
        return ToolResult(ok=False, error="Python not found")

    return ToolResult(
        ok=result.returncode == 0,
        data={
            "stdout": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
            "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
            "returncode": result.returncode,
        },
    )


def tool_schema_summary(variant: str = "pokegold") -> ToolResult:
    """Get the WorldState summary."""
    try:
        svc = _get_svc(variant)
    except FileNotFoundError as e:
        return ToolResult(ok=False, error=str(e))

    from ..kernel.state_schema import WorldState
    ws = WorldState.from_symbol_service(svc)
    return ToolResult(ok=True, data={"summary": ws.summary()})


def tool_bank_info(bank: int, memory: str = "ROMX", variant: str = "pokegold") -> ToolResult:
    """Get bank usage info (sections, free space)."""
    try:
        svc = _get_svc(variant)
    except FileNotFoundError as e:
        return ToolResult(ok=False, error=str(e))

    info = svc.bank_info(bank, memory)
    if info is None:
        return ToolResult(ok=False, error=f"No info for {memory} bank {bank}")
    return ToolResult(ok=True, data={
        "memory": info.memory,
        "bank": info.bank_number,
        "total_free": info.total_free,
        "total_used": info.total_used,
        "section_count": len(info.sections),
        "sections": [
            {"name": s.name, "start": s.start, "end": s.end, "size": s.size}
            for s in info.sections
        ],
    })


TOOL_TABLE: dict[str, Any] = {
    "read_symbol": tool_read_symbol,
    "query_symbol": tool_query_symbol,
    "lookup_label": tool_lookup_label,
    "run_audit": tool_run_audit,
    "run_smoke": tool_run_smoke,
    "schema_summary": tool_schema_summary,
    "bank_info": tool_bank_info,
}


def dispatch(tool_name: str, **kwargs: Any) -> ToolResult:
    """Dispatch a tool call by name."""
    fn = TOOL_TABLE.get(tool_name)
    if fn is None:
        return ToolResult(ok=False, error=f"Unknown tool: {tool_name}", data={
            "available": sorted(TOOL_TABLE.keys()),
        })
    try:
        return fn(**kwargs)
    except Exception as e:
        return ToolResult(ok=False, error=f"{type(e).__name__}: {e}")


def list_tools() -> list[dict[str, str]]:
    """List all available MCP tools."""
    return [
        {"name": name, "description": (fn.__doc__ or "").strip().split("\n")[0]}
        for name, fn in sorted(TOOL_TABLE.items())
    ]


def _handle_jsonrpc(request: dict[str, Any]) -> dict[str, Any]:
    """Handle one JSON-RPC 2.0 request and return a response."""
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "pokemon-gold-debugger", "version": "0.1.0"},
            },
        }

    if method == "notifications/initialized":
        return {}

    if method == "tools/list":
        tools = []
        for name, fn in sorted(TOOL_TABLE.items()):
            doc = (fn.__doc__ or "").strip().split("\n")[0]
            tools.append({
                "name": name,
                "description": doc,
                "inputSchema": {"type": "object", "properties": {}},
            })
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        result = dispatch(tool_name, **tool_args)
        content = [{"type": "text", "text": result.to_json()}]
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"content": content, "isError": not result.ok},
        }

    return {
        "jsonrpc": "2.0", "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def run_stdio() -> None:
    """Run the MCP server over stdin/stdout with Content-Length framing."""
    import sys

    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        content_length = -1
        while True:
            line = stdin.readline()
            if not line:
                return
            header = line.decode("utf-8", errors="replace").strip()
            if not header:
                break
            if header.lower().startswith("content-length:"):
                content_length = int(header.split(":", 1)[1].strip())

        if content_length < 0:
            continue

        body = stdin.read(content_length)
        if len(body) < content_length:
            return

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            continue

        response = _handle_jsonrpc(request)
        if not response:
            continue

        payload = json.dumps(response).encode("utf-8")
        stdout.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("utf-8"))
        stdout.write(payload)
        stdout.flush()
