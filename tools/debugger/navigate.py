"""Deity-mode auto-navigator: self-drive pokegold to a target game state.

The navigator boots a fresh ROM, replays a fixed *checkpoint* input log to a
known reachable state, and evaluates a target-state predicate
(``tools.debugger.state_predicate``) against live RAM every frame. The instant
the predicate is satisfied it captures a save-state + a replayable run manifest
and prints the ``predicate satisfied`` evidence marker. If the predicate is
never satisfied within the checkpoint's inputs it fails closed and reports the
nearest state it actually observed — it never claims a state it could not see.

This is the Phase-1 self-driving slice. The only checkpoint is ``new_game``
(power-on -> the New Bark bedroom, ``PLAYERS_HOUSE_2F``) and the only observable
field is ``map``. A predicate over an unobserved field (battle, turn,
wild_battle) parses fine but fails closed here — that is the honest "capability
not built yet" signal, not a crash.

    python -m tools.debugger navigate --to "map=PLAYERS_HOUSE_2F"
    python -m tools.debugger navigate --verify <run-manifest.json>
    python -m tools.debugger navigate --self-test

Roadmap: ``docs/debugger_deity_mode_roadmap.md`` section 6 (Phase 1, Task 3).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from tools.trace import runtime as rt

from . import state_predicate
from .input_log import build_input_playback, play_inputs_for_frame
from .runtime_state import load_map_catalog

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DIR = ROOT / "audit" / "debugger_checkpoints"
DEFAULT_ROM = ROOT / "pokegold.gbc"
DEFAULT_SYMBOLS = ROOT / "pokegold.sym"
ARTIFACT_DIR = ROOT / ".local" / "tmp" / "deity_nav"

EVIDENCE_MARKER = "predicate satisfied"
# Drive this many frames past the checkpoint's scheduled inputs before failing
# closed, so a predicate satisfied a few frames after the last button still hits.
FRAME_SLACK = 300


# --- checkpoints -------------------------------------------------------------


def load_checkpoint(name: str) -> dict[str, Any]:
    """Load a checkpoint manifest and its parsed input-log playback by id."""
    manifest_path = CHECKPOINT_DIR / f"{name}.manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"unknown checkpoint {name!r}: {manifest_path} not found")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    log_path = CHECKPOINT_DIR / manifest["input_log"]
    playback = build_input_playback((str(log_path),), root=ROOT, max_events=0)
    if playback["errors"]:
        raise ValueError(f"checkpoint {name!r} input log invalid: {playback['errors']}")
    return {
        "name": name,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "log_path": log_path,
        "playback": playback,
    }


def log_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- observation -------------------------------------------------------------


def map_const(catalog: dict[str, Any], group: int, number: int) -> str | None:
    entry = catalog.get("maps", {}).get(f"{group}:{number}")
    return entry.get("const") if isinstance(entry, dict) else None


def build_observed(catalog: dict[str, Any], group: int, number: int) -> dict[str, Any]:
    """The flat observed dict ``state_predicate.evaluate`` consumes.

    Phase-1 observes only the current map. ``group``/``number`` are kept under
    underscore keys for fail-closed messages; ``map`` is set only when a real
    map is loaded (group != 0) and the catalog names it.
    """
    observed: dict[str, Any] = {"_group": int(group), "_number": int(number)}
    const = map_const(catalog, group, number)
    if group and const:
        observed["map"] = const
    return observed


def observe(pyboy: Any, symbols: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    return build_observed(
        catalog,
        rt.read_byte(pyboy, symbols["wMapGroup"]),
        rt.read_byte(pyboy, symbols["wMapNumber"]),
    )


def describe_state(observed: dict[str, Any] | None) -> str:
    if not observed:
        return "no state observed"
    group, number = observed.get("_group", 0), observed.get("_number", 0)
    name = observed.get("map")
    return f"map={name} ({group}:{number})" if name else f"no map loaded ({group}:{number})"


# --- driving -----------------------------------------------------------------


def navigate_to(
    predicate_text: str,
    *,
    checkpoint: str = "new_game",
    rom: Path = DEFAULT_ROM,
    symbols_path: Path = DEFAULT_SYMBOLS,
    save_state: str | None = None,
    manifest_out: str | None = None,
    frame_slack: int = FRAME_SLACK,
) -> dict[str, Any]:
    """Replay ``checkpoint`` and stop the instant ``predicate_text`` holds.

    Raises ``PredicateError`` on a bad predicate (fail at parse, not frame
    100000). Returns an outcome dict; ``reached`` is True iff the predicate was
    satisfied, in which case a save-state + run manifest were written.
    """
    predicate = state_predicate.parse(predicate_text)
    checkpoint_data = load_checkpoint(checkpoint)
    symbols = rt.parse_symbols(symbols_path)
    for needed in ("wMapGroup", "wMapNumber"):
        if needed not in symbols:
            raise KeyError(f"symbol {needed} missing from {symbols_path}")
    catalog = load_map_catalog(root=ROOT, labels={})
    playback = checkpoint_data["playback"]
    budget = int(playback["total_frames"]) + max(0, frame_slack)

    pyboy = rt.open_pyboy(rom, "PyBoy required for navigate")
    rt.disable_realtime(pyboy)
    try:
        reached_frame: int | None = None
        observed: dict[str, Any] = {}
        for frame in range(budget):
            play_inputs_for_frame(pyboy, playback, frame)
            pyboy.tick(1, False)
            observed = observe(pyboy, symbols, catalog)
            if state_predicate.evaluate(predicate, observed).satisfied:
                reached_frame = frame
                break
        return _build_outcome(
            pyboy=pyboy,
            predicate=predicate,
            checkpoint_data=checkpoint_data,
            reached_frame=reached_frame,
            observed=observed,
            save_state=save_state,
            manifest_out=manifest_out,
        )
    finally:
        pyboy.stop()


def _build_outcome(
    *,
    pyboy: Any,
    predicate: state_predicate.Predicate,
    checkpoint_data: dict[str, Any],
    reached_frame: int | None,
    observed: dict[str, Any],
    save_state: str | None,
    manifest_out: str | None,
) -> dict[str, Any]:
    base = {
        "predicate": predicate.describe(),
        "checkpoint": checkpoint_data["name"],
        "nearest": describe_state(observed),
    }
    if reached_frame is None:
        unmet = state_predicate.evaluate(predicate, observed).unmet
        return {**base, "reached": False, "unmet": list(unmet)}

    state_path = (
        Path(save_state)
        if save_state
        else ARTIFACT_DIR / f"{checkpoint_data['name']}__{_slug(predicate.describe())}.state"
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("wb") as handle:
        pyboy.save_state(handle)

    manifest = {
        "schema_version": 1,
        "kind": "deity_navigator_run",
        "predicate": predicate.describe(),
        "checkpoint": checkpoint_data["name"],
        "checkpoint_log": checkpoint_data["manifest"]["input_log"],
        "checkpoint_log_sha256": log_sha256(checkpoint_data["log_path"]),
        "reached_frame": reached_frame,
        "observed_map": observed.get("map"),
        "observed_group": observed.get("_group"),
        "observed_number": observed.get("_number"),
        "save_state": str(state_path),
    }
    manifest_path = Path(manifest_out) if manifest_out else state_path.with_suffix(".manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        **base,
        "reached": True,
        "frame": reached_frame,
        "map": observed.get("map"),
        "map_desc": describe_state(observed),
        "state_path": str(state_path),
        "manifest_path": str(manifest_path),
    }


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text).strip("_") or "state"


# --- re-validation (North-Star #4: honest synthesis) -------------------------


def verify_run(
    manifest_path: str,
    *,
    rom: Path = DEFAULT_ROM,
    symbols_path: Path = DEFAULT_SYMBOLS,
    frame_slack: int = FRAME_SLACK,
) -> dict[str, Any]:
    """Replay a run manifest's checkpoint and re-assert its predicate + map.

    Confirms (1) the checkpoint log bytes are unchanged since the run (sha) and
    (2) re-driving from the checkpoint re-satisfies the stored predicate and
    reaches the same map const — the deterministic round-trip the roadmap asks
    of every synthesized state.
    """
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("kind") != "deity_navigator_run":
        raise ValueError(f"not a navigator run manifest: {manifest_path}")
    checkpoint_data = load_checkpoint(manifest["checkpoint"])
    sha_ok = log_sha256(checkpoint_data["log_path"]) == manifest.get("checkpoint_log_sha256")
    outcome = navigate_to(
        manifest["predicate"],
        checkpoint=manifest["checkpoint"],
        rom=rom,
        symbols_path=symbols_path,
        frame_slack=frame_slack,
    )
    map_ok = bool(outcome.get("reached")) and outcome.get("map") == manifest.get("observed_map")
    return {
        "passed": bool(sha_ok and map_ok),
        "sha_ok": sha_ok,
        "predicate_satisfied": bool(outcome.get("reached")),
        "map_ok": map_ok,
        "expected_map": manifest.get("observed_map"),
        "observed": outcome.get("map_desc") or outcome.get("nearest"),
    }


# --- pure-logic self-test (no emulator) --------------------------------------


def run_self_test() -> dict[str, Any]:
    """Verify the navigator's logic without booting PyBoy or needing a built ROM.

    Covers checkpoint parsing + byte integrity, map-catalog const resolution,
    and the predicate parse/observe/evaluate path the live drive uses — fast and
    deterministic so it can sit in the frozen selftest gate. The end-to-end
    self-drive proof lives in the deity benchmark (driver: auto), which actually
    boots PyBoy and reaches the bedroom.
    """
    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    checkpoint_data = load_checkpoint("new_game")
    playback = checkpoint_data["playback"]
    manifest = checkpoint_data["manifest"]

    record(
        "checkpoint_parses",
        not playback["errors"] and playback["event_count"] > 0,
        f"events={playback['event_count']} errors={playback['errors']}",
    )
    record(
        "checkpoint_buttons",
        {"A", "START"} <= set(playback["button_sample"]),
        f"button_sample={playback['button_sample']}",
    )
    actual_sha = log_sha256(checkpoint_data["log_path"])
    record(
        "checkpoint_sha",
        actual_sha == manifest["input_log_sha256"],
        f"actual={actual_sha} manifest={manifest['input_log_sha256']}",
    )

    catalog = load_map_catalog(root=ROOT, labels={})
    group, number = manifest["expected_group"], manifest["expected_number"]
    const = map_const(catalog, group, number)
    record(
        "catalog_const",
        const == manifest["expected_const"],
        f"{group}:{number} -> {const} (want {manifest['expected_const']})",
    )

    predicate = state_predicate.parse(f"map={manifest['expected_const']}")
    hit = build_observed(catalog, group, number)
    record("predicate_hit", state_predicate.evaluate(predicate, hit).satisfied, f"observed={hit}")

    miss = state_predicate.evaluate(predicate, {"map": "ROUTE_29"})
    record("predicate_miss", (not miss.satisfied) and bool(miss.unmet), f"unmet={miss.unmet}")

    no_map = build_observed(catalog, 0, 0)
    record(
        "fail_closed_no_map",
        "map" not in no_map and not state_predicate.evaluate(predicate, no_map).satisfied,
        f"observed={no_map}",
    )

    unobserved = state_predicate.parse("battle(boss=MORTY) and turn==3")
    record(
        "fail_closed_unobserved",
        not state_predicate.evaluate(unobserved, hit).satisfied,
        "predicate over unobserved fields stays unsatisfied (capability not built)",
    )

    errors = [f"{c['name']}: {c['detail']}" for c in checks if not c["ok"]]
    return {"passed": not errors, "checks": checks, "errors": errors}


# --- CLI ---------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger navigate",
        description=(
            "Self-drive pokegold to a target-state predicate from a fixed checkpoint, "
            "capturing a save-state + replayable manifest on success."
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--to", metavar="PREDICATE", help="target-state predicate to self-drive to")
    mode.add_argument("--verify", metavar="MANIFEST", help="replay a run manifest and re-assert it")
    mode.add_argument("--self-test", action="store_true", help="pure-logic self-check (no emulator)")
    parser.add_argument("--checkpoint", default="new_game", help="checkpoint id to replay (default: new_game)")
    parser.add_argument("--rom", default=str(DEFAULT_ROM))
    parser.add_argument("--symbols", default=str(DEFAULT_SYMBOLS))
    parser.add_argument("--save-state", default=None, help="save-state output path (default: under .local/tmp)")
    parser.add_argument("--manifest-out", default=None, help="run-manifest output path")
    parser.add_argument("--frame-slack", type=int, default=FRAME_SLACK)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.self_test:
        report = run_self_test()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            for check in report["checks"]:
                print(f"  {'[ok]  ' if check['ok'] else '[FAIL]'} {check['name']} - {check['detail']}")
            print(f"navigate self-test {'PASS' if report['passed'] else 'FAIL'}")
        return 0 if report["passed"] else 1

    if args.verify:
        report = verify_run(
            args.verify, rom=Path(args.rom), symbols_path=Path(args.symbols), frame_slack=args.frame_slack
        )
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"verify {'PASS' if report['passed'] else 'FAIL'}: {report}")
        return 0 if report["passed"] else 1

    try:
        outcome = navigate_to(
            args.to,
            checkpoint=args.checkpoint,
            rom=Path(args.rom),
            symbols_path=Path(args.symbols),
            save_state=args.save_state,
            manifest_out=args.manifest_out,
            frame_slack=args.frame_slack,
        )
    except state_predicate.PredicateError as exc:
        print(f"invalid predicate: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(outcome, indent=2))
        return 0 if outcome["reached"] else 1

    if outcome["reached"]:
        print(
            f"{EVIDENCE_MARKER}: {outcome['predicate']} at frame {outcome['frame']} "
            f"[checkpoint={outcome['checkpoint']}] {outcome['map_desc']}"
        )
        print(f"save-state: {outcome['state_path']}")
        print(f"manifest:   {outcome['manifest_path']}")
        return 0

    print(
        f"could not reach {outcome['predicate']} within checkpoint {outcome['checkpoint']}; "
        f"nearest observed {outcome['nearest']}; unmet: {', '.join(outcome['unmet'])}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
