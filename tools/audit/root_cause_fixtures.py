"""Evaluator-side historical ROM exports, without fix history or audit answers.

Exports are new directories, never worktree resets. Keep commit and evaluator
metadata outside the diagnostic input: a commit hash permits looking up the fix.
The input's source manifest contains only paths and content hashes.
This controls the files supplied to a benchmark; it is not an OS sandbox.
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


ROM_DIRECTORIES = frozenset({
    "audio", "constants", "data", "engine", "gfx", "home", "macros", "maps", "ram",
})
BUILD_FILES = frozenset({
    "Makefile", ".rgbds-version", "layout.link", "tools/Makefile",
    "tools/gbcpal.c", "tools/gfx.c", "tools/make_patch.c",
    "tools/png_dimensions.c", "tools/scan_includes.c", "tools/stadium.c",
    "tools/common.h", "tools/concat_files.py", "tools/strip_nulls.py",
    "tools/rm_files.py", "tools/copy_file.py",
})


def export_revision(root: Path, revision: str, destination: Path) -> dict:
    """Export only tracked build inputs from a resolved revision to a new path.

    Refuse an existing destination before any write. Resolve and read the archive
    before creating it, so an invalid revision leaves no partial fixture behind.
    Dirty files, .git, docs, regression audits, and debugger answer tables are
    excluded. Build with ``branch_currency_banner=``: old Makefiles' currency
    warning is intentionally inapplicable to a pinned historical fixture.
    """
    if destination.exists():
        raise FileExistsError(destination)
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}"],
        cwd=root, text=True, stderr=subprocess.PIPE,
    ).strip()
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "-z", commit], cwd=root,
    ).decode("utf-8").split("\0")
    selected = [name for name in paths if name and (
        PurePosixPath(name).parts[0] in ROM_DIRECTORIES
        or name in BUILD_FILES
        or (len(PurePosixPath(name).parts) == 1 and name.endswith(".asm"))
        or name.startswith("tools/lz/") and name.endswith((".c", ".h"))
    )]
    if not selected:
        raise ValueError("revision contains no ROM build inputs")
    # Collapse assets into directory pathspecs to stay below Windows' command-line
    # limit; only explicitly selected files are extracted from the archive.
    archive_paths = sorted({
        PurePosixPath(name).parts[0]
        if PurePosixPath(name).parts[0] in ROM_DIRECTORIES else name
        for name in selected
    })
    data = subprocess.check_output(
        ["git", "archive", "--format=zip", commit, "--", *archive_paths], cwd=root,
    )
    digest = hashlib.sha256()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        payloads = [(name, archive.read(name)) for name in sorted(selected)]
    destination.mkdir(parents=True)
    for name, payload in payloads:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(payload).digest())
    identity = {
        "source_commit": commit,
        "source_tree_sha256": digest.hexdigest().upper(),
        "exported_file_count": len(payloads),
        "source_files": {name: hashlib.sha256(payload).hexdigest().upper() for name, payload in payloads},
    }
    (destination / "source_manifest.json").write_text(json.dumps(
        {key: identity[key] for key in ("source_files", "source_tree_sha256")}, indent=2), encoding="utf-8")
    return identity


def verify_export(root: Path, identity: dict) -> bool:
    """Recheck evaluator-owned source hashes before trusting source locations."""
    files = identity.get("source_files")
    if not isinstance(files, dict) or not files:
        return False
    digest = hashlib.sha256()
    for name, expected in sorted(files.items()):
        try:
            actual = hashlib.sha256((root / name).read_bytes())
        except OSError:
            return False
        if actual.hexdigest().upper() != expected:
            return False
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(actual.digest())
    return digest.hexdigest().upper() == identity.get("source_tree_sha256")


def capture_grass_regrowth(root: Path, destination: Path) -> dict:
    """Capture the confirmed max-HP-54 development regression before execution.

    Reuse the existing ROM audit's between-turns state setup. Only the state and
    input schedule go into destination; the returned observation belongs to the
    evaluator and must not be supplied as a diagnosis or a hidden-cause hint.
    This is a staged routine fixture, not proof of fresh-game reachability.
    """
    if destination.exists():
        raise FileExistsError(destination)
    for name in ("pokegold.gbc", "pokegold.sym"):
        if not (root / name).is_file():
            raise FileNotFoundError(root / name)

    import importlib.metadata
    import json

    from tools.audit.check_grass_regrowth_rom import GRASS, run_case
    from tools.damage_debugger.emulator import DebugSession
    from tools.damage_debugger.safe_call import write_byte_banked
    from tools.debugger.report_envelope import sha256_file
    from tools.trace.runtime import load_pyboy

    # Use the trace backend before DebugSession imports PyBoy. Otherwise one
    # process can seed with a global install that a later trace process cannot
    # load because tools.trace prefers the repo's .local/pydeps installation.
    PyBoy = load_pyboy("PyBoy is required to capture the regression fixture")
    backend_file = Path(sys.modules[PyBoy.__module__].__file__)
    backend_version = next((dist.version for dist in importlib.metadata.distributions(
        path=[str(backend_file.parent.parent)],
    ) if dist.metadata["Name"].lower() == "pyboy"), "unversioned")
    destination.mkdir(parents=True)
    state = destination / "initial.state"

    class CapturingPyBoy:
        def __init__(self, pyboy, entry):
            self.pyboy, self.entry, self.saved = pyboy, entry, False

        def __getattr__(self, name):
            return getattr(self.pyboy, name)

        def tick(self, *args, **kwargs):
            if not self.saved and int(self.pyboy.register_file.PC) == self.entry:
                with state.open("wb") as handle:
                    self.pyboy.save_state(handle)
                self.saved = True
            return self.pyboy.tick(*args, **kwargs)

    class FixtureSession:
        @classmethod
        def open(cls, _variant):
            session = DebugSession.open(str(root.resolve() / "pokegold"))
            entry = session.symbols["HandleTypePassiveRegrowth_Far"].address
            session.pyboy = CapturingPyBoy(session.pyboy, entry)
            return session

    result = run_case(FixtureSession, write_byte_banked, GRASS, GRASS, 54)
    if isinstance(result, str) or not state.is_file():
        raise RuntimeError(f"regression fixture could not be captured: {result}")
    schedule = destination / "inputs.json"
    schedule.write_text(json.dumps({"frames": 30, "buttons": []}) + "\n", encoding="utf-8")
    return {
        "rom_sha256": sha256_file(root / "pokegold.gbc"),
        "symbols_sha256": sha256_file(root / "pokegold.sym"),
        "backend": f"PyBoy {backend_version}",
        "backend_sha256": sha256_file(backend_file),
        "state_basis": {
            "initial_state_sha256": sha256_file(state),
            "input_log_sha256": sha256_file(schedule),
            "rng": {"basis": "captured in initial state"},
        },
        "materialized": True,
        "expected_heal": 2,
        "observed_heal": result[0],
        "observed_type_contribution_at_use": result[1],
        "heal_observed": result[2],
        "known_limits": [
            "Synthetic between-turns state, not fresh-game navigation.",
            "Development case with known cause; not a blind acceptance result.",
        ],
    }


def capture_mail_removal(root: Path, destination: Path) -> dict:
    """Capture the historical party-mail removal call with distinct SRAM records.

    This evaluator-side fixture starts at the real caller's slot load, after menu
    confirmation and bag transfer. It does not establish navigation or bag behavior.
    Only state and inputs are exported; observations and locations stay with the
    evaluator. The caller and callee execute their own unmodified ROM instructions.
    """
    if destination.exists():
        raise FileExistsError(destination)
    for name in ("pokegold.gbc", "pokegold.sym"):
        if not (root / name).is_file():
            raise FileNotFoundError(root / name)

    import json
    from tools.damage_debugger.emulator import DebugSession
    from tools.damage_debugger.safe_call import write_byte_banked
    from tools.damage_debugger.symbols import SymbolTable
    from tools.debugger.report_envelope import replay_state_basis, sha256_file
    from tools.trace.runtime import load_pyboy

    symbols = SymbolTable.load(root / "pokegold.sym")
    start, end = symbols["MonMailAction.RemoveMailToBag"], symbols["MonMailAction.BagIsFull"]
    callee, current = symbols["ClearPartyMonMail"], symbols["wCurPartyMon"]
    rom = (root / "pokegold.gbc").read_bytes()
    offset = start.bank * 0x4000 + (start.address & 0x3FFF)
    code = rom[offset:offset + end.address - start.address]
    load = bytes([0xFA, current.address & 255, current.address >> 8])
    farcall = bytes([0x3E, callee.bank, 0x21, callee.address & 255, callee.address >> 8, 0xCF])
    matches = [(index, index + len(load) + len(transfer) + len(farcall))
               for index in range(len(code)) for transfer in (b"", b"\x5F")
               if code[index:].startswith(load + transfer + farcall)]
    if start.bank != end.bank or len(matches) != 1:
        raise ValueError("one observed caller slot-load/farcall sequence is required")
    entry, continuation = (start.address + value for value in matches[0])
    PyBoy = load_pyboy("PyBoy is required to capture the mail regression fixture")
    backend_file = Path(sys.modules[PyBoy.__module__].__file__)
    state_bytes = io.BytesIO()
    with DebugSession.open(str(root.resolve() / "pokegold")) as session:
        pb = session.pyboy
        pb.tick(600, False, False)
        party, mailbox = symbols["sPartyMail"], symbols["sMailboxes"]
        count = symbols["sMailboxCount"]
        for symbol, length in ((party, 6 * 47), (mailbox, 10 * 47)):
            for index in range(length):
                pb.memory[symbol.bank, symbol.address + index] = 1 + index % 254
        pb.memory[count.bank, count.address] = 10
        write_byte_banked(pb, current.address, 2, current.bank)
        pb.memory[0x2000] = start.bank
        pb.memory[symbols["hROMBank"].address] = start.bank
        pb.register_file.SP = 0xDFFF
        pb.register_file.PC = entry

        def snapshot():
            return {name: bytes(pb.memory[symbol.bank, symbol.address + index] for index in range(length)).hex().upper()
                    for name, symbol, length in (("party", party, 6 * 47), ("mailbox", mailbox, 10 * 47))}

        before = snapshot()
        pb.save_state(state_bytes)  # Save before installing the observation hook.
        observed = []
        pb.hook_register(start.bank, continuation, lambda _context: observed.append(snapshot()), None)
        try:
            pb.tick(1, False, False)
        finally:
            pb.hook_deregister(start.bank, continuation)
        if len(observed) != 1:
            raise RuntimeError("mail-removal call did not return exactly once in the recorded frame")
    destination.mkdir(parents=True)
    state = destination / "initial.state"
    state.write_bytes(state_bytes.getvalue())
    schedule = destination / "inputs.json"
    schedule.write_text(json.dumps({"frames": 1, "buttons": []}) + "\n", encoding="utf-8")
    return {
        "rom_sha256": sha256_file(root / "pokegold.gbc"), "symbols_sha256": sha256_file(root / "pokegold.sym"),
        "backend": f"{PyBoy.__module__}.{PyBoy.__name__}", "backend_sha256": sha256_file(backend_file),
        "state_basis": replay_state_basis(state, 1), "recording_sha256": sha256_file(schedule),
        "entry_bank": start.bank, "entry_pc": entry,
        "return_checkpoint": f"MonMailAction.RemoveMailToBag+0x{continuation - start.address:X}",
        "selected_slot": 2, "mail_record_bytes": 47, "before": before, "after": observed[0],
        "materialized": True,
        "known_limits": ["Staged caller continuation after menu confirmation and bag transfer; not a navigation proof.",
                         "Known historical cause used to develop a fixture; not blind acceptance evidence."],
    }
