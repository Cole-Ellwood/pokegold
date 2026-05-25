from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from tools.trace import boss_ai_trace_batch as batch
from tools.trace.boss_ai_trace_batch import (
    ROOT,
    as_int,
    build_command,
    build_pre_choice_replay_command,
    build_state_probe_command,
    command_for_display,
    load_manifest,
    optional_manifest_path,
    rel_or_abs,
    validate_capture,
    validate_capture_ids,
    validate_manifest_hash,
)


def _valid_capture(**overrides) -> dict:
    base = {
        "id": "morty",
        "boss": "morty",
        "status": "FINISHED",
        "out": "audit/boss_ai_trace/morty.txt",
        "notes": "",
    }
    base.update(overrides)
    return base


class RelOrAbsTests(unittest.TestCase):
    def test_absolute_path_returns_unchanged(self) -> None:
        absolute = Path(tempfile.gettempdir()).resolve()
        self.assertEqual(rel_or_abs(str(absolute)), absolute)

    def test_relative_path_is_resolved_against_repo_root(self) -> None:
        self.assertEqual(rel_or_abs("tools/trace/runtime.py"), ROOT / "tools/trace/runtime.py")


class AsIntTests(unittest.TestCase):
    def test_present_positive_int_returned(self) -> None:
        self.assertEqual(as_int({"watch_frames": 600}, "watch_frames", 100), 600)

    def test_missing_key_uses_default(self) -> None:
        self.assertEqual(as_int({}, "watch_frames", 100), 100)

    def test_negative_value_fails(self) -> None:
        stderr_buffer = io.StringIO()
        with redirect_stderr(stderr_buffer):
            with self.assertRaises(SystemExit):
                as_int({"watch_frames": -1}, "watch_frames", 100)
        self.assertIn("watch_frames must be a positive integer", stderr_buffer.getvalue())

    def test_zero_value_fails(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                as_int({"watch_frames": 0}, "watch_frames", 100)

    def test_non_int_string_fails(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                as_int({"watch_frames": "10"}, "watch_frames", 100)


class OptionalManifestPathTests(unittest.TestCase):
    def test_empty_string_returns_none(self) -> None:
        self.assertIsNone(optional_manifest_path({"trace_rom": ""}, "trace_rom"))

    def test_missing_key_returns_none(self) -> None:
        self.assertIsNone(optional_manifest_path({}, "trace_rom"))

    def test_returns_resolved_path_for_relative(self) -> None:
        path = optional_manifest_path({"trace_rom": "pokegold_trace.gbc"}, "trace_rom")
        self.assertEqual(path, ROOT / "pokegold_trace.gbc")

    def test_non_string_value_fails(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                optional_manifest_path({"trace_rom": 5}, "trace_rom")


class ValidateManifestHashTests(unittest.TestCase):
    def test_matching_hash_returns_path(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target = Path(tempdir) / "rom.gbc"
            target.write_bytes(b"hash me")
            expected = batch.sha256_file(target)
            data = {"trace_rom": str(target), "trace_rom_sha256": expected.lower()}
            self.assertEqual(
                validate_manifest_hash(data, "trace_rom", "trace_rom_sha256"),
                target,
            )

    def test_mismatched_hash_fails_with_expected_and_actual(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target = Path(tempdir) / "rom.gbc"
            target.write_bytes(b"hash me")
            data = {"trace_rom": str(target), "trace_rom_sha256": "DEADBEEF" * 8}
            stderr_buffer = io.StringIO()
            with redirect_stderr(stderr_buffer):
                with self.assertRaises(SystemExit):
                    validate_manifest_hash(data, "trace_rom", "trace_rom_sha256")
            err = stderr_buffer.getvalue()
            self.assertIn("hash mismatch", err)
            self.assertIn("expected DEADBEEF" * 1, err)

    def test_missing_file_fails(self) -> None:
        data = {"trace_rom": "no/such/file.gbc"}
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_manifest_hash(data, "trace_rom", "trace_rom_sha256")

    def test_empty_hash_string_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target = Path(tempdir) / "rom.gbc"
            target.write_bytes(b"x")
            data = {"trace_rom": str(target), "trace_rom_sha256": ""}
            self.assertEqual(
                validate_manifest_hash(data, "trace_rom", "trace_rom_sha256"),
                target,
            )

    def test_missing_path_key_returns_none(self) -> None:
        self.assertIsNone(validate_manifest_hash({}, "trace_rom", "trace_rom_sha256"))


class LoadManifestTests(unittest.TestCase):
    def test_valid_manifest_returned_as_dict(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "manifest.json"
            payload = {"captures": [{"id": "morty"}]}
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(load_manifest(path), payload)

    def test_missing_file_fails(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                load_manifest(Path("nope.json"))

    def test_invalid_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "manifest.json"
            path.write_text("{ not json", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    load_manifest(path)

    def test_root_must_be_object(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "manifest.json"
            path.write_text("[]", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    load_manifest(path)

    def test_captures_must_be_list(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "manifest.json"
            path.write_text('{"captures": {}}', encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    load_manifest(path)


class ValidateCaptureTests(unittest.TestCase):
    def test_minimal_valid_capture_passes(self) -> None:
        validate_capture(_valid_capture(), 1)

    def test_missing_required_string_field_fails(self) -> None:
        entry = _valid_capture()
        del entry["notes"]
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture(entry, 1)

    def test_unknown_status_fails(self) -> None:
        entry = _valid_capture(status="HALF_DONE")
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture(entry, 1)

    def test_choice_wait_frames_must_be_nonnegative_int(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture(_valid_capture(choice_wait_frames=-5), 1)
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture(_valid_capture(choice_wait_frames="60"), 1)
        # Zero is valid (e.g., snapshot-only entries).
        validate_capture(_valid_capture(choice_wait_frames=0), 1)

    def test_watch_frames_must_be_positive_int(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture(_valid_capture(watch_frames=0), 1)
        validate_capture(_valid_capture(watch_frames=120), 1)

    def test_preflight_expectation_must_match_id(self) -> None:
        entry = _valid_capture(id="jasmine", preflight={"expect": "morty"})
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture(entry, 1)

    def test_preflight_with_matching_id_passes(self) -> None:
        entry = _valid_capture(id="morty", preflight={"expect": "morty"})
        validate_capture(entry, 1)

    def test_unknown_preflight_expectation_fails(self) -> None:
        entry = _valid_capture(preflight={"expect": "unknown-boss"})
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture(entry, 1)


class ValidateCaptureIdsTests(unittest.TestCase):
    def test_duplicate_id_fails(self) -> None:
        captures = [_valid_capture(id="morty"), _valid_capture(id="morty")]
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture_ids(captures, set())

    def test_only_with_unknown_id_fails_with_available_list(self) -> None:
        captures = [_valid_capture(id="morty"), _valid_capture(id="jasmine")]
        stderr_buffer = io.StringIO()
        with redirect_stderr(stderr_buffer):
            with self.assertRaises(SystemExit):
                validate_capture_ids(captures, {"falkner"})
        err = stderr_buffer.getvalue()
        self.assertIn("unknown capture id(s) for --only: falkner", err)
        self.assertIn("available ids: jasmine, morty", err)

    def test_only_with_known_id_passes(self) -> None:
        captures = [_valid_capture(id="morty"), _valid_capture(id="jasmine")]
        validate_capture_ids(captures, {"morty"})

    def test_non_dict_entry_fails(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                validate_capture_ids(["string-not-dict"], set())


class BuildCommandTests(unittest.TestCase):
    def test_minimal_capture_uses_default_watch_and_poll(self) -> None:
        entry = _valid_capture()
        cmd = build_command(entry, 600, 1, None, None)
        self.assertEqual(cmd[0], sys.executable)
        self.assertIn("--boss", cmd)
        self.assertEqual(cmd[cmd.index("--boss") + 1], "morty")
        self.assertEqual(cmd[cmd.index("--watch-frames") + 1], "600")
        self.assertEqual(cmd[cmd.index("--poll-every") + 1], "1")

    def test_entry_overrides_default_watch_frames(self) -> None:
        entry = _valid_capture(watch_frames=900, poll_every=10)
        cmd = build_command(entry, 600, 1, None, None)
        self.assertEqual(cmd[cmd.index("--watch-frames") + 1], "900")
        self.assertEqual(cmd[cmd.index("--poll-every") + 1], "10")

    def test_snapshot_only_omits_watch_args(self) -> None:
        entry = _valid_capture(snapshot_only=True)
        cmd = build_command(entry, 600, 1, None, None)
        self.assertNotIn("--watch-frames", cmd)
        self.assertNotIn("--poll-every", cmd)

    def test_save_state_appended_when_present(self) -> None:
        entry = _valid_capture(save_state="captures/morty.state")
        cmd = build_command(entry, 600, 1, None, None)
        self.assertIn("--save-state", cmd)
        self.assertEqual(
            cmd[cmd.index("--save-state") + 1],
            str(ROOT / "captures/morty.state"),
        )

    def test_stop_after_first_capture_flag_added_unless_snapshot_only(self) -> None:
        with_flag = build_command(
            _valid_capture(stop_after_first_capture=True), 600, 1, None, None
        )
        self.assertIn("--stop-after-first-capture", with_flag)
        snapshot = build_command(
            _valid_capture(stop_after_first_capture=True, snapshot_only=True),
            600,
            1,
            None,
            None,
        )
        self.assertNotIn("--stop-after-first-capture", snapshot)

    def test_trace_rom_and_symbols_when_passed(self) -> None:
        cmd = build_command(
            _valid_capture(), 600, 1, Path("trace.gbc"), Path("trace.sym")
        )
        self.assertEqual(cmd[cmd.index("--rom") + 1], "trace.gbc")
        self.assertEqual(cmd[cmd.index("--symbols") + 1], "trace.sym")


class BuildPreChoiceReplayCommandTests(unittest.TestCase):
    def test_uses_capture_choice_button_and_wait_frames(self) -> None:
        entry = _valid_capture(
            pre_choice_state="pre.state",
            choice_button="b",
            choice_wait_frames=72,
        )
        cmd = build_pre_choice_replay_command(entry, 600, None, None)
        self.assertEqual(cmd[cmd.index("--button") + 1], "b")
        self.assertEqual(cmd[cmd.index("--watch-frames") + 1], "72")
        self.assertIn("pre-choice replay; ", cmd[cmd.index("--notes") + 1])
        self.assertEqual(
            cmd[cmd.index("--save-state") + 1],
            str(ROOT / "pre.state"),
        )

    def test_falls_back_to_default_button_and_watch_frames(self) -> None:
        entry = _valid_capture(pre_choice_state="pre.state")
        cmd = build_pre_choice_replay_command(entry, 600, None, None)
        self.assertEqual(cmd[cmd.index("--button") + 1], "a")
        self.assertEqual(cmd[cmd.index("--watch-frames") + 1], "600")


class BuildStateProbeCommandTests(unittest.TestCase):
    def test_no_preflight_returns_none(self) -> None:
        self.assertIsNone(
            build_state_probe_command(_valid_capture(), Path("x.state"), None, None)
        )

    def test_known_preflight_emits_expect_flag(self) -> None:
        entry = _valid_capture(id="morty", preflight={"expect": "morty"})
        cmd = build_state_probe_command(entry, Path("x.state"), None, None)
        self.assertIsNotNone(cmd)
        assert cmd is not None
        self.assertIn("--expect-morty", cmd)
        self.assertIn("--strict", cmd)
        self.assertEqual(cmd[cmd.index("--save-state") + 1], "x.state")


class CommandForDisplayTests(unittest.TestCase):
    def test_quotes_args_containing_spaces(self) -> None:
        cmd = ["python", "tools/trace/runtime.py", "C:/a path/file"]
        self.assertEqual(
            command_for_display(cmd),
            'python tools/trace/runtime.py "C:/a path/file"',
        )

    def test_leaves_unspaced_args_bare(self) -> None:
        self.assertEqual(command_for_display(["a", "b", "c"]), "a b c")


if __name__ == "__main__":
    unittest.main()
