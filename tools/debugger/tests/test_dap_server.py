from __future__ import annotations

import io
import json
import socket
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.debugger.dap_server import (
    DEFAULT_HOST,
    DapServer,
    encode_frame,
    main,
    read_frame,
    serve_stream,
    serve_tcp,
)


def _client_initialize_message(seq: int = 1) -> dict:
    return {
        "seq": seq,
        "type": "request",
        "command": "initialize",
        "arguments": {"clientID": "test-client", "adapterID": "pokegold"},
    }


def _trace_fixture(tmp_path) -> str:
    from pathlib import Path as _Path

    report = {
        "schema_version": 1,
        "kind": "unified_debugger_effect_trace",
        "valid": True,
        "events": [
            {
                "seq": 4,
                "pc_bank_address": "01:5A00",
                "pc_label": "BattleCommand_DamageCalc+6",
                "bank_state": {"wram": 1},
                "bank_state_sources": {"wram": "bank_state.wram"},
                "effects": [
                    {
                        "access": "write",
                        "kind": "memory_write",
                        "address_hex": "D141",
                        "address_key": "wramx:01:D141",
                        "value_hex": "2A",
                        "bank": 1,
                        "space": "wramx",
                    }
                ],
            }
        ],
    }
    path = _Path(tmp_path) / "effect.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return str(path)


class DapFramingTests(unittest.TestCase):
    def test_encode_then_read_round_trip(self) -> None:
        payload = {"seq": 1, "type": "request", "command": "initialize"}
        frame = encode_frame(payload)

        self.assertIn(b"Content-Length:", frame)
        body_start = frame.index(b"\r\n\r\n") + 4
        header = frame[:body_start - 4].decode("ascii")
        body = frame[body_start:]
        self.assertEqual(int(header.split(":")[1].strip()), len(body))

        parsed = read_frame(io.BytesIO(frame))
        self.assertEqual(parsed, payload)

    def test_read_frame_returns_none_on_eof(self) -> None:
        self.assertIsNone(read_frame(io.BytesIO(b"")))

    def test_read_frame_rejects_missing_content_length(self) -> None:
        with self.assertRaises(ValueError):
            read_frame(io.BytesIO(b"X-Other: 1\r\n\r\n{}"))

    def test_read_frame_rejects_truncated_body(self) -> None:
        with self.assertRaises(ValueError):
            read_frame(io.BytesIO(b"Content-Length: 100\r\n\r\n{}"))

    def test_read_frame_rejects_non_object_json_body(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON object"):
            read_frame(io.BytesIO(b"Content-Length: 2\r\n\r\n[]"))

    def test_serve_stream_handles_non_object_body_without_crashing(self) -> None:
        in_stream = io.BytesIO(b"Content-Length: 2\r\n\r\n[]")
        out_stream = io.BytesIO()
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            serve_stream(DapServer(), in_stream, out_stream)

        self.assertEqual(out_stream.getvalue(), b"")
        self.assertIn("DAP body must be a JSON object", stderr.getvalue())


class DapServerHandshakeTests(unittest.TestCase):
    def test_initialize_returns_capabilities_response_and_initialized_event(self) -> None:
        server = DapServer()
        responses = server.handle_message(_client_initialize_message(seq=7))

        self.assertEqual(len(responses), 2)
        response, event = responses
        self.assertEqual(response["type"], "response")
        self.assertEqual(response["command"], "initialize")
        self.assertEqual(response["request_seq"], 7)
        self.assertTrue(response["success"])
        self.assertIn("supportsConfigurationDoneRequest", response["body"])
        self.assertTrue(response["body"]["supportsConfigurationDoneRequest"])

        self.assertEqual(event["type"], "event")
        self.assertEqual(event["event"], "initialized")

    def test_unknown_command_returns_error_response(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 1,
            "type": "request",
            "command": "doesNotExist",
        })

        self.assertEqual(len(responses), 1)
        self.assertFalse(responses[0]["success"])
        self.assertEqual(responses[0]["request_seq"], 1)
        self.assertIn("unsupported command", responses[0]["message"])

    def test_non_request_message_type_returns_error(self) -> None:
        server = DapServer()
        responses = server.handle_message({"seq": 1, "type": "event"})

        self.assertEqual(len(responses), 1)
        self.assertFalse(responses[0]["success"])
        self.assertIn("unsupported message type", responses[0]["message"])

    def test_non_integer_seq_returns_error_response(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": "not-int",
            "type": "request",
            "command": "initialize",
        })

        self.assertEqual(len(responses), 1)
        self.assertFalse(responses[0]["success"])
        self.assertEqual(responses[0]["request_seq"], 0)
        self.assertIn("invalid request seq", responses[0]["message"])

    def test_boolean_seq_returns_error_response(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": True,
            "type": "request",
            "command": "initialize",
        })

        self.assertEqual(len(responses), 1)
        self.assertFalse(responses[0]["success"])
        self.assertEqual(responses[0]["request_seq"], 0)
        self.assertIn("invalid request seq", responses[0]["message"])

    def test_float_seq_returns_error_response(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 1.5,
            "type": "request",
            "command": "initialize",
        })

        self.assertEqual(len(responses), 1)
        self.assertFalse(responses[0]["success"])
        self.assertEqual(responses[0]["request_seq"], 0)
        self.assertIn("invalid request seq", responses[0]["message"])

    def test_seq_increments_across_responses(self) -> None:
        server = DapServer()
        first = server.handle_message(_client_initialize_message(seq=1))
        second = server.handle_message(_client_initialize_message(seq=2))

        first_seqs = [m["seq"] for m in first]
        second_seqs = [m["seq"] for m in second]
        self.assertEqual(first_seqs, [1, 2])
        self.assertEqual(second_seqs, [3, 4])


