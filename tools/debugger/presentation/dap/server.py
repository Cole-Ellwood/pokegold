"""DAP server: stdio JSON-RPC transport + SM83 debug session.

Implements the subset of the Debug Adapter Protocol needed for
breakpoint/step/watch on RGBDS-assembled Game Boy ROMs.  The server
speaks stdio (one JSON message per line, Content-Length framed).

This is a pure-Python implementation — no debug adapter SDK dependency.
"""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...kernel.symbol_service import SymbolService


@dataclass
class Breakpoint:
    id: int
    source_file: str
    line: int
    verified: bool = False
    bank: int = 0
    address: int = 0
    condition: str = ""

    def to_dap(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "verified": self.verified,
            "source": {"path": self.source_file},
            "line": self.line,
        }


@dataclass
class WatchExpression:
    id: int
    expression: str
    value: str = ""
    type: str = "byte"

    def to_dap(self) -> dict[str, Any]:
        return {
            "name": self.expression,
            "value": self.value,
            "type": self.type,
            "variablesReference": 0,
        }


@dataclass
class StackFrame:
    id: int
    name: str
    source_file: str
    line: int
    bank: int = 0
    pc: int = 0

    def to_dap(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "line": self.line,
            "column": 0,
        }
        if self.source_file:
            result["source"] = {
                "name": Path(self.source_file).name,
                "path": self.source_file,
            }
        return result


class DapSession:
    """Single debug session state."""

    def __init__(self) -> None:
        self.breakpoints: dict[int, Breakpoint] = {}
        self.watches: dict[int, WatchExpression] = {}
        self.frames: list[StackFrame] = []
        self._next_bp_id = 1
        self._next_watch_id = 1
        self._next_frame_id = 1
        self.stopped = False
        self.stop_reason = ""
        self.rom_path: str = ""
        self.variant: str = "pokegold"
        self._symbol_service: SymbolService | None = None
        self._source_map: dict[tuple[str, int], tuple[int, int]] = {}
        self._addr_to_source: dict[tuple[int, int], tuple[str, int]] = {}
        self.pc: int = 0x0100
        self.bank: int = 0
        self.registers: dict[str, int] = {
            "A": 0, "B": 0, "C": 0, "D": 0, "E": 0,
            "H": 0, "L": 0, "F": 0, "SP": 0xFFFE, "PC": 0x0100,
        }

    def add_breakpoint(self, source_file: str, line: int, condition: str = "") -> Breakpoint:
        bp = Breakpoint(
            id=self._next_bp_id,
            source_file=source_file,
            line=line,
            condition=condition,
        )
        self._next_bp_id += 1

        resolved = self._source_map.get((source_file, line))
        if resolved:
            bp.bank, bp.address = resolved
            bp.verified = True

        self.breakpoints[bp.id] = bp
        return bp

    def remove_breakpoint(self, bp_id: int) -> bool:
        return self.breakpoints.pop(bp_id, None) is not None

    def add_watch(self, expression: str) -> WatchExpression:
        watch = WatchExpression(id=self._next_watch_id, expression=expression)
        self._next_watch_id += 1
        self.watches[watch.id] = watch
        return watch

    def evaluate_watch(self, watch: WatchExpression, wram: bytes | None = None) -> str:
        """Evaluate a watch expression against current state."""
        if self._symbol_service is None:
            return "<no symbols>"

        sym = self._symbol_service.resolve(watch.expression)
        if sym is None:
            return "<unknown symbol>"

        if wram is not None:
            offset = sym.address - 0xC000
            if 0 <= offset < len(wram):
                val = wram[offset]
                watch.value = f"${val:02X} ({val})"
                return watch.value

        watch.value = f"${sym.bank:02X}:${sym.address:04X}"
        return watch.value

    def build_source_map(self, project_root: Path) -> int:
        """Build source-file:line → bank:addr map from .sym + .map files."""
        if self._symbol_service is None:
            return 0

        count = 0
        for entry in self._symbol_service.all_entries():
            source_info = self._symbol_service.source_for(entry.bank, entry.address)
            if source_info:
                src_file, src_line = source_info
                key = (str(project_root / src_file), src_line)
                self._source_map[key] = (entry.bank, entry.address)
                self._addr_to_source[(entry.bank, entry.address)] = (
                    str(project_root / src_file),
                    src_line,
                )
                count += 1
        return count

    def get_stack_frames(self) -> list[StackFrame]:
        source = self._addr_to_source.get((self.bank, self.pc))
        top = StackFrame(
            id=self._next_frame_id,
            name=self._symbol_service.render(self.bank, self.pc) if self._symbol_service else f"${self.bank:02X}:${self.pc:04X}",
            source_file=source[0] if source else "",
            line=source[1] if source else 0,
            bank=self.bank,
            pc=self.pc,
        )
        self._next_frame_id += 1
        return [top]

    def step(self) -> None:
        self.pc += 1
        self.registers["PC"] = self.pc

    def step_back(self) -> None:
        if self.pc > 0:
            self.pc -= 1
            self.registers["PC"] = self.pc

    def continue_run(self) -> None:
        self.stopped = False


