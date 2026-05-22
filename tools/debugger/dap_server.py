#!/usr/bin/env python3
"""Minimal Debug Adapter Protocol server (P14).

`debugger dap --port 4711` exposes a small DAP-shaped surface so Claude
and Codex (and VS Code, and any DAP client) can drive the debugger
through a normalized JSON protocol instead of re-inventing per-session
glue. Current slices ship Content-Length framing, initialize, launch,
configurationDone, setBreakpoints (recorded as unverified), threads,
synthetic stackTrace/scopes/variables, evaluate(tdb), and disconnect.
Later slices add live CPU frame state, reverseContinue, pause, and
continue.

Protocol shape grounded in microsoft/debug-adapter-protocol spec
(https://microsoft.github.io/debug-adapter-protocol/specification.html).
"""

from __future__ import annotations

import argparse
import io
import json
import socket
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Callable, Sequence

from .catalog import ROOT


SCHEMA_VERSION = 1
DEFAULT_PORT = 4711
DEFAULT_HOST = "127.0.0.1"

# Per DAP spec: messages framed as "Content-Length: N\r\n\r\n<JSON body>".
# Header section ends with the blank line; body is N bytes of UTF-8 JSON.
HEADER_TERMINATOR = b"\r\n\r\n"
CONTENT_LENGTH_PREFIX = b"Content-Length:"
SYNTHETIC_FRAME_ID = 1
DEBUGGER_SCOPE_VARIABLES_REFERENCE = 1