class DapServerThreadsTests(unittest.TestCase):
    def test_threads_returns_single_sm83_thread(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 5,
            "type": "request",
            "command": "threads",
        })

        self.assertEqual(len(responses), 1)
        body = responses[0]["body"]
        self.assertEqual(len(body["threads"]), 1)
        self.assertEqual(body["threads"][0]["name"], "sm83")
        self.assertEqual(body["threads"][0]["id"], 1)


class DapServerLaunchTests(unittest.TestCase):
    def test_launch_binds_default_reports_for_evaluate(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            _trace_fixture(tmp)
            server = DapServer(root=Path(tmp))
            launch = server.handle_message({
                "seq": 2,
                "type": "request",
                "command": "launch",
                "arguments": {"reports": ["effect.json"]},
            })
            evaluate = server.handle_message({
                "seq": 3,
                "type": "request",
                "command": "evaluate",
                "arguments": {"expression": "writes(addr=$D141)"},
            })

        self.assertTrue(launch[0]["success"])
        self.assertEqual(server.default_reports, ("effect.json",))
        self.assertTrue(evaluate[0]["success"], evaluate)
        matches = evaluate[0]["body"]["tdb"].get("matches", [])
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get("address_hex"), "D141")

    def test_launch_rejects_non_object_arguments(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 2,
            "type": "request",
            "command": "launch",
            "arguments": [],
        })

        self.assertFalse(responses[0]["success"])
        self.assertIn("arguments must be an object", responses[0]["message"])

    def test_launch_rejects_non_string_report_entries(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 2,
            "type": "request",
            "command": "launch",
            "arguments": {"reports": ["effect.json", 7]},
        })

        self.assertFalse(responses[0]["success"])
        self.assertIn("reports must be a list of strings", responses[0]["message"])


class DapServerDisconnectTests(unittest.TestCase):
    def test_disconnect_returns_success_response(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 6,
            "type": "request",
            "command": "disconnect",
        })

        self.assertEqual(len(responses), 1)
        self.assertTrue(responses[0]["success"])
        self.assertEqual(responses[0]["command"], "disconnect")
        self.assertEqual(responses[0]["request_seq"], 6)