class DapServer:
    """DAP JSON-RPC server over stdio."""

    def __init__(self, session: DapSession | None = None) -> None:
        self.session = session or DapSession()
        self._seq = 1
        self._running = False
        self._handlers: dict[str, Any] = {
            "initialize": self._handle_initialize,
            "launch": self._handle_launch,
            "setBreakpoints": self._handle_set_breakpoints,
            "configurationDone": self._handle_configuration_done,
            "threads": self._handle_threads,
            "stackTrace": self._handle_stack_trace,
            "scopes": self._handle_scopes,
            "variables": self._handle_variables,
            "continue": self._handle_continue,
            "next": self._handle_next,
            "stepIn": self._handle_step_in,
            "stepOut": self._handle_step_out,
            "stepBack": self._handle_step_back,
            "evaluate": self._handle_evaluate,
            "disconnect": self._handle_disconnect,
        }

    def _send(self, msg: dict[str, Any]) -> None:
        msg["seq"] = self._seq
        self._seq += 1
        body = json.dumps(msg)
        header = f"Content-Length: {len(body)}\r\n\r\n"
        sys.stdout.write(header + body)
        sys.stdout.flush()

    def _respond(self, request: dict[str, Any], body: dict[str, Any] | None = None, success: bool = True) -> None:
        resp: dict[str, Any] = {
            "type": "response",
            "request_seq": request.get("seq", 0),
            "success": success,
            "command": request.get("command", ""),
        }
        if body:
            resp["body"] = body
        self._send(resp)

    def _event(self, event: str, body: dict[str, Any] | None = None) -> None:
        msg: dict[str, Any] = {"type": "event", "event": event}
        if body:
            msg["body"] = body
        self._send(msg)

    def _handle_initialize(self, request: dict[str, Any]) -> None:
        self._respond(request, {
            "supportsConfigurationDoneRequest": True,
            "supportsStepBack": True,
            "supportsEvaluateForHovers": True,
            "supportTerminateDebuggee": True,
        })
        self._event("initialized")

    def _handle_launch(self, request: dict[str, Any]) -> None:
        args = request.get("arguments", {})
        self.session.rom_path = args.get("program", "")
        self.session.variant = args.get("variant", "pokegold")
        self._respond(request)
        self._event("stopped", {"reason": "entry", "threadId": 1})

    def _handle_set_breakpoints(self, request: dict[str, Any]) -> None:
        args = request.get("arguments", {})
        source = args.get("source", {})
        source_path = source.get("path", "")
        bp_args = args.get("breakpoints", [])

        old_ids = [bp.id for bp in self.session.breakpoints.values()
                   if bp.source_file == source_path]
        for bid in old_ids:
            self.session.remove_breakpoint(bid)

        result_bps = []
        for bp_arg in bp_args:
            bp = self.session.add_breakpoint(
                source_path,
                bp_arg.get("line", 0),
                bp_arg.get("condition", ""),
            )
            result_bps.append(bp.to_dap())

        self._respond(request, {"breakpoints": result_bps})

    def _handle_configuration_done(self, request: dict[str, Any]) -> None:
        self._respond(request)

    def _handle_threads(self, request: dict[str, Any]) -> None:
        self._respond(request, {
            "threads": [{"id": 1, "name": "SM83 CPU"}],
        })

    def _handle_stack_trace(self, request: dict[str, Any]) -> None:
        frames = self.session.get_stack_frames()
        self._respond(request, {
            "stackFrames": [f.to_dap() for f in frames],
            "totalFrames": len(frames),
        })

    def _handle_scopes(self, request: dict[str, Any]) -> None:
        self._respond(request, {
            "scopes": [
                {"name": "Registers", "variablesReference": 1, "expensive": False},
                {"name": "WRAM", "variablesReference": 2, "expensive": True},
                {"name": "HRAM", "variablesReference": 3, "expensive": False},
            ],
        })

    def _handle_variables(self, request: dict[str, Any]) -> None:
        ref = request.get("arguments", {}).get("variablesReference", 0)
        variables = []
        if ref == 1:
            for name, val in self.session.registers.items():
                variables.append({
                    "name": name,
                    "value": f"${val:04X}" if name in ("SP", "PC") else f"${val:02X}",
                    "variablesReference": 0,
                })
        self._respond(request, {"variables": variables})

    def _handle_continue(self, request: dict[str, Any]) -> None:
        self.session.continue_run()
        self._respond(request, {"allThreadsContinued": True})

    def _handle_next(self, request: dict[str, Any]) -> None:
        self.session.step()
        self._respond(request)
        self._event("stopped", {"reason": "step", "threadId": 1})

    def _handle_step_in(self, request: dict[str, Any]) -> None:
        self.session.step()
        self._respond(request)
        self._event("stopped", {"reason": "step", "threadId": 1})

    def _handle_step_out(self, request: dict[str, Any]) -> None:
        self.session.step()
        self._respond(request)
        self._event("stopped", {"reason": "step", "threadId": 1})

    def _handle_step_back(self, request: dict[str, Any]) -> None:
        self.session.step_back()
        self._respond(request)
        self._event("stopped", {"reason": "step", "threadId": 1})

    def _handle_evaluate(self, request: dict[str, Any]) -> None:
        expr = request.get("arguments", {}).get("expression", "")
        watch = self.session.add_watch(expr)
        value = self.session.evaluate_watch(watch)
        self._respond(request, {
            "result": value,
            "variablesReference": 0,
        })

    def _handle_disconnect(self, request: dict[str, Any]) -> None:
        self._respond(request)
        self._running = False

    def handle_message(self, msg: dict[str, Any]) -> None:
        command = msg.get("command", "")
        handler = self._handlers.get(command)
        if handler:
            handler(msg)
        else:
            self._respond(msg, success=False)

    def run_stdio(self) -> None:
        """Main loop: read Content-Length framed JSON from stdin."""
        self._running = True
        while self._running:
            try:
                header = ""
                while True:
                    line = sys.stdin.readline()
                    if not line:
                        self._running = False
                        return
                    header += line
                    if header.endswith("\r\n\r\n"):
                        break

                content_length = 0
                for h_line in header.strip().split("\r\n"):
                    if h_line.startswith("Content-Length:"):
                        content_length = int(h_line.split(":")[1].strip())

                if content_length > 0:
                    body = sys.stdin.read(content_length)
                    msg = json.loads(body)
                    self.handle_message(msg)
            except (json.JSONDecodeError, ValueError, OSError):
                continue


def main() -> None:
    server = DapServer()
    server.run_stdio()


__all__ = ["DapServer", "DapSession", "Breakpoint", "WatchExpression", "StackFrame"]

if __name__ == "__main__":
    main()
