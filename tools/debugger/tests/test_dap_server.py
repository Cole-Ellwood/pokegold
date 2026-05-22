from __future__ import annotations

import io
import json
import socket
import threading
import unittest

from tools.debugger.dap_server import (
    DEFAULT_HOST,
    DapServer,
    encode_frame,
    read_frame,
    serve_tcp,
)


def _client_initialize_message(seq: int = 1) -> dict:
    return {
        "seq": seq,
        "type": "request",
        "command": "initialize",
        "arguments": {"clientID": "test-client", "adapterID": "pokegold"},
    }


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

    def test_seq_increments_across_responses(self) -> None:
        server = DapServer()
        first = server.handle_message(_client_initialize_message(seq=1))
        second = server.handle_message(_client_initialize_message(seq=2))

        first_seqs = [m["seq"] for m in first]
        second_seqs = [m["seq"] for m in second]
        self.assertEqual(first_seqs, [1, 2])
        self.assertEqual(second_seqs, [3, 4])


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


if __name__ == "__main__":
    unittest.main()