class DapServerConfigurationDoneTests(unittest.TestCase):
    def test_configuration_done_returns_success_response(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 7,
            "type": "request",
            "command": "configurationDone",
        })

        self.assertEqual(len(responses), 1)
        self.assertTrue(responses[0]["success"])
        self.assertEqual(responses[0]["command"], "configurationDone")
        self.assertEqual(responses[0]["request_seq"], 7)


class DapServerSetBreakpointsTests(unittest.TestCase):
    def test_set_breakpoints_records_unverified_source_lines(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 8,
            "type": "request",
            "command": "setBreakpoints",
            "arguments": {
                "source": {"path": "engine/battle/effect_commands.asm"},
                "breakpoints": [{"line": 120}, {"line": 124}],
            },
        })

        self.assertEqual(len(responses), 1)
        response = responses[0]
        self.assertTrue(response["success"], response)
        breakpoints = response["body"]["breakpoints"]
        self.assertEqual([item["line"] for item in breakpoints], [120, 124])
        self.assertEqual([item["verified"] for item in breakpoints], [False, False])
        self.assertIn("PC binding", breakpoints[0]["message"])
        self.assertEqual(
            server.breakpoints_by_source["engine/battle/effect_commands.asm"],
            (
                {
                    "source": "engine/battle/effect_commands.asm",
                    "line": 120,
                    "verified": False,
                },
                {
                    "source": "engine/battle/effect_commands.asm",
                    "line": 124,
                    "verified": False,
                },
            ),
        )

    def test_set_breakpoints_replaces_existing_breakpoints_for_source(self) -> None:
        server = DapServer()
        first = {
            "seq": 8,
            "type": "request",
            "command": "setBreakpoints",
            "arguments": {
                "source": {"path": "engine/battle/effect_commands.asm"},
                "breakpoints": [{"line": 120}],
            },
        }
        second = {
            "seq": 9,
            "type": "request",
            "command": "setBreakpoints",
            "arguments": {
                "source": {"path": "engine/battle/effect_commands.asm"},
                "breakpoints": [],
            },
        }

        self.assertTrue(server.handle_message(first)[0]["success"])
        response = server.handle_message(second)[0]

        self.assertTrue(response["success"], response)
        self.assertEqual(response["body"]["breakpoints"], [])
        self.assertEqual(server.breakpoints_by_source["engine/battle/effect_commands.asm"], ())

    def test_set_breakpoints_rejects_missing_source(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 8,
            "type": "request",
            "command": "setBreakpoints",
            "arguments": {"breakpoints": [{"line": 120}]},
        })

        self.assertFalse(responses[0]["success"])
        self.assertIn("source object", responses[0]["message"])

    def test_set_breakpoints_rejects_non_integer_line(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 8,
            "type": "request",
            "command": "setBreakpoints",
            "arguments": {
                "source": {"path": "engine/battle/effect_commands.asm"},
                "breakpoints": [{"line": True}],
            },
        })

        self.assertFalse(responses[0]["success"])
        self.assertIn("breakpoint.line must be an integer", responses[0]["message"])