@dataclass
class DapServer:
    """Stateful DAP server core.

    Designed to be transport-agnostic: ``handle_message`` takes a parsed
    dict and returns a list of response/event dicts. ``serve_stream``
    wraps that in DAP framing and pumps bytes; ``serve_tcp`` wraps it in
    a socket. Pure-handler split keeps tests deterministic.
    """

    _seq: int = 0
    capabilities: dict[str, Any] = field(
        default_factory=lambda: {
            "supportsConfigurationDoneRequest": True,
            "supportsConditionalBreakpoints": False,
            "supportsEvaluateForHovers": True,
            "supportsRestartRequest": False,
            "supportsStepBack": False,
        }
    )
    default_reports: tuple[str, ...] = ()
    breakpoints_by_source: dict[str, tuple[dict[str, Any], ...]] = field(
        default_factory=dict
    )
    root: Path = field(default_factory=lambda: ROOT)

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def handle_message(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        msg_type = message.get("type")
        request_seq, seq_error = _request_seq(message)
        command = str(message.get("command", ""))
        if seq_error:
            return [self._error_response(
                request_seq=0,
                command=command,
                message=seq_error,
            )]
        if msg_type != "request":
            return [self._error_response(
                request_seq=request_seq,
                command=command,
                message=f"unsupported message type: {msg_type!r}",
            )]
        handler = _COMMAND_HANDLERS.get(command)
        if handler is None:
            return [self._error_response(
                request_seq=request_seq,
                command=command,
                message=f"unsupported command: {command!r}",
            )]
        return handler(self, message, request_seq)

    def _response(
        self,
        *,
        request_seq: int,
        command: str,
        success: bool,
        body: dict[str, Any] | None = None,
        message: str = "",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "seq": self._next_seq(),
            "type": "response",
            "request_seq": request_seq,
            "success": success,
            "command": command,
        }
        if body is not None:
            payload["body"] = body
        if message:
            payload["message"] = message
        return payload

    def _error_response(
        self, *, request_seq: int, command: str, message: str
    ) -> dict[str, Any]:
        return self._response(
            request_seq=request_seq,
            command=command,
            success=False,
            message=message,
        )

    def _initialize_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        # initialize handshake: capabilities response + initialized event.
        return [
            self._response(
                request_seq=request_seq,
                command="initialize",
                success=True,
                body=dict(self.capabilities),
            ),
            {
                "seq": self._next_seq(),
                "type": "event",
                "event": "initialized",
            },
        ]

    def _threads_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        # SM83 is single-threaded; one synthetic main thread.
        return [
            self._response(
                request_seq=request_seq,
                command="threads",
                success=True,
                body={"threads": [{"id": 1, "name": "sm83"}]},
            )
        ]

    def _stack_trace_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        args = message.get("arguments")
        if not isinstance(args, dict):
            return [self._error_response(
                request_seq=request_seq,
                command="stackTrace",
                message="stackTrace requires arguments.threadId",
            )]
        thread_id = args.get("threadId")
        if isinstance(thread_id, bool) or thread_id != 1:
            return [self._error_response(
                request_seq=request_seq,
                command="stackTrace",
                message="stackTrace supports only synthetic threadId=1",
            )]
        return [self._response(
            request_seq=request_seq,
            command="stackTrace",
            success=True,
            body={
                "stackFrames": [
                    {
                        "id": SYNTHETIC_FRAME_ID,
                        "name": "sm83 trace-query session",
                        "line": 1,
                        "column": 1,
                    }
                ],
                "totalFrames": 1,
            },
        )]

    def _scopes_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        args = message.get("arguments")
        if not isinstance(args, dict):
            return [self._error_response(
                request_seq=request_seq,
                command="scopes",
                message="scopes requires arguments.frameId",
            )]
        frame_id = args.get("frameId")
        if isinstance(frame_id, bool) or frame_id != SYNTHETIC_FRAME_ID:
            return [self._error_response(
                request_seq=request_seq,
                command="scopes",
                message=f"scopes supports only synthetic frameId={SYNTHETIC_FRAME_ID}",
            )]
        return [self._response(
            request_seq=request_seq,
            command="scopes",
            success=True,
            body={
                "scopes": [
                    {
                        "name": "debugger session",
                        "variablesReference": DEBUGGER_SCOPE_VARIABLES_REFERENCE,
                        "expensive": False,
                    }
                ]
            },
        )]

    def _variables_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        args = message.get("arguments")
        if not isinstance(args, dict):
            return [self._error_response(
                request_seq=request_seq,
                command="variables",
                message="variables requires arguments.variablesReference",
            )]
        variables_reference = args.get("variablesReference")
        if (
            isinstance(variables_reference, bool)
            or variables_reference != DEBUGGER_SCOPE_VARIABLES_REFERENCE
        ):
            return [self._error_response(
                request_seq=request_seq,
                command="variables",
                message=(
                    "variables supports only debugger-session "
                    f"variablesReference={DEBUGGER_SCOPE_VARIABLES_REFERENCE}"
                ),
            )]
        breakpoint_sources = {
            source: breakpoints
            for source, breakpoints in self.breakpoints_by_source.items()
            if breakpoints
        }
        breakpoint_count = sum(
            len(breakpoints) for breakpoints in breakpoint_sources.values()
        )
        return [self._response(
            request_seq=request_seq,
            command="variables",
            success=True,
            body={
                "variables": [
                    {
                        "name": "reports",
                        "value": ", ".join(self.default_reports) or "(none)",
                        "variablesReference": 0,
                    },
                    {
                        "name": "breakpoints",
                        "value": (
                            f"{breakpoint_count} unverified breakpoint(s) "
                            f"across {len(breakpoint_sources)} source(s)"
                        ),
                        "variablesReference": 0,
                    },
                    {
                        "name": "supported_commands",
                        "value": ", ".join(sorted(_COMMAND_HANDLERS)),
                        "variablesReference": 0,
                    },
                    {
                        "name": "runtime_state",
                        "value": "not live; trace-query metadata only",
                        "variablesReference": 0,
                    },
                ]
            },
        )]

    def _launch_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        # Minimal launch handshake. DAP clients can bind trace reports
        # through launch arguments once, then use evaluate(tdb) without
        # repeating custom report paths on every request.
        raw_args = message.get("arguments", {})
        if not isinstance(raw_args, dict):
            return [self._error_response(
                request_seq=request_seq,
                command="launch",
                message="launch arguments must be an object",
            )]
        reports, reports_error = _report_paths_from_arguments(
            raw_args,
            command="launch",
            default_reports=self.default_reports,
        )
        if reports_error:
            return [self._error_response(
                request_seq=request_seq,
                command="launch",
                message=reports_error,
            )]
        self.default_reports = reports
        return [self._response(
            request_seq=request_seq,
            command="launch",
            success=True,
        )]

    def _configuration_done_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        return [self._response(
            request_seq=request_seq,
            command="configurationDone",
            success=True,
        )]

    def _set_breakpoints_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        args = message.get("arguments")
        if not isinstance(args, dict):
            return [self._error_response(
                request_seq=request_seq,
                command="setBreakpoints",
                message="setBreakpoints requires arguments object",
            )]
        source = args.get("source")
        if not isinstance(source, dict):
            return [self._error_response(
                request_seq=request_seq,
                command="setBreakpoints",
                message="setBreakpoints requires arguments.source object",
            )]
        source_key = str(source.get("path") or source.get("name") or "").strip()
        if not source_key:
            return [self._error_response(
                request_seq=request_seq,
                command="setBreakpoints",
                message="setBreakpoints requires source.path or source.name",
            )]
        raw_breakpoints = args.get("breakpoints", [])
        if not isinstance(raw_breakpoints, list):
            return [self._error_response(
                request_seq=request_seq,
                command="setBreakpoints",
                message="setBreakpoints arguments.breakpoints must be a list",
            )]
        response_breakpoints: list[dict[str, Any]] = []
        stored_breakpoints: list[dict[str, Any]] = []
        for raw_breakpoint in raw_breakpoints:
            if not isinstance(raw_breakpoint, dict):
                return [self._error_response(
                    request_seq=request_seq,
                    command="setBreakpoints",
                    message="setBreakpoints breakpoint entries must be objects",
                )]
            line = raw_breakpoint.get("line")
            if isinstance(line, bool) or not isinstance(line, int):
                return [self._error_response(
                    request_seq=request_seq,
                    command="setBreakpoints",
                    message="setBreakpoints breakpoint.line must be an integer",
                )]
            if line <= 0:
                return [self._error_response(
                    request_seq=request_seq,
                    command="setBreakpoints",
                    message="setBreakpoints breakpoint.line must be positive",
                )]
            breakpoint = {
                "verified": False,
                "line": line,
                "message": "source-line breakpoint recorded; PC binding and stop support pending",
            }
            stored_breakpoints.append({
                "source": source_key,
                "line": line,
                "verified": False,
            })
            response_breakpoints.append(breakpoint)
        self.breakpoints_by_source[source_key] = tuple(stored_breakpoints)
        return [self._response(
            request_seq=request_seq,
            command="setBreakpoints",
            success=True,
            body={"breakpoints": response_breakpoints},
        )]

    def _disconnect_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        return [self._response(
            request_seq=request_seq,
            command="disconnect",
            success=True,
        )]

    def _evaluate_response(
        self, message: dict[str, Any], request_seq: int
    ) -> list[dict[str, Any]]:
        # evaluate runs the expression as a tdb query. Report paths can
        # be supplied per request via `arguments.reports` or once at
        # server launch via repeated CLI --report args. The result
        # mirrors the CLI tdb shape: matches[] + canonical + valid + errors.
        from .tdb import run_tdb

        args = message.get("arguments")
        if not isinstance(args, dict):
            return [self._error_response(
                request_seq=request_seq,
                command="evaluate",
                message="evaluate requires arguments.expression",
            )]
        expression = args.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            return [self._error_response(
                request_seq=request_seq,
                command="evaluate",
                message="evaluate requires non-empty string arguments.expression",
            )]
        reports, reports_error = _report_paths_from_arguments(
            args,
            command="evaluate",
            default_reports=self.default_reports,
        )
        if reports_error:
            return [self._error_response(
                request_seq=request_seq,
                command="evaluate",
                message=reports_error,
            )]
        tdb_result = run_tdb(query=expression, reports=reports, root=self.root)
        body = {
            "result": json.dumps(tdb_result, sort_keys=True),
            "variablesReference": 0,
            "tdb": tdb_result,
        }
        return [self._response(
            request_seq=request_seq,
            command="evaluate",
            success=bool(tdb_result.get("valid", False)),
            body=body,
            message="" if tdb_result.get("valid") else "tdb query failed; see body.tdb.errors",
        )]


_COMMAND_HANDLERS: dict[
    str, Callable[[DapServer, dict[str, Any], int], list[dict[str, Any]]]
] = {
    "initialize": DapServer._initialize_response,
    "launch": DapServer._launch_response,
    "configurationDone": DapServer._configuration_done_response,
    "setBreakpoints": DapServer._set_breakpoints_response,
    "threads": DapServer._threads_response,
    "stackTrace": DapServer._stack_trace_response,
    "scopes": DapServer._scopes_response,
    "variables": DapServer._variables_response,
    "evaluate": DapServer._evaluate_response,
    "disconnect": DapServer._disconnect_response,
}


def _request_seq(message: dict[str, Any]) -> tuple[int, str]:
    raw = message.get("seq", 0)
    if isinstance(raw, bool) or not isinstance(raw, int):
        return 0, f"invalid request seq: {raw!r}"
    return raw, ""


def _report_paths_from_arguments(
    args: dict[str, Any],
    *,
    command: str,
    default_reports: tuple[str, ...],
) -> tuple[tuple[str, ...], str]:
    raw_reports = args.get("reports")
    if raw_reports is None:
        return default_reports, ""
    if isinstance(raw_reports, list) and all(
        isinstance(item, str) for item in raw_reports
    ):
        return tuple(raw_reports), ""
    return (), f"{command} arguments.reports must be a list of strings"


def encode_frame(payload: dict[str, Any]) -> bytes:
    """Serialize a DAP message with Content-Length framing."""
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def read_frame(stream: BinaryIO) -> dict[str, Any] | None:
    """Read one DAP-framed message from a binary stream.

    Returns the parsed body dict, or None on EOF. Raises ValueError on
    a malformed header or body.
    """
    header = b""
    while HEADER_TERMINATOR not in header:
        chunk = stream.read(1)
        if not chunk:
            return None
        header += chunk
    header_text, _, _ = header.partition(HEADER_TERMINATOR)
    content_length: int | None = None
    for line in header_text.split(b"\r\n"):
        if line.startswith(CONTENT_LENGTH_PREFIX):
            try:
                content_length = int(line[len(CONTENT_LENGTH_PREFIX):].strip())
            except ValueError as exc:
                raise ValueError(f"malformed Content-Length: {line!r}") from exc
            break
    if content_length is None:
        raise ValueError(f"missing Content-Length header in: {header_text!r}")
    body = b""
    while len(body) < content_length:
        chunk = stream.read(content_length - len(body))
        if not chunk:
            raise ValueError("stream closed mid-body")
        body += chunk
    try:
        decoded = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON body: {exc.msg}") from exc
    if not isinstance(decoded, dict):
        raise ValueError("DAP body must be a JSON object")
    return decoded


def serve_stream(
    server: DapServer,
    in_stream: BinaryIO,
    out_stream: BinaryIO,
) -> None:
    """Pump DAP frames between two binary streams until EOF."""
    while True:
        try:
            message = read_frame(in_stream)
        except ValueError as exc:
            sys.stderr.write(f"dap_server: read error: {exc}\n")
            return
        if message is None:
            return
        for response in server.handle_message(message):
            out_stream.write(encode_frame(response))
            out_stream.flush()


def serve_tcp(
    server: DapServer,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    once: bool = False,
    on_listen: Callable[[int], None] | None = None,
) -> None:
    """Run the DAP server over TCP.

    ``once=True`` accepts a single client then returns (used by tests).
    ``on_listen`` is called with the actual bound port after listen().
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(1)
        bound_port = sock.getsockname()[1]
        if on_listen is not None:
            on_listen(bound_port)
        while True:
            client, _addr = sock.accept()
            try:
                with client.makefile("rwb", buffering=0) as stream:
                    serve_stream(server, stream, stream)
            finally:
                client.close()
            if once:
                return


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.dap_server",
        description=(
            "Minimal Debug Adapter Protocol server (P14). Current slices "
            "ship initialize, launch, configurationDone, setBreakpoints, threads, "
            "synthetic stackTrace/scopes/variables, evaluate(tdb), and disconnect; "
            "later slices add live CPU frame state/reverseContinue."
        ),
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"TCP port (default {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--host", type=str, default=DEFAULT_HOST, help=f"TCP host (default {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="serve over stdin/stdout instead of TCP",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="(TCP only) accept a single client then exit",
    )
    parser.add_argument(
        "--report",
        action="append",
        default=[],
        help="effect-trace report path available to evaluate(tdb); repeatable",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    server = DapServer(default_reports=tuple(args.report))
    if args.stdio:
        serve_stream(server, sys.stdin.buffer, sys.stdout.buffer)
        return 0
    serve_tcp(server, host=args.host, port=args.port, once=args.once)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