class DapServerEvaluateTests(unittest.TestCase):
    def _trace_fixture(self, tmp_path) -> str:
        return _trace_fixture(tmp_path)

    def test_evaluate_requires_arguments(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 1,
            "type": "request",
            "command": "evaluate",
        })
        self.assertFalse(responses[0]["success"])
        self.assertIn("arguments.expression", responses[0]["message"])

    def test_evaluate_requires_non_empty_expression(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 1,
            "type": "request",
            "command": "evaluate",
            "arguments": {"expression": "  "},
        })
        self.assertFalse(responses[0]["success"])

    def test_evaluate_rejects_non_list_reports(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 1,
            "type": "request",
            "command": "evaluate",
            "arguments": {
                "expression": "writes(addr=$D141)",
                "reports": "effect.json",
            },
        })

        self.assertFalse(responses[0]["success"])
        self.assertIn("reports must be a list of strings", responses[0]["message"])

    def test_evaluate_rejects_non_string_report_entries(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 1,
            "type": "request",
            "command": "evaluate",
            "arguments": {
                "expression": "writes(addr=$D141)",
                "reports": ["effect.json", {"path": "other.json"}],
            },
        })

        self.assertFalse(responses[0]["success"])
        self.assertIn("reports must be a list of strings", responses[0]["message"])

    def test_evaluate_runs_tdb_query_against_supplied_report(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._trace_fixture(tmp)
            server = DapServer()
            server.root = type(server.root)(tmp)
            responses = server.handle_message({
                "seq": 9,
                "type": "request",
                "command": "evaluate",
                "arguments": {
                    "expression": "writes(addr=$D141)",
                    "reports": ["effect.json"],
                },
            })

        self.assertEqual(len(responses), 1)
        response = responses[0]
        self.assertTrue(response["success"], response)
        tdb_payload = response["body"]["tdb"]
        self.assertTrue(tdb_payload.get("valid"))
        matches = tdb_payload.get("matches", [])
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get("address_hex"), "D141")

    def test_evaluate_uses_default_reports_when_request_omits_reports(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._trace_fixture(tmp)
            server = DapServer(default_reports=("effect.json",))
            server.root = type(server.root)(tmp)
            responses = server.handle_message({
                "seq": 9,
                "type": "request",
                "command": "evaluate",
                "arguments": {"expression": "writes(addr=$D141)"},
            })

        response = responses[0]
        self.assertTrue(response["success"], response)
        matches = response["body"]["tdb"].get("matches", [])
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].get("address_hex"), "D141")

    def test_evaluate_returns_tdb_errors_with_success_false(self) -> None:
        server = DapServer()
        responses = server.handle_message({
            "seq": 9,
            "type": "request",
            "command": "evaluate",
            "arguments": {"expression": "writes(addr=$D141)"},
        })
        # No reports supplied -> tdb returns valid=False with an errors list.
        response = responses[0]
        self.assertFalse(response["success"])
        self.assertIn("tdb query failed", response["message"])


class DapServerTcpTests(unittest.TestCase):
    def test_initialize_handshake_round_trip_over_tcp(self) -> None:
        server = DapServer()
        bound_port: list[int] = []
        ready = threading.Event()

        def _record_port(port: int) -> None:
            bound_port.append(port)
            ready.set()

        thread = threading.Thread(
            target=serve_tcp,
            kwargs={
                "server": server,
                "host": DEFAULT_HOST,
                "port": 0,
                "once": True,
                "on_listen": _record_port,
            },
            daemon=True,
        )
        thread.start()
        self.assertTrue(ready.wait(timeout=2.0))
        port = bound_port[0]

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((DEFAULT_HOST, port))
            with client.makefile("rwb", buffering=0) as stream:
                stream.write(encode_frame(_client_initialize_message(seq=42)))
                stream.flush()
                response = read_frame(stream)
                event = read_frame(stream)

        thread.join(timeout=2.0)
        self.assertIsNotNone(response)
        self.assertEqual(response["command"], "initialize")
        self.assertTrue(response["success"])
        self.assertEqual(response["request_seq"], 42)
        self.assertEqual(event["event"], "initialized")


class DapServerCliTests(unittest.TestCase):
    def test_help_describes_current_evaluate_surface(self) -> None:
        stdout = io.StringIO()

        with self.assertRaises(SystemExit) as caught:
            with redirect_stdout(stdout):
                main(["--help"])

        self.assertEqual(caught.exception.code, 0)
        text = stdout.getvalue()
        self.assertIn("evaluate(tdb)", text)
        self.assertIn("Current slices", text)
        self.assertNotIn("scopes/evaluate(tdb)/reverseContinue", text)

    def test_stdio_cli_passes_default_reports_to_server(self) -> None:
        with patch("tools.debugger.dap_server.serve_stream") as serve_stream_mock:
            code = main(["--stdio", "--report", "effect.json", "--report", "other.json"])

        self.assertEqual(code, 0)
        server = serve_stream_mock.call_args.args[0]
        self.assertEqual(server.default_reports, ("effect.json", "other.json"))


if __name__ == "__main__":
    unittest.main()
